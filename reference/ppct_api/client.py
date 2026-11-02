from __future__ import annotations
import base64,mimetypes,time
from pathlib import Path
from typing import Any
import requests
class GenerationResult:
    def __init__(self,text:str,raw:dict,model:str,provider:str,latency_ms:int): self.text,self.raw,self.model,self.provider,self.latency_ms=text,raw,model,provider,latency_ms
class OpenAICompatibleClient:
    def __init__(self,base_url:str,api_key:str,model:str,timeout:int=300,retries:int=0,protocol:str='chat_completions'): self.base_url=base_url.rstrip('/'); self.api_key=api_key; self.model=model; self.timeout=timeout; self.retries=retries; self.protocol=protocol
    @staticmethod
    def _data_url(path:str):
        p=Path(path); mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'; return f'data:{mime};base64,'+base64.b64encode(p.read_bytes()).decode()
    def _endpoint(self): return self.base_url if self.base_url.endswith('/chat/completions') else (self.base_url if self.base_url.endswith('/v1') else self.base_url+'/v1')+'/chat/completions'
    def generate(self,messages:list[dict[str,Any]],images:list[str]|None=None,video:str|None=None,allow_video:bool=False,temperature:float=0.0,audio:str|None=None,extra_body:dict|None=None):
        content=[]
        if images: content += [{'type':'image_url','image_url':{'url':self._data_url(x)}} for x in images]
        if video and allow_video: content.append({'type':'video_url','video_url':{'url':self._data_url(video)}})
        if audio:
            content.append({"type":"input_audio","input_audio":{"data":base64.b64encode(Path(audio).read_bytes()).decode(),"format":Path(audio).suffix.lstrip(".")}})
        payload_messages=messages
        if content:
            user=dict(messages[-1]); user['content']=content+[{'type':'text','text':str(messages[-1]['content'])}]; payload_messages=messages[:-1]+[user]
        endpoint=self._endpoint()
        payload={'model':self.model,'messages':payload_messages,'temperature':temperature}
        if self.protocol=='responses':
            if audio: raise ValueError('Responses audio input is not supported by this client')
            if video and allow_video: raise ValueError('Responses video input is not supported by this client')
            converted=[]
            for message in messages:
                converted.append({'role':message['role'],'content':[{'type':'input_text','text':str(message['content'])}]})
            if images:
                converted[-1]['content']=[{'type':'input_image','image_url':self._data_url(x)} for x in images]+converted[-1]['content']
            payload={'model':self.model,'input':converted,'store':False}
            endpoint=endpoint.removesuffix('/chat/completions')+'/responses'
        if extra_body: payload.update(extra_body)
        headers={'Authorization':f'Bearer {self.api_key}','Content-Type':'application/json'}; last=None
        for attempt in range(self.retries+1):
            started=time.time()
            try:
                resp=requests.post(endpoint,headers=headers,json=payload,timeout=self.timeout)
                if not resp.ok: raise RuntimeError(f'HTTP {resp.status_code}: {resp.text[:2000].replace(self.api_key,"[REDACTED]")}')
                raw=resp.json()
                if self.protocol=='responses':
                    if raw.get('status') in ('failed','incomplete'): raise ValueError(f'Responses status: {raw.get("status")}; details: {raw.get("incomplete_details") or raw.get("error")}')
                    msg=''.join(part.get('text','') for item in raw.get('output',[]) if item.get('type')=='message' for part in item.get('content',[]) if part.get('type')=='output_text')
                    if not msg: raise ValueError('Responses returned no output_text')
                else: msg=raw['choices'][0]['message']['content']
                if isinstance(msg,list): msg=''.join(str(x.get('text',x)) if isinstance(x,dict) else str(x) for x in msg)
                return GenerationResult(str(msg),raw,self.model,self.base_url,int((time.time()-started)*1000))
            except Exception as exc:
                last=exc
                if attempt<self.retries: time.sleep(2**attempt)
        raise RuntimeError(f'API request failed after {self.retries+1} attempts: {last}')
