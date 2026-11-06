"""Skill document of version 2: one section per dataset (MER2024 / MELD), each with three modules (first / relook / reflect).
A sample's prompt carries only its dataset's section. Edits are dicts {module, op, target, content} applied inside one section.
lint() adds two checks to version 1: label names outside the dataset, and default-label (direction-only) rules.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skillopt_v5e'))
import skill as S1  # noqa: E402  (version 1: edit ops and the basic lint)

MODULES = S1.MODULES
TITLES = S1.TITLES
DATASETS = ('MER2024', 'MELD')
CLASSES = {'MER2024': ['neutral', 'angry', 'sad', 'happy', 'worried', 'surprise'],
           'MELD': ['neutral', 'anger', 'sadness', 'joy', 'surprise', 'fear', 'disgust']}
ALL_LABELS = sorted({c for v in CLASSES.values() for c in v})
SECTION_CHARS = 900
LABEL_WORDS = {'neutral': ['中性', '平静'], 'angry': ['愤怒', '生气'], 'anger': ['愤怒', '生气'], 'sad': ['悲伤', '难过'], 'sadness': ['悲伤', '难过'],
               'happy': ['喜悦', '高兴', '开心'], 'joy': ['喜悦', '高兴', '开心'], 'worried': ['担忧', '担心', '焦虑'], 'surprise': ['惊讶', '吃惊'],
               'fear': ['恐惧', '害怕'], 'disgust': ['厌恶', '反感']}
_label_alt = '|'.join(sorted({w for v in LABEL_WORDS.values() for w in v} | set(ALL_LABELS), key=len, reverse=True))
DEFAULT_PATTERN = re.compile(rf'(优先|默认|一律|统统|果断|倾向于?|宁可|偏向|首选)[^。；;\n]{{0,8}}({_label_alt})|({_label_alt})[^。；;\n]{{0,4}}(优先|为默认|兜底)', re.I)


class Skill:
    def __init__(self, sections=None):
        sections = sections or {}
        self.sections = {d: S1.Skill(sections.get(d, {})) for d in DATASETS}

    @staticmethod
    def empty():
        return Skill()

    @staticmethod
    def from_json(text):
        return Skill(json.loads(text)['sections'])

    def to_json(self):
        return json.dumps(dict(sections={d: s.modules for d, s in self.sections.items()}), ensure_ascii=False, indent=1, sort_keys=True)

    def sha256(self):
        return hashlib.sha256(json.dumps({d: s.modules for d, s in self.sections.items()}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    def chars(self, dataset=None):
        return sum(s.chars() for d, s in self.sections.items() if dataset in (None, d))

    def markdown(self, dataset=None):
        out = []
        for d in DATASETS:
            if dataset in (None, d):
                out.append(f'# {d} 节\n' + self.sections[d].markdown())
        return '\n\n'.join(out)

    def block(self, dataset, module):
        return self.sections[dataset].block(module)

    def replace_section(self, dataset, section):
        new = Skill({d: s.modules for d, s in self.sections.items()})
        new.sections[dataset] = section
        return new

    def apply(self, dataset, edits):
        """Apply edits to one section. Returns (new_skill, applied, rejected). No length cap here (the trainer condenses when needed)."""
        sec = S1.Skill(dict(self.sections[dataset].modules))
        applied, rejected = [], []
        for e in edits:
            reason = sec._apply_one(e)
            (rejected.append((e, reason)) if reason else applied.append(e))
        return self.replace_section(dataset, sec), applied, rejected


def lint(edit, dataset, forbidden_texts=()):
    reason = S1.lint(edit, forbidden_texts)
    if reason:
        return reason
    content = (edit.get('content') or '')
    low = content.lower()
    foreign = [c for c in ALL_LABELS if c not in CLASSES[dataset] and re.search(rf'\b{c}\b', low)]
    if foreign:
        return 'label names of the other dataset: ' + ', '.join(foreign)
    if DEFAULT_PATTERN.search(content):
        return 'default-label / direction-only wording'
    return None


def lint_section_text(modules, dataset):
    """Reason if a whole rewritten section breaks the rules (used for condensed sections)."""
    for m in MODULES:
        r = lint(dict(module=m, op='append', content=modules.get(m, '') or '占位'), dataset)
        if r and not r.startswith('edit longer'):
            return f'{m}: {r}'
    return None
