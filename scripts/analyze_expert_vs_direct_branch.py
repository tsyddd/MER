"""只读诊断（F9）：不一致分支上，三位“主责某模态”的专家与 Direct 的偏离、neutral 过度预测，以及全 400 条的单专家准确率。

读 metrics/direct_rerun_117.json（Direct run1）与 metrics/reflect_debate_v4_{gemini,gpt}_all.json。
真实标签只用于评估；无模型调用；开发集探索性统计。
Usage: python -X utf8 -I scripts/analyze_expert_vs_direct_branch.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP = ['graph', 'audio_subtitle', 'image']


def main():
    rr = json.load(open(ROOT / 'metrics/direct_rerun_117.json', encoding='utf8'))
    out = {}
    for prov in ['gemini', 'gpt']:
        full = json.load(open(ROOT / f'metrics/reflect_debate_v4_{prov}_all.json', encoding='utf8'))
        ps = {p['id']: p for p in full['per_sample']}
        c = Counter()
        for r in rr[prov]:
            p, g, d = ps[r['id']], r['gold'], r['run1']
            c['n'] += 1
            c['gold neutral'] += g == 'neutral'
            c['Direct pred neutral'] += d == 'neutral'
            c['Direct neutral wrong'] += d == 'neutral' and g != 'neutral'
            c['v4 final pred neutral'] += p['final'] == 'neutral'
            c['v4 final neutral wrong'] += p['final'] == 'neutral' and g != 'neutral'
            for e in EXP:
                a = (p['reflect'][e] or [None])[0]
                same = a == d
                c[e + ' reflect correct'] += a == g
                c[e + ' same as Direct'] += same
                c[e + ' differs: expert correct'] += (not same) and a == g
                c[e + ' differs: Direct correct'] += (not same) and d == g
                c[e + ' pred neutral'] += a == 'neutral'
                c[e + ' neutral wrong'] += a == 'neutral' and g != 'neutral'
        out[prov] = dict(branch=dict(c), all400_r0_expert_primary_correct=full['expert_primary_correct'],
                         all400_r0_primary_majority=full['stats']['r0 primary majority (ties wrong)'], all400_v4_final=full['stats']['v4 final'])
        print(prov, json.dumps(out[prov], ensure_ascii=False))
    (ROOT / 'metrics/expert_vs_direct_branch_diagnostic.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')


if __name__ == '__main__':
    main()
