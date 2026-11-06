"""R2-MAD step 3: build the experience memory of one provider from its training set T (<= 400 disagreement samples, see pool.py).

For every training sample: Round-0 outputs (reused from the pool step) -> summary S0 -> debate 1 (no experience) -> summary S1 -> debate 2
(no experience); all rounds are forced (no early stop). Then 3 experts x 3 rounds = 9 records per sample (see memory.py for key / value).
Gold labels are read only here, to mark correctness and to fill the example value; they are never sent to a model.

Usage (server, project root; GPU only for `embed`):
  .venv/bin/python versions/v6/build_memory.py debates --provider gemini|gpt [--workers 2] [--ids-smoke N]
  CUDA_VISIBLE_DEVICES=1 .venv/bin/python versions/v6/build_memory.py embed --provider gemini|gpt
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import re
import time
import numpy as np
from common import (DATASETS, GRAPH_POOL, LIMITS, OUT, ROLES, TOKENS, Client, compact, consensus_ratio, labels_of, pool_rows, prepare_frames, question_text,
                    read, save, update_log, v4, nonempty)
import prompts_v6 as P6
from captions import get_caption
from memory import value_text

POOL = OUT / 'pool'


def state_validate(v):
    assert isinstance(v, dict) and set(v) == {'summary'} and isinstance(v['summary'], str), 'summary object required'
    s = v['summary'].strip()
    assert s.startswith('Dynamic:') and 'Insight:' in s and len(s) <= 900, 'summary must be "Dynamic: ... Insight: ..."'


def sanitize(text, classes):
    """The state summary must not name labels (the prompt asks for it; this makes it certain)."""
    for c in classes:
        text = re.sub(re.escape(c), '某标签', text, flags=re.I)
    return text


def summarize_state(folder, tag, client, classes, question, outputs, prev_outputs, prev_summary, ratio):
    agents = []
    for i, role in enumerate(ROLES):
        a = dict(index=i, answer=outputs[role]['answer'], open_emotion=outputs[role]['open_emotion'], reason=str(outputs[role]['reason'])[:400])
        if prev_outputs is not None:
            a['previous_answer'] = prev_outputs[role]['answer']
            a['stance_changed'] = str(prev_outputs[role]['answer'] != outputs[role]['answer']).lower()
        agents.append(a)
    payload = dict(question=question, previous_summary=prev_summary or 'None', agents=agents, consensus_ratio=f'{ratio:.2f}')
    out = v4.call_stage(folder, tag, client, P6.STATE, payload, [], None, state_validate, TOKENS['state'])
    return sanitize(out['summary'].strip(), classes)


def load_pool_payloads(row, provider):
    """Role payloads of a pool sample (frozen graph + organization text of this provider, both made in pool.py)."""
    client = Client(provider)
    info = prepare_frames(row)
    audio = row['audio'] if client.config.get('audio_supported') else None
    graph = read(GRAPH_POOL / row['id'] / 'graph.json')
    organization = read(POOL / provider / row['id'] / 'organization.json')['output']['text']
    return client, info, audio, v4.role_payloads(row, graph, organization, info, audio)


def run_debate_round(folder, rd, client, row, payloads, info, audio, state, union, system_for, extra=None):
    """One debate round: every expert answers once (same validator, fallback and format repair as v4). `extra(role)` adds payload fields."""
    classes = row['classes']
    subtitle = row.get('subtitle', '').strip()
    pool = concurrent.futures.ThreadPoolExecutor(3)

    def fb_for(role):
        def fb(error):
            prev = state[role]
            return dict({k: prev[k] for k in v4.BASE_KEYS}, answer=prev['answer'], changed=False, adopted_evidence=[], response_to_others=[], fallback=True, fallback_reason=error)
        return fb
    futures = {}
    for role in ROLES:
        payload = dict(payloads[role], round=rd, your_previous_output=state[role], candidate_labels=union,
                       other_experts={o: state[o] for o in ROLES if o != role})
        if extra:
            payload = extra(role, payload)
        futures[role] = pool.submit(v4.call_stage, folder, f'debate{rd}_{role}', client, system_for(role), payload, info['frames'], audio,
                                    v4.validator('debate', role, classes, audio, subtitle, union), TOKENS['debate'], fb_for(role))
    out = {role: f.result() for role, f in futures.items()}
    pool.shutdown()
    return out


def train_sample(row, provider):
    folder = OUT / 'train' / provider / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    done = folder / 'train_result.json'
    if done.exists():
        return read(done)
    classes = row['classes']
    client, info, audio, payloads = load_pool_payloads(row, provider)
    r0 = {role: read(POOL / provider / row['id'] / f'r0_{role}.json')['output'] for role in ROLES}
    union = sorted({l for role in ROLES for l in labels_of(r0[role])}, key=classes.index)
    question = question_text(row, get_caption(row))
    c0 = consensus_ratio(r0)
    s0 = summarize_state(folder, 'state0', client, classes, question, r0, None, None, c0)
    d1 = run_debate_round(folder, 1, client, row, payloads, info, audio, r0, union, lambda role: P6.debate(role, classes))
    c1 = consensus_ratio(d1)
    s1 = summarize_state(folder, 'state1', client, classes, question, d1, r0, s0, c1)
    d2 = run_debate_round(folder, 2, client, row, payloads, info, audio, d1, union, lambda role: P6.debate(role, classes))
    result = dict(status='success', id=row['id'], dataset=row['dataset'], provider=provider, question=question, union=union, c0=c0, c1=c1, c2=consensus_ratio(d2),
                  s0=s0, s1=s1, answers=dict(r0={r: r0[r]['answer'] for r in ROLES}, d1={r: d1[r]['answer'] for r in ROLES}, d2={r: d2[r]['answer'] for r in ROLES}))
    save(done, result)
    return result


def selected_rows(provider, smoke=0):
    sel = read(POOL / 'selection.json') if not smoke else read(POOL / 'selection_smoke.json')
    lookup = {r['id']: r for ds in DATASETS for r in pool_rows(ds)}
    rows = [lookup[i] for ds in DATASETS for i in sel[ds][provider]['selected']]
    return rows[:smoke] if smoke else rows


def cmd_debates(a):
    rows = selected_rows(a.provider, a.smoke)
    update_log(f'R²-MAD 建库启动：{a.provider}，训练样本 {len(rows)} 条，第 0 轮复用，强制 2 轮辩论（无经验）+ 两次摘要；请求级并发 {LIMITS[a.provider]}；输出 outputs/v6_rmad/train/{a.provider}。')
    ok, errors = 0, []

    def one(r):
        try:
            train_sample(r, a.provider)
            return r['id'], None
        except Exception as exc:  # noqa: BLE001
            return r['id'], f'{type(exc).__name__}: {str(exc)[:240]}'
    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        for i, (rid, err) in enumerate(pool.map(one, rows), 1):
            ok += err is None
            if err:
                errors.append((rid, err))
            if i % 10 == 0:
                print(f'[{time.strftime("%T")}] {i}/{len(rows)} ok={ok} err={len(errors)}', flush=True)
    update_log(f'R²-MAD 建库辩论结束：{a.provider}，成功 {ok}/{len(rows)}，失败 {len(errors)}。')
    for e in errors:
        print('ERR', e)


def records_for(row, provider):
    """The 9 records of one training sample (gold label read here)."""
    folder = OUT / 'train' / provider / row['id']
    res = read(folder / 'train_result.json')
    r0 = {role: read(POOL / provider / row['id'] / f'r0_{role}.json')['output'] for role in ROLES}
    d1 = {role: read(folder / f'debate1_{role}.json')['output'] for role in ROLES}
    d2 = {role: read(folder / f'debate2_{role}.json')['output'] for role in ROLES}
    states = [r0, d1, d2]
    summaries = [res['s0'], res['s1']]
    ratios = [res['c0'], res['c1']]
    q = res['question']
    gold = row['label']
    out = []
    for role in ROLES:
        for r in range(3):
            cur = states[r][role]
            correct = cur['answer'] == gold
            key = q if r == 0 else f'{q}\n{compact(states[r - 1][role])}\n{summaries[r - 1]}'
            changed = None if r == 0 else bool(cur['answer'] != states[r - 1][role]['answer'])
            out.append(dict(db_id=f'{row["id"]}|{r}|{role}', qid=row['id'], dataset=row['dataset'], role=role, round=r, key_text=key,
                            value_text=value_text(q, gold, compact(cur), changed, correct), resp_text=compact(cur),
                            prev_consensus=-1.0 if r == 0 else ratios[r - 1], correct=bool(correct), solution=gold, stance_changed=changed,
                            question=q, response=compact(cur)))
    return out


def cmd_embed(a):
    from embedder import Embedder
    rows = selected_rows(a.provider, a.smoke)
    recs = []
    skipped = []
    for r in rows:
        if not (OUT / 'train' / a.provider / r['id'] / 'train_result.json').exists():
            skipped.append(r['id'])
            continue
        recs += records_for(r, a.provider)
    emb = Embedder()
    folder = OUT / 'memory' / a.provider
    folder.mkdir(parents=True, exist_ok=True)
    keys = emb.encode([x['key_text'] for x in recs])
    values = emb.encode([x['value_text'] for x in recs])
    resps = emb.encode([x['resp_text'] for x in recs])
    np.savez(folder / 'embeddings.npz', ids=np.array([x['db_id'] for x in recs]), keys=keys.astype(np.float16), values=values.astype(np.float16), responses=resps.astype(np.float16))
    (folder / 'records.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in recs), encoding='utf-8')
    stats = dict(samples=len(rows) - len(skipped), skipped=skipped, records=len(recs), correct=sum(x['correct'] for x in recs),
                 by_round={r: sum(1 for x in recs if x['round'] == r) for r in range(3)})
    save(folder / 'stats.json', stats)
    update_log(f'R²-MAD 经验库写入：{a.provider}，样本 {stats["samples"]}，记录 {stats["records"]}（bge-m3 向量已存），跳过 {len(skipped)}。')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['debates', 'embed'])
    ap.add_argument('--provider', required=True, choices=['gemini', 'gpt'])
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--smoke', type=int, default=0)
    a = ap.parse_args()
    (cmd_debates if a.cmd == 'debates' else cmd_embed)(a)
