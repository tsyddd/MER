"""R2-MAD step 2: one comprehensive caption per sample from Gemini (it sees the 8 frames, the audio track and the subtitle in one call).
The task question Q = caption + emotion-recognition question (labels listed) is built from it by common.question_text. The caption call
is label-free (no allowed_labels, no gold). Shared by both providers' memories.

Usage (server, project root):
  .venv/bin/python versions/v6/captions.py run --set train|test [--workers 4]
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import time
from common import (DATASETS, OUT, TOKENS, Client, pool_rows, prepare_frames, read, save, test_rows, update_log, v4, v4_disagreement_ids)
import prompts_v6 as P6

CAPTIONS = OUT / 'caption'


def validate(v):
    assert isinstance(v, dict) and set(v) == {'caption'} and isinstance(v['caption'], str) and 60 <= len(v['caption'].strip()) <= 2000, 'caption must be a 60-2000 character string'


def caption_for(row):
    client = Client('gemini')
    folder = CAPTIONS / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    info = prepare_frames(row)
    audio = row['audio']  # Gemini: audio supported
    payload = v4.media_payload(row, info, audio)
    payload.pop('allowed_labels')
    return v4.call_stage(folder, 'caption', client, P6.CAPTION, payload, info['frames'], audio, validate, TOKENS['caption'])['caption'].strip()


def get_caption(row):
    f = CAPTIONS / row['id'] / 'caption.json'
    return read(f)['output']['caption'].strip() if f.exists() else caption_for(row)


def rows_for(which):
    if which in ('train', 'train-smoke'):
        sel = read(OUT / 'pool' / ('selection.json' if which == 'train' else 'selection_smoke.json'))
        ids = {i for ds in sel.values() for p in ('gemini', 'gpt') for i in ds[p]['selected']}
        lookup = {r['id']: r for ds in DATASETS for r in pool_rows(ds)}
        return [lookup[i] for i in sorted(ids)]
    ids = sorted(set(v4_disagreement_ids('gemini')) | set(v4_disagreement_ids('gpt')))
    lookup = test_rows()
    return [lookup[i] for i in ids]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['run'])
    ap.add_argument('--set', choices=['train', 'train-smoke', 'test', 'smoke'], required=True)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    if a.set == 'smoke':
        rows = [r for ds in DATASETS for r in pool_rows(ds)[:2]]
    else:
        rows = rows_for(a.set)
    update_log(f'R²-MAD Caption 启动：集合 {a.set}，{len(rows)} 条，Gemini 一次综合描述（帧 + 音轨 + 字幕，不含标签）；请求级并发 4；输出 outputs/v6_rmad/caption。')
    ok = 0
    errors = []

    def one(r):
        try:
            caption_for(r) if not (CAPTIONS / r['id'] / 'caption.json').exists() else None
            return r['id'], None
        except Exception as exc:  # noqa: BLE001
            return r['id'], f'{type(exc).__name__}: {str(exc)[:200]}'
    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        for i, (rid, err) in enumerate(pool.map(one, rows), 1):
            if err:
                errors.append((rid, err))
            else:
                ok += 1
            if i % 20 == 0:
                print(f'[{time.strftime("%T")}] {i}/{len(rows)} ok={ok} err={len(errors)}', flush=True)
    update_log(f'R²-MAD Caption 结束：集合 {a.set}，成功 {ok}/{len(rows)}，失败 {len(errors)}。')
    for e in errors:
        print('ERR', e)


if __name__ == '__main__':
    main()
