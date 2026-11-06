"""R2-MAD step 1: training-sample pool -> frozen Gemini graph -> Round-0 of three experts for Gemini and GPT -> route on the Round-0 answers.

Pool = all samples of the 5-model evaluation folder that pass the media filter, minus the old 400 (MER2024 969 + MELD 2408).
To cap the cost, the pool is processed in a fixed seeded random order, in chunks, and a dataset stops as soon as BOTH providers have
QUOTA (200) disagreement samples in it; the training set of a provider is then its first QUOTA disagreement samples in that order
(a uniform random subset of its disagreement pool). Disagreement = the three Round-0 answer sets have no unique common label.
No reflection stage. Gold labels are never sent to a model and are not read here.

Usage (server, project root):
  .venv/bin/python versions/v6/pool.py run [--smoke] [--quota 200] [--chunk 40] [--workers 8]
  .venv/bin/python versions/v6/pool.py status
"""
from __future__ import annotations
import argparse
import concurrent.futures
import fcntl
import json
import shutil
import time
import traceback
from common import (DATASETS, GRAPH_POOL, OUT, ROLES, ROOT, TOKENS, Client, digest, labels_of, pool_rows, prepare_frames, read, save, update_log, v4)
from engine import sample as engine_sample

POOL = OUT / 'pool'
PROVIDERS = ['gemini', 'gpt']


def ensure_graph(row):
    folder = GRAPH_POOL / row['id']
    entry, dst = folder / 'entry.json', folder / 'graph.json'
    if entry.exists():
        e = read(entry)
        assert digest(dst) == e['sha256'], 'Frozen graph changed'
        return read(dst)
    res = engine_sample(row, 'gemini', 'ppct')  # original PPCT flow (labels not sent); graph.json is written before the final stage
    if res['status'] != 'success':
        raise RuntimeError('graph generation failed: ' + str(res.get('error') or res.get('stage'))[:200])
    src = ROOT / 'outputs' / 'ppct' / 'gemini' / row['id'] / 'graph.json'
    graph = read(src)
    assert graph.get('nodes'), 'empty graph'
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    save(entry, dict(source=str(src), sha256=digest(dst), source_provider='gemini', source_model=Client('gemini').model))
    return graph


def r0_sample(row, provider, graph):
    folder = POOL / provider / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    done = folder / 'r0_summary.json'
    if done.exists():
        return read(done)
    classes = row['classes']
    client = Client(provider)
    info = prepare_frames(row)
    audio = row['audio'] if client.config.get('audio_supported') else None
    subtitle = row.get('subtitle', '').strip()
    organization = v4.get_organization(folder, provider, row, client, graph)
    payloads = v4.role_payloads(row, graph, organization, info, audio)
    with concurrent.futures.ThreadPoolExecutor(3) as pool:
        futures = {role: pool.submit(v4.call_stage, folder, f'r0_{role}', client, v4.prompts.expert(role, classes), payloads[role], info['frames'], audio,
                                     v4.validator('r0', role, classes, audio, subtitle), TOKENS['r0'], None) for role in ROLES}
        r0 = {role: f.result() for role, f in futures.items()}
    sets = {role: sorted(labels_of(r0[role]), key=classes.index) for role in ROLES}
    common = set.intersection(*[set(s) for s in sets.values()])
    result = dict(status='success', id=row['id'], dataset=row['dataset'], provider=provider, sets=sets, common=sorted(common),
                  disagree=len(common) != 1, answers={role: r0[role]['answer'] for role in ROLES})
    save(done, result)
    return result


def process(row):
    errors = {}
    try:
        graph = ensure_graph(row)
    except Exception as exc:  # noqa: BLE001
        msg = f'graph: {type(exc).__name__}: {str(exc)[:300]}'
        return {p: dict(status='error', error=msg) for p in PROVIDERS}
    out = {}
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        futures = {p: pool.submit(r0_sample, row, p, graph) for p in PROVIDERS}
        for p, f in futures.items():
            try:
                out[p] = f.result()
            except Exception as exc:  # noqa: BLE001
                out[p] = dict(status='error', error=f'{type(exc).__name__}: {str(exc)[:300]}')
                errors[p] = traceback.format_exc()[-1500:]
    return out


def ledger(row, result):
    with (POOL / 'ledger.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with (POOL / 'ledger.jsonl').open('a') as f:
            f.write(json.dumps(dict(id=row['id'], dataset=row['dataset'], time=time.strftime('%F %T'),
                                    **{p: (dict(disagree=r['disagree'], answers=r['answers']) if r.get('status') == 'success' else dict(error=r.get('error')))
                                       for p, r in result.items()}), ensure_ascii=False) + '\n')


def tally(order, upto):
    """Per provider: processed / success / disagreement counts and the first-QUOTA ids, over the processed prefix of one dataset."""
    out = {p: dict(success=0, disagree=0, ids=[], errors=0) for p in PROVIDERS}
    for row in order[:upto]:
        for p in PROVIDERS:
            f = POOL / p / row['id'] / 'r0_summary.json'
            if f.exists():
                out[p]['success'] += 1
                if read(f)['disagree']:
                    out[p]['disagree'] += 1
                    out[p]['ids'].append(row['id'])
            else:
                out[p]['errors'] += 1
    return out


def run(args):
    POOL.mkdir(parents=True, exist_ok=True)
    orders = {ds: pool_rows(ds) for ds in DATASETS}
    if args.smoke:
        orders = {'MER2024': orders['MER2024'][:3], 'MELD': orders['MELD'][:2]}
    pos = {ds: 0 for ds in orders}
    active = set(orders)
    update_log(f'R²-MAD 训练池筛选启动：候选池 {", ".join(f"{d} {len(o)}" for d, o in orders.items())}，随机顺序种子 42，每批每数据集 {args.chunk} 条，'
               f'两个模型都攒够 {args.quota} 条不一致样本即停；请求级并发 Gemini {LIMITS_TEXT}；输出 outputs/v6_rmad/pool，冻结图谱 data/gemini_graph_pool_v6；smoke={args.smoke}。')
    while active:
        batch = []
        for ds in sorted(active):
            part = orders[ds][pos[ds]:pos[ds] + args.chunk]
            pos[ds] += len(part)
            batch += part
        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            for row, res in zip(batch, pool.map(process, batch)):
                ledger(row, res)
        for ds in sorted(active):
            t = tally(orders[ds], pos[ds])
            line = ' | '.join(f'{p}: 成功 {t[p]["success"]}/{pos[ds]}，不一致 {t[p]["disagree"]}' for p in PROVIDERS)
            print(f'[{time.strftime("%T")}] {ds} 已处理 {pos[ds]}/{len(orders[ds])}：{line}', flush=True)
            if (not args.smoke and min(t[p]['disagree'] for p in PROVIDERS) >= args.quota) or pos[ds] >= len(orders[ds]):
                active.discard(ds)
    selection = {}
    for ds, order in orders.items():
        t = tally(order, pos[ds])
        selection[ds] = dict(processed=pos[ds], pool=len(order), **{p: dict(success=t[p]['success'], disagree=t[p]['disagree'], selected=t[p]['ids'][:args.quota]) for p in PROVIDERS})
    save(POOL / ('selection_smoke.json' if args.smoke else 'selection.json'), selection)
    update_log('R²-MAD 训练池筛选结束：' + '；'.join(f'{ds} 处理 {s["processed"]}，Gemini 不一致 {s["gemini"]["disagree"]}、GPT 不一致 {s["gpt"]["disagree"]}' for ds, s in selection.items()) + f'；smoke={args.smoke}。')


def status(_):
    orders = {ds: pool_rows(ds) for ds in DATASETS}
    for ds, order in orders.items():
        done = [r for r in order if all((POOL / p / r['id'] / 'r0_summary.json').exists() for p in PROVIDERS)]
        t = tally(order, len(done))
        print(ds, 'both done', len(done), {p: (t[p]['success'], t[p]['disagree']) for p in PROVIDERS})


LIMITS_TEXT = ''

if __name__ == '__main__':
    from common import LIMITS
    LIMITS_TEXT = f'{LIMITS["gemini"]}、GPT {LIMITS["gpt"]}'
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['run', 'status'])
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--quota', type=int, default=200)
    ap.add_argument('--chunk', type=int, default=40)
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    (run if a.cmd == 'run' else status)(a)
