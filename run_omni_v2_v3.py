"""Deployment verification gate -> Omni v2 -> Omni v3; no API-provider calls."""
import os,json,time,sys,subprocess,fcntl
from pathlib import Path
from engine import ROOT,save,update_log
LOG=ROOT/'logs/omni_v2_v3'
LOG.mkdir(parents=True,exist_ok=True)
VERIFY=ROOT/'logs/omni_restart_20261101_235917_verification/status.json'
VERSIONS=[('v2','shared_media_experts_v2.py','gemini_graph_shared_media_v2'),('v3','versions/v3/pipeline.py','gemini_graph_emotion_wheel_v3')]
def read(p):return json.loads(p.read_text())
def status(**kw):save(LOG/'status.json',dict(pid=os.getpid(),**kw))
with (LOG/'schedule.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 save(LOG/'pid.json',dict(pid=os.getpid()))
 try:
  start=time.time()
  status(state='waiting_for_verified_omni',verification=str(VERIFY))
  update_log('用户授权Omni加载验证后依次运行v2、v3各80条。监督PID'+str(os.getpid())+'；logs/omni_v2_v3/status.json。4workers，独立版本/结果，GPT/Gemini不重跑。')
  while time.time()-start<2*3600:
   verified=read(VERIFY) if VERIFY.exists() else {}
   if verified.get('state')=='verified':break
   if verified.get('state')=='failed':raise RuntimeError('Deployment media verification failed: '+verified.get('error','unknown'))
   time.sleep(30)
  else:raise RuntimeError('Timed out waiting for real Omni media verification')
  results={}
  for version,script,experiment in VERSIONS:
   # Do not race an already running worker/controller for this version.
   base=ROOT/'outputs'/experiment
   for name in ['controller','omni']:
    with (base/(name+'.lock')).open('a') as stage_lock:
     fcntl.flock(stage_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   log=LOG/(version+'_controller.log')
   with log.open('a') as stream:
    child=subprocess.Popen([sys.executable,'-u',script,'--controller','--providers','omni'],cwd=ROOT,
     env=dict(os.environ,PPCT_OMNI_WORKERS='4'),stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   status(state='running',version=version,worker_controller_pid=child.pid,log=str(log),results=results)
   update_log('Omni '+version+'启动控制器'+str(child.pid)+'，先跨MER/MELD各1条检查再80条，日志'+str(log.relative_to(ROOT))+'，保留成功缓存。')
   while child.poll() is None:time.sleep(30)
   report=read(ROOT/'metrics'/(experiment+'_audit.json'))
   result=report['providers']['omni']
   results[version]=dict(valid=result['valid'],complete=result['complete'],metrics=result['metrics'],controller_exit=child.returncode)
   save(LOG/(version+'_result.json'),results[version])
   update_log('Omni '+version+'本轮结束，逐条有效'+str(result['valid'])+'/80；'+('已完成' if result['complete'] else '仍有失败/缺失，原响应保留')+'。')
  complete=all(r['complete'] for r in results.values())
  status(state='complete' if complete else 'needs_attention',results=results)
  update_log('Omni v2/v3顺序任务结束：'+str({k:r['valid'] for k,r in results.items()})+'；完整='+str(complete)+'。服务保留。')
 except Exception as exc:
  status(state='blocked',error=str(exc))
  update_log('Omni v2/v3调度阻塞：'+str(exc)+'；见logs/omni_v2_v3/status.json，不宣称完成。')
  raise
