"""Build docs/v5-results-details.html (the full, detailed version of the v5 results; the short page is scripts/build_v5_results_page.py): summary of the v5 disagreement-branch runs (A, B0, B1, D) against Direct, v4 and v3-free baselines.

Reads metrics/reflect_debate_v5_{gemini,gpt}.json (copied from the server) and the numbers recorded in metrics/findings_log.md
(F6 Direct / v4 disagreement counts, F8 v5 summary). Static HTML, no scripts, no model calls.
Usage: python scripts/build_v5_results_details.py
"""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = {p: json.loads((ROOT / f'metrics/reflect_debate_v5_{p}.json').read_text(encoding='utf8')) for p in ['gemini', 'gpt']}
RR = json.loads((ROOT / 'metrics/direct_rerun_117.json').read_text(encoding='utf8'))
N = {'gemini': 62, 'gpt': 55}
ALL = 400
M = ['A', 'B0', 'B1', 'D']
NAME = {'A': 'A 匿名化辩论', 'B0': 'B0 轨迹记分（零调用）', 'B1': 'B1 反从众批判 + 记分', 'D': 'D 候选取证控制器'}
# Baselines (from findings_log F6 / F8 and the saved json)
BASE_BRANCH = {'gemini': {'随机选（期望）': 25.6, 'v4 辩论': 26, 'Direct': 38, '候选集上限': 58},
               'gpt': {'随机选（期望）': 22.8, 'v4 辩论': 19, 'Direct': 26, '候选集上限': 49}}
BASE_ALL = {'gemini': {'v4': 307, 'Direct': 311, '一致用 v4 + 不一致用 Direct': 319, '候选集上限（完美选择）': 339},
            'gpt': {'v4': 300, 'Direct': 294, '一致用 v4 + 不一致用 Direct': 307, '候选集上限（完美选择）': 330}}
CONS_V4 = 281  # consensus-branch correct count for both models (400-sample split: 281 of 338 / 345 respectively as recorded)
CONS_N = {'gemini': 338, 'gpt': 345}


def c(p, m, key):
    return D[p][m]['counts'].get(key, 0)


def pct(a, b):
    return f'{100 * a / b:.1f}%' if b else '—'


def bar(v, mx, color):
    w = 0 if mx == 0 else 100 * v / mx
    return f'<div class="bar" style="width:{w:.1f}%;background:{color}"></div>'


css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1180px;margin:24px auto;padding:0 18px;color:#222;background:#fafafa}
h1{font-size:25px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:18px 0 6px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 18px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:5px 8px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}.muted{color:#666}.small{font-size:13px}
.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}
.bar{height:12px;border-radius:2px;display:inline-block;vertical-align:middle;margin-right:6px}.barw{width:260px;display:inline-block}
.best{font-weight:700;background:#e6ffed}.bad{color:#b33}.good{color:#2a7a2a}'''

P = []
P.append('<h1>v5 结果汇总（详细版）：不一致分支的各种方法</h1><p class="small"><a href="v5-results.html">← 返回精简版</a></p>')
P.append('<p class="muted">数据：Gemini 62 条、GPT 55 条的 v4 不一致样本（三位专家没有恰好一个共同标签），以及它们对应的 Direct。一致分支（约 85%）沿用 v4，不变。'
         '计数来自 <code>metrics/reflect_debate_v5_{gemini,gpt}.json</code>，并与 <code>metrics/findings_log.md</code> F6、F8、F9 一致。'
         '<b>所有 v5 结果都是一次运行，开发复用数据（验证集）+ 按模型正确性筛选的训练集，只能作参考，不能作为最终结论。</b></p>')

# ---------------------------------------------------------------- 1 summary
P.append('<section class="panel"><h2>一、结论</h2><ul>'
         '<li><b>四种方法都没有超过 Direct。</b>不一致分支合计：Direct 64/117，四种 v5 方法都在 45–51 之间。</li>'
         '<li><b>四种方法只比 v4 略好或持平</b>（v4 合计 45/117）：D 最高 51，B0 与 B1 为 50，A 最低 45。</li>'
         '<li><b>整体 400 条（一致分支用 v4、不一致分支用各方法）：</b>Gemini 最好的是 B1 和 D 并列（310），GPT 最好的是 B0（304）。两个模型都低于“不一致分支用 Direct”（Gemini 319、GPT 307）。</li>'
         '<li><b>A 匿名化没有减少从众：</b>Gemini 第 1 轮从众率 0.39→0.37，GPT 反而 0.24→0.35；A 在 GPT 上比 v4 还少 1 条。</li>'
         '<li><b>D 的净收益最大但有代价：</b>相对 v4 改对 10、改错 7（Gemini 不一致分支）；GPT 上 17/55 条控制器“不确定”回退到 Direct。</li></ul>'
         '<p class="small muted">选择规则上，“一致用 v4、不一致用 Direct”（Gemini 319、GPT 307）是目前最好的组合，但它是看到结果后选出的，需要新样本确认。</p></section>')

# ---------------------------------------------------------------- 2 branch table
P.append('<section class="panel"><h2>二、不一致分支答对数（Gemini 62 条 / GPT 55 条）</h2>')
for p in ['gemini', 'gpt']:
    P.append(f'<h3>{"Gemini" if p == "gemini" else "GPT"}（{N[p]} 条）</h3><table><tr><th>方法</th><th class="n">答对</th><th>占比</th><th>柱状图</th><th class="n">相对 Direct 改对</th><th class="n">相对 Direct 改错</th><th class="n">相对 v4 改对</th><th class="n">相对 v4 改错</th></tr>')
    rr = RR[p]
    rr_ok = sum(x['run2'] == x['gold'] for x in rr)
    rr_fix_v4 = sum(x['run2'] == x['gold'] and x['v4'] != x['gold'] for x in rr)
    rr_brk_v4 = sum(x['v4'] == x['gold'] and x['run2'] != x['gold'] for x in rr)
    rows = [(k, v) for k, v in BASE_BRANCH[p].items()] + [(NAME[m], c(p, m, 'all ok')) for m in M] + [('Direct（重跑）', rr_ok)]
    mx = N[p]
    best = max(v for k, v in rows if k in [NAME[m] for m in M])
    for k, v in rows:
        is_m = k in [NAME[m] for m in M]
        m_key = [m for m in M if NAME[m] == k][0] if is_m else None
        cls = ' class="best"' if is_m and v == best else ''
        if is_m:
            fd, bd, fv, bv = c(p, m_key, 'fix_vs_direct'), c(p, m_key, 'break_vs_direct'), c(p, m_key, 'fix_vs_v4'), c(p, m_key, 'break_vs_v4')
            extra = f'<td class="n">{fd}</td><td class="n">{bd}</td><td class="n">{fv}</td><td class="n">{bv}</td>'
        elif k == 'Direct（重跑）':
            fd = sum(x['run2'] == x['gold'] and x['run1'] != x['gold'] for x in rr)
            bd = sum(x['run1'] == x['gold'] and x['run2'] != x['gold'] for x in rr)
            extra = f'<td class="n">{fd}</td><td class="n">{bd}</td><td class="n">{rr_fix_v4}</td><td class="n">{rr_brk_v4}</td>'
        else:
            extra = '<td colspan="4" class="muted">—</td>'
        color = '#4a7' if k == 'Direct' else '#9ab' if k == 'v4 辩论' else '#bbb' if '随机' in k else '#d9a' if '上限' in k else '#f0b86e'
        P.append(f'<tr{cls}><td>{e(k)}</td><td class="n">{v:g}</td><td>{pct(v, mx)}</td><td><div class="barw">{bar(v, mx, color)}</div></td>{extra}</tr>')
    P.append('</table>')
P.append('<p class="small muted">“Direct（重跑）”行：“相对 Direct 改对 / 改错”是重跑相对第一次 Direct 的逐条翻转（即 Direct 自身的噪声），“相对 v4”是重跑相对 v4 的逐条比较。'
         '“改对 / 改错”是相对 Direct（或相对 v4）逐条比较。Direct 本身重跑时有 24–29% 的答案不同（见 F9），逐条翻转包含这部分噪声，但合计差距 13–19 条超过重跑的 ±2。</p></section>')

# ---------------------------------------------------------------- 3 all-400 table
P.append('<section class="panel"><h2>三、整体 400 条（一致分支用 v4 + 不一致分支换成各方法）</h2>')
P.append('<table><tr><th>方法</th><th class="n">Gemini</th><th class="n">占比</th><th class="n">GPT</th><th class="n">占比</th></tr>')
rows = []
for k in BASE_ALL['gemini']:
    rows.append((k, BASE_ALL['gemini'][k], BASE_ALL['gpt'][k]))
for m in M:
    rows.append((NAME[m], CONS_V4 + c('gemini', m, 'all ok'), CONS_V4 + c('gpt', m, 'all ok')))
gbest = max(r[1] for r in rows if any(NAME[m] == r[0] for m in M))
gpt_best = max(r[2] for r in rows if any(NAME[m] == r[0] for m in M))
_E = {p: json.loads((ROOT / f'metrics/single_agent_relook_v5e_{p}.json').read_text(encoding='utf8'))['counts']['final ok'] for p in ['gemini', 'gpt']}
rows.append(('E 单 agent 先答、拿不准再回看', CONS_V4 + _E['gemini'], CONS_V4 + _E['gpt']))
rows.insert(1, ('原 PPCT', 295, None))
for k, g, t in rows:
    is_m = any(NAME[m] == k for m in M)
    gc = ' class="best"' if is_m and g == gbest else ''
    tc = ' class="best"' if is_m and t == gpt_best else ''
    if t is None:
        tcell = '<td class="n muted" colspan="2">GPT 原 PPCT 只在验证集 80 条上跑过（62/80 = 77.5%），训练集未跑，无 400 条数字</td>' if k == '原 PPCT' else '<td class="n">—</td><td class="n">—</td>'
    else:
        tcell = f'<td class="n"{tc}>{t}</td><td class="n">{pct(t, ALL)}</td>'
    P.append(f'<tr><td>{e(k)}</td><td class="n"{gc}>{g}</td><td class="n">{pct(g, ALL)}</td>{tcell}</tr>')
P.append('</table><p class="small muted">v5 行的一致分支答对数：Gemini 与 GPT 的 v4 一致分支分别是 281 条（来自 F8 的计算：307 − 26 = 281；300 − 19 = 281）。'
         '“候选集上限”假设不一致分支里候选内的样本全部选对，只是参考上限。</p></section>')

# ---------------------------------------------------------------- 4 diagnostics
P.append('<section class="panel"><h2>四、从众率与坚持率（第 1 轮，与 v4 同样定义）</h2>'
         '<table><tr><th>模型</th><th>版本</th><th class="n">样本数</th><th class="n">从众率（改成同伴上一轮的答案）</th><th class="n">坚持率（保持自己的答案）</th></tr>')
for p in ['gemini', 'gpt']:
    for name, key in [('v4 辩论', 'v4'), ('A 匿名化', 'A')]:
        g = D[p]['diagnostics_round1'][key]
        P.append(f'<tr><td>{"Gemini" if p == "gemini" else "GPT"}</td><td>{name}</td><td class="n">{g["n"]}</td><td class="n">{g["conformity"]:.3f}</td><td class="n">{g["obstinacy"]:.3f}</td></tr>')
P.append('</table><p class="small muted">从众率下降不明显（Gemini）或上升（GPT）。A 的匿名化没有起到去除“多数拉力”的作用。这两个指标是我们自己的定义，与 Identity Bias 论文的精确定义未核对。</p></section>')

# ---------------------------------------------------------------- 5 routes
P.append('<section class="panel"><h2>五、路由与回退</h2><table><tr><th>方法</th><th>Gemini</th><th>GPT</th></tr>')
P.append(f'<tr><td>A</td><td>一致 {c("gemini","A","route consensus")}，汇总器 {c("gemini","A","route summary")}</td><td>一致 {c("gpt","A","route consensus")}，汇总器 {c("gpt","A","route summary")}</td></tr>')
P.append(f'<tr><td>B0</td><td>唯一最高分 {c("gemini","B0","route unique")}</td><td>唯一最高分 {c("gpt","B0","route unique")}</td></tr>')
P.append(f'<tr><td>B1</td><td>唯一最高分 {c("gemini","B1","route unique")}，平局用 Direct {c("gemini","B1","route tie_direct")}</td><td>唯一最高分 {c("gpt","B1","route unique")}</td></tr>')
P.append(f'<tr><td>D</td><td>控制器给出标签 {c("gemini","D","route controller")}，“不确定”回退 0</td><td>控制器给出标签 {c("gpt","D","route controller")}，“不确定”回退到 Direct {c("gpt","D","route unsure_direct")}</td></tr>')
P.append('</table><p class="small muted">D 在 GPT 上有 17/55 回退到 Direct，所以它的成绩有一部分来自 Direct 本身。</p></section>')

# ---------------------------------------------------------------- 6 by dataset
P.append('<section class="panel"><h2>六、按数据集（不一致分支）</h2><table><tr><th>模型</th><th>数据集</th><th class="n">样本</th><th class="n">Direct</th><th class="n">v4</th><th class="n">A</th><th class="n">B0</th><th class="n">B1</th><th class="n">D</th></tr>')
for p in ['gemini', 'gpt']:
    for ds in ['MER2024', 'MELD']:
        P.append(f'<tr><td>{"Gemini" if p == "gemini" else "GPT"}</td><td>{ds}</td><td class="n">{c(p,"A",ds + " n")}</td><td class="n">{c(p,"A",ds + " direct")}</td><td class="n">{c(p,"A",ds + " v4")}</td>'
                 + ''.join(f'<td class="n">{c(p, m, ds + " ok")}</td>' for m in M) + '</tr>')
P.append('</table><p class="small muted">Gemini 的 MELD 不一致样本（36 条）上 Direct 答对 23，所有 v5 方法都低于它（最高 D 的 18）；Gemini 的 MER2024 上 A、B0、B1、D 均不高于 Direct（15）。GPT 的 MER2024 上 D（10）高于 Direct（7），但样本只有 23 条。</p></section>')

# ---------------------------------------------------------------- 6b Direct re-run
P.append('<section class="panel"><h2>六之二、Direct 重跑与噪声（117 条不一致样本）</h2>'
         '<p class="small muted">同一套 Direct 流程重跑一次，原结果不改（<code>metrics/direct_rerun_117.json</code>，由 <code>scripts/export_rerun.py</code> 导出）。'
         '只重跑了不一致样本，没有重跑全部 400 条。</p>'
         '<table><tr><th>模型</th><th class="n">样本</th><th class="n">第一次答对</th><th class="n">重跑答对</th><th class="n">两次答案不同</th><th class="n">错→对</th><th class="n">对→错</th><th class="n">两次都对</th><th class="n">至少一次对</th></tr>')
for p in ['gemini', 'gpt']:
    r = RR[p]
    one = sum(x['run1'] == x['gold'] for x in r)
    two = sum(x['run2'] == x['gold'] for x in r)
    diff = sum(x['run1'] != x['run2'] for x in r)
    w2r = sum(x['run1'] != x['gold'] and x['run2'] == x['gold'] for x in r)
    r2w = sum(x['run1'] == x['gold'] and x['run2'] != x['gold'] for x in r)
    both = sum(x['run1'] == x['gold'] and x['run2'] == x['gold'] for x in r)
    any_ = sum(x['run1'] == x['gold'] or x['run2'] == x['gold'] for x in r)
    P.append(f'<tr><td>{"Gemini" if p == "gemini" else "GPT"}</td><td class="n">{len(r)}</td><td class="n">{one}</td><td class="n">{two}</td>'
             f'<td class="n">{diff}（{pct(diff, len(r))}）</td><td class="n">{w2r}</td><td class="n">{r2w}</td><td class="n">{both}</td><td class="n">{any_}</td></tr>')
P.append('</table>'
         '<p class="small muted">结论：两次运行的总答对数相差 1–2 条，但逐条答案有 24%–29% 不同。<b>（更正：补跑到 5 次后，Gemini 单次答对数在 33–39 之间，极差 6 条，“相差 1–2 条”低估了噪声，见六之五。）</b>'
         '所以 v5 各方法相对 Direct 的逐条“改对 / 改错”里有一部分是噪声；但 Direct 与 v5 合计 13–19 条的差距远大于两次之间的 1–2 条差，这个差距是稳定的。'
         '“一次跑的 Direct”作为对照是可接受的，但对照表需要注明它是单次结果。</p></section>')

# ---------------------------------------------------------------- 6c majority votes
VT = json.loads((ROOT / 'metrics/vote_disagree_117.json').read_text(encoding='utf8'))
P.append('<section class="panel"><h2>六之三、不一致分支的多数投票 vs Direct（117 条）</h2>'
         '<p class="small muted">投票只用已保存的输出，不调用模型。平局时若 Direct 第一次的答案在平局里则取它，否则取字母序靠前者（<code>scripts/vote_disagree.py</code>，<code>metrics/vote_disagree_117.json</code>）。</p>'
         '<table><tr><th>投票方式</th><th class="n">Gemini 答对（62）</th><th class="n">GPT 答对（55）</th><th class="n">合计（117）</th><th class="n">Gemini 平局数</th><th class="n">GPT 平局数</th></tr>')


def cnt(p, k):
    return sum(x[k] == x['gold'] for x in VT[p])


def ties(p, k):
    return sum(x['ties'][k] for x in VT[p])


rows_v = [('Direct 第一次（参照）', lambda p: cnt(p, 'direct1'), None),
          ('Direct 重跑（参照）', lambda p: cnt(p, 'direct2'), None),
          ('V1：三位专家反思后的多数（纯专家）', lambda p: cnt(p, 'v1'), 'v1'),
          ('V3：三位专家第 0 轮的多数（纯专家）', lambda p: cnt(p, 'v3'), 'v3'),
          ('V2：三位专家反思 + 两次 Direct 的 5 票多数', lambda p: cnt(p, 'v2'), 'v2'),
          ('V4：三位专家第 0 轮 + 两次 Direct 的 5 票多数', lambda p: cnt(p, 'v4'), 'v4')]
for name, f, key in rows_v:
    g, t = f('gemini'), f('gpt')
    gt = ties('gemini', key) if key else ''
    tt = ties('gpt', key) if key else ''
    P.append(f'<tr><td>{e(name)}</td><td class="n">{g}（{pct(g, 62)}）</td><td class="n">{t}（{pct(t, 55)}）</td><td class="n">{g + t}（{pct(g + t, 117)}）</td><td class="n">{gt}</td><td class="n">{tt}</td></tr>')
P.append('</table>'
         '<p class="small muted"><b>怎么读</b>：纯专家的多数投票（V1、V3）比 Direct 低；把两次 Direct 也放进投票（V2、V4）后，略高于单次 Direct（Gemini 39–40 对 38，GPT 28–29 对 26），但投票里有 2/5 的票就是 Direct 本身，所以这个略高不能说明“投票比 Direct 更好”，只能说明加入专家意见后没有明显损害。'
         '平局较多（Gemini V1 7 个、V4 4 个），平局规则会影响结果。这些差距（1–5 条）都在 Direct 自身的噪声（两次之间 1–2 条差、逐条翻转 7–13 条）范围内，不能下定论。</p></section>')

# ---------------------------------------------------------------- 6e direct votes experiment
DV = json.loads((ROOT / 'metrics/direct_vote_experiment.json').read_text(encoding='utf8'))['summary']
P.append('<section class="panel"><h2>六之五、Direct 多次独立运行后投票，是否比单次 Direct 好（重新做的实验）</h2>'
         '<p class="small muted">设计：每条不一致样本共有 5 次独立的 Direct 运行（第 1 次 = 原结果，第 2 次 = 重跑，第 3–5 次 = 本次新跑的 <code>direct_vote1–3</code>；同一流程、温度 0、全部成功）。'
         '单次准确率取 5 次的均值；三次投票有两种算法：只用新跑的三次，以及对 5 次中全部 10 种三次组合取平均；另有 5 次全部投票。平局取该组第一次运行的答案（也算了字母序作敏感性检查，结果几乎相同）。'
         '数据 <code>metrics/direct_vote_experiment.json</code>，计算 <code>scripts/analyze_direct_votes.py</code>，没有调用被测模型之外的任何东西。</p>'
         '<table><tr><th>模型（样本数）</th><th class="n">第 1–5 次单次答对</th><th class="n">单次均值</th><th class="n">三次投票（新跑三次）</th><th class="n">三次投票（10 种组合均值，最低–最高）</th><th class="n">五次投票</th><th class="n">五次中至少一次对</th><th class="n">五次都对</th></tr>')
for p, name in [('gemini', 'Gemini'), ('gpt', 'GPT')]:
    r = DV[p]
    tr = r['vote3_all_triples_first']
    P.append(f'<tr><td>{name}（{r["n"]}）</td><td class="n">{" / ".join(str(x) for x in r["single"])}</td><td class="n">{r["single_mean"]:.1f}（{pct(r["single_mean"], r["n"])}）</td>'
             f'<td class="n">{r["vote3_fresh_first"]}（{pct(r["vote3_fresh_first"], r["n"])}）</td><td class="n">{r["vote3_all_triples_mean_first"]:.1f}（{min(tr)}–{max(tr)}）</td>'
             f'<td class="n">{r["vote5_first"]}（{pct(r["vote5_first"], r["n"])}）</td><td class="n">{r["any_correct_of_5"]}</td><td class="n">{r["all_correct_of_5"]}</td></tr>')
tot_single = sum(DV[p]['single_mean'] for p in DV)
tot_v3 = sum(DV[p]['vote3_all_triples_mean_first'] for p in DV)
tot_v5 = sum(DV[p]['vote5_first'] for p in DV)
P.append(f'<tr><td><b>合计（117）</b></td><td class="n">—</td><td class="n"><b>{tot_single:.1f}</b>（{pct(tot_single, 117)}）</td><td class="n">—</td><td class="n"><b>{tot_v3:.1f}</b>（{pct(tot_v3, 117)}）</td><td class="n"><b>{tot_v5}</b>（{pct(tot_v5, 117)}）</td><td class="n">{sum(DV[p]["any_correct_of_5"] for p in DV)}</td><td class="n">{sum(DV[p]["all_correct_of_5"] for p in DV)}</td></tr></table>')
P.append('<table><tr><th>模型</th><th>数据集</th><th class="n">样本</th><th class="n">单次均值</th><th class="n">三次投票（新跑三次）</th><th class="n">五次投票</th></tr>')
for p, name in [('gemini', 'Gemini'), ('gpt', 'GPT')]:
    for ds in ('MER2024', 'MELD'):
        d = DV[p]['by_dataset'][ds]
        P.append(f'<tr><td>{name}</td><td>{ds}</td><td class="n">{d["n"]}</td><td class="n">{d["single_mean"]:.1f}</td><td class="n">{d["vote3_fresh"]}</td><td class="n">{d["vote5"]}</td></tr>')
P.append('</table>'
         '<div class="note"><b>结论</b>：<ul>'
         '<li><b>三次投票没有稳定地好于单次 Direct。</b>Gemini：单次均值 36.6，三次投票的 10 种组合均值 38.0（+1.4 条，约 +2 个百分点），五次投票 38；GPT：单次均值 23.8，三次投票均值 23.8（持平），五次投票 23。合计 60.4 → 61.8（三次）/ 61（五次），提升约 1 条，在噪声范围内。</li>'
         '<li><b>噪声比我之前说的大。</b>Gemini 的 5 次单次答对数是 38 / 39 / 35 / 38 / 33，极差 6 条；三次投票的 10 种组合从 33 到 41，极差 8 条。之前只用两次（38、39）估计“±1–2 条”偏乐观；而且<b>此前对照用的“Direct 38 / 26”恰好是较高的一次抽样</b>（均值 36.6 / 23.8）。</li>'
         '<li><b>只用新跑的三次投票反而是 33（Gemini）</b>，低于任何一次单次的平均值，这是三次组合里最差的一组，说明“三次投票”的结果本身就会因抽到哪三次而差 8 条。</li>'
         '<li>上限仍然很宽：五次中至少一次答对的有 87/117，但五次都对的只有 33/117；Gemini 29/62、GPT 25/55 的样本五次答案完全一致，其中仍有 8 条和 13 条是一致地错（Gemini 29−21，GPT 25−12）。多次采样改变不了这类系统性错误。</li>'
         '<li>对 v5 的含义：v5 各方法（合计 45–51）仍明显低于 Direct 的均值（60.4），这个差距在噪声之外，结论不变；但“Direct 比某个 v5 方法多 1–3 条”这类小差距不能解读。</li></ul></div></section>')

# ---------------------------------------------------------------- 6f single agent re-look (v5-E)
EE = {p: json.loads((ROOT / f'metrics/single_agent_relook_v5e_{p}.json').read_text(encoding='utf8')) for p in ['gemini', 'gpt']}


def ec(p, k):
    return EE[p]['counts'].get(k, 0)


def efl(p, key):  # flips of the final answer vs Direct run 1
    ps = EE[p]['per_sample']
    if key == 'fix':
        return sum(x['final'] == x['gold'] and x['direct_runs'][0] != x['gold'] for x in ps)
    return sum(x['final'] != x['gold'] and x['direct_runs'][0] == x['gold'] for x in ps)


P.append('<section class="panel"><h2>六之六、v5-E 单 agent 先答、拿不准再回看（已运行，117 条）</h2>'
         '<p class="small muted">设计见 <code>docs/v5-orchestra.html</code>：一个全模态 agent 在候选集内作答并自己写不确定点；有不确定点才按它指定的时间窗取 16 帧（Gemini 另带该段音轨）回看，再反思，改答案必须引用回看的新证据。'
         '不使用任何专家输出、图谱和组织文本。数据 <code>metrics/single_agent_relook_v5e_{gemini,gpt}.json</code>。每个设置只跑一次。</p>'
         '<table><tr><th>指标</th><th class="n">Gemini（62）</th><th class="n">GPT（55）</th><th class="n">合计（117）</th></tr>')
rows_e = [('Direct（5 次均值）', 36.6, 23.8), ('Direct 三次投票（10 种组合均值）', 38.0, 23.8), ('v5-D（此前最好的 v5 方法）', 29, 22),
          ('E 首次作答', ec('gemini', 'first ok'), ec('gpt', 'first ok')), ('E 回看后最终答案', ec('gemini', 'final ok'), ec('gpt', 'final ok'))]
for name, g, t_ in rows_e:
    b_ = ' class="best"' if name.startswith('E 回看') else ''
    P.append(f'<tr{b_}><td>{e(name)}</td><td class="n">{g:g}（{pct(g, 62)}）</td><td class="n">{t_:g}（{pct(t_, 55)}）</td><td class="n">{g + t_:g}（{pct(g + t_, 117)}）</td></tr>')
P.append('</table>')
P.append('<table><tr><th>回看相关统计</th><th class="n">Gemini</th><th class="n">GPT</th></tr>')
stats = [('首次作答自己写了不确定点的样本', lambda p: f'{ec(p, "flagged")}/{ec(p, "n")}（{pct(ec(p, "flagged"), ec(p, "n"))}）'),
         ('其中首次作答答对', lambda p: f'{ec(p, "flagged & first ok")}/{ec(p, "flagged")}'),
         ('没写不确定点的样本里首次作答答对', lambda p: f'{ec(p, "unflagged & first ok")}/{ec(p, "unflagged")}（{pct(ec(p, "unflagged & first ok"), ec(p, "unflagged"))}）'),
         ('回看后的“对不确定点的回答”：是 / 否 / 不确定', lambda p: f'{ec(p, "point yes")} / {ec(p, "point no")} / {ec(p, "point unsure")}'),
         ('反思后改了答案（REVISE）', lambda p: str(ec(p, 'revise'))),
         ('其中 错→对 / 对→错 / 错→错', lambda p: f'{ec(p, "revise wrong->right")} / {ec(p, "revise right->wrong")} / {ec(p, "revise wrong->wrong")}'),
         ('最终答案相对 Direct 第一次：改对 / 改错', lambda p: f'{efl(p, "fix")} / {efl(p, "break")}'),
         ('答错的样本里：被标了不确定点 / 没标', lambda p: f'{ec(p, "flagged") - ec(p, "flagged & first ok")} / {ec(p, "unflagged") - ec(p, "unflagged & first ok")}')]
for name, f in stats:
    P.append(f'<tr><td>{e(name)}</td><td class="n">{f("gemini")}</td><td class="n">{f("gpt")}</td></tr>')
P.append('</table>'
         '<div class="note"><b>结论</b><ul>'
         '<li><b>合计 63/117，是所有 v5 方法里最高的</b>（v5-D 51、B0 50），也比 Direct 5 次均值（60.4）和三次投票均值（61.8）多 2.6 和 1.2 条。但<b>没有达到事先约定的标准</b>（比 Direct 均值多至少 4 条）；而且 Direct 自己单次波动有 6 条、三次投票组合差 8 条，这个差距在噪声范围内。</li>'
         '<li><b>绝大多数提升来自“首次作答”本身，不是回看。</b>首次作答合计 61，已经和 Direct 持平（候选集内作答 + 易混边界 + 证据，没有明显增益）。回看只让 GPT 的 2 条错→对，Gemini 一条都没改。</li>'
         '<li><b>agent 很少写不确定点</b>：Gemini 7/62（11%）、GPT 6/55（11%）。<b>答错的样本绝大多数没被标记</b>（Gemini 23 条错里 20 条没标，GPT 33 条错里 28 条没标），也就是“自信地错”，回看够不到。</li>'
         '<li><b>“不确定”标记的可靠程度因模型而异</b>：GPT 被标记的 6 条里只有 1 条首答答对（17%），没标的 43%——标记有用；Gemini 被标记的 7 条里 4 条答对（57%），没标的 64%——几乎没区别。样本太少，只能作线索。</li>'
         '<li><b>回看改答案时很谨慎</b>：回看后的回答 Gemini 7 条里 6 条是“否”（疑虑被排除，保持首答），GPT 改了 2 条且都改对，没有一条改错。</li>'
         '<li>下一步要看的是触发方式：只靠 agent 自述，回看只触及约 11% 的样本。设计里的对照（对全部样本回看，或用“多次首答不一致”触发，对 Gemini 有数据支持）还没有跑。</li></ul></div></section>')

# ---------------------------------------------------------------- 6d accuracy by branch
BA = json.loads((ROOT / 'metrics/branch_acc.json').read_text(encoding='utf8'))
P.append('<section class="panel"><h2>六之四、各专家、投票与 Direct 在一致 / 不一致分支上的准确率</h2>'
         '<p class="small muted">一致分支：三位专家的共同标签（即 v4 直接输出）；不一致分支：三位专家反思后主答案的多数投票（平局时取 Direct 第一次的答案，否则字母序）。'
         '“反思”指反思后的主答案。数据来自 <code>scripts/branch_acc.py</code>，<code>metrics/branch_acc.json</code>，不调用模型。</p>')
ROWS = [('图谱专家（第 0 轮）', 'R0 图谱专家'), ('图谱专家（反思后）', '反思 图谱专家'),
        ('音频字幕专家（第 0 轮）', 'R0 音频字幕专家'), ('音频字幕专家（反思后）', '反思 音频字幕专家'),
        ('图像专家（第 0 轮）', 'R0 图像专家'), ('图像专家（反思后）', '反思 图像专家'),
        ('多数投票（一致分支 = 共同标签；不一致分支 = 反思后多数）', '多数投票'),
        ('Direct 第一次', 'Direct 第一次'),
        ('v4 最终输出', 'v4 最终')]


def acc_cell(a, n):
    return f'{a}/{n}（{pct(a, n)}）' if n else '—'


P.append('<table><tr><th>方法</th><th class="n">Gemini 一致（338）</th><th class="n">Gemini 不一致（62）</th><th class="n">GPT 一致（345）</th><th class="n">GPT 不一致（55）</th></tr>')
for name, key in ROWS:
    cells = []
    for p in ['gemini', 'gpt']:
        for br in ['consensus', 'disagree']:
            d = BA[p][br]
            cells.append(acc_cell(d.get(key, 0), d['n']))
    P.append(f'<tr><td>{e(name)}</td>' + ''.join(f'<td class="n">{x}</td>' for x in cells) + '</tr>')
# voting that includes the two Direct runs (5 votes) - disagreement branch only
VT5 = json.loads((ROOT / 'metrics/vote_disagree_117.json').read_text(encoding='utf8'))
v5cells = ['—']
v5cells.append(acc_cell(sum(x['v2'] == x['gold'] for x in VT5['gemini']), len(VT5['gemini'])))
v5cells.append('—')
v5cells.append(acc_cell(sum(x['v2'] == x['gold'] for x in VT5['gpt']), len(VT5['gpt'])))
P.append('<tr><td>多数投票，含两次 Direct（5 票：3 位反思后专家 + 2 次 Direct）</td>' + ''.join(f'<td class="n">{x}</td>' for x in v5cells) + '</tr>')
# Direct re-run row: only the disagreement branch exists
rr = []
for p in ['gemini', 'gpt']:
    rr.append('—')
    d = BA[p]['disagree']
    rr.append(acc_cell(d['Direct 重跑'], d['Direct 重跑样本数']))
P.append('<tr><td>Direct 重跑</td>' + ''.join(f'<td class="n">{x}</td>' for x in rr) + '</tr>')
P.append('</table><p class="small muted">注意：一致分支上“多数投票”与 v4 最终输出相同（都是共同标签）。不一致分支上，三位专家各自的准确率只有 17–32/55–62，而 Direct 在 Gemini 上是 38/62（39/62 重跑）、GPT 上是 26/55（24/55 重跑）。'
         'Direct 在一致分支的准确率 Gemini 为 273/338（80.8%），低于专家共同标签的 281/338（83.1%）；GPT 为 268/345（77.7%），低于 281/345（81.4%）。'
         'Direct 重跑只在不一致样本上有，一致分支上的 Direct 重跑没有数据。</p></section>')

# ---------------------------------------------------------------- 7 caveats
P.append('<section class="panel"><h2>七、注意事项</h2><ul>'
         '<li>每个方法只跑了一次；Direct 自己的重跑在 117 条上有 13–18 条答案不同（F9）；5 次独立运行的单次答对数极差 6 条（Gemini 33–39，GPT 20–26），第一次 Direct（38 / 26）是较高的一次抽样（见六之五）。</li>'
         '<li>样本是按模型正确性筛选的，验证集为开发复用数据；训练集按筛选后的正确性分布，不能代表真实分布。</li>'
         '<li>排名中的“最好”只差 1–6 条，不足以说明哪个方法真的更好。</li>'
         '<li>本页的所有 v5 设计、提示词与流程图见 <code>docs/v5-methods.html</code>；v4 不一致分支的分析见 <code>docs/v4-80-debate-analysis.html</code>。</li></ul></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>v5 结果汇总（详细版）</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v5-results-details.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
