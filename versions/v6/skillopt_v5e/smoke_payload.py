"""Payload smoke test for the reflection model: one request that carries GROUP samples (8 frames each, optional relook frames,
Gemini also one audio clip each). The instruction asks only for a one-line description per sample (no emotion label, no gold).
Writes outputs/v6_skillopt_v5e/_smoke/payload_<provider>.json (status, seconds, usage, counts; never keys).

Usage (server, project root):  .venv/bin/python versions/v6/skillopt_v5e/smoke_payload.py --provider gemini|gpt [--group 8] [--relook 2] [--models]
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import OptClient, optimizer_client, v6c  # noqa: E402

ROOT = v6c.ROOT
spec = importlib.util.spec_from_file_location('orchestra5', ROOT / 'versions' / 'v5' / 'orchestra.py')
o5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o5)

SYSTEM = ('你是载荷测试助手。输入里有多个样本，每个样本先有一行“样本 #k”，随后是它的若干帧图片（按时间顺序），可能还有一段音频。'
          '请对每个样本各写一行：scene（不超过 20 字，画面里能看到什么）和 audio（不超过 20 字，音频的特点；没有音频写“无”）。'
          '不要判断情绪，不要使用任何标签。只返回JSON：{"samples":[{"k":1,"scene":"...","audio":"..."}]}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gemini', 'gpt'], required=True)
    ap.add_argument('--group', type=int, default=8)
    ap.add_argument('--relook', type=int, default=2, help='how many of the samples also get 16 relook frames')
    ap.add_argument('--models', action='store_true', help='only list the model ids of the endpoint that contain gpt / sol / 6')
    a = ap.parse_args()
    client = optimizer_client(a.provider)
    out_dir = ROOT / 'outputs' / 'v6_skillopt_v5e' / '_smoke'
    out_dir.mkdir(parents=True, exist_ok=True)
    if a.models:
        ids = client.list_models()
        keep = [i for i in ids if any(k in i.lower() for k in ('sol', 'gpt-6', 'gpt6', 'gemini-3'))]
        print(json.dumps(dict(provider=a.provider, configured=client.model, total=len(ids), matching=keep), ensure_ascii=False))
        return
    rows = []
    for ds in v6c.DATASETS:
        rows += v6c.pool_rows(ds)[:a.group // 2]
    rows = rows[:a.group]
    parts, n_images, n_audio = [], 0, 0
    for k, row in enumerate(rows, 1):
        info = v6c.prepare_frames(row)
        parts.append(('text', f'样本 #{k}（{row["dataset"]}）：以下是它的 {len(info["frames"])} 帧'))
        for p in info['frames']:
            parts.append(('image', p))
            n_images += 1
        if k <= a.relook:
            folder = out_dir / 'relook' / row['id']
            frames, times, _, win = o5.window_inputs(row, folder, 0.2, 1.4)
            parts.append(('text', f'样本 #{k} 的回看帧（窗口 {win} 秒）'))
            for p in frames:
                parts.append(('image', p))
                n_images += 1
        if a.provider == 'gemini' and row.get('audio') and Path(row['audio']).is_file():
            parts.append(('text', f'样本 #{k} 的音频'))
            parts.append(('audio', row['audio']))
            n_audio += 1
    parts.append(('text', '请返回JSON。'))
    result = dict(provider=a.provider, model=client.model, group=len(rows), images=n_images, audio_clips=n_audio)
    try:
        text, raw, seconds = client.generate_parts(SYSTEM, parts, 2000)
        try:
            value = v6c.v4.parse_json(text)
            n = len(value.get('samples', []))
        except Exception as exc:
            n = -1
            result['parse_error'] = str(exc)[:200]
        result.update(status='ok', seconds=round(seconds, 1), usage=raw.get('usage'), described=n, response_model=raw.get('model'), sample=text[:600])
    except Exception as exc:
        result.update(status='error', error=client.clean(exc)[:800])
    (out_dir / f'payload_{a.provider}.json').write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in result.items() if k != 'sample'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
