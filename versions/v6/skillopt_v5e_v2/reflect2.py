"""Reflect / merge / select / condense of version 2. Reuses version 1's implementation (versions/v6/skillopt_v5e/reflect.py: cached
calls, analyst with frames + audio, hierarchical failure-first merge, per-module ranking) with two changes:
  - the prompts are version 2's (prompts_opt/ here: task context forbids default-label rules and other-dataset labels), and
  - everything runs on ONE dataset section: the optimizer sees only that section, the request names the dataset and its labels.
condense() rewrites one section that would exceed the cap (SkillOpt's rewrite_skill, adapted); its result still has to pass the gate.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('reflect_v1', HERE.parents[0] / 'skillopt_v5e' / 'reflect.py')
import sys  # noqa: E402
sys.path.insert(0, str(HERE.parents[0] / 'skillopt_v5e'))
R1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R1)
R1.PROMPTS = HERE / 'prompts_opt'  # version 2 prompts (task.md differs; analyst / merge / ranking are copies)

import skill2 as S2  # noqa: E402

call_opt = R1.call_opt
MAX_TOKENS = dict(R1.MAX_TOKENS, condense=4096)


class SectionView:
    """What version 1's reflect code needs from a skill: .markdown() and .modules, for one dataset section, with the dataset named."""
    def __init__(self, skill, dataset):
        self.dataset = dataset
        self.modules = skill.sections[dataset].modules

    def markdown(self):
        return (f'（只编辑数据集 {self.dataset} 这一节；该数据集的标签只有：{", ".join(S2.CLASSES[self.dataset])}）\n'
                + S2.S1.Skill(self.modules).markdown())


def reflect_groups(client, skill, dataset, fail_groups, succ_groups, L, buffer_ctx, folder, workers=4, log=print):
    return R1.reflect_groups(client, SectionView(skill, dataset), fail_groups, succ_groups, L, buffer_ctx, folder, 'gemini', workers, log)


def merge_all(client, skill, dataset, fp, sp, folder):
    return R1.merge_all(client, SectionView(skill, dataset), fp, sp, folder)


def select_per_module(client, skill, dataset, merged, L, folder):
    return R1.select_per_module(client, SectionView(skill, dataset), merged, L, folder)


def _v_condense(v):
    assert isinstance(v, dict) and isinstance(v.get('modules'), dict) and set(v['modules']) <= set(S2.MODULES), 'need modules {first, relook, reflect}'
    assert all(isinstance(x, str) for x in v['modules'].values())


def condense(client, skill, dataset, edits, folder, cap=S2.SECTION_CHARS):
    """One call: rewrite this dataset's section (current text + the new edits) to <= cap characters. Returns a version-1 Skill (the section) or None."""
    text = (f'## Dataset\n{dataset}（标签：{", ".join(S2.CLASSES[dataset])}）\n\n## Length cap\n{cap} characters for the whole section (three modules together)\n\n'
            f'## Current section\n{json.dumps(skill.sections[dataset].modules, ensure_ascii=False, indent=1)}\n\n'
            f'## New edits to incorporate\n{json.dumps(edits, ensure_ascii=False, indent=1)}')
    value = call_opt(client, folder, 'condense', R1.system_for('condense'), [('text', text)], _v_condense, MAX_TOKENS['condense'])
    sec = S2.S1.Skill({m: value['modules'].get(m, '') for m in S2.MODULES})
    if sec.chars() > cap:
        return None, f'condensed section still {sec.chars()} > {cap} characters'
    reason = S2.lint_section_text(sec.modules, dataset)
    if reason:
        return None, 'condensed section rejected by lint: ' + reason
    return sec, None
