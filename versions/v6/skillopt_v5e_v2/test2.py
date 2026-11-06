"""Test of version 2 (Gemini, 62 test samples; design page section 3, criteria fixed in advance).

  skill run 1, skill run 2 : the frozen best_skill.json of version 2, no expansion, separate output folders (independent runs)
  control run 2            : empty skill, no expansion (= plain v5-E); control run 1 is version 1's 'control' run (same setting)
Criterion: mean(skill runs) >= mean(control runs) + 3 correct, and on each dataset mean(skill) >= mean(control). Otherwise: no effect.

  python versions/v6/skillopt_v5e_v2/test2.py --mode skill1|skill2|control2|report [--workers 4]
"""
from __future__ import annotations
import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / 'skillopt_v5e'))
import split2 as SP  # noqa: E402
import rollout2 as RO  # noqa: E402
import skill2 as S2  # noqa: E402

ROOT = SP.ROOT
V1_CONTROL = ROOT / 'outputs' / 'v6_skillopt_v5e' / 'gemini' / 'test' / 'control'


def summarize(results):
    out = {}
    for ds in S2.DATASETS:
        rs = [r for r in results if r['dataset'] == ds]
        by = defaultdict(list)
        for r in rs:
            by[r['label']].append(r.get('status') == 'success' and r['prediction'] == r['label'])
        ok = [r for r in rs if r.get('status') == 'success']
        out[ds] = dict(n=len(rs), correct=sum(r['prediction'] == r['label'] for r in ok), bal=round(sum(sum(v) / len(v) for v in by.values()) / len(by), 4),
                       pred_neutral=sum(r['prediction'] == 'neutral' for r in ok), flagged=sum(r['flagged'] for r in ok),
                       revise_wr=sum(r.get('decision') == 'REVISE' and r['first_answer'] != r['label'] and r['prediction'] == r['label'] for r in ok),
                       revise_rw=sum(r.get('decision') == 'REVISE' and r['first_answer'] == r['label'] and r['prediction'] != r['label'] for r in ok),
                       errors=len(rs) - len(ok))
    out['total'] = sum(out[d]['correct'] for d in S2.DATASETS)
    return out


def load_dir(d):
    return [json.loads(Path(f).read_text()) for f in glob.glob(str(d) + '/*/*/result.json')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['skill1', 'skill2', 'control2', 'report'], required=True)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    out = SP.provider_dir('gemini')
    test_dir = out / 'test'
    items = SP.load('gemini')['test']
    if a.mode != 'report':
        if a.mode.startswith('skill'):
            skill = S2.Skill.from_json((out / 'best_skill.json').read_text())
        else:
            skill = S2.Skill.empty()
        res = RO.run_many(items, 'gemini', skill, test_dir / a.mode, a.workers)
        s = summarize(res)
        (test_dir / f'{a.mode}_summary.json').write_text(json.dumps(dict(mode=a.mode, skill_sha=skill.sha256(), **s), ensure_ascii=False, indent=1))
        print(a.mode, json.dumps(s, ensure_ascii=False))
        return
    runs = {'control1 (v1 control)': summarize(load_dir(V1_CONTROL))}
    for m in ('control2', 'skill1', 'skill2'):
        if (test_dir / m).exists():
            runs[m] = summarize(load_dir(test_dir / m))
    sk = [runs[m] for m in ('skill1', 'skill2') if m in runs]
    ct = [runs[m] for m in ('control1 (v1 control)', 'control2') if m in runs]
    mean = lambda xs, f: sum(f(x) for x in xs) / len(xs)  # noqa: E731
    verdict = None
    if len(sk) == 2 and len(ct) == 2:
        d_total = mean(sk, lambda x: x['total']) - mean(ct, lambda x: x['total'])
        d_ds = {d: mean(sk, lambda x: x[d]['correct']) - mean(ct, lambda x: x[d]['correct']) for d in S2.DATASETS}
        verdict = dict(diff_total=d_total, diff_per_dataset=d_ds, success=d_total >= 3 and all(v >= 0 for v in d_ds.values()))
    rep = dict(runs=runs, verdict=verdict, criterion='mean(skill) - mean(control) >= 3 and per dataset >= 0 (fixed before testing)')
    (ROOT / 'metrics' / 'v6_skillopt_v5e_v2_gemini_test.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf8')
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
