"""Wait for existing healthy transfer; bounded sequential recovery after it exits."""
import fcntl
import os
import subprocess
import time
from pathlib import Path
from engine import ROOT, update_log


def alive(pid):
    p = Path('/proc')/str(pid)/'stat'
    return p.exists() and p.read_text().split()[2] != 'Z'


lock=(ROOT/'logs/download_guard.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
original=int((ROOT/'logs/download_modelscope.pid').read_text())
(ROOT/'logs/download_worker.pid').write_text(str(original))
(ROOT/'logs/download_modelscope.pid').write_text(str(os.getpid()))
verified=ROOT/'models/Qwen3-Omni-30B-A3B-Thinking/download_verified.json'
while alive(original) and not verified.exists(): time.sleep(5)
for attempt in range(1,4):
    if verified.exists(): break
    time.sleep(30)
    with (ROOT/'logs/download_modelscope.log').open('a') as stream:
        worker=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-u',str(ROOT/'download_modelscope.py')],
            cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        (ROOT/'logs/download_worker.pid').write_text(str(worker.pid))
        update_log(f'原下载已退出未校验；顺序恢复第{attempt}次，8线程复用已完成分段，worker PID={worker.pid}。')
        code=worker.wait()
    if code==0 and verified.exists(): break
else:
    update_log('下载顺序恢复达到3次上限仍未验证，需后续排查。')
    raise SystemExit(1)
if verified.exists(): update_log('官方Thinking权重分片SHA及文件大小校验完成，下载已验证。')
