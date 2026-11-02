"""Shared frozen Gemini graphs -> organization -> 3 isolated experts -> summary.

No optimization occurs on validation. Original six evaluation groups are untouched.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

from engine import ROOT, Client, digest, parse_json, prepare_frames, save, update_log
from reference.ppct_api.schemas import GraphOutput
import frozen_graph_expert_prompts as prompts

VERSION = 'gemini_graph_three_experts_v1'
BASE = ROOT / 'outputs' / VERSION
FROZEN = ROOT / 'data' / VERSION
STAGES = ['organization', 'expert_graph', 'expert_audio_subtitle', 'expert_image', 'summary']
PATTERN = r'(?:process|person|context)_\d+'


def rows():
    data = [json.loads(l) for l in (ROOT/'data/manifests/validation.jsonl').read_text().splitlines()]
    assert len(data) == len({r['id'] for r in data}) == 80
    return data


def read(path):
    return json.loads(Path(path).read_text())


def initialize():
    FROZEN.mkdir(parents=True, exist_ok=True)
    with (FROZEN/'init.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest = {}
        for row in rows():
            src = ROOT/'outputs/ppct/gemini'/row['id']/'graph.json'
            dst = FROZEN/row['id']/'graph.json'
            graph = GraphOutput.model_validate_json(src.read_text())
            assert graph.nodes
            if dst.exists():
                assert digest(src) == digest(dst), 'Frozen graph differs; refuse overwrite'
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            manifest[row['id']] = dict(path=str(dst), sha256=digest(dst), source=str(src),
                source_provider='gemini', source_model='gemini-3.8-flash-high',
                contains_audio_derived_nodes=any('audio' in n.evidence_sources for n in graph.nodes))
        dest = FROZEN/'manifest.json'
        if dest.exists():
            assert read(dest) == manifest, 'Frozen manifest changed'
        else:
            save(dest, manifest)
    BASE.mkdir(parents=True, exist_ok=True)
    save(BASE/'protocol.json', dict(version=VERSION, samples=80, datasets={'MER2024':40,'MELD':40},
        graph_source='frozen Gemini graphs from original PPCT80', graphs=manifest,
        topology=STAGES, experts_independent=True, summary_text_only=True,
        graph_audio_derivatives_shared_with_gpt=True, raw_audio_supported={'gpt':False,'gemini':True,'omni':True},
        frames=8, labels_not_sent=True, optimization=False))


def validate(value, name, classes, graph):
    assert isinstance(value, dict), 'Expected JSON object'
    ids = {n['id'] for n in graph['nodes']}
    if name == 'organization':
        assert set(value) == {'text'} and isinstance(value['text'],str) and value['text'].strip(), 'Nonempty organization text required'
        refs = set(re.findall(PATTERN,value['text']))
        assert refs and refs <= ids, 'Organization must cite actual nodes'
        assert '<answer>' not in value['text'], 'Organization cannot classify'
    else:
        required = {'reason','answer'} if name == 'summary' else {'expert','reason','answer','evidence_refs'}
        assert set(value) == required, 'Output schema mismatch'
        assert isinstance(value['reason'],str) and value['reason'].strip(), 'Nonempty reason required'
        assert value['answer'] in classes, 'Answer outside original label space'
        assert '<answer>' not in value['reason'] and '</answer>' not in value['reason'], 'Reason contains answer wrapper'
        if name != 'summary':
            role = name.removeprefix('expert_')
            assert value['expert'] == role, 'Expert identity mismatch'
            assert isinstance(value['evidence_refs'],list), 'Evidence references must be a list'
            if role == 'graph':
                refs = set(re.findall(PATTERN,value['reason']))
                assert refs and refs <= ids and set(value['evidence_refs']) == refs, 'Graph expert citations must match real nodes in reason'
            else:
                assert value['evidence_refs'] == [], 'Media experts did not receive graph references'


def check_no_gold(obj):
    if isinstance(obj, dict):
        assert not {'label','gold','ground_truth','prediction','teacher_predictions'} & obj.keys(), 'Gold/prior prediction leak'
        for v in obj.values(): check_no_gold(v)
    elif isinstance(obj,list):
        for v in obj: check_no_gold(v)


def signature(request):
    return hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def run_stage(folder, name, client, system, payload, frames, audio, classes, graph, max_tokens):
    check_no_gold(payload)
    request = dict(system=system,payload=payload,frames=frames,audio=str(audio) if audio else None,
        model=client.model,provider=client.provider,base_url=client.config['base_url'],max_tokens=max_tokens,
        frame_hashes=[digest(p) for p in frames],audio_hash=digest(audio) if audio else None,version=VERSION)
    stamp = signature(request)
    cache = folder/(name+'_cache.json')
    output = folder/(name+'.json')
    if cache.exists() and output.exists() and read(cache).get('signature') == stamp:
        value=read(output);validate(value,name,classes,graph);return value
    save(folder/(name+'_request.json'),dict(request,signature=stamp))
    # Requests also exist for transport failures without a completed response.
    previous = sorted(folder.glob(name+'_request_attempt*.json'))
    last = max([int(re.search(r'attempt(\d+)',p.name)[1]) for p in previous]+[0])
    feedback = None
    error = None
    for retry in range(3):
        attempt=last+retry+1
        actual = payload if feedback is None else dict(original_input=payload,format_repair=feedback)
        check_no_gold(actual)
        save(folder/f'{name}_request_attempt{attempt}.json',dict(request,payload=actual,signature=stamp))
        generated=False
        try:
            text,raw,seconds=client.generate(system,actual,frames,audio,max_tokens)
            generated=True
            save(folder/f'{name}_response_attempt{attempt}.json',raw)
            (folder/f'{name}_raw_attempt{attempt}.txt').write_text(text)
            value=parse_json(text)
            validate(value,name,classes,graph)
            save(output,value)
            save(cache,dict(signature=stamp,seconds=seconds,usage=raw.get('usage'),response_model=raw.get('model'),attempt=attempt))
            return value
        except Exception as exc:
            error=client.clean(exc)
            save(folder/f'{name}_error_attempt{attempt}.json',dict(error=error))
            if generated:
                feedback=dict(error=error,previous_response=text,instruction='Only repair JSON fields, output type and valid node references using the original input. Do not add facts. Return the required complete schema.')
            if any(code in error for code in ['HTTP 401','HTTP 403','HTTP 404']): break
            if retry<2:time.sleep(30*(retry+1) if not generated else 3)
    raise RuntimeError(name+': '+str(error))


def requests_for(row, graph, organization, info, audio):
    target=dict(sample_id=row['id'],target_speaker=row.get('speaker') or 'main person',allowed_labels=row['classes'])
    graph_payload=dict(target,graph=graph,organization=organization,graph_source='Gemini frozen graph; may include audio-derived facts')
    auditory=dict(target,audio_provided=bool(audio))
    if row.get('subtitle','').strip():auditory['subtitle']=row['subtitle']
    visual=dict(target,frame_times_seconds=info['seconds'])
    return {'graph':(graph_payload,[],None),'audio_subtitle':(auditory,[],audio),'image':(visual,info['frames'],None)}


def sample(row, provider):
    client=Client(provider);folder=BASE/provider/row['id'];folder.mkdir(parents=True,exist_ok=True)
    with (folder/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result_path=folder/'result.json'
        if result_path.exists() and read(result_path).get('status')=='success': return read(result_path)
        started=time.time();current='prepare'
        try:
            entry=read(FROZEN/'manifest.json')[row['id']]
            assert digest(entry['path'])==entry['sha256'], 'Frozen graph integrity changed'
            graph=read(entry['path']);info=prepare_frames(row)
            audio=row['audio'] if client.config.get('audio_supported') else None
            target=dict(sample_id=row['id'],target_speaker=row.get('speaker') or 'main person')
            save(folder/'input_protocol.json',dict(version=VERSION,graph=entry,frames=info,
                audio_provided=bool(audio),subtitle_provided=bool(row.get('subtitle')),target=target,
                independent_experts=True,summary_text_only=True,graph_audio_derivatives=True))
            current='organization'
            organization=run_stage(folder,current,client,prompts.ORGANIZATION,
                dict(target,graph=graph),[],None,row['classes'],graph,2048)['text']
            experts={}
            for role,(payload,frames,track) in requests_for(row,graph,organization,info,audio).items():
                current='expert_'+role
                experts[role]=run_stage(folder,current,client,prompts.EXPERTS[role],payload,frames,track,row['classes'],graph,1200)
            current='summary'
            summary=run_stage(folder,current,client,prompts.SUMMARY,
                dict(target,allowed_labels=row['classes'],experts=experts),[],None,row['classes'],graph,1600)
            result=dict(id=row['id'],dataset=row['dataset'],provider=provider,model=client.model,status='success',
                version=VERSION,graph_sha256=entry['sha256'],graph_source_provider='gemini',
                raw_audio_provided=bool(audio),graph_contains_audio_derived_nodes=entry['contains_audio_derived_nodes'],frames=8,
                prediction=summary['answer'],emotion_analysis=summary['reason'],
                output=summary['reason']+'\n<answer>'+summary['answer']+'</answer>',label=row['label'],
                elapsed_seconds=time.time()-started)
        except Exception as exc:
            result=dict(id=row['id'],dataset=row['dataset'],provider=provider,model=client.model,status='error',
                version=VERSION,stage=current,error=client.clean(exc),traceback=client.clean(traceback.format_exc()),elapsed_seconds=time.time()-started)
        save(result_path,result)
        return result


def audit(provider):
    items=[];correct={'MER2024':0,'MELD':0};valid_ds={'MER2024':0,'MELD':0};usage=Counter();calls=0;seconds=0.
    frozen=read(FROZEN/'manifest.json')
    for row in rows():
        folder=BASE/provider/row['id'];issues=[]
        try:
            result=read(folder/'result.json');assert result['status']=='success',result.get('error','not successful')
            entry=frozen[row['id']];assert digest(entry['path'])==entry['sha256']==result['graph_sha256'],'Frozen graph hash'
            graph=read(entry['path']);GraphOutput.model_validate(graph)
            protocol=read(folder/'input_protocol.json')
            assert len(protocol['frames']['frames'])==8 and all(Path(p).is_file() for p in protocol['frames']['frames']),'8 frames missing'
            assert re.findall(r'<answer>(.*?)</answer>',result['output'],re.S)==[result['prediction']],'Answer wrapping mismatch'
            assert result['output'].count('<answer>')==result['output'].count('</answer>')==1,'Answer wrapper count'
            assert result['prediction'] in row['classes'] and result['emotion_analysis'].strip(),'Final result invalid'
            assert result['raw_audio_provided']==(provider!='gpt'),'Audio capability protocol'
            for name in STAGES:
                value=read(folder/(name+'.json'));validate(value,name,row['classes'],graph)
                request=read(folder/(name+'_request.json'));cache=read(folder/(name+'_cache.json'))
                stamp=request.pop('signature');assert signature(request)==stamp==cache['signature'],'Stage cache signature'
                for req in folder.glob(name+'_request*.json'):check_no_gold(read(req)['payload'])
                frames=request['frames'];audio=request['audio'];payload=request['payload']
                assert request['frame_hashes']==[digest(p) for p in frames],'Frame hash changed'
                assert request['audio_hash']==(digest(audio) if audio else None),'Audio hash changed'
                if name=='expert_image':
                    assert len(frames)==8 and not audio and 'subtitle' not in payload and 'graph' not in payload and 'organization' not in payload,'Image expert isolation'
                elif name=='expert_audio_subtitle':
                    assert not frames and bool(audio)==(provider!='gpt') and 'graph' not in payload and 'organization' not in payload,'Audio/subtitle expert isolation'
                else:
                    assert not frames and not audio,'Text-only stage isolation'
                    if name=='summary':
                        assert set(payload['experts'])=={'graph','audio_subtitle','image'},'Three expert outputs missing'
                        assert all(payload['experts'][role]==read(folder/('expert_'+role+'.json')) for role in payload['experts']),'Summary expert inputs differ'
                        assert 'graph' not in payload and 'organization' not in payload and 'subtitle' not in payload,'Summary must consume experts only'
                seconds+=cache.get('seconds',0)
            assert result['prediction']==read(folder/'summary.json')['answer'],'Summary/result mismatch'
            valid_ds[row['dataset']]+=1;correct[row['dataset']]+=result['prediction']==row['label']
        except Exception as exc:issues.append(str(exc) if not isinstance(exc,FileNotFoundError) else 'not yet completed')
        for f in folder.glob('*_response_attempt*.json'):
            calls+=1
            for k,v in (read(f).get('usage') or {}).items():
                if k in ['prompt_tokens','completion_tokens','total_tokens'] and isinstance(v,(int,float)):usage[k]+=v
        items.append(dict(id=row['id'],valid=not issues,issues=issues))
    good=sum(x['valid'] for x in items)
    metrics={ds:dict(valid=valid_ds[ds],expected=40,correct=correct[ds],accuracy=correct[ds]/40 if valid_ds[ds]==40 else None) for ds in correct}
    metrics['ALL']=dict(valid=good,expected=80,correct=sum(correct.values()),accuracy=sum(correct.values())/80 if good==80 else None)
    return dict(provider=provider,complete=good==80,valid=good,incomplete_or_invalid=80-good,metrics=metrics,
        recorded_responses=calls,usage=dict(usage),successful_stage_seconds=seconds,items=items)


from collections import Counter


def report():
    results={p:audit(p) for p in ['gpt','gemini','omni']}
    document=dict(version=VERSION,complete=all(x['complete'] for x in results.values()),providers=results)
    save(ROOT/'metrics'/f'{VERSION}_audit.json',document)
    lines=['# Frozen Gemini graphs + three independent experts','',
        'Each provider: frozen Gemini graph -> own organization -> graph / audio+subtitle /8-image experts -> text-only summary. Same fixed80 development samples, no prompt optimization.',
        'GPT audio+subtitle branch receives subtitle only; graph branch indirectly receives Gemini audio-derived observations. Summary never receives raw media. Each expert is the same requested model as its summary, not cross-model voting.','',
        '| Model | MER2024 | MELD | All80 | Audited | Responses | Total tokens | Successful stage seconds |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for p,r in results.items():
        vals=[f'{100*r["metrics"][ds]["accuracy"]:.2f}% ({r["metrics"][ds]["correct"]}/{r["metrics"][ds]["expected"]})' if r['metrics'][ds]['accuracy'] is not None else 'pending' for ds in ['MER2024','MELD','ALL']]
        lines.append('| '+p+' | '+' | '.join(vals)+f' | {r["valid"]}/80 | {r["recorded_responses"]} | {r["usage"].get("total_tokens",0)} | {r["successful_stage_seconds"]:.1f} |')
    lines+=['','Prior baseline/PPCT comparison: metrics/validation_comparison.md. Frozen graph hashes: data/'+VERSION+'/manifest.json.',
        'Graph integrity, source identity, 8-frame hashes, stage outputs, source isolation, answer wrapping, label space, request payload leakage and summary dependencies audited per unique sample ID. This does not verify semantic truth of every observation.',
        'Recorded usage includes persisted responses for this experiment, excluding source-graph generation, external connection probes and failed network requests with no response. Successful stage time is a sum, not end-to-end wall time. Candidate/provider identity is as reported by the configured service.']
    (ROOT/'metrics'/f'{VERSION}_comparison.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({p:dict(valid=r['valid'],complete=r['complete'],metrics=r['metrics']) for p,r in results.items()},ensure_ascii=False),flush=True)
    return document


def worker(provider,smoke=False):
    BASE.mkdir(parents=True,exist_ok=True)
    with (BASE/(provider+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        selected=rows()
        if smoke:selected=[next(r for r in selected if r['dataset']==d) for d in ['MER2024','MELD']]
        def one(r):
            result=sample(r,provider)
            print(json.dumps(dict(provider=provider,id=r['id'],status=result['status'],stage=result.get('stage'),error=result.get('error')),ensure_ascii=False),flush=True)
            return result['status']=='success'
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get('PPCT_OMNI_WORKERS','4')) if provider=='omni' else 2) as pool:
            success=list(pool.map(one,selected))
        return 0 if all(success) else 1


def controller():
    BASE.mkdir(parents=True,exist_ok=True)
    with (BASE/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        initialize();jobs={};processes={};started=time.time()
        save(BASE/'controller.pid',os.getpid())
        def launch(provider,smoke,attempt):
            name='smoke' if smoke else 'full';log=ROOT/'logs'/f'{VERSION}_{provider}_{name}_{attempt}.log'
            args=[sys.executable,'-u',str(Path(__file__).resolve()),'--provider',provider]
            if smoke:args.append('--smoke')
            with log.open('a') as stream:
                proc=subprocess.Popen(args,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            processes[provider]=proc;jobs[provider]=dict(pid=proc.pid,smoke=smoke,attempt=attempt,state='running',log=str(log))
            update_log(f'{VERSION}启动{provider}/{name}第{attempt}轮，PID{proc.pid}，日志{log.relative_to(ROOT)}；复用固定图谱与已成功阶段。')
        for provider in ['gpt','gemini','omni']:launch(provider,True,1)
        last=0
        while processes and time.time()-started<24*3600:
            for provider,proc in list(processes.items()):
                code=proc.poll()
                if code is None:continue
                job=jobs[provider];del processes[provider];job.update(state='finished' if code==0 else 'failed',exit_code=code)
                if code==0 and job['smoke']:launch(provider,False,1)
                elif code!=0 and job['attempt']<2:launch(provider,job['smoke'],job['attempt']+1)
            if time.time()-last>60:
                inspected=report();save(BASE/'controller_status.json',dict(pid=os.getpid(),jobs=jobs,elapsed_seconds=time.time()-started,complete=inspected['complete']))
                last=time.time()
            time.sleep(15)
        inspected=report();save(BASE/'controller_status.json',dict(pid=os.getpid(),jobs=jobs,elapsed_seconds=time.time()-started,complete=inspected['complete'],state='complete' if inspected['complete'] else 'needs_attention'))
        update_log(f'{VERSION}调度结束，逐条审计完成数'+str({p:r['valid'] for p,r in inspected['providers'].items()})+'，全部完成='+str(inspected['complete'])+'；报告metrics/'+VERSION+'_comparison.md。服务保留。')


def self_test():
    graph={'nodes':[{'id':'person_0','type':'person','content':'嘴角上扬','time_index':0,'evidence_sources':['visual']}],'edges':[]}
    row={'id':'fixture','speaker':'target','classes':['joy','neutral'],'subtitle':'test'}
    routes=requests_for(row,graph,'事实〔person_0〕',{'seconds':list(range(8)),'frames':list(range(8))},'/audio.wav')
    assert routes['image'][1]==list(range(8)) and routes['image'][2] is None and 'subtitle' not in routes['image'][0]
    assert routes['graph'][1:]==([],None) and routes['audio_subtitle'][1]==[]
    assert requests_for(row,graph,'text',{'seconds':[],'frames':[]},None)['audio_subtitle'][0]['audio_provided'] is False
    validate({'expert':'graph','reason':'Person〔person_0〕描述嘴角上扬','answer':'joy','evidence_refs':['person_0']},'expert_graph',row['classes'],graph)
    for bad in [{'expert':'graph','reason':'〔person_999〕','answer':'joy','evidence_refs':['person_999']},{'expert':'graph','reason':'〔person_0〕','answer':'anger','evidence_refs':['person_0']}]:
        try:validate(bad,'expert_graph',row['classes'],graph)
        except AssertionError:pass
        else:raise AssertionError('Invalid citation/label accepted')
    try:check_no_gold({'experts':{'graph':{'gold':'joy'}}})
    except AssertionError:pass
    else:raise AssertionError('Gold leak accepted')
    assert signature({'payload':{'organization':'a'}})!=signature({'payload':{'organization':'b'}})
    print('Offline isolation/citation/label/leakage/signature checks passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--provider',choices=['gpt','gemini','omni']);parser.add_argument('--smoke',action='store_true');parser.add_argument('--init',action='store_true');parser.add_argument('--audit',action='store_true');parser.add_argument('--controller',action='store_true');parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test()
    elif args.init:initialize()
    elif args.audit:report()
    elif args.controller:controller()
    elif args.provider:sys.exit(worker(args.provider,args.smoke))
    else:parser.error('Choose --init/--controller/--audit/--provider/--self-test')
