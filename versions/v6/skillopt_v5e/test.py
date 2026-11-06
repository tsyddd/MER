"""Test of SkillOpt-V5E on the 117 test samples (Gemini 62 + GPT 55; v4-disagreement samples of the old 400). Run only after the user has approved
the frozen skill (design page, stage 2).

Modes (each writes outputs/v6_skillopt_v5e/<provider>/test/<mode>/ and metrics/v6_skillopt_v5e_<provider>_<mode>.json):
  skill         the frozen best_skill.json + candidate expansion
  control       empty skill, NO expansion: a second run of plain v5-E (noise estimate of a single run)
  expand_only   empty skill + expansion (separates the effect of the expansion from the skill; optional)

  python versions/v6/skillopt_v5e/test.py --provider gemini|gpt --mode skill|control|expand_only [--skill path] [--workers 4]
Gold labels are only read to score. Known limits: the dev-set samples were analysed many times before; the 80-sample confusion matrix contains 20 test samples.
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import v6c  # noqa: E402
import confusion as CF  # noqa: E402
import split as SP  # noqa: E402
import rollout as RO  # noqa: E402
from skill import Skill  # noqa: E402

ROOT = v6c.ROOT


def report(results, provider, mode, extra):
    c = Counter()
    for r in results:
        if r['status'] != 'success':
            c['missing'] += 1
            continue
        g = r['label']
        fo, fi, fl = r['first_answer'] == g, r['prediction'] == g, r['flagged']
        c['n'] += 1
        c['first ok'] += fo
        c['final ok'] += fi
        c['flagged'] += fl
        c['flagged & first ok'] += fl and fo
        c['expanded labels present'] += any(s == 'expanded' for s in r['sources'].values())
        c['gold in candidates'] += g in r['candidates']
        c['gold only via expansion'] += g in r['candidates'] and r['sources'][g] == 'expanded'
        if fl:
            c['revise'] += r['decision'] == 'REVISE'
            c['revise wrong->right'] += r['decision'] == 'REVISE' and not fo and fi
            c['revise right->wrong'] += r['decision'] == 'REVISE' and fo and not fi
        c[r['dataset'] + ' n'] += 1
        c[r['dataset'] + ' final ok'] += fi
    out = dict(provider=provider, mode=mode, counts=dict(c), **extra)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gemini', 'gpt'], required=True)
    ap.add_argument('--mode', choices=['skill', 'control', 'expand_only'], required=True)
    ap.add_argument('--skill', default=None)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int, default=0, help='first N test samples only (smoke)')
    a = ap.parse_args()
    out = SP.provider_dir(a.provider)
    items = SP.load(a.provider)['test']
    if a.limit:
        items = items[:a.limit]
    table = CF.load()
    if a.mode == 'skill':
        path = Path(a.skill) if a.skill else out / 'best_skill.json'
        skill, expand = Skill.from_json(path.read_text()), True
    else:
        skill, expand = Skill.empty(), a.mode == 'expand_only'
    name = a.mode + (f'_{skill.sha256()[:8]}' if a.mode == 'skill' else '') + (f'_limit{a.limit}' if a.limit else '')
    print(f'{a.provider} {name}: {len(items)} samples, skill chars {skill.chars()}, expansion {expand}', flush=True)
    results = RO.run_many(items, a.provider, skill, out / 'test' / name, table, expand, a.workers)
    rep = report(results, a.provider, a.mode, dict(skill_sha256=skill.sha256(), expansion=expand, samples=len(items), limit=a.limit))
    path = ROOT / 'metrics' / f'v6_skillopt_v5e_{a.provider}_{name}.json'
    path.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf8')
    print(json.dumps(rep['counts'], ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
