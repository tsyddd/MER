"""Majority-vote variants on the disagreement branch (117 samples), compared with Direct.

Votes come only from saved outputs (no model calls): the three experts' reflected primary answers (reflect_*.json),
the three Round-0 primaries (r0_*.json), and the two Direct runs (outputs/direct, outputs/direct_rerun).
Ties are broken by Direct run 1 when it is among the tied labels, otherwise alphabetically; the number of ties is reported.
Writes metrics/vote_disagree_117.json. Server (Linux) only.
Usage: python scripts/vote_disagree.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
jr = lambda p: json.loads(Path(p).read_text())
ROLES = ['graph', 'audio_subtitle', 'image']
rows = []
for s in ['validation', 'train']:
    rows += [dict(json.loads(l), split=s) for l in (ROOT / 'data/manifests' / (s + '.jsonl')).read_text().splitlines() if l.strip()]


def vote(votes, tiebreak):
    top = Counter(votes).most_common()
    best = top[0][1]
    tied = sorted(k for k, v in top if v == best)
    if len(tied) == 1:
        return tied[0], False
    if tiebreak in tied:
        return tiebreak, True
    return tied[0], True


out = {}
for p in ['gemini', 'gpt']:
    recs = []
    for r in rows:
        f = ROOT / 'outputs/reflect_debate_v4' / p / r['id']
        if jr(f / 'result.json')['route'] == 'common_label':
            continue
        d1 = jr(ROOT / 'outputs/direct' / p / r['id'] / 'result.json')['prediction']
        d2 = jr(ROOT / 'outputs/direct_rerun' / p / r['id'] / 'result.json')['prediction']
        rf = [jr(f / f'reflect_{k}.json')['output']['answer'] for k in ROLES]
        r0 = [jr(f / f'r0_{k}.json')['output']['answer'] for k in ROLES]
        v1, t1 = vote(rf, d1)  # 3 reflected experts, tie -> Direct run 1
        v2, t2 = vote(rf + [d1, d2], d1)  # 3 reflected experts + 2 Direct runs
        v3, t3 = vote(r0, d1)  # 3 Round-0 primaries only
        v4, t4 = vote(r0 + [d1, d2], d1)  # 3 Round-0 + 2 Direct runs
        recs.append(dict(id=r['id'], dataset=r['dataset'], split=r['split'], gold=r['label'], direct1=d1, direct2=d2,
                         v1=v1, v2=v2, v3=v3, v4=v4, ties={'v1': t1, 'v2': t2, 'v3': t3, 'v4': t4}))
    out[p] = recs
(ROOT / 'metrics' / 'vote_disagree_117.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
for p in out:
    r = out[p]
    print(p, len(r), 'direct1', sum(x['direct1'] == x['gold'] for x in r), 'direct2', sum(x['direct2'] == x['gold'] for x in r),
          {k: sum(x[k] == x['gold'] for x in r) for k in ['v1', 'v2', 'v3', 'v4']},
          'ties', {k: sum(x['ties'][k] for x in r) for k in ['v1', 'v2', 'v3', 'v4']})
