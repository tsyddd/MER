"""Train / validation split of version 2 (Gemini): the same disagreement pool as version 1 (v6 pool, Round-0 disagreement, MELD samples
sharing a dialogue with the old 400 removed, <= 200 per dataset), but split STRATIFIED by label: every class with >= 6 samples puts
max(3, round(25%)) samples into validation, others round(25%); MELD keeps whole dialogues on one side. Test = the same 62 samples as
version 1 (candidate set = v4 candidate_labels). Labels are read here only to stratify; they never go to the target model.

  python versions/v6/skillopt_v5e_v2/split2.py build --provider gemini
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / 'skillopt_v5e'))
import split as SP1  # noqa: E402  (version 1: pool reading, manifests, test set)

ROOT = SP1.ROOT
OUT_ROOT = ROOT / 'outputs' / 'v6_skillopt_v5e_v2'
SEED = 42


def provider_dir(provider, tag=None):
    return OUT_ROOT / (provider + (('_' + tag) if tag else ''))


def build(provider):
    rows = SP1.manifest_rows()
    v1 = SP1.provider_dir(provider) / 'split'
    pool = json.loads((v1 / 'train.json').read_text()) + json.loads((v1 / 'val.json').read_text())  # same pool as version 1
    test = json.loads((v1 / 'test.json').read_text())
    train, val, report = [], [], {}
    for ds in ('MER2024', 'MELD'):
        items = [it for it in pool if it['dataset'] == ds]
        counts = Counter(rows[it['id']]['label'] for it in items)
        target = {c: (max(3, round(0.25 * n)) if n >= 6 else round(0.25 * n)) for c, n in counts.items()}
        groups = defaultdict(list)
        for it in items:
            groups[rows[it['id']]['dialogue_id'] if ds == 'MELD' else it['id']].append(it)
        keys = sorted(groups, key=str)
        random.Random(SEED).shuffle(keys)
        have, vkeys = Counter(), set()
        for k in keys:
            labs = Counter(rows[it['id']]['label'] for it in groups[k])
            if all(have[l] + n <= target[l] for l, n in labs.items()) and any(have[l] < target[l] for l in labs):
                vkeys.add(k)
                have.update(labs)
        v = [it for k in keys if k in vkeys for it in groups[k]]
        t = [it for k in keys if k not in vkeys for it in groups[k]]
        val += sorted(v, key=lambda x: x['id'])
        train += sorted(t, key=lambda x: x['id'])
        report[ds] = dict(train=len(t), val=len(v), val_labels=dict(have), train_labels=dict(Counter(rows[it['id']]['label'] for it in t)), target=target)
    assert not {it['id'] for it in train} & {it['id'] for it in val}
    folder = provider_dir(provider) / 'split'
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in (('train', train), ('val', val), ('test', test)):
        (folder / f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
    summary = dict(provider=provider, train=len(train), val=len(val), test=len(test), per_dataset=report,
                   sha256={n: hashlib.sha256((folder / f'{n}.json').read_bytes()).hexdigest() for n in ('train', 'val', 'test')})
    (folder / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    return summary


def load(provider, tag=None):
    folder = provider_dir(provider, tag) / 'split'
    if not folder.exists() and tag:
        folder = provider_dir(provider) / 'split'
    rows = SP1.manifest_rows()
    test_rows = SP1.v6c.test_rows()
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
