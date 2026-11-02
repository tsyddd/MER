import sys,time,os,json,re,fcntl
from pathlib import Path
sys.path.insert(0,str(Path('versions/v3').resolve()))
import pipeline as v
LOG=v.ROOT/'logs/v3_gpt_cooldown_recovery'
LOG.mkdir(parents=True,exist_ok=True)
def status(**values):v.save(LOG/'status.json',dict(pid=os.getpid(),**values))
with (v.BASE/'gpt.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 status(state='starting');started=time.time();failures=[]
 v.update_log('恢复v3 GPT未完成14条，限额感知顺序续跑，仅缺失阶段；已有66条/全部Gemini保留。恢复PID'+str(os.getpid())+'，状态logs/v3_gpt_cooldown_recovery/status.json。')
 for row in v.rows():
  path=v.BASE/'gpt'/row['id']/'result.json'
  if path.exists() and v.read(path).get('status')=='success':continue
  for attempt in range(3):
   if time.time()-started>24*3600:break
   status(state='running',sample_id=row['id'],attempt=attempt+1,valid=v.audit('gpt')['valid'])
   result=v.sample(row,'gpt');print(json.dumps({k:result.get(k) for k in ['id','status','stage','error']},ensure_ascii=False),flush=True)
   v.report()
   if result['status']=='success':break
   error=result.get('error','')
   if '429' not in error:failures.append(row['id']);break
   resets=re.findall(r'"(?:reset_seconds|resets_in_seconds)"\s*:\s*(\d+)',error)
   delay=max([int(x) for x in resets]+[600])+30
   status(state='provider_cooldown',sample_id=row['id'],wait_seconds=delay,valid=v.audit('gpt')['valid'])
   v.update_log('v3 GPT仍HTTP429，按服务冷却等待'+str(delay)+'秒，保留缓存。')
   time.sleep(delay)
  else:
   status(state='needs_attention',reason='Repeated provider cooldown',valid=v.audit('gpt')['valid']);break
 inspected=v.report();r=inspected['providers']['gpt']
 status(state='complete' if r['complete'] else 'needs_attention',valid=r['valid'],failures=failures,metrics=r['metrics'])
 v.update_log('v3 GPT恢复结束，有效'+str(r['valid'])+'/80，状态logs/v3_gpt_cooldown_recovery/status.json；报告metrics/gemini_graph_emotion_wheel_v3_comparison.md。')
