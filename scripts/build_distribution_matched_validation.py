"""Select 30-sample validation subsets per dataset, matching the full-dataset label distribution.

Same rules as build_distribution_matched_subset.py (media filters, largest-remainder quotas, prefer
>=3-correct then 2/1/0), and additionally disjoint from:
- the earlier 400 samples and the new 200+200 training samples (by id);
- MELD: the dialogues of the new training samples;
- both datasets: exact video SHA-256 of the training samples (new and earlier).
Runs on the liang server; reads only. No model is called.
"""
import collections
import datetime
import hashlib
import json
import random
from pathlib import Path

SOURCE = Path('/media/liang/12T/han/emotion_eval_5models_4frames_20261030')
PREVIOUS = Path('/media/liang/12T/han/self_evolution_mer_meld_200_20261101')
TRAIN = Path('/media/liang/12T/han/self_evolution_dist_matched_200_20261104')
OUT = TRAIN / 'validation'
MODELS = ['Emotion-LLaMA', 'AffectGPT', 'AffectGPT-RL', 'OPPO', 'VidEmo-7B']
DATASETS = ['MER2024', 'MELD']
N = 30
SEED = 42
ANOMALOUS = {'MELD/dia38_utt4', 'MELD/dia220_utt0'}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path):
    return [json.loads(l) for l in Path(path).open() if l.strip()]


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def largest_remainder(counts, n):
    total = sum(counts.values())
    exact = {k: n * v / total for k, v in counts.items()}
    quota = {k: int(x) for k, x in exact.items()}
    for k in sorted(counts, key=lambda k: (-(exact[k] - quota[k]), k))[:n - sum(quota.values())]:
        quota[k] += 1
    return quota


def main():
    assert not OUT.exists(), 'validation output already exists'
    media_probe = json.loads((SOURCE / 'self_evolution_media_probe.json').read_text())
    report = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'seed': SEED, 'output': str(OUT), 'datasets': {}}
    all_rows, results = [], {}
    for ds in DATASETS:
        rows = read_jsonl(SOURCE / 'manifests' / (ds + '.jsonl'))
        old = read_jsonl(PREVIOUS / ds / 'selected_200.jsonl')
        new = read_jsonl(TRAIN / ds / 'selected_200.jsonl')
        used_ids = {r['id'] for r in old + new}
        assert len(used_ids) == 400
        train_dialogues = {r['dialogue_id'] for r in old + new} if ds == 'MELD' else set()
        train_hashes = {digest(r['video']) for r in old + new}
        predictions = {}
        for model in MODELS:
            selected = {}
            for line in (SOURCE / 'results' / model / (ds + '.jsonl')).open():
                r = json.loads(line)
                if r['id'] not in selected or selected[r['id']].get('status') != 'success':
                    selected[r['id']] = r
            predictions[model] = selected

        pool, dropped = [], collections.Counter()
        for original in rows:
            r = dict(original)
            if r['id'] in used_ids:
                continue
            reasons = []
            probe = media_probe[r['id']]
            if probe.get('error'):
                reasons.append('media_probe_error')
            else:
                if not 0 < probe['video_seconds'] <= 60: reasons.append('video_duration_outside_0_to_60_seconds')
                if not 0 < probe['audio_seconds'] <= 60: reasons.append('audio_duration_outside_0_to_60_seconds')
                r['video_duration_seconds'] = probe['video_seconds']
                r['audio_duration_seconds'] = probe['audio_seconds']
            for field in ['video', 'audio']:
                if not Path(r[field]).is_file(): reasons.append('missing_' + field)
            if not r.get('subtitle', '').strip(): reasons.append('missing_subtitle')
            frame_cache = SOURCE / 'cache' / 'frames' / (r['id'] + '.npy')
            metadata_path = frame_cache.with_suffix('.json')
            metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
            if not frame_cache.exists() or len(metadata.get('frame_indices', [])) != 4:
                reasons.append('missing_four_frame_cache')
            if metadata.get('repeated'): reasons.append('fewer_than_four_distinct_frames')
            if r['id'] in ANOMALOUS: reasons.append('known_anomalous_multi_minute_source_clip')
            if ds == 'MELD' and r['dialogue_id'] in train_dialogues:
                reasons.append('dialogue_shared_with_training')
            if reasons:
                for reason in reasons: dropped[reason] += 1
                continue
            r['correct_models'] = [m for m in MODELS
                                   if predictions[m][r['id']].get('status') == 'success'
                                   and predictions[m][r['id']].get('prediction') == r['label']]
            r['correct_count'] = len(r['correct_models'])
            r['frames_cache'] = str(frame_cache)
            r['frame_indices'] = metadata['frame_indices']
            r['num_frames'] = 4
            pool.append(r)

        full_counts = collections.Counter(r['label'] for r in rows)
        quota = largest_remainder(full_counts, N)
        rng = random.Random(SEED)
        picked, per_label, hash_dropped = [], {}, 0
        for label in full_counts:
            cands = sorted((r for r in pool if r['label'] == label), key=lambda r: r['id'])
            rng.shuffle(cands)
            cands.sort(key=lambda r: -1 if r['correct_count'] >= 3 else 3 - r['correct_count'])
            take, seen = [], set(train_hashes)
            for r in cands:
                if len(take) == quota[label]: break
                h = digest(r['video'])
                if h in seen:
                    hash_dropped += 1
                    continue
                seen.add(h); r['video_sha256'] = h; take.append(r)
            assert len(take) == quota[label], (ds, label, quota[label], len(take))
            picked += take
            per_label[label] = {'full_count': full_counts[label], 'quota': quota[label],
                                'available_ge3': sum(r['correct_count'] >= 3 for r in cands),
                                'selected_ge3': sum(r['correct_count'] >= 3 for r in take),
                                'supplement_below_3': sum(r['correct_count'] < 3 for r in take)}
        assert len(picked) == N and len({r['id'] for r in picked}) == N
        assert len({r['video_sha256'] for r in picked}) == N

        folder = OUT / ds
        folder.mkdir(parents=True)
        learner, audit = [], []
        for r in sorted(picked, key=lambda r: r['id']):
            example = {k: v for k, v in r.items() if k not in ['correct_count', 'correct_models', 'split']}
            example['source_split'] = r['split']
            example['split'] = 'validation'
            example['target_answer'] = '<answer>' + r['label'] + '</answer>'
            learner.append(example)
            audit.append({'id': r['id'], 'label': r['label'], 'correct_count': r['correct_count'],
                          'correct_models': r['correct_models'],
                          'supplement_below_3': r['correct_count'] < 3,
                          'predictions': {m: predictions[m][r['id']].get('prediction') for m in MODELS}})
        write_jsonl(folder / 'selected_30.jsonl', learner)
        write_jsonl(folder / 'selection_audit.jsonl', audit)
        report['datasets'][ds] = {
            'pool': len(pool), 'removed_before_pool': dict(dropped), 'duplicate_video_hash_skipped': hash_dropped,
            'per_label': per_label,
            'correct_count_histogram': dict(sorted(collections.Counter(a['correct_count'] for a in audit).items()))}
        all_rows += learner
    write_jsonl(OUT / 'validation.jsonl', all_rows)
    (OUT / 'selection_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (OUT / 'README.md').write_text(
        '# Distribution-matched validation subsets (30 per dataset)\n\n'
        'Same rules as the sibling training subsets (full-dataset label shares, >=3-correct preferred, '
        'media-quality filters). Disjoint from the earlier 400 and the new 200+200 training samples; '
        'MELD dialogues are disjoint from training; exact video SHA-256 differs from every training sample. '
        'MER2024 has no film/dialogue IDs, so film/speaker independence is not established.\n\n'
        'Do not use these samples for training or method tuning. selection_audit.jsonl holds model predictions; '
        'keep it out of any model request. Source is official TEST data selected with model correctness, so this is '
        'development data biased toward easier items, not an unbiased test estimate.\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
