"""v5-E with a skill document and an expanded candidate set (one sample = up to three model calls; design page, figure 1).

Same stages, validators, frame / audio handling and caching as versions/v5/orchestra.py (reused, not modified), with three differences:
  1. the candidate set is C' (original candidates + confusion-matrix top-1 expansion), and the payload carries candidate_sources;
  2. the prompt of each stage gets the candidate-source note (only when something was expanded) and that stage's skill module;
  3. candidates / output folder are arguments (training samples have no v4 result).
Gold labels are never sent (call_stage asserts it); the label is only copied into result.json for scoring.
"""
from __future__ import annotations
import concurrent.futures
import fcntl
import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import v6c  # noqa: E402
import confusion as CF  # noqa: E402
from skill import Skill  # noqa: E402

ROOT = v6c.ROOT
sys.path.insert(0, str(ROOT / 'versions' / 'v5'))
import v5_prompts as P5  # noqa: E402

_spec = importlib.util.spec_from_file_location('orchestra5', ROOT / 'versions' / 'v5' / 'orchestra.py')
o5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(o5)
v4 = v6c.v4
Client = v6c.Client
read = v6c.read
save = v6c.save


def candidate_note(sources):
    """Prompt note on where the candidate labels come from. Empty when nothing was expanded (then the prompt equals plain v5-E)."""
    expanded = [c for c, s in sources.items() if s == 'expanded']
    if not expanded:
        return ''
    original = [c for c, s in sources.items() if s == 'original']
    return ('\n【候选标签的来源】\n输入里的candidate_sources标明每个候选标签的来源：original = 原候选（此前三位专家给出的答案：' + '、'.join(original) +
            '）；expanded = 扩充标签（' + '、'.join(expanded) + '，由程序根据易混淆情况加入，不是专家给出的；含义是：当判断结果是某个原候选时，真实情绪有时是它）。'
            '你只能在candidate_labels里选择答案；原候选与扩充标签同等对待，按画面、声音、字幕里可定位的证据来判断。')


def first_prompt(classes, cands, sources, skill):
    return P5.first_answer(classes, cands) + candidate_note(sources) + skill.block('first')


def relook_prompt(classes, cands, sources, skill):
    return P5.relook(classes, cands) + candidate_note(sources) + skill.block('relook')


def reflect_prompt(classes, cands, sources, skill):
    return P5.reflect_final(classes, cands) + candidate_note(sources) + skill.block('reflect')


def run_sample(item, provider, skill, folder, table, expand=True, reuse_dir=None):
    """One sample. folder is unique per (skill version, purpose). Returns the result dict (also saved as folder/result.json).
    reuse_dir: folder of an earlier run of the same items (the current skill). Its cached stage outputs (first / relook) are copied in
    before the calls; call_stage re-uses them only when the signature (prompt + payload + media + model) is identical, so a gate of the
    relook / reflect module re-runs only the stages whose prompt changed and the score difference comes from that module alone."""
    row = item['row']
    client = Client(provider)
    exp = CF.expand(table, provider, item['dataset'], item['candidates']) if expand else CF.no_expansion(item['candidates'])
    cands, sources = exp['candidates'], exp['sources']
    classes = row['classes']
    folder = Path(folder) / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rp = folder / 'result.json'
        if rp.exists() and read(rp).get('status') == 'success':
            return read(rp)
        if reuse_dir is not None:
            import shutil
            src = Path(reuse_dir) / row['id']
            for tag in ('first', 'relook'):
                if (src / f'{tag}.json').exists() and not (folder / f'{tag}.json').exists():
                    shutil.copy2(src / f'{tag}.json', folder / f'{tag}.json')
        t0 = time.time()
        try:
            info = v6c.prepare_frames(row)
            audio = row['audio'] if client.config.get('audio_supported') else None
            subtitle = row.get('subtitle', '').strip()
            import cv2
            cap = cv2.VideoCapture(row['video'])
            duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / float(cap.get(cv2.CAP_PROP_FPS))
            cap.release()
            media = v4.media_payload(row, info, audio)
            media.pop('allowed_labels', None)
            media['video_duration_seconds'] = round(duration, 2)
            base = dict(media, candidate_labels=cands, candidate_sources=sources)
            first = v4.call_stage(folder, 'first', client, first_prompt(classes, cands, sources, skill), base, info['frames'], audio,
                                  o5.v_first(cands, audio, subtitle, duration), o5.TOK['first'])
            flagged = first['uncertainty'] is not None
            out = dict(first_answer=first['answer'], flagged=flagged, uncertainty=first['uncertainty'], first=first, look=None, ref=None)
            if not flagged:
                out.update(prediction=first['answer'], route='first_no_doubt')
            else:
                r = first['uncertainty']['relook']
                paths, times, apath, win = o5.window_inputs(row, folder, float(r['start_sec']), float(r['end_sec']))
                use_audio = apath if audio else None
                first_view = dict(answer=first['answer'], reason=first['reason'], evidence=first['evidence'])
                look = v4.call_stage(folder, 'relook', client, relook_prompt(classes, cands, sources, skill),
                                     dict(base, first_answer=first_view, uncertain_point=first['uncertainty']['point'], relook_window_seconds=list(win),
                                          relook_frame_times_seconds=times, relook_audio_provided=bool(use_audio)),
                                     info['frames'] + paths, use_audio, o5.v_relook([e['id'] for e in first['evidence']]), o5.TOK['relook'])
                ref = v4.call_stage(folder, 'reflect', client, reflect_prompt(classes, cands, sources, skill),
                                    dict(base, first_answer=first_view, uncertain_point=first['uncertainty']['point'], relook_result=look),
                                    info['frames'], audio, o5.v_reflect(cands, first['answer']), o5.TOK['reflect'])
                out.update(prediction=ref['answer'], route='relook_' + ref['decision'].lower(), relook_window=list(win), decision=ref['decision'],
                           point_answer=look['point_answer'], n_new_observations=len(look['new_observations']), look=look, ref=ref,
                           relook_frames=paths, has_audio_segment=bool(use_audio))
            result = dict(id=row['id'], dataset=row['dataset'], provider=provider, model=client.model, status='success', label=row['label'],
                          candidates=cands, sources=sources, added=exp['added'], skill_sha256=skill.sha256(), elapsed_seconds=time.time() - t0, **out)
        except Exception as exc:
            result = dict(id=row['id'], dataset=row['dataset'], provider=provider, status='error', error=client.clean(exc),
                          traceback=client.clean(traceback.format_exc())[-1500:], elapsed_seconds=time.time() - t0)
        save(rp, result)
        return result


def run_many(items, provider, skill, base_dir, table, expand=True, workers=4, log=print, reuse_dir=None):
    """All items with this skill; two passes (a failed sample is retried once). Returns results in item order."""
    results = {}
    for _ in range(2):
        todo = [it for it in items if results.get(it['id'], {}).get('status') != 'success']
        if not todo:
            break

        def one(it):
            res = run_sample(it, provider, skill, base_dir, table, expand, reuse_dir)
            log(json.dumps(dict(id=it['id'], status=res['status'], pred=res.get('prediction'), route=res.get('route'), error=(res.get('error') or '')[:160]), ensure_ascii=False))
            return it['id'], res
        with concurrent.futures.ThreadPoolExecutor(workers) as ex:
            results.update(dict(ex.map(one, todo)))
    return [results[it['id']] for it in items]


def correct(res):
    return res.get('status') == 'success' and res['prediction'] == res['label']


def score(results):
    return sum(correct(r) for r in results)
