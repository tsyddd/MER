"""Build docs/v5-design.html: v5 design draft (simple version) for review. v5 = v4's first half (Round 0 -> reflection ->
common-label routing, reused as saved) + ONE change in the disagreement branch: instead of the debate, a single media-only
call that compares the candidate labels and picks one. Static HTML with inline SVG, no scripts, no model calls; nothing in
this page has been run.
Usage: python scripts/build_v5_design_page.py
"""
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COL = {'plain': ('#ffffff', '#6b6b6b'), 'old': ('#eeeeee', '#8a8a8a'), 'new': ('#fff3c4', '#b8860b'), 'final': ('#d8f3dc', '#2d6a4f'), 'cond': ('#fdecea', '#b33')}


def box(x, y, w, h, lines, cls='plain', size=13, bold_first=True, align='middle'):
    f, s = COL[cls]
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{f}" stroke="{s}" stroke-width="1.6"/>'
    lh = size + 6
    y0 = y + h / 2 - lh * (len(lines) - 1) / 2 + size / 3
    for i, t in enumerate(lines):
        fw = ' font-weight="700"' if (i == 0 and bold_first) else ''
        tx = x + w / 2 if align == 'middle' else x + 14
        out += f'<text x="{tx}" y="{y0 + i * lh}" font-size="{size}" text-anchor="{align}" fill="#222"{fw}>{e(t)}</text>'
    return out


def diamond(cx, cy, rx, ry, lines):
    out = f'<polygon points="{cx},{cy - ry} {cx + rx},{cy} {cx},{cy + ry} {cx - rx},{cy}" fill="#fff8e6" stroke="#b8860b" stroke-width="1.6"/>'
    for i, t in enumerate(lines):
        out += f'<text x="{cx}" y="{cy + 5 + (i - (len(lines) - 1) / 2) * 18}" font-size="13" text-anchor="middle" fill="#222">{e(t)}</text>'
    return out


def arrow(pts, color='#444'):
    d = ' '.join(f'{x},{y}' for x, y in pts)
    return f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.8" marker-end="url(#ah)"/>'


def lab(x, y, t, anchor='start', size=12, color='#333', bold=False):
    fw = ' font-weight="700"' if bold else ''
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{fw}>{e(t)}</text>'


def flow():
    b = '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#444"/></marker></defs>'
    b += lab(20, 26, '沿用 v4（读已保存的输出，不重跑）', size=13, color='#666', bold=True)
    b += box(20, 40, 170, 84, ['输入', '8 帧 + 字幕', '（+音轨）（+图谱）'])
    b += box(230, 40, 340, 84, ['Round 0：三位专家各自判断', '（可给 1–2 个答案）', '→ 反思（每位一次）'], 'old')
    b += arrow([(190, 82), (230, 82)]) + arrow([(570, 82), (595, 82)])
    b += diamond(700, 82, 105, 52, ['三位答案集合有', '恰好 1 个共同标签？'])
    b += arrow([(805, 82), (880, 82)]) + lab(812, 72, '是（约 85%）')
    b += box(880, 52, 210, 60, ['直接输出共同标签', '（一致分支，不改）'], 'old')
    b += arrow([(1090, 82), (1120, 82)])
    b += box(1120, 52, 110, 60, ['最终标签'], 'final')
    b += arrow([(700, 134), (700, 236)])
    b += lab(712, 176, '否（约 15%：Gemini 62 条、GPT 55 条）')
    # v5 change
    b += '<rect x="20" y="206" width="1210" height="226" rx="12" fill="#fffdf2" stroke="#b8860b" stroke-width="1.6" stroke-dasharray="6 4"/>'
    b += lab(36, 228, 'v5 唯一的改动：不一致分支不再辩论，改成一次“候选内对比裁决”', size=14, color='#8a6d00', bold=True)
    b += box(40, 246, 270, 164, ['裁判看不到的', '专家的理由、答案和身份', '辩论记录', '图谱与组织文本'], 'cond', size=12.5)
    b += box(340, 246, 580, 164, ['候选内对比裁决（一次调用，看原媒体）', '输入：原媒体（8 帧、可用音轨、字幕）+ 候选标签（平均约 2.4 个）', '　　　+ 情绪轮里与这些候选相关的易混边界说明', '要求：每个候选各写一条最具体的支持观察和一条反对观察（带位置），', '　　　再比较，只在候选里选一个', '输出：候选之一 + 2–3 句理由'], 'new', size=12.5, align='start')
    b += arrow([(920, 328), (1175, 328), (1175, 114)])
    b += lab(1186, 262, '答案只能在', size=12)
    b += lab(1186, 280, '候选集内', size=12)
    b += arrow([(310, 328), (340, 328)], '#b33')
    b += lab(20, 458, '成本：每个不一致样本 1 次调用；117 条（Gemini 62 + GPT 55）共 117 次。', size=13)
    b += lab(20, 480, '图例：', size=12)
    for i, (cls, t) in enumerate([('old', '沿用 v4'), ('new', 'v5 新增'), ('cond', '不提供给裁判'), ('final', '输出')]):
        f, s = COL[cls]
        b += f'<rect x="{68 + i * 130}" y="468" width="16" height="16" rx="3" fill="{f}" stroke="{s}"/>' + lab(90 + i * 130, 481, t, size=12)
    return f'<svg viewBox="0 0 1250 500" width="100%" role="img" aria-label="v5 流程图" font-family="Microsoft YaHei,sans-serif">{b}</svg>'


def bars():
    """Reference bars for the 117 disagreement-branch samples; the new method is a dashed placeholder."""
    out = '<defs></defs>'
    panels = [('Gemini（62 条）', 62, [('随机选（期望）', 25.6, '#bbb'), ('图谱专家', 26, '#f0b86e'), ('音频字幕专家', 32, '#f0b86e'), ('图像专家', 27, '#f0b86e'), ('v4 辩论', 26, '#9ab'), ('Direct', 38, '#4a7'), ('v5 对比裁决', None, None), ('候选集上限', 58, '#d9a')], 20),
              ('GPT（55 条）', 55, [('随机选（期望）', 22.8, '#bbb'), ('图谱专家', 31, '#f0b86e'), ('音频字幕专家', 17, '#f0b86e'), ('图像专家', 21, '#f0b86e'), ('v4 辩论', 19, '#9ab'), ('Direct', 26, '#4a7'), ('v5 对比裁决', None, None), ('候选集上限', 49, '#d9a')], 640)]
    for title, n, rows, x0 in panels:
        out += lab(x0, 24, title, size=14, bold=True)
        scale = 340.0 / n
        for i, (name, v, color) in enumerate(rows):
            y = 44 + i * 40
            out += lab(x0, y + 16, name, size=12.5)
            if v is None:
                out += f'<rect x="{x0 + 120}" y="{y}" width="{int(scale * (n / 2))}" height="22" rx="3" fill="none" stroke="#b8860b" stroke-dasharray="5 3"/>' + lab(x0 + 128, y + 16, '待运行（审核通过后才跑）', size=12, color='#8a6d00')
            else:
                out += f'<rect x="{x0 + 120}" y="{y}" width="{max(2, int(scale * v))}" height="22" rx="3" fill="{color}"/>' + lab(x0 + 126 + int(scale * v), y + 16, f'{v:g}（{100 * v / n:.0f}%）', size=12)
        out += f'<line x1="{x0 + 120}" y1="38" x2="{x0 + 120}" y2="372" stroke="#999"/>'
    return f'<svg viewBox="0 0 1250 385" width="100%" role="img" aria-label="不一致分支对照" font-family="Microsoft YaHei,sans-serif">{out}</svg>'


PROMPT = '''你是情绪判别员。判断指定目标人物在当前片段的情绪。你有按时间排列的8帧、可用字幕，以及audio_provided=true时的真实音轨；没有音轨时，听觉判断限于字幕与视觉。
candidate_labels是这条样本的候选标签（2到3个），你的答案从其中选一个。
请逐个候选标签对照原始媒体：
1. 为每个候选找出原媒体里最能支持它的一条具体观察，和最能反对它的一条具体观察；每条都写明位置（frame编号与时间、音轨时间段或字幕原话）。
2. 先写看到或听到了什么，再写它说明什么；只使用片段里可以定位的观察。找不到时写“未找到”。
3. 比较各候选的支持与反对，选出证据最充分的一个。
【易混边界】（只放入与这几个候选相关的条目，条目取自本数据集情绪轮的易混边界说明）
……
只返回JSON，字段恰好为：{"comparison":[{"label":"候选标签","support":{"observation":"...","location":"..."},"against":{"observation":"...","location":"..."}}],"answer":"候选标签之一","reason":"2到3句：为什么选它，以及为什么不选其他候选"}。程序统一包装<answer>。'''

PAYLOAD = '''{"sample_id": "...", "target_speaker": "...", "candidate_labels": ["worried", "surprise"], "frame_times_seconds": [...], "audio_provided": true, "subtitle": "..."}
# 不包含：专家的答案/理由/证据、专家身份、图谱、组织文本、辩论记录、真实标签。图片为8帧，Gemini 另附音轨。'''

css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1240px;margin:24px auto;padding:0 18px;color:#222;background:#fafafa}
h1{font-size:25px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:18px 0 6px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 18px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:5px 8px;text-align:left;vertical-align:top}th{background:#eef}
.muted{color:#666}.small{font-size:13px}.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}
.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}code{background:#eee;padding:0 4px;border-radius:3px}
pre{background:#f6f6f6;border:1px solid #ddd;border-radius:4px;padding:10px 12px;white-space:pre-wrap;font:13px/1.6 Consolas,"Microsoft YaHei",monospace}
.fig{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px;margin:10px 0}'''

P = []
P.append('<h1>v5 设计草案（简化版）：不一致分支改成“候选内对比裁决”</h1>')
P.append('<p class="muted">日期 2026-11-03。<b>待你审核；尚未实现、未运行，没有任何结果。</b>这一版只做一个改动，替换上一版的四步方案（那版的抽取论断、盲核对等因为太重、且每一步都没有数据支持，已放弃，见第六节）。下面的数字来自已保存的 v4 / Direct 结果（<code>metrics/findings_log.md</code> F5–F7）。</p>')

P.append('<section class="panel"><h2>一、要解决的问题</h2><ul>'
         '<li><b>不一致分支是 v4 最弱的一块，而且是辩论造成的。</b>400 条里有 117 条（Gemini 62、GPT 55）没有恰好 1 个共同标签。v4 辩论在这块答对 26 和 19 条，约等于在候选里随机选（期望 25.6 和 22.8）。</li>'
         '<li><b>辩论没有产生新信息。</b>少数派专家几乎全部改投多数（13/13、6/7），而多数方只对 4/13 和 2/7；改答案时写的“核实”只是语言。</li>'
         '<li><b>没有专家参与的 Direct 在这块明显更好。</b>Direct 答对 38 和 26 条，它的答案 96%–97% 落在专家候选内（60/62、53/55）。</li>'
         '<li><b>候选里有答案，选不出来。</b>候选并集覆盖真实标签 89%–94%，完美选择的上限是 58 和 49 条。瓶颈是在 2–3 个候选里选对。</li></ul>'
         '<p><b>问题：</b>在不一致分支里，一个只看原媒体、并被要求逐个比较候选标签证据的裁判，能不能比不加约束的 Direct 选得更准？</p>'
         '<p class="small muted">我的猜测（未验证）：Direct 的一部分错误是没有认真比较备选标签；强制“每个候选各给一条支持、一条反对”可以让它真的去对照媒体。同时放入情绪轮里已有的易混边界，是 Direct 没有的信息。</p></section>')

P.append('<section class="panel"><h2>二、方法与流程图</h2><div class="fig">' + flow() + '</div>'
         '<p class="muted small">只改黄色部分。前半（Round 0 → 反思 → 路由）和一致分支沿用 v4 已保存的输出，不重跑。裁判看不到任何专家的东西，所以没有“多数”可以跟；它也不是辩论，只有一次调用。</p>'
         '<table><tr><th>设计点</th><th>选择</th><th>为什么</th></tr>'
         '<tr><td>候选标签</td><td>用 v4 已经算出的候选并集（三位专家 Round 0 与反思后出现过的全部标签，含备选）</td><td>覆盖 89%–94%，不需要另造候选；答案限制在候选内也让选择变成 2–3 选 1。</td></tr>'
         '<tr><td>不给专家的任何内容</td><td>不给答案、理由、身份、图谱、组织文本</td><td>数据显示专家之间没有额外信息，给了反而会被带偏；Direct 正是因为独立才表现更好。</td></tr>'
         '<tr><td>强制对比</td><td>每个候选各一条支持、一条反对，带位置</td><td>要求裁判真的在媒体里为每个候选找依据，而不是只给一个印象。</td></tr>'
         '<tr><td>易混边界说明</td><td>取情绪轮里已有的、同时提到至少两个候选标签的条目；没有匹配的条目就不放</td><td>这是 Direct 没有、而我们已经写好的知识；规则简单，不为这 117 条定制。</td></tr>'
         '<tr><td>调用次数</td><td>每个不一致样本 1 次</td><td>保持简单；117 次调用。</td></tr></table></section>')

P.append('<section class="panel"><h2>三、裁判的“问题”：提示词与输入输出草案（待审核）</h2>'
         '<p>系统提示词草案（正向写法，不含版本信息；“易混边界”处按上面的规则插入相应条目）：</p><pre>' + e(PROMPT) + '</pre>'
         '<p>用户消息（输入）：</p><pre>' + e(PAYLOAD) + '</pre>'
         '<p class="small muted">程序检查：JSON 字段齐全；<code>answer</code> 必须在 <code>candidate_labels</code> 内；<code>comparison</code> 覆盖每个候选；没有音轨时不得声称听过声音（与 v4 一致）。不合格时重试，最多 3 次；仍不合格则该样本记为无效并如实统计，不用其他方法补。温度 0，只跑一次。</p></section>')

P.append('<section class="panel"><h2>四、评价指标与判断标准（先定好，再跑）</h2><div class="fig">' + bars() + '</div>'
         '<p class="muted small">灰色=随机选的期望，橙=三位专家各自的 Round 0 主答案，蓝=v4 辩论，绿=Direct，粉=候选集上限（完美选择）；黄色虚线框是 v5 的位置（待运行）。柱长按各自分支的样本数缩放。三位专家取 Round 0 独立判断的主答案；反思后的主答案分别是 Gemini 25 / 31 / 26、GPT 30 / 16 / 19，几乎相同。每位专家只回答自己拿到的信息（图谱专家有图谱与组织文本，另两位没有）。</p>')
P.append('<h3>主要判断（运行前约定）</h3><ul>'
         '<li><b>对照组是 Direct，不是 v4</b>：Direct 在这块已经比 v4 好很多。</li>'
         '<li><b>算“有提升”的条件</b>：合并两个模型的 117 条，v5 比 Direct 多答对<b>至少 4 条</b>（约 3.4 个百分点），并且两个模型各自都不低于 Direct。否则结论是“没有提升”，不一致分支直接用 Direct 兜底。</li>'
         '<li>这个阈值是我定的，可以改；117 条的检测力很低，即使达标也只能说“值得在新样本上验证”，不能说方法有效。</li></ul>')
P.append('<h3>每个模型都要报告的表</h3>'
         '<table><tr><th>表</th><th>内容</th></tr>'
         '<tr><td>T1 分支准确率</td><td>不一致分支答对数：v5 / 三位专家 / Direct / v4 / 随机期望 / 候选集上限；按模型、按数据集（MER2024、MELD）、按验证与训练拆开。</td></tr>'
         '<tr><td>T2 与 Direct 的逐条翻转</td><td>同对 / 同错 / v5 改对 / v5 改错，附精确符号检验的 p 值（仅供参考，样本很少）。</td></tr>'
         '<tr><td>T3 整体 400 条</td><td>“一致用 v4、不一致用 v5”的整体准确率，对照 v4（307 / 300）、Direct（311 / 294）、“一致用 v4、不一致用 Direct”（319 / 307）、上限（339 / 330）。</td></tr>'
         '<tr><td>T4 约束与成本</td><td>答案落在候选内的比例（应为 100%）、重试次数、无效样本数、调用次数和 token 数。</td></tr>'
         '<tr><td>T5 人工抽查</td><td>翻转的样本（改对和改错各至少 10 条，不足则全看）：检查“支持/反对”的观察是不是真的能在帧、字幕里定位。这是定性阅读，只作说明。</td></tr></table>')
P.append('<h3>防止自欺的做法</h3><ul>'
         '<li>提示词在运行前冻结，不在这 117 条上调；跑一次，所有结果都报告。</li>'
         '<li>真实标签不进入任何调用，只在算分时读取。</li>'
         '<li>训练集样本是按模型正确性筛选的、验证集是开发复用数据，所以绝对数字只作参考，重点看相对 Direct 的差值。</li>'
         '<li>如果有提升，下一步是在没有被模型筛选过的新样本上确认，而不是继续在这 117 条上改。</li></ul></section>')

P.append('<section class="panel"><h2>五、风险与限制</h2><ul>'
         '<li>Direct 的答案 96%–97% 已经在候选内，所以“限制在候选内”本身几乎没有区别，真正的变量是“强制对比”和“易混边界说明”。如果有提升，我分不清是哪一个起作用；需要的话可以再各去掉一个做消融，但那是第二步。</li>'
         '<li>“逐个候选写支持与反对”可能只是让模型写出看起来合理的话，不一定真的更准；这就是为什么要人工抽查翻转样本。</li>'
         '<li>GPT 没有音轨，声音类的对比只能依据字幕和视觉。</li>'
         '<li>样本很少（117 条），而且这块本来就是最难的样本，噪声大。</li>'
         '<li><b>如果没有提升</b>：说明不一致分支的信息确实有限，最合理的结论是用 Direct 兜底，不再投入这块，转去做新样本评估或一致分支。</li></ul></section>')

P.append('<section class="panel"><h2>六、暂不做的方案（记录，非本次范围）</h2><ul>'
         '<li>抽取分歧论断 → 逐个论断盲核对 → 裁判（上一版 v5）：约 350–600 次调用，每步都没有我们数据的支持；等这一版的结果出来再决定要不要加。</li>'
         '<li>倡导者加裁判、匿名化或反从众的辩论变体：辩论本身没有新信息，预期收益有限。</li>'
         '<li>Conformal 预测集：候选覆盖已经够高，瓶颈不在覆盖。</li>'
         '<li>用训练集做经验记忆、跨模型辩手：成本高，且训练集是筛选过的，放到后面。</li></ul></section>')

P.append('<section class="panel"><h2>七、请你审核的点（括号里是我的默认）</h2><ol>'
         '<li>候选来源 = v4 已算出的候选并集，含备选。（是）</li>'
         '<li>裁判不看专家的任何内容，也不看图谱和组织文本。（是）</li>'
         '<li>提示词草案（第三节）：措辞、要求“每个候选各一条支持和反对”是否合适？</li>'
         '<li>易混边界说明：放入同时提到至少两个候选标签的条目。（放）</li>'
         '<li>判断标准：合并 117 条比 Direct 多答对至少 4 条，且两个模型都不低于 Direct。（阈值可改）</li>'
         '<li>只跑一次、温度 0、无效样本如实统计，不用其他方法补。（是）</li>'
         '<li>代码放 <code>versions/v5/</code>，不改 v4，结果放新目录，并先对 2 到 3 条样本做冒烟再全量。（是）</li></ol>'
         '<div class="warn">你审核通过前，我不会写流水线代码，也不会调用任何模型。</div></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>v5 设计草案（简化版）</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v5-design.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
