"""Build docs/expert-union-confusable.html: what "expert answers ∪ confusable labels" looks like on the 80 samples.

For every sample: E = set of the three v3 expert answers; N(E) = labels "confusable" with any label in E;
C = E ∪ N(E). "Confusable" is learned from error events (gold != prediction) of 10 result sets
(GPT, Gemini x Direct / PPCT / v1 / v2 / v3 summary), per dataset, unordered pairs with >= t errors.
Each row uses a leave-one-sample-out table (the sample's own errors are removed) so the sample cannot
"peek" at its own answer. Static HTML, no model calls. Usage: python scripts/build_candidate_set_view.py
"""
import json
import sys
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import build_confusion_view as BC  # noqa: E402
from build_debate_vs_vote import CSS as BASE_CSS  # noqa: E402

OUT = ROOT / 'outputs'
V3 = OUT / 'gemini_graph_emotion_wheel_v3'
ROLES = ['graph', 'audio_subtitle', 'image']
RN = {'graph': '图', 'audio_subtitle': '音', 'image': '像'}
GOLD, DS = BC.GOLD, BC.DS
M5 = ['direct', 'ppct', 'v1', 'v2', 'v3']
DEFAULT_T = 5
SWEEP = [3, 5, 8, 12, 20]
EXTRA_CSS = '''.cset{display:inline-block;margin:1px 2px}.sz{font:12px Consolas,monospace;color:#607583}.hit{background:#e3f3ea}.near{background:#fff3da}.miss{background:#fbe4de}
.hub{font-weight:700}.mini{display:inline-block;height:12px;background:#9fb4aa;border-radius:2px;vertical-align:middle}'''


def e(s):
    return escape(str(s), quote=True)


def jread(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf8'))
    except Exception:
        return None


S = {(p, m): BC.preds(m, p) for p in ('gpt', 'gemini') for m in M5}
pair_tot = defaultdict(Counter)
pair_own = defaultdict(Counter)
dir_tot = defaultdict(Counter)  # (dataset) -> (pred, gold) -> count
dir_own = defaultdict(Counter)  # sample -> (pred, gold) -> count
for (p, m), pr in S.items():
    for i, a in pr.items():
        if a != GOLD[i]:
            k = frozenset((GOLD[i], a))
            pair_tot[DS[i]][k] += 1
            pair_own[i][k] += 1
            dir_tot[DS[i]][(a, GOLD[i])] += 1
            dir_own[i][(a, GOLD[i])] += 1


def neighbours(ds, label, t, exclude=None):
    """labels confusable with `label` (unordered pair with >= t error events, optionally without sample `exclude`)."""
    out = {}
    for pair, v in pair_tot[ds].items():
        if label in pair:
            v2 = v - (pair_own[exclude].get(pair, 0) if exclude else 0)
            if v2 >= t:
                (other,) = pair - {label}
                out[other] = v2
    return out


def provider_rows(prov, t):
    rows = []
    for i, g in GOLD.items():
        es = [jread(V3 / prov / i / f'expert_{r}.json') for r in ROLES]
        s = jread(V3 / prov / i / 'summary.json')
        if any(x is None or 'answer' not in x for x in es) or not s:
            continue
        ds = DS[i]
        K = len(BC.ORDER[ds])
        labels = [x['answer'] for x in es]
        E = set(labels)
        N = set()
        for l in E:
            N |= set(neighbours(ds, l, t, exclude=i))
        N -= E
        C = E | N
        rows.append(dict(id=i, ds=ds, K=K, gold=g, labels=labels, E=E, N=N, C=C, summ=s['answer'],
                         inE=g in E, inC=g in C, chance=len(C) / K))
    return rows


def sweep(prov):
    out = []
    for t in SWEEP:
        r = provider_rows(prov, t)
        n = len(r)
        miss_E = [x for x in r if not x['inE']]
        out.append(dict(t=t, n=n, size=sum(len(x['C']) for x in r) / n, K=sum(x['K'] for x in r) / n, cov=sum(x['inC'] for x in r),
                        chance=sum(x['chance'] for x in r), nmiss=len(miss_E), cov_miss=sum(x['inC'] for x in miss_E),
                        chance_miss=sum(x['chance'] for x in miss_E)))
    return out


def ranked_extras(i, ds, E):
    """Labels not in E, ranked by how often (leave-one-sample-out) experts saying a label of E had this label as gold.
    Score = sum over l in E of count(pred=l, gold=x). Labels with score 0 follow in alphabetical order (arbitrary)."""
    sc = Counter()
    for (pred, gold), v in dir_tot[ds].items():
        if pred in E and gold not in E:
            sc[gold] += v - dir_own[i].get((pred, gold), 0)
    scored = sorted((x for x in sc if sc[x] > 0), key=lambda x: (-sc[x], x))
    rest = sorted(x for x in BC.ORDER[ds] if x not in E and x not in scored)
    return scored, rest


def topk_stats(prov):
    rows = []
    for i, g in GOLD.items():
        es = [jread(V3 / prov / i / f'expert_{r}.json') for r in ROLES]
        if any(x is None or 'answer' not in x for x in es):
            continue
        ds = DS[i]
        E = {x['answer'] for x in es}
        scored, rest = ranked_extras(i, ds, E)
        order = scored + rest
        R = len(order)
        pos = order.index(g) + 1 if g in order else None  # None => gold already in E
        rows.append(dict(id=i, ds=ds, E=E, gold=g, R=R, pos=pos, n_scored=len(scored), in_scored=(g in scored)))
    return rows


def topk_section(prov):
    rows = topk_stats(prov)
    n = len(rows)
    inE = [r for r in rows if r['pos'] is None]
    miss = [r for r in rows if r['pos'] is not None]
    kmax = max(r['R'] for r in miss)
    h = (f'<p>真实标签已在 E 内：<b>{len(inE)}</b> 条（不需要加任何标签）；不在 E 内、需要靠加标签捞回的：<b>{len(miss)}</b> 条。'
         f'下面是"再往 E 里加 k 个标签（按排序从高到低取）"能捞回多少，随机期望是"随机加 k 个不在 E 里的标签"。</p>'
         '<table><tr><th>再加 k 个标签</th><th>平均候选集大小</th><th>捞回条数（共 %d 条）</th><th>捞回比例</th><th>随机加 k 个的期望条数</th><th>整体覆盖（80 条）</th></tr>' % len(miss))
    for k in range(0, kmax + 1):
        hit = sum(1 for r in miss if r['pos'] <= k)
        rnd = sum(min(k, r['R']) / r['R'] for r in miss)
        size = sum(len(r['E']) + min(k, r['R']) for r in rows) / n
        h += (f'<tr><td class="n">{k}</td><td class="n">{size:.2f}</td><td class="n"><b>{hit}</b></td><td class="n">{100 * hit / len(miss):.0f}%</td>'
              f'<td class="n">{rnd:.1f}（{100 * rnd / len(miss):.0f}%）</td><td class="n">{len(inE) + hit}/{n} = {100 * (len(inE) + hit) / n:.0f}%</td></tr>')
    h += '</table>'
    # rank histogram
    cnt = Counter(r['pos'] for r in miss)
    sc_in = sum(1 for r in miss if r['in_scored'])
    h += (f'<h3>真实标签排在第几位（只看不在 E 内的 {len(miss)} 条）</h3><table><tr><th>真实标签的排名</th><th>条数</th></tr>'
          + ''.join(f'<tr><td>第 {k} 位</td><td class="n">{v}</td></tr>' for k, v in sorted(cnt.items()))
          + f'</table><p class="muted small">其中真实标签有"非零分数"（即在其他样本里见过这种混淆）的有 {sc_in}/{len(miss)} 条；其余是排在末尾、按字母序取的标签，等同随机。</p>')
    return h


def lab(l, gold):
    return f'<span class="l {"ok" if l == gold else "bad"}">{e(l)}</span>'


def confusable_table():
    h = '<table><tr><th>数据集</th><th>标签</th><th>与它"易混淆"的标签（错判次数，两个方向合计，≥ %d）</th></tr>' % DEFAULT_T
    for ds in ('MER2024', 'MELD'):
        for l in BC.ORDER[ds]:
            nb = neighbours(ds, l, DEFAULT_T)
            txt = '，'.join(f'<b>{e(o)}</b>（{v}）' for o, v in sorted(nb.items(), key=lambda kv: -kv[1])) or '<span class="muted">无</span>'
            h += f'<tr><td>{ds}</td><td><b>{e(l)}</b></td><td>{txt}</td></tr>'
    return h + '</table>'


def sweep_table(prov):
    h = ('<table><tr><th>阈值 t（至少 t 次错判才算易混淆）</th><th>平均候选集大小</th><th>平均标签总数</th><th>真实标签∈候选集</th><th>随机期望</th>'
         '<th>专家全错的样本数</th><th>其中真实标签∈候选集</th><th>随机期望</th></tr>')
    for r in sweep(prov):
        h += (f'<tr><td class="n">{r["t"]}</td><td class="n">{r["size"]:.2f}</td><td class="n">{r["K"]:.1f}</td><td class="n">{r["cov"]}/{r["n"]} = {100 * r["cov"] / r["n"]:.0f}%</td>'
              f'<td class="n">{100 * r["chance"] / r["n"]:.0f}%</td><td class="n">{r["nmiss"]}</td><td class="n"><b>{r["cov_miss"]}/{r["nmiss"]}</b> = {100 * r["cov_miss"] / r["nmiss"]:.0f}%</td>'
              f'<td class="n">{100 * r["chance_miss"] / r["nmiss"]:.0f}%</td></tr>')
    return h + '</table>'


def summary_block(rows):
    n = len(rows)
    inE = sum(x['inE'] for x in rows)
    near = sum((not x['inE']) and x['inC'] for x in rows)
    miss = sum(not x['inC'] for x in rows)
    szE = Counter(len(x['E']) for x in rows)
    szC = Counter(len(x['C']) for x in rows)
    mx = max(szC.values())
    bars = ''.join(f'<tr><td>候选集含 {k} 个标签</td><td><span class="mini" style="width:{160 * v / mx:.0f}px"></span> <span class="sz">{v} 条</span></td></tr>' for k, v in sorted(szC.items()))
    return (f'<table><tr><th>真实标签在…</th><th>条数</th><th>占比</th></tr>'
            f'<tr class="hit"><td>专家答案集合 E 内（有专家答对）</td><td class="n">{inE}</td><td class="n">{100 * inE / n:.0f}%</td></tr>'
            f'<tr class="near"><td>不在 E，但在易混淆邻居里（靠扩展候选集才能捞回）</td><td class="n">{near}</td><td class="n">{100 * near / n:.0f}%</td></tr>'
            f'<tr class="miss"><td>连候选集 C 也不在</td><td class="n">{miss}</td><td class="n">{100 * miss / n:.0f}%</td></tr></table>'
            f'<p class="muted small">E 的大小：' + '，'.join(f'{k} 个标签 {v} 条' for k, v in sorted(szE.items())) + f'；平均 |E| = {sum(len(x["E"]) for x in rows) / n:.2f}，平均 |C| = {sum(len(x["C"]) for x in rows) / n:.2f}。</p>'
            f'<table><tr><th>候选集大小</th><th>条数</th></tr>{bars}</table>')


def sample_table(rows):
    h = ('<table><tr><th>样本</th><th>真实</th><th>专家（图 / 音 / 像）</th><th>E（专家答案）</th><th>邻居 N(E) − E</th><th>候选集 |C| / 标签数</th><th>真实标签落在</th></tr>')
    order = {'in': 0, 'near': 1, 'miss': 2}
    def key(x):
        return order['in' if x['inE'] else 'near' if x['inC'] else 'miss']
    for x in sorted(rows, key=lambda x: (key(x), x['ds'], x['id'])):
        g = x['gold']
        k = key(x)
        cls = ['hit', 'near', 'miss'][k]
        where = ['E 内（专家有对）', '仅在邻居里', '候选集外'][k]
        h += (f'<tr class="{cls}"><td>{e(x["id"])}</td><td>{e(g)}</td><td>{" / ".join(lab(l, g) for l in x["labels"])}</td>'
              f'<td>{" ".join(lab(l, g) for l in sorted(x["E"]))}</td><td>{" ".join(lab(l, g) for l in sorted(x["N"])) or "—"}</td>'
              f'<td class="n">{len(x["C"])} / {x["K"]}</td><td><b>{where}</b></td></tr>')
    return h + '</table>'


def build():
    body = f'''<div class="eyebrow">CANDIDATE SET</div>
<h1>"专家答案 ∪ 易混淆标签"在 80 条样本上长什么样</h1>
<p class="muted">对每条样本：E = v3 三位专家的答案集合；N(E) = 与 E 中任一标签"易混淆"的标签；候选集 C = E ∪ N(E)。想检验的是：把候选集扩大到易混淆标签之后，真实标签是不是基本都在里面，以及这个扩大值不值得。</p>
<div class="warn"><b>"易混淆"的定义（需要先看懂）：</b>在 GPT 与 Gemini 的 10 组结果（Direct、原始 PPCT、v1、v2、v3 汇总）里，按数据集统计所有判错事件，标签对（不分方向）错判次数 ≥ t 就算易混淆，默认 t = {DEFAULT_T}。每一行都用<b>去掉该样本自己的错误</b>之后的表来算（留一法），避免样本"偷看"自己的答案。80 条是复用的开发集，样本小，结论只能看趋势。</div>

<section class="panel"><h2>① 易混淆标签表（t = {DEFAULT_T}，用全部样本）</h2>{confusable_table()}
<p class="muted small">注意 <b>neutral</b>、<b>worried</b>（MER）、<b>anger</b>（MELD）几乎和所有标签都"易混淆"，它们是 hub：把任何一个包含它们的 E 扩展一次，候选集就会变得很大。</p></section>
'''
    for prov in ('gpt', 'gemini'):
        rows = provider_rows(prov, DEFAULT_T)
        body += f'''<section class="panel"><h2>② {prov.upper()}（v3 三位专家）</h2>
<h3>真实标签落在哪</h3>{summary_block(rows)}
<h3>往候选集里再加 1 个、2 个、3 个…标签：逐个加入的捞回统计</h3>{topk_section(prov)}
<h3>候选集扩大到多大才捞回多少：阈值扫描</h3>{sweep_table(prov)}
<p class="muted small">阈值越低，"易混淆"越宽松，候选集越大，覆盖率越高，但随机期望也同步升高。要看的是<b>覆盖率是否明显高于随机期望</b>。最右两列针对"专家全错"的样本，那才是候选集扩展真正要救的。</p>
<h3>逐条（按真实标签落点排序）</h3>
<p class="muted small">标签颜色：绿色 = 等于这条样本的真实标签，红色 = 不是。所以"仅在邻居里"那些行，会在"邻居"一列看到一个绿色标签，就是靠扩展候选集才找到的真实标签。</p>{sample_table(rows)}</section>'''
    body += '<p class="muted small" style="margin-top:20px">由 scripts/build_candidate_set_view.py 生成；静态页面，不依赖脚本，不调用模型。</p>'
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>专家答案与易混淆标签</title><style>{BASE_CSS}{EXTRA_CSS}</style></head><body><main>{body}</main></body></html>'


def main():
    out = ROOT / 'docs' / 'expert-union-confusable.html'
    out.write_text(build(), encoding='utf8')
    print(out, out.stat().st_size // 1024, 'KB')
    for prov in ('gpt', 'gemini'):
        tk = topk_stats(prov)
        miss = [r for r in tk if r['pos'] is not None]
        print(f'\n[{prov}] 不在 E 内 {len(miss)} 条；逐个加入 k 个标签的捞回数:', [(k, sum(1 for r in miss if r['pos'] <= k), round(sum(min(k, r['R']) / r['R'] for r in miss), 1)) for k in range(0, 7)])
        print('   排名分布:', dict(sorted(Counter(r['pos'] for r in miss).items())), '| 有非零分数:', sum(1 for r in miss if r['in_scored']))
        rows = provider_rows(prov, DEFAULT_T)
        n = len(rows)
        print(f"\n{prov}: n={n} | 真实∈E {sum(x['inE'] for x in rows)} | 仅邻居 {sum((not x['inE']) and x['inC'] for x in rows)} | 候选集外 {sum(not x['inC'] for x in rows)} | 平均|E| {sum(len(x['E']) for x in rows) / n:.2f} 平均|C| {sum(len(x['C']) for x in rows) / n:.2f}")
        print('  |C|分布', dict(sorted(Counter(len(x['C']) for x in rows).items())))
        for r in sweep(prov):
            print(f"  t={r['t']:>2}: |C|={r['size']:.2f}/K={r['K']:.1f}  覆盖 {r['cov']}/{r['n']} (随机{100 * r['chance'] / r['n']:.0f}%)  专家全错{r['nmiss']}条中覆盖 {r['cov_miss']} (随机{100 * r['chance_miss'] / r['nmiss']:.0f}%)")


if __name__ == '__main__':
    main()
