"""Run the two authorized single-stage baselines; bounded transport-only recovery."""
import fcntl
import json
import subprocess
from pathlib import Path
from engine import ROOT, save, update_log
from audit_outputs import audit


def publish():
    audits = audit()
    rows = [json.loads(s) for s in (ROOT/'data/manifests/validation.jsonl').read_text().splitlines()]
    methods = {}
    lines = ['# Direct API baseline vs PPCT', '',
             '| Method | MER2024 | MELD | All80 | Audited |', '|---|---:|---:|---:|---:|']
    for provider in ['gpt','gemini']:
        for mode in ['direct','ppct']:
            key = mode+'/'+provider
            item = audits[key]
            valid = {r['id'] for r in item['items'] if r['valid']}
            rs = [json.loads((ROOT/'outputs'/mode/provider/r['id']/'result.json').read_text()) for r in rows if r['id'] in valid]
            stats, values = {}, []
            for ds in ['MER2024','MELD','ALL']:
                selected = [r for r in rs if ds=='ALL' or r['dataset']==ds]
                expected = 80 if ds=='ALL' else 40
                correct = sum(r['prediction']==r['label'] for r in selected)
                acc = correct/expected if len(selected)==expected else None
                stats[ds] = dict(expected=expected,valid=len(selected),correct=correct,accuracy=acc)
                values.append(f'{100*acc:.2f}% ({correct}/{expected})' if acc is not None else f'pending ({len(selected)}/{expected})')
            methods[key] = dict(complete=item['complete'],metrics=stats,recorded_usage=item['recorded_usage'],
                                recorded_responses=item['recorded_response_files'])
            lines.append('| '+key+' | '+' | '.join(values)+f' | {len(valid)}/80 |')
    lines += ['', 'Same fixed 80 development samples and eight frames as PPCT. GPT: frames and available subtitle; Gemini: frames, original audio and available subtitle. Each direct request receives no graph, nodes, prior model predictions or organization text. Output includes explanation and one <answer>label</answer>.',
              '', 'Direct has a single inference stage and accepts one completed response. Transport failures may retry; a received but invalid response is recorded as failure without model-assisted repair. Artifacts and request attempts are preserved. Token totals cover recorded responses only.',
              '', 'These model-selected balanced development samples do not represent untouched benchmark test accuracy. Previous five-model comparisons use four frames.']
    save(ROOT/'metrics/direct_api_baseline_comparison.json',methods)
    (ROOT/'metrics/direct_api_baseline_comparison.md').write_text('\n'.join(lines)+'\n')
    return methods


def main():
    lock=(ROOT/'logs/direct_api_runner.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    jobs={}
    def launch(provider, attempt):
        log=ROOT/'logs'/f'direct_{provider}_attempt{attempt}.log'
        with log.open('a') as stream:
            p=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-u',str(ROOT/'engine.py'),
                '--provider',provider,'--mode','direct','--workers','2'],cwd=ROOT,
                stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        jobs[provider]=dict(process=p,attempt=attempt)
        update_log(f'启动单阶段直接基线{provider}，80条，PID={p.pid}，日志{log.relative_to(ROOT)}。')
    update_log('用户新增授权：GPT/Gemini分别80条直接基线，8帧及可用字幕，Gemini另含音频；每条单阶段输出解释与标签，不使用PPCT上下文，格式失败不模型修复，仅传输失败有限重试。')
    for provider in ['gpt','gemini']: launch(provider,1)
    import time
    while jobs:
        for provider,job in list(jobs.items()):
            code=job['process'].poll()
            if code is None: continue
            del jobs[provider]
            if code and job['attempt']<3:
                # Successful samples are cached. Retry only if all remaining errors are transport failures.
                results=list((ROOT/'outputs/direct'/provider).glob('*/*/result.json'))
                errors=[json.loads(p.read_text()) for p in results if json.loads(p.read_text()).get('status')!='success']
                if errors and all(any(s in r.get('error','') for s in ['HTTP 429','HTTP 50','Connection','timed out','ProxyError','NameResolutionError']) for r in errors):
                    time.sleep(30)
                    launch(provider,job['attempt']+1)
            publish()
        save(ROOT/'logs/direct_api_status.json',dict(running={k:dict(pid=v['process'].pid,attempt=v['attempt']) for k,v in jobs.items()}))
        if jobs: time.sleep(15)
    methods=publish()
    complete=all(methods['direct/'+p]['complete'] for p in ['gpt','gemini'])
    update_log('两API直接基线调度结束，完整审计'+('通过' if complete else '尚有失败需处理')+'；报告metrics/direct_api_baseline_comparison.md。')
    raise SystemExit(0 if complete else 1)


if __name__=='__main__': main()
