"""v5-E rollout of version 2: the same as version 1 (versions/v6/skillopt_v5e/rollout.py) except that
  - the candidate set is NOT expanded (C = the original candidates; the candidate-source note is therefore empty), and
  - each stage gets the module of the sample's OWN dataset section.
Version 1's run_sample reads the skill through skill.block(module); a small adapter gives it the right section.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skillopt_v5e'))
import rollout as RO1  # noqa: E402

score = RO1.score
correct = RO1.correct


class _SectionView:
    """Looks like a version-1 Skill to rollout.py: block(module) returns this dataset's module; sha256 identifies the whole skill."""
    def __init__(self, skill, dataset):
        self.skill, self.dataset = skill, dataset

    def block(self, module):
        return self.skill.block(self.dataset, module)

    def sha256(self):
        return self.skill.sha256()


def run_many(items, provider, skill, base_dir, workers=4, log=print, reuse_dir=None):
    """Like version 1's run_many, no expansion, per-dataset section. Items of both datasets may be mixed."""
    out = {}
    for ds in ('MER2024', 'MELD'):
        part = [it for it in items if it['dataset'] == ds]
        if part:
            res = RO1.run_many(part, provider, _SectionView(skill, ds), base_dir, None, False, workers, log, reuse_dir)
            out.update({r['id']: r for r in res})
    return [out[it['id']] for it in items]
