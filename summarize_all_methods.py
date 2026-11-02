"""Audited comparison of fixed validation samples; no inference/API calls."""
import json
from pathlib import Path
from engine import ROOT, save
from audit_outputs import audit


def main():
    audited=audit()
    rows=[json.loads(s) for s in (ROOT/'data/manifests/validation.jsonl').read_text().splitlines()]
    prior=json.loads((ROOT/'metrics/five_models_validation_acc.json').read_text())
    methods={}
    lines=['# Fixed validation comparison','',
           '| Model / method | Frames | MER2024 | MELD | All80 | Valid |',
           '|---|---:|---:|---:|---:|---:|']
    for model,item in prior.items():
        vals=[f'{100*item[ds]["accuracy"]:.2f}% ({item[ds]["correct"]}/{item[ds]["total"]})' for ds in ['MER2024','MELD','ALL']]
        lines.append('| '+model+' | 4 | '+' | '.join(vals)+' | 80/80 |')
    for provider in ['omni','gpt','gemini']:
        for mode in ['direct','ppct']:
            key=mode+'/'+provider;inspection=audited[key]
            base=ROOT/'outputs'/mode/provider
            valid_ids={i['id'] for i in inspection['items'] if i['valid']}
            results=[json.loads((base/r['id']/'result.json').read_text()) for r in rows if r['id'] in valid_ids]
            stats={};vals=[]
            for ds in ['MER2024','MELD','ALL']:
                rs=[r for r in results if ds=='ALL' or r['dataset']==ds]
                expected=80 if ds=='ALL' else 40
                correct=sum(r['prediction']==r['label'] for r in rs)
                accuracy=correct/expected if len(rs)==expected else None
                stats[ds]=dict(expected=expected,valid=len(rs),correct=correct,accuracy=accuracy)
                vals.append(f'{100*accuracy:.2f}% ({correct}/{expected})' if accuracy is not None else f'pending ({len(rs)}/{expected})')
            seconds=sum(json.loads(p.read_text()).get('seconds',0) for p in base.glob('*/*/*_cache.json'))
            repair_files=list(base.glob('*/*/*_repairs_attempt*.json'))
            repairs=sum(bool(json.loads(p.read_text()).get('repairs')) for p in repair_files)
            label='Qwen3-Omni-30B-A3B-Instruct' if provider=='omni' else provider
            methods[key]=dict(model=label,mode=mode,frames=8,complete=inspection['complete'],metrics=stats,
                recorded_responses=inspection['recorded_response_files'],recorded_usage=inspection['recorded_usage'],
                successful_stage_seconds=seconds,logged_structural_repair_records=repairs)
            lines.append('| '+label+' / '+mode+' | 8 | '+' | '.join(vals)+f' | {len(valid_ids)}/80 |')
    complete=all(m['complete'] for m in methods.values())
    document=dict(complete=complete,methods=methods,prior_five_models=prior,
        protocol=dict(validation_samples=80,mer2024=40,meld=40,mer_classes=6,meld_classes=7,
            prior_frames=4,new_frames=8,omni_audio=True,gemini_audio=True,gpt_audio=False),
        limits=['Balanced development subset selected using prior model correctness, not untouched benchmark accuracy.',
                'Four-frame prior models versus eight-frame new methods are not a controlled frame-matched comparison.',
                'Audit verifies flow/format and input protocol, not factual correctness of each explanation.',
                'Recorded usage may omit overwritten historical retries, network failures and separate probes; summed successful stage times are not end-to-end wall time.',
                'Omni permits logged structural normalization/deletion of invalid edges and recovery of complete typed nodes from truncated responses, discarding incomplete tails and exact repeated content; GPT/Gemini use strict validation with generated repair feedback.'])
    save(ROOT/'metrics/all_methods_validation_report.json',document)
    lines+=['','All six new-method groups audited: '+str(complete)+'. Pending groups have no final ACC.',
            '', '| Method | Valid / expected | Incomplete or invalid | Recorded responses | Prompt tokens | Completion tokens | Total tokens | Successful stage time (seconds) |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    for key,m in methods.items():
        usage=m['recorded_usage']; valid=m['metrics']['ALL']['valid']
        lines.append(f'| {key} | {valid}/80 | {80-valid} | {m["recorded_responses"]} | {usage.get("prompt_tokens",0)} | {usage.get("completion_tokens",0)} | {usage.get("total_tokens",0)} | {m["successful_stage_seconds"]:.1f} |')
    lines += [
            '', 'GPT uses frames and available subtitle; Gemini/Omni also receive original audio. Direct inference has one stage and no graph/organization context; PPCT has five stages including a program-built graph. Output includes evidence explanation and exactly one <answer>label</answer>.',
            '', 'Omni is the existing Instruct checkpoint served on dashan; Thinking is retained on liang but unused in this evaluation.',
            '', 'Limits:']+['- '+s for s in document['limits']]
    (ROOT/'metrics/all_methods_validation_report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:dict(valid=v['metrics']['ALL']['valid'],complete=v['complete'],accuracy=v['metrics']['ALL']['accuracy']) for k,v in methods.items()},indent=2))
    return document


if __name__=='__main__':main()
