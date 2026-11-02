"""Publish API validation metrics only after row-level artifact auditing."""
import json
from engine import ROOT, save
from audit_outputs import audit


def main():
    audits = audit()
    rows = [json.loads(s) for s in (ROOT/'data/manifests/validation.jsonl').read_text().splitlines()]
    methods = {}
    for provider in ['gpt','gemini']:
        base = ROOT/'outputs/ppct'/provider
        valid_ids = {r['id'] for r in audits['ppct/'+provider]['items'] if r['valid']}
        results = [json.loads((base/r['id']/'result.json').read_text()) for r in rows if r['id'] in valid_ids]
        stats = {}
        for ds in ['MER2024','MELD','ALL']:
            selected = [r for r in results if ds=='ALL' or r['dataset']==ds]
            expected = 80 if ds=='ALL' else 40
            correct = sum(r['prediction']==r['label'] for r in selected)
            stats[ds] = dict(expected=expected,audit_valid=len(selected),correct=correct,
                             accuracy=correct/expected if len(selected)==expected else None)
        seconds = sum(json.loads(p.read_text()).get('seconds',0) for p in base.glob('*/*/*_cache.json'))
        methods[provider] = dict(metrics=stats,complete=audits['ppct/'+provider]['complete'],
            usage=audits['ppct/'+provider]['recorded_usage'],
            recorded_responses=audits['ppct/'+provider]['recorded_response_files'],
            successful_stage_response_seconds=seconds,
            usage_scope='Recorded responses; historical overwritten attempts, network failures and separate probes may be absent. Sum of successful stage response times is not end-to-end wall time.')
    save(ROOT/'metrics/api_validation_report.json',methods)
    lines=['# GPT / Gemini PPCT validation','',
           '| Method | MER2024 | MELD | All80 | Audited |','|---|---:|---:|---:|---:|']
    for provider, method in methods.items():
        values=[]
        for ds in ['MER2024','MELD','ALL']:
            s=method['metrics'][ds]
            values.append(f'{100*s["accuracy"]:.2f}% ({s["correct"]}/{s["expected"]})' if s['accuracy'] is not None else 'pending')
        lines.append('| '+provider+' | '+' | '.join(values)+f' | {method["metrics"]["ALL"]["audit_valid"]}/80 |')
    lines += ['', 'Each sample follows perception, temporal/joint judgments, program graph, organization and final inference. Eight chronological frames and available subtitle are used. Gemini also receives audio; GPT audio is omitted because this endpoint rejects it.',
        '', 'Final output contains an evidence explanation and exactly one <answer>label</answer>. MER2024 retains six labels, MELD seven. Gold labels and prior model predictions are excluded from inference payloads. Structural repair feedback, when needed, contains only prior response and validation error.',
        '', 'These are balanced development subsets selected using five prior models, not untouched benchmark tests. The prior five-model comparison uses four frames, so this eight-frame result is not a controlled frame-matched comparison.',
        '', 'API identities are provider-reported aliases. Usage and timing cover recorded response artifacts only; see JSON for scope. Flow/format audit does not establish that every observation or explanation is factually correct.',
        '', 'Omni allows logged structural normalization and removal of invalid edges; GPT/Gemini retain strict validation with model-generated repair feedback. Omni direct and PPCT results remain pending until separately completed and audited.']
    (ROOT/'metrics/api_validation_report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(methods,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
