"""Why does the v4 reflect+debate flow not beat the simple baselines on the 80 validation samples?

Reads saved outputs only (no model calls): outputs/reflect_debate_v4/<provider>/<id>/*, the saved v3 summary/expert outputs,
and the saved Direct / original-PPCT results. Gold labels are read only here. Run on the server (the raw outputs live there);
writes metrics/v4_val80_debate_analysis.json, which scripts/build_v4_debate_analysis_page.py turns into a static HTML page.
Usage: python scripts/analyze_v4_debate_80.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V4 = ROOT / 'outputs' / 'reflect_debate_v4'
V3 = ROOT / 'outputs' / 'gemini_graph_emotion_wheel_v3'
ROLES = ['graph', 'audio_subtitle', 'image']


def jr(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


def cut(s, n):
    s = (s or '').replace('\n', ' ')
    return s if len(s) <= n else s[:n] + '…'


def labels(o):
    return {o['answer']} | ({o['alt_answer']} if o.get('alt_answer') else set())


def analyse(provider, rows):
    recs, c = [], Counter()
    for row in rows:
        sid, gold = row['id'], row['label']
        f = V4 / provider / sid
        res = jr(f / 'result.json')
        r0 = {r: jr(f / f'r0_{r}.json')['output'] for r in ROLES}
        rf = {r: jr(f / f'reflect_{r}.json')['output'] for r in ROLES}
        v3 = (jr(V3 / provider / sid / 'summary.json') or {}).get('answer')
        direct = (jr(ROOT / 'outputs/direct' / provider / sid / 'result.json') or {}).get('prediction')
        ppct = (jr(ROOT / 'outputs/ppct' / provider / sid / 'result.json') or {}).get('prediction')
        prim_r0 = [r0[r]['answer'] for r in ROLES]
        prim = [rf[r]['answer'] for r in ROLES]
        union = res['candidate_labels']
        top = Counter(prim).most_common()
        majority = top[0][0] if top[0][1] >= 2 else None
        deb = res['route'] != 'common_label'
        rec = dict(id=sid, dataset=row['dataset'], gold=gold, subtitle=row.get('subtitle', ''), route=res['route'], final=res['prediction'],
                   ok=res['prediction'] == gold, v3_summary=v3, direct=direct, ppct=ppct,
                   r0_primary=dict(zip(ROLES, prim_r0)), reflect_primary=dict(zip(ROLES, prim)),
                   r0_sets={r: sorted(labels(r0[r])) for r in ROLES}, reflect_sets={r: sorted(labels(rf[r])) for r in ROLES},
                   candidate_union=union, majority=majority)
        c['n'] += 1
        c['ok'] += rec['ok']
        c['direct_ok'] += direct == gold
        c['ppct_ok'] += ppct == gold
        c['v3_ok'] += v3 == gold
        c['majority_ok'] += majority == gold
        if not rec['ok']:
            c['wrong'] += 1
            c[f'wrong_route_{res["route"]}'] += 1
            if not deb:
                c['wrong_common_allthree_same_primary'] += len(set(prim)) == 1
                c['wrong_common_gold_in_union'] += gold in union
                c['wrong_common_gold_in_some_primary'] += gold in prim
        if deb:
            c['debated'] += 1
            c['debated_ok'] += rec['ok']
            c['debated_majority_ok'] += majority == gold
            c['debated_v3_ok'] += v3 == gold
            c['debated_direct_ok'] += direct == gold
            c['debated_ppct_ok'] += ppct == gold
            c['debated_gold_in_primary'] += gold in prim
            c['debated_gold_in_union'] += gold in union
            c['debated_gold_in_union_only_via_backup'] += (gold in union and gold not in prim)
            c['debated_split_2_1'] += len(set(prim)) == 2
            c['debated_split_1_1_1'] += len(set(prim)) == 3
            c['debated_all_same_primary_but_no_single_common'] += len(set(prim)) == 1
            c['debated_majority_wrong_final_right'] += (majority != gold and rec['ok'])
            c['debated_majority_right_final_wrong'] += (majority == gold and not rec['ok'])
            c['debated_final_equals_majority'] += (majority is not None and res['prediction'] == majority)
            c['debated_with_majority'] += majority is not None
            c['debated_final_equals_v3'] += res['prediction'] == v3
            rec['debate_rounds'] = res['debate_rounds']
            c['debate_rounds_%d' % res['debate_rounds']] += 1
            experts = {}
            last_state = dict(rf)
            for rd in range(1, res['debate_rounds'] + 1):
                cur = {r: jr(f / f'debate{rd}_{r}.json')['output'] for r in ROLES}
                for r in ROLES:
                    experts.setdefault(r, []).append(dict(round=rd, answer=cur[r]['answer'], changed=cur[r]['changed'], open_emotion=cur[r]['open_emotion'],
                        adopted=[dict(frm=a['from'], verified=cut(a['verified'], 160)) for a in cur[r]['adopted_evidence']],
                        responses=[dict(to=x['expert'], claim=cut(x['their_claim'], 110), reply=cut(x['my_response'], 160), evidence=x['evidence'][:3]) for x in cur[r]['response_to_others']]))
                last_state = cur
            rec['debate'] = {r: dict(reflect_answer=rf[r]['answer'], reflect_open=rf[r]['open_emotion'], reflect_reason=cut(rf[r]['reason'], 200),
                                     reflect_counter=cut(rf[r]['counterevidence'], 140), rounds=experts[r], final=last_state[r]['answer']) for r in ROLES}
            for r in ROLES:
                a0, a1 = rf[r]['answer'], last_state[r]['answer']
                c['debate_expert_total'] += 1
                if a0 != a1:
                    c['debate_expert_changed'] += 1
                    c['flip_to_majority'] += (majority is not None and a1 == majority)
                    c['flip_correct_to_wrong'] += (a0 == gold and a1 != gold)
                    c['flip_wrong_to_correct'] += (a0 != gold and a1 == gold)
                    c['flip_wrong_to_wrong'] += (a0 != gold and a1 != gold)
                else:
                    c['debate_expert_held'] += 1
                    c['held_correct'] += a0 == gold
                if majority is not None and a0 != majority:  # minority expert
                    c['minority_experts'] += 1
                    c['minority_correct'] += a0 == gold
                    c['minority_adopted_majority'] += a1 == majority
                    c['minority_correct_persuaded_away'] += (a0 == gold and a1 != gold)
            c['summary_used'] += res['route'] == 'summary'
        recs.append(rec)
    return dict(counts=dict(c), samples=recs)


def main():
    rows = [json.loads(l) for l in (ROOT / 'data/manifests/validation.jsonl').read_text().splitlines() if l.strip()]
    out = {p: analyse(p, rows) for p in ['gemini', 'gpt']}
    (ROOT / 'metrics' / 'v4_val80_debate_analysis.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf8')
    for p, d in out.items():
        print(p, json.dumps(d['counts'], ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
