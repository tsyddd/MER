"""Resumable, auditable five-stage PPCT evaluation; gold labels never sent."""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import fcntl
import hashlib
import json
import os
import re
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import cv2
import numpy as np
import requests

from reference.ppct_api.graph import build_graph, candidate_pairs
from reference.ppct_api.schemas import (
    EvidenceNode, EvidenceOutput, JointJudgmentOutput, JointEdge,
    OrganizationOutput, RawEvidenceOutput, RelationOutput,
    TemporalEdge, TemporalJudgmentOutput,
)
from reference.ppct_api import prompts as original

ROOT = Path(__file__).resolve().parent


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    tmp.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def update_log(message):
    with (ROOT / 'update.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with (ROOT / 'update.md').open('a') as f:
            f.write('\n- ' + datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S') +
                    '（Asia/Shanghai）：' + message + '\n')


def prepare_frames(row):
    out = ROOT / 'data/frames8' / row['id']
    out.mkdir(parents=True, exist_ok=True)
    metadata = out / 'sampling.json'
    if metadata.exists():
        info = json.loads(metadata.read_text())
        if len(info['frames']) == 8 and all(Path(p).is_file() for p in info['frames']):
            return info
    cap = cv2.VideoCapture(row['video'])
    if not cap.isOpened():
        raise RuntimeError('Video cannot be opened: ' + row['id'])
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if count <= 0 or fps <= 0:
        raise RuntimeError('Invalid video metadata: ' + row['id'])
    indices = np.linspace(0, count - 1, 8).round().astype(int).tolist()
    paths = []
    try:
        for i, index in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f'Cannot decode {row["id"]} frame {index}')
            height, width = frame.shape[:2]
            scale = min(1., 448 / max(width, height))
            frame = cv2.resize(frame, (max(1, round(width * scale)), max(1, round(height * scale))))
            path = out / f'frame_{i:02d}.jpg'
            if not cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85]):
                raise RuntimeError('Frame write failed')
            paths.append(str(path))
    finally:
        cap.release()
    result = dict(frames=paths, frame_indices=indices, source_frames=count,
                  seconds=[i / fps for i in indices], count=8,
                  unique_frames=len(set(indices)), repeated=len(set(indices)) < 8,
                  sha256=[digest(p) for p in paths], max_edge=448)
    save(metadata, result)
    return result


class Client:
    def __init__(self, provider):
        self.provider = provider
        public = json.loads((ROOT / 'configs/providers.json').read_text())[provider]
        self.config = public
        self.model = public['model']
        self.url = public['base_url'].rstrip('/') + '/chat/completions'
        self.key = ''
        if provider != 'omni':
            self.key = json.loads((ROOT / 'configs/private_api.json').read_text())['api_key']
        self.session = requests.Session()
        self.session.trust_env = False
        if public.get('proxy_url'):
            self.session.proxies.update({'http': public['proxy_url'], 'https': public['proxy_url']})

    def clean(self, text):
        return str(text).replace(self.key, '[REDACTED]') if self.key else str(text)

    def generate(self, system, payload, frames=None, audio=None, max_tokens=4096):
        content = []
        for path in frames or []:
            content.append({'type': 'image_url', 'image_url': {
                'url': 'data:image/jpeg;base64,' + base64.b64encode(Path(path).read_bytes()).decode()}})
        if audio:
            data = base64.b64encode(Path(audio).read_bytes()).decode()
            if self.provider == 'omni':
                content.append({'type': 'audio_url', 'audio_url': {'url': 'data:audio/wav;base64,' + data}})
            else:
                content.append({'type': 'input_audio', 'input_audio': {'data': data, 'format': 'wav'}})
        text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        content.append({'type': 'text', 'text': text})
        body = {'model': self.model, 'messages': [
            {'role': 'system', 'content': system}, {'role': 'user', 'content': content}],
            'max_tokens': max_tokens, 'temperature': 0}
        headers = {'Content-Type': 'application/json'}
        if self.key:
            headers['Authorization'] = 'Bearer ' + self.key
        started = time.time()
        r = self.session.post(self.url, json=body, headers=headers, timeout=(45, 600))
        if not r.ok:
            raise RuntimeError(f'HTTP {r.status_code}: ' + self.clean(r.text)[:1500])
        raw = r.json()
        msg = raw['choices'][0]['message']
        text = msg.get('content') or ''
        if isinstance(text, list):
            text = ''.join(p.get('text', '') for p in text if isinstance(p, dict))
        if not text:
            raise ValueError('API returned no final content; finish_reason=' + str(raw['choices'][0].get('finish_reason')))
        return text, raw, time.time() - started


def parse_json(text):
    # Prefer the final answer after a possible external model thinking section.
    text = text.rsplit('</think>', 1)[-1].strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
    try:
        return json.loads(text)
    except ValueError:
        decoder = json.JSONDecoder()
        candidates = []
        for match in re.finditer(r'\{', text):
            try:
                obj, length = decoder.raw_decode(text[match.start():])
                if isinstance(obj, dict):
                    candidates.append((match.start() + length, obj))
            except ValueError:
                pass
        if not candidates:
            raise ValueError('No complete JSON object in final response')
        return max(candidates, key=lambda item: item[0])[1]


def stage(folder, name, client, system, payload, frames, audio, schema=None, validate=None, max_tokens=4096):
    signature = hashlib.sha256(json.dumps(dict(system=system, payload=payload,
        frame_hashes=[digest(p) for p in frames or []],
        audio_hash=digest(audio) if audio else None, model=client.model,
        base_url=client.config['base_url'], max_tokens=max_tokens), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    dest = folder / (name + '.json')
    stamp = folder / (name + '_cache.json')
    if dest.exists() and stamp.exists() and json.loads(stamp.read_text())['signature'] == signature:
        parsed = json.loads(dest.read_text())
        value = schema.model_validate(parsed) if schema else parsed
        if validate:
            validate(value)
        return value
    request = dict(system=system, payload=payload, frames=frames, audio=audio,
                   model=client.model, provider=client.provider, max_tokens=max_tokens,
                   signature=signature)
    save(folder / (name + '_request.json'), request)
    error = None
    feedback = None
    for attempt in range(1, 4):
        generated = False
        try:
            actual_payload = payload if feedback is None else dict(original_input=payload, structure_repair=feedback)
            save(folder / f'{name}_request_attempt{attempt}.json', dict(request, payload=actual_payload))
            text, raw, elapsed = client.generate(system, actual_payload, frames, audio, max_tokens)
            generated = True
            save(folder / f'{name}_response_attempt{attempt}.json', raw)
            (folder / f'{name}_raw_attempt{attempt}.txt').write_text(text)
            recovery_notes = []
            try:
                if client.provider == 'omni' and name == 'perception' and any(c.get('finish_reason') == 'length' for c in raw.get('choices', [])):
                    from omni_tolerance import recover_truncated_perception
                    obj, recovery_notes = recover_truncated_perception(text)
                else:
                    obj = parse_json(text)
            except ValueError:
                if client.provider == 'omni' and name == 'organization':
                    obj = {'text': text.rsplit('</think>', 1)[-1].strip()}
                else:
                    raise
            if client.provider == 'omni':
                from omni_tolerance import normalize
                obj, repairs = normalize(name, obj, payload)
                save(folder / f'{name}_repairs_attempt{attempt}.json', dict(repairs=recovery_notes + repairs, policy='omni_only_structural_tolerance'))
            parsed = schema.model_validate(obj) if schema else obj
            if validate:
                validate(parsed)
            save(dest, parsed.model_dump(mode='json') if schema else parsed)
            save(stamp, dict(signature=signature, seconds=elapsed, usage=raw.get('usage'),
                             response_model=raw.get('model'), attempt=attempt))
            return parsed
        except Exception as exc:
            error = client.clean(exc)
            if generated:
                feedback = dict(validation_error=error, previous_response=text, instruction='Repair only JSON/schema/graph consistency using the original evidence. Do not change observation content or introduce facts. For after edges source time_index must be strictly greater than target; same-index nodes cannot have an after edge. Omit unsupported edges. Return the required complete schema.')
            save(folder / f'{name}_error_attempt{attempt}.json', dict(error=error))
            # A direct baseline uses one completed model response; only transport errors retry.
            if generated and 'direct' in folder.parts:
                break
            # Capability errors must not silently remove an input modality.
            if any(code in error for code in ['HTTP 401', 'HTTP 403', 'HTTP 404']):
                break
            if attempt < 3:
                time.sleep(30 * attempt if any(x in error for x in ['Connection refused', 'Read timed out', 'ProxyError', 'NameResolutionError', 'HTTP 429']) else 2 ** attempt)
    raise RuntimeError(name + ' failed: ' + str(error))


def sensory_prompt(prompt, audio, frames=True):
    prompt = prompt.replace('观看完整视频', '检查提供的8张时间顺序视频帧')
    prompt = prompt.replace('观看原始视频', '检查提供的时间顺序视频帧')
    prompt = prompt.replace('不先确定情绪', '不先确定情绪')
    if audio:
        prompt = prompt.replace('画面或字幕', '画面、实际音频或字幕')
        prompt += '\n实际提供了音轨。Person可包含能从音轨核对的声调、音量、语速与停顿事实，用audio标记来源；不得把字幕内容当成听觉证据。'
    else:
        prompt += '\n本次没有提供音轨，不能臆测语气、声调、音量或语速。'
    return prompt


def final_prompt(row, ppct, audio):
    labels = ', '.join(row['classes'])
    extra = ('结合组织文本和图谱中的实际节点、边定位证据；说明采用了哪些实际节点及其关系，不编造引用。'
             if ppct else '只依据原始媒体与字幕，不存在PPCT组织文本或图谱。')
    return (f'你是情绪识别评测模型。判断指定目标人物当前片段的情绪。候选标签只有：{labels}。'
            '先核对当前人物、时间、画面事实与字幕，区分转述、假设、过去和他人台词。'
            + ('提供音频时可以使用真实听觉线索。' if audio else '没有提供音频，不得编造听觉线索。')
            + extra + '候选情绪须结合当前表达判断，不能只按台词主题或单个动作决定。'
            '用2至4句简洁文字说明可核对的证据。只返回合法JSON，键为reason和answer；'
            'answer必须是上述列表中的单个原始标签，不翻译、不改写，不输出多标签或confidence。')


def sample(row, provider, mode):
    client = Client(provider)
    folder = ROOT / 'outputs' / mode / provider / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    lock = (folder / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    result_path = folder / 'result.json'
    if result_path.exists():
        old = json.loads(result_path.read_text())
        if old.get('status') == 'success':
            return old
    started = time.time()
    current_stage = 'prepare'
    try:
        info = prepare_frames(row)
        frames = info['frames']
        audio = row['audio'] if client.config.get('audio_supported') else None
        # Only these label-free fields are provided upstream. Gold is added after inference.
        context = dict(sample_id=row['id'], target_speaker=row.get('speaker') or 'main person',
                       frame_times_seconds=info['seconds'])
        if row.get('subtitle', '').strip():
            context['subtitle'] = row['subtitle']
        save(folder / 'input_protocol.json', dict(context=context, frames=info, audio=audio,
             model=client.model, mode=mode, ground_truth_not_sent=True))
        graph = organization = None
        if mode == 'ppct':
            current_stage = 'perception'
            raw = stage(folder, current_stage, client, sensory_prompt(original.EVIDENCE_PROMPT, audio),
                        context, frames, audio, RawEvidenceOutput, max_tokens=4096)
            nodes = []
            for layer in ['process', 'person', 'context']:
                for node in getattr(raw, layer).nodes:
                    assert node.type == layer, 'Node type differs from its layer'
                    if not audio:
                        assert 'audio' not in node.evidence_sources, 'Unprovided audio evidence'
                    nodes.append(EvidenceNode(**node.model_dump()))
            evidence = EvidenceOutput(nodes=nodes)
            if not nodes:
                raise ValueError('Empty perception graph')
            save(folder / 'nodes.json', evidence.model_dump(mode='json'))
            by_id = {node.id: node for node in nodes}

            def temporal_valid(out):
                for edge in out.edges:
                    a, b = by_id.get(edge.source), by_id.get(edge.target)
                    assert a and b and a.type == b.type and a.id != b.id, 'Invalid temporal endpoints'
                    assert edge.relation == a.type + '_temporal', 'Temporal relation layer mismatch'
                    if edge.temporal_relation == 'after':
                        assert a.time_index > b.time_index, 'after source must occur later than target'
                    elif edge.temporal_relation == 'simultaneous':
                        assert a.time_index == b.time_index, 'simultaneous nodes must share event phase'

            payload = dict(context=context, nodes=[n.model_dump(mode='json') for n in nodes])
            current_stage = 'temporal'
            temporal = stage(folder, current_stage, client, sensory_prompt(original.TEMPORAL_PROMPT, audio),
                             payload, frames, audio, TemporalJudgmentOutput, temporal_valid, 3072)
            pairs = {layer: candidate_pairs([n for n in nodes if n.type == layer])
                     for layer in ['process', 'person', 'context']}

            def joint_valid(out):
                seen = set()
                for edge in out.edges:
                    a, b = by_id.get(edge.source), by_id.get(edge.target)
                    assert a and b and a.id != b.id and a.type == b.type, 'Invalid joint endpoints'
                    assert edge.relation == a.type + '_joint', 'Joint layer mismatch'
                    pair = frozenset([a.id, b.id])
                    assert pair not in seen, 'Duplicate joint pair'
                    seen.add(pair)
                    assert any({p['source'], p['target']} == {a.id, b.id} for p in pairs[a.type])

            current_stage = 'joint'
            joint = stage(folder, current_stage, client, sensory_prompt(original.JOINT_PROMPT, audio),
                          dict(payload, candidate_pairs=pairs), frames, audio,
                          JointJudgmentOutput, joint_valid, 3072)
            evidence.temporal_relations = [TemporalEdge(source=e.source, target=e.target,
                relation=e.temporal_relation, reason=e.reason, entity_anchor=e.entity_anchor)
                for e in temporal.edges]
            relations = {layer: RelationOutput(edges=[JointEdge(**e.model_dump()) for e in joint.edges
                         if e.relation == layer + '_joint']) for layer in ['process', 'person', 'context']}
            current_stage = 'program_graph'
            graph = build_graph(evidence, relations).model_dump(mode='json')
            save(folder / 'graph.json', graph)
            current_stage = 'organization'
            org_prompt = original.ORGANIZATION_PROMPT.replace('六分类', '数据集候选')
            org_prompt += '\n本阶段只收到已建立的图谱和字幕，不重新观看视频或收听音频；只组织输入事实，不引入未在节点中的观察，不给最终分类标签。'
            org = stage(folder, current_stage, client, org_prompt,
                        dict(context=context, graph=graph), [], None, OrganizationOutput, max_tokens=3072)
            organization = org.text
        current_stage = 'final'
        payload = dict(context, allowed_labels=row['classes'])
        if mode == 'ppct':
            payload.update(organization=organization, graph=graph)

        def final_valid(obj):
            assert isinstance(obj, dict) and set(obj) == {'reason', 'answer'}, 'Final schema mismatch'
            assert isinstance(obj['reason'], str) and obj['reason'].strip(), 'Missing explanation'
            assert obj['answer'] in row['classes'], 'Answer outside dataset label space'

        answer = stage(folder, current_stage, client, final_prompt(row, mode == 'ppct', audio),
                       payload, frames, audio, validate=final_valid, max_tokens=4096)
        result = dict(id=row['id'], dataset=row['dataset'], model=client.model,
                      provider=provider, mode=mode, status='success', frames=8,
                      audio_provided=bool(audio), subtitle_provided=bool(row.get('subtitle')),
                      prediction=answer['answer'], emotion_analysis=answer['reason'],
                      output=answer['reason'] + '\n<answer>' + answer['answer'] + '</answer>',
                      label=row['label'], elapsed_seconds=time.time() - started,
                      node_count=len(graph['nodes']) if graph else None,
                      edge_count=len(graph['edges']) if graph else None)
        save(result_path, result)
        return result
    except Exception as exc:
        result = dict(id=row['id'], dataset=row['dataset'], provider=provider, mode=mode,
                      model=client.model, status='error', stage=current_stage,
                      error=client.clean(exc), traceback=client.clean(traceback.format_exc()),
                      label=row['label'], elapsed_seconds=time.time() - started)
        save(result_path, result)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', choices=['gpt', 'gemini', 'omni'], required=True)
    parser.add_argument('--mode', choices=['ppct', 'direct'], default='ppct')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    rows = [json.loads(l) for l in (ROOT / 'data/manifests/validation.jsonl').open()]
    assert len(rows) == 80 and len({r['id'] for r in rows}) == 80
    if args.smoke:
        rows = [next(r for r in rows if r['dataset'] == ds) for ds in ['MER2024', 'MELD']]
    out = ROOT / 'outputs' / args.mode / args.provider
    out.mkdir(parents=True, exist_ok=True)
    lock = (out / 'runner.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    status_file = out / ('smoke_summary.json' if args.smoke else 'summary.json')
    update_log(f'启动 {args.provider}/{args.mode}，{len(rows)}条，workers={args.workers}；结果目录 {out.relative_to(ROOT)}。')
    done = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(sample, r, args.provider, args.mode): r for r in rows}
        for future in concurrent.futures.as_completed(pending):
            result = future.result()
            done.append(result)
            stats = {}
            for ds in ['MER2024', 'MELD', 'ALL']:
                expected = [r for r in rows if ds == 'ALL' or r['dataset'] == ds]
                rs = [r for r in done if ds == 'ALL' or r['dataset'] == ds]
                good = [r for r in rs if r['status'] == 'success']
                correct = sum(r['prediction'] == r['label'] for r in good)
                stats[ds] = dict(expected=len(expected), processed=len(rs), valid=len(good),
                                 correct=correct, accuracy_all=correct / len(expected),
                                 accuracy_valid=correct / len(good) if good else None)
            report = dict(provider=args.provider, mode=args.mode, frames=8,
                          status='finished' if len(done) == len(rows) else 'running',
                          smoke=args.smoke, updated=time.time(), metrics=stats)
            save(status_file, report)
            print(json.dumps(dict(progress=len(done), total=len(rows), id=result['id'],
                                  status=result['status'], stage=result.get('stage'))), flush=True)
    (out / ('smoke_results.jsonl' if args.smoke else 'results.jsonl')).write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in sorted(done, key=lambda r: r['id'])))
    errors = [r for r in done if r['status'] != 'success']
    update_log(f'{args.provider}/{args.mode} 本轮结束：{len(done) - len(errors)}/{len(rows)}有效；'
               f'错误{len(errors)}；统计 {status_file.relative_to(ROOT)}。未成功项可按阶段恢复。')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
