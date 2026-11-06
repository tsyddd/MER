"""Frozen Gemini graph -> three experts (1-2 answers) -> reflection -> common-label routing -> debate -> summary.

Round 0 / reflection / debate / summary prompts: versions/v4/emotion_wheel_prompts.py. The organization text reuses
the already saved v3 output of the same provider (identical prompt, identical frozen graph); if it is missing it is
generated with the same prompt. Gold labels are never sent to a model; they are read only by report().

Routing (code, not prompt):
  after reflection every expert has a label set {answer, alt_answer?}; exactly one label in the intersection of the three
  sets -> output it. Otherwise debate (<= MAX_ROUNDS rounds, each expert gives ONE answer within the candidate union =
  all labels proposed in Round 0 and reflection). Three identical debate answers -> adopt, else the summary stage.

Usage (Linux server, project root as cwd):
  python versions/v4/pipeline.py run --provider gpt|gemini [--smoke] [--workers 3]
  python versions/v4/pipeline.py report --provider gpt|gemini
"""
from __future__ import annotations
import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import ROOT, Client, digest, parse_json, prepare_frames, save, update_log
import emotion_wheel_prompts as prompts

VERSION = 'reflect_debate_v4'
BASE = ROOT / 'outputs' / VERSION
FROZEN = ROOT / 'data' / 'gemini_graph_three_experts_v1'  # validation 80 (frozen earlier, never modified)
FROZEN_TRAIN = ROOT / 'data' / 'gemini_graph_train_v4'  # train 320, built by scripts/gen_train_graphs.py
V3 = ROOT / 'outputs' / 'gemini_graph_emotion_wheel_v3'
ROLES = ['graph', 'audio_subtitle', 'image']
MAX_ROUNDS = 2
PATTERN = r'(?:process|person|context)_\d+'
TOKENS = dict(organization=2048, r0=3200, reflect=3200, debate=3800, summary=2600)
EV_KEYS = {'id', 'source', 'anchor', 'observation', 'interpretation', 'polarity'}
BASE_KEYS = {'expert', 'reason', 'open_emotion', 'answer', 'mapping_reason', 'evidence', 'counterevidence'}
ALT_KEYS = {'alt_answer', 'alt_open_emotion', 'uncertainty_reason'}


class StageInvalid(RuntimeError):
    """The model answered every attempt but never with a valid output."""


def read(path):
    return json.loads(Path(path).read_text())


def rows(split='all'):
    data = []
    for name, n in (('validation', 80), ('train', 320)):
        part = [json.loads(l) for l in (ROOT / 'data/manifests' / (name + '.jsonl')).read_text().splitlines() if l.strip()]
        assert len(part) == len({r['id'] for r in part}) == n
        data += [dict(r, split=name) for r in part]
    assert len(data) == len({r['id'] for r in data}) == 400, 'train/validation ids overlap'
    return data if split == 'all' else [r for r in data if r['split'] == split]


def graph_entries():
    entries = dict(read(FROZEN / 'manifest.json'))
    if (FROZEN_TRAIN / 'manifest.json').exists():
        entries.update(read(FROZEN_TRAIN / 'manifest.json'))
    return entries


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def check_no_gold(obj):
    if isinstance(obj, dict):
        assert not {'label', 'gold', 'ground_truth', 'prediction', 'teacher_predictions'} & obj.keys(), 'Gold/prior prediction leak'
        for v in obj.values():
            check_no_gold(v)
    elif isinstance(obj, list):
        for v in obj:
            check_no_gold(v)


# ------------------------------------------------------------------------------------------------ validation
def nonempty(x):
    return isinstance(x, str) and bool(x.strip())


def check_evidence(evidence, role, audio, subtitle):
    assert isinstance(evidence, list) and 1 <= len(evidence) <= 4, 'evidence needs 1-4 items'
    ids = []
    for e in evidence:
        assert isinstance(e, dict) and set(e) == EV_KEYS and all(nonempty(v) for v in e.values()), 'bad evidence item'
        assert re.fullmatch(r'E[1-9]\d*', e['id']), 'bad evidence id'
        assert e['source'] in {'visual', 'audio', 'subtitle', 'graph'} and e['polarity'] in {'support', 'counter', 'uncertain'}
        assert e['source'] != 'graph' or role == 'graph', 'Other experts have no graph'
        assert e['source'] != 'audio' or audio, 'No actual audio supplied'
        assert e['source'] != 'subtitle' or subtitle, 'No subtitle supplied'
        ids.append(e['id'])
    assert len(set(ids)) == len(ids), 'duplicate evidence ids'


def validator(stage, role, classes, audio, subtitle, candidates=None):
    """stage in organization / r0 / reflect / debate / summary"""
    def check(v):
        assert isinstance(v, dict), 'Expected JSON object'
        if stage == 'summary':
            assert set(v) == {'reason', 'answer', 'evidence_refs'}, 'summary keys'
            assert nonempty(v['reason']) and v['answer'] in classes, 'summary reason/answer'
            assert isinstance(v['evidence_refs'], list) and all(isinstance(r, str) for r in v['evidence_refs'])
            return
        keys = set(BASE_KEYS)
        if stage in ('r0', 'reflect'):
            keys |= ALT_KEYS
        if stage == 'reflect':
            keys |= {'changed', 'reflection'}
        if stage == 'debate':
            keys |= {'changed', 'adopted_evidence', 'response_to_others'}
        assert set(v) == keys, 'keys must be exactly: ' + ', '.join(sorted(keys))
        assert v['expert'] == role, 'expert must be ' + role
        assert nonempty(v['reason']) and nonempty(v['mapping_reason']) and nonempty(v['counterevidence'])
        prompts.validate_open(v)
        assert v['answer'] in classes, 'answer outside the label space'
        check_evidence(v['evidence'], role, audio, subtitle)
        if stage in ('r0', 'reflect'):
            alt = [v[k] for k in sorted(ALT_KEYS)]
            if any(a is not None for a in alt):
                assert all(a is not None for a in alt), 'alt fields must be all null or all set'
                assert v['alt_answer'] in classes and v['alt_answer'] != v['answer'], 'alt_answer must be another allowed label'
                assert nonempty(v['alt_open_emotion']) and nonempty(v['uncertainty_reason'])
        if stage == 'reflect':
            assert isinstance(v['changed'], bool) and nonempty(v['reflection'])
        if stage == 'debate':
            assert v['answer'] in candidates, 'answer must be one of candidate_labels'
            assert isinstance(v['changed'], bool)
            ad = v['adopted_evidence']
            assert isinstance(ad, list) and all(isinstance(a, dict) and set(a) == {'from', 'verified'} and nonempty(a['from']) and nonempty(a['verified']) for a in ad)
            assert not v['changed'] or ad, 'changed=true needs adopted_evidence'
            rs = v['response_to_others']
            assert isinstance(rs, list) and len(rs) == 2, 'response_to_others needs one item per other expert'
            for r in rs:
                assert isinstance(r, dict) and set(r) == {'expert', 'their_claim', 'my_response', 'evidence'}
                assert nonempty(r['expert']) and nonempty(r['their_claim']) and nonempty(r['my_response'])
                assert isinstance(r['evidence'], list) and r['evidence'] and all(nonempty(x) for x in r['evidence']), 'each response needs locatable evidence'
    return check


def labels_of(o):
    return {o['answer']} | ({o['alt_answer']} if o.get('alt_answer') else set())


# ------------------------------------------------------------------------------------------------ one model call with cache
def call_stage(folder, tag, client, system, payload, frames, audio, validate, max_tokens, fallback=None):
    check_no_gold(payload)
    signature = sha(dict(system=sha(system), payload=payload, frames=[digest(p) for p in frames], audio=digest(audio) if audio else None,
                         model=client.model, provider=client.provider, max_tokens=max_tokens, version=VERSION))
    dest = folder / (tag + '.json')
    if dest.exists():
        cached = read(dest)
        if cached.get('signature') == signature:
            if not cached.get('fallback'):
                validate(cached['output'])
            return cached['output']
    feedback = None
    error = None
    generated = False
    text = ''
    for attempt in range(1, 4):
        actual = payload if feedback is None else dict(original_input=payload, format_repair=feedback)
        check_no_gold(actual)
        text = ''
        try:
            text, raw, seconds = client.generate(system, actual, frames, audio, max_tokens)
            generated = True
            save(folder / 'calls' / f'{tag}_attempt{attempt}.json',
                 dict(tag=tag, attempt=attempt, system_sha256=sha(system), payload=actual, frame_hashes=[digest(p) for p in frames],
                      audio_hash=digest(audio) if audio else None, model=client.model, provider=client.provider, text=text, raw=raw))
            value = parse_json(text)
            validate(value)
            save(dest, dict(signature=signature, output=value, attempt=attempt, seconds=seconds, usage=raw.get('usage'),
                            response_model=raw.get('model'), fallback=False))
            return value
        except Exception as exc:
            error = client.clean(exc)
            save(folder / 'calls' / f'{tag}_error_attempt{attempt}.json', dict(error=error))
            if text:
                feedback = dict(error=error, previous_response=text,
                                instruction='Repair only the JSON fields and values according to the required schema; use the original input and add no facts. Return the complete JSON object.')
            if any(code in error for code in ['HTTP 401', 'HTTP 403', 'HTTP 404']):
                break
            if attempt < 3:
                time.sleep((60 if 'HTTP 429' in error else 30) * attempt if not text else 3)
    if fallback is not None and generated:
        value = fallback(error)
        save(dest, dict(signature=signature, output=value, attempt=3, fallback=True, error=error))
        return value
    raise (StageInvalid if generated else RuntimeError)(tag + ': ' + str(error))


# ------------------------------------------------------------------------------------------------ payloads
def media_payload(row, info, audio):
    result = dict(sample_id=row['id'], target_speaker=row.get('speaker') or 'main person',
                  allowed_labels=row['classes'], frame_times_seconds=info['seconds'], audio_provided=bool(audio))
    if row.get('subtitle', '').strip():
        result['subtitle'] = row['subtitle']
    return result


def role_payloads(row, graph, organization, info, audio):
    shared = media_payload(row, info, audio)
    return {'graph': dict(shared, graph=graph, organization=organization, graph_source='Frozen Gemini graph; indirect audio facts are not direct listening'),
            'audio_subtitle': dict(shared), 'image': dict(shared)}


def get_organization(folder, provider, row, client, graph):
    dest = folder / 'organization.json'
    if dest.exists():
        return read(dest)['output']['text']
    src = V3 / provider / row['id'] / 'organization.json'
    if src.exists():
        value = read(src)
        assert set(value) == {'text'} and nonempty(value['text'])
        assert set(re.findall(PATTERN, value['text'])) <= {n['id'] for n in graph['nodes']}
        save(dest, dict(output=value, reused_from=str(src.relative_to(ROOT)), sha256=digest(src)))
        return value['text']

    def check(v):
        assert isinstance(v, dict) and set(v) == {'text'} and nonempty(v['text'])
        refs = set(re.findall(PATTERN, v['text']))
        assert refs and refs <= {n['id'] for n in graph['nodes']}, 'Organization must cite actual nodes'
    out = call_stage(folder, 'organization_gen', client, prompts.ORGANIZATION,
                     dict(sample_id=row['id'], target_speaker=row.get('speaker') or 'main person', graph=graph), [], None, check, TOKENS['organization'])
    save(dest, dict(output=out, reused_from=None))
    return out['text']


# ------------------------------------------------------------------------------------------------ one sample
def sample(row, provider):
    client = Client(provider)
    folder = BASE / provider / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result_path = folder / 'result.json'
        if result_path.exists() and read(result_path).get('status') == 'success':
            return read(result_path)
        started = time.time()
        current = 'prepare'
        classes = row['classes']
        try:
            entry = graph_entries()[row['id']]
            assert digest(entry['path']) == entry['sha256'], 'Frozen graph integrity changed'
            graph = read(entry['path'])
            info = prepare_frames(row)
            audio = row['audio'] if client.config.get('audio_supported') else None
            frames = info['frames']
            subtitle = row.get('subtitle', '').strip()
            current = 'organization'
            organization = get_organization(folder, provider, row, client, graph)
            payloads = role_payloads(row, graph, organization, info, audio)
            pool = concurrent.futures.ThreadPoolExecutor(3)

            def experts(stage, tag, make_payload, candidates=None, fallback_from=None):
                futures = {}
                for role in ROLES:
                    system = {'r0': prompts.expert, 'reflect': prompts.reflection, 'debate': prompts.debate}[stage](role, classes)
                    fb = None
                    if fallback_from:
                        def fb(error, role=role):
                            prev = fallback_from[role]
                            return dict({k: prev[k] for k in BASE_KEYS}, answer=prev['answer'], changed=False, adopted_evidence=[],
                                        response_to_others=[], fallback=True, fallback_reason=error)
                    futures[role] = pool.submit(call_stage, folder, f'{tag}_{role}', client, system, make_payload(role), frames, audio,
                                                validator(stage, role, classes, audio, subtitle, candidates), TOKENS[stage], fb)
                return {role: f.result() for role, f in futures.items()}

            current = 'r0'
            r0 = experts('r0', 'r0', lambda role: payloads[role])
            current = 'reflect'
            reflect = experts('reflect', 'reflect', lambda role: dict(payloads[role], your_previous_output=r0[role]))
            sets = {role: labels_of(reflect[role]) for role in ROLES}
            common = set.intersection(*sets.values())
            union = sorted({l for o in list(r0.values()) + list(reflect.values()) for l in labels_of(o)}, key=classes.index)
            history = {role: dict(r0=r0[role], reflect=reflect[role]) for role in ROLES}
            route, final, debate_rounds, summary = None, None, 0, None
            if len(common) == 1:
                route, final = 'common_label', next(iter(common))
            else:
                state = reflect
                for rd in range(1, MAX_ROUNDS + 1):
                    current = f'debate{rd}'
                    state = experts('debate', f'debate{rd}',
                                    lambda role: dict(payloads[role], round=rd, your_previous_output=state[role], candidate_labels=union,
                                                      other_experts={o: state[o] for o in ROLES if o != role}),
                                    candidates=union, fallback_from=state)
                    debate_rounds = rd
                    for role in ROLES:
                        history[role][f'debate{rd}'] = state[role]
                    if len({state[r]['answer'] for r in ROLES}) == 1:
                        break
                answers = {r: state[r]['answer'] for r in ROLES}
                if len(set(answers.values())) == 1:
                    route, final = 'debate_consensus', next(iter(answers.values()))
                else:
                    current = 'summary'
                    route = 'summary'
                    summary = call_stage(folder, 'summary', client, prompts.summary(classes),
                                         dict(media_payload(row, info, audio), expert_history=history, final_single_answers=answers, candidate_labels=union),
                                         frames, audio, validator('summary', None, classes, audio, subtitle), TOKENS['summary'])
                    final = summary['answer']
            pool.shutdown()
            primaries = [r for r in ROLES if reflect[r]['answer'] == final]
            result = dict(id=row['id'], dataset=row['dataset'], provider=provider, model=client.model, status='success', version=VERSION,
                          route=route, prediction=final, debate_rounds=debate_rounds, candidate_labels=union,
                          r0_sets={r: sorted(labels_of(r0[r])) for r in ROLES}, reflect_sets={r: sorted(sets[r]) for r in ROLES},
                          common_labels=sorted(common), final_is_primary_of_roles_after_reflect=primaries,
                          debate_answers={f'debate{d}': {r: history[r][f'debate{d}']['answer'] for r in ROLES} for d in range(1, debate_rounds + 1)},
                          fallbacks=[f'{k}_{r}' for r in ROLES for k, v in history[r].items() if v.get('fallback')],
                          summary_reason=summary['reason'] if summary else None, label=row['label'],
                          raw_audio_provided=bool(audio), frames=8, elapsed_seconds=time.time() - started)
        except Exception as exc:
            result = dict(id=row['id'], dataset=row['dataset'], provider=provider, model=client.model, status='error', version=VERSION,
                          stage=current, error=client.clean(exc), traceback=client.clean(traceback.format_exc()), elapsed_seconds=time.time() - started)
        save(result_path, result)
        return result


def worker(provider, smoke, workers, ids=None, split='all'):
    BASE.mkdir(parents=True, exist_ok=True)
    selected = rows(split)
    entries = graph_entries()
    missing = [r['id'] for r in selected if r['id'] not in entries]
    selected = [r for r in selected if r['id'] in entries]
    if missing:
        print('SKIPPED (no frozen graph):', json.dumps(missing), flush=True)
    if ids:
        selected = [r for r in selected if r['id'] in ids]
        assert len(selected) == len(ids), 'unknown ids'
    elif smoke:
        selected = [next(r for r in selected if r['dataset'] == d) for d in ['MER2024', 'MELD']]
    save(BASE / provider / ('protocol_' + split + '.json'), dict(
        version=VERSION, provider=provider, split=split, samples=len(selected), skipped_without_graph=missing, workers=workers,
        graph='frozen Gemini graph (data/gemini_graph_three_experts_v1 for validation, data/gemini_graph_train_v4 for train)',
        organization='validation: reused from saved outputs of the same provider (identical prompt); train: generated per provider with the same prompt',
        flow='r0 (1-2 answers) -> reflect (always) -> common-label routing -> debate (<=2 rounds, single answer in candidate union) -> summary',
        routing='intersection of label sets after reflection has exactly one label -> output', max_rounds=MAX_ROUNDS, frames=8,
        raw_audio_supported=provider != 'gpt', max_tokens=TOKENS, labels_not_sent=True, optimization=False, smoke=smoke,
        prompts_sha256=dict(emotion_wheel_prompts=digest(Path(prompts.__file__)), emotion_wheels=digest(prompts.CONFIG_PATH)),
        note='validation 80 reused as development data; train 320 not used for any prompt or rule development in v4'))
    with (BASE / (provider + ('_smoke' if smoke else '') + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        update_log(f'v4 反思+辩论流水线启动：{provider}，{len(selected)} 条（smoke={smoke}），workers={workers}；输出 outputs/{VERSION}/{provider}。')
        done = {}
        for rnd in range(2):  # second pass retries samples that ended in error (stage outputs are cached)
            todo = [r for r in selected if done.get(r['id']) != 'success']
            if not todo:
                break

            def one(r):
                res = sample(r, provider)
                print(json.dumps(dict(provider=provider, id=r['id'], status=res['status'], route=res.get('route'), stage=res.get('stage'),
                                      error=(res.get('error') or '')[:200]), ensure_ascii=False), flush=True)
                return r['id'], res['status']
            with concurrent.futures.ThreadPoolExecutor(workers) as pool:
                done.update(dict(pool.map(one, todo)))
        ok = sum(v == 'success' for v in done.values())
        update_log(f'v4 反思+辩论流水线结束：{provider}，成功 {ok}/{len(selected)}（smoke={smoke}）；结果以 outputs/{VERSION}/{provider}/*/result.json 为准。')
        return 0 if ok == len(selected) else 1


# ------------------------------------------------------------------------------------------------ evaluation (gold used only here)
def report(provider, split='all'):
    stats = Counter()
    by_route = {}
    expert_acc = Counter()
    detail = []
    n = 0
    for row in rows(split):
        p = BASE / provider / row['id'] / 'result.json'
        if not p.exists() or read(p).get('status') != 'success':
            continue
        res, gold = read(p), row['label']
        folder = BASE / provider / row['id']
        r0 = {r: read(folder / f'r0_{r}.json')['output'] for r in ROLES}
        rf = {r: read(folder / f'reflect_{r}.json')['output'] for r in ROLES}
        v3 = V3 / provider / row['id']
        v3_summary = read(v3 / 'summary.json')['answer'] if (v3 / 'summary.json').exists() else None
        v3_experts = [read(v3 / f'expert_{r}.json')['answer'] for r in ROLES] if (v3 / 'expert_graph.json').exists() else None
        n += 1
        ok = res['prediction'] == gold
        stats['v4 final'] += ok
        stats[f'v4 final / {row["dataset"]}'] += ok
        if v3_summary is not None:
            stats['v3 summary'] += v3_summary == gold
            stats['v3 summary → v4: wrong→right'] += (v3_summary != gold) and ok
            stats['v3 summary → v4: right→wrong'] += (v3_summary == gold) and not ok
        if v3_experts:
            top = Counter(v3_experts).most_common()
            stats['v3 expert majority (ties wrong)'] += (len(top) < 3 and top[0][0] == gold)
        for name, outs in (('r0', r0), ('reflect', rf)):
            top = Counter(o['answer'] for o in outs.values()).most_common()
            stats[f'{name} primary majority (ties wrong)'] += (len(top) < 3 and top[0][0] == gold)
            for r in ROLES:
                expert_acc[f'{name} {r} primary'] += outs[r]['answer'] == gold
        stats['reflect changed primary'] += sum(rf[r]['answer'] != r0[r]['answer'] for r in ROLES)
        stats['gold in r0 primaries'] += gold in {o['answer'] for o in r0.values()}
        stats['gold in r0 label sets'] += gold in set().union(*[labels_of(o) for o in r0.values()])
        stats['gold in candidate union'] += gold in res['candidate_labels']
        stats['experts giving a backup (r0)'] += sum(bool(o.get('alt_answer')) for o in r0.values())
        stats['experts giving a backup (reflect)'] += sum(bool(o.get('alt_answer')) for o in rf.values())
        stats['fallbacks'] += len(res['fallbacks'])
        b = by_route.setdefault(res['route'], Counter())
        b['n'] += 1
        b['correct'] += ok
        if res['route'] == 'common_label':
            b['final is nobody\'s primary'] += not res['final_is_primary_of_roles_after_reflect']
            b['v3 summary correct on same'] += v3_summary == gold
        elif v3_summary is not None:
            b['v3 summary correct on same'] += v3_summary == gold
        if res['route'] != 'common_label':
            last = res['debate_answers'][f'debate{res["debate_rounds"]}']
            for r in ROLES:
                expert_acc[f'debate {r}'] += last[r] == gold
        detail.append(dict(id=row['id'], dataset=row['dataset'], gold=gold, route=res['route'], final=res['prediction'], v3_summary=v3_summary,
                           r0={r: sorted(labels_of(r0[r])) for r in ROLES}, reflect={r: sorted(labels_of(rf[r])) for r in ROLES},
                           debate=res['debate_answers']))
    if split == 'train':  # v3 was never run on train
        for b in by_route.values():
            b.pop('v3 summary correct on same', None)
    out = dict(version=VERSION, provider=provider, split=split, n=n, stats=dict(stats), by_route={k: dict(v) for k, v in by_route.items()},
               expert_primary_correct=dict(expert_acc), per_sample=detail)
    save(ROOT / 'metrics' / (f'{VERSION}_{provider}.json' if split == 'validation' else f'{VERSION}_{provider}_{split}.json'), out)
    print(f'{provider} [{split}]: n={n}')
    for k, v in stats.items():
        print(f'  {k}: {v}')
    for k, v in by_route.items():
        print(f'  route {k}: {dict(v)}')
    for k, v in expert_acc.items():
        print(f'  {k}: {v}')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['run', 'report'])
    ap.add_argument('--provider', choices=['gpt', 'gemini'], required=True)
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--split', choices=['validation', 'train', 'all'], default='all')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--ids', nargs='*', help='run only these sample ids (implies smoke-style protocol/lock)')
    a = ap.parse_args()
    if a.mode == 'run':
        sys.exit(worker(a.provider, a.smoke or bool(a.ids), a.workers, a.ids, a.split))
    report(a.provider, a.split)


if __name__ == '__main__':
    main()
