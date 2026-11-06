"""Candidate-set expansion from the 80-sample confusion matrix (design: docs/v6-skillopt-v5e-design.html, section 5).

Matrix (built once, locally, from the saved results on the 80 old validation samples): per provider x dataset x direction.
For a candidate label c, g(c) = the gold label that most often occurs when the answer is c (top 1). Ranking: number of distinct
samples first, then number of error events (the same sample is counted once per result set: Direct / PPCT / v1 / v2 / v3 summary), then label.
Labels without any record are not expanded. Expansion: C' = C + {g(c)}; a label already in C stays "original" (even when it is also some g(c)).
Known limits (accepted by the user): the 80 samples contain 20 samples of the 117 test samples; the matrix is thin (most top-1 rest on 1-2 samples).

  build:   python versions/v6/skillopt_v5e/confusion.py build      (needs the saved outputs of the 80 samples; writes data/skillopt_v5e/confusion_top1.json)
  library: expand(table, provider, dataset, candidates) -> dict(candidates, sources, added)
"""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TABLE_PATH = ROOT / 'data' / 'skillopt_v5e' / 'confusion_top1.json'
METHODS = ['direct', 'ppct', 'v1', 'v2', 'v3']


def build():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import build_confusion_view as BC  # saved-output readers for the 80 validation samples
    gold, ds_of = BC.GOLD, BC.DS
    table = {}
    for provider in ('gemini', 'gpt'):
        events = defaultdict(Counter)
        samples = defaultdict(lambda: defaultdict(set))
        for method in METHODS:
            for sample_id, answer in BC.preds(method, provider).items():
                if answer != gold[sample_id]:
                    key = (ds_of[sample_id], answer)
                    events[key][gold[sample_id]] += 1
                    samples[key][gold[sample_id]].add(sample_id)
        table[provider] = {}
        for ds in ('MER2024', 'MELD'):
            rows = {}
            for c in BC.ORDER[ds]:
                options = [(len(samples[(ds, c)][g]), events[(ds, c)][g], g) for g in events[(ds, c)]]
                options.sort(key=lambda x: (-x[0], -x[1], x[2]))
                rows[c] = None if not options else dict(gold=options[0][2], samples=options[0][0], events=options[0][1])
            table[provider][ds] = rows
    meta = dict(source='80 old validation samples x 5 result sets per provider (direct, ppct, v1, v2, v3 summary)', direction='answer c -> gold g',
                ranking='distinct samples, then events, then label', note='contains 20 samples that are also in the 117 test samples (accepted by the user)')
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLE_PATH.write_text(json.dumps(dict(meta=meta, table=table), ensure_ascii=False, indent=1))
    return table


def load(path=None):
    return json.loads(Path(path or TABLE_PATH).read_text())['table']


def expand(table, provider, dataset, candidates):
    """C -> C'. sources maps every label of C' to 'original' or 'expanded'; added lists the expansions with their support."""
    cands = list(candidates)
    sources = {c: 'original' for c in cands}
    added = []
    for c in cands:
        entry = table[provider][dataset].get(c)
        if entry and entry['gold'] not in sources:
            sources[entry['gold']] = 'expanded'
            added.append(dict(for_label=c, label=entry['gold'], samples=entry['samples'], events=entry['events']))
    return dict(candidates=list(sources), sources=sources, added=added)


def no_expansion(candidates):
    cands = list(candidates)
    return dict(candidates=cands, sources={c: 'original' for c in cands}, added=[])


if __name__ == '__main__':
    if sys.argv[1:] == ['build']:
        t = build()
        for p, d in t.items():
            for ds, rows in d.items():
                print(p, ds, {c: (v['gold'], v['samples'], v['events']) if v else None for c, v in rows.items()})
    else:
        print(__doc__)
