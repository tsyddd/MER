"""Audit unique fixed validation rows and required artifacts, without API calls."""
import json
import re
from pathlib import Path
from engine import ROOT, save
from reference.ppct_api.schemas import GraphOutput


def audit():
    rows = [json.loads(s) for s in (ROOT/'data/manifests/validation.jsonl').read_text().splitlines()]
    report = {}
    for mode, provider in [('direct','omni'),('ppct','omni'),('ppct','gpt'),('ppct','gemini'),('direct','gpt'),('direct','gemini')]:
        items, usage, calls = [], {}, 0
        correct = {'MER2024':0,'MELD':0}
        for row in rows:
            folder = ROOT/'outputs'/mode/provider/row['id']
            issues = []
            result_path = folder/'result.json'
            result = json.loads(result_path.read_text()) if result_path.exists() else {}
            if result.get('status') != 'success':
                issues.append('missing/error: '+str(result.get('error','not yet completed'))[:200])
            else:
                try:
                    assert result['id'] == row['id'], 'sample identity'
                    assert result['prediction'] in row['classes'], 'label space'
                    assert result['emotion_analysis'].strip(), 'empty explanation'
                    tags = re.findall(r'<answer>(.*?)</answer>',result['output'],re.S)
                    assert tags == [result['prediction']], 'answer tag mismatch'
                    assert result['output'].count('<answer>') == result['output'].count('</answer>') == 1, 'duplicate tags'
                    protocol = json.loads((folder/'input_protocol.json').read_text())
                    assert len(protocol['frames']['frames']) == 8, 'frame count'
                    assert all(Path(p).is_file() for p in protocol['frames']['frames']), 'missing frames'
                    assert result['audio_provided'] == (provider != 'gpt'), 'audio protocol'
                    stages = ['final'] if mode == 'direct' else ['perception','temporal','joint','organization','final']
                    for stage in stages:
                        for suffix in ['.json','_cache.json','_request.json']:
                            assert (folder/(stage+suffix)).is_file(), 'missing '+stage+suffix
                        request = json.loads((folder/(stage+'_request.json')).read_text())
                        def check_keys(value):
                            if isinstance(value,dict):
                                assert not {'label','gold','ground_truth','prediction','teacher_predictions'} & set(value), 'label/prediction leak'
                                for v in value.values(): check_keys(v)
                            elif isinstance(value,list):
                                for v in value: check_keys(v)
                        check_keys(request['payload'])
                        for attempt_request in folder.glob(stage+'_request_attempt*.json'):
                            check_keys(json.loads(attempt_request.read_text())['payload'])
                    if mode == 'ppct':
                        graph = GraphOutput.model_validate_json((folder/'graph.json').read_text())
                        assert graph.nodes, 'empty evidence'
                        assert (folder/'nodes.json').is_file(), 'missing nodes'
                        organization = json.loads((folder/'organization.json').read_text())['text']
                        assert organization.strip(), 'empty organization'
                    if result['prediction'] == row['label']: correct[row['dataset']] += 1
                except Exception as exc: issues.append(str(exc))
            for p in folder.glob('*_response_attempt*.json'):
                calls += 1
                data = json.loads(p.read_text()).get('usage',{}) or {}
                for key in ['prompt_tokens','completion_tokens','total_tokens']:
                    if isinstance(data.get(key),(int,float)): usage[key] = usage.get(key,0)+data[key]
            items.append(dict(id=row['id'],valid=not issues,issues=issues))
        good = sum(i['valid'] for i in items)
        report[mode+'/'+provider] = dict(expected=80,audit_valid=good,incomplete_or_invalid=80-good,
            complete=good==80,correct=correct,accuracy_final={ds:correct[ds]/40 for ds in correct} if good==80 else None,
            recorded_response_files=calls,recorded_usage=usage,
            usage_note='Recorded response files only; network failures and overwritten historical attempts may not be included.',
            items=items)
    save(ROOT/'metrics/full_stage_format_audit.json',report)
    print(json.dumps({k:{f:v[f] for f in ['audit_valid','incomplete_or_invalid','complete']} for k,v in report.items()},indent=2))
    return report


if __name__ == '__main__': audit()
