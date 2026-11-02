import concurrent.futures
import json
import time
from pathlib import Path

from engine import ROOT, Client, prepare_frames, save, update_log


def main():
    rows = [json.loads(l) for l in (ROOT / 'data/manifests/validation.jsonl').open()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        prepared = list(pool.map(prepare_frames, rows))
    assert len(prepared) == 80 and all(len(r['frames']) == 8 for r in prepared)
    save(ROOT / 'data/frames8/verification.json', dict(samples=80, frames_per_sample=8,
         repeated_frame_samples=sum(r['repeated'] for r in prepared)))
    config_path = ROOT / 'configs/providers.json'
    config = json.loads(config_path.read_text())
    report = {}
    # A common audiovisual probe without subtitle or gold emotion.
    row = next(r for r in rows if r['dataset'] == 'MER2024')
    frames = prepare_frames(row)['frames']
    for provider in ['gpt', 'gemini']:
        client = Client(provider)
        report[provider] = {}
        for mode, audio in [('images8', None), ('images8_audio', row['audio'])]:
            try:
                text, raw, seconds = client.generate('Describe only what you can directly perceive.',
                    'Describe one visible detail. If audio is provided, transcribe a short audible phrase or describe its audible content. Do not guess missing audio.',
                    frames, audio, max_tokens=1536)
                save(ROOT / 'configs' / f'probe_{provider}_{mode}_response.json', raw)
                report[provider][mode] = dict(success=True, text=text, seconds=seconds,
                                              response_model=raw.get('model'), usage=raw.get('usage'))
            except Exception as exc:
                report[provider][mode] = dict(success=False, error=client.clean(exc))
        config[provider]['images_supported'] = report[provider]['images8']['success']
        config[provider]['audio_supported'] = report[provider]['images8_audio']['success']
        config[provider]['capabilities_tested'] = True
        save(ROOT / 'configs/multimodal_probe.json', report)
        save(config_path, config)
        print(provider, json.dumps(report[provider], ensure_ascii=False), flush=True)
    update_log('完成80条8帧预处理和外部API多模态探测；结果 configs/multimodal_probe.json，实际模态写入 configs/providers.json。')


if __name__ == '__main__':
    main()
