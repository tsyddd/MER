"""Download author's ModelScope files in ranges; verify against pinned HF SHA256."""
import concurrent.futures
import fcntl
import hashlib
import json
import os
import threading
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'models/Qwen3-Omni-30B-A3B-Thinking'
CHUNK = 16 * 1024 * 1024
local = threading.local()


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def transfer(task):
    item, offset, length, partial, marker = task
    if marker.exists():
        return 0
    if not hasattr(local, 'session'):
        local.session = requests.Session()
        local.session.trust_env = False
    url = 'https://modelscope.cn/models/Qwen/Qwen3-Omni-30B-A3B-Thinking/resolve/master/' + item['name']
    last = None
    for attempt in range(4):
        try:
            with local.session.get(url, headers={'Range': f'bytes={offset}-{offset+length-1}'},
                                   stream=True, timeout=(15, 90)) as r:
                expected = f'bytes {offset}-{offset+length-1}/{item["size"]}'
                if r.status_code != 206 or r.headers.get('Content-Range') != expected:
                    raise RuntimeError(f'Unexpected range response {r.status_code}: {r.headers.get("Content-Range")}')
                fd = os.open(partial, os.O_WRONLY)
                count = 0
                try:
                    for data in r.iter_content(512 * 1024):
                        if count + len(data) > length:
                            raise ValueError('Range response exceeds requested length')
                        written = os.pwrite(fd, data, offset + count)
                        if written != len(data):
                            raise IOError('Incomplete local write')
                        count += len(data)
                finally:
                    os.close(fd)
                if count != length:
                    raise ValueError('Incomplete range response')
            marker.touch()
            return count
        except Exception as exc:
            last = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise RuntimeError(item['name'] + f' range {offset} failed: {last}')


def main():
    lock = (ROOT / 'logs/download_modelscope.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    manifest = json.loads((ROOT / 'models/official_download_manifest.json').read_text())
    # Keep tokenizer/configs pinned to the HF revision, even when weights use the author's mirror.
    for item in manifest['files']:
        if item['name'].endswith('.safetensors'):
            continue
        dest = TARGET / item['name']
        if dest.exists() and dest.stat().st_size == item['size']:
            continue
        url = ('https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Thinking/resolve/'
               + manifest['revision'] + '/' + item['name'])
        response = requests.get(url, timeout=120,
                                proxies={'http': 'http://127.0.0.1:17897', 'https': 'http://127.0.0.1:17897'})
        response.raise_for_status()
        if len(response.content) != item['size']:
            raise ValueError('Pinned auxiliary file size mismatch: ' + item['name'])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)
    tasks = []
    pending = []
    for item in manifest['files']:
        if not item['name'].endswith('.safetensors'):
            continue
        dest = TARGET / item['name']
        if dest.exists() and dest.stat().st_size == item['size'] and sha256(dest) == item['sha256']:
            continue
        folder = TARGET / '.modelscope_ranges' / item['name']
        folder.mkdir(parents=True, exist_ok=True)
        partial = folder / 'data.partial'
        if not partial.exists():
            with partial.open('wb') as f:
                f.truncate(item['size'])
        pending.append((item, partial))
        for offset in range(0, item['size'], CHUNK):
            tasks.append((item, offset, min(CHUNK, item['size'] - offset), partial, folder / (str(offset) + '.done')))
    started = time.time()
    transferred = 0
    failures = []
    status = ROOT / 'logs/modelscope_download_status.json'
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(transfer, task) for task in tasks]
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                transferred += future.result()
            except Exception as exc:
                failures.append(str(exc))
                print(json.dumps(dict(range_error=str(exc))), flush=True)
            if index % 16 == 0 or index == len(tasks):
                record = dict(state='downloading', completed_ranges=sum(t[4].exists() for t in tasks), failed_ranges=len(failures), total_ranges=len(tasks),
                              transferred_this_run=transferred, seconds=time.time() - started,
                              bytes_per_second=transferred / max(1, time.time() - started), updated=time.time())
                status.write_text(json.dumps(record, indent=2))
                print(json.dumps(record), flush=True)
    if failures:
        raise RuntimeError(f'{len(failures)} ranges failed; completed markers retained for resume')
    checks = []
    for item, partial in pending:
        actual = sha256(partial)
        if actual != item['sha256']:
            raise ValueError('Pinned HF SHA256 differs from ModelScope bytes: ' + item['name'])
        partial.replace(TARGET / item['name'])
        checks.append(dict(file=item['name'], bytes=item['size'], sha256=actual))
    # Every original official file (including configs/tokenizer) must exist with the pinned size.
    for item in manifest['files']:
        dest = TARGET / item['name']
        if not dest.exists() or dest.stat().st_size != item['size']:
            raise RuntimeError('Missing official nonweight file: ' + item['name'])
    verification = dict(revision=manifest['revision'], weight_source='author ModelScope',
                        hash_reference='pinned official HuggingFace manifest', shards=checks)
    (TARGET / 'download_verified.json').write_text(json.dumps(verification, indent=2))
    result = dict(state='verified', updated=time.time(), revision=manifest['revision'])
    status.write_text(json.dumps(result, indent=2))
    (ROOT / 'logs/download_omni_status.json').write_text(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
