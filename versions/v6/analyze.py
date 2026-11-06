"""Server-side analysis of the R2-MAD (v6) run -> metrics/v6_rmad_analysis.json (read-only; gold labels used only for scoring).
Collects: training-set composition, memory size / correctness, retrieval stats (retrieved-case correctness, same-label rate, reliability marks),
per-variant accuracy (total / by dataset / routes / rounds), flips vs n0 and vs Direct run1 and vs v4, call counts.
Usage (server, project root): .venv/bin/python versions/v6/analyze.py
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from common import DATASETS, OUT, ROOT, V4_OUT, pool_rows, read, test_rows, v4_disagreement_ids

VARIANTS = ['n0', 'n1', 'n2', 'n3']
PROVIDERS = ['gemini', 'gpt']


def count_calls(folder):
    return sum(1 for f in folder.rglob('calls/*_attempt*.json') if '_error_' not in f.name)


def main():
    out = {}
    sel = read(OUT / 'pool' / 'selection.json')
    pool = {r['id']: r for ds in DATASETS for r in pool_rows(ds)}
    trows = test_rows()
    # ---------------------------------------------------------------- training set
    train = {}
    for p in PROVIDERS:
        d = {}
        for ds in DATASETS:
            s = sel[ds]
            ids = s[p]['selected']
            d[ds] = dict(processed=s['processed'], success=s[p]['success'], disagree=s[p]['disagree'], selected=len(ids),
                         ratio=round(s[p]['disagree'] / max(1, s[p]['success']), 4),
                         labels=dict(Counter(pool[i]['label'] for i in ids).most_common()),
                         pool_labels_processed=None)
        train[p] = d
    out['train'] = train
    # ---------------------------------------------------------------- memory
    mem = {}
    for p in PROVIDERS:
        recs = [json.loads(l) for l in (OUT / 'memory' / p / 'records.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        by = defaultdict(lambda: [0, 0])
        for r in recs:
            by[f"r{r['round']}"][0] += r['correct']; by[f"r{r['round']}"][1] += 1
            by[r['role']][0] += r['correct']; by[r['role']][1] += 1
        # training debate dynamics: consensus after each round, final majority correctness
        dyn = Counter()
        for r in sel['MER2024'][p]['selected'] + sel['MELD'][p]['selected']:
            f = OUT / 'train' / p / r / 'train_result.json'
            if not f.exists():
                continue
            t = read(f)
            gold = pool[r]['label']
            for rd in ('r0', 'd1', 'd2'):
                a = t['answers'][rd]
                dyn[f'{rd}_unanimous'] += len(set(a.values())) == 1
                dyn[f'{rd}_any_correct'] += gold in a.values()
                maj = Counter(a.values()).most_common(1)[0]
                dyn[f'{rd}_majority_correct'] += maj[1] >= 2 and maj[0] == gold
            dyn['n'] += 1
        mem[p] = dict(records=len(recs), correct=sum(r['correct'] for r in recs), by={k: dict(correct=v[0], n=v[1]) for k, v in by.items()}, train_dynamics=dict(dyn))
    out['memory'] = mem
    # ---------------------------------------------------------------- test
    test = {}
    for p in PROVIDERS:
        ids = v4_disagreement_ids(p)
        gold = {i: trows[i]['label'] for i in ids}
        ds_of = {i: trows[i]['dataset'] for i in ids}
        v4p = {i: read(V4_OUT / p / i / 'result.json')['prediction'] for i in ids}
        d1 = {}
        for i in ids:
            f = ROOT / 'outputs' / 'direct' / p / i / 'result.json'
            if f.exists():
                d1[i] = read(f).get('prediction')
        res = {}
        preds = {}
        for v in VARIANTS:
            rs = {i: read(OUT / 'test' / p / v / i / 'result.json') for i in ids if (OUT / 'test' / p / v / i / 'result.json').exists()}
            preds[v] = {i: r['prediction'] for i, r in rs.items()}
            routes = Counter(r['route'] for r in rs.values())
            rounds = Counter(r['debate_rounds'] for r in rs.values())
            acc = sum(preds[v][i] == gold[i] for i in rs)
            byds = {ds: dict(n=sum(1 for i in rs if ds_of[i] == ds), correct=sum(1 for i in rs if ds_of[i] == ds and preds[v][i] == gold[i])) for ds in DATASETS}
            # retrieval stats
            rstat = Counter()
            if v != 'n0':
                recs = {json.loads(l)['db_id']: json.loads(l) for l in (OUT / 'memory' / p / 'records.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
                for i, r in rs.items():
                    for rd, roles in r.get('retrieved', {}).items():
                        for role, info in roles.items():
                            for c in info['cases']:
                                rec = recs[c]
                                rstat['cases'] += 1
                                rstat['cases_correct'] += rec['correct']
                                rstat['cases_solution_eq_gold'] += rec['solution'] == gold[i]
                                rstat[f'cases_round{rec["round"]}'] += 1
                            for peer, mark in info['reliability'].items():
                                rstat[f'rel_{mark}'] += 1
                # did the experts follow the retrieved label? (debate-1 answer == solution of the first retrieved case)
                for i, r in rs.items():
                    info = r.get('retrieved', {}).get('debate1', {})
                    d1a = r['debate_answers'].get('debate1', {})
                    for role, x in info.items():
                        if x['cases'] and role in d1a:
                            sol = recs[x['cases'][0]]['solution']
                            rstat['d1_follow_n'] += 1
                            rstat['d1_follow_eq'] += d1a[role] == sol
                            rstat['d1_sol_in_union'] += sol in r['union']
            calls = sum(count_calls(OUT / 'test' / p / v / i) for i in rs)
            res[v] = dict(done=len(rs), correct=acc, by_dataset=byds, routes=dict(routes), rounds=dict(rounds), retrieval=dict(rstat), calls=calls)
        # flips
        flips = {}
        for v in VARIANTS[1:]:
            common = [i for i in ids if i in preds[v] and i in preds['n0']]
            flips[v] = dict(vs_n0_fixed=sum(preds['n0'][i] != gold[i] and preds[v][i] == gold[i] for i in common),
                            vs_n0_broken=sum(preds['n0'][i] == gold[i] and preds[v][i] != gold[i] for i in common),
                            vs_n0_changed=sum(preds['n0'][i] != preds[v][i] for i in common), common=len(common))
        for v in VARIANTS:
            common = [i for i in ids if i in preds[v] and i in d1]
            res[v]['vs_direct1'] = dict(fixed=sum(d1[i] != gold[i] and preds[v][i] == gold[i] for i in common), broken=sum(d1[i] == gold[i] and preds[v][i] != gold[i] for i in common), common=len(common))
            common = [i for i in ids if i in preds[v]]
            res[v]['vs_v4'] = dict(fixed=sum(v4p[i] != gold[i] and preds[v][i] == gold[i] for i in common), broken=sum(v4p[i] == gold[i] and preds[v][i] != gold[i] for i in common), v4_correct_same=sum(v4p[i] == gold[i] for i in common))
        shared_calls = sum(count_calls(OUT / 'test' / p / 'shared' / i) for i in ids if (OUT / 'test' / p / 'shared' / i).exists())
        test[p] = dict(n=len(ids), variants=res, flips=flips, shared_state0_calls=shared_calls,
                       direct1_correct=sum(d1.get(i) == gold[i] for i in ids), v4_correct=sum(v4p[i] == gold[i] for i in ids),
                       labels=dict(Counter(gold.values()).most_common()),
                       per_sample={i: dict(gold=gold[i], dataset=ds_of[i], v4=v4p[i], direct1=d1.get(i), **{v: preds[v].get(i) for v in VARIANTS}) for i in ids})
    out['test'] = test
    # training call count
    out['train_calls'] = {p: sum(count_calls(OUT / 'train' / p / i) for ds in DATASETS for i in sel[ds][p]['selected']) for p in PROVIDERS}
    out['pool_calls'] = {p: None for p in PROVIDERS}
    (ROOT / 'metrics').mkdir(exist_ok=True)
    (ROOT / 'metrics' / 'v6_rmad_analysis.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({p: {v: (out['test'][p]['variants'][v]['done'], out['test'][p]['variants'][v]['correct']) for v in VARIANTS} for p in PROVIDERS}))


if __name__ == '__main__':
    main()
