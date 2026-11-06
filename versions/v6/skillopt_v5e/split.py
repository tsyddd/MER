"""Train / validation / test sets of SkillOpt-V5E (design page, section 2). Run on the server; reads saved outputs only, no model call.

  train + validation: v6 pool samples (old 400 removed) whose Round-0 of the three experts is a disagreement for THIS provider
     (outputs/v6_rmad/pool/<provider>/<dataset>/<sample_id>/r0_summary.json), minus MELD samples that share a dialogue with the old 400
     (test source), capped at 200 per dataset in the pool's seeded order, then split 75 / 25 by group (MELD: dialogue; MER2024: sample),
     seed 42. Candidate set C = the union of the three experts' answers, in the dataset's label order.
  test: the 117 v4-disagreement samples of the old 400 (Gemini 62, GPT 55); candidate set = candidate_labels of the saved v4 result.

  python versions/v6/skillopt_v5e/split.py build --provider gemini|gpt
Gold labels are not read here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import v6c  # noqa: E402

ROOT = v6c.ROOT
OUT_ROOT = ROOT / 'outputs' / 'v6_skillopt_v5e'
VAL_FRACTION = 0.25
QUOTA = 200
SEED = 42


def provider_dir(provider, tag=None):
    return OUT_ROOT / (provider + (('_' + tag) if tag else ''))


def manifest_rows():
    rows = {}
    for ds in v6c.DATASETS:
        for line in (v6c.SOURCE / 'manifests' / (ds + '.jsonl')).open():
            if line.strip():
                r = json.loads(line)
                rows[r['id']] = r
    return rows


def old400_ids():
    return {json.loads(l)['id'] for ds in v6c.DATASETS for l in (v6c.OLD_400 / ds / 'selected_200.jsonl').open() if l.strip()}


def build(provider):
    rows = manifest_rows()
    old = old400_ids()
    old_dialogues = {rows[i]['dialogue_id'] for i in old if i.startswith('MELD')}
    train, val, report = [], [], {}
    for ds in v6c.DATASETS:
        kept, removed = [], 0
        for r in v6c.pool_rows(ds):  # pool order (seeded), old 400 already removed
            f = v6c.OUT / 'pool' / provider / ds / r['sample_id'] / 'r0_summary.json'
            if not f.exists():
                continue
            d = v6c.read(f)
            if d.get('status') != 'success' or not d['disagree']:
                continue
            if ds == 'MELD' and rows[r['id']]['dialogue_id'] in old_dialogues:
                removed += 1
                continue
            union = {a for v in d['sets'].values() for a in v}
            kept.append(dict(id=r['id'], dataset=ds, group=(rows[r['id']]['dialogue_id'] if ds == 'MELD' else r['id']),
                             candidates=[c for c in r['classes'] if c in union]))
        kept = kept[:QUOTA]
        groups = defaultdict(list)
        for it in kept:
            groups[it['group']].append(it)
        keys = sorted(groups)
        random.Random(SEED).shuffle(keys)
        v, t = [], []
        for k in keys:
            (v if len(v) < VAL_FRACTION * len(kept) else t).extend(groups[k])
        train += sorted(t, key=lambda x: x['id'])
        val += sorted(v, key=lambda x: x['id'])
        report[ds] = dict(disagreement_after_exclusion=len(kept), removed_same_dialogue_as_old400=removed, train=len(t), val=len(v),
                          train_groups=len(groups) - len({x['group'] for x in v}), val_groups=len({x['group'] for x in v}))
    assert not {x['group'] for x in train} & {x['group'] for x in val}
    assert not {x['id'] for x in train + val} & old
    test = []
    for i in v6c.v4_disagreement_ids(provider):
        res = v6c.read(v6c.V4_OUT / provider / i / 'result.json')
        test.append(dict(id=i, dataset=i.split('/')[0], candidates=list(res['candidate_labels'])))
    folder = provider_dir(provider) / 'split'
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in (('train', train), ('val', val), ('test', test)):
        (folder / f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
    summary = dict(provider=provider, train=len(train), val=len(val), test=len(test), per_dataset=report,
                   sha256={n: hashlib.sha256((folder / f'{n}.json').read_bytes()).hexdigest() for n in ('train', 'val', 'test')})
    (folder / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    return summary


def load(provider, tag=None):
    """dict(train, val, test): lists of dict(id, dataset, candidates, row) where row is the manifest row (test: the v4 row)."""
    folder = provider_dir(provider, tag) / 'split'
    if not folder.exists() and tag:
        folder = provider_dir(provider) / 'split'
    rows = manifest_rows()
    test_rows = v6c.test_rows()
    out = {}
    for name in ('train', 'val', 'test'):
        items = json.loads((folder / f'{name}.json').read_text())
        for it in items:
            it['row'] = test_rows[it['id']] if name == 'test' else rows[it['id']]
        out[name] = items
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['build'])
    ap.add_argument('--provider', choices=['gemini', 'gpt'], required=True)
    a = ap.parse_args()
    print(json.dumps(build(a.provider), ensure_ascii=False, indent=1))
