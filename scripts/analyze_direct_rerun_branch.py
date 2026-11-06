"""只读诊断：不一致分支上 Direct 两次运行的稳定性，以及“改 Direct”的上限与风险（F8）。

读 metrics/direct_rerun_117.json 与 metrics/reflect_debate_v4_{gemini,gpt}_all.json，写 metrics/direct_rerun_branch_diagnostic.json。
真实标签只用于评估；没有模型调用；开发集探索性统计。
Usage: python -X utf8 -I scripts/analyze_direct_rerun_branch.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    rr = json.load(open(ROOT / 'metrics/direct_rerun_117.json', encoding='utf8'))
    out = {}
    for prov in ['gemini', 'gpt']:
        ps = {p['id']: p for p in json.load(open(ROOT / f'metrics/reflect_debate_v4_{prov}_all.json', encoding='utf8'))['per_sample']}
        c = Counter()
        for r in rr[prov]:
            p, g = ps[r['id']], r['gold']
            union = {(p['reflect'][e] or [None])[0] for e in p['reflect']}
            ok1, ok2 = r['run1'] == g, r['run2'] == g
            c['n'] += 1
            c['run1 ok'] += ok1
            c['run2 ok'] += ok2
            c['runs agree'] += r['run1'] == r['run2']
            c['either ok'] += ok1 or ok2
            c['both ok'] += ok1 and ok2
            c['run1 wrong & gold in reflect primaries'] += (not ok1) and g in union
            c['run1 wrong & gold not in reflect primaries'] += (not ok1) and g not in union
            c['run1 in reflect primaries'] += r['run1'] in union
        out[prov] = dict(c)
        print(prov, dict(c))
    (ROOT / 'metrics/direct_rerun_branch_diagnostic.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')


if __name__ == '__main__':
    main()
