"""Select MER2024 / MELD self-evolution subsets whose label distribution matches the full dataset.

Runs on the liang server against the read-only 5-model evaluation folder.
- Excludes the previously selected 400 samples (self_evolution_mer_meld_200_20261101).
- Applies the same media-quality filters as build_self_evolution_subset.py.
- Per-label quotas: largest-remainder rounding of the full-dataset label shares.
- Within a label, prefer samples that >=3 of the 5 models classified correctly (seeded random);
  only if a label has too few of them, supplement with 2-, then 1-, then 0-correct samples.
No model is called; labels are used only for selection.
"""
import collections
import datetime
import hashlib
import json
import random
from pathlib import Path

SOURCE = Path('/media/liang/12T/han/emotion_eval_5models_4frames_20261030')
PREVIOUS = Path('/media/liang/12T/han/self_evolution_mer_meld_200_20261101')
OUT = Path('/media/liang/12T/han/self_evolution_dist_matched_200_20261104')
MODELS = ['Emotion-LLaMA', 'AffectGPT', 'AffectGPT-RL', 'OPPO', 'VidEmo-7B']
DATASETS = ['MER2024', 'MELD']
N = 200
SEED = 42
ANOMALOUS = {'MELD/dia38_utt4', 'MELD/dia220_utt0'}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def largest_remainder(counts, n):
    total = sum(counts.values())
    exact = {k: n * v / total for k, v in counts.items()}
    quota = {k: int(x) for k, x in exact.items()}
    order = sorted(counts, key=lambda k: (-(exact[k] - quota[k]), k))
    for k in order[:n - sum(quota.values())]:
        quota[k] += 1
    return quota


def main():
    media_probe = json.loads((SOURCE / 'self_evolution_media_probe.json').read_text())
    report = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'seed': SEED, 'source': str(SOURCE), 'output': str(OUT), 'datasets': {}}
    all_rows = []
    for ds in DATASETS:
        rows = [json.loads(l) for l in (SOURCE / 'manifests' / (ds + '.jsonl')).open() if l.strip()]
        previous = {json.loads(l)['id'] for l in (PREVIOUS / ds / 'selected_200.jsonl').open() if l.strip()}
        assert len(previous) == 200, (ds, len(previous))
        predictions = {}
        for model in MODELS:
            selected = {}
            for line in (SOURCE / 'results' / model / (ds + '.jsonl')).open():
                r = json.loads(line)
                if r['id'] not in selected or selected[r['id']].get('status') != 'success':
                    selected[r['id']] = r
            predictions[model] = selected

        # Media-quality eligibility, identical to the earlier self-evolution subset.
        pool, excluded = [], collections.Counter()
        for original in rows:
            r = dict(original)
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
            if reasons:
                for reason in reasons: excluded[reason] += 1
                r['_ineligible'] = True
            r['correct_models'] = [m for m in MODELS
                                   if predictions[m][r['id']].get('status') == 'success'
                                   and predictions[m][r['id']].get('prediction') == r['label']]
            r['correct_count'] = len(r['correct_models'])
            r['frames_cache'] = str(frame_cache)
            r['frame_indices'] = metadata.get('frame_indices')
            r['num_frames'] = 4
            if not r.get('_ineligible') and r['id'] not in previous:
                pool.append(r)

        full_counts = collections.Counter(r['label'] for r in rows)
        quota = largest_remainder(full_counts, N)
        rng = random.Random(SEED)
        picked, per_label = [], {}
        for label in full_counts:
            cands = sorted((r for r in pool if r['label'] == label), key=lambda r: r['id'])
            rng.shuffle(cands)
            need = quota[label]
            # >=3-correct first, then 2, 1, 0 only to fill the shortfall.
            cands.sort(key=lambda r: -1 if r['correct_count'] >= 3 else 3 - r['correct_count'])
            take = cands[:need]
            assert len(take) == need, (ds, label, need, len(cands))
            picked += take
            per_label[label] = {
                'full_count': full_counts[label],
                'quota': need,
                'available_ge3_after_exclusion': sum(r['correct_count'] >= 3 for r in cands),
                'selected_ge3': sum(r['correct_count'] >= 3 for r in take),
                'supplement_below_3': sum(r['correct_count'] < 3 for r in take)}
        assert len(picked) == N and len({r['id'] for r in picked}) == N
        assert not {r['id'] for r in picked} & previous

        folder = OUT / ds
        folder.mkdir(parents=True)
        learner, audit = [], []
        for r in sorted(picked, key=lambda r: r['id']):
            example = {k: v for k, v in r.items() if k not in ['correct_count', 'correct_models', 'split', '_ineligible']}
            example['source_split'] = r['split']
            example['split'] = 'train'
            example['target_answer'] = '<answer>' + r['label'] + '</answer>'
            learner.append(example)
            audit.append({'id': r['id'], 'label': r['label'], 'correct_count': r['correct_count'],
                          'correct_models': r['correct_models'],
                          'supplement_below_3': r['correct_count'] < 3,
                          'predictions': {m: predictions[m][r['id']].get('prediction') for m in MODELS}})
        write_jsonl(folder / 'selected_200.jsonl', learner)
        write_jsonl(folder / 'selection_audit.jsonl', audit)
        report['datasets'][ds] = {
            'source_total': len(rows), 'previous_excluded': len(previous),
            'media_ineligible_reasons': dict(excluded), 'pool_after_filters_and_exclusion': len(pool),
            'per_label': per_label,
            'correct_count_histogram': dict(sorted(collections.Counter(a['correct_count'] for a in audit).items())),
            'manifest_sha256': digest(SOURCE / 'manifests' / (ds + '.jsonl'))}
        all_rows += learner
    write_jsonl(OUT / 'train.jsonl', all_rows)
    (OUT / 'selection_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (OUT / 'README.md').write_text(
        '# Distribution-matched self-evolution subsets\n\n'
        'MER2024 and MELD, 200 samples each, disjoint from the earlier 400 (self_evolution_mer_meld_200_20261101). '
        'Per-label counts follow the full-dataset label shares (largest-remainder rounding). '
        'Within a label, >=3-correct samples are preferred; shortfalls are filled with 2-, 1-, then 0-correct samples '
        '(flagged supplement_below_3 in selection_audit.jsonl). Same media-quality filters as the earlier subset. '
        'MELD dialogues are not kept disjoint from anything here, since there is no validation split.\n\n'
        'Ground truth is the original dataset label. Selection agreement and predictions are only in selection_audit.jsonl; '
        'keep them out of any model request. The pool comes from official TEST data, so once used for self-evolution it is '
        'development data, not an untouched test set. Model-correctness filtering biases the sample toward easier items.\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
