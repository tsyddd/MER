"""Build docs/agent-debate-survey.html: agent-debate literature survey + conditional-debate design for PPCT v3.

Static HTML with inline SVG diagrams (no scripts). The literature table is curated by hand from the
sources listed on the page; the data section (trigger rate, headroom, majority-vote baseline) is computed
from saved outputs. No model calls. Usage: python scripts/build_debate_survey.py
"""
import json
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs'
VERS = {'v2': 'gemini_graph_shared_media_v2', 'v3': 'gemini_graph_emotion_wheel_v3'}
GOLD = {}
for line in (ROOT / 'data/manifests/validation.jsonl').read_text(encoding='utf8').splitlines():
    if line.strip():
        r = json.loads(line)
        GOLD[r['id']] = r['label']


def e(s):
    return escape(str(s), quote=True)


# ---------------------------------------------------------------- SVG helpers
def svg(w, h, body, label):
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}"><defs>'
            '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0 0 L10 5 L0 10 Z" fill="#6b8179"/></marker></defs>' + body + '</svg>')


def txt(x, y, lines, cls='t', anchor='middle'):
    if isinstance(lines, str):
        lines = [lines]
    top = y - (len(lines) - 1) * 8
    return ''.join(f'<text class="{cls}" x="{x}" y="{top + i * 16 + 5}" text-anchor="{anchor}">{e(l)}</text>' for i, l in enumerate(lines))


def box(x, y, w, h, lines, cls='exist'):
    return f'<rect class="n {cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>' + txt(x + w / 2, y + h / 2, lines, 't' + (' w' if cls == 'final' else ''))


def diamond(cx, cy, hw, hh, lines, cls='gate'):
    pts = f'{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}'
    return f'<polygon class="n {cls}" points="{pts}"/>' + txt(cx, cy, lines, 't')


def arrow(pts, dashed=False):
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
    return f'<path class="a{" d" if dashed else ""}" d="{d}" marker-end="url(#ar)"/>'


def lab(x, y, s, anchor='middle', cls='l'):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{e(s)}</text>'


def d_du():
    b = box(20, 110, 110, 60, ['问题'], 'plain')
    for i, y in enumerate([40, 125, 210]):
        b += box(190, y, 150, 50, [f'Agent {i + 1}', '独立回答'], 'exist')
        b += arrow([(130, 140), (190, y + 25)]) + arrow([(340, y + 25), (400, 140)])
    b += box(400, 80, 270, 120, ['第 r 轮辩论', '每个 Agent 读到其余 Agent 的回答', '并重写自己的回答', '（论文默认 3 个 Agent × 2 轮）'], 'new')
    b += arrow([(640, 80), (640, 45), (430, 45), (430, 80)]) + lab(535, 36, '重复若干轮')
    b += box(730, 105, 220, 70, ['收敛后的共同答案', '（或多数）'], 'judge') + arrow([(670, 140), (730, 140)])
    b += lab(490, 296, '局限（论文自述）：能收敛，但可能收敛到错误答案，且模型仍很自信')
    return svg(980, 312, b, 'Du 等人的同伴辩论流程')


def d_judge():
    b = box(20, 110, 110, 60, ['问题'], 'plain')
    b += box(190, 40, 170, 60, ['辩手 A', '主张答案 1'], 'exist') + box(190, 200, 170, 60, ['辩手 B', '主张答案 2'], 'exist')
    b += arrow([(130, 130), (190, 70)]) + arrow([(130, 150), (190, 230)])
    b += arrow([(255, 100), (255, 200)]) + arrow([(295, 200), (295, 100)])
    b += lab(310, 155, '多轮针锋相对', 'start')
    b += box(500, 110, 210, 80, ['裁判', '主持辩论 · 自适应终止', '选出最终答案'], 'judge')
    b += arrow([(360, 70), (500, 140)]) + arrow([(360, 230), (500, 160)])
    b += box(780, 115, 170, 70, ['最终答案'], 'final') + arrow([(710, 150), (780, 150)])
    b += lab(490, 285, 'Liang 等（MAD）：裁判可提前终止；Khan 等：裁判是较弱的模型，只看辩论')
    return svg(980, 300, b, '辩手加裁判的辩论流程')


def d_chateval():
    b = ''
    xs = [20, 340, 660]
    titles = ['① One-by-One（轮流发言）', '② Simultaneous-Talk（同时发言）', '③ 同时发言 + Summarizer']
    for x0, t in zip(xs, titles):
        b += lab(x0, 26, t, 'start', 'l b')
        for i, n in enumerate('ABC'):
            b += box(x0 + i * 108, 50, 84, 44, [f'角色 {n}'], 'exist')
    b += arrow([(104, 72), (128, 72)]) + arrow([(212, 72), (236, 72)])
    b += lab(20, 126, '后发言者能看到前面所有人的发言', 'start')
    b += box(340, 150, 300, 44, ['共享聊天记录（同轮并发写入）'], 'plain')
    for i in range(3):
        b += arrow([(382 + i * 108, 94), (382 + i * 108, 150)])
    b += lab(340, 226, '消除发言顺序的影响', 'start')
    b += box(660, 150, 300, 44, ['Summarizer：汇总本轮发言'], 'judge')
    for i in range(3):
        b += arrow([(702 + i * 108, 94), (702 + i * 108, 150)])
    b += lab(660, 226, '摘要写回每个角色的记录', 'start')
    b += lab(20, 262, '共同点：每个角色人设不同（去掉后性能下降）；多讨论几轮没有显著提升，甚至退化', 'start', 'l b')
    return svg(980, 290, b, 'ChatEval 的三种通信策略')


def d_reconcile():
    b = ''
    for i, y in enumerate([30, 110, 190]):
        b += box(20, y, 240, 62, [f'Agent {i + 1}（不同的 LLM）', '答案 + 解释 + 置信度'], 'exist')
        b += arrow([(260, y + 31), (390, 140)])
    b += box(390, 40, 310, 200, ['Phase 2 讨论（最多 R 轮）', '每个 Agent 收到：', '(a) 上一轮各答案分组 + 解释', '(b) 各自的置信度', '(c) 能说服对方的样例', '全部一致 → 提前结束'], 'new')
    b += arrow([(670, 40), (670, 12), (420, 12), (420, 40)]) + lab(545, 8, '循环', 'middle')
    b += box(770, 90, 190, 100, ['Phase 3 团队答案', '置信度加权投票'], 'judge') + arrow([(700, 140), (770, 140)])
    b += lab(20, 278, '要点：参与者是不同的模型（异质），而不是同一个模型的多个副本', 'start', 'l b')
    return svg(980, 296, b, 'ReConcile 圆桌讨论流程')


def d_adaptive():
    b = box(20, 90, 110, 60, ['问题'], 'plain')
    b += box(180, 80, 200, 80, ['初始回答', '（多个 Agent 或单个 Agent）'], 'exist') + arrow([(130, 120), (180, 120)])
    b += diamond(520, 120, 90, 60, ['一致 / 高置信？']) + arrow([(380, 120), (430, 120)])
    b += box(700, 20, 200, 60, ['直接输出（不辩论）'], 'judge') + arrow([(520, 60), (520, 50), (700, 50)]) + lab(530, 44, '是', 'start')
    b += box(700, 160, 200, 60, ['多轮辩论'], 'new') + arrow([(520, 180), (520, 190), (700, 190)]) + lab(530, 210, '否', 'start')
    b += lab(20, 262, 'DOWN：按首轮置信度触发　　ARMOR-MAD：按辩论前的一致度路由（高一致直接通过，低一致才辩论）', 'start', 'l b')
    return svg(980, 280, b, '按需触发辩论的先例')


def d_design():
    b = box(20, 225, 150, 90, ['输入', '8 帧 + 字幕', '（+ 音轨）+ 图谱'], 'plain')
    b += lab(230, 134, 'Round 0：独立判断（现有 v3 专家）', 'start', 'l b')
    names = [('图谱专家', '读图谱 + 组织文本'), ('音频字幕专家', '偏语言与声音'), ('图像专家', '偏表情与姿态')]
    for i, (a, c) in enumerate(names):
        y = 150 + i * 90
        b += box(230, y, 180, 60, [a, c], 'exist') + arrow([(170, 270), (230, y + 30)])
        b += arrow([(410, y + 30), (462, 270)])
    b += diamond(540, 270, 78, 56, ['三个标签', '一致吗？'])
    # yes branch
    b += arrow([(540, 214), (540, 110), (660, 110)]) + lab(550, 160, '一致', 'start', 'l b')
    b += box(660, 70, 240, 80, ['不辩论', '直接采纳一致标签', '（汇总器不改答案）'], 'judge')
    b += box(940, 235, 140, 70, ['最终标签'], 'final')
    b += arrow([(900, 110), (1010, 110), (1010, 235)])
    # no branch
    b += arrow([(540, 326), (540, 470), (640, 470)]) + lab(550, 400, '不一致', 'start', 'l b')
    b += box(640, 405, 240, 130, ['辩论（最多 R = 2 轮）', '每位专家读到另两位的', '标签 + 证据 + 反证', '回看原媒体后：修订或坚持', '（须引用可核对的证据）'], 'new')
    b += diamond(975, 470, 64, 54, ['已一致？']) + arrow([(880, 470), (911, 470)])
    b += arrow([(975, 416), (975, 305)]) + lab(985, 365, '是：采纳', 'start', 'l b')
    b += arrow([(975, 524), (975, 560)]) + lab(985, 546, '否 / 达到 R 轮', 'start', 'l b')
    b += box(880, 560, 200, 62, ['汇总器（裁判）', '原媒体 + 辩论记录 → 单标签'], 'judge')
    b += arrow([(1080, 591), (1092, 591), (1092, 270), (1080, 270)])
    # legend
    b += '<rect class="n exist" x="20" y="540" width="16" height="16" rx="3"/>' + lab(44, 553, '现有（v3 已有的专家）', 'start')
    b += '<rect class="n new" x="20" y="564" width="16" height="16" rx="3"/>' + lab(44, 577, '新增（辩论）', 'start')
    b += '<rect class="n judge" x="20" y="588" width="16" height="16" rx="3"/>' + lab(44, 601, '汇总器 / 采纳', 'start')
    return svg(1100, 630, b, '按分歧触发辩论的方案')


def d_design_v2():
    """Revised flow v2 (2026-11-02): Round 0 may already give 1-2 answers when really unsure; every expert then reflects
    (always, consistent or not) and gives exactly one answer; route on consistency: consistent -> output,
    inconsistent -> debate (then summary if still inconsistent)."""
    b = lab(180, 96, '① Round 0：第一次独立判断', 'start', 'l b')
    b += lab(430, 96, '② 反思（一律进行，不管是否一致）', 'start', 'l b')
    b += lab(685, 96, '③ 路由：有共同标签吗？', 'start', 'l b')
    b += box(20, 225, 130, 80, ['输入', '8 帧 + 字幕', '（+ 音轨）+ 图谱'], 'plain')
    for name, y in [('图谱专家', 150), ('音频字幕专家', 265), ('图像专家', 380)]:
        b += box(180, y - 36, 210, 72, [name + ' · Round 0', '1 个答案；实在拿不准', '时可给 2 个答案'], 'exist') + arrow([(150, 265), (180, y)])
        b += box(430, y - 36, 235, 72, ['反思（一律进行）', '原媒体 + 自己 Round 0 的答案/理由', '→ 1～2 个答案（主答案 + 备选）'], 'new') + arrow([(390, y), (430, y)])
        b += arrow([(665, y), (685, 265)])
    b += diamond(770, 265, 85, 58, ['三位答案集合', '有共同标签吗？'])
    # consistent -> output
    b += arrow([(770, 207), (770, 70), (910, 70)]) + lab(780, 150, '恰好 1 个共同标签', 'start', 'l b')
    b += box(910, 35, 200, 70, ['直接输出', '这个共同标签'], 'judge')
    b += box(1150, 230, 130, 70, ['最终标签'], 'final')
    b += arrow([(1110, 70), (1215, 70), (1215, 230)])
    # inconsistent -> debate -> consistent? -> summary
    b += arrow([(770, 323), (770, 480), (840, 480)]) + lab(780, 405, '无共同标签，或多于 1 个', 'start', 'l b')
    b += box(840, 415, 240, 130, ['辩论（最多 R = 2 轮）', '读另两位反思后的答案、证据、反证', '回看原媒体后：修订或坚持', '结束时每位只给 1 个答案', '（须在三位候选的并集内）'], 'new')
    b += diamond(1180, 480, 60, 52, ['三个单答案', '一致吗？'])
    b += arrow([(1080, 480), (1120, 480)])
    b += arrow([(1180, 428), (1180, 300)]) + lab(1190, 372, '一致：采纳', 'start', 'l b')
    b += arrow([(1180, 532), (1180, 570)]) + lab(1190, 556, '不一致', 'start', 'l b')
    b += box(1095, 570, 170, 80, ['汇总器（裁判）', '原媒体 + 全部历史', '→ 1 个最终标签'], 'judge')
    b += arrow([(1265, 610), (1290, 610), (1290, 265), (1280, 265)])
    # candidate-set note and legend
    b += lab(180, 590, '路由：三位答案集合的交集恰好 1 个标签 → 直接输出；交集为空或多于 1 个 → 辩论（后一半为默认规则，待确认）', 'start')
    b += lab(180, 612, '辩论候选并集 = 三位 Round 0 与反思后的全部答案；辩论结束时每位只给 1 个答案', 'start')
    b += '<rect class="n exist" x="20" y="470" width="16" height="16" rx="3"/>' + lab(44, 483, '第一次独立判断', 'start')
    b += '<rect class="n new" x="20" y="494" width="16" height="16" rx="3"/>' + lab(44, 507, '新增（反思、辩论）', 'start')
    b += '<rect class="n judge" x="20" y="518" width="16" height="16" rx="3"/>' + lab(44, 531, '输出 / 汇总器', 'start')
    return svg(1300, 670, b, '修订方案 v2：第一次和反思都允许 1～2 个答案，按是否有共同标签路由')


# ---------------------------------------------------------------- data
def j(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf8'))
    except Exception:
        return None


def stats(ver, prov):
    c = Counter()
    for i, g in GOLD.items():
        f = OUT / VERS[ver] / prov / i
        es = [j(f / f'expert_{r}.json') for r in ('graph', 'audio_subtitle', 'image')]
        s = j(f / 'summary.json')
        if not s or any(x is None or 'answer' not in x for x in es):
            continue
        a = [x['answer'] for x in es]
        top = Counter(a).most_common()
        sr = s['answer'] == g
        c['n'] += 1
        c['sum'] += sr
        c['oracle'] += g in a
        c['vote'] += len(top) < 3 and top[0][0] == g
        if len(set(a)) == 1:
            c['una_ok' if a[0] == g else 'una_bad'] += 1
        else:
            c['split'] += 1
            if sr:
                c['split_ok'] += 1
            elif g in a:
                c['recov'] += 1
            else:
                c['hopeless'] += 1
    return c


def data_section():
    rows, bars = '', ''
    for ver in ('v3', 'v2'):
        for p in ('gpt', 'gemini', 'omni'):
            c = stats(ver, p)
            n = c['n']
            pc = lambda x: f'{100 * x / n:.1f}%'
            rows += (f'<tr><td>{ver}</td><td>{p}</td><td>{n}</td><td>{c["sum"]} ({pc(c["sum"])})</td><td><b>{c["vote"]} ({pc(c["vote"])})</b></td>'
                     f'<td>{c["split"]} <span class="m">({100 * c["split"] / n:.0f}%)</span></td><td>{c["una_bad"]}</td><td>{c["recov"]}</td>'
                     f'<td>{c["oracle"]} ({pc(c["oracle"])})</td></tr>')
            if ver == 'v3':
                seg = [('una_ok', '一致且对', '#2f9e7e'), ('una_bad', '一致且错', '#c9533c'), ('split_ok', '不一致 · 汇总已对', '#9fd3c1'),
                       ('recov', '不一致 · 汇总错但有专家对', '#e1a53b'), ('hopeless', '不一致 · 无人对', '#b5c3bb')]
                inner = ''.join(f'<div style="width:{100 * c[k] / n:.2f}%;background:{col}" title="{lbl}：{c[k]}">{c[k] if c[k] else ""}</div>' for k, lbl, col in seg)
                bars += f'<div class="brow"><span class="bl">{p.upper()}（{n} 条）</span><div class="stackbar">{inner}</div></div>'
    legend = ''.join(f'<span><i style="background:{col}"></i>{lbl}</span>' for _, lbl, col in [('', '一致且对', '#2f9e7e'), ('', '一致且错', '#c9533c'), ('', '不一致 · 汇总已对', '#9fd3c1'),
                                                                                               ('', '不一致 · 汇总错但有专家对（辩论的挽回空间）', '#e1a53b'), ('', '不一致 · 无人对', '#b5c3bb')])
    return rows, bars, legend


# ---------------------------------------------------------------- literature
# (title, link, venue/year, citations, kind, finding, verified, relevance)
LIT = {
    '经典辩论架构（常被引用的"标准做法"）': [
        ('Improving Factuality and Reasoning in Language Models through Multiagent Debate (Du 等)', 'https://arxiv.org/abs/2305.14325', 'ICML · 2023', 2571, '同伴辩论',
         '多个同款 Agent 先独立回答；之后每人读到其余人的回答并更新，重复若干轮（默认 3 个 Agent、2 轮）。轮数超过 4 增益持平；"更固执"的提示词让辩论更长、结果更好；局限：会收敛到错误答案且仍自信。', '正文', '你的"辩论"步骤最直接的参照'),
        ('Encouraging Divergent Thinking in LLMs through Multi-Agent Debate (Liang 等，MAD)', 'https://arxiv.org/abs/2305.19118', 'EMNLP · 2023', 1520, '辩手 + 裁判',
         '多个辩手 + 一个裁判主持辩论；需要适度的"针锋相对"和自适应终止；摘要指出若各 Agent 用不同的 LLM，裁判可能不公平。', '摘要', '对应你的"汇总器 = 裁判"'),
        ('ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate (Chan 等)', 'https://arxiv.org/abs/2308.07201', 'arXiv · 2023', 1029, '角色评审团',
         '多个人设不同的评审 Agent 讨论；三种通信方式（轮流 / 同时 / 同时 + Summarizer）；人设多样性必要；增加讨论轮数无显著提升。', '正文', '你的三位专家本来就是"不同角色"，与它同构'),
        ('ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs (Chen 等)', 'https://arxiv.org/abs/2309.13007', 'ACL · 2023', 447, '圆桌共识',
         '不同的 LLM 作为参与者；每轮收到"分组后的答案 + 置信度 + 说服性样例"；全体一致就提前结束，最多 R 轮；最终用置信度加权投票。', '正文', '"一致即停"的直接先例；强调参与者异质'),
        ('AI safety via debate (Irving 等)', 'https://arxiv.org/abs/1805.00899', 'arXiv · 2018', 513, '辩论原型',
         '辩论思想的源头：两个 Agent 轮流论证，由人来判。', '仅标题', '背景'),
        ('Debating with More Persuasive LLMs Leads to More Truthful Answers (Khan 等)', 'https://arxiv.org/abs/2402.06782', 'ICML · 2024', 345, '辩手 + 较弱裁判',
         '两位专家辩手各自论证不同答案，由信息更少的裁判选；摘要称辩论让裁判准确率达 76%（模型）和 88%（人类），朴素基线为 48% 和 60%。', '摘要', '说明"让裁判只看论证"能起作用'),
        ('Mixture-of-Agents Enhances Large Language Model Capabilities (Wang 等)', 'https://arxiv.org/abs/2406.04692', 'ICLR · 2024', 618, '分层聚合',
         '多层 Agent：上一层的输出作为下一层的参考，最后由聚合者综合。', '仅标题', '与"汇总器"的聚合思路相关，但不是辩论'),
    ],
    '质疑与基线（做之前必须读）': [
        ('Self-Consistency Improves Chain of Thought Reasoning (Wang 等)', 'https://arxiv.org/abs/2203.11171', 'ICLR · 2022', 8146, '投票基线',
         '多次采样后取多数答案，是所有辩论论文都要比较的基线。', '仅标题', '你的"三专家多数投票"就是它的变体'),
        ('Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs? (Choi 等)', 'https://arxiv.org/abs/2508.17536', 'NeurIPS · 2025', 110, '拆解分析',
         '把 MAD 拆成"多数投票"和"辩论"；七个基准上，多数投票本身就占了大部分收益；理论上辩论是 martingale，单靠辩论不提高期望正确率；有针对性地偏向"纠正"的更新才能改善。', '摘要 + 正文开头', '直接决定你的评估必须对比多数投票'),
        ('Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs (Smit 等)', 'https://arxiv.org/abs/2311.17371', 'ICML · 2023', 179, '系统比较',
         '摘要称 MAD 系统"不能稳定超过"self-consistency 等策略；对超参数很敏感；调节 Agent 之间的一致程度可显著提升。', '摘要', '提示"一致度"本身是可调旋钮'),
        ('Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Key? (Wang 等)', 'https://arxiv.org/abs/2402.18272', 'ACL · 2024', 243, '系统比较',
         '摘要称：强提示的单 Agent 几乎能达到最佳讨论方法；只有在提示里没有示例时，多 Agent 讨论才占优。', '摘要', '同上，提醒基线要强'),
        ('Stop Overvaluing Multi-Agent Debate — We Must Rethink Evaluation and Embrace Model Heterogeneity', 'https://arxiv.org/abs/2502.08788', 'arXiv · 2025', 51, '评测反思',
         '标题表明：主张重新审视评测，并强调模型的异质性。', '仅标题', '你的专家是同一模型，异质性弱'),
    ],
    '按需触发 / 提前终止（与你的方案最接近）': [
        ('Debate Only When Necessary: Adaptive Multiagent Collaboration (DOWN)', 'https://arxiv.org/abs/2504.05047', 'arXiv · 2025', 33, '按置信度触发',
         '摘要：依据首轮回答的置信度选择性启动辩论，效率最多提升 6 倍，同时保持或超过现有方法，并减轻"不必要辩论带来的错误传播"。', '摘要', '最接近"不确定才辩论"的思路'),
        ('ARMOR-MAD: Adaptive Routing for Heterogeneous Multi-Agent Debate', 'https://arxiv.org/abs/2606.13197', 'arXiv · 2026', 0, '按一致度路由',
         '检索摘要：Pre-debate Agreement Routing——高一致的样本直接通过，低一致的才进入多轮辩论；EASE 在三个 Agent 答案一致时停止。', '检索摘要（未读全文）', '与你的"一致就不辩论"同构；论文很新，引用为 0'),
        ('Multi-Agent Debate for LLM Judges with Adaptive Stability Detection', 'https://arxiv.org/abs/2510.12697', 'NeurIPS · 2025', 31, '稳定性终止',
         '检索摘要：监测评审一致性的统计量，达到稳定即提前停止，用更少轮数达到不低于固定 3 轮的准确率。', '检索摘要（未读全文）', '可借用其"何时停止"的判据'),
        ('From Debate to Decision: Conformal Social Choice for Safe Multi-Agent Deliberation', 'https://arxiv.org/abs/2604.07667', 'arXiv · 2026', 5, '风险提示',
         '摘要的核心论点："agreement is not evidence of correctness"——Agent 可能通过社会强化收敛到错误答案；提出保形预测来决定自动采纳还是升级给人。', '摘要', '正是你的盲区：一致但错，不会触发辩论'),
        ('HCP-MAD（引用 1）· Sequential Consensus / Wald-SPRT（引用 0）', 'https://arxiv.org/abs/2604.09679', 'arXiv · 2026', 1, '提前终止',
         '检索摘要：分别用僵局计数器、序贯概率比检验决定何时停止辩论。', '检索摘要（未读全文）', '太新，仅作参考'),
    ],
    '多模态 / 情绪识别中的多专家': [
        ('AutoGen-Powered Multi-Agent Framework for Interpretable Multimodal Emotion Recognition (ACM)', 'https://doi.org/10.1145/3773365.3773421', 'ACM · 2025', None, '按冲突讨论',
         '检索摘要：先各模态独立预测；若预测冲突，五个专家 Agent（文本、音频、视频、融合、问答）共享证据达成共识；去掉融合 Agent 后准确率降到 66.9%。', '检索摘要（未读全文）', '与你的场景最相近：专家不一致才讨论'),
        ('From disagreement to insight: multi-agent collaborative reasoning for multimodal emotional support conversations (MiAgent)', 'https://link.springer.com/article/10.1007/s00530-026-02385-9', 'Springer · 2026', None, '跨模态冲突裁决',
         '检索摘要：对视频、音频、文本之间的冲突建模，过滤不可靠信号；例如"强颜欢笑 + 悲伤故事"。', '检索摘要（未读全文）', '给出模态冲突的典型例子'),
        ('M3MAD-Bench: Multi-Dimensional Evaluation of Multi-Agent Debate Across Domains and Modalities', 'https://arxiv.org/abs/2601.02854', 'arXiv · 2026', 0, '多模态评测',
         '检索摘要：多视角辩论对多模态任务有提升，对单模态任务收益小甚至为负。', '检索摘要（未读全文）', '引用为 0，新论文'),
        ('DART: Leveraging Multi-Agent Disagreement for Tool Recruitment in Multimodal Reasoning', 'https://arxiv.org/abs/2512.07132', 'EACL · 2025', 8, '分歧触发工具',
         '检索摘要：视觉语言模型之间的辩论常常无效；DART 用外部工具的信息来化解分歧。', '检索摘要（未读全文）', '提示：纯语言辩论解决不了感知分歧'),
    ],
    '常被一并引用的通用多智能体框架（工具，不是辩论协议）': [
        ('AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation', 'https://arxiv.org/abs/2308.08155', 'arXiv · 2023', 3083, '对话框架', '多 Agent 对话的编程框架。', '仅标题', '实现工具'),
        ('MetaGPT: Meta Programming for Multi-Agent Collaborative Framework', 'https://arxiv.org/abs/2308.00352', 'arXiv · 2023', 2753, '角色流水线', '以软件工程角色分工的多 Agent 框架。', '仅标题', '角色分工思路'),
        ('CAMEL: Communicative Agents for "Mind" Exploration of LLM Society', 'https://arxiv.org/abs/2303.17760', 'NeurIPS · 2023', 2121, '角色扮演对话', '两个角色 Agent 自主对话完成任务。', '仅标题', '背景'),
        ('AgentVerse: Facilitating Multi-Agent Collaboration…', 'https://arxiv.org/abs/2308.10848', 'ICLR · 2023', 865, '协作框架', '招募专家并协作决策的框架。', '仅标题', '背景'),
    ],
}

CSS = '''
:root{--ink:#172c38;--muted:#607583;--paper:#f4f6f3;--line:#dce4de;--green:#137a68;--amber:#b47c20;--red:#c9533c}*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1240px;margin:auto;padding:34px 28px 70px}
.eyebrow{font-size:12px;color:var(--green);font-weight:700;letter-spacing:2px}h1{font-size:31px;margin:8px 0 6px;line-height:1.3}h2{font-size:21px;margin:0 0 8px}h3{font-size:16px;margin:22px 0 6px}
.muted{color:var(--muted)}.small{font-size:12.5px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 26px;margin-top:20px}
code{font:12.5px Consolas,monospace;background:#f1f5f1;padding:1px 5px;border-radius:4px}a{color:var(--green)}
.tldr{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}.tl{border:1px solid var(--line);border-radius:12px;padding:14px 18px;background:#fff}.tl>b:first-child{display:block;margin-bottom:4px}.tl.k{border-color:#a7cfc1;background:#eef7f1}.tl.w{border-color:#e1c48d;background:#fff8e9}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:8px 9px;border-bottom:1px solid #edf1ed;text-align:left;vertical-align:top}th{color:var(--muted);font-size:12px;font-weight:600;background:#f7f9f7}
td.c{text-align:right;font:600 13px Consolas,monospace;white-space:nowrap}.tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:12px;background:#edf3f0;color:var(--green);white-space:nowrap}.v{font-size:11.5px;color:var(--muted)}
.grp td{background:#eef2ef;font-weight:700;color:var(--ink)}.m{color:var(--muted);font-size:12px}
.fig{margin:12px 0 4px;border:1px solid var(--line);border-radius:12px;background:#fcfdfc;padding:8px}.fig svg{width:100%;height:auto;display:block}.cap{font-size:13px;color:var(--muted);margin:2px 4px 8px}
svg .n{stroke-width:1.6}svg .exist{fill:#eaf1ff;stroke:#9db2ee}svg .new{fill:#fff3da;stroke:#e1c48d}svg .judge{fill:#e6f4ee;stroke:#8cc4b0}svg .plain{fill:#f4f6f3;stroke:#c9d6cf}svg .final{fill:#172c38;stroke:#172c38}svg .gate{fill:#fff8e9;stroke:#b47c20}
svg .t{font:13px "Microsoft YaHei","Segoe UI",sans-serif;fill:#172c38}svg .t.w{fill:#fff}svg .l{font:12px "Microsoft YaHei","Segoe UI",sans-serif;fill:#607583}svg .l.b{fill:#172c38;font-weight:600}
svg .a{fill:none;stroke:#6b8179;stroke-width:1.8}svg .a.d{stroke-dasharray:6 5}
.brow{display:grid;grid-template-columns:150px 1fr;gap:10px;align-items:center;margin:8px 0}.bl{font-size:13px;font-weight:600}.stackbar{display:flex;height:30px;border-radius:6px;overflow:hidden;border:1px solid var(--line)}
.stackbar div{display:flex;align-items:center;justify-content:center;color:#fff;font:600 12px Consolas,monospace}.leg{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;color:var(--muted);margin:8px 0}.leg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-2px}
ol,ul{padding-left:22px}li{margin:5px 0}.steps li b{color:var(--green)}
.warn{margin-top:14px;padding:10px 14px;border-left:3px solid var(--amber);background:#fff8e9;font-size:13.5px}
pre{background:#f6f8f6;border:1px solid var(--line);border-radius:10px;padding:14px 18px;overflow:auto;font:13px/1.7 Consolas,"Microsoft YaHei",monospace}
@media(max-width:900px){.tldr{grid-template-columns:1fr}main{padding:20px 14px}.brow{grid-template-columns:1fr}.panel{padding:16px}}
'''


def lit_table():
    h = ('<table style="table-layout:fixed"><colgroup><col style="width:23%"><col style="width:8%"><col style="width:6%"><col style="width:9%">'
         '<col style="width:29%"><col style="width:9%"><col style="width:16%"></colgroup>'
         '<tr><th>论文</th><th>发表场所 · arXiv 年</th><th>引用量</th><th>架构</th><th>要点</th><th>我核实到什么程度</th><th>与你的方案的关系</th></tr>')
    for grp, items in LIT.items():
        h += f'<tr class="grp"><td colspan="7">{e(grp)}</td></tr>'
        for t, link, ven, cit, kind, find, ver, rel in items:
            c = f'{cit:,}' if cit is not None else '未查到'
            h += (f'<tr><td><a href="{e(link)}">{e(t)}</a></td><td class="m">{e(ven)}</td><td class="c">{c}</td><td><span class="tag">{e(kind)}</span></td>'
                  f'<td>{e(find)}</td><td class="v">{e(ver)}</td><td>{e(rel)}</td></tr>')
    return h + '</table>'


def build():
    rows, bars, legend = data_section()
    body = f'''<div class="eyebrow">AGENT DEBATE / SURVEY</div>
<h1>Agent Debate 调研，以及"一致就不辩论、不一致才辩论"的方案</h1>
<p class="muted">目标：三位专家 + 一个汇总器；三位专家意见一致就直接采纳，不一致才辩论。本页先梳理常用的辩论架构（含引用量），再画出你的方案，并用你们自己的 v3 结果估算这个方案有多大空间。</p>

<div class="tldr">
<div class="tl k"><b>① 常用架构只有三类</b>同伴辩论（Du，引用 2571）、辩手 + 裁判（Liang / Khan）、角色评审团 / 圆桌共识（ChatEval / ReConcile）。你的"三专家 + 汇总器"正好是"角色评审团 + 裁判"。</div>
<div class="tl k"><b>② "不一致才辩论"有先例</b>DOWN（按置信度触发）、ARMOR-MAD（按一致度路由）。但它们很新，引用量低（33 和 0）；高引用的经典论文都是"总是辩论"。</div>
<div class="tl w"><b>③ 必须先过的关：多数投票</b>Choi 等发现多数投票解释了 MAD 的大部分收益。你们的数据里，三专家直接投票已经<b>不低于</b>现有汇总器（v3 Gemini 59 对 56）。辩论必须超过投票才有意义。</div>
<div class="tl w"><b>④ 盲区：一致但错不会被触发</b>v3 里 GPT 有 15 条、Gemini 有 12 条是三人一致地错，"一致就不辩论"碰不到它们；文献也明确提醒"一致不等于正确"。</div>
</div>

<section class="panel"><h2>一、常用架构图</h2>
<p class="muted small">下图是我按各论文的描述整理的示意图，细节以"已读正文 / 已读摘要"标注的来源为准。</p>
<h3>1. 同伴辩论（Du 等，引用 2571）</h3><div class="fig">{d_du()}</div><p class="cap">没有裁判，所有 Agent 地位平等；每轮每人读到其余人的回答再更新。</p>
<h3>2. 辩手 + 裁判（Liang 等引用 1520；Khan 等引用 345）</h3><div class="fig">{d_judge()}</div><p class="cap">辩手持相反立场针锋相对，由裁判决定何时结束、选哪个答案。</p>
<h3>3. 角色评审团（ChatEval，引用 1029）</h3><div class="fig">{d_chateval()}</div><p class="cap">与你的专家分工最接近：角色不同，区别在于"怎么共享发言"。</p>
<h3>4. 圆桌共识（ReConcile，引用 447）</h3><div class="fig">{d_reconcile()}</div><p class="cap">一致即停，最多 R 轮，最后用置信度加权投票；参与者是不同的 LLM。</p>
<h3>5. "按需触发"的先例（DOWN、ARMOR-MAD）</h3><div class="fig">{d_adaptive()}</div><p class="cap">简单样本直接通过，只有不确定的才辩论——这是你的想法在文献里的对应。</p>
</section>

<section class="panel"><h2>二、你的方案</h2>
<div class="fig">{d_design()}</div>
<p class="cap">蓝色是现有的 v3 专家，黄色是新增的辩论，绿色是汇总器。只有三位专家的标签不一致时才进入辩论。</p>
<h3>流程（伪代码）</h3>
<pre>round0 = [expert_graph(x), expert_audio_subtitle(x), expert_image(x)]      # 现有 v3 专家，独立判断
if len({{e.label for e in round0}}) == 1:
    return round0[0].label                                                  # 一致：不辩论，直接采纳
state = round0
for r in 1..R:                                                              # R = 2
    state = [revise(e, others=[o for o in state if o is not e], media=x)    # 读到另两位的标签+证据+反证，回看原媒体，修订或坚持
             for e in state]
    if len({{e.label for e in state}}) == 1:
        return state[0].label                                               # 辩论后一致：采纳
return summary_agent(x, transcript=[round0, *rounds])                       # 仍不一致：汇总器看原媒体 + 辩论记录，给出单标签</pre>
</section>

<section class="panel"><h2>三、用你们的 v3 / v2 结果估算：这个方案有多大空间</h2>
<p class="muted small">数据来自本机保存的专家与汇总器输出；"多数投票"= 三位专家取多数（平票算错）。80 条是复用的开发集，Omni 的 v2/v3 不完整（分母为有效条数）。</p>
<div class="leg">{legend}</div>
{bars}
<table style="margin-top:16px"><tr><th>版本</th><th>模型</th><th>样本</th><th>汇总器答对</th><th>三专家多数投票答对</th><th>触发辩论（不一致）</th><th>一致且错（碰不到）</th><th>可挽回（汇总错但有专家对）</th><th>任一专家对（上限）</th></tr>{rows}</table>
<h3>怎么读这张表</h3>
<ul>
<li><b>触发率不高。</b>v3 里 GPT 只有 19%、Gemini 26% 的样本会进入辩论；Omni 高达 43%。</li>
<li><b>空间很小。</b>"可挽回"（汇总错但有专家对）只有 GPT 4 条、Gemini 7 条（80 条里）。即使辩论把这些全部救回，上限也只是"任一专家对"：GPT 60/80（75%）、Gemini 63/80（78.8%）。而多数投票已经有 57 和 59，所以<b>相对投票，辩论最多只能再多救 3 条和 4 条</b>，在 80 条里这是噪声量级。</li>
<li><b>真正的大头碰不到。</b>GPT 的 15 条、Gemini 的 12 条是"三人一致地错"，不会触发辩论。其中 7 条在 GPT 和 Gemini 里是同一批样本，它们很可能是感知或标签本身的问题，不是辩论能解决的。</li>
<li><b>汇总器目前略逊于投票。</b>三位专家一致时，汇总器从未改过答案；它的推翻都发生在 2 比 1 的分歧里：GPT 2 次、Gemini 5 次、Omni 8 次，其中多数本来是对的占 1、3、4 次。所以只要在 2 比 1 时让汇总器服从多数（即条件 B），就能不辩论地多得 GPT +1、Gemini +3、Omni +1 条。</li>
<li><b>成本估算：</b>每个触发样本额外约 3 × R 次专家调用（R = 2 时 6 次）；按 19% 到 26% 的触发率，平均每样本多约 1.1 到 1.6 次调用，对比现在每样本约 5 次。</li>
</ul></section>

<section class="panel"><h2>四、设计要点（文献 + 你们的数据，是我的建议，不是定论）</h2>
<ol class="steps">
<li><b>触发条件</b>：先用"标签不一致"，最简单，也与 ARMOR-MAD 的一致度路由对应。第二步再考虑加入"一致但证据弱 / 反证强"，类似 DOWN 的置信度触发。注意：v3 现在不输出置信度，需要新增字段。</li>
<li><b>辩论轮数</b>：R = 1 到 2。Du 的默认是 2 轮，超过 4 轮持平；ChatEval 增加讨论轮数无显著提升，甚至退化。</li>
<li><b>通信方式</b>：每位专家收到的应是"另两位的标签 + 证据 + 反证"的结构化摘要，而不是全文拼接（ReConcile 的分组摘要思路；Du 提到长辩论会让模型只关注最近的内容）。ChatEval 在其设置里发现轮流发言略优，可作为对比项。</li>
<li><b>保持角色多样</b>：ChatEval 发现去掉人设差异后性能下降。你们三位专家共享原媒体，差异本来就小，辩论时不要让他们变成同一个人。</li>
<li><b>防从众</b>：Du 观察到模型"很好说话"，更"固执"的提示让辩论更长、结果更好。提示词应要求"改变或坚持都必须引用可核对的帧号、字幕或节点"。</li>
<li><b>汇总器的角色</b>：三位专家一致时不参与；辩论后仍不一致时才作为裁判，看原媒体和辩论记录（对应 Liang / Khan 的裁判）。注意它现在在 2 比 1 分歧里偶尔推翻多数且常常推翻错，所以裁判的提示词要明确"多数不是自动胜出，也不是自动出局"，并用实验 A 与 B 的差异检验它是否真的比投票好。</li>
<li><b>感知分歧不能靠语言辩论解决</b>：DART 等工作指出视觉语言模型间的辩论常常无效。你们的专家都可回看原媒体，这是优势；但若分歧源自"没看见 / 没听见"，辩论帮助有限。</li>
</ol></section>

<section class="panel"><h2>五、最小实验方案</h2>
<table><tr><th>条件</th><th>做法</th><th>用来回答什么</th></tr>
<tr><td>A. 现状</td><td>三专家 + 汇总器</td><td>基线</td></tr>
<tr><td>B. 多数投票</td><td>不用汇总器，三专家取多数</td><td>辩论必须超过它（Choi 等的核心提醒）</td></tr>
<tr><td>C. 条件辩论 R = 1</td><td>不一致才辩论 1 轮；仍不一致由汇总器裁决</td><td>辩论本身带来多少（对比 B）</td></tr>
<tr><td>D. 条件辩论 R = 2</td><td>同上，最多 2 轮</td><td>轮数是否有收益</td></tr>
<tr><td>E. 对照：全量辩论</td><td>不论是否一致都辩论</td><td>验证"一致就不辩论"是否既省又不伤</td></tr>
<tr><td>F. 变体：辩论后仍不一致时回退</td><td>不用汇总器，改用多数 / 置信度加权（ReConcile 做法）</td><td>汇总器作为裁判是否值得</td></tr></table>
<p><b>报告什么：</b>准确率、触发率、调用次数、翻转表（答案由对变错 / 由错变对），并分别统计"一致"和"不一致"两类样本。</p>
<div class="warn"><b>数据使用：</b>80 条已被反复用于开发，只能当开发集结果。若要调提示词或轮数，应使用清单里的 train 320 条，这需要先在服务器补跑感知，有 API 费用，需要你授权。三位专家同属一个模型，错误高度相关；ReConcile 与 Choi 等的结论都提示，异质模型比同模型多副本更值得尝试。</div></section>

<section class="panel"><h2>六、引用量一览（Semantic Scholar，2026-11-02 检索）</h2>
<p class="muted small">引用量来自 Semantic Scholar 的批量接口，不同数据库数字会有差异；"我核实到什么程度"一栏如实标注：正文 = 下载了论文全文核对；摘要 = 读了 arXiv 摘要；检索摘要 = 只看到搜索结果里的概括，未读全文；仅标题 = 只用标题和引用量，没有核实内容。2026 年的论文很新，引用量天然偏低，不代表质量。</p>
{lit_table()}
</section>

<section class="panel"><h2>七、修订方案 v2（2026-11-02）：第一次允许多答案，一律反思，有共同标签则输出，否则辩论</h2>
<p class="muted">按你的最新要求重画（替代同日早些时候"Round 0 单答案 + Round 1 重判"的版本）：三位专家<b>第一次独立判断</b>时，实在拿不准就可以给 1～2 个答案；然后<b>不管是否一致，每位专家都做一次反思</b>，反思后<b>仍允许 1～2 个答案</b>；再看三位的答案集合<b>有没有共同标签</b>：有（且恰好 1 个）就直接输出，否则进入辩论；辩论结束时每位必须只给 1 个答案，三个单答案一致就采纳，仍不一致再交给汇总器。</p>
<div class="fig">{d_design_v2()}</div>
<p class="cap">蓝色是第一次独立判断，黄色是新增的反思与辩论，绿色是输出和汇总器。本图只是设计，尚未实现、未运行。</p>
<h3>每一步的输入与输出</h3>
<table><tr><th>步骤</th><th>谁</th><th>看到什么</th><th>输出什么</th></tr>
<tr><td>① Round 0 独立判断</td><td>三位专家各自独立</td><td>原媒体（8 帧、字幕、音轨）；图谱专家另有图谱与组织文本</td><td>1 个标签；实在拿不准时 2 个（主答案 + 备选，写明为什么拿不准）+ 理由与证据</td></tr>
<tr><td>② 反思（一律进行）</td><td>三位专家各自独立</td><td>原媒体 + <b>自己</b> Round 0 的答案与理由（看不到另两位）</td><td>1～2 个标签（主答案 + 备选）+ 反思说明（改了什么、为什么没改）</td></tr>
<tr><td>③ 路由</td><td>程序</td><td>三位反思后的答案集合</td><td>三个集合的<b>交集恰好 1 个标签</b> → 直接输出该标签；交集为空，或多于 1 个 → 进入辩论<span class="tag">后半为默认规则，待确认</span></td></tr>
<tr><td>辩论（≤ 2 轮）</td><td>三位专家</td><td>原媒体 + 另两位反思后的答案（含备选）、证据、反证</td><td><b>必须只有 1 个标签</b>，且在三位候选的并集内；附对另两位的回应</td></tr>
<tr><td>辩论后路由</td><td>程序</td><td>三个单答案</td><td>完全相同 → 采纳；否则交给汇总器</td></tr>
<tr><td>汇总</td><td>汇总器（裁判）</td><td>原媒体 + 三位辩论后的单答案 + 全部历史记录</td><td>1 个最终标签</td></tr></table>
<h3>示意例子（编造的过程，只用来说明格式，未运行）</h3>
<table><tr><th>步骤</th><th>图谱专家</th><th>音频字幕专家</th><th>图像专家</th><th>说明</th></tr>
<tr><td>例 1 · Round 0</td><td>surprise、angry（拿不准）</td><td>worried</td><td>worried</td><td>图谱专家给了 2 个答案</td></tr>
<tr><td>例 1 · 反思后</td><td>angry、surprise</td><td>worried、angry</td><td>worried</td><td>三个集合的交集为空 → 辩论；候选并集为 surprise、angry、worried</td></tr>
<tr><td>例 1 · 辩论后</td><td>angry</td><td>angry</td><td>angry</td><td>一致 → 采纳 angry</td></tr>
<tr><td>例 2 · 反思后</td><td>worried、angry</td><td>worried</td><td>worried</td><td>交集恰好是 worried → 直接输出 worried</td></tr>
<tr><td>例 3 · 反思后</td><td>angry、worried</td><td>worried、angry</td><td>angry、worried</td><td>交集有 2 个标签（angry、worried）→ 按默认规则进入辩论</td></tr></table>
<h3>与上一版（Round 0 单答案 + Round 1 重判）的区别</h3>
<ul><li>"允许给 1～2 个答案"现在<b>第一次独立判断和反思都有</b>；上一版的 Round 1 重判变成了反思，并且对所有样本都做。</li>
<li>路由的依据由"三个单答案是否相同"变成"三位答案集合有没有共同标签"，所以备选答案会参与路由。</li>
<li>辩论之后的处理沿用你上一轮的选择：一致就采纳，不一致才进汇总器。</li></ul>
<h3>需要留意的几点（我从设计里推出来的，不是实验结果）</h3>
<ul><li><b>第一次判断不能再直接复用已保存的 v3 专家输出</b>：v3 专家只输出单个标签，要允许 1～2 个答案，需要新版本的专家提示词，三位专家的第一次判断也要重新跑。</li>
<li><b>调用量变大</b>：每条样本固定多 3 次反思调用。80 条验证集就是多 240 次；而此前的条件辩论只对 19% 到 26% 的不一致样本多调用。进入辩论的样本还要再加辩论和汇总。</li>
<li><b>共同标签可以只靠备选"凑"出来</b>：如果三位的主答案各不相同（比如 surprise、worried、neutral），只要三人都把 angry 写成备选，交集就是 angry，会直接输出一个没有任何人当主答案的标签。这条规则比"主答案相同"宽松得多，实验时需要单独统计这类样本是否可靠。</li>
<li><b>风险</b>：如果三位都没提到真实标签，辩论无法改对（GPT 有 20 条、Gemini 有 17 条是三位专家全都没答对）。允许给 2 个答案，是为了让更多真实标签进入候选（对应发现 F1），但专家自己给的第 2 个答案是否比统计上的易混淆标签更准，需要实验才知道。</li></ul>
<div class="note"><b>已确认的设定（2026-11-02）</b>：① 反思时只看原媒体和自己 Round 0 的答案与理由；② 反思后仍允许 1～2 个答案；③ 路由的"一致"= 三位的答案集合有共同标签；④ 辩论后三位已一致就直接采纳、不一致才进汇总器；⑤ 辩论的最终答案必须从三位候选的并集里选，且每位只给 1 个。</div>
<div class="warn"><b>标了"待确认"的地方</b>：共同标签<b>有多个</b>时怎么办？我默认视为不一致、进入辩论（因为输出不唯一）。另一种做法是选"被更多专家当主答案"的那个，平票再进辩论。另外是否要求"共同标签至少是一位专家的主答案"，以避免上面说的"凑出来的标签"，也需要你定。</div>
</section>
<p class="muted small" style="margin-top:22px">由 scripts/build_debate_survey.py 生成；页面静态渲染，不依赖脚本，不调用模型。</p>'''
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Debate 调研</title><style>{CSS}</style></head><body><main>{body}</main></body></html>'


def main():
    out = ROOT / 'docs' / 'agent-debate-survey.html'
    out.write_text(build(), encoding='utf8')
    print(out, out.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
