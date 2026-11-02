from __future__ import annotations
import csv,json,re,subprocess
from pathlib import Path
from .client import OpenAICompatibleClient
LABELS=['happy','sad','neutral','angry','worried','surprise']
EVIDENCE_PROMPT='''你是视频事实证据提取器。只根据视频画面和字幕提取当前片段中可核对的 Process、Person、Context 线索，至少提取10条、不重复。Process是当前实际发生的动作、语言和互动；Person是可观察的面部、视线、姿态和肢体；Context是可确认的场景、对象和互动条件。不要输出情绪、心理原因、动机或视频外事实。每条节点包含id、type、content、time_index；Context最多2条。只输出JSON：{"nodes":[{"id":"P1","type":"process","content":"...","time_index":0}]}。'''
RELATION_PROMPT='''你是PPCT层内关系判断器。输入是同一层节点和候选节点对。结合视频判断哪些节点联合使用能提供更完整的当前情绪证据。每条边先写reason，再给source、target、relation。只允许relation为process_joint、person_joint或context_joint；不能创建节点和跨层边。只返回JSON：{"edges":[{"reason":"...","source":"P1","target":"P2","relation":"process_joint"}]}。'''
ORG_PROMPT='''你是事实线索组织器。以Process为锚点，按时间写一段连贯中文，说明Person如何表现、Context如何限定行为，并保留时序和联合关系。只写视频和字幕能核对的事实，不输出情绪类别、心理原因或动机。'''
REASON_PROMPT='''你是视频情感推理模型。视频和字幕是主要依据，PPCT线索组织文本和图谱只用于定位证据及其关系。结合当前画面、字幕和组织文本推理目标说话人物当前情绪。倾向选择得到最多独立当前证据及其关系支持的标签；证据不足时选择neutral。先输出Reason，最后严格输出<answer>标签</answer>。标签只能是happy、sad、neutral、angry、worried、surprise。不要输出JSON、confidence或防御性说明。'''
def frames(video:Path,out:Path,count=8):
 out.mkdir(parents=True,exist_ok=True); pattern=out/'frame_%02d.jpg'; subprocess.run(['ffmpeg','-y','-i',str(video),'-vf','fps=1,scale=640:-1','-frames:v',str(count),str(pattern)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False); return [str(x) for x in sorted(out.glob('frame_*.jpg'))]
def parse_json(text):
 text=text.strip().removeprefix('```json').removesuffix('```').strip()
 try:return json.loads(text)
 except json.JSONDecodeError:
  m=re.search(r'\{.*\}',text,re.S)
  if not m:raise
  return json.loads(m.group(0))
def load_emer(video_root:Path,labels:Path,subtitles:Path,limit:int):
 lab={r['name']:r['discrete'] for r in csv.DictReader(labels.open(encoding='utf-8-sig'))}; sub={r['name']:r['chinese'] for r in csv.DictReader(subtitles.open(encoding='utf-8-sig'))}; rows=[]
 for name,label in lab.items():
  video=video_root/f'{name}.mp4'
  if video.exists(): rows.append({'sample_id':name,'video':str(video),'subtitle':sub.get(name,''),'label':label})
  if len(rows)>=limit:break
 return rows
def pairs(nodes):return [{'source':nodes[i]['id'],'target':nodes[j]['id']} for i in range(len(nodes)) for j in range(i+1,len(nodes))]
def run_sample(row,client:OpenAICompatibleClient,out:Path,video_mode=False):
 target=out/row['sample_id']; target.mkdir(parents=True,exist_ok=True); fs=frames(Path(row['video']),target/'frames'); base=f"字幕：{row['subtitle']}\\n样本：{row['sample_id']}"; result={'sample_id':row['sample_id'],'gold_label':row['label'],'video':row['video'],'frames':fs}
 def call(prompt,payload):
  messages=[{'role':'system','content':prompt},{'role':'user','content':payload}]
  try:
   return client.generate(messages,images=fs,video=row['video'],allow_video=video_mode)
  except Exception:
   if not video_mode: raise
   # OpenAI-compatible Gemini proxies may reject video_url; fall back to frames.
   return client.generate(messages,images=fs,video=None,allow_video=False)
 try:
  e=call(EVIDENCE_PROMPT,base); (target/'evidence_raw.txt').write_text(e.text,encoding='utf-8'); evidence=parse_json(e.text); nodes=evidence.get('nodes',[]); result['node_count']=len(nodes); (target/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8'); graph={'nodes':nodes,'edges':[]}
  for typ in ('process','person','context'):
   ns=[n for n in nodes if n.get('type')==typ]
   if len(ns)>1:
    rel=call(RELATION_PROMPT,json.dumps({'layer':typ,'nodes':ns,'candidate_pairs':pairs(ns),'video_context':base},ensure_ascii=False)); (target/f'{typ}_relation_raw.txt').write_text(rel.text,encoding='utf-8')
    try:graph['edges'].extend(parse_json(rel.text).get('edges',[]))
    except Exception:pass
  (target/'graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf-8'); org=call(ORG_PROMPT,json.dumps({'video_subtitle':base,'graph':graph},ensure_ascii=False)); (target/'organization_raw.txt').write_text(org.text,encoding='utf-8'); (target/'organization.txt').write_text(org.text,encoding='utf-8'); reason=call(REASON_PROMPT,json.dumps({'subtitle':row['subtitle'],'organization':org.text,'graph':graph,'labels':LABELS},ensure_ascii=False)); (target/'reasoning_raw.txt').write_text(reason.text,encoding='utf-8'); m=re.search(r'<answer>\s*([^<]+?)\s*</answer>',reason.text,re.I); result.update({'prediction':m.group(1).strip().lower() if m else None,'reason':reason.text,'error':None})
 except Exception as exc: result.update({'prediction':None,'error':f'{type(exc).__name__}: {exc}'})
 (target/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); return result
