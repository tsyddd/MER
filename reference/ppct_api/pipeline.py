from __future__ import annotations
import json,re
from pathlib import Path
from pydantic import BaseModel
from .client import OpenAICompatibleClient
from .graph import build_graph,candidate_pairs
from .prompts import EVIDENCE_PROMPT,TEMPORAL_PROMPT,JOINT_PROMPT,ORGANIZATION_PROMPT,EXPERT_PROMPTS,SUMMARY_PROMPT,DIRECT_PROMPT,REASONING_PROMPT
from .schemas import EvidenceOutput,RelationOutput,OrganizationOutput,ReasoningOutput,GraphOutput,ExpertOutput,SummaryOutput,RawEvidenceOutput,TemporalJudgmentOutput,JointJudgmentOutput,EvidenceNode,TemporalEdge,JointEdge
from .video import extract_frames
class SamplePipelineError(RuntimeError): pass
def _json(text:str):
    value=text.strip()
    if value.startswith('```'):
        value=value.split('\n',1)[1].rsplit('```',1)[0].strip()
    return json.loads(value)
def _save_json(path:Path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def _call(client,prompt,payload,frames,video,video_mode):
    return client.generate([{'role':'system','content':prompt},{'role':'user','content':payload}],images=frames,video=video if video_mode else None,allow_video=video_mode)
def _stage(target:Path,name:str,client,prompt,payload,frames,video,video_mode,schema,validator=None):
    _save_json(target/f'{name}_request.json',{'system':prompt,'user':payload,'video_mode':video_mode,'model':client.model,'images':frames})
    last=None
    for attempt in range(1,4):
        try:
            response=_call(client,prompt,payload,frames,video,video_mode)
            _save_json(target/f'{name}_response_attempt{attempt}.json',response.raw)
            (target/f'{name}_raw_attempt{attempt}.txt').write_text(response.text+'\n',encoding='utf-8')
            (target/f'{name}_raw.txt').write_text(response.text+'\n',encoding='utf-8')
            parsed=schema.model_validate(_json(response.text))
            if validator is not None: validator(parsed)
            _save_json(target/f'{name}.json',parsed.model_dump(mode='json'))
            return parsed
        except Exception as exc:
            last=exc
            _save_json(target/f'{name}_error_attempt{attempt}.json',{'stage':name,'attempt':attempt,'error_type':type(exc).__name__,'error':str(exc)})
    raise ValueError(f'{name} failed after 3 attempts: {last}') from last

def _flatten_raw_evidence(raw:RawEvidenceOutput):
    nodes=[]; temporal=[]
    for layer in ('process','person','context'):
        block=getattr(raw,layer)
        nodes.extend(EvidenceNode(id=n.id,type=n.type,content=n.content,time_index=n.time_index,evidence_sources=n.evidence_sources,dimension=n.dimension,evidence_status=n.evidence_status) for n in block.nodes)
    return EvidenceOutput(nodes=nodes,temporal_relations=temporal)

def _joint_by_layer(judgment:JointJudgmentOutput):
    out={k:RelationOutput(edges=[]) for k in ('process','person','context')}
    for e in judgment.edges:
        layer=e.relation.split('_',1)[0]
        out[layer].edges.append(JointEdge(reason=e.reason,source=e.source,target=e.target,relation=e.relation))
    return out

def _valid_temporal_edges(temporal, evidence, target):
    """Keep only same-layer, non-self temporal edges; preserve rejected edges."""
    by_id={n.id:n for n in evidence.nodes}; valid=[]; rejected=[]
    for e in temporal.edges:
        a,b=by_id.get(e.source),by_id.get(e.target)
        prefix=e.relation.split('_',1)[0] if '_' in e.relation else ''
        if not a or not b or a.type!=b.type or a.type!=prefix or a.id==b.id:
            rejected.append(e.model_dump(mode='json')); continue
        valid.append(e)
    _save_json(target/'temporal_rejected_edges.json',{'edges':rejected})
    return valid

def run_sample(row,client:OpenAICompatibleClient,out:Path,video_mode:bool,skill_text:str|None=None):
    target=out/row['sample_id']; target.mkdir(parents=True,exist_ok=True)
    metadata={'sample_id':row['sample_id'],'video':row['video'],'subtitle':row['subtitle'],'gold_label':row.get('label',row.get('gold')),'video_mode':video_mode}
    _save_json(target/'input.json',metadata)
    try:
        frames=extract_frames(Path(row['video']),target/'frames'); _save_json(target/'frames.json',{'frames':frames})
        context=f"样本：{row['sample_id']}\n字幕：{row['subtitle']}"
        raw_evidence=_stage(target,'evidence_raw',client,EVIDENCE_PROMPT,context,frames,row['video'],video_mode,RawEvidenceOutput)
        evidence=_flatten_raw_evidence(raw_evidence); _save_json(target/'evidence.json',evidence.model_dump(mode='json'))
        temporal_payload=json.dumps({'subtitle':row['subtitle'],'nodes_by_layer':{layer:[n.model_dump(mode='json') for n in evidence.nodes if n.type==layer] for layer in ('process','person','context')}},ensure_ascii=False)
        temporal=_stage(target,'temporal',client,TEMPORAL_PROMPT,temporal_payload,frames,row['video'],video_mode,TemporalJudgmentOutput)
        _save_json(target/'temporal_relations.json',temporal.model_dump(mode='json'))
        temporal_edges=_valid_temporal_edges(temporal,evidence,target)
        evidence=EvidenceOutput(nodes=evidence.nodes,temporal_relations=[TemporalEdge(source=e.source,target=e.target,relation=e.temporal_relation,reason=e.reason,entity_anchor=e.entity_anchor) for e in temporal_edges]); _save_json(target/'evidence.json',evidence.model_dump(mode='json'))
        nodes_by={layer:[n for n in evidence.nodes if n.type==layer] for layer in ('process','person','context')}
        pairs={layer:candidate_pairs(nodes) for layer,nodes in nodes_by.items()}
        joint_payload=json.dumps({'subtitle':row['subtitle'],'nodes':[n.model_dump(mode='json') for n in evidence.nodes],'candidate_pairs':pairs},ensure_ascii=False)
        joint=_stage(target,'joint',client,JOINT_PROMPT,joint_payload,frames,row['video'],video_mode,JointJudgmentOutput)
        _save_json(target/'joint_relations.json',joint.model_dump(mode='json')); relations=_joint_by_layer(joint)
        graph=build_graph(evidence,relations); _save_json(target/'graph.json',graph.model_dump(mode='json'))
        organization=_stage(target,'organization',client,ORGANIZATION_PROMPT,json.dumps({'subtitle':row['subtitle'],'graph':graph.model_dump(mode='json')},ensure_ascii=False),frames,row['video'],video_mode,OrganizationOutput)
        common={'subtitle':row['subtitle'],'organization':organization.text,'graph':graph.model_dump(mode='json'),'labels':['happy','sad','neutral','angry','worried','surprise']}
        expert_inputs={
            'video': {'subtitle':row['subtitle'],'organization':organization.text,'graph':graph.model_dump(mode='json'),'frames_note':'这些帧按视频时间顺序排列；只依据可见事实。'},
            'ppct': {'subtitle':row['subtitle'],'organization':organization.text,'graph':graph.model_dump(mode='json')},
            'subtitle': {'subtitle':row['subtitle'],'organization':organization.text,'graph':graph.model_dump(mode='json'),'target_speaker':row.get('target_speaker','')},
        }
        experts={}
        for name in ('video','ppct','subtitle'):
            prompt = EXPERT_PROMPTS[name] + (f'\n\n当前版本的附加skill规则：\n{skill_text}' if skill_text else '')
            experts[name]=_stage(target,f'{name}_expert',client,prompt,json.dumps(expert_inputs[name],ensure_ascii=False),frames,row['video'],video_mode,ExpertOutput)
        summary_payload={**common,'experts':{k:v.model_dump(mode='json') for k,v in experts.items()}}
        summary_prompt = SUMMARY_PROMPT + (f'\n\n当前版本的附加skill规则：\n{skill_text}' if skill_text else '')
        summary=_stage(target,'summary',client,summary_prompt,json.dumps(summary_payload,ensure_ascii=False),frames,row['video'],video_mode,SummaryOutput)
        _save_json(target/'reasoning.json',summary.model_dump(mode='json'))
        # Keep the prior result contract and make the requested extraction marker explicit.
        (target/'answer.txt').write_text(f'<answer>{summary.answer}</answer>\n',encoding='utf-8')
        result={**metadata,'frame_count':len(frames),'node_count':len(evidence.nodes),'edge_count':len(graph.edges),'expert_labels':{k:v.answer for k,v in experts.items()},'prediction':summary.answer,'reason':summary.reason,'error':None}
        _save_json(target/'result.json',result); _save_json(target/'status.json',{'status':'completed'}); return result
    except Exception as exc:
        error={'status':'error','sample_id':row['sample_id'],'stage':_guess_stage(target),'error_type':type(exc).__name__,'error':str(exc)}; _save_json(target/'status.json',error); _save_json(target/'result.json',{**metadata,'error':error}); raise SamplePipelineError(f"{row['sample_id']} failed at {error['stage']}: {exc}") from exc
def _guess_stage(target:Path):
    for name in ('evidence_raw','temporal','joint','organization','video_expert','ppct_expert','subtitle_expert','summary'):
        if not (target/f'{name}.json').exists(): return name
    return 'unknown'

def run_final_stage_cached(row,client:OpenAICompatibleClient,cache:Path,out:Path,video_mode:bool,skill_text:str|None=None):
    """Run only Video/PPCT/Subtitle experts and Summary from fixed PPCT artifacts."""
    source=cache/row['sample_id']; target=out/row['sample_id']; target.mkdir(parents=True,exist_ok=True)
    required=[source/'frames.json',source/'graph.json',source/'organization.json']
    if not all(p.exists() for p in required):
        raise SamplePipelineError(f"cached PPCT artifacts missing for {row['sample_id']}")
    frames=json.loads((source/'frames.json').read_text(encoding='utf-8'))['frames']
    graph=json.loads((source/'graph.json').read_text(encoding='utf-8'))
    organization=json.loads((source/'organization.json').read_text(encoding='utf-8'))['text']
    metadata={'sample_id':row['sample_id'],'video':row['video'],'subtitle':row.get('subtitle',''),'gold_label':row.get('label',row.get('gold')),'video_mode':video_mode}
    _save_json(target/'input.json',metadata); _save_json(target/'frames.json',{'frames':frames}); _save_json(target/'graph.json',graph); _save_json(target/'organization.json',{'text':organization})
    expert_inputs={'video':{'subtitle':row.get('subtitle',''),'organization':organization,'graph':graph,'frames_note':'这些帧按视频时间顺序排列；只依据可见事实。'},'ppct':{'subtitle':row.get('subtitle',''),'organization':organization,'graph':graph},'subtitle':{'subtitle':row.get('subtitle',''),'organization':organization,'graph':graph,'target_speaker':row.get('target_speaker','')}}
    experts={}
    for name in ('video','ppct','subtitle'):
        prompt=EXPERT_PROMPTS[name]+(f'\n\n当前版本的附加skill规则：\n{skill_text}' if skill_text else '')
        experts[name]=_stage(target,f'{name}_expert',client,prompt,json.dumps(expert_inputs[name],ensure_ascii=False),frames,row['video'],video_mode,ExpertOutput)
    payload={'subtitle':row.get('subtitle',''),'organization':organization,'graph':graph,'labels':['happy','sad','neutral','angry','worried','surprise'],'experts':{k:v.model_dump(mode='json') for k,v in experts.items()}}
    prompt=SUMMARY_PROMPT+(f'\n\n当前版本的附加skill规则：\n{skill_text}' if skill_text else '')
    summary=_stage(target,'summary',client,prompt,json.dumps(payload,ensure_ascii=False),frames,row['video'],video_mode,SummaryOutput)
    _save_json(target/'reasoning.json',summary.model_dump(mode='json')); (target/'answer.txt').write_text(f'<answer>{summary.answer}</answer>\n',encoding='utf-8')
    result={**metadata,'frame_count':len(frames),'node_count':len(graph.get('nodes',[])),'edge_count':len(graph.get('edges',[])),'expert_labels':{k:v.answer for k,v in experts.items()},'prediction':summary.answer,'reason':summary.reason,'error':None}
    _save_json(target/'result.json',result); _save_json(target/'status.json',{'status':'completed'}); return result

def run_direct(row,client:OpenAICompatibleClient,out:Path,video_mode:bool):
    """Direct baseline: same frames and subtitle, without PPCT artifacts."""
    target=out/row['sample_id']; target.mkdir(parents=True,exist_ok=True)
    metadata={'sample_id':row['sample_id'],'video':row['video'],'subtitle':row.get('subtitle',''),'gold_label':row.get('label',row.get('gold')),'video_mode':video_mode}
    _save_json(target/'input.json',metadata)
    try:
        frames=extract_frames(Path(row['video']),target/'frames'); _save_json(target/'frames.json',{'frames':frames})
        payload=json.dumps({'subtitle':row.get('subtitle',''),'labels':['happy','sad','neutral','angry','worried','surprise']},ensure_ascii=False)
        parsed=_stage(target,'direct',client,DIRECT_PROMPT,payload,frames,row['video'],video_mode,ReasoningOutput)
        _save_json(target/'reasoning.json',parsed.model_dump(mode='json')); (target/'answer.txt').write_text(f'<answer>{parsed.answer}</answer>\n',encoding='utf-8')
        result={**metadata,'frame_count':len(frames),'prediction':parsed.answer,'reason':parsed.reason,'error':None}; _save_json(target/'result.json',result); _save_json(target/'status.json',{'status':'completed'}); return result
    except Exception as exc:
        error={'status':'error','sample_id':row['sample_id'],'stage':_guess_stage(target),'error_type':type(exc).__name__,'error':str(exc)}; _save_json(target/'status.json',error); raise SamplePipelineError(f"{row['sample_id']} failed at {error['stage']}: {exc}") from exc

def run_lite_cached(row,client:OpenAICompatibleClient,cache:Path,out:Path,video_mode:bool):
    """PPCT-lite: fixed graph/organization plus video and subtitle, no experts."""
    source=cache/row['sample_id']; target=out/row['sample_id']; target.mkdir(parents=True,exist_ok=True)
    required=[source/'frames.json',source/'graph.json',source/'organization.json']
    if not all(p.exists() for p in required): raise SamplePipelineError(f"cached PPCT artifacts missing for {row['sample_id']}")
    frames=json.loads((source/'frames.json').read_text(encoding='utf-8'))['frames']; graph=json.loads((source/'graph.json').read_text(encoding='utf-8')); organization=json.loads((source/'organization.json').read_text(encoding='utf-8'))['text']
    metadata={'sample_id':row['sample_id'],'video':row['video'],'subtitle':row.get('subtitle',''),'gold_label':row.get('label',row.get('gold')),'video_mode':video_mode}; _save_json(target/'input.json',metadata); _save_json(target/'frames.json',{'frames':frames}); _save_json(target/'graph.json',graph); _save_json(target/'organization.json',{'text':organization})
    prompt=REASONING_PROMPT+"\n你还必须使用线索组织文本和图谱来定位、连接视频证据，但不能把其中无法核对的解释当作事实。"
    payload=json.dumps({'subtitle':row.get('subtitle',''),'organization':organization,'graph':graph,'labels':['happy','sad','neutral','angry','worried','surprise']},ensure_ascii=False)
    try:
        parsed=_stage(target,'lite',client,prompt,payload,frames,row['video'],video_mode,ReasoningOutput); _save_json(target/'reasoning.json',parsed.model_dump(mode='json')); (target/'answer.txt').write_text(f'<answer>{parsed.answer}</answer>\n',encoding='utf-8')
        result={**metadata,'frame_count':len(frames),'node_count':len(graph.get('nodes',[])),'edge_count':len(graph.get('edges',[])),'prediction':parsed.answer,'reason':parsed.reason,'error':None}; _save_json(target/'result.json',result); _save_json(target/'status.json',{'status':'completed'}); return result
    except Exception as exc:
        error={'status':'error','sample_id':row['sample_id'],'stage':_guess_stage(target),'error_type':type(exc).__name__,'error':str(exc)}; _save_json(target/'status.json',error); raise SamplePipelineError(f"{row['sample_id']} failed at {error['stage']}: {exc}") from exc

def run_ppct_upstream(row,client:OpenAICompatibleClient,out:Path,video_mode:bool):
    """Create only the reusable PPCT cache; no final emotion judgment."""
    target=out/row['sample_id']; target.mkdir(parents=True,exist_ok=True)
    _save_json(target/'input.json',{'sample_id':row['sample_id'],'video':row['video'],'subtitle':row.get('subtitle',''),'gold_label':row.get('label',row.get('gold')),'video_mode':video_mode})
    try:
        frames=extract_frames(Path(row['video']),target/'frames'); _save_json(target/'frames.json',{'frames':frames}); context=f"样本：{row['sample_id']}\n字幕：{row.get('subtitle','')}"
        raw=_stage(target,'evidence_raw',client,EVIDENCE_PROMPT,context,frames,row['video'],video_mode,RawEvidenceOutput); evidence=_flatten_raw_evidence(raw); _save_json(target/'evidence.json',evidence.model_dump(mode='json'))
        temporal_payload=json.dumps({'subtitle':row.get('subtitle',''),'nodes_by_layer':{layer:[n.model_dump(mode='json') for n in evidence.nodes if n.type==layer] for layer in ('process','person','context')}},ensure_ascii=False); temporal=_stage(target,'temporal',client,TEMPORAL_PROMPT,temporal_payload,frames,row['video'],video_mode,TemporalJudgmentOutput); _save_json(target/'temporal_relations.json',temporal.model_dump(mode='json')); temporal_edges=_valid_temporal_edges(temporal,evidence,target)
        evidence=EvidenceOutput(nodes=evidence.nodes,temporal_relations=[TemporalEdge(source=e.source,target=e.target,relation=e.temporal_relation,reason=e.reason,entity_anchor=e.entity_anchor) for e in temporal_edges]); _save_json(target/'evidence.json',evidence.model_dump(mode='json'))
        nodes_by={layer:[n for n in evidence.nodes if n.type==layer] for layer in ('process','person','context')}; pairs={layer:candidate_pairs(nodes) for layer,nodes in nodes_by.items()}; joint_payload=json.dumps({'subtitle':row.get('subtitle',''),'nodes':[n.model_dump(mode='json') for n in evidence.nodes],'candidate_pairs':pairs},ensure_ascii=False); joint=_stage(target,'joint',client,JOINT_PROMPT,joint_payload,frames,row['video'],video_mode,JointJudgmentOutput); _save_json(target/'joint_relations.json',joint.model_dump(mode='json')); graph=build_graph(evidence,_joint_by_layer(joint)); _save_json(target/'graph.json',graph.model_dump(mode='json'))
        organization=_stage(target,'organization',client,ORGANIZATION_PROMPT,json.dumps({'subtitle':row.get('subtitle',''),'graph':graph.model_dump(mode='json')},ensure_ascii=False),frames,row['video'],video_mode,OrganizationOutput); _save_json(target/'status.json',{'status':'completed'}); return {'sample_id':row['sample_id'],'node_count':len(evidence.nodes),'edge_count':len(graph.edges),'error':None}
    except Exception as exc:
        error={'status':'error','sample_id':row['sample_id'],'stage':_guess_stage(target),'error_type':type(exc).__name__,'error':str(exc)}; _save_json(target/'status.json',error); raise SamplePipelineError(f"{row['sample_id']} failed at {error['stage']}: {exc}") from exc
