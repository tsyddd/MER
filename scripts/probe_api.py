import json,time,requests
from pathlib import Path
root=Path(__file__).resolve().parents[1];cfg=json.loads((root/'configs/private_api.json').read_text());key=cfg['api_key'];base=cfg['base_url'].rstrip('/');session=requests.Session();session.trust_env=False
headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'};report={'base_url':base,'checked':time.time(),'models':{}}
def safe(text):return str(text).replace(key,'[REDACTED]')[:1000]
try:
 r=session.get(base+'/v1/models',headers=headers,timeout=45)
 report['model_list_http']=r.status_code
 ids=[x['id'] for x in r.json().get('data',[]) if isinstance(x,dict) and 'id' in x] if r.ok else []
 wanted=[m for m in ids if ('gpt' in m.lower() and '6' in m.lower() and 'sol' in m.lower()) or ('gemini' in m.lower() and ('3.8' in m.lower() or 'flash' in m.lower()))]
 report['matching_model_ids']=wanted;print('MATCHING_MODELS',json.dumps(wanted),flush=True)
 for name,requested in [('gpt','gpt-6-sol'),('gemini','gemini-3.8-flash')]:
  matches=[m for m in ids if m.lower()==requested]
  if not matches:matches=[m for m in wanted if (name=='gpt' and 'gpt-6-sol' in m.lower()) or (name=='gemini' and '3.8' in m.lower() and 'flash' in m.lower())]
  model=matches[0] if matches else requested
  record={'model':model,'attempts':[]}
  for protocol in ['chat_completions','responses'] if name=='gpt' else ['chat_completions']:
   endpoint=base+('/v1/responses' if protocol=='responses' else '/v1/chat/completions')
   payload={'model':model,'input':'Reply only PPCT_OK.','max_output_tokens':512,'store':False} if protocol=='responses' else {'model':model,'messages':[{'role':'user','content':'Reply only PPCT_OK.'}],'max_tokens':512}
   try:
    started=time.time();r=session.post(endpoint,headers=headers,json=payload,timeout=150);entry={'protocol':protocol,'http_status':r.status_code,'seconds':time.time()-started}
    if r.ok:
     raw=r.json();text=''.join(c.get('text','') for item in raw.get('output',[]) if item.get('type')=='message' for c in item.get('content',[]) if c.get('type')=='output_text') if protocol=='responses' else raw.get('choices',[{}])[0].get('message',{}).get('content','')
     entry['text']=safe(text);entry['response_model']=raw.get('model');entry['usage']=raw.get('usage');entry['success']=bool(text)
     if text:record.update(available=True,protocol=protocol)
    else:entry['error']=safe(r.text)
    record['attempts'].append(entry)
    if record.get('available'):break
   except Exception as exc:record['attempts'].append({'protocol':protocol,'error':safe(exc),'success':False})
  report['models'][name]=record;print(name,json.dumps(record),flush=True)
except Exception as exc:report['error']=safe(exc);print('PROBE_ERROR',safe(exc),flush=True)
(root/'configs/api_probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
