"""SkillOpt-V5E version 2 training loop, Gemini (design: docs/v6-skillopt-v5e-v2-design.html).

Per epoch (<= 3, early stop when no section accepted anything in a whole epoch), per step:
  1 batch of 40 training samples drawn CLASS-BALANCED (each slot: a uniformly random (dataset, label) bucket, then its next item)
  2 rollout of v5-E with the current skill (no candidate expansion; each sample reads its own dataset section)
  3 for each dataset separately: trajectories -> failure / success piles -> groups of 8 -> one reflection model per group (frames + audio)
    -> merge -> per module keep the top L -> lint (incl. other-dataset label names and default-label wording)
  4 gate per dataset, module by module, on that dataset's validation samples:
      first  : class-balanced recall >= current + 0.05 AND correct count not lower
      relook / reflect : only the flagged validation samples count; the candidate must change >= 1 answer and (newly right - newly wrong) >= 1
    if applying the edits would make the section exceed 900 characters, one condense call rewrites the section with the edits; that
    rewritten section is the candidate.
  End of every epoch: validation score of the current skill is recorded; the final skill = the epoch snapshot with the highest
  sum over datasets of class-balanced recall (ties -> the earlier one).
Gold labels go to the reflection model and to the gate only; never into a target-model request.

  python versions/v6/skillopt_v5e_v2/train2.py --provider gemini [--epochs 3] [--smoke] [--workers 4]
"""
from __future__ import annotations
import argparse
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / 'skillopt_v5e'))
from llm import optimizer_client  # noqa: E402
import trajectory as T  # noqa: E402
import split2 as SP  # noqa: E402
import rollout2 as RO  # noqa: E402
import reflect2 as RF  # noqa: E402
import skill2 as S2  # noqa: E402

BATCH = 40
EPOCHS = 3
L_MAX, L_MIN = 4, 2
BAL_MARGIN = 0.05
SEED = 42


def lr_for(step, total):
    if total <= 1:
        return L_MAX
    t = min(step, total) / total
    return max(L_MIN, round(L_MIN + 0.5 * (L_MAX - L_MIN) * (1 + math.cos(math.pi * t))))


class Logger:
    def __init__(self, path):
        self.path = path

    def __call__(self, msg):
        line = time.strftime('%H:%M:%S ') + str(msg)
        print(line, flush=True)
        with self.path.open('a', encoding='utf8') as f:
            f.write(line + '\n')


def metrics(results, dataset):
    rs = [r for r in results if r['dataset'] == dataset]
    ok = [r for r in rs if r['status'] == 'success']
    by = defaultdict(list)
    for r in rs:
        by[r['row_label']].append(r['status'] == 'success' and r['prediction'] == r['row_label'])
    bal = sum(sum(v) / len(v) for v in by.values()) / len(by) if by else 0.0
    return dict(n=len(rs), correct=sum(r['prediction'] == r['row_label'] for r in ok), bal=round(bal, 4),
                pred=dict(sorted(((p, sum(r['prediction'] == p for r in ok)) for p in {r['prediction'] for r in ok}))), errors=len(rs) - len(ok))


def balanced_batches(items, epoch, batch):
    """One epoch = ceil(len(items) / batch) batches. Each slot draws a (dataset, label) bucket uniformly at random, then the next item of that
    bucket (shuffled, without repetition until the bucket is used up; a used-up bucket is reshuffled and reused). So every batch is
    class-balanced in expectation; small classes are seen several times per epoch and large ones (neutral) are not all seen every epoch.
    No item appears twice in one batch."""
    rng = random.Random(SEED + 1000 * epoch)
    buckets = defaultdict(list)
    for it in items:
        buckets[(it['dataset'], it['row']['label'])].append(it)
    keys = sorted(buckets)
    queues = {k: [] for k in keys}
    out = []
    for _ in range(math.ceil(len(items) / batch)):
        chosen, ids = [], set()
        while len(chosen) < min(batch, len(items)):
            k = keys[rng.randrange(len(keys))]
            if not queues[k]:
                queues[k] = list(buckets[k])
                rng.shuffle(queues[k])
            pick = next((i for i, it in enumerate(queues[k]) if it['id'] not in ids), None)
            if pick is None:  # every item of this small bucket is already in the batch
                if all(it['id'] in ids for kk in keys for it in buckets[kk]):
                    break
                continue
            it = queues[k].pop(pick)
            chosen.append(it)
            ids.add(it['id'])
        out.append(chosen)
    return out


def buffer_text(records, dataset):
    rel = [r for r in records if dataset in r.get('per_ds', {})]
    if not rel:
        return ''
    parts = ['Below is a summary of previous steps of this epoch for this dataset. Avoid repeating ineffective edits; prioritise unsolved failure patterns.']
    for r in rel:
        x = r['per_ds'][dataset]
        parts.append(f'### Step {r["step"]} - rollout {x["rollout_correct"]}/{x["batch"]} correct')
        for s in x.get('failure_patterns', [])[:6]:
            parts.append('  - ' + (s if isinstance(s, str) else json.dumps(s, ensure_ascii=False))[:300])
        for g in x.get('gates', []):
            if not g['accepted']:
                parts.append(f'  Rejected {g["module"]} edits ({g["why"]}): ' + ' | '.join(json.dumps(e, ensure_ascii=False)[:300] for e in g['edits']))
    return '\n'.join(parts)


def run(args):
    provider = args.provider
    assert provider == 'gemini', 'version 2 is for Gemini only (user decision)'
    tag = 'smoke' if args.smoke else None
    out = SP.provider_dir(provider, tag)
    for d in ('steps', 'eval'):
        (out / d).mkdir(parents=True, exist_ok=True)
    log = Logger(out / 'train.log')
    data = SP.load(provider, tag)
    train_items, val_items = list(data['train']), list(data['val'])
    if args.smoke:
        rng = random.Random(1)
        rng.shuffle(train_items)
        rng.shuffle(val_items)
        train_items = train_items[:args.train_n]
        val_items = [v for v in val_items if v['dataset'] == 'MER2024'][:args.val_n // 2] + [v for v in val_items if v['dataset'] == 'MELD'][:args.val_n // 2]
    batch = args.batch or BATCH
    client = optimizer_client(provider)
    forbidden = [it['row'].get('subtitle', '').strip() for it in data['train'] + data['val'] + data['test']]
    (out / 'config.json').write_text(json.dumps(dict(provider=provider, smoke=args.smoke, train=len(train_items), val=len(val_items), batch=batch, epochs=args.epochs,
                                                      L=[L_MAX, L_MIN], bal_margin=BAL_MARGIN, section_chars=S2.SECTION_CHARS, expansion=False, seed=SEED,
                                                      optimizer_model=client.model, target_model=RO.RO1.Client(provider).model), indent=1))
    log(f'train {len(train_items)}  val {len(val_items)}  batch {batch}  epochs<={args.epochs}  optimizer {client.model}')

    def evaluate(skill, name, items=None, reuse=None):
        items = items or val_items
        res = RO.run_many(items, provider, skill, out / 'eval' / name, args.workers, log=lambda *_: None, reuse_dir=(out / 'eval' / reuse) if reuse else None)
        lab = {it['id']: it['row']['label'] for it in items}
        for r in res:
            r['row_label'] = lab[r['id']]
        return res

    def by_id(res):
        return {r['id']: r for r in res}

    # ------------------------------------------------------------ baseline
    skill = S2.Skill.empty()
    cur_eval = {ds: 'S0' for ds in S2.DATASETS}  # per dataset: evaluation folder holding the current skill's validation results
    cur_res = evaluate(skill, 'S0')
    cur = {ds: metrics(cur_res, ds) for ds in S2.DATASETS}
    log('S0 ' + json.dumps(cur, ensure_ascii=False))
    (out / 'baseline.json').write_text(json.dumps(cur, ensure_ascii=False, indent=1))

    per_epoch = math.ceil(len(train_items) / batch)
    total = per_epoch * args.epochs
    records, snapshots, step = [], [], 0
    for epoch in range(1, args.epochs + 1):
        accepted_this_epoch = 0
        for items in balanced_batches(train_items, epoch, batch):
            step += 1
            L = lr_for(step, total)
            folder = out / 'steps' / f'step_{step:02d}'
            folder.mkdir(parents=True, exist_ok=True)
            done = folder / 'record.json'
            if done.exists():  # resume
                r = json.loads(done.read_text())
                records.append(r)
                skill = S2.Skill.from_json((folder / 'skill.json').read_text())
                cur_eval, cur = r['cur_eval_after'], r['cur_after']
                accepted_this_epoch += r['n_accepted']
                cur_res = [r for ds in S2.DATASETS for r in evaluate(skill, cur_eval[ds], [v for v in val_items if v['dataset'] == ds])]
                continue
            log(f'=== step {step}/{total} (epoch {epoch})  L={L}  batch={len(items)}  chars MER {skill.chars("MER2024")} MELD {skill.chars("MELD")}')
            results = RO.run_many(items, provider, skill, folder / 'rollout', args.workers, log=lambda *_: None)
            rows = {it['id']: it['row'] for it in items}
            ok = [r for r in results if r['status'] == 'success']
            for r in ok:
                r['_row'] = rows[r['id']]
            record = dict(step=step, epoch=epoch, L=L, batch=len(items), per_ds={}, n_accepted=0)
            for ds in S2.DATASETS:
                rs = [r for r in ok if r['dataset'] == ds]
                x = dict(batch=sum(it['dataset'] == ds for it in items), rollout_correct=sum(r['prediction'] == r['label'] for r in rs),
                         types={t: sum(T.classify(r) == t for r in rs) for t in T.FAIL_ORDER + T.SUCC_ORDER}, gates=[], lint_rejected=[], failure_patterns=[])
                record['per_ds'][ds] = x
                if not rs:
                    continue
                fail_g, succ_g = T.piles(rs, seed=SEED + step)
                x.update(fail_groups=[len(g) for g in fail_g], succ_groups=[len(g) for g in succ_g])
                rdir = folder / ds
                fp, sp, summaries = RF.reflect_groups(client, skill, ds, fail_g, succ_g, L, buffer_text([q for q in records if q['epoch'] == epoch], ds),
                                                      rdir / 'reflect', args.workers, log)
                for s in summaries:
                    x['failure_patterns'] += s if isinstance(s, list) else [s]
                merged = RF.merge_all(client, skill, ds, fp, sp, rdir / 'merge')
                selected = RF.select_per_module(client, skill, ds, merged, L, rdir / 'merge')
                copies = forbidden + [e['observation'] for r in rs for e in r['first']['evidence']]
                val_ds = [v for v in val_items if v['dataset'] == ds]
                for m in S2.MODULES:
                    edits = []
                    for e in selected[m]:
                        reason = S2.lint(e, ds, copies)
                        (x['lint_rejected'].append(dict(edit=e, reason=reason)) if reason else edits.append(e))
                    if not edits:
                        continue
                    cand, applied, rejected = skill.apply(ds, edits)
                    if rejected:
                        x.setdefault('apply_rejected', []).extend(dict(edit=e, reason=r) for e, r in rejected)
                    if not applied or cand.sections[ds].modules[m] == skill.sections[ds].modules[m]:
                        continue
                    condensed = False
                    if cand.chars(ds) > S2.SECTION_CHARS:
                        sec, why = RF.condense(client, skill, ds, applied, rdir / f'condense_{m}')
                        if sec is None:
                            x['gates'].append(dict(module=m, edits=applied, accepted=False, why=why))
                            log(f'[{ds}] {m}: {why}')
                            continue
                        cand, condensed = skill.replace_section(ds, sec), True
                    name = f'step{step:02d}_{ds}_{m}'
                    reuse = None if (m == 'first' or condensed) else cur_eval[ds]
                    res = evaluate(cand, name, val_ds, reuse)
                    new = metrics(res, ds)
                    old_by = by_id([r for r in cur_res if r['dataset'] == ds and r.get('status') == 'success'])
                    if m == 'first' or condensed:
                        ok_gate = new['bal'] >= cur[ds]['bal'] + BAL_MARGIN and new['correct'] >= cur[ds]['correct']
                        why = f'bal {cur[ds]["bal"]:.3f}->{new["bal"]:.3f} (need +{BAL_MARGIN}), correct {cur[ds]["correct"]}->{new["correct"]} (need not lower)'
                    else:
                        changed = [r for r in res if r['status'] == 'success' and r['id'] in old_by and r['prediction'] != old_by[r['id']]['prediction']]
                        right = sum(r['prediction'] == r['row_label'] for r in changed)
                        wrong = sum(old_by[r['id']]['prediction'] == r['row_label'] for r in changed)
                        ok_gate = len(changed) >= 1 and right - wrong >= 1
                        why = f'changed {len(changed)} answers, newly right {right}, newly wrong {wrong} (need >=1 change and net >=1)'
                    x['gates'].append(dict(module=m, edits=applied, condensed=condensed, accepted=ok_gate, why=why, cur=cur[ds], cand=new))
                    log(f'[{ds}] gate {m}{" (condensed)" if condensed else ""}: {why} -> {"ACCEPT" if ok_gate else "reject"}')
                    if ok_gate:
                        # the candidate's validation results on this dataset replace the current ones; the other dataset is unchanged
                        merged_res = [r for r in cur_res if r['dataset'] != ds] + res
                        skill, cur_res, cur = cand, merged_res, dict(cur, **{ds: new})
                        cur_eval = dict(cur_eval, **{ds: name})
                        record['n_accepted'] += 1
            accepted_this_epoch += record['n_accepted']
            record.update(cur_after=cur, cur_eval_after=cur_eval, skill_sha=skill.sha256())
            (folder / 'skill.json').write_text(skill.to_json())
            done.write_text(json.dumps(record, ensure_ascii=False, indent=1))
            records.append(record)
        # end of epoch: re-measure the current skill on the whole validation set
        res = evaluate(skill, f'epoch{epoch}_full')
        snap = {ds: metrics(res, ds) for ds in S2.DATASETS}
        snapshots.append(dict(epoch=epoch, val=snap, bal_sum=round(sum(snap[d]['bal'] for d in S2.DATASETS), 4), skill_sha=skill.sha256()))
        (out / f'skill_epoch{epoch}.json').write_text(skill.to_json())
        (out / f'skill_epoch{epoch}.md').write_text(skill.markdown(), encoding='utf8')
        log(f'epoch {epoch} done: accepted {accepted_this_epoch}  validation ' + json.dumps(snap, ensure_ascii=False))
        if accepted_this_epoch == 0 and epoch < args.epochs:
            log(f'early stop: nothing accepted in epoch {epoch}')
            break
    best = max(snapshots, key=lambda s: (s['bal_sum'], -s['epoch']))
    best_skill = (out / f'skill_epoch{best["epoch"]}.json').read_text()
    (out / 'best_skill.json').write_text(best_skill)
    (out / 'best_skill.md').write_text(S2.Skill.from_json(best_skill).markdown(), encoding='utf8')
    summary = dict(provider=provider, epochs_run=len(snapshots), steps=step, baseline=json.loads((out / 'baseline.json').read_text()), snapshots=snapshots,
                   best_epoch=best['epoch'], best_skill_sha=best['skill_sha'],
                   gates=[dict(step=r['step'], ds=ds, module=g['module'], accepted=g['accepted'], why=g['why']) for r in records for ds, x in r['per_ds'].items() for g in x['gates']])
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    log(f'done: best epoch {best["epoch"]}  ' + json.dumps(best['val'], ensure_ascii=False))
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gemini'], default='gemini')
    ap.add_argument('--epochs', type=int, default=EPOCHS)
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--train-n', type=int, default=16)
    ap.add_argument('--val-n', type=int, default=10)
    ap.add_argument('--batch', type=int, default=0)
    ap.add_argument('--workers', type=int, default=4)
    run(ap.parse_args())
