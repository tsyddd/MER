"""Accuracy by branch (consensus vs disagreement) for each expert, majority voting, and Direct.

Experts: Round-0 primary and reflected primary of each of the three experts (saved outputs). Voting: majority of the three
reflected primaries (ties -> Direct run 1 if tied, else alphabetical), applied to the disagreement branch; on the consensus
branch voting equals the common label. Direct: run 1 and run 2. No model calls. Writes metrics/branch_acc.json.
Usage: python scripts/branch_acc.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
jr = lambda p: json.loads(Path(p).read_text())
ROLES = ['graph', 'audio_subtitle', 'image']
NAME = {'graph': '图谱专家', 'audio_subtitle': '音频字幕专家', 'image': '图像专家'}
rows = []
for s in ['validation', 'train']:
    rows += [dict(json.loads(l), split=s) for l in (ROOT / 'data/manifests' / (s + '.jsonl')).read_text().splitlines() if l.strip()]
out = {}
for p in ['gemini', 'gpt']:
    B = {'consensus': Counter(), 'disagree': Counter()}
    for r in rows:
        f = ROOT / 'outputs/reflect_debate_v4' / p / r['id']
        res = jr(f / 'result.json')
        br = 'consensus' if res['route'] == 'common_label' else 'disagree'
        g = r['label']
        B[br]['n'] += 1
        r0 = {k: jr(f / f'r0_{k}.json')['output']['answer'] for k in ROLES}
        rf = {k: jr(f / f'reflect_{k}.json')['output']['answer'] for k in ROLES}
        for k in ROLES:
            B[br]['R0 ' + NAME[k]] += r0[k] == g
            B[br]['反思 ' + NAME[k]] += rf[k] == g
        d1 = jr(ROOT / 'outputs/direct' / p / r['id'] / 'result.json')['prediction']
        B[br]['Direct 第一次'] += d1 == g
        q = ROOT / 'outputs/direct_rerun' / p / r['id'] / 'result.json'
        if q.exists():  # the re-run only covers the 117 disagreement samples
            B[br]['Direct 重跑'] += jr(q)['prediction'] == g
            B[br]['Direct 重跑样本数'] += 1
        if br == 'consensus':
            vote = res['prediction']
        else:
            top = Counter(rf.values()).most_common()
            tied = sorted(k for k, v in top if v == top[0][1])
            vote = d1 if (len(tied) > 1 and d1 in tied) else tied[0] if len(tied) > 1 else top[0][0]
            # for disagreement rows, tie among three singletons is also resolved by the rule above
        B[br]['多数投票'] += vote == g
        B[br]['v4 最终'] += res['prediction'] == g
    out[p] = {k: dict(v) for k, v in B.items()}
(ROOT / 'metrics' / 'branch_acc.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
for p in out:
    print(p, json.dumps(out[p], ensure_ascii=False))
