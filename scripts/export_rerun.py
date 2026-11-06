"""Export the Direct re-run (117 disagreement samples, Gemini and GPT) next to the original Direct run, for the v5 results page.

Server (Linux) only: reads outputs/direct and outputs/direct_rerun, writes metrics/direct_rerun_117.json. No model calls.
Usage: python scripts/export_rerun.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
jr = lambda p: json.loads(Path(p).read_text())
rows = []
for s in ['validation', 'train']:
    rows += [dict(json.loads(l), split=s) for l in (ROOT / 'data/manifests' / (s + '.jsonl')).read_text().splitlines() if l.strip()]
out = {}
for p in ['gemini', 'gpt']:
    recs = []
    for r in rows:
        v = jr(ROOT / 'outputs/reflect_debate_v4' / p / r['id'] / 'result.json')
        if v['route'] == 'common_label':
            continue
        d1 = jr(ROOT / 'outputs/direct' / p / r['id'] / 'result.json')
        d2 = jr(ROOT / 'outputs/direct_rerun' / p / r['id'] / 'result.json')
        recs.append(dict(id=r['id'], dataset=r['dataset'], split=r['split'], gold=r['label'], run1=d1['prediction'], run1_status=d1['status'],
                         run2=d2['prediction'], run2_status=d2['status'], v4=v['prediction']))
    out[p] = recs
(ROOT / 'metrics' / 'direct_rerun_117.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
print('ok', {p: len(out[p]) for p in out})
