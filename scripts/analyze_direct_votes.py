"""Does voting over several independent Direct runs beat a single Direct run? (disagreement branch, 117 samples)

Five runs per sample: outputs/direct (run 1), outputs/direct_rerun (run 2), outputs/direct_vote1..3 (runs 3-5). Single-run accuracy is reported
for each run and as their mean; majority-of-3 is reported for (a) the three fresh runs 3-5 and (b) the average over all C(5,3)=10 triples;
majority-of-5 uses all runs. Ties (all three answers different / 2-2-1) are broken by the first run in the group, and the number of ties is
reported; an alphabetical tie-break is computed as a sensitivity check. Gold labels are read only here. No model calls.
Writes metrics/direct_vote_experiment.json. Server (Linux) only.
Usage: python scripts/analyze_direct_votes.py
"""
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
jr = lambda p: json.loads(Path(p).read_text())
DIRS = ['direct', 'direct_rerun', 'direct_vote1', 'direct_vote2', 'direct_vote3']
rows = []
for s in ['validation', 'train']:
    rows += [dict(json.loads(l), split=s) for l in (ROOT / 'data/manifests' / (s + '.jsonl')).read_text().splitlines() if l.strip()]


def vote(ans, mode):
    top = Counter(ans).most_common()
    best = top[0][1]
    tied = sorted(k for k, v in top if v == best)
    if len(tied) == 1:
        return tied[0], False
    return (ans[0] if mode == 'first' else tied[0]), True


out = {}
for p in ['gemini', 'gpt']:
    recs = []
    for r in rows:
        v4 = jr(ROOT / 'outputs/reflect_debate_v4' / p / r['id'] / 'result.json')
        if v4['route'] == 'common_label':
            continue
        runs = []
        for d in DIRS:
            x = jr(ROOT / 'outputs' / d / p / r['id'] / 'result.json')
            assert x['status'] == 'success', (d, r['id'])
            runs.append(x['prediction'])
        recs.append(dict(id=r['id'], dataset=r['dataset'], split=r['split'], gold=r['label'], runs=runs, v4=v4['prediction'], cand=v4['candidate_labels']))
    out[p] = recs

summary = {}
for p, recs in out.items():
    n = len(recs)
    g = lambda x: x['gold']
    single = [sum(x['runs'][i] == g(x) for x in recs) for i in range(5)]
    triples = list(combinations(range(5), 3))
    res = dict(n=n, single=single, single_mean=sum(single) / 5)
    for mode in ('first', 'alpha'):
        fresh = [vote([x['runs'][i] for i in (2, 3, 4)], mode) for x in recs]
        res[f'vote3_fresh_{mode}'] = sum(v == g(x) for (v, _), x in zip(fresh, recs))
        res[f'vote3_fresh_ties_{mode}'] = sum(t for _, t in fresh)
        per = []
        for tr in triples:
            per.append(sum(vote([x['runs'][i] for i in tr], mode)[0] == g(x) for x in recs))
        res[f'vote3_all_triples_{mode}'] = per
        res[f'vote3_all_triples_mean_{mode}'] = sum(per) / len(per)
        v5 = [vote(x['runs'], mode) for x in recs]
        res[f'vote5_{mode}'] = sum(v == g(x) for (v, _), x in zip(v5, recs))
        res[f'vote5_ties_{mode}'] = sum(t for _, t in v5)
    res['unanimous_5'] = sum(len(set(x['runs'])) == 1 for x in recs)
    res['unanimous_5_correct'] = sum(len(set(x['runs'])) == 1 and x['runs'][0] == g(x) for x in recs)
    res['any_correct_of_5'] = sum(g(x) in x['runs'] for x in recs)
    res['all_correct_of_5'] = sum(all(r_ == g(x) for r_ in x['runs']) for x in recs)
    res['distinct_answers_mean'] = sum(len(set(x['runs'])) for x in recs) / n
    # flips of the fresh vote-of-3 relative to run 1 (single saved Direct) and to the v4 output
    f3 = [vote([x['runs'][i] for i in (2, 3, 4)], 'first')[0] for x in recs]
    res['fresh3_vs_run1_fix'] = sum(a == g(x) and x['runs'][0] != g(x) for a, x in zip(f3, recs))
    res['fresh3_vs_run1_break'] = sum(a != g(x) and x['runs'][0] == g(x) for a, x in zip(f3, recs))
    res['fresh3_in_candidates'] = sum(a in x['cand'] for a, x in zip(f3, recs))
    by_ds = {}
    for ds in ('MER2024', 'MELD'):
        sub = [x for x in recs if x['dataset'] == ds]
        f = [vote([x['runs'][i] for i in (2, 3, 4)], 'first')[0] for x in sub]
        by_ds[ds] = dict(n=len(sub), single_mean=sum(sum(x['runs'][i] == g(x) for x in sub) for i in range(5)) / 5,
                         vote3_fresh=sum(a == g(x) for a, x in zip(f, sub)),
                         vote5=sum(vote(x['runs'], 'first')[0] == g(x) for x in sub))
    res['by_dataset'] = by_ds
    summary[p] = res
(ROOT / 'metrics' / 'direct_vote_experiment.json').write_text(json.dumps(dict(summary=summary, per_sample=out), ensure_ascii=False, indent=1), encoding='utf8')
for p, r in summary.items():
    print(p, json.dumps(r, ensure_ascii=False))
