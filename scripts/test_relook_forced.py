"""Forced test of the re-look and reflect stages of versions/v5/orchestra.py (the first-pass smoke never named an uncertain point).
Takes the cached first answer of a sample, injects a synthetic uncertain point and window, and runs the window extraction, relook and
reflect calls into a scratch folder (outputs/_relook_forced_test, not part of any result). Server only.
Usage: python scripts/test_relook_forced.py --provider gemini --id MELD/dia198_utt2
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('orch', ROOT / 'versions/v5/orchestra.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ap = argparse.ArgumentParser()
ap.add_argument('--provider', required=True)
ap.add_argument('--id', required=True)
a = ap.parse_args()
row = next(r for r in m.v4.rows('all') if r['id'] == a.id)
client = m.Client(a.provider)
first = json.loads((m.BASE / a.provider / a.id / 'first.json').read_text())['output']
res4 = m.read(m.V4 / a.provider / a.id / 'result.json')
cands, classes = res4['candidate_labels'], row['classes']
info = m.prepare_frames(row)
audio = row['audio'] if client.config.get('audio_supported') else None
folder = ROOT / 'outputs' / '_relook_forced_test' / a.provider / a.id
folder.mkdir(parents=True, exist_ok=True)
paths, times, apath, win = m.window_inputs(row, folder, 0.3, 1.4)
print('window', win, 'frames', len(paths), 'audio segment', bool(apath), 'times', times[:3], '...', times[-2:])
media = m.v4.media_payload(row, info, audio)
media.pop('allowed_labels', None)
use_audio = apath if audio else None
fa = dict(answer=first['answer'], reason=first['reason'], evidence=first['evidence'])
pt = '说话者的眉眼和手势是否显示出对对方的不满'
look = m.v4.call_stage(folder, 'relook', client, m.P5.relook(classes, cands), dict(media, candidate_labels=cands, first_answer=fa, uncertain_point=pt, relook_window_seconds=list(win),
                       relook_frame_times_seconds=times, relook_audio_provided=bool(use_audio)), info['frames'] + paths, use_audio, m.v_relook([e['id'] for e in first['evidence']]), m.TOK['relook'])
ref = m.v4.call_stage(folder, 'reflect', client, m.P5.reflect_final(classes, cands), dict(media, candidate_labels=cands, first_answer=fa, uncertain_point=pt, relook_result=look),
                      info['frames'], audio, m.v_reflect(cands, first['answer']), m.TOK['reflect'])
print('first', first['answer'], '| relook point_answer', look['point_answer'], 'new_obs', len(look['new_observations']), '| reflect', ref['decision'], ref['answer'])
print(json.dumps(look, ensure_ascii=False)[:600])
