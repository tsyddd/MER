"""Soft citation diagnostics; never infer new evidence, labels or reasons."""
import re

POLICY = 'soft_citations_20261101'


def warnings(value, name, graph, payload):
    result=[]
    reason=value.get('reason','')
    if name=='organization':return result
    if name=='summary':
        available={role+':'+e['id'] for role,expert in payload['experts'].items() for e in expert['evidence']}
        refs=set(value.get('evidence_refs',[]))
        if not refs:result.append('No explicit expert evidence IDs; retain natural-language evidence explanation')
        if refs-available:result.append('Unknown expert references: '+str(sorted(refs-available)))
        if refs != set(re.findall(r'\[((?:graph|audio_subtitle|image):E\d+)\]',reason)):
            result.append('Summary citation style/list differs from reason; not a generation failure')
    else:
        ids={e['id'] for e in value['evidence']}
        cited=set(re.findall(r'\[(E\d+)\]',reason))
        if not cited:result.append('No bracketed E-number in reason; structured evidence retained')
        if cited-ids:result.append('Reason contains unknown evidence IDs: '+str(sorted(cited-ids)))
        real={n['id'] for n in graph['nodes']}
        for e in value['evidence']:
            if e['source']=='graph':
                refs=set(re.findall(r'(?:process|person|context)_\d+',e['anchor']))
                if not refs or not refs <= real:result.append('Unresolved graph citation '+e['id']+': '+e['anchor'])
            if e['source']=='visual' and not re.search(r'frame_0[0-7]\b',e['anchor']):
                result.append('Noncanonical visual locator '+e['id']+': '+e['anchor'])
        if name=='expert_graph' and not any(e['source']=='graph' for e in value['evidence']):
            result.append('Graph specialist did not provide explicit graph-source citation')
    return result


def record(folder,name,value,graph,payload,save):
    save(folder/(name+'_citation_diagnostics.json'),dict(policy=POLICY,warnings=warnings(value,name,graph,payload),
         semantic_truth_verified=False,output_unchanged=True))


def recover(folder,name,stamp,payload,audio,classes,graph,validate,check_output,parse_json,read,save):
    candidates=sorted(folder.glob(name+'_raw_attempt*.txt'),key=lambda p:int(re.search(r'attempt(\d+)',p.name)[1]))
    for raw in candidates:
        attempt=int(re.search(r'attempt(\d+)',raw.name)[1])
        request=folder/f'{name}_request_attempt{attempt}.json'
        response=folder/f'{name}_response_attempt{attempt}.json'
        if not request.exists() or not response.exists() or read(request).get('signature')!=stamp:continue
        try:
            value=parse_json(raw.read_text())
            validate(value,name,classes,graph)
            check_output(value,name,payload,audio)
        except (ValueError,AssertionError,KeyError,TypeError):continue
        saved_response=read(response)
        save(folder/(name+'.json'),value)
        save(folder/(name+'_cache.json'),dict(signature=stamp,seconds=0,seconds_unavailable_on_recovery=True,
            usage=saved_response.get('usage'),response_model=saved_response.get('model'),attempt=attempt,
            recovered_from_saved_response=True,citation_policy=POLICY))
        record(folder,name,value,graph,payload,save)
        save(folder/(name+'_offline_recovery.json'),dict(policy=POLICY,source=str(raw),attempt=attempt,
             no_new_model_call=True,output_unchanged=True))
        return value
    return None
