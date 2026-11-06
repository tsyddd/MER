"""只读诊断：v4 不一致（辩论）分支上，辩论到底发生了什么。

对应文献里可检验的量：
- When Debate Helps：可恢复余量 H（多数错、但正确答案在提议里）、恢复 R、损伤 L；
- 2609.38324：正确的少数派专家在辩论中是坚持还是被说服（压制 / 内化的代理量）；
- 2606.02866：救回 vs 带偏。

只读 metrics/reflect_debate_v4_{gemini,gpt}_all.json（逐样本 gold、反思主答案、各轮辩论答案、最终答案）。
真实标签只用于评估；没有任何模型调用。这是开发集上的探索性统计，不用于选方法或调参。
Usage: python -X utf8 -I scripts/analyze_disagreement_branch.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPERTS = ['graph', 'audio_subtitle', 'image']


def primary(x):
    return x[0] if x else None


def plurality(labels):
    c = Counter(l for l in labels if l)
    if not c:
        return None, True
    top = c.most_common()
    tie = len(top) > 1 and top[0][1] == top[1][1]
    return top[0][0], tie


def analyze(provider):
    ps = json.load(open(ROOT / f'metrics/reflect_debate_v4_{provider}_all.json', encoding='utf8'))['per_sample']
    deb = [p for p in ps if p['route'] != 'common_label']
    out = dict(n_all=len(ps), n_branch=len(deb))
    c = Counter()
    per_exp = {e: Counter() for e in EXPERTS}
    moves = Counter()  # 每位专家从反思答案到辩论末轮答案
    minority = Counter()  # 孤立专家（另两位一致且与其不同）是否坚持
    for p in deb:
        g = p['gold']
        refl = {e: primary(p['reflect'].get(e)) for e in EXPERTS}
        r0 = {e: primary(p['r0'].get(e)) for e in EXPERTS}
        rounds = [p['debate'][k] for k in sorted(p['debate'])]
        last = rounds[-1] if rounds else {}
        maj, tie = plurality(refl.values())
        union = set(refl.values()) - {None}
        c['gold in reflect primaries (P=1)'] += g in union
        c['reflect plurality correct (V=1, ties wrong)'] += (maj == g and not tie)
        c['reflect three-way tie'] += tie
        c['final correct'] += p['final'] == g
        c['v3 summary correct'] += p['v3_summary'] == g
        v = (maj == g and not tie)
        if not v and g in union:
            c['headroom H: V=0 and P=1'] += 1
            c['recovery: H and final correct'] += p['final'] == g
        if v:
            c['damage: V=1 and final wrong'] += p['final'] != g
        c['debate rounds >=2'] += len(rounds) >= 2
        for e in EXPERTS:
            per_exp[e]['r0 correct'] += r0[e] == g
            per_exp[e]['reflect correct'] += refl[e] == g
            per_exp[e]['debate-final correct'] += last.get(e) == g
            a, b = refl[e], last.get(e)
            if b is None:
                continue
            if a != b:
                moves['changed'] += 1
                moves['wrong->right' if (a != g and b == g) else 'right->wrong' if (a == g and b != g) else 'wrong->wrong'] += 1
            else:
                moves['kept'] += 1
            others = [refl[o] for o in EXPERTS if o != e]
            if others[0] == others[1] and others[0] != a:  # e 是孤立少数
                kind = 'lone expert correct' if a == g else 'lone expert wrong'
                minority[kind + ' n'] += 1
                minority[kind + ' kept'] += (b == a)
                minority[kind + ' followed others'] += (b == others[0])
    out['counts'] = dict(c)
    out['per_expert_on_branch'] = {e: dict(v) for e, v in per_exp.items()}
    out['expert_moves_reflect_to_debate'] = dict(moves)
    out['lone_expert'] = dict(minority)
    return out


def main():
    res = {p: analyze(p) for p in ['gemini', 'gpt']}
    (ROOT / 'metrics/disagreement_branch_diagnostic.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf8')
    for p, r in res.items():
        print('==', p, 'branch', r['n_branch'], '/', r['n_all'])
        for k, v in r['counts'].items():
            print('  ', k, v)
        print('   per expert:', json.dumps(r['per_expert_on_branch'], ensure_ascii=False))
        print('   moves:', r['expert_moves_reflect_to_debate'])
        print('   lone expert:', r['lone_expert'])


if __name__ == '__main__':
    main()
