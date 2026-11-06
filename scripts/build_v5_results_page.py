"""Build docs/v5-results.html: the short v5 results page = one table (disagreement-branch correct counts) + a few conclusions.
Everything else (conformity, routes, by dataset, Direct re-run, votes, per-branch accuracy, whole-400 table) lives in the detailed page
docs/v5-results-details.html (scripts/build_v5_results_details.py). Reads metrics/*.json only. Static HTML, no scripts, no model calls.
Usage: python scripts/build_v5_results_page.py
"""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rd = lambda name: json.loads((ROOT / 'metrics' / name).read_text(encoding='utf8'))
V5 = {p: rd(f'reflect_debate_v5_{p}.json') for p in ['gemini', 'gpt']}
E = {p: rd(f'single_agent_relook_v5e_{p}.json')['counts'] for p in ['gemini', 'gpt']}
DV = rd('direct_vote_experiment.json')['summary']
N = {'gemini': 62, 'gpt': 55}

rows = [
    ('参照', None, None),
    ('随机选（候选里随机挑一个的期望）', 25.6, 22.8),
    ('v4 辩论（原流程）', 26, 19),
    ('Direct（5 次独立运行的均值）', DV['gemini']['single_mean'], DV['gpt']['single_mean']),
    ('Direct 三次投票（10 种组合均值）', DV['gemini']['vote3_all_triples_mean_first'], DV['gpt']['vote3_all_triples_mean_first']),
    ('候选集上限（完美选择）', 58, 49),
    ('v5 方法', None, None),
    ('A 匿名化辩论', V5['gemini']['A']['counts']['all ok'], V5['gpt']['A']['counts']['all ok']),
    ('B0 轨迹记分（零调用）', V5['gemini']['B0']['counts']['all ok'], V5['gpt']['B0']['counts']['all ok']),
    ('B1 反从众批判 + 记分', V5['gemini']['B1']['counts']['all ok'], V5['gpt']['B1']['counts']['all ok']),
    ('D 候选取证控制器', V5['gemini']['D']['counts']['all ok'], V5['gpt']['D']['counts']['all ok']),
    ('E 单 agent 先答、拿不准再回看', E['gemini']['final ok'], E['gpt']['final ok']),
]
direct_total = DV['gemini']['single_mean'] + DV['gpt']['single_mean']
v5_totals = {name: g + t for name, g, t in rows[7:]}
best = max(v5_totals.values())

css = '''body{font:16px/1.75 "Microsoft YaHei",sans-serif;max-width:900px;margin:32px auto;padding:0 20px;color:#222;background:#fff}
h1{font-size:26px;margin-bottom:4px}h2{font-size:19px;margin-top:30px}.sub{color:#666;font-size:14px;margin-top:0}
table{border-collapse:collapse;width:100%;margin:12px 0}th,td{border-bottom:1px solid #e3e3e3;padding:8px 10px;text-align:left}
th{background:#f4f6fb;border-bottom:2px solid #ccd}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.grp td{background:#fafafa;color:#888;font-size:13px;letter-spacing:.05em;border-bottom:none;padding-top:14px}
tr.best td{background:#eafaf0;font-weight:700}tr.ref td{color:#444}.pos{color:#1e7e34}.neg{color:#b02a37}
ul{padding-left:20px}li{margin:6px 0}.foot{color:#777;font-size:13px;margin-top:28px;border-top:1px solid #eee;padding-top:10px}a{color:#2456a6}'''

P = ['<h1>v5 结果</h1>',
     '<p class="sub">每个方法只跑了一次。第一张表只看三位专家没有共同标签的不一致样本（Gemini 62 条、GPT 55 条，合计 117 条）；第二张表把一致分支合并回来，看全部 400 条。</p>',
     '<h2>不一致分支答对数</h2>',
     '<table><tr><th>方法</th><th class="n">Gemini（62）</th><th class="n">GPT（55）</th><th class="n">合计（117）</th><th class="n">比 Direct 均值</th></tr>']
for name, g, t in rows:
    if g is None:
        P.append(f'<tr class="grp"><td colspan="5">{e(name)}</td></tr>')
        continue
    tot = g + t
    is_v5 = name in v5_totals
    cls = ' class="best"' if is_v5 and tot == best else (' class="ref"' if not is_v5 else '')
    diff = tot - direct_total
    dcell = '—' if name.startswith('Direct（') or name.startswith('候选集上限') else (f'<span class="{"pos" if diff > 0.05 else "neg" if diff < -0.05 else ""}">{diff:+.1f}</span>')
    P.append(f'<tr{cls}><td>{e(name)}</td><td class="n">{g:g}（{100 * g / 62:.0f}%）</td><td class="n">{t:g}（{100 * t / 55:.0f}%）</td><td class="n">{tot:g}（{100 * tot / 117:.0f}%）</td><td class="n">{dcell}</td></tr>')
P.append('</table>')

# ---- whole 400 samples = consensus branch (v4 common label) + disagreement branch (method under test)
BA = rd('branch_acc.json')
CONS = {p: BA[p]['consensus']['v4 最终'] for p in ['gemini', 'gpt']}  # 281 / 281, identical for every method below
CONS_N = {p: BA[p]['consensus']['n'] for p in ['gemini', 'gpt']}
D1 = {p: BA[p]['consensus']['Direct 第一次'] + BA[p]['disagree']['Direct 第一次'] for p in ['gemini', 'gpt']}  # Direct on all 400, first run
dis = {  # disagreement-branch correct counts by method (same numbers as the table above)
    'v4': (26, 19), 'Direct 均值': (DV['gemini']['single_mean'], DV['gpt']['single_mean']), 'Direct 第一次': (38, 26),
    'Direct 投票': (DV['gemini']['vote3_all_triples_mean_first'], DV['gpt']['vote3_all_triples_mean_first']), '上限': (58, 49),
    'A': rows[7][1:], 'B0': rows[8][1:], 'B1': rows[9][1:], 'D': rows[10][1:], 'E': rows[11][1:]}
base_g, base_t = CONS['gemini'] + dis['Direct 均值'][0], CONS['gpt'] + dis['Direct 均值'][1]
whole = [('参照', None, None),
         ('v4 原流程（一致用共同标签 + 不一致用辩论）', CONS['gemini'] + dis['v4'][0], CONS['gpt'] + dis['v4'][1]),
         ('Direct 全程（第一次运行，不分支）', D1['gemini'], D1['gpt']),
         ('一致用 v4 + 不一致用 Direct（均值）', base_g, base_t),
         ('一致用 v4 + 不一致用 Direct（第一次运行）', CONS['gemini'] + dis['Direct 第一次'][0], CONS['gpt'] + dis['Direct 第一次'][1]),
         ('候选集上限（不一致分支全部选对）', CONS['gemini'] + dis['上限'][0], CONS['gpt'] + dis['上限'][1]),
         ('v5 方法（一致用 v4 + 不一致用该方法）', None, None),
         ('A 匿名化辩论', CONS['gemini'] + dis['A'][0], CONS['gpt'] + dis['A'][1]),
         ('B0 轨迹记分（零调用）', CONS['gemini'] + dis['B0'][0], CONS['gpt'] + dis['B0'][1]),
         ('B1 反从众批判 + 记分', CONS['gemini'] + dis['B1'][0], CONS['gpt'] + dis['B1'][1]),
         ('D 候选取证控制器', CONS['gemini'] + dis['D'][0], CONS['gpt'] + dis['D'][1]),
         ('E 单 agent 先答、拿不准再回看', CONS['gemini'] + dis['E'][0], CONS['gpt'] + dis['E'][1])]
v5w = {n: g + t for n, g, t in whole[7:]}
bestw = max(v5w.values())
P.append('<h2>合并一致分支后：全部 400 条</h2>'
         f'<p class="sub">一致分支（Gemini {CONS_N["gemini"]} 条、GPT {CONS_N["gpt"]} 条）都用 v4 的共同标签，答对 {CONS["gemini"]} 和 {CONS["gpt"]} 条，对所有方法相同；'
         '差别只来自不一致分支（Gemini 62 条、GPT 55 条）用什么方法。“比基线”是相对“一致用 v4 + 不一致用 Direct（均值）”。</p>'
         '<table><tr><th>方法</th><th class="n">Gemini（400）</th><th class="n">GPT（400）</th><th class="n">合计（800）</th><th class="n">比基线</th></tr>')
for name, g, t in whole:
    if g is None:
        P.append(f'<tr class="grp"><td colspan="5">{e(name)}</td></tr>')
        continue
    tot = g + t
    is_v5 = name in v5w
    cls = ' class="best"' if is_v5 and tot == bestw else (' class="ref"' if not is_v5 else '')
    diff = tot - (base_g + base_t)
    dcell = '—' if name.startswith('一致用 v4 + 不一致用 Direct（均值）') or name.startswith('候选集上限') else f'<span class="{"pos" if diff > 0.05 else "neg" if diff < -0.05 else ""}">{diff:+.1f}</span>'
    P.append(f'<tr{cls}><td>{e(name)}</td><td class="n">{g:g}（{100 * g / 400:.1f}%）</td><td class="n">{t:g}（{100 * t / 400:.1f}%）</td><td class="n">{tot:g}（{100 * tot / 800:.1f}%）</td><td class="n">{dcell}</td></tr>')
P.append('</table>'
         '<p class="sub">说明：Direct 的“均值”只有不一致分支重跑过 5 次，所以基线 = 一致分支 281 + 不一致分支 Direct 5 次均值；“第一次运行”是此前一直引用的 319 / 307，它碰巧是较高的一次抽样。</p>')
P.append('<h2>结论</h2><ul>'
         f'<li><b>没有一个 v5 方法稳定地超过 Direct。</b>最高的是 E（合计 {E["gemini"]["final ok"] + E["gpt"]["final ok"]}），比 Direct 均值多 {E["gemini"]["final ok"] + E["gpt"]["final ok"] - direct_total:.1f} 条，没有达到约定的“多至少 4 条”。</li>'
         '<li><b>A、B0、B1、D 都低于 Direct</b>，只比原来的 v4 辩论略好或持平。</li>'
         '<li><b>E 的提升主要来自“首次作答”本身</b>（首答合计 61，已与 Direct 持平），回看只改对了 GPT 的 2 条。</li>'
         '<li><b>差距小于噪声</b>：Direct 自己单次运行就会差 6 条（Gemini 33–39），所以 1–3 条的差别不能解读。</li></ul>')
P.append('<p class="foot">样本是按模型正确性筛选和开发中复用的数据，只作参考。更多内容（整体 400 条、各专家与投票的分支准确率、Direct 重跑与投票、从众率、按数据集）见 <a href="v5-results-details.html">详细版</a>；方法设计见 <a href="v5-methods.html">v5-methods</a>、<a href="v5-orchestra.html">v5-orchestra</a>。</p>')
html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>v5 结果</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v5-results.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
