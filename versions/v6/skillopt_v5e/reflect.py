"""Reflect -> aggregate -> select of one training step (design page, figure 4, steps 2-5).

Reflect: for every group of up to 8 trajectories ONE reflection model (the optimizer client) reads the text cards AND watches the frames
(Gemini also hears the audio) and writes a patch whose edits name their module. Failure groups use analyst_error, success groups
analyst_success. Aggregate: SkillOpt's hierarchical merge (8 patches per merge call, failure and success piles separately, then
failure-first final merge); these calls carry text only. Select: per module, if the pool exceeds the edit budget L, one ranking call keeps the top L.
All calls are cached on disk by a signature of their inputs, so an interrupted step resumes without repeating calls.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import re
import time
from pathlib import Path

from llm import v6c
from skill import MODULES, OPS
import trajectory as T

PROMPTS = Path(__file__).resolve().parent / 'prompts_opt'
MAX_TOKENS = dict(analyst=4096, merge=4096, rank=1500)
MERGE_BATCH = 8


def load_prompt(name):
    text = (PROMPTS / f'{name}.md').read_text(encoding='utf8')
    return re.sub(r'<!--.*?-->\s*', '', text, flags=re.S).strip()


def system_for(name):
    return load_prompt('task') + '\n\n---\n\n' + load_prompt(name)


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def call_opt(client, folder, tag, system, parts, validate, max_tokens):
    """Cached model call with up to 3 attempts (format repair feedback). parts: list of (kind, value)."""
    folder = Path(folder)
    sig = sha(dict(system=sha(system), parts=[(k, v if k == 'text' else v6c.digest(v)) for k, v in parts], model=client.model, max_tokens=max_tokens))
    dest = folder / (tag + '.json')
    if dest.exists():
        cached = v6c.read(dest)
        if cached.get('signature') == sig:
            return cached['output']
    feedback, error, text = None, None, ''
    for attempt in range(1, 4):
        actual = parts if feedback is None else parts + [('text', feedback)]
        text = ''
        try:
            text, raw, seconds = client.generate_parts(system, actual, max_tokens)
            value = v6c.v4.parse_json(text)
            validate(value)
            v6c.save(dest, dict(signature=sig, output=value, attempt=attempt, seconds=seconds, usage=raw.get('usage'), model=client.model))
            return value
        except Exception as exc:
            error = client.clean(exc)
            v6c.save(folder / 'calls' / f'{tag}_error{attempt}.json', dict(error=error, response=text[:3000]))
            if text:
                feedback = ('Your previous answer was invalid: ' + error + '\nReturn the complete, corrected JSON object only; use the original input and add no facts.')
            if any(code in error for code in ('HTTP 401', 'HTTP 403', 'HTTP 404')):
                break
            if attempt < 3:
                time.sleep((60 if 'HTTP 429' in error else 20) * attempt if not text else 3)
    raise RuntimeError(f'{tag}: {error}')


# ---------------------------------------------------------------------------------------------- validators
def _edit_ok(e):
    assert isinstance(e, dict) and e.get('module') in MODULES and e.get('op') in OPS, 'each edit needs module (first|relook|reflect) and op'


def v_analyst(v):
    assert isinstance(v, dict) and isinstance(v.get('patch'), dict) and isinstance(v['patch'].get('edits'), list), 'need patch.edits list'
    for e in v['patch']['edits']:
        _edit_ok(e)


def v_merge(v):
    assert isinstance(v, dict) and isinstance(v.get('edits'), list), 'need edits list'
    for e in v['edits']:
        _edit_ok(e)


def v_rank(n):
    def check(v):
        assert isinstance(v, dict) and isinstance(v.get('selected_indices'), list) and all(isinstance(i, int) and 0 <= i < n for i in v['selected_indices'])
    return check


# ---------------------------------------------------------------------------------------------- reflect
def analyst_parts(skill, items, L, buffer_ctx, provider):
    parts = [('text', '## Current skill document\n' + skill.markdown() + ('\n\n## Step context (earlier steps of this run)\n' + buffer_ctx if buffer_ctx else '') +
              f'\n\n## Budget\nL = {L} (at most {L} edits)\n\n## Trajectories ({len(items)}) with their media\n')]
    for k, (res, row) in enumerate(items, 1):
        frames, relook, audio = T.media(res, row, with_audio=(provider == 'gemini'))
        parts.append(('text', T.card(res, row, k)))
        parts.append(('text', f'轨迹 #{k} 的 {len(frames)} 帧（按时间顺序）：'))
        parts += [('image', p) for p in frames]
        if relook:
            parts.append(('text', f'轨迹 #{k} 回看窗口里的 {len(relook)} 帧（按时间顺序）：'))
            parts += [('image', p) for p in relook]
        if audio:
            parts.append(('text', f'轨迹 #{k} 的音频：'))
            parts.append(('audio', audio))
    parts.append(('text', 'Return the JSON object now.'))
    return parts


def reflect_groups(client, skill, fail_groups, succ_groups, L, buffer_ctx, folder, provider, workers=4, log=print):
    """One analyst call per group. Returns (failure_patches, success_patches, summaries)."""
    jobs = [('fail', i, g) for i, g in enumerate(fail_groups)] + [('succ', i, g) for i, g in enumerate(succ_groups)]

    def one(job):
        kind, i, group = job
        items = [(r, r['_row']) for r in group]
        value = call_opt(client, folder, f'analyst_{kind}_{i:02d}', system_for('analyst_error' if kind == 'fail' else 'analyst_success'),
                         analyst_parts(skill, items, L, buffer_ctx, provider), v_analyst, MAX_TOKENS['analyst'])
        edits = [dict(e, source_type='failure' if kind == 'fail' else 'success') for e in value['patch']['edits']][:L]
        log(f'  [reflect {kind} group {i}] {len(group)} trajectories -> {len(edits)} edits')
        return kind, dict(edits=edits, reasoning=value['patch'].get('reasoning', '')), value.get('failure_summary') or value.get('success_patterns')
    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        out = list(ex.map(one, jobs))
    fail = [p for k, p, _ in out if k == 'fail' and p['edits']]
    succ = [p for k, p, _ in out if k == 'succ' and p['edits']]
    summaries = [s for k, _, s in out if k == 'fail' and s]
    return fail, succ, summaries


# ---------------------------------------------------------------------------------------------- aggregate
def _merge_call(client, skill, patches, prompt_name, source_type, folder, tag):
    text = '## Current skill document\n' + skill.markdown() + f'\n\n## Patches to merge ({len(patches)})\n' + json.dumps(patches, ensure_ascii=False, indent=1)
    value = call_opt(client, folder, tag, system_for(prompt_name), [('text', text)], v_merge, MAX_TOKENS['merge'])
    return dict(edits=[dict(e, source_type=e.get('source_type', source_type)) for e in value['edits']], reasoning=value.get('reasoning', ''))


def merge_pile(client, skill, patches, source_type, folder):
    """Hierarchical merge of one pile (failure or success); 8 patches per merge call."""
    cur = [p for p in patches if p and p.get('edits')]
    level = 0
    while len(cur) > 1:
        level += 1
        nxt = []
        for bi in range(0, len(cur), MERGE_BATCH):
            chunk = cur[bi:bi + MERGE_BATCH]
            nxt.append(chunk[0] if len(chunk) == 1 else _merge_call(client, skill, chunk, 'merge_failure' if source_type == 'failure' else 'merge_success',
                                                                    source_type, folder, f'merge_{source_type}_L{level}_{bi // MERGE_BATCH}'))
        cur = nxt
    return cur[0] if cur else None


def merge_all(client, skill, fail_patches, succ_patches, folder):
    f = merge_pile(client, skill, fail_patches, 'failure', folder)
    s = merge_pile(client, skill, succ_patches, 'success', folder)
    if f and s:
        return _merge_call(client, skill, [f, s], 'merge_final', 'failure', folder, 'merge_final')
    return f or s or dict(edits=[], reasoning='no patches')


# ---------------------------------------------------------------------------------------------- select
def select_per_module(client, skill, merged, L, folder):
    """Per module: more than L edits -> one ranking call keeps the top L. Returns dict module -> list of edits."""
    by = {m: [e for e in merged['edits'] if e['module'] == m] for m in MODULES}
    out = {}
    for m, edits in by.items():
        if len(edits) <= L:
            out[m] = edits
            continue
        desc = '\n'.join(f'[{i}] {json.dumps(e, ensure_ascii=False)}' for i, e in enumerate(edits))
        text = f'## Current module `{m}`\n{skill.modules[m] or "(empty)"}\n\n## Edit pool ({len(edits)} edits, budget={L})\n{desc}\n\nSelect the {L} most important edits. Return their 0-based indices in priority order.'
        value = call_opt(client, folder, f'rank_{m}', system_for('ranking'), [('text', text)], v_rank(len(edits)), MAX_TOKENS['rank'])
        picked = []
        for i in value['selected_indices']:
            if i not in picked:
                picked.append(i)
        out[m] = [edits[i] for i in picked[:L]]
    return out
