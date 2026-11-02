"""Track only this project's dedicated SSH session so a reconnect can release it."""
import json
import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER = ROOT / 'logs/tunnel_session.json'


def identity(pid):
    proc = Path('/proc') / str(pid)
    return proc.joinpath('cmdline').read_bytes().replace(b'\0', b' ').decode(), proc.joinpath('stat').read_text().split()[21]


if '--cleanup' in sys.argv:
    if MARKER.exists():
        saved = json.loads(MARKER.read_text())
        try:
            command, stamp = identity(saved['sshd_pid'])
            if stamp == saved['start_ticks'] and command.strip() == 'sshd: liang@notty':
                os.kill(saved['sshd_pid'], signal.SIGTERM)
                print('Released tracked project SSH session', saved['sshd_pid'])
        except (FileNotFoundError, ProcessLookupError):
            pass
else:
    pid = os.getppid()
    while pid > 1:
        command, stamp = identity(pid)
        if command.strip() == 'sshd: liang@notty':
            MARKER.write_text(json.dumps(dict(sshd_pid=pid, start_ticks=stamp,
                                             session_pid=os.getpid(), port=18101, created=time.time())))
            break
        pid = int((Path('/proc') / str(pid) / 'stat').read_text().split()[3])
    else:
        raise RuntimeError('Cannot identify dedicated SSH session')
    time.sleep(48 * 3600)
