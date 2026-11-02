import os,json,time,hashlib,fcntl
from pathlib import Path
from huggingface_hub import HfApi,snapshot_download
root=Path(__file__).resolve().parents[1];target=root/'models/Qwen3-Omni-30B-A3B-Thinking';target.mkdir(exist_ok=True)
lock=open(root/'logs/download_omni.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
status=root/'logs/download_omni_status.json'
def save(**kw):status.write_text(json.dumps(dict(updated=time.time(),**kw),indent=2))
try:
 info=HfApi().model_info('Qwen/Qwen3-Omni-30B-A3B-Thinking',files_metadata=True)
 files=[dict(name=s.rfilename,size=s.size,sha256=getattr(s.lfs,'sha256',None) if s.lfs else None) for s in info.siblings]
 (root/'models/official_download_manifest.json').write_text(json.dumps({'repo':info.id,'revision':info.sha,'files':files},indent=2))
 save(state='downloading',revision=info.sha,expected_bytes=sum(f['size'] or 0 for f in files));print('REVISION',info.sha,'EXPECTED_BYTES',sum(f['size'] or 0 for f in files),flush=True)
 snapshot_download(repo_id=info.id,revision=info.sha,local_dir=target,max_workers=4)
 checks=[]
 for item in files:
  p=target/item['name']
  if not p.is_file():raise RuntimeError('Missing official file '+item['name'])
  if item['size'] is not None and p.stat().st_size!=item['size']:raise RuntimeError('Size mismatch '+item['name'])
  if p.suffix=='.safetensors':
   h=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
   digest=h.hexdigest()
   if item['sha256'] and digest!=item['sha256']:raise RuntimeError('SHA mismatch '+item['name'])
   checks.append({'file':item['name'],'bytes':p.stat().st_size,'sha256':digest})
 (target/'download_verified.json').write_text(json.dumps({'revision':info.sha,'shards':checks},indent=2));save(state='verified',revision=info.sha,shard_count=len(checks));print('VERIFIED',len(checks),flush=True)
except Exception as exc:save(state='error',error=str(exc));raise
