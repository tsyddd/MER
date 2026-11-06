"""Build docs/v6-rmad-report.html: analysis report of the R2-MAD (v6) run on the v4 disagreement branch (Gemini 62 + GPT 55).
Reads metrics/v6_rmad_analysis.json (made on the server by versions/v6/analyze.py) only. Static HTML, no scripts, no model calls.
Usage: python scripts/build_v6_rmad_report.py
"""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = json.loads((ROOT / 'metrics' / 'v6_rmad_analysis.json').read_text(encoding='utf-8'))
T, TR, M = A['test'], A['train'], A['memory']
V = ['n0', 'n1', 'n2', 'n3']
VN = {'n0': 'n0 不检索（对照）', 'n1': 'n1 每轮取 1 条经验', 'n2': 'n2 每轮取 2 条经验', 'n3': 'n3 每轮取 3 条经验'}
DMEAN = {'gemini': 36.6, 'gpt': 23.8}
V4 = {'gemini': 26, 'gpt': 19}
N = {p: T[p]['n'] for p in T}
pct = lambda a, b: f'{100 * a / b:.0f}%' if b else '—'  # noqa: E731


def c(p, v):
    return T[p]['variants'][v]['correct']


def done(p, v):
    return T[p]['variants'][v]['done']


tot = {v: c('gemini', v) + c('gpt', v) for v in V}
n0 = tot['n0']
best_v = max(V[1:], key=lambda v: tot[v])
met = {v: tot[v] - n0 >= 4 and c('gemini', v) >= DMEAN['gemini'] and c('gpt', v) >= DMEAN['gpt'] for v in V[1:]}

css = '''body{font:15px/1.75 "Microsoft YaHei",sans-serif;max-width:1080px;margin:24px auto;padding:0 18px;color:#222;background:#fafafa}
h1{font-size:26px;margin-bottom:4px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:14px 0 4px}
.sub{color:#666;font-size:14px}.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px 18px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:5px 9px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}tr.grp td{background:#f6f6f6;color:#777;font-size:13px}tr.hl td{background:#eafaf0;font-weight:700}tr.ref td{color:#444}
.pos{color:#1e7e34}.neg{color:#b02a37}.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}
.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}.bad{background:#fdecea;border-left:4px solid #c0392b;padding:8px 12px;margin:10px 0}
.small{font-size:13px}.muted{color:#666}code{background:#eee;padding:0 4px;border-radius:3px}a{color:#2456a6}'''

P = ['<h1>R²-MAD（v6）结果报告：不一致分支上的经验召回</h1>',
     '<p class="sub">2026-11-06。测试集 = 旧 400 条里 v4 判为不一致的样本（Gemini 62、GPT 55，共 117 条）。每个变体只跑一次。'
     '数据来自 <code>metrics/v6_rmad_analysis.json</code>（服务器 <code>versions/v6/analyze.py</code> 生成）。设计见 <a href="v6-selfevolve-design.html">v6-selfevolve-design</a>，项目回顾见 <a href="project-journey.html">project-journey</a>。</p>']

# ---------------------------------------------------------------- conclusion
P.append('<section class="panel"><h2>一、结论</h2><div class="bad"><ul>'
         f'<li><b>没有达到事先约定的“有提升”标准。</b>标准是：比 n0 多答对至少 4 条，且两个模型各自不低于 Direct 均值（Gemini 36.6、GPT 23.8）。'
         f'最好的是 {best_v}，合计 {tot[best_v]}，比 n0（{n0}）多 {tot[best_v] - n0} 条；两个模型都远低于 Direct 均值。</li>'
         f'<li><b>经验召回的作用在噪声范围内。</b>n1 / n2 / n3 相对 n0 的改对 / 改错：Gemini '
         + '、'.join(f"{v} {T['gemini']['flips'][v]['vs_n0_fixed']}/{T['gemini']['flips'][v]['vs_n0_broken']}" for v in V[1:])
         + '；GPT ' + '、'.join(f"{v} {T['gpt']['flips'][v]['vs_n0_fixed']}/{T['gpt']['flips'][v]['vs_n0_broken']}" for v in V[1:])
         + '。每次只改动 7–11 条样本的答案，对错大致对半。</li>'
         f'<li><b>整个辩论框架仍然约等于 v4。</b>n0（去掉反思、静态 2 轮辩论）合计 {n0}，v4 是 45，在候选里随机选的期望是 48.4；Direct 均值 60.4。'
         '去掉反思没有影响，加经验也没有改变“辩论 ≈ 随机”的格局。</li>'
         '<li>相对 Direct（第一次运行），所有变体都是改错多、改对少（见第三节）。</li></ul></div></section>')

# ---------------------------------------------------------------- core table
P.append('<section class="panel"><h2>二、核心表：不一致分支答对数</h2>'
         '<table><tr><th>方法</th><th class="n">Gemini（62）</th><th class="n">GPT（55）</th><th class="n">合计（117）</th><th class="n">比 n0</th><th class="n">比 Direct 均值</th></tr>')
rows = [('参照', None, None), ('在候选里随机选（期望）', 25.6, 22.8), ('v4 辩论（含反思）', V4['gemini'], V4['gpt']),
        ('Direct（5 次单次均值）', DMEAN['gemini'], DMEAN['gpt']), ('R²-MAD（v6）', None, None)]
rows += [(VN[v], c('gemini', v), c('gpt', v)) for v in V]
for name, g, t in rows:
    if g is None:
        P.append(f'<tr class="grp"><td colspan="6">{e(name)}</td></tr>')
        continue
    s = g + t
    is_v = name in VN.values()
    cls = ' class="hl"' if is_v and s == max(tot.values()) else (' class="ref"' if not is_v else '')
    dn0 = f'<span class="{"pos" if s - n0 > 0 else "neg" if s - n0 < 0 else ""}">{s - n0:+g}</span>' if is_v and name != VN['n0'] else '—'
    dd = s - 60.4
    gcell = f'{g:g}（{pct(g, 62)}）'
    if name == VN['n3']:
        gcell = f'{g:g}/{done("gemini", "n3")}（{pct(g, done("gemini", "n3"))}）*'
    P.append(f'<tr{cls}><td>{e(name)}</td><td class="n">{gcell}</td><td class="n">{t:g}（{pct(t, 55)}）</td><td class="n">{s:g}</td>'
             f'<td class="n">{dn0}</td><td class="n">' + ('—' if name.startswith('Direct') else f'<span class="neg">{dd:+.1f}</span>') + '</td></tr>')
P.append('</table><p class="small muted">* Gemini n3 有 1 条（MER2024/samplenew_00034724）辩论第 1 轮的音频字幕专家调用连续 6 次接口返回为空（list index out of range），没有结果，按未完成处理；该样本在 n0、n1、n2 和 Direct 都答对（angry）。'
         '若把它算作答对，n3 合计为 48，刚好比 n0 多 4 条，但两个模型仍远低于各自的 Direct 均值，所以仍未达到标准。</p>')
P.append('<h3>按数据集</h3><table><tr><th>变体</th><th class="n">Gemini MER2024</th><th class="n">Gemini MELD</th><th class="n">GPT MER2024</th><th class="n">GPT MELD</th></tr>')
for v in V:
    cells = []
    for p in ('gemini', 'gpt'):
        for ds in ('MER2024', 'MELD'):
            b = T[p]['variants'][v]['by_dataset'][ds]
            cells.append(f'{b["correct"]}/{b["n"]}')
    P.append(f'<tr><td>{VN[v]}</td>' + ''.join(f'<td class="n">{x}</td>' for x in cells) + '</tr>')
P.append('</table></section>')

# ---------------------------------------------------------------- flips & routes
P.append('<section class="panel"><h2>三、答案改动、流程走向与调用数</h2>'
         '<table><tr><th>变体</th><th>模型</th><th class="n">相对 n0 改动 / 改对 / 改错</th><th class="n">相对 Direct（第 1 次）改对 / 改错</th><th class="n">相对 v4 改对 / 改错</th>'
         '<th class="n">1 轮早停 / 2 轮</th><th class="n">进入汇总器</th><th class="n">调用数</th></tr>')
for v in V:
    for p in ('gemini', 'gpt'):
        r = T[p]['variants'][v]
        f = T[p]['flips'].get(v)
        fl = f'{f["vs_n0_changed"]} / {f["vs_n0_fixed"]} / {f["vs_n0_broken"]}' if f else '—'
        calls = r['calls'] + (T[p]['shared_state0_calls'] if v != 'n0' else 0)
        P.append(f'<tr><td>{v}</td><td>{p}</td><td class="n">{fl}</td><td class="n">{r["vs_direct1"]["fixed"]} / {r["vs_direct1"]["broken"]}</td>'
                 f'<td class="n">{r["vs_v4"]["fixed"]} / {r["vs_v4"]["broken"]}</td><td class="n">{r["rounds"].get("1", 0)} / {r["rounds"].get("2", 0)}</td>'
                 f'<td class="n">{r["routes"].get("summary", 0)}</td><td class="n">{calls}</td></tr>')
P.append('</table><ul class="small">'
         '<li>“1 轮早停”= 第 1 轮辩论后三位专家答案相同；“进入汇总器”= 两轮后仍不一致。调用数含格式修复重试，n1–n3 另含第 0 轮摘要 S0（与 n0 无关，三个变体共用一次，已计入）；不含测试集 Caption（102 次，两个模型共用）。</li>'
         '<li>加经验后 Gemini 的两轮辩论和汇总器都变多（n0 2 轮 10、汇总器 1；n1 2 轮 17、汇总器 9）：经验让专家更不容易马上一致，但这没有转化成更多答对。</li></ul></section>')

# ---------------------------------------------------------------- retrieval
P.append('<section class="panel"><h2>四、检索到了什么、专家用了没有</h2>'
         '<table><tr><th>变体</th><th>模型</th><th class="n">取回案例数</th><th class="n">案例本身答对</th><th class="n">案例标签 = 当前样本真实标签</th>'
         '<th class="n">辩论 1 答案 = 第 1 条案例标签</th><th class="n">第 1 条案例标签在当前候选内</th><th class="n">同伴可靠度 high / low / 不标</th></tr>')
for v in V[1:]:
    for p in ('gemini', 'gpt'):
        r = T[p]['variants'][v]['retrieval']
        P.append(f'<tr><td>{v}</td><td>{p}</td><td class="n">{r["cases"]}</td><td class="n">{r["cases_correct"]}（{pct(r["cases_correct"], r["cases"])}）</td>'
                 f'<td class="n">{r["cases_solution_eq_gold"]}（{pct(r["cases_solution_eq_gold"], r["cases"])}）</td>'
                 f'<td class="n">{r["d1_follow_eq"]}/{r["d1_follow_n"]}（{pct(r["d1_follow_eq"], r["d1_follow_n"])}）</td>'
                 f'<td class="n">{r["d1_sol_in_union"]}/{r["d1_follow_n"]}（{pct(r["d1_sol_in_union"], r["d1_follow_n"])}）</td>'
                 f'<td class="n">{r.get("rel_high", 0)} / {r.get("rel_low", 0)} / {r.get("rel_None", 0)}</td></tr>')
gr = T['gemini']['variants']['n1']['retrieval']
pr = T['gpt']['variants']['n1']['retrieval']
P.append('</table><div class="note"><ul>'
         f'<li><b>取回的案例大多是“答对的案例”</b>（Gemini n1 {pct(gr["cases_correct"], gr["cases"])}、GPT n1 {pct(pr["cases_correct"], pr["cases"])}），这是 MMR 设计的效果（相关性项乘以“是否答对”）。'
         f'<b>但案例的标签只有约 {pct(gr["cases_solution_eq_gold"], gr["cases"])}（Gemini）和 {pct(pr["cases_solution_eq_gold"], pr["cases"])}（GPT）等于当前样本的真实标签</b>，'
         '只比从 6–7 个标签里随便挑一个（约 15%）略高：Caption 相似并不意味着情绪相同。</li>'
         f'<li>第 1 条案例的标签只有 {pct(gr["d1_sol_in_union"], gr["d1_follow_n"])}（Gemini）和 {pct(pr["d1_sol_in_union"], pr["d1_follow_n"])}（GPT）落在当前样本的候选标签里；'
         f'专家辩论第 1 轮的答案与它相同的比例 {pct(gr["d1_follow_eq"], gr["d1_follow_n"])} 和 {pct(pr["d1_follow_eq"], pr["d1_follow_n"])}。专家没有盲目照抄案例，但案例本身也给不出方向。</li>'
         '<li>同伴可靠度 high 和 low 的数量相近，几乎每个同伴都被打了标记（只有不到 15% 不标），所以它也没有提供“该信谁”的区分度。</li></ul></div></section>')

# ---------------------------------------------------------------- training set and memory
P.append('<section class="panel"><h2>五、训练集与经验库</h2><h3>训练集怎么来的</h3>'
         '<table><tr><th>模型</th><th>数据集</th><th class="n">已处理（候选池）</th><th class="n">不一致 / 成功（比例）</th><th class="n">入选</th><th>入选样本的标签</th></tr>')
pool = {'MER2024': 969, 'MELD': 2408}
for p in ('gemini', 'gpt'):
    for ds in ('MER2024', 'MELD'):
        d = TR[p][ds]
        labs = '、'.join(f'{k} {v}' for k, v in d['labels'].items())
        P.append(f'<tr><td>{p}</td><td>{ds}</td><td class="n">{d["processed"]}（{pool[ds]}）</td><td class="n">{d["disagree"]}/{d["success"]}（{100 * d["ratio"]:.0f}%）</td>'
                 f'<td class="n">{d["selected"]}</td><td class="small">{labs}</td></tr>')
P.append('</table><ul class="small"><li>候选池 = 5 模型评测目录中去掉旧 400 条、通过媒体过滤的样本；按种子 42 随机顺序分批处理，每个数据集两个模型都攒够 200 条不一致样本或池子跑完即停。'
         'MER2024 的不一致比例低（Gemini 10%、GPT 17%），池子跑完也凑不满 200 条。</li>'
         '<li>入选样本按“先到先得”取，没有按标签分层。<b>训练集里 neutral 很多</b>（MELD：Gemini 85/200、GPT 110/200），而测试的不一致样本里 neutral 只有 Gemini 8/62、GPT 14/55。</li></ul>')
P.append('<h3>经验库</h3><table><tr><th>模型</th><th class="n">样本</th><th class="n">记录</th><th class="n">记录里答对</th><th class="n">第 0 / 1 / 2 轮答对</th><th class="n">训练辩论调用数</th></tr>')
for p in ('gemini', 'gpt'):
    m = M[p]
    b = m['by']
    rd = ' / '.join(f'{pct(b[f"r{i}"]["correct"], b[f"r{i}"]["n"])}' for i in range(3))
    P.append(f'<tr><td>{p}</td><td class="n">{m["train_dynamics"]["n"]}</td><td class="n">{m["records"]}</td><td class="n">{m["correct"]}（{pct(m["correct"], m["records"])}）</td>'
             f'<td class="n">{rd}</td><td class="n">{A["train_calls"][p]}</td></tr>')
P.append('</table><h3>训练集上的辩论本身（无经验，强制 2 轮）</h3><table><tr><th>模型</th><th class="n">样本</th><th class="n">第 0 轮 / 辩论 1 / 辩论 2：三人一致</th>'
         '<th class="n">多数答对</th><th class="n">至少一人答对</th></tr>')
for p in ('gemini', 'gpt'):
    d = M[p]['train_dynamics']
    P.append(f'<tr><td>{p}</td><td class="n">{d["n"]}</td><td class="n">{d["r0_unanimous"]} / {d["d1_unanimous"]} / {d["d2_unanimous"]}</td>'
             f'<td class="n">{d["r0_majority_correct"]} / {d["d1_majority_correct"]} / {d["d2_majority_correct"]}</td>'
             f'<td class="n">{d["r0_any_correct"]} / {d["d1_any_correct"]} / {d["d2_any_correct"]}</td></tr>')
gd, pd = M['gemini']['train_dynamics'], M['gpt']['train_dynamics']
P.append('</table><div class="warn">在新的训练样本上又看到同样的现象：辩论让三人迅速一致（Gemini 一致 '
         f'{gd["r0_unanimous"]}→{gd["d2_unanimous"]}），但“至少一人答对”从 {gd["r0_any_correct"]} 掉到 {gd["d2_any_correct"]}（GPT {pd["r0_any_correct"]}→{pd["d2_any_correct"]}），'
         f'多数答对只多了 {gd["d2_majority_correct"] - gd["r0_majority_correct"]}（GPT {pd["d2_majority_correct"] - pd["r0_majority_correct"]}）条。'
         '辩论把对的少数意见消掉了，这和旧 400 条上的结论（F5、F7）一致。经验库里存的就是这种辩论的轨迹。</div></section>')

# ---------------------------------------------------------------- why
P.append('<section class="panel"><h2>六、为什么没有用（分析，未做因果检验）</h2><ol>'
         '<li><b>检索给不出有用的类比。</b>案例按“Caption + 题目 + 自己上一轮回答 + 摘要”找相似，取回的案例标签与当前真实标签一致的只有约五分之一（随机约 15%）。视频情绪不像数学题那样“同类题同类解法”，外观和语气相似的片段情绪可以完全不同。</li>'
         '<li><b>经验来自同一个会从众的辩论。</b>训练辩论本身就会消掉正确的少数意见，案例里“专家改立场后答对 / 答错”的信号主要反映多数方向，而不是证据质量。</li>'
         '<li><b>训练集与测试集分布不同。</b>训练集偏 neutral、偏容易（MER2024 不一致比例只有 10%–17%），测试的不一致样本是旧 400 条里最难的那部分。</li>'
         '<li><b>同伴可靠度几乎处处有标记，high 与 low 各半</b>，模型得不到“该信谁”的有效信息。</li>'
         '<li><b>辩论框架本身的上限</b>：n0 就只有 44，比 Direct 低约 16 条。经验召回是在这个框架里微调，即使有效，也很难弥补这么大的差距。</li></ol></section>')

# ---------------------------------------------------------------- limits
P.append('<section class="panel"><h2>七、限制</h2><ul>'
         '<li>每个变体只跑一次；Direct 单次运行的极差就有 6 条，所以 1–3 条的差别都不能解读。</li>'
         '<li>测试集是旧 400 条里 v4 判为不一致的样本，这批样本已在开发中反复使用并按模型正确性筛选过。</li>'
         '<li>Gemini n3 缺 1 条（接口连续空返回）。</li>'
         '<li>实现与原版 R²-MAD 的差异：检索键用精简回答；同伴可靠度在相似度和≈0 时不标；摘要里的标签词被替换；结束规则沿用 v4（三人相同早停，否则静态汇总器），不是原版的多数票；经验库按数据集和专家过滤；案例的“标准解答”只有标签。</li>'
         '<li>训练集没有按标签分层，MER2024 两个模型都不满 200 条。</li>'
         '<li>“为什么没用”的几点是根据统计做的解释，没有改设置重跑验证。</li></ul></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>R²-MAD（v6）结果报告</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v6-rmad-report.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html), {v: tot[v] for v in V}, met)
