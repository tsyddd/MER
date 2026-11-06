"""Build docs/v4-80-debate-analysis.html: why the v4 reflect+debate flow does not beat the simple baselines on the 80
validation samples. Reads metrics/v4_val80_debate_analysis.json (made by scripts/analyze_v4_debate_80.py on the server) and
the train/all metrics of the 400-sample run. Static HTML, no scripts, no model calls.
Usage: python scripts/build_v4_debate_analysis_page.py
"""
import json
from collections import Counter
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / 'metrics/v4_val80_debate_analysis.json').read_text(encoding='utf8'))
TRAIN = {p: json.loads((ROOT / f'metrics/reflect_debate_v4_{p}_train.json').read_text(encoding='utf8')) for p in ['gemini', 'gpt']}
PN = {'gemini': 'Gemini', 'gpt': 'GPT'}
RN = {'graph': '图谱', 'audio_subtitle': '音频字幕', 'image': '图像'}
C = {p: D[p]['counts'] for p in D}


def pct(a, b):
    return f'{100 * a / b:.1f}%' if b else '—'


def sub(p, route_common):
    return [s for s in D[p]['samples'] if (s['route'] == 'common_label') == route_common]


def ok(rows, key):
    return sum((s['ok'] if key == 'v4' else s['majority'] == s['gold'] if key == 'majority' else s[key] == s['gold']) for s in rows)


css = '''body{font:15px/1.65 "Microsoft YaHei",sans-serif;max-width:1180px;margin:24px auto;padding:0 18px;color:#222;background:#fafafa}
h1{font-size:24px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:18px 0 6px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 18px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:4px 8px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}.muted{color:#666}.small{font-size:13px}
.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}
.good{background:#e6ffed}.bad{background:#ffeef0}.mid{background:#fff8dc}
.bar{display:inline-block;height:12px;vertical-align:middle;border-radius:2px}.b1{background:#48c}.b2{background:#c44}.b3{background:#999}
code{background:#eee;padding:0 4px;border-radius:3px}q{color:#333}
.case{border:1px solid #ccc;border-radius:5px;padding:6px 12px;margin:10px 0;background:#fcfcfc}.case p{margin:4px 0}.k{color:#a30}'''

P = []
P.append('<h1>v4 在 80 条验证集上为什么效果不好</h1>')
P.append('<p class="muted">日期 2026-11-03。数据来自已保存的输出（<code>scripts/analyze_v4_debate_80.py</code> 只读计算，没有新增模型调用）；真实标签只在计算时使用。验证集是开发中反复用过的数据，且进入辩论的样本很少（Gemini 15 条、GPT 8 条），下面都是描述性结论，不是显著性检验。</p>')

# ---------------------------------------------------------------- summary
g, t = C['gemini'], C['gpt']
P.append('<section class="panel"><h2>一、结论摘要</h2><ol>'
         f'<li><b>大多数错误根本不会进入辩论。</b>Gemini 答错 {g["wrong"]} 条，其中 {g["wrong_route_common_label"]} 条走的是“有共同标签，直接输出”，且 {g["wrong_common_allthree_same_primary"]} 条是三位专家主答案完全相同；GPT 答错 {t["wrong"]} 条，其中 {t["wrong_route_common_label"]} 条直接输出、{t["wrong_common_allthree_same_primary"]} 条三位完全相同。这些样本里<b>没有任何一位专家的主答案是真实标签</b>（0 条），辩论即使触发也无从纠正。</li>'
         f'<li><b>进入辩论的是最难的一小撮，而且这里“多数”并不可靠。</b>辩论样本 Gemini {g["debated"]} 条、GPT {t["debated"]} 条；其中三位主答案是 2:1 的 {g["debated_split_2_1"]}、{t["debated_split_2_1"]} 条，多数方答对只有 {g["debated_majority_ok"]}/{g["debated_with_majority"]}、{t["debated_majority_ok"]}/{t["debated_with_majority"]}。同样这批样本上，Direct 答对 {g["debated_direct_ok"]}/{g["debated"]}、{t["debated_direct_ok"]}/{t["debated"]}，v4 只有 {g["debated_ok"]}/{g["debated"]}、{t["debated_ok"]}/{t["debated"]}。</li>'
         f'<li><b>辩论结果几乎就是多数方。</b>Gemini 有多数方的 {g["debated_with_majority"]} 条里，少数派 {g["minority_experts"]} 位<b>全部</b>改投多数方，最终答案 {g["debated_final_equals_majority"]}/{g["debated_with_majority"]} 等于多数方；其中答对的少数派 {g["minority_correct"]} 位全部被说服走。GPT 是 {t["minority_adopted_majority"]}/{t["minority_experts"]} 位少数派改投、{t["minority_correct_persuaded_away"]}/{t["minority_correct"]} 位答对的少数派被说服走。</li>'
         '<li><b>“引用证据”没有挡住从众。</b>改答案时确实写了 <code>adopted_evidence</code>，但在我读的几条案例里，同一位专家反思时写“重音急促”，辩论时又写“重新听取后语速均匀平缓”，改答案的人只是接受了对方的描述；两个描述至少有一个不是真正核验过的（见第五节）。</li>'
         f'<li><b>反思没有产生新信息。</b>240 次反思里主答案只改了 1 次（Gemini）和 2 次（GPT）；反思后的多数投票与 Round 0 完全相同。备选答案让候选并集多了 4 到 5 条真实标签，但路由规则（恰好 1 个共同标签）用不上它们。</li>'
         '<li><b>错答案集中在常见标签，真实标签是稀有类。</b>辩论后答错的最终标签以 worried、neutral、surprise、anger、sad 为主，真实标签是 angry、disgust、fear、joy 等（见第四节），与之前混淆矩阵里“稀有类被吸收进常见类”一致。</li>'
         '</ol></section>')

# ---------------------------------------------------------------- results table
calls = {'gemini': 240 + 240 + (12 + 3 * 2) * 3, 'gpt': 240 + 240 + (5 + 3 * 2) * 3}
rowsT = [('Direct（原媒体直接分类）', 60, 52, '1 次'),
         ('原 PPCT', 54, 62, '5 次（感知、时序、联合、组织、分类）'),
         ('v3 汇总器', 56, 56, '5 次（组织 + 三专家 + 汇总）'),
         ('v3 三专家多数投票（平票算错）', 59, 57, '同上，不用汇总器'),
         ('v4 Round 0 主答案多数投票', 57, 55, '3 次'),
         ('v4 反思后主答案多数投票', 57, 55, '6 次'),
         ('<b>v4 最终</b>', 57, 55, f'约 {calls["gemini"] / 80:.1f} / {calls["gpt"] / 80:.1f} 次（不含复用的组织文本）')]
P.append('<section class="panel"><h2>二、结果总表（80 条：MER2024 40 + MELD 40）</h2><table><tr><th>方法</th><th class="n">Gemini</th><th class="n">GPT</th><th>每条样本的模型调用</th></tr>' +
         ''.join(f'<tr><td>{n}</td><td class="n">{a}/80（{pct(a, 80)}）</td><td class="n">{b}/80（{pct(b, 80)}）</td><td>{c}</td></tr>' for n, a, b, c in rowsT) +
         '</table><p class="muted small">Direct、原 PPCT、v3 汇总器的数字来自已保存的结果（与 <code>LOCAL_WORKSPACE.md</code> 一致，本页由逐样本文件重新计数核对）。v4 调用次数为 80 条总调用除以 80：Round 0 与反思各 240 次，加上辩论调用。v4 对 GPT 比 Direct 多 3 条，比原 PPCT 少 7 条；对 Gemini 比 Direct 少 3 条。</p></section>')

# ---------------------------------------------------------------- route table
P.append('<section class="panel"><h2>三、错误出在哪一条路径</h2>')
for p in ['gemini', 'gpt']:
    rc, rd = sub(p, True), sub(p, False)
    rows = [('直接输出（恰好 1 个共同标签）', rc), ('辩论（后一致或进汇总器）', rd)]
    P.append(f'<h3>{PN[p]}</h3><table><tr><th>路径</th><th class="n">样本</th><th class="n">v4 答对</th><th class="n">v4 答错</th><th class="n">Direct 答对</th><th class="n">v3 汇总器答对</th><th class="n">多数投票答对</th><th>答对占比（柱）</th></tr>')
    for name, rs in rows:
        a = ok(rs, 'v4')
        P.append(f'<tr><td>{name}</td><td class="n">{len(rs)}</td><td class="n">{a}</td><td class="n">{len(rs) - a}</td><td class="n">{ok(rs, "direct")}</td><td class="n">{ok(rs, "v3_summary")}</td>'
                 f'<td class="n">{ok(rs, "majority")}</td><td><span class="bar b1" style="width:{int(150 * a / max(1, len(rs)))}px"></span><span class="bar b2" style="width:{int(150 * (len(rs) - a) / max(1, len(rs)))}px"></span> {pct(a, len(rs))}</td></tr>')
    P.append('</table>')
    c = C[p]
    P.append(f'<p class="small">直接输出路径答错 {c["wrong_route_common_label"]} 条：三位主答案完全相同 {c["wrong_common_allthree_same_primary"]} 条；真实标签出现在某位专家主答案里的 {c["wrong_common_gold_in_some_primary"]} 条；只出现在备选答案（候选并集）里的 {c["wrong_common_gold_in_union"]} 条。'
             f'辩论路径答错 {c["wrong_route_debate_consensus"]} 条。汇总器在 80 条里 {c["summary_used"]} 次被调用（辩论后全部达成一致）。</p>')
P.append('<div class="note">所以 v4 能改的只有“辩论路径”这一小块：Gemini 15 条、GPT 8 条，占 80 条的 19% 和 10%，而错误的另一半以上不在这块里。最理想的情况下，即使辩论路径全部答对，Gemini 最多也只是 57+11=68、GPT 55+6=61；而实际辩论路径的答对率是 27% 和 25%。</div></section>')

# ---------------------------------------------------------------- debate behaviour
P.append('<section class="panel"><h2>四、辩论路径里发生了什么</h2>')
P.append('<table><tr><th>统计</th><th class="n">Gemini</th><th class="n">GPT</th></tr>')
items = [('进入辩论的样本', 'debated'), ('其中 2:1 分歧（主答案）', 'debated_split_2_1'), ('其中 1:1:1 分歧', 'debated_split_1_1_1'),
         ('真实标签在三位反思后主答案之内', 'debated_gold_in_primary'), ('真实标签在候选并集内（含备选）', 'debated_gold_in_union'),
         ('其中只靠备选才进入并集', 'debated_gold_in_union_only_via_backup'), ('需要第 2 轮辩论', 'debate_rounds_2'),
         ('参与辩论的专家次数', 'debate_expert_total'), ('其中改变了答案', 'debate_expert_changed'), ('改答案：改向多数方', 'flip_to_majority'),
         ('改答案：对→错', 'flip_correct_to_wrong'), ('改答案：错→对', 'flip_wrong_to_correct'), ('改答案：错→错', 'flip_wrong_to_wrong'),
         ('2:1 里的少数派专家', 'minority_experts'), ('其中答对的少数派', 'minority_correct'), ('少数派最终改投多数方', 'minority_adopted_majority'),
         ('答对的少数派被说服走', 'minority_correct_persuaded_away'), ('多数方答对', 'debated_majority_ok'), ('v4 最终答对', 'debated_ok'),
         ('多数方错而辩论后对（救回）', 'debated_majority_wrong_final_right'), ('多数方对而辩论后错（带偏）', 'debated_majority_right_final_wrong'),
         ('最终等于多数方（有多数方的样本）', 'debated_final_equals_majority')]
for name, k in items:
    P.append(f'<tr><td>{name}</td><td class="n">{g.get(k, 0)}</td><td class="n">{t.get(k, 0)}</td></tr>')
P.append('</table>')
P.append('<p class="small">“救回”和“带偏”都很少：Gemini 0 和 0，GPT 1 和 1。辩论路径上的结果基本由反思时的多数方决定，辩论本身没有创造增益；它只是让少数派改口，使三个单答案一致。</p>')

P.append('<h3>辩论后答错的样本：真实标签 → 最终标签</h3><table><tr><th>模型</th><th>样本</th><th>真实</th><th>三位反思后主答案（图谱/音频字幕/图像）</th><th>最终</th><th>Direct</th></tr>')
for p in ['gemini', 'gpt']:
    for s in sub(p, False):
        if not s['ok']:
            pr = s['reflect_primary']
            P.append(f'<tr class="bad"><td>{PN[p]}</td><td>{e(s["id"])}</td><td>{s["gold"]}</td><td>{pr["graph"]} / {pr["audio_subtitle"]} / {pr["image"]}</td><td>{s["final"]}</td><td>{s["direct"]}{" ✓" if s["direct"] == s["gold"] else ""}</td></tr>')
P.append('</table>')
for p in ['gemini', 'gpt']:
    wrong = [s for s in D[p]['samples'] if not s['ok']]
    pair = Counter((s['gold'], s['final']) for s in wrong)
    P.append(f'<p class="small">{PN[p]} 全部 {len(wrong)} 条错误的（真实→最终）：' + '；'.join(f'{a}→{b} ×{n}' for (a, b), n in pair.most_common(8)) + '。</p>')
P.append('</section>')

# ---------------------------------------------------------------- all debated samples
P.append('<section class="panel"><h2>五、全部辩论样本与四个案例</h2>')
P.append('<table><tr><th>模型</th><th>样本</th><th>真实</th><th>Round 0 答案集合（图/音/像）</th><th>反思后主答案</th><th>辩论后</th><th>最终</th><th>Direct</th><th>v3</th></tr>')
for p in ['gemini', 'gpt']:
    for s in sub(p, False):
        r0s = ' | '.join('+'.join(s['r0_sets'][r]) for r in ['graph', 'audio_subtitle', 'image'])
        pr = ' / '.join(s['reflect_primary'][r] for r in ['graph', 'audio_subtitle', 'image'])
        fin = ' / '.join(s['debate'][r]['final'] for r in ['graph', 'audio_subtitle', 'image'])
        cls = 'good' if s['ok'] else 'bad'
        P.append(f'<tr class="{cls}"><td>{PN[p]}</td><td>{e(s["id"])}</td><td>{s["gold"]}</td><td>{r0s}</td><td>{pr}</td><td>{fin}</td><td>{s["final"]}</td><td>{s["direct"]}</td><td>{s["v3_summary"]}</td></tr>')
P.append('</table>')
P.append('<h3>案例（节选自已保存的辩论输出，字段原文截断）</h3>')
CASES = [('gemini', 'MELD/dia198_utt2', 'image'), ('gemini', 'MELD/dia186_utt0', 'image'), ('gemini', 'MER2024/samplenew_00033166', 'graph'), ('gpt', 'MELD/dia66_utt1', 'image')]
for p, sid, role in CASES:
    s = next(x for x in D[p]['samples'] if x['id'] == sid)
    ex = s['debate'][role]
    rd = ex['rounds'][0]
    P.append(f'<div class="case"><p><b>{PN[p]} · {e(sid)}</b>　真实 <b>{s["gold"]}</b>，{RN[role]}专家反思后答 <b>{ex["reflect_answer"]}</b>，辩论后改成 <b>{rd["answer"]}</b>；最终 {s["final"]}；Direct {s["direct"]}。字幕：{e(s["subtitle"][:80])}</p>'
             f'<p><span class="k">反思时的理由：</span>{e(ex["reflect_reason"])}</p>'
             f'<p><span class="k">反思时写的最强反证：</span>{e(ex["reflect_counter"])}</p>' +
             ''.join(f'<p><span class="k">改答案时“核实”的内容（采纳自 {e(a["frm"])}）：</span>{e(a["verified"])}</p>' for a in rd['adopted']) +
             ''.join(f'<p><span class="k">对{e(x["to"])}专家的回应：</span>{e(x["reply"])}</p>' for x in rd['responses']) + '</div>')
P.append('<div class="warn"><b>怎么读这些案例</b>：dia198_utt2 里，图像专家反思时写“音轨前段对 No-no 和 kicked 的急促加重发音”，辩论时又写“重新听取音轨，语速均匀平缓，尾音自然落定”，并据此改成 neutral；两个描述针对同一段音轨，不可能都是真正听过之后的描述。dia186_utt0 也是：反思时写“嘴角向下撇起、下唇收紧”，辩论时写“嘴角下撇程度极弱”。samplenew_00033166 则不是前后矛盾，而是对同一组特征（眉眼紧绷、声音加重）换了解读：从“严厉反诘”改成“焦急”。GPT 的 dia66_utt1 没有前后矛盾，专家只是因为对方指出“持续笑容属于右侧女子”而下调了轻微笑意的权重，这是正常的改变，但结果仍是答错。以上是我读了 6 条案例（上面 4 条，另 2 条为 Gemini 的 dia131_utt3 和 GPT 的 sample_00002038）后的观察，没有对全部 23 条逐条核对，也没有独立听音轨判断谁对。可以确定的是：要求“引用证据并写出核实到了什么”，没有让改答案变成“只有证据真的变了才改”，因为模型没有工具可以核实，只能用语言复述对方的观察。</div></section>')

# ---------------------------------------------------------------- 400 recheck
P.append('<section class="panel"><h2>六、训练集 320 条上的复核</h2><p class="muted small">同一套流程在训练集 320 条上跑过（图谱为新生成）；训练集样本是按模型正确性筛选的，不能与验证集比绝对数字，只看结构是否一致。</p>')
P.append('<table><tr><th>指标</th><th class="n">Gemini</th><th class="n">GPT</th></tr>')
for name, f in [('v4 最终', lambda p: TRAIN[p]['stats']['v4 final']), ('Round 0 主答案多数投票', lambda p: TRAIN[p]['stats']['r0 primary majority (ties wrong)']),
                ('直接输出：样本 / 答对', lambda p: f'{TRAIN[p]["by_route"]["common_label"]["n"]} / {TRAIN[p]["by_route"]["common_label"]["correct"]}'),
                ('辩论后一致：样本 / 答对', lambda p: f'{TRAIN[p]["by_route"]["debate_consensus"]["n"]} / {TRAIN[p]["by_route"]["debate_consensus"]["correct"]}'),
                ('汇总器：样本 / 答对', lambda p: f'{TRAIN[p]["by_route"].get("summary", {}).get("n", 0)} / {TRAIN[p]["by_route"].get("summary", {}).get("correct", 0)}'),
                ('反思改变主答案的专家次数（共 960 次）', lambda p: TRAIN[p]['stats']['reflect changed primary'])]:
    P.append(f'<tr><td>{name}</td><td class="n">{f("gemini")}</td><td class="n">{f("gpt")}</td></tr>')
P.append('</table><p class="small">结构与验证集相同：直接输出路径答对率 83.5%，辩论路径只有 43%–48%；v4 最终低于自己的 Round 0 多数投票 4 到 5 条；反思几乎不改答案。</p></section>')

# ---------------------------------------------------------------- hypotheses
P.append('<section class="panel"><h2>七、可能的改进方向（假设，未验证）</h2><ul>'
         '<li><b>分歧来源要独立。</b>同一个模型的三个角色，错误高度相关（F2）；分歧只在 15 和 8 条里出现。用 GPT/Gemini/Omni 跨模型专家，或让不同模型当辩手，才可能让“有人对”的样本变多。</li>'
         '<li><b>把触发条件改成“可能共同出错”。</b>三位一致的错误占了错误的一半以上；需要别的信号（对该类易混淆标签的先验、模型间分歧、置信度）去触发复核，而不是只看分歧。</li>'
         '<li><b>辩论里让证据可检验。</b>目前“核实”只是语言；如果改为对某一帧/某一段音频做独立的小任务（例如仅回答“该段音轨是否有重音”），再把结果当事实交给辩手，才能阻止“复述对方的观察”。</li>'
         '<li><b>别强制单一答案收敛。</b>少数派答对的样本里，保留少数派标签作为汇总器的候选（而不是在辩论中让它改口），可能比“少数改投多数”更好；这需要实验。</li>'
         '<li><b>稀有类先验。</b>错误集中在 angry→worried、disgust→anger/neutral 这类单向混淆（见 <code>docs/confusion-matrices.html</code>），也许是校准问题，而不是推理问题。</li></ul>'
         '<p class="muted small">以上都是读完数据后的推测，每一条都需要单独实验，并且要在训练集或新数据上验证，不能只看这 80 条。</p></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>v4 在 80 条上为什么效果不好</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v4-80-debate-analysis.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
