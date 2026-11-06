"""Direct baseline (original media + subtitle -> one label, no graph/experts) on all 400 samples (validation 80 + train 320).

Uses the same engine.sample(row, provider, 'direct') as the existing validation Direct runs (8 frames; audio for Gemini only),
so the 80 validation results are cached and skipped; only the 320 train samples are new. Gold labels are never sent; they are
read only when the accuracy is computed at the end. Server (Linux) only.

Usage: python scripts/run_direct_400.py --provider gpt|gemini [--workers 4]
"""
import argparse
import concurrent.futures
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import sample, save, update_log  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gpt', 'gemini'], required=True)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    rows = []
    for s in ['validation', 'train']:
        rows += [dict(json.loads(l), split=s) for l in (ROOT / 'data/manifests' / (s + '.jsonl')).read_text().splitlines() if l.strip()]
    assert len(rows) == len({r['id'] for r in rows}) == 400
    update_log(f'Direct 400 条启动：{a.provider}，验证 80 条缓存复用 + 训练 320 条新跑，workers={a.workers}；输出 outputs/direct/{a.provider}/<id>。')
    status = {}
    for rnd in range(2):  # second pass retries errors
        todo = [r for r in rows if status.get(r['id']) != 'success']
        if not todo:
            break

        def one(r):
            res = sample(r, a.provider, 'direct')
            print(json.dumps(dict(provider=a.provider, id=r['id'], status=res['status'], stage=res.get('stage'), error=(res.get('error') or '')[:200]), ensure_ascii=False), flush=True)
            return r['id'], res['status']
        with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
            status.update(dict(pool.map(one, todo)))
    c = Counter()
    for r in rows:
        res = json.loads((ROOT / 'outputs/direct' / a.provider / r['id'] / 'result.json').read_text())
        for key in ['all', r['split'], r['dataset']]:
            c[key + ' n'] += 1
            if res['status'] == 'success':
                c[key + ' valid'] += 1
                c[key + ' correct'] += res['prediction'] == r['label']
    out = dict(provider=a.provider, counts=dict(c))
    save(ROOT / 'metrics' / f'direct_400_{a.provider}.json', out)
    ok = sum(v == 'success' for v in status.values())
    update_log(f'Direct 400 条结束：{a.provider}，成功 {ok}/400；全部 {c["all correct"]}/{c["all n"]}，验证 {c["validation correct"]}/{c["validation n"]}，训练 {c["train correct"]}/{c["train n"]}（失败样本按无效计）。指标 metrics/direct_400_{a.provider}.json。')
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0 if ok == 400 else 1)


if __name__ == '__main__':
    main()
