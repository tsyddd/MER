"""Wait for own restarted service, verify four media requests, resume Omni only."""
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

import requests
from engine import ROOT, Client, prepare_frames, save, update_log
from frozen_graph_experts import BASE, rows, report, audit

LOG = ROOT / 'logs/concurrency4'


def main():
    LOG.mkdir(parents=True, exist_ok=True)
    with (LOG/'resume.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        save(LOG/'resume.pid', os.getpid())
        session = requests.Session()
        session.trust_env = False
        endpoint = Client('omni').config['base_url'].rstrip('/').removesuffix('/v1')
        started = time.time()
        while time.time()-started < 90*60:
            try:
                response = session.get(endpoint+'/v1/models', timeout=8)
                response.raise_for_status()
                break
            except requests.RequestException:
                save(LOG/'status.json', dict(state='waiting_for_model_reload', pid=os.getpid(), elapsed=time.time()-started))
                time.sleep(30)
        else:
            raise RuntimeError('Service not ready within90min; no experiment requests sent')
        selected = []
        for ds in ['MER2024','MELD']:
            selected.extend([r for r in rows() if r['dataset']==ds][:2])
        barrier = threading.Barrier(4)
        def probe(index, row):
            frames = prepare_frames(row)
            payload = dict(target_speaker=row.get('speaker') or 'main person', allowed_labels=row['classes'],
                           frame_times_seconds=frames['seconds'])
            if row.get('subtitle'): payload['subtitle'] = row['subtitle']
            barrier.wait(timeout=30)
            began = time.time()
            text, raw, seconds = Client('omni').generate(
                'Describe the target person emotion using visible and audible evidence, then finish with exactly one <answer>label</answer> from allowed_labels.',
                payload, frames['frames'], row['audio'], 512)
            result = dict(id=row['id'], started=began, ended=time.time(), seconds=seconds,
                          frames=8, audio=True, text=text, raw=raw)
            save(LOG/f'probe_{index}.json', result)
            assert text.strip(), 'Empty probe response'
            return result
        peak = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(probe, i, row) for i,row in enumerate(selected)]
            while not all(f.done() for f in futures):
                try:
                    metrics = session.get(endpoint+'/metrics', timeout=3).text
                    current = sum(float(line.rsplit(' ',1)[1]) for line in metrics.splitlines()
                                  if re.match(r'vllm:num_requests_running(?:\{|\s)', line))
                    peak = max(peak, current)
                except (requests.RequestException, ValueError): pass
                time.sleep(.5)
            results = [f.result() for f in futures]
        overlap = max(r['started'] for r in results) < min(r['ended'] for r in results)
        save(LOG/'verification.json', dict(success=True, simultaneous_requests=4, intervals_overlap=overlap,
                                          observed_running_peak=peak, server_max_num_seqs=4, client_workers=4,
                                          samples=[r['id'] for r in results], time=time.time()))
        assert overlap, 'Four client requests did not overlap'
        update_log(f'4路实际8帧+音频请求全部成功，客户端区间重叠，服务metrics最高Running={peak}。Omni客户端4workers，保留成功样本与阶段缓存；仅恢复未完成Omni，不调用GPT/Gemini。验证logs/concurrency4/verification.json。')
        for attempt in [1,2]:
            if audit('omni')['complete']: break
            log = LOG/f'omni_resume_attempt{attempt}.log'
            with log.open('a') as stream:
                env = dict(os.environ, PPCT_OMNI_WORKERS='4')
                proc = subprocess.Popen([sys.executable, '-u', 'frozen_graph_experts.py', '--provider', 'omni'],
                    cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
                save(LOG/'status.json', dict(state='running', workers=4, pid=os.getpid(), worker_pid=proc.pid, attempt=attempt))
                update_log(f'Omni4workers续跑第{attempt}轮PID{proc.pid}，日志{log.relative_to(ROOT)}；成功缓存保留。')
                while proc.poll() is None:
                    report()
                    time.sleep(60)
            report()
        result = report()
        save(LOG/'status.json', dict(state='complete' if result['complete'] else 'needs_attention',
            pid=os.getpid(), valid={p:r['valid'] for p,r in result['providers'].items()}, workers=4))
        update_log('4路并发续跑结束，逐条审计数量'+str({p:r['valid'] for p,r in result['providers'].items()})+'；未通过项保留失败原因，不宣称完成。')


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        save(LOG/'status.json', dict(state='failed', error=str(exc), pid=os.getpid()))
        update_log('4路并发恢复阻塞：'+str(exc)+'；logs/concurrency4/status.json，保留缓存，需排查。')
        raise
