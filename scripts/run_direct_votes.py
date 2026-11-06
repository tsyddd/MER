"""Three fresh independent Direct runs on the v4 disagreement samples, to test whether voting over several Direct runs beats a single Direct.

Same code path as every earlier Direct run (engine.sample(row, provider, <mode>): 8 frames, audio for Gemini only, temperature 0, one
completed response per run). Each run goes to its own directory outputs/<mode>/<provider>/<id> (modes direct_vote1..3), so the saved
Direct (outputs/direct) and the first re-run (outputs/direct_rerun) are never touched; together there are five runs per sample.
Gold labels are never sent. Server (Linux) only.

Usage: python scripts/run_direct_votes.py --provider gemini|gpt [--workers 4]
"""
import argparse
import concurrent.futures
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import sample, update_log  # noqa: E402

V4 = ROOT / 'outputs' / 'reflect_debate_v4'
MODES = ['direct_vote1', 'direct_vote2', 'direct_vote3']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gpt', 'gemini'], required=True)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    rows = []
    for s in ['validation', 'train']:
        rows += [json.loads(l) for l in (ROOT / 'data/manifests' / (s + '.jsonl')).read_text().splitlines() if l.strip()]
    rows = [r for r in rows if json.loads((V4 / a.provider / r['id'] / 'result.json').read_text())['route'] != 'common_label']
    update_log(f'Direct 三次独立重跑启动（投票实验）：{a.provider}，v4 不一致样本 {len(rows)} 条，模式 {",".join(MODES)}，workers={a.workers}；输出 outputs/direct_vote{{1,2,3}}/{a.provider}/<id>，原 Direct 与 direct_rerun 不改。')
    ok_total = 0
    for mode in MODES:
        status = {}
        for _ in range(2):
            todo = [r for r in rows if status.get(r['id']) != 'success']
            if not todo:
                break

            def one(r):
                res = sample(r, a.provider, mode)
                print(json.dumps(dict(provider=a.provider, mode=mode, id=r['id'], status=res['status'], error=(res.get('error') or '')[:200]), ensure_ascii=False), flush=True)
                return r['id'], res['status']
            with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
                status.update(dict(pool.map(one, todo)))
        ok = sum(v == 'success' for v in status.values())
        ok_total += ok
        update_log(f'Direct 投票实验 {mode} 结束：{a.provider}，成功 {ok}/{len(rows)}。')
    sys.exit(0 if ok_total == 3 * len(rows) else 1)


if __name__ == '__main__':
    main()
