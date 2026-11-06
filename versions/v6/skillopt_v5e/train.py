"""SkillOpt-V5E training loop (design: docs/v6-skillopt-v5e-design.html, figure 4; flow chart: docs/v6-skillopt-v5e-flow.html).

--epochs passes over the training set in batches of 40 (Gemini 4 steps, GPT 6 steps per epoch); every epoch reshuffles the order
(seed 42 + 1000 x epoch, so epoch 1 keeps the order of the first run). Per step:
  1 rollout of v5-E with the current skill on the batch (candidate set C' = C + confusion-matrix top-1)
  2 trajectories -> failure / success piles -> groups of 8 -> ONE reflection model per group (sees text cards + frames (+ Gemini audio)) -> patches
  3 hierarchical merge (failure first)   4 per module keep the top L edits (L cosine 4 -> 2 over the steps)
  5 lint (module scope, no sample ids / subtitle copies / numbers / format words, length cap) and apply
  6 gate, module by module (first, relook, reflect) on the validation set: first needs >= current + 2 correct, relook / reflect >= current
    (not lower); a module without edits is skipped. Accepted -> becomes the current skill.
The step buffer (failure patterns + rejected edits shown to the reflection model) is reset every epoch, as in SkillOpt.
At the end of every epoch the current skill is saved as best_skill_epoch<k>.json / .md; the final one also as best_skill.json / .md.
Everything is cached and resumable: re-run the command; with a larger --epochs the run continues after the last finished step.
Not implemented (deviation from SkillOpt): Slow Update and Meta Skill at epoch boundaries.
Gold labels go to the reflection model only (in the trajectory cards); they are never in a target-model request.

  python versions/v6/skillopt_v5e/train.py --provider gemini|gpt [--epochs 1] [--smoke] [--workers 4]
Environment: SKILLOPT_GPT_OPT_MODEL=gpt-6.1-sol selects the GPT optimizer model (user decision).
"""
from __future__ import annotations
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import v6c, optimizer_client  # noqa: E402
import confusion as CF  # noqa: E402
import split as SP  # noqa: E402
import rollout as RO  # noqa: E402
import reflect as RF  # noqa: E402
import trajectory as T  # noqa: E402
from skill import MODULES, Skill, lint  # noqa: E402

BATCH = 40
EPOCHS = 1
L_MAX, L_MIN = 4, 2
MARGIN = {'first': 2, 'relook': 0, 'reflect': 0}
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


def buffer_text(records):
    """Step context for the reflection model: failure patterns and rejected edits of earlier steps (SkillOpt's step buffer; the caller passes this epoch's records only)."""
    if not records:
        return ''
    parts = ['Below is a summary of previous steps. Use it to avoid repeating ineffective edits and to prioritise failure patterns that remain unsolved.']
    for r in records:
        parts.append(f'### Step {r["step"]} - rollout {r["rollout_correct"]}/{r["batch"]} correct')
        for s in r.get('failure_patterns', [])[:6]:
            parts.append('  - ' + (s if isinstance(s, str) else json.dumps(s, ensure_ascii=False))[:300])
        for g in r.get('gates', []):
            if not g['accepted']:
                parts.append(f'  Rejected {g["module"]} edits (validation {g["cur_score"]} -> {g["cand_score"]}): ' + ' | '.join(json.dumps(e, ensure_ascii=False)[:300] for e in g['edits']))
    return '\n'.join(parts)


def run(args):
    provider = args.provider
    tag = 'smoke' if args.smoke else None
    out = SP.provider_dir(provider, tag)
    for d in ('steps', 'eval'):
        (out / d).mkdir(parents=True, exist_ok=True)
    log = Logger(out / 'train.log')
    data = SP.load(provider, tag)
    rng = random.Random(1)
    train_items, val_items = list(data['train']), list(data['val'])
    if args.smoke:  # tiny, mixed datasets
        rng.shuffle(train_items)
        rng.shuffle(val_items)
        train_items, val_items = train_items[:args.train_n], val_items[:args.val_n]
    batch = args.batch or BATCH
    table = CF.load()
    client = optimizer_client(provider)
    forbidden = [it['row'].get('subtitle', '').strip() for it in data['train'] + data['val'] + data['test']]
    log(f'train {len(train_items)}  val {len(val_items)}  batch {batch}  optimizer {client.model}  target {RO.Client(provider).model}')
    (out / 'config.json').write_text(json.dumps(dict(provider=provider, smoke=args.smoke, train=len(train_items), val=len(val_items), batch=batch, epochs=args.epochs,
                                                      L=[L_MAX, L_MIN], margin=MARGIN, optimizer_model=client.model, target_model=RO.Client(provider).model,
                                                      seed=SEED, group=T.GROUP), indent=1))

    # ------------------------------------------------------------ baseline
    def evaluate(skill, name, reuse=None):
        results = RO.run_many(val_items, provider, skill, out / 'eval' / name, table, True, args.workers, log=lambda *_: None,
                              reuse_dir=(out / 'eval' / reuse) if reuse else None)
        return RO.score(results), results

    skill, cur_score, start_step, records = Skill.empty(), None, 1, []
    cur_eval = 'S0'  # evaluation folder of the current skill (its first / relook outputs are re-used by relook / reflect gates)
    base_file = out / 'baseline.json'
    if base_file.exists():
        cur_score = json.loads(base_file.read_text())['val_correct']
    else:
        cur_score, res = evaluate(skill, 'S0')
        base_file.write_text(json.dumps(dict(val_correct=cur_score, val_n=len(val_items), errors=sum(r['status'] != 'success' for r in res)), indent=1))
    log(f'S0 (v5-E + expansion, empty skill) validation: {cur_score}/{len(val_items)}')

    def epoch_batches(epoch):
        order = list(train_items)
        random.Random(SEED + 1000 * epoch).shuffle(order)
        return [order[i:i + batch] for i in range(0, len(order), batch)]

    per_epoch = len(epoch_batches(1))
    total = per_epoch * args.epochs

    def epoch_of(step):
        return (step - 1) // per_epoch + 1
    log(f'{args.epochs} epoch(s) x {per_epoch} steps; L per step (steps run earlier keep the L they were run with): {[lr_for(s, total) for s in range(1, total + 1)]}')

    # ------------------------------------------------------------ resume
    for s in range(1, total + 1):
        rec = out / 'steps' / f'step_{s:02d}' / 'record.json'
        if rec.exists():
            r = json.loads(rec.read_text())
            records.append(r)
            skill = Skill.from_json((out / 'steps' / f'step_{s:02d}' / 'skill.json').read_text())
            cur_score = r['cur_score_after']
            cur_eval = r.get('cur_eval_after', cur_eval)
            start_step = s + 1
    if start_step > 1:
        log(f'resumed after step {start_step - 1}; current validation {cur_score}')

    # ------------------------------------------------------------ steps
    for step in range(start_step, total + 1):
        L = lr_for(step, total)
        epoch = epoch_of(step)
        items = epoch_batches(epoch)[(step - 1) % per_epoch]
        folder = out / 'steps' / f'step_{step:02d}'
        folder.mkdir(parents=True, exist_ok=True)
        log(f'=== step {step}/{total} (epoch {epoch})  L={L}  batch={len(items)}  skill chars={skill.chars()}')
        results = RO.run_many(items, provider, skill, folder / 'rollout', table, True, args.workers, log=lambda *_: None)
        by_id = {it['id']: it for it in items}
        ok = [r for r in results if r['status'] == 'success']
        for r in ok:
            r['_row'] = by_id[r['id']]['row']
        correct_n = RO.score(results)
        types = {t: sum(T.classify(r) == t for r in ok) for t in T.FAIL_ORDER + T.SUCC_ORDER}
        log(f'rollout {correct_n}/{len(items)} correct  types {types}  errors {len(results) - len(ok)}')
        fail_g, succ_g = T.piles(ok, seed=SEED + step)
        record = dict(step=step, epoch=epoch, L=L, batch=len(items), rollout_correct=correct_n, types=types, fail_groups=[len(g) for g in fail_g],
                      succ_groups=[len(g) for g in succ_g], skill_before=skill.sha256(), cur_score_before=cur_score, gates=[], lint_rejected=[])
        failure_patterns = []
        if fail_g or succ_g:
            fp, sp, summaries = RF.reflect_groups(client, skill, fail_g, succ_g, L, buffer_text([r for r in records if r.get('epoch', epoch_of(r['step'])) == epoch]),
                                                folder / 'reflect', provider, args.workers, log)
            for s in summaries:
                failure_patterns += s if isinstance(s, list) else [s]
            merged = RF.merge_all(client, skill, fp, sp, folder / 'merge')
            selected = RF.select_per_module(client, skill, merged, L, folder / 'merge')
            record.update(n_patches=dict(failure=len(fp), success=len(sp)), merged_edits=len(merged['edits']), selected={m: len(v) for m, v in selected.items()})
            copies = forbidden + [e['observation'] for r in ok for e in r['first']['evidence']]
            for m in MODULES:
                edits = []
                for e in selected[m]:
                    reason = lint(e, copies)
                    (record['lint_rejected'].append(dict(edit=e, reason=reason)) if reason else edits.append(e))
                if not edits:
                    continue
                cand, applied, rejected = skill.apply(edits)
                record.setdefault('apply_rejected', []).extend(dict(edit=e, reason=r) for e, r in rejected)
                if not applied or cand.modules[m] == skill.modules[m]:
                    continue
                name = f'step{step:02d}_{m}'
                score, _ = evaluate(cand, name, reuse=None if m == 'first' else cur_eval)
                accepted = score >= cur_score + MARGIN[m]
                record['gates'].append(dict(module=m, edits=applied, cur_score=cur_score, cand_score=score, margin=MARGIN[m], accepted=accepted, val_n=len(val_items)))
                log(f'gate {m}: candidate {score} vs current {cur_score} (margin {MARGIN[m]}) -> {"ACCEPT" if accepted else "reject"}  edits {len(applied)}')
                if accepted:
                    skill, cur_score, cur_eval = cand, score, name
        else:
            log('no usable trajectories in this step')
        record.update(failure_patterns=failure_patterns, skill_after=skill.sha256(), cur_score_after=cur_score, cur_eval_after=cur_eval)
        (folder / 'skill.json').write_text(skill.to_json())
        (folder / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=1))
        records.append(record)
        if step % per_epoch == 0:
            (out / f'best_skill_epoch{epoch}.json').write_text(skill.to_json())
            (out / f'best_skill_epoch{epoch}.md').write_text(skill.markdown(), encoding='utf8')
            log(f'epoch {epoch} done: validation {cur_score}/{len(val_items)}, skill chars {skill.chars()}')

    # ------------------------------------------------------------ result
    (out / 'best_skill.json').write_text(skill.to_json())
    (out / 'best_skill.md').write_text(skill.markdown(), encoding='utf8')
    per_epoch_val = {}
    for r in records:
        per_epoch_val[r.get('epoch', epoch_of(r['step']))] = r['cur_score_after']
    summary = dict(provider=provider, epochs=args.epochs, steps=total, val_after_epoch=per_epoch_val, val_baseline=json.loads(base_file.read_text())['val_correct'], val_final=cur_score, val_n=len(val_items),
                   accepted=[dict(step=r['step'], epoch=r.get('epoch', epoch_of(r['step'])), module=g['module']) for r in records for g in r['gates'] if g['accepted']],
                   rejected=[dict(step=r['step'], epoch=r.get('epoch', epoch_of(r['step'])), module=g['module']) for r in records for g in r['gates'] if not g['accepted']],
                   skill_sha256=skill.sha256(), skill_chars=skill.chars())
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    log('done ' + json.dumps(summary, ensure_ascii=False))
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gemini', 'gpt'], required=True)
    ap.add_argument('--epochs', type=int, default=EPOCHS)
    ap.add_argument('--smoke', action='store_true', help='tiny run into outputs/v6_skillopt_v5e/<provider>_smoke')
    ap.add_argument('--train-n', type=int, default=8)
    ap.add_argument('--val-n', type=int, default=6)
    ap.add_argument('--batch', type=int, default=0)
    ap.add_argument('--workers', type=int, default=4)
    run(ap.parse_args())
