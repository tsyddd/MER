"""v5: three replacements of the v4 disagreement branch, run only on samples where v4 had no unique common label.

  A  anonymized debate   (Identity Bias): experts debate as in v4 but see an anonymized, shuffled pool of opinions
                          (their own included, unmarked); <=2 rounds; unanimous -> adopt, else anonymized summary.
  B0 trajectory scoring  (Free-MAD, c-variant): score saved v4 trajectories (R0, reflection, v4 debate). No model call.
  B1 trajectory scoring  (Free-MAD, n-variant): one new anti-conformity critique round (peers anonymized), then score
                          R0, reflection, critique.
  D  candidate-evidence controller: anonymous evidence pool -> one evidence-gathering call per candidate -> controller
                          verifies and compares -> label, or Direct's answer when the controller is not sure.

Reuses the saved v4 outputs (Round 0, reflection, routing, candidate set, organization text) and the saved Direct
answers; gold labels are never sent and are read only by report(). Design: docs/v5-methods.html.

Usage (server, project root): python versions/v5/pipeline.py run --provider gemini|gpt --method A|B1|D [--ids ...] [--workers 4]
                              python versions/v5/pipeline.py report --provider gemini|gpt
"""
from __future__ import annotations
import argparse
import concurrent.futures
import fcntl
import json
import random
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import importlib.util

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'v4'))  # emotion_wheel_prompts / prompts_base of v4
sys.path.insert(0, str(HERE.parents[1]))  # project root (engine)
_spec = importlib.util.spec_from_file_location('v4pipeline', HERE.parent / 'v4' / 'pipeline.py')
v4 = importlib.util.module_from_spec(_spec)  # versions/v4/pipeline.py, loaded under a distinct name
_spec.loader.exec_module(v4)
import emotion_wheel_prompts as P4  # noqa: E402
import v5_prompts as P5  # noqa: E402
from engine import ROOT, Client, digest, prepare_frames, save, update_log  # noqa: E402

VERSION = 'reflect_debate_v5'
BASE = ROOT / 'outputs' / VERSION
V4 = ROOT / 'outputs' / 'reflect_debate_v4'
DIRECT = ROOT / 'outputs' / 'direct'
ROLES = v4.ROLES
W = (20.0, 25.0, 30.0, 20.0)  # Free-MAD weights (w1 initial, w2 abandon, w3 adopt, w4 keep)
TOK = dict(debate=3800, summary=2600, critique=3800, gather=2400, controller=3000)
read = v4.read
nonempty = v4.nonempty


# ------------------------------------------------------------------------------------------- shared inputs
def disagreement_rows(provider):
    out = []
    for r in v4.rows('all'):
        res = V4 / provider / r['id'] / 'result.json'
        if res.exists() and read(res).get('status') == 'success' and read(res)['route'] != 'common_label':
            out.append(r)
    return out


def load_case(row, provider, client):
    f4 = V4 / provider / row['id']
    res = read(f4 / 'result.json')
    r0 = {r: read(f4 / f'r0_{r}.json')['output'] for r in ROLES}
    rf = {r: read(f4 / f'reflect_{r}.json')['output'] for r in ROLES}
    deb = {}
    for k in (1, 2):
        if (f4 / f'debate{k}_graph.json').exists():
            deb[k] = {r: read(f4 / f'debate{k}_{r}.json')['output'] for r in ROLES}
    entry = v4.graph_entries()[row['id']]
    assert digest(entry['path']) == entry['sha256'], 'Frozen graph integrity changed'
    graph = read(entry['path'])
    organization = read(f4 / 'organization.json')['output']['text']
    info = prepare_frames(row)
    audio = row['audio'] if client.config.get('audio_supported') else None
    direct = read(DIRECT / provider / row['id'] / 'result.json')
    return dict(row=row, res=res, r0=r0, rf=rf, deb=deb, graph=graph, organization=organization, info=info, audio=audio,
                frames=info['frames'], subtitle=row.get('subtitle', '').strip(), cands=res['candidate_labels'],
                direct=direct.get('prediction') if direct.get('status') == 'success' else None,
                payloads=v4.role_payloads(row, graph, organization, info, audio))


ROLE_WORDS = [('图谱专家', '一位专家'), ('音频字幕专家', '一位专家'), ('图像专家', '一位专家'), ('audio_subtitle', '专家'), ('graph', '专家'), ('image', '专家')]


def scrub(text):
    """Remove role names / role-prefixed evidence refs from free text (node IDs such as person_1 stay)."""
    if not isinstance(text, str):
        return text
    text = re.sub(r'\b(?:graph|audio_subtitle|image)\s*[:：]\s*(?:(?:r0|reflect|debate\d)\s*[:：]\s*)?(E\d+)', r'\1', text)
    for a, b in ROLE_WORDS[:3]:
        text = text.replace(a, b)
    return text


def opinion(o):
    """Content-only view of an expert output (no expert name, no debate bookkeeping)."""
    keep = ('answer', 'open_emotion', 'mapping_reason', 'reason', 'evidence', 'counterevidence')
    out = {k: o[k] for k in keep if k in o}
    out = json.loads(scrub(json.dumps(out, ensure_ascii=False)))
    return out


def rng_for(*parts):
    return random.Random('|'.join(map(str, parts)))


# ------------------------------------------------------------------------------------------- validators
def v_expert_common(v, role, classes, cands, audio, subtitle):
    assert v.get('expert') == role, 'expert must be ' + role
    assert v.get('answer') in cands, 'answer must be one of candidate_labels'
    for k in ('reason', 'mapping_reason', 'counterevidence'):
        assert nonempty(v.get(k)), k + ' required'
    P4.validate_open(v)
    v4.check_evidence(v.get('evidence'), role, audio, subtitle)


def v_anon(role, classes, cands, audio, subtitle, n_op):
    keys = {'expert', 'reason', 'open_emotion', 'answer', 'mapping_reason', 'adopted_evidence', 'response_to_opinions', 'evidence', 'counterevidence'}

    def check(v):
        assert isinstance(v, dict) and set(v) == keys, 'keys must be exactly: ' + ', '.join(sorted(keys))
        v_expert_common(v, role, classes, cands, audio, subtitle)
        ad = v['adopted_evidence']
        assert isinstance(ad, list) and all(isinstance(a, dict) and set(a) == {'from', 'verified'} and nonempty(a['from']) and nonempty(a['verified']) for a in ad)
        rs = v['response_to_opinions']
        assert isinstance(rs, list) and len(rs) == n_op, f'response_to_opinions needs {n_op} items'
        for r in rs:
            assert isinstance(r, dict) and set(r) == {'opinion', 'their_claim', 'my_response', 'evidence'}
            assert nonempty(r['opinion']) and nonempty(r['their_claim']) and nonempty(r['my_response'])
            assert isinstance(r['evidence'], list) and r['evidence'] and all(nonempty(x) for x in r['evidence'])
    return check


def v_critique(role, classes, cands, audio, subtitle, prev):
    keys = {'expert', 'my_reasoning', 'peer_review', 'decision', 'answer', 'open_emotion', 'mapping_reason', 'reason', 'evidence', 'counterevidence'}

    def check(v):
        assert isinstance(v, dict) and set(v) == keys, 'keys must be exactly: ' + ', '.join(sorted(keys))
        v_expert_common(v, role, classes, cands, audio, subtitle)
        assert nonempty(v['my_reasoning'])
        assert v['decision'] in ('KEEP', 'REVISE'), 'decision must be KEEP or REVISE'
        assert v['decision'] == 'REVISE' or v['answer'] == prev, 'KEEP must keep the previous answer ' + prev
        pr = v['peer_review']
        assert isinstance(pr, list) and len(pr) == 2, 'peer_review needs one item per peer'
        for r in pr:
            assert isinstance(r, dict) and set(r) == {'peer', 'correct_points', 'errors', 'error_type', 'evidence'}
            assert all(nonempty(r[k]) for k in ('peer', 'correct_points', 'errors', 'error_type'))
            assert isinstance(r['evidence'], list)
    return check


def v_gather(target):
    def item_ok(x):
        return isinstance(x, dict) and set(x) == {'ref', 'location', 'observation', 'why'} and all(nonempty(x[k]) for k in x)

    def check(v):
        assert isinstance(v, dict) and set(v) == {'candidate', 'support', 'against', 'discriminating'}, 'keys: candidate, support, against, discriminating'
        assert v['candidate'] == target, 'candidate must be ' + target
        assert isinstance(v['support'], list) and 1 <= len(v['support']) <= 4 and all(item_ok(x) for x in v['support']), 'support: 1-4 items with ref/location/observation/why'
        assert isinstance(v['against'], list) and len(v['against']) <= 3 and all(item_ok(x) for x in v['against']), 'against: 0-3 items'
        assert nonempty(v['discriminating'])
    return check


def v_controller(cands, ids):
    def check(v):
        assert isinstance(v, dict) and set(v) == {'verification', 'assessment', 'decision', 'reason'}
        assert v['decision'] in list(cands) + ['不确定'], 'decision must be a candidate or 不确定'
        assert nonempty(v['reason'])
        ver = {x.get('candidate'): x for x in v['verification']}
        assert set(ver) == set(cands), 'verification must cover every candidate'
        for c in cands:
            got = {i.get('id') for i in ver[c]['items']}
            assert got == set(ids[c]), f'verification of {c} must list items {sorted(ids[c])}'
            assert all(i.get('status') in ('成立', '不成立', '无法核对') for i in ver[c]['items'])
        ass = {x.get('candidate'): x for x in v['assessment']}
        assert set(ass) == set(cands), 'assessment must cover every candidate'
        for x in ass.values():
            assert isinstance(x.get('confirmed_support'), int) and isinstance(x.get('discriminating'), int)
            assert isinstance(x.get('modalities'), list) and isinstance(x.get('strongest_counter_holds'), bool)
    return check


# ------------------------------------------------------------------------------------------- A
def run_A(case, client, folder, pool):
    row, cands, classes = case['row'], case['cands'], case['row']['classes']
    state = dict(case['rf'])
    alias = dict(zip(ROLES, rng_for(row['id'], 'alias').sample(['专家1', '专家2', '专家3'], 3)))
    history = {alias[r]: dict(r0=opinion(case['r0'][r]), reflect=opinion(case['rf'][r])) for r in ROLES}
    rounds = 0
    for rd in (1, 2):
        futs = {}
        for role in ROLES:
            ops = [opinion(state[r]) for r in ROLES]
            rng_for(row['id'], rd, role).shuffle(ops)
            ops = [dict(id=f'观点{i + 1}', **o) for i, o in enumerate(ops)]
            payload = dict(case['payloads'][role], round=rd, candidate_labels=cands, opinions=ops)
            futs[role] = pool.submit(v4.call_stage, folder, f'debate{rd}_{role}', client, P5.anon_debate(role, classes), payload,
                                     case['frames'], case['audio'], v_anon(role, classes, cands, case['audio'], case['subtitle'], len(ops)), TOK['debate'])
        state = {r: f.result() for r, f in futs.items()}
        rounds = rd
        for r in ROLES:
            history[alias[r]][f'debate{rd}'] = json.loads(scrub(json.dumps({k: state[r][k] for k in state[r] if k != 'expert'}, ensure_ascii=False)))
        if len({state[r]['answer'] for r in ROLES}) == 1:
            break
    answers = {r: state[r]['answer'] for r in ROLES}
    if len(set(answers.values())) == 1:
        return dict(prediction=next(iter(answers.values())), route='consensus', rounds=rounds, answers=answers)
    summ = v4.call_stage(folder, 'summary', client, P5.anon_summary(classes),
                         dict(v4.media_payload(row, case['info'], case['audio']), expert_history=history,
                              final_single_answers={alias[r]: a for r, a in answers.items()}, candidate_labels=cands),
                         case['frames'], case['audio'], v4.validator('summary', None, classes, case['audio'], case['subtitle']), TOK['summary'])
    return dict(prediction=summ['answer'], route='summary', rounds=rounds, answers=answers, summary_in_candidates=summ['answer'] in cands)


# ------------------------------------------------------------------------------------------- B
def score(traj, normalize=False):
    """traj: {role: [answer_k0, answer_k1, ...]} -> (scores, contributors). Free-MAD event scoring, f = 1/(k+1)."""
    raw, contrib = Counter(), {}
    for role, seq in traj.items():
        for k, a in enumerate(seq):
            f = 1.0 / (k + 1)
            if k == 0:
                raw[a] += W[0] * f
                contrib.setdefault(a, set()).add(role)
            elif a == seq[k - 1]:
                raw[a] += W[3] * f
                contrib.setdefault(a, set()).add(role)
            else:
                raw[seq[k - 1]] -= W[1] * f
                raw[a] += W[2] * f
                contrib.setdefault(a, set()).add(role)
    if normalize:
        return {a: raw[a] / max(1, len(contrib.get(a, ()))) for a in raw}, contrib
    return dict(raw), contrib


def pick(scores, direct):
    top = max(scores.values())
    tied = sorted(a for a, s in scores.items() if abs(s - top) < 1e-9)
    if len(tied) == 1:
        return tied[0], 'unique'
    if direct in tied:
        return direct, 'tie_direct'
    return tied[0], 'tie_alpha'


def run_B0(case):
    traj = {r: [case['r0'][r]['answer'], case['rf'][r]['answer']] + [case['deb'][k][r]['answer'] for k in sorted(case['deb'])] for r in ROLES}
    out = {}
    for norm in (False, True):
        sc, _ = score(traj, norm)
        lab, how = pick(sc, case['direct'])
        out['norm' if norm else 'raw'] = dict(prediction=lab, tie=how, scores={a: round(s, 3) for a, s in sc.items()})
    return dict(prediction=out['raw']['prediction'], tie=out['raw']['tie'], scores=out['raw']['scores'], normalized=out['norm'], trajectory=traj)


def run_B1(case, client, folder, pool):
    row, cands, classes = case['row'], case['cands'], case['row']['classes']
    futs = {}
    for role in ROLES:
        peers = [opinion(case['rf'][r]) for r in ROLES if r != role]
        rng_for(row['id'], 'peers', role).shuffle(peers)
        payload = dict(case['payloads'][role], candidate_labels=cands, your_previous_output=opinion(case['rf'][role]),
                       peers=[dict(id=f'Peer #{i + 1}', **p) for i, p in enumerate(peers)])
        futs[role] = pool.submit(v4.call_stage, folder, f'critique_{role}', client, P5.critique(role, classes), payload, case['frames'], case['audio'],
                                 v_critique(role, classes, cands, case['audio'], case['subtitle'], case['rf'][role]['answer']), TOK['critique'])
    crit = {r: f.result() for r, f in futs.items()}
    traj = {r: [case['r0'][r]['answer'], case['rf'][r]['answer'], crit[r]['answer']] for r in ROLES}
    sc, _ = score(traj)
    lab, how = pick(sc, case['direct'])
    nsc, _ = score(traj, True)
    nlab, nhow = pick(nsc, case['direct'])
    return dict(prediction=lab, tie=how, scores={a: round(s, 3) for a, s in sc.items()}, trajectory=traj,
                decisions={r: crit[r]['decision'] for r in ROLES}, normalized=dict(prediction=nlab, tie=nhow, scores={a: round(s, 3) for a, s in nsc.items()}))


# ------------------------------------------------------------------------------------------- D
def evidence_pool(case):
    seen, items = set(), []
    for r in ROLES:
        for ev in case['rf'][r]['evidence']:
            obs = scrub(ev['observation']).strip()
            key = re.sub(r'\s+', '', obs)
            if key in seen:
                continue
            seen.add(key)
            items.append(dict(source=ev['source'], location=scrub(ev['anchor']), observation=obs))
    rng_for(case['row']['id'], 'pool').shuffle(items)
    return [dict(id=f'P{i + 1}', **x) for i, x in enumerate(items)]


def run_D(case, client, folder, pool):
    row, cands, classes = case['row'], case['cands'], case['row']['classes']
    media = v4.media_payload(row, case['info'], case['audio'])
    media.pop('allowed_labels', None)
    ev_pool = evidence_pool(case)
    futs = {}
    for c in cands:
        payload = dict(media, candidate_labels=cands, target_label=c, evidence_pool=ev_pool)
        futs[c] = pool.submit(v4.call_stage, folder, f'gather_{c}', client, P5.gather(classes, cands), payload, case['frames'], case['audio'], v_gather(c), TOK['gather'])
    dossiers, ids = {}, {}
    for c, f in futs.items():
        g = f.result()
        sup = [dict(id=f'S{i + 1}', location=x['location'], observation=x['observation'], why=x['why']) for i, x in enumerate(g['support'])]
        ag = [dict(id=f'A{i + 1}', location=x['location'], observation=x['observation'], why=x['why']) for i, x in enumerate(g['against'])]
        dossiers[c] = dict(candidate=c, support=sup, against=ag, discriminating=g['discriminating'])
        ids[c] = [x['id'] for x in sup + ag]
    order = list(cands)
    rng_for(row['id'], 'dossier').shuffle(order)
    ctrl = v4.call_stage(folder, 'controller', client, P5.controller(classes, cands), dict(media, candidate_labels=cands, dossiers=[dossiers[c] for c in order]),
                         case['frames'], case['audio'], v_controller(cands, ids), TOK['controller'])
    if ctrl['decision'] in cands:
        return dict(prediction=ctrl['decision'], route='controller', pool_size=len(ev_pool))
    if case['direct'] in cands:
        return dict(prediction=case['direct'], route='unsure_direct', pool_size=len(ev_pool))
    ass = {x['candidate']: x for x in ctrl['assessment']}
    best = sorted(cands, key=lambda c: (-ass[c]['confirmed_support'], -ass[c]['discriminating'], c))[0]
    return dict(prediction=best, route='unsure_best_assessment', pool_size=len(ev_pool))


# ------------------------------------------------------------------------------------------- driver
def sample(row, provider, method):
    client = Client(provider)
    folder = BASE / method / provider / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rp = folder / 'result.json'
        if rp.exists() and read(rp).get('status') == 'success':
            return read(rp)
        t0 = time.time()
        try:
            case = load_case(row, provider, client)
            with concurrent.futures.ThreadPoolExecutor(3) as pool:
                if method == 'A':
                    out = run_A(case, client, folder, pool)
                elif method == 'B0':
                    out = run_B0(case)
                elif method == 'B1':
                    out = run_B1(case, client, folder, pool)
                elif method == 'D':
                    out = run_D(case, client, folder, pool)
                else:
                    raise ValueError(method)
            assert out['prediction'] in row['classes']
            result = dict(id=row['id'], dataset=row['dataset'], split=row['split'], provider=provider, model=client.model, method=method,
                          status='success', version=VERSION, candidate_labels=case['cands'], direct=case['direct'], v4_prediction=case['res']['prediction'],
                          label=row['label'], elapsed_seconds=time.time() - t0, **out)
        except Exception as exc:
            result = dict(id=row['id'], provider=provider, method=method, status='error', version=VERSION, error=client.clean(exc),
                          traceback=client.clean(traceback.format_exc()), elapsed_seconds=time.time() - t0)
        save(rp, result)
        return result


def worker(provider, method, workers, ids=None):
    rows = disagreement_rows(provider)
    if ids:
        rows = [r for r in rows if r['id'] in ids]
        assert len(rows) == len(ids), 'some ids are not disagreement samples of this provider'
    (BASE / method / provider).mkdir(parents=True, exist_ok=True)
    save(BASE / method / provider / ('protocol_smoke.json' if ids else 'protocol.json'), dict(
        version=VERSION, method=method, provider=provider, samples=len(rows), workers=workers, weights=W, max_tokens=TOK,
        source='disagreement samples of outputs/reflect_debate_v4 (route != common_label)', direct_fallback='outputs/direct',
        prompts_sha256=digest(HERE / 'v5_prompts.py'), pipeline_sha256=digest(Path(__file__)), labels_not_sent=True))
    with (BASE / method / (provider + ('_smoke' if ids else '') + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        update_log(f'v5 {method} 启动：{provider}，{len(rows)} 条不一致样本{"（冒烟）" if ids else ""}，workers={workers}；输出 outputs/{VERSION}/{method}/{provider}。')
        done = {}
        for _ in range(2):
            todo = [r for r in rows if done.get(r['id']) != 'success']
            if not todo:
                break

            def one(r):
                res = sample(r, provider, method)
                print(json.dumps(dict(provider=provider, method=method, id=r['id'], status=res['status'], pred=res.get('prediction'), route=res.get('route'),
                                      error=(res.get('error') or '')[:200]), ensure_ascii=False), flush=True)
                return r['id'], res['status']
            with concurrent.futures.ThreadPoolExecutor(workers) as ex:
                done.update(dict(ex.map(one, todo)))
        ok = sum(v == 'success' for v in done.values())
        update_log(f'v5 {method} 结束：{provider}，成功 {ok}/{len(rows)}{"（冒烟）" if ids else ""}。')
        return 0 if ok == len(rows) else 1


# ------------------------------------------------------------------------------------------- report (gold used only here)
def report(provider):
    rows = disagreement_rows(provider)
    out = {}
    for method in ('B0', 'A', 'B1', 'D'):
        c = Counter()
        per = []
        for r in rows:
            p = BASE / method / provider / r['id'] / 'result.json'
            if not p.exists() or read(p).get('status') != 'success':
                c['missing'] += 1
                continue
            res = read(p)
            g = r['label']
            ok, dok, vok = res['prediction'] == g, res['direct'] == g, res['v4_prediction'] == g
            for key in ('all', r['split'], r['dataset']):
                c[key + ' n'] += 1
                c[key + ' ok'] += ok
                c[key + ' direct'] += dok
                c[key + ' v4'] += vok
            c['fix_vs_direct'] += ok and not dok
            c['break_vs_direct'] += dok and not ok
            c['fix_vs_v4'] += ok and not vok
            c['break_vs_v4'] += vok and not ok
            c['route ' + str(res.get('route') or res.get('tie'))] += 1
            if 'normalized' in res:
                c['normalized ok'] += res['normalized']['prediction'] == g
            per.append(dict(id=r['id'], gold=g, pred=res['prediction'], direct=res['direct'], v4=res['v4_prediction'], route=res.get('route') or res.get('tie')))
        out[method] = dict(counts=dict(c), per_sample=per)
        print(provider, method, {k: v for k, v in sorted(c.items())})
    # diagnostics: conformity / obstinacy, v4 debate round 1 vs A round 1 (defined against the other two experts' previous answers)
    diag = {}
    for name, base_dir, prev_key in (('v4', V4, 'reflect'), ('A', BASE / 'A', None)):
        n = conf = obst = 0
        for r in rows:
            f = (base_dir / provider / r['id'])
            d1 = {k: f / f'debate1_{k}.json' for k in ROLES}
            if not all(x.exists() for x in d1.values()):
                continue
            prev = {k: read(V4 / provider / r['id'] / f'reflect_{k}.json')['output']['answer'] for k in ROLES}
            now = {k: read(d1[k])['output']['answer'] for k in ROLES}
            for k in ROLES:
                others = {prev[o] for o in ROLES if o != k} - {prev[k]}
                if not others:
                    continue
                n += 1
                conf += now[k] in others
                obst += now[k] == prev[k]
        diag[name] = dict(n=n, conformity=conf / n if n else None, obstinacy=obst / n if n else None)
    out['diagnostics_round1'] = diag
    print(provider, 'round-1 diagnostics', diag)
    save(ROOT / 'metrics' / f'{VERSION}_{provider}.json', out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['run', 'report'])
    ap.add_argument('--provider', choices=['gpt', 'gemini'], required=True)
    ap.add_argument('--method', choices=['A', 'B0', 'B1', 'D'])
    ap.add_argument('--ids', nargs='*')
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    if a.mode == 'run':
        sys.exit(worker(a.provider, a.method, a.workers, a.ids))
    report(a.provider)


if __name__ == '__main__':
    main()
