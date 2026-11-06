"""Re-run the Direct baseline once more on the v4 disagreement samples to measure its own run-to-run noise.

Same code path as the original Direct runs (engine.sample(row, provider, 'direct') protocol: 8 frames, audio for Gemini only,
temperature 0) but written to a separate directory (outputs/direct_rerun) so the saved Direct results are never touched.
Gold labels are never sent; they are read only when the comparison is computed at the end. Server (Linux) only.

Usage: python scripts/run_direct_rerun.py --provider gemini|gpt [--workers 4]
"""
import argparse
import concurrent.futures
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import sample, save, update_log  # noqa: E402

V4 = ROOT / 'outputs' / 'reflect_debate_v4'
MODE = 'direct_rerun'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gpt', 'gemini'], required=True)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    rows = []
    for s in ['validation', 'train']:
        rows += [json.loads(l) for l in (ROOT / 'data/manifests' / (s + '.jsonl')).read_text().splitlines() if l.strip()]
    rows = [r for r in rows if json.loads((V4 / a.provider / r['id'] / 'result.json').read_text())['route'] != 'common_label']
    update_log(f'Direct 重跑启动（测噪声）：{a.provider}，v4 不一致样本 {len(rows)} 条，workers={a.workers}；输出 outputs/{MODE}/{a.provider}/<id>，原 Direct 结果不改。')
    status = {}
    for _ in range(2):
        todo = [r for r in rows if status.get(r['id']) != 'success']
        if not todo:
            break

        def one(r):
            res = sample(r, a.provider, MODE)
            print(json.dumps(dict(provider=a.provider, id=r['id'], status=res['status'], error=(res.get('error') or '')[:200]), ensure_ascii=False), flush=True)
            return r['id'], res['status']
        with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
            status.update(dict(pool.map(one, todo)))
    ok = sum(v == 'success' for v in status.values())
    update_log(f'Direct 重跑结束：{a.provider}，成功 {ok}/{len(rows)}。')
    sys.exit(0 if ok == len(rows) else 1)


if __name__ == '__main__':
    main()
