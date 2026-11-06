"""Trajectories of a rollout: type (F1-F4 failure, S1-S2 success), the text card the reflection model reads, grouping into minibatches,
and the media (frames / audio) that go with each card. Gold labels appear in the cards on purpose (they are only for the reflection model).

Types:  F1 first answer wrong, no uncertainty named (missed doubt)   F2 wrong, uncertainty named, KEEP (look-back did not help)
        F3 first right, REVISE made it wrong                         F4 first wrong, REVISE to another wrong label
        S1 first wrong, REVISE made it right                         S2 final right (stable)
"""
from __future__ import annotations
import json
import random
from pathlib import Path

FAIL_ORDER = ['F1', 'F2', 'F3', 'F4']
SUCC_ORDER = ['S1', 'S2']
DESCRIPTION = {'F1': '首答错且没写不确定点', 'F2': '首答错，写了不确定点，回看后仍保持错答案', 'F3': '首答对，回看后改成了错的', 'F4': '首答错，回看后改成另一个错的',
               'S1': '首答错，回看后改对', 'S2': '最终答对'}
MIN_TAIL = 4
GROUP = 8


def classify(res):
    if res.get('status') != 'success':
        return None
    gold = res['label']
    first_ok, final_ok = res['first_answer'] == gold, res['prediction'] == gold
    if final_ok:
        return 'S2' if first_ok else 'S1'
    if first_ok:
        return 'F3'
    if not res['flagged']:
        return 'F1'
    return 'F4' if res.get('decision') == 'REVISE' else 'F2'


def card(res, row, k):
    """Text card of one trajectory (no sample id: it is called #k)."""
    first, look, ref = res['first'], res.get('look'), res.get('ref')
    src = ', '.join(f'{c}（{"原候选" if s == "original" else "扩充"}）' for c, s in res['sources'].items())
    lines = [f'### 轨迹 #{k}　数据集 {res["dataset"]}　类型 {classify(res)}（{DESCRIPTION[classify(res)]}）',
             f'候选标签：{src}',
             f'字幕：{row.get("subtitle", "").strip() or "（无）"}',
             f'首答：{first["answer"]}　理由：{first["reason"]}']
    for e in first['evidence']:
        lines.append(f'　证据 {e["id"]}（{e["source"]}，{e["location"]}）：{e["observation"]}')
    u = first['uncertainty']
    lines.append('不确定点：无（没有回看）' if u is None else f'不确定点：{u["point"]}（原因：{u["why"]}；回看窗口 {u["relook"]["start_sec"]}–{u["relook"]["end_sec"]} 秒）')
    if look:
        lines.append(f'回看结果：对不确定点的回答={look["point_answer"]}')
        for o in look['new_observations']:
            lines.append(f'　新观察（{o["location"]}）：{o["observation"]}')
        for c in look['evidence_check']:
            lines.append(f'　首答证据 {c["id"]}：{c["status"]}（{c["note"]}）')
        lines.append(f'反思决定：{ref["decision"]}　最终答案：{ref["answer"]}　理由：{ref["reason"]}')
        if ref['new_evidence']:
            lines.append('　所依据的新证据：' + '；'.join(ref['new_evidence']))
    else:
        lines.append(f'最终答案：{res["prediction"]}')
    lines.append(f'标准标签：{res["label"]}')
    return '\n'.join(lines)


def media(res, row, with_audio):
    """(frames, relook_frames, audio_path or None) of one trajectory, for the reflection model."""
    from llm import v6c
    info = v6c.prepare_frames(row)
    relook = list(res.get('relook_frames') or [])
    audio = row['audio'] if with_audio and row.get('audio') and Path(row['audio']).is_file() else None
    return list(info['frames']), relook, audio


def piles(results, seed):
    """(failure_groups, success_groups): each a list of 1..N lists of (result). Same type neighbours, groups of 8, tail < 4 merged back."""
    rng = random.Random(seed)
    out = []
    for order in (FAIL_ORDER, SUCC_ORDER):
        items = [r for r in results if classify(r) in order]
        rng.shuffle(items)
        items.sort(key=lambda r: order.index(classify(r)))  # stable: types adjacent, shuffled inside a type
        groups = [items[i:i + GROUP] for i in range(0, len(items), GROUP)]
        if len(groups) > 1 and len(groups[-1]) < MIN_TAIL:
            tail = groups.pop()
            groups[-1] = groups[-1] + tail
        out.append(groups)
    return out
