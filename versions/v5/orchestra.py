"""v5-E: one full-modal agent answers from all modalities; when it names an uncertain point it looks back (denser frames in the doubtful
time window + that audio segment), then reflects and gives the final answer. Only the v4 disagreement samples are run. Experts, graph
and organization text are NOT provided. Gold labels are never sent; report() reads them. Design: docs/v5-orchestra.html.

Stages per sample (cached, resumable):  first  ->  [uncertainty named?]  ->  relook  ->  reflect  -> final
  first   : 8 original frames + subtitle (+ audio for Gemini), candidate set only          (1 call)
  relook  : + 16 frames inside the named window (+ the audio segment); answers the point    (1 call, only if uncertainty named)
  reflect : first answer + relook result; REVISE needs cited new evidence                   (1 call, only if uncertainty named)

Usage (server, project root):
  python versions/v5/orchestra.py run --provider gemini|gpt [--ids ...] [--workers 4]
  python versions/v5/orchestra.py report --provider gemini|gpt
"""
from __future__ import annotations
import argparse
import concurrent.futures
import fcntl
import importlib.util
import json
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'v4'))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
_spec = importlib.util.spec_from_file_location('v4pipeline', HERE.parent / 'v4' / 'pipeline.py')
v4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v4)
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import v5_prompts as P5  # noqa: E402
from engine import ROOT, Client, digest, prepare_frames, save, update_log  # noqa: E402

VERSION = 'single_agent_relook_v5e'
BASE = ROOT / 'outputs' / VERSION
V4 = ROOT / 'outputs' / 'reflect_debate_v4'
TOK = dict(first=2400, relook=2600, reflect=2400)
RELOOK_FRAMES = 16
PAD = 0.5  # seconds added on both sides of the window the agent names
MAX_EDGE = 448  # same long-edge limit as the original frames; the new information is temporal density
read = v4.read
nonempty = v4.nonempty


def disagreement_rows(provider):
    out = []
    for r in v4.rows('all'):
        res = V4 / provider / r['id'] / 'result.json'
        if res.exists() and read(res).get('status') == 'success' and read(res)['route'] != 'common_label':
            out.append(r)
    return out


# ------------------------------------------------------------------------------------------- re-look input
def window_inputs(row, folder, start, end):
    """16 frames evenly spaced in [start-PAD, end+PAD] (clamped to the video) and the matching audio segment (wav). Returns (frames, times, audio_path)."""
    cap = cv2.VideoCapture(row['video'])
    if not cap.isOpened():
        raise RuntimeError('video cannot be opened')
    count, fps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), float(cap.get(cv2.CAP_PROP_FPS))
    dur = count / fps
    s, e = max(0.0, start - PAD), min(dur, end + PAD)
    if e - s < 0.8:  # a very short window: widen it around its centre
        c = (s + e) / 2
        s, e = max(0.0, c - 0.4), min(dur, c + 0.4)
    idx = np.linspace(int(s * fps), min(count - 1, int(e * fps)), RELOOK_FRAMES).round().astype(int).tolist()
    out_dir = folder / 'relook_frames'
    out_dir.mkdir(parents=True, exist_ok=True)
    paths, times = [], []
    try:
        for i, k in enumerate(idx):
            cap.set(cv2.CAP_PROP_POS_FRAMES, k)
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f'cannot decode frame {k}')
            h, w = frame.shape[:2]
            sc = min(1.0, MAX_EDGE / max(w, h))
            frame = cv2.resize(frame, (max(1, round(w * sc)), max(1, round(h * sc))))
            p = out_dir / f'relook_{i:02d}.jpg'
            cv2.imwrite(str(p), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            paths.append(str(p))
            times.append(round(k / fps, 3))
    finally:
        cap.release()
    audio_path = None
    if row.get('audio') and Path(row['audio']).is_file():
        data, sr = sf.read(row['audio'])
        a, b = int(s * sr), max(int(s * sr) + 1, int(e * sr))
        seg = data[a:b]
        if len(seg):
            audio_path = str(folder / 'relook_audio.wav')
            sf.write(audio_path, seg, sr)
    return paths, times, audio_path, (round(s, 3), round(e, 3))


# ------------------------------------------------------------------------------------------- validators
def v_first(cands, audio, subtitle, duration):
    def check(v):
        assert isinstance(v, dict) and set(v) == {'answer', 'reason', 'evidence', 'uncertainty'}, 'keys must be answer, reason, evidence, uncertainty'
        assert v['answer'] in cands, 'answer must be one of candidate_labels'
        assert nonempty(v['reason'])
        ev = v['evidence']
        assert isinstance(ev, list) and 1 <= len(ev) <= 3, 'evidence needs 1-3 items'
        ids = []
        for e in ev:
            assert isinstance(e, dict) and set(e) == {'id', 'source', 'location', 'observation'} and all(nonempty(e[k]) for k in e), 'bad evidence item'
            assert e['source'] in ('visual', 'audio', 'subtitle')
            assert e['source'] != 'audio' or audio, 'No actual audio supplied'
            assert e['source'] != 'subtitle' or subtitle, 'No subtitle supplied'
            ids.append(e['id'])
        assert len(set(ids)) == len(ids)
        u = v['uncertainty']
        if u is not None:
            assert isinstance(u, dict) and set(u) == {'point', 'why', 'relook'}, 'uncertainty keys: point, why, relook'
            assert nonempty(u['point']) and nonempty(u['why'])
            r = u['relook']
            assert isinstance(r, dict) and set(r) == {'start_sec', 'end_sec'}
            assert all(isinstance(r[k], (int, float)) and not isinstance(r[k], bool) for k in r), 'start_sec and end_sec must be numbers'
            assert 0 <= r['start_sec'] < r['end_sec'] <= duration + 0.5, f'relook window must lie inside 0..{duration:.2f} seconds'
    return check


def v_relook(first_ids):
    def check(v):
        assert isinstance(v, dict) and set(v) == {'point_answer', 'new_observations', 'evidence_check'}
        assert v['point_answer'] in ('是', '否', '不确定')
        no = v['new_observations']
        assert isinstance(no, list) and len(no) <= 4 and all(isinstance(x, dict) and set(x) == {'location', 'observation'} and nonempty(x['location']) and nonempty(x['observation']) for x in no)
        ec = v['evidence_check']
        assert isinstance(ec, list) and {x.get('id') for x in ec} == set(first_ids), f'evidence_check must cover {sorted(first_ids)}'
        assert all(x.get('status') in ('被支持', '被削弱', '不变') and nonempty(x.get('note')) for x in ec)
    return check


def v_reflect(cands, first_answer):
    def check(v):
        assert isinstance(v, dict) and set(v) == {'decision', 'answer', 'reason', 'new_evidence'}
        assert v['decision'] in ('KEEP', 'REVISE') and v['answer'] in cands and nonempty(v['reason'])
        ne = v['new_evidence']
        assert isinstance(ne, list) and all(nonempty(x) for x in ne)
        if v['decision'] == 'KEEP':
            assert v['answer'] == first_answer and not ne, 'KEEP keeps the first answer and has no new_evidence'
        else:
            assert v['answer'] != first_answer and ne, 'REVISE needs another label and at least one new_evidence item'
    return check


# ------------------------------------------------------------------------------------------- one sample
def sample(row, provider):
    client = Client(provider)
    folder = BASE / provider / row['id']
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rp = folder / 'result.json'
        if rp.exists() and read(rp).get('status') == 'success':
            return read(rp)
        t0 = time.time()
        try:
            res4 = read(V4 / provider / row['id'] / 'result.json')
            cands, classes = res4['candidate_labels'], row['classes']
            info = prepare_frames(row)
            audio = row['audio'] if client.config.get('audio_supported') else None
            subtitle = row.get('subtitle', '').strip()
            cap = cv2.VideoCapture(row['video'])
            duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / float(cap.get(cv2.CAP_PROP_FPS))
            cap.release()
            media = v4.media_payload(row, info, audio)
            media.pop('allowed_labels', None)
            media['video_duration_seconds'] = round(duration, 2)
            payload = dict(media, candidate_labels=cands)
            first = v4.call_stage(folder, 'first', client, P5.first_answer(classes, cands), payload, info['frames'], audio, v_first(cands, audio, subtitle, duration), TOK['first'])
            flagged = first['uncertainty'] is not None
            out = dict(first_answer=first['answer'], flagged=flagged, uncertainty=first['uncertainty'])
            if not flagged:
                out.update(prediction=first['answer'], route='first_no_doubt')
            else:
                r = first['uncertainty']['relook']
                paths, times, apath, win = window_inputs(row, folder, float(r['start_sec']), float(r['end_sec']))
                use_audio = apath if audio else None
                rp_payload = dict(media, candidate_labels=cands, first_answer=dict(answer=first['answer'], reason=first['reason'], evidence=first['evidence']),
                                  uncertain_point=first['uncertainty']['point'], relook_window_seconds=list(win), relook_frame_times_seconds=times,
                                  relook_audio_provided=bool(use_audio))
                look = v4.call_stage(folder, 'relook', client, P5.relook(classes, cands), rp_payload, info['frames'] + paths, use_audio,
                                     v_relook([e['id'] for e in first['evidence']]), TOK['relook'])
                rf_payload = dict(media, candidate_labels=cands, first_answer=dict(answer=first['answer'], reason=first['reason'], evidence=first['evidence']),
                                  uncertain_point=first['uncertainty']['point'], relook_result=look)
                ref = v4.call_stage(folder, 'reflect', client, P5.reflect_final(classes, cands), rf_payload, info['frames'], audio,
                                    v_reflect(cands, first['answer']), TOK['reflect'])
                out.update(prediction=ref['answer'], route='relook_' + ref['decision'].lower(), relook_window=list(win), point_answer=look['point_answer'],
                           n_new_observations=len(look['new_observations']), decision=ref['decision'], has_audio_segment=bool(use_audio))
            result = dict(id=row['id'], dataset=row['dataset'], split=row['split'], provider=provider, model=client.model, status='success', version=VERSION,
                          candidate_labels=cands, v4_prediction=res4['prediction'], label=row['label'], elapsed_seconds=time.time() - t0, **out)
        except Exception as exc:
            result = dict(id=row['id'], provider=provider, status='error', version=VERSION, error=client.clean(exc),
                          traceback=client.clean(traceback.format_exc()), elapsed_seconds=time.time() - t0)
        save(rp, result)
        return result


def worker(provider, workers, ids=None):
    rows = disagreement_rows(provider)
    if ids:
        rows = [r for r in rows if r['id'] in ids]
        assert len(rows) == len(ids), 'some ids are not disagreement samples of this provider'
    BASE.mkdir(parents=True, exist_ok=True)
    save(BASE / provider / ('protocol_smoke.json' if ids else 'protocol.json'), dict(
        version=VERSION, provider=provider, samples=len(rows), workers=workers, max_tokens=TOK, relook_frames=RELOOK_FRAMES, pad_seconds=PAD, max_edge=MAX_EDGE,
        source='disagreement samples of outputs/reflect_debate_v4', prompts_sha256=digest(HERE / 'v5_prompts.py'), pipeline_sha256=digest(Path(__file__)),
        provided='original media + candidate set (+ boundary notes); no expert output, graph or organization text', labels_not_sent=True))
    with (BASE / (provider + ('_smoke' if ids else '') + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        update_log(f'v5-E 单 agent 回看 启动：{provider}，{len(rows)} 条不一致样本{"（冒烟）" if ids else ""}，workers={workers}；输出 outputs/{VERSION}/{provider}。')
        done = {}
        for _ in range(2):
            todo = [r for r in rows if done.get(r['id']) != 'success']
            if not todo:
                break

            def one(r):
                res = sample(r, provider)
                print(json.dumps(dict(provider=provider, id=r['id'], status=res['status'], pred=res.get('prediction'), route=res.get('route'), error=(res.get('error') or '')[:240]), ensure_ascii=False), flush=True)
                return r['id'], res['status']
            with concurrent.futures.ThreadPoolExecutor(workers) as ex:
                done.update(dict(ex.map(one, todo)))
        ok = sum(v == 'success' for v in done.values())
        update_log(f'v5-E 单 agent 回看 结束：{provider}，成功 {ok}/{len(rows)}{"（冒烟）" if ids else ""}。')
        return 0 if ok == len(rows) else 1


# ------------------------------------------------------------------------------------------- report (gold read only here)
def report(provider):
    rows = disagreement_rows(provider)
    dv = json.loads((ROOT / 'metrics' / 'direct_vote_experiment.json').read_text())['per_sample'][provider]
    runs = {x['id']: x['runs'] for x in dv}
    c, per = Counter(), []
    for r in rows:
        p = BASE / provider / r['id'] / 'result.json'
        if not p.exists() or read(p).get('status') != 'success':
            c['missing'] += 1
            continue
        x = read(p)
        g = r['label']
        fo, fi, fl = x['first_answer'] == g, x['prediction'] == g, x['flagged']
        c['n'] += 1
        c['first ok'] += fo
        c['final ok'] += fi
        c['direct run1 ok'] += runs[r['id']][0] == g
        c['direct mean(5) ok x5'] += sum(q == g for q in runs[r['id']])
        c['v4 ok'] += x['v4_prediction'] == g
        c['flagged'] += fl
        c['flagged & first ok'] += fl and fo
        c['unflagged'] += not fl
        c['unflagged & first ok'] += (not fl) and fo
        if fl:
            c['revise'] += x['decision'] == 'REVISE'
            c['revise wrong->right'] += x['decision'] == 'REVISE' and not fo and fi
            c['revise right->wrong'] += x['decision'] == 'REVISE' and fo and not fi
            c['revise wrong->wrong'] += x['decision'] == 'REVISE' and not fo and not fi
            c['flagged final ok'] += fi
            c['point yes'] += x['point_answer'] == '是'
            c['point no'] += x['point_answer'] == '否'
            c['point unsure'] += x['point_answer'] == '不确定'
            c['new obs 0'] += x['n_new_observations'] == 0
        for key in (r['dataset'],):
            c[key + ' n'] += 1
            c[key + ' first ok'] += fo
            c[key + ' final ok'] += fi
        per.append(dict(id=r['id'], gold=g, first=x['first_answer'], final=x['prediction'], flagged=fl, route=x['route'], direct_runs=runs[r['id']]))
    c['direct mean(5) ok'] = c['direct mean(5) ok x5'] / 5
    out = dict(counts=dict(c), per_sample=per)
    (ROOT / 'metrics' / f'{VERSION}_{provider}.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
    print(provider, json.dumps(dict(c), ensure_ascii=False, sort_keys=True))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['run', 'report'])
    ap.add_argument('--provider', choices=['gpt', 'gemini'], required=True)
    ap.add_argument('--ids', nargs='*')
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    if a.mode == 'run':
        sys.exit(worker(a.provider, a.workers, a.ids))
    report(a.provider)


if __name__ == '__main__':
    main()
