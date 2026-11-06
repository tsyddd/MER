"""R2-MAD test run on the v4 disagreement samples of the old 400 (Gemini 62, GPT 55), one variant at a time:
  n0 = control: same flow (no reflection, 2 debate rounds, static summarizer) WITHOUT retrieval, no state summaries
  n1 / n2 / n3 = R2-MAD with n retrieved cases per expert per round (candidate pool = top-3n)
Flow per sample: Round-0 outputs (read from the saved v4 run, no call) -> [S0] -> debate 1 (retrieval) -> all three answers equal? stop
  -> [S1] -> debate 2 (retrieval) -> equal? stop -> static summarizer (the v4 summary prompt without the reflection stage).
Debate answers must be inside the Round-0 label union. Gold labels are read only by `report`.

Usage (server, project root):
  CUDA_VISIBLE_DEVICES=1 .venv/bin/python versions/v6/run_rmad.py run --provider gemini|gpt --variant n0|n1|n2|n3 [--workers 2] [--smoke N]
  .venv/bin/python versions/v6/run_rmad.py report [--provider gemini|gpt]
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import threading
import time
import traceback
import numpy as np
from common import (LIMITS, OUT, ROLES, TOKENS, V4_OUT, Client, compact, consensus_ratio, labels_of, prepare_frames, question_text, read, save, test_rows,
                    update_log, v4, v4_disagreement_ids)
import prompts_v6 as P6
from build_memory import run_debate_round, summarize_state
from captions import get_caption

TEST = OUT / 'test'
_EMBEDDER = None
_MEMORY = {}
_LOAD_LOCK = threading.Lock()  # worker threads must not load bge-m3 / the memory concurrently (meta-tensor / import races)
_ENC_LOCK = threading.Lock()


class _LockedEmbedder:
    def __init__(self, inner):
        self.inner = inner

    def encode(self, texts, batch=8):
        with _ENC_LOCK:
            return self.inner.encode(texts, batch)


def embedder():
    global _EMBEDDER
    with _LOAD_LOCK:
        if _EMBEDDER is None:
            from embedder import Embedder
            _EMBEDDER = _LockedEmbedder(Embedder())
    return _EMBEDDER


def memory(provider):
    with _LOAD_LOCK:
        if provider not in _MEMORY:
            from memory import Memory
            _MEMORY[provider] = Memory(OUT / 'memory' / provider)
    return _MEMORY[provider]


def load_test_payloads(row, provider):
    client = Client(provider)
    info = prepare_frames(row)
    audio = row['audio'] if client.config.get('audio_supported') else None
    entry = v4.graph_entries()[row['id']]
    graph = read(entry['path'])
    organization = read(V4_OUT / provider / row['id'] / 'organization.json')['output']['text']
    return client, info, audio, v4.role_payloads(row, graph, organization, info, audio)


def sample(row, provider, variant):
    n = int(variant[1:])
    folder = TEST / provider / variant / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    result_path = folder / 'result.json'
    if result_path.exists() and read(result_path).get('status') == 'success':
        return read(result_path)
    shared = TEST / provider / 'shared' / row['id']
    shared.mkdir(parents=True, exist_ok=True)
    classes = row['classes']
    subtitle = row.get('subtitle', '').strip()
    client, info, audio, payloads = load_test_payloads(row, provider)
    r0 = {role: read(V4_OUT / provider / row['id'] / f'r0_{role}.json')['output'] for role in ROLES}
    union = sorted({l for role in ROLES for l in labels_of(r0[role])}, key=classes.index)
    question = question_text(row, get_caption(row)) if n else None
    history = {role: dict(r0=r0[role]) for role in ROLES}
    state, prev_state, summary, ratio = r0, None, None, consensus_ratio(r0)
    rounds, retrieved_log = 0, {}
    final, route = None, None
    for rd in (1, 2):
        extra = None
        if n:
            tag = f'state{rd - 1}'
            summary = summarize_state(shared if rd == 1 else folder, tag, client, classes, question, state, prev_state, summary, ratio)  # S0 depends only on Round 0 (shared by n1-n3)
            mem = memory(provider)
            emb = embedder()
            texts = {role: f'{question}\n{compact(state[role])}\n{summary}' for role in ROLES}
            qvecs = dict(zip(ROLES, emb.encode([texts[r] for r in ROLES])))
            pvecs = dict(zip(ROLES, emb.encode([compact(state[r]) for r in ROLES])))
            plan = {}
            for role in ROLES:
                sel, cand, _ = mem.retrieve(role, row['dataset'], qvecs[role], n, ratio)
                rel = mem.peer_reliability(cand, {o: pvecs[o] for o in ROLES if o != role})
                plan[role] = (sel, rel)
            retrieved_log[f'debate{rd}'] = {role: dict(cases=[mem.records[i]['db_id'] for i in plan[role][0]], reliability=plan[role][1]) for role in ROLES}

            def extra(role, payload, plan=plan, mem=mem):
                sel, rel = plan[role]
                payload['retrieved_examples'] = [dict(example_question=mem.records[i]['question'], example_solution=mem.records[i]['solution'],
                                                      example_agent_response=mem.records[i]['response'],
                                                      example_agent_stance_changed=('不适用（第0轮）' if mem.records[i]['stance_changed'] is None else mem.records[i]['stance_changed']),
                                                      example_agent_response_correctness=('该回答正确。' if mem.records[i]['correct'] else '该回答不正确。')) for i in sel]
                payload['other_experts'] = {o: (dict(v, reliability=rel[o]) if rel.get(o) else v) for o, v in payload['other_experts'].items()}
                return payload
        new = run_debate_round(folder, rd, client, row, payloads, info, audio, state, union, lambda role: P6.debate(role, classes, memory=bool(n)), extra)
        rounds = rd
        for role in ROLES:
            history[role][f'debate{rd}'] = new[role]
        prev_state, state, ratio = state, new, consensus_ratio(new)
        if len({new[r]['answer'] for r in ROLES}) == 1:
            route, final = 'debate_consensus', new[ROLES[0]]['answer']
            break
    answers = {r: state[r]['answer'] for r in ROLES}
    summary_out = None
    if final is None:
        route = 'summary'
        summary_out = v4.call_stage(folder, 'summary', client, P6.summarizer(classes),
                                    dict(v4.media_payload(row, info, audio), expert_history=history, final_single_answers=answers, candidate_labels=union),
                                    info['frames'], audio, v4.validator('summary', None, classes, audio, subtitle), TOKENS['summary'])
        final = summary_out['answer']
    result = dict(status='success', id=row['id'], dataset=row['dataset'], provider=provider, variant=variant, route=route, prediction=final, debate_rounds=rounds,
                  union=union, r0_answers={r: r0[r]['answer'] for r in ROLES}, debate_answers={f'debate{d}': {r: history[r][f'debate{d}']['answer'] for r in ROLES} for d in range(1, rounds + 1)},
                  retrieved=retrieved_log)
    save(result_path, result)
    return result


def cmd_run(a):
    ids = v4_disagreement_ids(a.provider)
    rows_by_id = test_rows()
    rows = [rows_by_id[i] for i in ids]
    if a.smoke:
        rows = rows[:a.smoke]
    update_log(f'R²-MAD 测试启动：{a.provider}/{a.variant}，v4 不一致样本 {len(rows)} 条；请求级并发 {LIMITS[a.provider]}；输出 outputs/v6_rmad/test/{a.provider}/{a.variant}；smoke={a.smoke}。')
    ok, errors = 0, []

    def one(r):
        try:
            sample(r, a.provider, a.variant)
            return r['id'], None
        except Exception as exc:  # noqa: BLE001
            return r['id'], f'{type(exc).__name__}: {str(exc)[:240]}\n' + traceback.format_exc()[-600:]
    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        for i, (rid, err) in enumerate(pool.map(one, rows), 1):
            ok += err is None
            if err:
                errors.append((rid, err))
            if i % 10 == 0:
                print(f'[{time.strftime("%T")}] {i}/{len(rows)} ok={ok} err={len(errors)}', flush=True)
    update_log(f'R²-MAD 测试结束：{a.provider}/{a.variant}，成功 {ok}/{len(rows)}，失败 {len(errors)}。')
    for e in errors:
        print('ERR', e)


def cmd_report(a):
    rows_by_id = test_rows()
    out = {}
    for provider in ([a.provider] if a.provider else ['gemini', 'gpt']):
        ids = v4_disagreement_ids(provider)
        res = {'n_samples': len(ids)}
        for variant in ['n0', 'n1', 'n2', 'n3']:
            rs = {i: read(TEST / provider / variant / i / 'result.json') for i in ids if (TEST / provider / variant / i / 'result.json').exists()}
            if not rs:
                continue
            ok = sum(r['prediction'] == rows_by_id[i]['label'] for i, r in rs.items())
            routes = {}
            for r in rs.values():
                routes[r['route']] = routes.get(r['route'], 0) + 1
            v4_ok = sum(read(V4_OUT / provider / i / 'result.json')['prediction'] == rows_by_id[i]['label'] for i in rs)
            res[variant] = dict(done=len(rs), correct=ok, routes=routes, v4_correct_same_samples=v4_ok,
                                by_dataset={ds: dict(n=sum(1 for i in rs if rows_by_id[i]['dataset'] == ds), correct=sum(1 for i, r in rs.items() if rows_by_id[i]['dataset'] == ds and r['prediction'] == rows_by_id[i]['label']))
                                            for ds in ('MER2024', 'MELD')})
        out[provider] = res
    save(ROOT_METRICS / 'v6_rmad_test.json', out)
    print(json.dumps(out, ensure_ascii=False, indent=1))


from common import ROOT  # noqa: E402
ROOT_METRICS = ROOT / 'metrics'

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['run', 'report'])
    ap.add_argument('--provider', choices=['gemini', 'gpt'])
    ap.add_argument('--variant', choices=['n0', 'n1', 'n2', 'n3'])
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--smoke', type=int, default=0)
    a = ap.parse_args()
    if a.cmd == 'run':
        assert a.provider and a.variant
        cmd_run(a)
    else:
        cmd_report(a)
