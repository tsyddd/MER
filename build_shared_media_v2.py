"""Create versioned v2 pipeline from v1 without modifying its results or prompts."""
from pathlib import Path

source = Path('frozen_graph_experts.py').read_text()
source = source.replace('import argparse\n', 'import argparse\nfrom collections import Counter\n')
source = source.replace('import frozen_graph_expert_prompts as prompts', 'import shared_media_expert_prompts_v2 as prompts')
source = source.replace("VERSION = 'gemini_graph_three_experts_v1'", "VERSION = 'gemini_graph_shared_media_v2'")
source = source.replace("FROZEN = ROOT / 'data' / VERSION", "FROZEN = ROOT / 'data' / 'gemini_graph_three_experts_v1'")


def replace_function(name, new):
    global source
    start = source.index('def '+name+'(')
    end = source.find('\ndef ', start+4)
    if end < 0:
        end = source.index("\nif __name__", start+4)
    source = source[:start]+new.strip()+'\n\n'+source[end:]


replace_function('validate', r'''
def validate(value, name, classes, graph):
    assert isinstance(value,dict), 'Expected JSON object'
    if name=='organization':
        assert set(value)=={'text'} and isinstance(value['text'],str) and value['text'].strip()
        refs=set(re.findall(PATTERN,value['text']))
        assert refs and refs <= {n['id'] for n in graph['nodes']}, 'Organization must cite actual nodes'
        assert '<answer>' not in value['text']
        return
    assert isinstance(value.get('reason'),str) and value['reason'].strip(), 'Nonempty reason required'
    assert value.get('answer') in classes, 'Answer outside label space'
    assert '<answer>' not in value['reason'] and '</answer>' not in value['reason']
    if name=='summary':
        assert set(value)=={'reason','answer','evidence_refs'}
        refs=value['evidence_refs']
        assert isinstance(refs,list) and refs and all(isinstance(r,str) for r in refs)
        assert len(refs)==len(set(refs))
        assert set(refs)==set(re.findall(r'\[((?:graph|audio_subtitle|image):E\d+)\]',value['reason'])), 'Summary evidence references differ'
        return
    assert set(value)=={'expert','reason','answer','evidence','counterevidence'}
    assert value['expert']==name.removeprefix('expert_')
    assert isinstance(value['counterevidence'],str) and value['counterevidence'].strip()
    evidence=value['evidence']
    assert isinstance(evidence,list) and 1<=len(evidence)<=4
    ids=[]
    for e in evidence:
        assert isinstance(e,dict) and set(e)=={'id','source','anchor','observation','interpretation','polarity'}
        assert all(isinstance(v,str) and v.strip() for v in e.values())
        assert re.fullmatch(r'E[1-9]\d*',e['id'])
        assert e['source'] in {'visual','audio','subtitle','graph'}
        assert e['polarity'] in {'support','counter','uncertain'}
        if e['source']=='graph':
            assert name=='expert_graph', 'Other experts have no graph'
            refs=set(re.findall(PATTERN,e['anchor']))
            assert refs and refs <= {n['id'] for n in graph['nodes']}, 'Unknown graph node'
        if e['source']=='visual':assert re.search(r'frame_0[0-7]\b',e['anchor']), 'Visual evidence needs actual frame index'
        ids.append(e['id'])
    assert len(set(ids))==len(ids)
    cited=set(re.findall(r'\[(E\d+)\]',value['reason']))
    assert cited and cited <= set(ids), 'Reason must cite real evidence'
    if name=='expert_graph':assert any(e['source']=='graph' for e in evidence), 'Graph role must address graph'


def check_output(value,name,payload,audio):
    if name.startswith('expert_'):
        assert audio or not any(e['source']=='audio' for e in value['evidence']), 'No actual audio supplied'
        assert payload.get('subtitle') or not any(e['source']=='subtitle' for e in value['evidence']), 'No subtitle supplied'
    if name=='summary':
        available={role+':'+e['id'] for role,expert in payload['experts'].items() for e in expert['evidence']}
        assert set(value['evidence_refs']) <= available, 'Summary cites absent expert evidence'
''')
source = source.replace('value=read(output);validate(value,name,classes,graph);return value', 'value=read(output);validate(value,name,classes,graph);check_output(value,name,payload,audio);return value')
source = source.replace('validate(value,name,classes,graph)\n            save(output,value)', 'validate(value,name,classes,graph)\n            check_output(value,name,payload,audio)\n            save(output,value)')

replace_function('requests_for', '''
def media_payload(row,info,audio):
    result=dict(sample_id=row['id'],target_speaker=row.get('speaker') or 'main person',
        allowed_labels=row['classes'],frame_times_seconds=info['seconds'],audio_provided=bool(audio))
    if row.get('subtitle','').strip():result['subtitle']=row['subtitle']
    return result


def requests_for(row, graph, organization, info, audio):
    shared=media_payload(row,info,audio)
    graph_payload=dict(shared,graph=graph,organization=organization,graph_source='Frozen Gemini graph; indirect audio facts are not direct listening')
    return {'graph':(graph_payload,info['frames'],audio),
            'audio_subtitle':(dict(shared),info['frames'],audio),
            'image':(dict(shared),info['frames'],audio)}
''')
source = source.replace('independent_experts=True,summary_text_only=True,graph_audio_derivatives=True', 'independent_experts=True,summary_text_only=False,graph_audio_derivatives=True,shared_raw_media=True,development_reflect=True')
source = source.replace('row[\'classes\'],graph,1200)', "row['classes'],graph,2400)")
source = source.replace("dict(target,allowed_labels=row['classes'],experts=experts),[],None,row['classes'],graph,1600)", "dict(media_payload(row,info,audio),experts=experts),info['frames'],audio,row['classes'],graph,2200)")
source = source.replace('topology=STAGES, experts_independent=True, summary_text_only=True,', 'topology=STAGES, experts_independent=True, summary_text_only=False, shared_raw_media=True, development_reflect=True,')
source = source.replace('frames=8, labels_not_sent=True, optimization=False', 'frames=8, labels_not_sent=True, optimization=False, one_manual_development_reflect=True')

replace_function('audit', '''
def audit(provider):
    items=[];correct={'MER2024':0,'MELD':0};valid_ds={'MER2024':0,'MELD':0};usage=Counter();calls=0;seconds=0.
    frozen=read(FROZEN/'manifest.json')
    for row in rows():
        folder=BASE/provider/row['id'];issues=[]
        try:
            result=read(folder/'result.json');assert result['status']=='success',result.get('error','unfinished')
            entry=frozen[row['id']];assert digest(entry['path'])==entry['sha256']==result['graph_sha256']
            graph=read(entry['path']);GraphOutput.model_validate(graph)
            info=prepare_frames(row);expected_audio=row['audio'] if provider!='gpt' else None
            assert result['version']==VERSION and result['frames']==8 and result['raw_audio_provided']==bool(expected_audio)
            assert result['prediction'] in row['classes'] and result['emotion_analysis'].strip()
            assert re.findall(r'<answer>(.*?)</answer>',result['output'],re.S)==[result['prediction']]
            assert result['output'].count('<answer>')==result['output'].count('</answer>')==1
            for name in STAGES:
                value=read(folder/(name+'.json'));validate(value,name,row['classes'],graph)
                request=read(folder/(name+'_request.json'));cache=read(folder/(name+'_cache.json'))
                stamp=request.pop('signature');assert signature(request)==stamp==cache['signature']
                assert request['system']==(prompts.ORGANIZATION if name=='organization' else prompts.SUMMARY if name=='summary' else prompts.EXPERTS[name.removeprefix('expert_')])
                for req in folder.glob(name+'_request*.json'):check_no_gold(read(req)['payload'])
                payload=request['payload'];frames=request['frames'];audio=request['audio']
                assert request['frame_hashes']==[digest(p) for p in frames]
                assert request['audio_hash']==(digest(audio) if audio else None)
                check_output(value,name,payload,audio)
                if name=='organization':
                    assert not frames and not audio and payload['graph']==graph
                else:
                    assert frames==info['frames'] and len(frames)==8 and audio==expected_audio, 'Shared raw media mismatch'
                    assert payload.get('subtitle')==row.get('subtitle') and payload['audio_provided']==bool(expected_audio)
                    if name=='expert_graph':
                        assert payload['graph']==graph and payload['organization']==read(folder/'organization.json')['text']
                    else:
                        assert 'graph' not in payload and 'organization' not in payload, 'Graph leaked to other role'
                    if name=='summary':
                        assert set(payload['experts'])=={'graph','audio_subtitle','image'}
                        assert all(payload['experts'][r]==read(folder/('expert_'+r+'.json')) for r in payload['experts'])
                    else:assert 'experts' not in payload, 'Experts must remain independent'
                seconds+=cache.get('seconds',0)
            assert result['prediction']==read(folder/'summary.json')['answer']
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
''')

replace_function('self_test', '''
def self_test():
    graph={'nodes':[{'id':'person_0','content':'test'}],'edges':[]}
    row={'id':'fixture','speaker':'target','classes':['joy','neutral'],'subtitle':'test'}
    info={'seconds':list(range(8)),'frames':['frame_%02d.jpg'%i for i in range(8)]}
    for audio in ['/audio.wav',None]:
        routes=requests_for(row,graph,'facts',info,audio)
        for role,(payload,frames,track) in routes.items():
            assert frames==info['frames'] and track==audio and payload['subtitle']=='test'
            assert ('graph' in payload)==(role=='graph') and ('organization' in payload)==(role=='graph')
            assert 'experts' not in payload
            check_no_gold(payload)
    expert={'expert':'image','reason':'Visible [E1]','answer':'joy','evidence':[{'id':'E1','source':'visual','anchor':'frame_02 @2s','observation':'mouth corners raised','interpretation':'may be smile','polarity':'support'}],'counterevidence':'speech may disambiguate'}
    validate(expert,'expert_image',row['classes'],graph)
    check_output(expert,'expert_image',{'subtitle':'test'},None)
    summary={'reason':'Verified [image:E1]','answer':'joy','evidence_refs':['image:E1']}
    validate(summary,'summary',row['classes'],graph)
    check_output(summary,'summary',{'experts':{'image':expert}},None)
    for bad in [dict(summary,evidence_refs=['image:E9']),dict(summary,answer='anger')]:
        try:
            validate(bad,'summary',row['classes'],graph);check_output(bad,'summary',{'experts':{'image':expert}},None)
        except AssertionError:pass
        else:raise AssertionError('Invalid summary accepted')
    bad=dict(expert,evidence=[dict(expert['evidence'][0],source='audio')])
    try:check_output(bad,'expert_image',{},None)
    except AssertionError:pass
    else:raise AssertionError('Unprovided audio accepted')
    try:check_no_gold({'gold':'joy'})
    except AssertionError:pass
    else:raise AssertionError('Gold accepted')
    assert signature({'system':'old'})!=signature({'system':'new'})
    print('Shared-media routing, graph access, evidence references, audio capability, label space, no-gold and cache invalidation checks passed')
''')
source = source.replace('Each provider: frozen Gemini graph -> own organization -> graph / audio+subtitle /8-image experts -> text-only summary. Same fixed80 development samples, no prompt optimization.', 'V2: frozen Gemini graph -> own organization -> three independent role-specialized experts with shared8 images/audio/subtitles -> raw-media summary without graph. Four rubrics per role, one manual reflect on8 prior outputs (6 unique clips); these80 are reused development data, not held-out results.')
source = source.replace('Summary never receives raw media.', 'Summary receives raw media but no graph/organization; only graph expert gets graph/organization.')
source = source.replace('Graph integrity, source identity, 8-frame hashes, stage outputs, source isolation, answer wrapping, label space, request payload leakage and summary dependencies audited per unique sample ID.', 'Graph integrity,8-frame hashes, shared media per role, exclusive graph access, evidence reference validity, answer wrapping, label space, no-gold payload and summary dependencies audited per unique sample ID.')
source = source.replace("'manifest.json.'", "'manifest.json.'")
source = source.replace("'Prior baseline/PPCT comparison: metrics/validation_comparison.md. Frozen graph hashes: data/'+VERSION+'/manifest.json.'", "'Prior baseline/PPCT comparison: metrics/validation_comparison.md. Frozen graph hashes: data/gemini_graph_three_experts_v1/manifest.json.'")
source = source.replace('def controller():', "def controller(providers=None):\n    providers=providers or ['gpt','gemini','omni']")
source = source.replace("for provider in ['gpt','gemini','omni']:launch(provider,True,1)", 'for provider in providers:launch(provider,True,1)')
source = source.replace("complete=inspected['complete']", "providers=providers,complete=all(inspected['providers'][p]['complete'] for p in providers)")
source = source.replace("state='complete' if inspected['complete'] else 'needs_attention'", "state='complete' if all(inspected['providers'][p]['complete'] for p in providers) else 'needs_attention'")
source = source.replace("parser.add_argument('--controller',action='store_true');", "parser.add_argument('--controller',action='store_true');parser.add_argument('--providers',nargs='+',choices=['gpt','gemini','omni']);")
source = source.replace('elif args.controller:controller()', 'elif args.controller:controller(args.providers)')
Path('shared_media_experts_v2.py').write_text(source)
if Path('apply_soft_citations_v2.py').exists():
    import apply_soft_citations_v2
    apply_soft_citations_v2.apply()
print('Built shared_media_experts_v2.py; v1 unchanged')
