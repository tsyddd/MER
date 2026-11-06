"""The skill document: ONE prompt with three modules (first answer / look back / reflect), updated module by module.

A module is plain Chinese text (empty at the start). Edits come from the reflection model as dicts
{module, op, target, content}; ops follow SkillOpt: append / insert_after / replace / delete, applied inside the named module only.
lint() rejects edits that would leak sample-specific information or change the output format (design: section 4 of the design page).
"""
from __future__ import annotations
import hashlib
import json
import re

MODULES = ('first', 'relook', 'reflect')
TITLES = {'first': '首答模块（A 区分线索 + B 何时写不确定点）', 'relook': '回看模块（C 回看时怎么看）', 'reflect': '反思模块（D 何时改答案）'}
OPS = ('append', 'insert_after', 'replace', 'delete')
MAX_CHARS = 1500          # whole document
MAX_EDIT_CHARS = 400      # one edit

ID_PATTERN = re.compile(r'(MER2024|MELD)\s*/|sample_?\d+|samplenew|dia\d+_utt\d+|\bdia\d+\b|utt\d+')
FORMAT_PATTERN = re.compile(r'输出字段|返回格式|JSON|json|schema|字段名|必须返回|只返回')
NUMBER_PATTERN = re.compile(r'\d+\s*%|\d+\s*/\s*\d+|\d+\s*(条|个样本|次|例)')
GOLD_PATTERN = re.compile(r'标准标签|金标签|真实标签是|ground.?truth', re.I)


class Skill:
    def __init__(self, modules=None):
        self.modules = {m: (modules or {}).get(m, '').strip() for m in MODULES}

    # ------------------------------------------------------------------ io
    @staticmethod
    def empty():
        return Skill()

    @staticmethod
    def from_json(text):
        return Skill(json.loads(text)['modules'])

    def to_json(self):
        return json.dumps(dict(modules=self.modules), ensure_ascii=False, indent=1, sort_keys=True)

    def sha256(self):
        return hashlib.sha256(json.dumps(self.modules, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    def chars(self):
        return sum(len(v) for v in self.modules.values())

    def markdown(self):
        return '\n\n'.join(f'## {TITLES[m]}\n{self.modules[m] or "（空）"}' for m in MODULES)

    # ------------------------------------------------------------------ use in prompts
    def block(self, module):
        """Text appended to the prompt of the stage that owns `module` ('' while the module is empty)."""
        text = self.modules[module]
        if not text:
            return ''
        return '\n【经验技能（从训练样本总结的通用经验，只作参考；不改变上面的输出格式和规则）】\n' + text

    # ------------------------------------------------------------------ edits
    def apply(self, edits):
        """Apply edits one by one on a copy. Returns (new_skill, applied, rejected[(edit, reason)])."""
        new = Skill(dict(self.modules))
        applied, rejected = [], []
        for e in edits:
            reason = new._apply_one(e)
            (rejected.append((e, reason)) if reason else applied.append(e))
        if new.chars() > MAX_CHARS:
            return self, [], [(e, f'skill would exceed {MAX_CHARS} characters') for e in edits]
        return new, applied, rejected

    def _apply_one(self, e):
        m, op, target, content = e.get('module'), e.get('op'), (e.get('target') or '').strip(), (e.get('content') or '').strip()
        text = self.modules[m]
        if not text and op in ('insert_after', 'replace') and target in ('', '（空）', '(empty)', '（空)'):
            op = 'append'  # the empty module is shown as a placeholder; treat edits on it as append
        if op == 'append':
            self.modules[m] = (text + '\n' + content).strip()
        elif op in ('insert_after', 'replace', 'delete'):
            i = text.find(target)
            if not target or i < 0:
                return 'target not found in module'
            end = i + len(target)
            if op == 'insert_after':
                line_end = text.find('\n', end)
                line_end = len(text) if line_end < 0 else line_end
                self.modules[m] = (text[:line_end] + '\n' + content + text[line_end:]).strip()
            elif op == 'replace':
                self.modules[m] = (text[:i] + content + text[end:]).strip()
            else:
                self.modules[m] = (text[:i] + text[end:]).strip()
        return None


def lint(edit, forbidden_texts=()):
    """Reason string if the edit must be dropped, else None. forbidden_texts: subtitle / evidence strings of the samples (no verbatim copies)."""
    if not isinstance(edit, dict) or edit.get('module') not in MODULES:
        return 'module must be one of first / relook / reflect'
    if edit.get('op') not in OPS:
        return 'unknown op'
    content = (edit.get('content') or '').strip()
    target = (edit.get('target') or '').strip()
    if edit['op'] != 'delete' and not content:
        return 'empty content'
    if edit['op'] != 'append' and not target:
        return 'missing target'
    if len(content) > MAX_EDIT_CHARS:
        return f'edit longer than {MAX_EDIT_CHARS} characters'
    for name, pattern in (('sample id', ID_PATTERN), ('output-format wording', FORMAT_PATTERN), ('statistics / numbers', NUMBER_PATTERN), ('gold-label wording', GOLD_PATTERN)):
        if pattern.search(content):
            return f'content contains {name}'
    for s in forbidden_texts:
        if len(s) >= 6 and s in content:
            return 'content copies a subtitle / evidence text of a sample'
    return None
