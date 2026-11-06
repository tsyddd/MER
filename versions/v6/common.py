"""Shared helpers of the R2-MAD (v6) pipeline. Loads the v4 pipeline as a module (cached model calls, validators, payloads), adds a
request-level concurrency limit per provider (Gemini 4, GPT 2: at most that many HTTP requests in flight in this process), and
defines the data locations. Gold labels are never sent to a model; only report/memory-building code reads them.
"""
from __future__ import annotations
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'versions' / 'v4'))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
_spec = importlib.util.spec_from_file_location('v4pipeline', ROOT / 'versions' / 'v4' / 'pipeline.py')
v4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v4)
from engine import Client, digest, prepare_frames, save, update_log  # noqa: E402

read = v4.read
nonempty = v4.nonempty
labels_of = v4.labels_of
ROLES = v4.ROLES
OUT = ROOT / 'outputs' / 'v6_rmad'
V4_OUT = ROOT / 'outputs' / 'reflect_debate_v4'
GRAPH_POOL = ROOT / 'data' / 'gemini_graph_pool_v6'
SOURCE = Path('/media/liang/12T/han/emotion_eval_5models_4frames_20261030')
OLD_400 = Path('/media/liang/12T/han/self_evolution_mer_meld_200_20261101')
DATASETS = ['MER2024', 'MELD']
SEED = 42
TOKENS = dict(organization=2048, r0=3200, debate=3800, summary=2600, caption=1800, state=1200)

# ------------------------------------------------------------------------------------------------ request-level concurrency
LIMITS = {'gemini': int(os.environ.get('V6_LIMIT_GEMINI', 5)), 'gpt': int(os.environ.get('V6_LIMIT_GPT', 4))}
_SLOTS = ROOT / 'logs' / 'v6_slots'
_orig_generate = Client.generate


class _Slot:
    """Cross-process request slot: LIMITS[provider] flock files; a request holds one while in flight (all v6 processes share the cap)."""
    def __init__(self, provider):
        import fcntl
        self.fcntl = fcntl
        self.provider = provider
        self.fd = None

    def __enter__(self):
        import time
        folder = _SLOTS / self.provider
        folder.mkdir(parents=True, exist_ok=True)
        while self.fd is None:
            for i in range(LIMITS[self.provider]):
                fd = open(folder / f'slot{i}.lock', 'a')
                try:
                    self.fcntl.flock(fd, self.fcntl.LOCK_EX | self.fcntl.LOCK_NB)
                    self.fd = fd
                    return self
                except OSError:
                    fd.close()
            time.sleep(0.25)

    def __exit__(self, *exc):
        self.fcntl.flock(self.fd, self.fcntl.LOCK_UN)
        self.fd.close()


def _limited_generate(self, *args, **kwargs):
    if self.provider not in LIMITS:
        return _orig_generate(self, *args, **kwargs)
    with _Slot(self.provider):
        return _orig_generate(self, *args, **kwargs)


Client.generate = _limited_generate


# ------------------------------------------------------------------------------------------------ rows
def pool_rows(dataset):
    """All samples of the 5-model evaluation folder that pass the media filter and are NOT in the old 400, in a fixed seeded order."""
    import random
    probe = json.loads((SOURCE / 'self_evolution_media_probe.json').read_text())
    old = {json.loads(l)['id'] for l in (OLD_400 / dataset / 'selected_200.jsonl').open() if l.strip()}
    rows = []
    for line in (SOURCE / 'manifests' / (dataset + '.jsonl')).open():
        if not line.strip():
            continue
        r = json.loads(line)
        p = probe.get(r['id'], {})
        if p.get('error') or not (0 < p.get('video_seconds', 0) <= 60 and 0 < p.get('audio_seconds', 0) <= 60) or r['id'] in old:
            continue
        rows.append(dict(r, split='pool'))
    random.Random(SEED).shuffle(rows)
    return rows


def test_rows():
    return {r['id']: r for r in v4.rows('all')}


def v4_disagreement_ids(provider):
    out = []
    for r in v4.rows('all'):
        res = V4_OUT / provider / r['id'] / 'result.json'
        if res.exists() and read(res).get('status') == 'success' and read(res)['route'] != 'common_label':
            out.append(r['id'])
    return out


# ------------------------------------------------------------------------------------------------ small text helpers
def compact(o):
    """Short text of one expert output: answer, open emotion, reason (no evidence list: its frame ids belong to that sample only)."""
    s = f"答案：{o['answer']}；开放情绪：{o['open_emotion']}；理由：{str(o['reason'])[:320]}"
    if o.get('alt_answer'):
        s += f"；备选：{o['alt_answer']}"
    return s


def consensus_ratio(outputs):
    """Largest number of experts sharing the same primary answer / 3."""
    from collections import Counter
    return max(Counter(o['answer'] for o in outputs.values()).values()) / len(outputs)


def question_text(row, caption):
    classes = row['classes']
    speaker = row.get('speaker') or 'main person'
    return f'【片段综合描述】{caption}\n【任务】判断说话者（{speaker}）在该片段中表达的情绪，候选标签：{", ".join(classes)}。'
