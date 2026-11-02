"""Persistent task runner: API pilots/full runs, then verified local model baseline/PPCT."""
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

from engine import ROOT, save, update_log


def aggregate():
    methods = {}
    for mode, provider in [('direct', 'omni'), ('ppct', 'omni'), ('ppct', 'gpt'), ('ppct', 'gemini')]:
        path = ROOT / 'outputs' / mode / provider / 'summary.json'
        if path.exists():
            methods[mode + '/' + provider] = json.loads(path.read_text())
    save(ROOT / 'metrics/new_methods_validation_acc.json', methods)
    original = json.loads((ROOT / 'metrics/five_models_validation_acc.json').read_text())
    lines = ['# Validation comparison', '',
        'MER2024: 40 samples, six classes. MELD: 40 samples, seven classes. Errors count as incorrect in ACC-all. '
        'These are model-selected development subsets, not untouched benchmark tests.', '',
        '| Method | Frames | MER2024 | MELD | All80 | Completed |',
        '|---|---:|---:|---:|---:|---:|']
    for name, item in original.items():
        vals = [f'{100*item[ds]["accuracy"]:.2f}% ({item[ds]["correct"]}/{item[ds]["total"]})'
                for ds in ['MER2024', 'MELD', 'ALL']]
        lines.append('| ' + name + ' | 4 | ' + ' | '.join(vals) + ' | 80/80 |')
    for name in ['direct/omni', 'ppct/omni', 'ppct/gpt', 'ppct/gemini']:
        if name not in methods:
            lines.append('| ' + name + ' | 8 | pending | pending | pending | 0/80 |')
            continue
        item = methods[name]['metrics']
        vals = [f'{100*item[ds]["accuracy_all"]:.2f}% ({item[ds]["correct"]}/{item[ds]["expected"]})'
                for ds in ['MER2024', 'MELD', 'ALL']]
        lines.append('| ' + name + ' | 8 | ' + ' | '.join(vals) +
                     f' | {item["ALL"]["valid"]}/{item["ALL"]["expected"]} |')
    lines += ['', 'GPT uses eight frames and available subtitle without audio (endpoint rejects audio). '
              'Gemini and Omni use eight frames, original audio and available subtitle. '
              'All PPCT stages are model-specific; original five model answers and gold labels are never sent as inference context.']
    (ROOT / 'metrics/validation_comparison.md').write_text('\n'.join(lines) + '\n')


def main():
    lock = (ROOT / 'logs/orchestrator.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.environ['TZ'] = 'Asia/Shanghai'
    if hasattr(time, 'tzset'):
        time.tzset()
    processes, jobs, errors = {}, {}, {}
    server = None
    server_started = None
    local_ready = False
    local_failed = False
    started = time.time()
    last_logged = 0

    def launch(name, provider, mode, smoke=False, attempt=1):
        args = [str(ROOT / '.venv/bin/python'), '-u', str(ROOT / 'engine.py'),
                '--provider', provider, '--mode', mode, '--workers',
                '1' if smoke or provider == 'omni' else '2']
        if smoke:
            args.append('--smoke')
        log = ROOT / 'logs' / (name + f'_attempt{attempt}.log')
        stream = log.open('a')
        process = subprocess.Popen(args, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, start_new_session=True)
        stream.close()
        processes[name] = process
        jobs[name] = dict(provider=provider, mode=mode, smoke=smoke, attempt=attempt,
                          pid=process.pid, state='running', log=str(log.relative_to(ROOT)))
        update_log(f'调度 {name}，PID={process.pid}，日志 {log.relative_to(ROOT)}。')

    class AdoptedProcess:
        def __init__(self, pid, summary):
            self.pid, self.summary = pid, summary
        def poll(self):
            path = Path('/proc') / str(self.pid) / 'stat'
            if path.exists() and path.read_text().split()[2] != 'Z':
                return None
            if self.summary.exists():
                item = json.loads(self.summary.read_text()).get('metrics', {}).get('ALL', {})
                if item.get('valid') == item.get('expected') == 80:
                    return 0
            return 1

    previous_path = ROOT / 'orchestrator_status.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    for name, job in previous.get('jobs', {}).items():
        if name not in ('gpt_ppct', 'gemini_ppct'):
            continue
        summary = ROOT / 'outputs/ppct' / job['provider'] / 'summary.json'
        process = AdoptedProcess(job['pid'], summary)
        path = Path('/proc') / str(job['pid']) / 'cmdline'
        if process.poll() is None and path.exists() and 'engine.py' in path.read_bytes().decode() and (Path('/proc') / str(job['pid']) / 'cwd').resolve() == ROOT:
            jobs[name] = dict(job, state='running')
            processes[name] = process
            update_log(f'接管现有健康任务{name} PID={job["pid"]}，不重复启动API调用。')
        elif process.poll() == 0:
            jobs[name] = dict(job, state='finished', exit_code=0)

    capabilities = json.loads((ROOT / 'configs/providers.json').read_text())
    for provider in ['gpt', 'gemini']:
        if provider + '_ppct' in jobs:
            continue
        cfg = capabilities[provider]
        if not cfg.get('capabilities_tested') or not cfg.get('images_supported'):
            errors[provider] = 'Required image capability was not verified'
        elif provider == 'gemini' and not cfg.get('audio_supported'):
            errors[provider] = 'Required Gemini audio capability was not verified'
        else:
            launch(provider + '_ppct_smoke', provider, 'ppct', smoke=True)
    update_log('启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。')
    omni_config = capabilities['omni']
    external_omni = omni_config.get('deployment') == 'dashan'
    while time.time() - started < 48 * 3600:
        for name, proc in list(processes.items()):
            code = proc.poll()
            if code is None:
                continue
            job = jobs[name]
            job.update(state='finished' if code == 0 else 'error', exit_code=code)
            del processes[name]
            if code == 0:
                if job['smoke']:
                    launch(job['provider'] + '_' + job['mode'], job['provider'], job['mode'])
                elif name == 'omni_direct':
                    launch('omni_ppct_smoke', 'omni', 'ppct', smoke=True)
            elif not job['smoke'] and job['attempt'] == 1:
                launch(name, job['provider'], job['mode'], attempt=2)
            else:
                errors[name] = 'Execution failed; inspect ' + job['log']
        if external_omni and not local_ready and not local_failed:
            try:
                session = requests.Session()
                session.trust_env = False
                response = session.get(omni_config['base_url'].rstrip('/') + '/models', timeout=(3,5))
                ids = [r['id'] for r in response.json().get('data', [])] if response.ok else []
                if omni_config['model'] in ids:
                    local_ready = True
                    save(ROOT / 'configs/vllm_ready.json', dict(time=time.time(), deployment='dashan',
                         endpoint=omni_config['base_url'], model_ids=ids))
                    update_log('dashan Instruct模型接口已从liang探测就绪；开始两条音视频直接推理检查，之后接续80直接基线与PPCT。')
                    launch('omni_direct_smoke','omni','direct',smoke=True)
            except (requests.RequestException, ValueError):
                pass
        if not external_omni and not local_ready and not local_failed:
            verified = ROOT / 'models/Qwen3-Omni-30B-A3B-Thinking/download_verified.json'
            download_pid_path = ROOT / 'logs/download_modelscope.pid'
            if not verified.exists() and download_pid_path.exists():
                pid = int(download_pid_path.read_text())
                proc = Path('/proc') / str(pid) / 'stat'
                alive = proc.exists() and proc.read_text().split()[2] != 'Z'
                if not alive:
                    errors['download'] = 'Weight downloader exited before verification; inspect logs/download_modelscope.log'
                    local_failed = True
                    update_log('权重下载进程已退出且未生成验证标记；Omni队列暂停，需检查下载错误。')
            if verified.exists() and server is None:
                gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used',
                                               '--format=csv,noheader,nounits'], text=True)
                if all(int(value.strip()) < 1024 for value in gpu.splitlines()[:4]):
                    try:
                        probe = requests.get('http://127.0.0.1:18030/v1/models', timeout=2)
                        occupied = probe.status_code == 200
                    except requests.RequestException:
                        occupied = False
                    if occupied:
                        errors['vllm'] = 'Port 18030 already serves another instance; not replacing it'
                        local_failed = True
                    else:
                        stream = (ROOT / 'logs/vllm.log').open('a')
                        server = subprocess.Popen(['bash', str(ROOT / 'start_vllm.sh')], cwd=ROOT,
                            stdout=stream, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            start_new_session=True)
                        stream.close()
                        server_started = time.time()
                        (ROOT / 'logs/vllm.pid').write_text(str(server.pid))
                        update_log(f'官方权重验证完成；启动四卡vLLM，PID={server.pid}，日志 logs/vllm.log，尚未确认服务就绪。')
            if server is not None:
                if server.poll() is not None:
                    errors['vllm'] = 'Server exited; inspect logs/vllm.log'
                    local_failed = True
                    update_log('vLLM启动失败，未运行Omni实验；查看 logs/vllm.log。')
                else:
                    try:
                        result = requests.get('http://127.0.0.1:18030/v1/models', timeout=3)
                        model_ids = [r['id'] for r in result.json().get('data', [])] if result.ok else []
                        if 'omni30b-thinking' in model_ids:
                            local_ready = True
                            save(ROOT / 'configs/vllm_ready.json', dict(time=time.time(), pid=server.pid,
                                model_ids=model_ids, config='start_vllm.sh'))
                            update_log('vLLM模型接口已就绪；开始两条跨数据集音视频直接推理测试，尚未确认80条基线完成。')
                            launch('omni_direct_smoke', 'omni', 'direct', smoke=True)
                    except (requests.RequestException, ValueError):
                        pass
                    if not local_ready and time.time() - server_started > 1800:
                        errors['vllm'] = 'Server not ready after 30 minutes; inspect logs/vllm.log'
                        local_failed = True
        aggregate()
        state = dict(updated=time.time(), orchestrator_pid=os.getpid(), jobs=jobs, errors=errors,
                     local_ready=local_ready, local_failed=local_failed,
                     download_verified=(ROOT / 'models/Qwen3-Omni-30B-A3B-Thinking/download_verified.json').exists())
        all_success = all(jobs.get(name, {}).get('state') == 'finished'
                          for name in ['gpt_ppct', 'gemini_ppct', 'omni_direct', 'omni_ppct'])
        if all_success:
            from audit_outputs import audit
            audited = audit()
            if not all(item['complete'] for item in audited.values()):
                all_success = False
                errors['audit'] = 'Full stage/format audit failed; inspect metrics/full_stage_format_audit.json'
        state['state'] = 'complete' if all_success else 'running'
        local_terminal = local_failed or (local_ready and any(
            name in jobs and jobs[name]['state'] != 'running'
            for name in ['omni_ppct', 'omni_ppct_smoke']
        )) or ('omni_direct_smoke' in errors) or ('omni_direct' in errors)
        if not processes and local_terminal and not all_success:
            state['state'] = 'needs_attention'
        save(ROOT / 'orchestrator_status.json', state)
        if all_success:
            update_log('80条验证集的Omni直接基线及三模型PPCT均有效完成；比较报告 metrics/validation_comparison.md。vLLM服务继续保留。')
            return
        if state['state'] == 'needs_attention':
            update_log('实验调度结束，有实质故障待处理，见 orchestrator_status.json；未将不完整实验标记为完成。')
            raise SystemExit(1)
        if time.time() - last_logged >= 300:
            active = [name for name, j in jobs.items() if j['state'] == 'running']
            progress_path = ROOT / 'logs/modelscope_download_status.json'
            progress = json.loads(progress_path.read_text()) if progress_path.exists() else {}
            update_log('后台进度：运行任务 ' + ', '.join(active or ['等待权重/服务']) +
                       f'；下载范围 {progress.get("completed_ranges", "?")}/{progress.get("total_ranges", "?")}；'
                       '详见 orchestrator_status.json 和 metrics/validation_comparison.md。')
            last_logged = time.time()
        time.sleep(15)
    update_log('调度达到48小时上限，停止继续等待；已有服务和独立任务状态需核对，不宣称实验完成。')
    raise SystemExit(1)


if __name__ == '__main__':
    main()
