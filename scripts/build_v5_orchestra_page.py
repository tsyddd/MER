"""Build docs/v5-orchestra.html: design draft of v5-E (revised twice, final form per the user's idea):
ONE full-modal agent answers directly from all modalities; if it names an uncertain point, it looks back at the video (denser frames
around the doubtful moment + that audio window) and reflects, then gives the final answer. No experts, no controller.
Diagram first, nothing has been run. Reuses the drawing helpers of scripts/v5_paper_figs.py. Static HTML, no scripts, no model calls.
Usage: python scripts/build_v5_orchestra_page.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_paper_figs import (CTRL, NEW, CODE, agent, arrow, code_tag, diamond, doc, film, group, label_chip, legend, llm_tag, media_row, module,  # noqa: E402
                           out_box, svg, t, wave)

ROOT = Path(__file__).resolve().parent.parent


def fig_single():
    b = group(14, 40, 236, 400, '输入：一条样本', sub='（不一致分支，只给原媒体和候选集）')
    b += media_row(26, 96)
    b += t(26, 186, '候选集 C（通常 2 个）', size=11.5, bold=True)
    b += label_chip(26, 212, 'neutral') + label_chip(96, 212, 'anger')
    b += doc(26, 238, 200, 112, ['不提供：', '· 三位专家的答案、证据', '· 图谱与组织文本', '· 辩论与投票结果', '', '提供：原媒体 + 候选集 +', '　本数据集情绪轮的易混边界'], title='这个 agent 看到的', size=10)
    b += t(26, 382, 'Direct 的答案：anger（只用于对照）', size=10, color='#777')
    b += t(26, 398, '真实标签：anger（只用于评分）', size=10, color='#777')
    # (1) first answer
    b += module(284, 40, 244, 400, NEW[0], NEW[1], '首次作答', 1, 'Answer · 全模态一次判断')
    b += llm_tag(0, 12, 'LLM ×1', right=528)
    b += agent(334, 124, 24, '#555', '#eee', media=True)
    b += t(366, 118, '一个 agent', size=11, bold=True) + t(366, 134, '同时看 8 帧、音轨、字幕', size=10)
    b += t(298, 180, '要求输出：', size=11, bold=True)
    for i, s in enumerate(['1. 答案 ∈ C', '2. 1–3 条带位置的证据', '3. 不确定点：写出“我拿不准的是什么”', '　（例如“双眉是否聚拢”），', '　以及应该回看哪一段（帧 / 时间）；', '　没有不确定点就写“无”']):
        b += t(298, 200 + i * 18, s, size=10.5)
    b += doc(298, 316, 216, 118, ['答案：anger', '证据：f01 食指指向、No-no 加重', '不确定点：', '“眉心是否真的聚拢”', '回看：frame_01–03，音轨 0–2 秒', '（示意，未运行）'], title='输出示例', size=9.5)
    b += arrow([(250, 220), (284, 220)])
    # diamond
    b += diamond(588, 220, 52, 44, ['有不确定', '点？'])
    b += arrow([(528, 220), (536, 220)])
    b += arrow([(588, 264), (588, 318)]) + t(596, 296, '否', size=11.5, color='#C0392B', bold=True)
    b += out_box(534, 318, 108, 50, ('输出首次答案', '∈ C'))
    b += arrow([(640, 220), (676, 220)]) + t(656, 212, '是', size=11.5, anchor='middle', color='#2D6A4F', bold=True)
    # (2) re-look
    b += module(676, 40, 264, 400, NEW[0], NEW[1], '回看（带新输入）', 2, 'Re-look · 只看拿不准的地方')
    b += llm_tag(0, 12, 'LLM ×1', right=940)
    b += code_tag(0, 60, right=940)
    b += t(690, 108, '程序按它指定的位置取新输入：', size=10.5, bold=True)
    b += film(694, 122, 62, 40) + t(725, 176, '该时间窗内', size=9.5, anchor='middle', color='#555') + t(725, 189, '16 帧（更密）', size=9.5, anchor='middle', color='#555')
    b += wave(780, 130, 56, 28) + t(808, 176, '该时间段', size=9.5, anchor='middle', color='#555') + t(808, 189, '音轨片段', size=9.5, anchor='middle', color='#555')
    b += doc(852, 124, 76, 56, ['原 8 帧', '+ 字幕'], size=9.5, fold=7)
    for i, s in enumerate(['agent 针对“不确定点”再看一遍：', '· 回答那个具体问题（是 / 否 / 不确定）', '· 写出新看到的观察和位置', '· 与首次作答的证据比较：', '　哪条证据被新输入支持、哪条被削弱']):
        b += t(690, 222 + i * 19, s, size=10.5)
    b += t(690, 332, '新输入的来源：视频本身有 21–175 帧，', size=10, color='#555') + t(690, 347, '原来只均匀抽了 8 帧、最长边 448 像素，', size=10, color='#555') + t(690, 362, '所以更密的帧是真正的新信息。', size=10, color='#555')
    b += t(690, 392, 'GPT 无音轨：只回看帧与字幕', size=10, color='#8a6d00')
    # (3) reflect
    b += arrow([(940, 220), (972, 220)])
    b += module(972, 40, 254, 400, CTRL[1], CTRL[0], '反思核对 → 最终答案', 3, 'Reflect · 同一个 agent')
    b += llm_tag(0, 12, 'LLM ×1', right=1226)
    b += agent(1018, 120, 22, '#555', '#eee', media=True)
    b += t(1050, 114, '读：首次答案 + 回看结果', size=10.5, bold=True)
    for i, s in enumerate(['· 首次答案的每条证据现在还成立吗？', '· 回看有没有发现新的、可定位的证据？', '· 决定：保持首答 / 改为 C 内另一个标签', '　改答案必须引用回看得到的新证据；', '　没有新证据就保持首答', '· 仍无法确定 → 保持首次答案']):
        b += t(986, 176 + i * 19, s, size=10.5)
    b += out_box(1100, 318, 118, 50, ('最终标签', '∈ C'))
    b += t(1100, 400, '无不确定点的样本只用 1 次调用', size=10, color='#777', anchor='middle')
    b += legend(462)
    return svg(b, 484)


css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1260px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}
h1{font-size:25px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 16px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:5px 8px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.muted{color:#666}.small{font-size:13px}.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}
.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}code{background:#eee;padding:0 4px;border-radius:3px}
.fig{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px;margin:10px 0}.cap{font-size:14px;color:#333;margin:4px 6px 12px;line-height:1.7}'''

P = []
P.append('<h1>v5-E 设计草案（按你的思路）：一个全模态 agent，拿不准时回看再给最终答案</h1>')
P.append('<p class="muted">日期 2026-11-04。<b>只有设计，尚未实现、未运行，没有任何结果。</b>没有专家、没有控制器：一个 agent 看全部模态直接作答；它自己指出不确定的地方，才回看视频并反思，再给最终答案。只作用于 v4 的不一致分支（Gemini 62 条、GPT 55 条）；一致分支沿用 v4。前两版（四视角、控制器统筹专家）已被本页取代。</p>')
P.append('<section class="panel"><h2>一、流程图</h2><div class="fig">' + fig_single() + '</div>'
         '<p class="cap"><b>图 1　v5-E：一个全模态 agent，先答、拿不准再回看。</b>①同一个 agent 同时看 8 帧、音轨和字幕，在候选集内给出答案、带位置的证据，并自己写出“不确定点”和应该回看的位置（没有就写“无”，直接输出首次答案，只用 1 次调用）；②有不确定点时，程序按它指定的位置取<b>新的输入</b>（该时间窗内更密的帧、对应的音轨片段），agent 针对那个具体问题再看一遍；③同一个 agent 对照首次答案和回看结果做反思核对：改答案必须引用回看得到的新证据，否则保持首次答案。</p></section>')
P.append('<section class="panel"><h2>二、设计要点：为什么“回看”要带新输入</h2><ul>'
         '<li><b>只反思、不换输入，不太可能有用。</b>我们自己的数据：1200 次专家反思里，Gemini 只改过 6 次答案，GPT 13 次；文献里“没有外部反馈的自我纠正通常不提升，甚至下降”（Huang 等，ICLR 2024，我只读了摘要级信息）也是这个方向。所以这里的反思必须建立在<b>回看拿到的新信息</b>之上，并且规定“没有新证据不改答案”。</li>'
         '<li><b>新信息从哪里来</b>：视频本身有 21–175 帧，现有输入只均匀抽了 8 帧、最长边 448 像素。围绕不确定点所在的时间窗取更密的帧（默认 16 帧），或把音轨的对应片段单独给出（Gemini），是模型之前真的没看到的内容。这需要新写“按时间窗取帧”的代码。</li>'
         '<li><b>候选集内作答</b>：Direct 的答案 96%–97% 本来就在专家候选里，限定在候选集内不损失覆盖，并把任务变成 2–3 选 1。（备选：给全部标签，作为对照。）</li></ul></section>')
P.append('<section class="panel"><h2>三、最关键的问题：怎么判断“不确定”（已有数据）</h2>'
         '<p class="small muted">用 5 次独立 Direct 运行的“答案是否一致”作为不确定性的代理指标（<code>metrics/direct_vote_experiment.json</code>）。agent 自己写的“不确定点”是否可靠，目前<b>没有数据</b>，要靠第一步实验测。</p>'
         '<table><tr><th>模型</th><th>5 次 Direct 答案</th><th class="n">样本</th><th class="n">单次平均答对</th><th class="n">五次中至少一次对</th></tr>'
         '<tr><td rowspan="3">Gemini</td><td>完全一致</td><td class="n">29</td><td class="n">72%</td><td class="n">21</td></tr>'
         '<tr><td>4:1</td><td class="n">13</td><td class="n">48%</td><td class="n">10</td></tr>'
         '<tr><td>3:2 或更散</td><td class="n">20</td><td class="n">47%</td><td class="n">19</td></tr>'
         '<tr><td rowspan="3">GPT</td><td>完全一致</td><td class="n">25</td><td class="n">48%</td><td class="n">12</td></tr>'
         '<tr><td>4:1</td><td class="n">16</td><td class="n">44%</td><td class="n">14</td></tr>'
         '<tr><td>3:2 或更散</td><td class="n">14</td><td class="n">34%</td><td class="n">11</td></tr></table>'
         '<div class="note"><ul>'
         '<li><b>Gemini</b>：自己多次作答不一致，确实预示更容易错（72% 对 47%–48%），并且不一致的 33 条里有 29 条的五次答案出现过正确标签——“回看”有救回的空间。</li>'
         '<li><b>GPT</b>：这个信号几乎没用——五次完全一致的 25 条也只有 48% 答对，一半是“很确定却错了”。如果 GPT 的错误多半是自信地错，“只在不确定时回看”会漏掉大部分错误。GPT 可能需要对所有样本都回看，或者换一个触发信号。</li>'
         '<li>所以触发条件有三种选法：<b>(a) agent 自己写不确定点</b>（你的思路，默认）；<b>(b) 多次首答不一致</b>（3 次，成本更高，但对 Gemini 有数据支持）；<b>(c) 全部回看</b>（对照）。第一步实验就是测 (a) 的标记与答错是否相关。</li></ul></div></section>')
P.append('<section class="panel"><h2>四、每一步做什么</h2><table><tr><th>步骤</th><th>输入</th><th>输出</th><th>调用</th></tr>'
         '<tr><td>① 首次作答</td><td>原媒体（8 帧、可用音轨、字幕）、候选集 C、情绪轮里与 C 相关的易混边界</td><td>答案 ∈ C；1–3 条带位置的证据；不确定点（或“无”）及应回看的位置</td><td>1 次，看媒体</td></tr>'
         '<tr><td>② 回看</td><td>程序取的新输入：不确定点所在时间窗内的 16 帧、对应音轨片段（Gemini）、字幕；首次答案</td><td>对不确定点的回答（是 / 否 / 不确定）；新观察和位置；哪些首答证据被支持或削弱</td><td>仅有不确定点时 1 次，看媒体</td></tr>'
         '<tr><td>③ 反思核对</td><td>首次答案 + 回看结果</td><td>最终答案 ∈ C：保持或改变；改变必须引用新证据</td><td>仅有不确定点时 1 次</td></tr></table>'
         '<p class="small muted">没有不确定点的样本只用 1 次调用；有不确定点的 3 次。117 条约 117–351 次，比之前所有方法都便宜。</p></section>')
P.append('<section class="panel"><h2>五、评价（先定好，再跑）</h2><ul>'
         '<li>对象：不一致分支 117 条。真实标签只在算分时读取。</li>'
         '<li><b>对照</b>：Direct 单次均值（Gemini 36.6、GPT 23.8，合计 60.4）、Direct 三次投票均值（61.8）、v5-D（51）、v5-B0（50）。首次作答本身就是一个 Direct，所以“回看”带来的增量 = 最终答案 − 首次答案。</li>'
         '<li><b>“有提升”</b>：合并 117 条，最终答案比 Direct 5 次均值多答对至少 4 条，并且两个模型各自都不低于自己的均值；还要比首次答案多答对（否则回看没有价值）。</li>'
         '<li><b>必须报告</b>：首次答案的准确率；被标“不确定”的样本比例，以及标记与答错的关系（标不确定的是否更容易错、没标的里还有多少错）；回看改变答案的数量，其中改对 / 改错；改答案时是否真的引用了新证据；分模型、分数据集的结果；调用数。</li>'
         '<li>分两步做：<b>第一步</b>只跑首次作答（117 次），测准确率和“不确定”标记是否可靠，不涉及回看；<b>第二步</b>才实现“按时间窗取帧”和回看，只对被标记的样本跑。这样第一步成本很低，也能先判断这个思路是否站得住。</li>'
         '<li>提示词运行前冻结，每种设置跑一次。样本是筛选和开发复用数据，Direct 自己的单次波动达 6 条，只看相对差。</li></ul></section>')
P.append('<section class="panel"><h2>六、请你确认（括号里是我的默认）</h2><ol>'
         '<li>agent 只看原媒体 + 候选集（+ 易混边界），不看任何专家输出。（是）</li>'
         '<li>“不确定”由 agent 自己在首次作答里写出来；备选的触发方式（多次首答不一致、全部回看）作为对照。（是，先做 (a)）</li>'
         '<li>回看的新输入 = 不确定点所在时间窗内的 16 帧 + 对应音轨片段；GPT 无音轨只回看帧。（是；时间窗由 agent 指定，程序限制在 ±1 秒内取帧）</li>'
         '<li>反思核对：改答案必须引用回看得到的新证据；否则保持首次答案。（是）</li>'
         '<li>分两步：先只跑首次作答（117 次）测准确率和不确定标记；再做回看。（是）</li>'
         '<li>首次作答限定在候选集内。（是；是否另给一个“全部标签”的对照？默认不做）</li></ol>'
         '<div class="warn">你审核通过前，我不会写这个方法的代码，也不会调用模型来跑它。</div></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>v5-E 单 agent 回看（设计草案）</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v5-orchestra.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
