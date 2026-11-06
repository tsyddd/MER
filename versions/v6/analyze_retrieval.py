"""Offline analysis of the R2-MAD retrieval on the test set (read-only; no LLM call; bge-m3 on CPU).

For every test sample x variant (n1/n2/n3) x debate round x expert, rebuild the query exactly as run_rmad.py did
(question = caption + task text; key = question + compact(previous state of this expert) + sanitized state summary),
re-encode it, re-run Memory.retrieve, and check that the selected case ids equal the logged ones.
Then measure, against the gold label of the test sample:
  - label agreement of the retrieved cases vs. chance and vs. the label prior of the memory slice
  - whether retrieval mostly returns cases whose label equals the expert's own current answer (echo)
  - similarity vs. label agreement (are closer cases more useful?)
  - an oracle: the best case in the slice by key similarity whose label equals the gold label - where does it rank?
  - what the expert did after seeing the cases (answer moved toward the first case's label? right or wrong?)
  - peer reliability marks vs. whether that peer's answer was actually right
Writes metrics/v6_rmad_retrieval_analysis.json.
"""
import json, glob, collections, sys, math, os
from pathlib import Path
import numpy as np
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
sys.path.insert(0, 'versions/v6')
from common import compact, read, test_rows, OUT, ROLES  # noqa
from memory import Memory  # noqa
from build_memory import sanitize  # noqa
from captions import get_caption  # noqa
from common import question_text, consensus_ratio  # noqa
from embedder import Embedder  # noqa

TEST = OUT / 'test'
V4 = Path('outputs/reflect_debate_v4')
rows = test_rows()
emb = Embedder(device='cpu')


def enc(texts):
    return emb.encode(texts, batch=4)


report = {}
for provider in ('gemini', 'gpt'):
    mem = Memory(OUT / 'memory' / provider)
    recs = mem.records
    rec_by_id = {r['db_id']: i for i, r in enumerate(recs)}
    # label prior of each (role, dataset) slice: share of records whose solution == label
    prior = {}
    for (role, ds), idx in mem.by_role_ds.items():
        c = collections.Counter(recs[i]['solution'] for i in idx)
        prior[(role, ds)] = {k: v / len(idx) for k, v in c.items()}
    out = dict(variants={})
    for variant in ('n1', 'n2', 'n3'):
        n = int(variant[1:])
        st = collections.Counter()
        sims_hit, sims_miss = [], []
        rank_oracle = []
        per_case = []
        move = collections.Counter()
        rel_stats = collections.Counter()
        for f in sorted(glob.glob(str(TEST / provider / variant / '*' / '*' / 'result.json'))):
            r = json.load(open(f))
            if r.get('status') != 'success' or not r.get('retrieved'):
                continue
            row = rows[r['id']]
            gold, ds, classes = row['label'], row['dataset'], row['classes']
            folder = Path(f).parent
            shared = TEST / provider / 'shared' / row['id']
            question = question_text(row, get_caption(row))
            r0 = {role: read(V4 / provider / row['id'] / f'r0_{role}.json')['output'] for role in ROLES}
            state = r0
            ratio = consensus_ratio(r0)
            for rd in (1, 2):
                key = f'debate{rd}'
                if key not in r['retrieved']:
                    break
                sfile = (shared if rd == 1 else folder) / f'state{rd - 1}.json'
                summary = sanitize(read(sfile)['output']['summary'].strip(), classes)
                texts = {role: f'{question}\n{compact(state[role])}\n{summary}' for role in ROLES}
                qv = dict(zip(ROLES, enc([texts[x] for x in ROLES])))
                new = {role: read(folder / f'debate{rd}_{role}.json')['output'] for role in ROLES}
                for role in ROLES:
                    logged = r['retrieved'][key][role]['cases']
                    sel, cand, csim = mem.retrieve(role, ds, qv[role], n, ratio)
                    st['queries'] += 1
                    st['reproduced'] += [recs[i]['db_id'] for i in sel] == logged
                    used = [rec_by_id[c] for c in logged]
                    own_prev = state[role]['answer']
                    for k, i in enumerate(used):
                        lab = recs[i]['solution']
                        s = float(mem.K[i] @ qv[role])
                        st['cases'] += 1
                        st['case_label_eq_gold'] += lab == gold
                        st['case_label_eq_own_answer'] += lab == own_prev
                        st['case_label_in_union'] += lab in r['union']
                        st['case_correct'] += bool(recs[i]['correct'])
                        st['chance_eq_gold'] += 1 / len(classes)
                        st['prior_eq_gold'] += prior[(role, ds)].get(gold, 0.0)
                        st['own_answer_correct'] += own_prev == gold
                        (sims_hit if lab == gold else sims_miss).append(s)
                        per_case.append(dict(sim=s, hit=lab == gold, rank=k))
                    # oracle: rank (by key similarity, within the slice) of the most similar case whose label is the gold label
                    idx = np.array(mem.by_role_ds[(role, ds)])
                    sims = mem.K[idx] @ qv[role]
                    order = idx[np.argsort(-sims, kind='stable')]
                    labs = [recs[i]['solution'] for i in order]
                    rk = next((j for j, l in enumerate(labs) if l == gold), None)
                    rank_oracle.append(rk)
                    st['slice_size'] += len(idx)
                    # behaviour: did the expert move to the first case's label?
                    first_lab = recs[used[0]]['solution'] if used else None
                    a_prev, a_new = own_prev, new[role]['answer']
                    if first_lab is not None and first_lab != a_prev:
                        tag = 'moved_to_case' if a_new == first_lab else ('moved_elsewhere' if a_new != a_prev else 'kept')
                        move[tag] += 1
                        if tag == 'moved_to_case':
                            move['moved_to_case_right'] += a_new == gold
                            move['moved_to_case_wrong_from_right'] += a_prev == gold
                    elif first_lab is not None:
                        move['case_agrees_with_own'] += 1
                        move['case_agrees_kept'] += a_new == a_prev
                    # peer reliability marks
                    for o, mark in (r['retrieved'][key][role].get('reliability') or {}).items():
                        if mark in ('high', 'low'):
                            right = state[o]['answer'] == gold
                            rel_stats[f'{mark}_n'] += 1
                            rel_stats[f'{mark}_peer_right'] += right
                        else:
                            rel_stats['none_n'] += 1
                state, ratio = new, consensus_ratio(new)
        # similarity buckets
        cases = sorted(per_case, key=lambda x: x['sim'])
        q = len(cases) // 4
        buckets = []
        for b in range(4):
            part = cases[b * q:(b + 1) * q] if b < 3 else cases[3 * q:]
            if part:
                buckets.append(dict(sim_from=round(part[0]['sim'], 3), sim_to=round(part[-1]['sim'], 3), n=len(part), hit=round(sum(x['hit'] for x in part) / len(part), 3)))
        ranks = [x for x in rank_oracle if x is not None]
        out['variants'][variant] = dict(
            counts=dict(st), move=dict(move), reliability=dict(rel_stats), sim_buckets=buckets,
            sim_mean_hit=round(float(np.mean(sims_hit)), 4) if sims_hit else None, sim_mean_miss=round(float(np.mean(sims_miss)), 4) if sims_miss else None,
            oracle_rank=dict(n=len(rank_oracle), none=len(rank_oracle) - len(ranks), within_top1=sum(x < 1 for x in ranks), within_top3=sum(x < 3 for x in ranks),
                             within_top9=sum(x < 9 for x in ranks), median=float(np.median(ranks)) if ranks else None,
                             mean_slice=round(st['slice_size'] / max(st['queries'], 1), 1)))
        print(provider, variant, json.dumps(out['variants'][variant]['counts'], ensure_ascii=False), flush=True)
    report[provider] = out
Path('metrics/v6_rmad_retrieval_analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
print(json.dumps(report, ensure_ascii=False)[:6000])
