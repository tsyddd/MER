"""Paper-style SVG figures for docs/v5-methods.html (imported by scripts/build_v5_variants_page.py).

Each figure: input panel on the left (one disagreement sample), numbered modules in the middle, output on the right.
Icons are drawn with plain SVG shapes (no fonts/emoji needed). The example is Gemini MELD/dia198_utt2 (saved v4 outputs,
abridged); v5 results are placeholders except the B0 score, which is computed by hand from the saved records.
"""
from html import escape as e

W = 1250
C_EXP = {'G': ('#4C78A8', '#DCE7F3', '图谱专家'), 'A': ('#59A14F', '#DDEFD9', '音频字幕专家'), 'I': ('#F28E2B', '#FCE3CC', '图像专家')}
C_LAB = {'neutral': ('#7F7F7F', '#EDEDED'), 'anger': ('#C0392B', '#F9DEDB'), '?': ('#B8860B', '#FFF4CC')}
NEW = ('#FFF8E6', '#C9A227')
CODE = ('#EEF2F7', '#7A8CA5')
OUT = ('#D8F3DC', '#2D6A4F')
CTRL = ('#6A4C93', '#E9E1F3')

DEFS = ('<defs>'
        '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#555"/></marker>'
        '<marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#999"/></marker>'
        '<filter id="sh" x="-5%" y="-5%" width="110%" height="115%"><feDropShadow dx="0" dy="1.2" stdDeviation="1.2" flood-opacity="0.18"/></filter>'
        '</defs>')


def tw(s, size):
    return sum(size if ord(c) > 255 else size * 0.56 for c in s)


def t(x, y, s, size=12, anchor='start', color='#222', bold=False, italic=False):
    fw = ' font-weight="700"' if bold else ''
    fs = ' font-style="italic"' if italic else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{fw}{fs}>{e(s)}</text>'


def arrow(pts, color='#555', dashed=False, width=1.8):
    d = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    dash = ' stroke-dasharray="5 4"' if dashed else ''
    mk = 'ahg' if color == '#999' else 'ah'
    return f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#{mk})"/>'


def curve(x1, y1, x2, y2, color='#555', dashed=False):
    mx = (x1 + x2) / 2
    dash = ' stroke-dasharray="5 4"' if dashed else ''
    mk = 'ahg' if color == '#999' else 'ah'
    return f'<path d="M{x1:.1f},{y1:.1f} C{mx:.1f},{y1:.1f} {mx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#{mk})"/>'


def group(x, y, w, h, title, color='#999', fill='#FCFCFC', num=None, sub=None):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{color}" stroke-width="1.4" stroke-dasharray="6 4"/>'
    tx = x + 12
    if num is not None:
        out += f'<circle cx="{x + 20}" cy="{y + 18}" r="10" fill="{color}"/>' + t(x + 20, y + 22.5, str(num), size=12, anchor='middle', color='#fff', bold=True)
        tx = x + 36
    out += t(tx, y + 23, title, size=13.5, bold=True, color='#222')
    if sub:
        out += t(tx, y + 40, sub, size=11, color='#666')
    return out


def module(x, y, w, h, fill, stroke, title=None, num=None, sub=None):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.6" filter="url(#sh)"/>'
    if title:
        tx = x + 12
        if num is not None:
            out += f'<circle cx="{x + 20}" cy="{y + 19}" r="10" fill="{stroke}"/>' + t(x + 20, y + 23.5, str(num), size=12, anchor='middle', color='#fff', bold=True)
            tx = x + 36
        out += t(tx, y + 24, title, size=13.5, bold=True)
        if sub:
            out += t(tx, y + 41, sub, size=10.5, color='#666', italic=True)
    return out


def agent(cx, cy, r, color, light, label=None, sub=None, media=False, label_side='below'):
    out = f'<line x1="{cx}" y1="{cy - r}" x2="{cx}" y2="{cy - r - 6}" stroke="{color}" stroke-width="1.6"/><circle cx="{cx}" cy="{cy - r - 7}" r="2.4" fill="{color}"/>'
    out += f'<rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r * 0.9}" rx="{r * 0.45}" fill="{light}" stroke="{color}" stroke-width="1.8"/>'
    out += f'<circle cx="{cx - r * 0.38}" cy="{cy - r * 0.15}" r="{r * 0.13}" fill="{color}"/><circle cx="{cx + r * 0.38}" cy="{cy - r * 0.15}" r="{r * 0.13}" fill="{color}"/>'
    out += f'<path d="M{cx - r * 0.35},{cy + r * 0.3} Q{cx},{cy + r * 0.52} {cx + r * 0.35},{cy + r * 0.3}" fill="none" stroke="{color}" stroke-width="1.6"/>'
    if media:
        out += film(cx + r * 0.55, cy + r * 0.35, 18, 12)
    if label and label_side == 'below':
        out += t(cx, cy + r + 15, label, size=11.5, anchor='middle', bold=True)
        if sub:
            out += t(cx, cy + r + 29, sub, size=10.5, anchor='middle', color='#555')
    elif label and label_side == 'right':
        out += t(cx + r + 8, cy + 2, label, size=11.5, bold=True)
        if sub:
            out += t(cx + r + 8, cy + 16, sub, size=10.5, color='#555')
    return out


def film(x, y, w=46, h=30):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#3A3A3A"/>'
    n = max(3, int(w / 9))
    for i in range(n):
        xx = x + 3 + i * (w - 6) / n
        out += f'<rect x="{xx:.1f}" y="{y + 2}" width="{(w - 6) / n * 0.55:.1f}" height="{h * 0.12:.1f}" fill="#fff"/>'
        out += f'<rect x="{xx:.1f}" y="{y + h - 2 - h * 0.12:.1f}" width="{(w - 6) / n * 0.55:.1f}" height="{h * 0.12:.1f}" fill="#fff"/>'
    out += f'<rect x="{x + 4}" y="{y + h * 0.25:.1f}" width="{w - 8}" height="{h * 0.5:.1f}" fill="#9EC5E8"/>'
    return out


def wave(x, y, w=46, h=24, color='#59A14F'):
    pts = []
    amps = [0.2, 0.6, 0.35, 0.9, 0.5, 0.75, 0.3, 0.55, 0.2, 0.65, 0.4, 0.15]
    for i, a in enumerate(amps):
        xx = x + i * w / (len(amps) - 1)
        pts.append(f'{xx:.1f},{y + h / 2 - a * h / 2:.1f}')
        pts.append(f'{xx:.1f},{y + h / 2 + a * h / 2:.1f}')
    return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.4"/>'


def bubble(x, y, w, h, lines, size=10.5):
    out = f'<path d="M{x + 8},{y} H{x + w - 8} Q{x + w},{y} {x + w},{y + 8} V{y + h - 8} Q{x + w},{y + h} {x + w - 8},{y + h} H{x + 22} L{x + 10},{y + h + 9} L{x + 14},{y + h} H{x + 8} Q{x},{y + h} {x},{y + h - 8} V{y + 8} Q{x},{y} {x + 8},{y} Z" fill="#fff" stroke="#888" stroke-width="1.2"/>'
    for i, ln in enumerate(lines):
        out += t(x + 7, y + 14 + i * (size + 4), ln, size=size, color='#333', italic=True)
    return out


def doc(x, y, w, h, lines, title=None, fill='#ffffff', stroke='#8a8a8a', size=10.5, fold=10):
    out = f'<path d="M{x},{y} H{x + w - fold} L{x + w},{y + fold} V{y + h} H{x} Z" fill="{fill}" stroke="{stroke}" stroke-width="1.2" filter="url(#sh)"/>'
    out += f'<path d="M{x + w - fold},{y} V{y + fold} H{x + w}" fill="none" stroke="{stroke}" stroke-width="1.2"/>'
    yy = y + 15
    if title:
        out += t(x + 7, yy, title, size=size + 0.5, bold=True)
        yy += size + 5
    for ln in lines:
        out += t(x + 7, yy, ln, size=size, color='#333')
        yy += size + 4
    return out


def chip(x, y, s, fg='#555', bg='#eee', size=10.5, anchor='start', bold=False):
    w = tw(s, size) + 12
    xx = x - w / 2 if anchor == 'middle' else x
    return (f'<rect x="{xx:.1f}" y="{y - size - 2}" width="{w:.1f}" height="{size + 7}" rx="{(size + 7) / 2:.1f}" fill="{bg}" stroke="{fg}" stroke-width="1"/>'
            + t(xx + w / 2, y + 1, s, size=size, anchor='middle', color=fg, bold=bold)), w


def label_chip(x, y, lab, anchor='start', size=10.5):
    fg, bg = C_LAB.get(lab, ('#555', '#eee'))
    return chip(x, y, lab, fg, bg, size, anchor, bold=True)[0]


def code_tag(x, y, right=None):
    s_ = '</> 程序'
    w = tw(s_, 9.5) * 1.1 + 14
    if right is not None:
        x = right - w - 10
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="17" rx="8.5" fill="{CODE[1]}"/>' + t(x + w / 2, y + 12.5, s_, size=9.5, anchor='middle', color='#fff', bold=True))


def llm_tag(x, y, s, right=None):
    w = tw(s, 9.5) * 1.1 + 14
    if right is not None:
        x = right - w - 10
    return f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="17" rx="8.5" fill="{NEW[1]}"/>' + t(x + w / 2, y + 12.5, s, size=9.5, anchor='middle', color='#fff', bold=True)


def diamond(cx, cy, rx, ry, lines, fill='#FFF8E6', stroke='#C9A227'):
    out = f'<polygon points="{cx},{cy - ry} {cx + rx},{cy} {cx},{cy + ry} {cx - rx},{cy}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
    for i, s in enumerate(lines):
        out += t(cx, cy + 4 + (i - (len(lines) - 1) / 2) * 15, s, size=11.5, anchor='middle')
    return out


def out_box(x, y, w=110, h=48, lines=('最终标签', '∈ C')):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{OUT[0]}" stroke="{OUT[1]}" stroke-width="1.8" filter="url(#sh)"/>'
    for i, s in enumerate(lines):
        out += t(x + w / 2, y + h / 2 + 5 + (i - (len(lines) - 1) / 2) * 16, s, size=12.5 if i == 0 else 11, anchor='middle', bold=(i == 0))
    return out


def svg(body, h):
    return f'<svg viewBox="0 0 {W} {h}" width="100%" role="img" font-family="Microsoft YaHei,Segoe UI,sans-serif">{DEFS}{body}</svg>'


# ------------------------------------------------------------------------------------------- shared input panel
def media_row(x, y):
    b = film(x, y, 46, 30) + t(x + 23, y + 44, '8 帧', size=10, anchor='middle', color='#555')
    b += wave(x + 56, y + 3, 40, 24) + t(x + 76, y + 44, '音轨', size=10, anchor='middle', color='#555')
    b += bubble(x + 106, y - 2, 104, 34, ['“No-no, she kicked', 'our butts…”'], size=9.5)
    b += t(x + 150, y + 44, '字幕', size=10, anchor='middle', color='#555')
    return b


def input_panel(x=14, y=40, w=236, h=360, variant='answers'):
    b = group(x, y, w, h, '输入：一条不一致样本', sub='（三位专家没有共同标签）')
    b += media_row(x + 12, y + 56)
    yy = y + 128
    if variant == 'answers':
        for i, (k, lab) in enumerate([('G', 'neutral'), ('A', 'neutral'), ('I', 'anger')]):
            c, l, name = C_EXP[k]
            cy = yy + 18 + i * 52
            b += agent(x + 30, cy, 14, c, l)
            b += t(x + 54, cy + 4, name, size=11.5, bold=True)
            b += label_chip(x + 150, cy + 4, lab)
    elif variant == 'traj':
        b += t(x + 12, yy + 6, '每位专家各轮的主答案', size=11, color='#555')
        cols = ['R0', '反思', 'v4辩论']
        for j, cname in enumerate(cols):
            b += t(x + 108 + j * 46, yy + 26, cname, size=10, anchor='middle', color='#555', bold=True)
        rows = [('G', ['neutral', 'neutral', 'neutral']), ('A', ['neutral', 'neutral', 'neutral']), ('I', ['anger', 'anger', 'neutral'])]
        for i, (k, labs) in enumerate(rows):
            c, l, name = C_EXP[k]
            cy = yy + 52 + i * 42
            b += agent(x + 28, cy, 12, c, l)
            b += t(x + 46, cy + 4, name[:2], size=10.5, bold=True)
            for j, lab in enumerate(labs):
                fg, bg = C_LAB[lab]
                b += f'<rect x="{x + 108 + j * 46 - 19}" y="{cy - 9}" width="38" height="18" rx="9" fill="{bg}" stroke="{fg}"/>' + t(x + 108 + j * 46, cy + 4, lab[:3], size=10, anchor='middle', color=fg, bold=True)
        b += t(x + 108 + 92, yy + 156, '↑ 辩论中改口', size=9.5, anchor='middle', color='#C0392B')
        b += t(x + 12, yy + 156, 'neu=neutral，ang=anger', size=9.5, color='#777')
    elif variant == 'evidence':
        cols = [('G', ['语速均匀平缓', '手势只是说明性']), ('A', ['声调起伏温和', '冷面调侃']), ('I', ['f01 食指指向', 'f01 双眉聚拢', 'No-no加重'])]
        for i, (k, evs) in enumerate(cols):
            c, l, name = C_EXP[k]
            cx = x + 40 + i * 76
            b += agent(cx, yy + 16, 12, c, l)
            b += t(cx, yy + 44, name[:2], size=10, anchor='middle', bold=True)
            for j, ev in enumerate(evs):
                b += f'<rect x="{cx - 34}" y="{yy + 54 + j * 26}" width="68" height="20" rx="4" fill="{l}" stroke="{c}"/>'
                b += t(cx, yy + 68 + j * 26, ev[:7], size=9, anchor='middle')
        b += t(x + 12, yy + 148, '每位 1–4 条证据（位置 + 观察）', size=10.5, color='#555')
    b += f'<line x1="{x + 12}" y1="{y + h - 52}" x2="{x + w - 12}" y2="{y + h - 52}" stroke="#ddd"/>'
    b += t(x + 12, y + h - 30, '候选集 C =', size=11.5, bold=True)
    b += label_chip(x + 88, y + h - 26, 'neutral') + label_chip(x + 156, y + h - 26, 'anger')
    b += t(x + 12, y + h - 10, 'Direct：anger　真实标签：anger（只用于评分）', size=9.5, color='#777')
    return b


def legend(y):
    b = ''
    items = [('agent', '大模型调用'), ('film', '附原始媒体'), ('code', '程序（不调用模型）'), ('doc', '中间产物'), ('dash', '回退 / 循环')]
    x = 18
    for kind, name in items:
        if kind == 'agent':
            b += agent(x + 10, y + 6, 8, '#666', '#eee')
        elif kind == 'film':
            b += film(x, y - 2, 22, 15)
        elif kind == 'code':
            b += code_tag(x - 8, y - 4)
            x += 40
        elif kind == 'doc':
            b += doc(x, y - 6, 18, 22, [], fold=6)
        else:
            b += arrow([(x - 4, y + 6), (x + 24, y + 6)], '#999', True)
        b += t(x + 30, y + 10, name, size=11, color='#444')
        x += 30 + tw(name, 11) + 34
    return b


# ------------------------------------------------------------------------------------------- overview
def overview_fig():
    b = ''
    b += group(14, 30, 196, 250, '视频片段')
    b += film(36, 74, 70, 44) + t(71, 136, '8 帧画面', size=11, anchor='middle', color='#555')
    b += wave(118, 82, 66, 30) + t(151, 136, '音轨', size=11, anchor='middle', color='#555')
    b += bubble(32, 158, 150, 40, ['字幕：No-no, she kicked', 'our butts…'], size=10)
    b += t(112, 236, '问：这个人此刻是什么情绪？', size=11, anchor='middle', color='#333')
    b += t(112, 254, '（6 或 7 选 1）', size=11, anchor='middle', color='#333')
    b += module(246, 30, 290, 250, '#F7F9FC', '#7A8CA5', '同一个大模型扮演 3 位专家', num=1, sub='Round 0 各自判断 → 反思一次')
    for i, k in enumerate(['G', 'A', 'I']):
        c, l, name = C_EXP[k]
        cx = 300 + i * 92
        b += agent(cx, 132, 22, c, l, name, media=True)
        b += f'<path d="M{cx + 24},{112} q16,-18 0,-34" fill="none" stroke="#999" stroke-width="1.3" stroke-dasharray="3 3"/>'
    b += t(391, 214, '每位给 1 个答案（拿不准可再给 1 个备选）', size=11, anchor='middle', color='#444')
    b += t(391, 232, '+ 带位置的证据（如 frame_01：食指指向）', size=11, anchor='middle', color='#444')
    b += t(391, 258, '反思：只看原媒体和自己上一轮的回答', size=10.5, anchor='middle', color='#777', italic=True)
    b += arrow([(210, 155), (246, 155)]) + arrow([(536, 155), (572, 155)])
    b += diamond(652, 155, 80, 52, ['三人的答案集合', '恰好有 1 个', '共同标签？'])
    b += arrow([(732, 155), (752, 155), (752, 72), (790, 72)]) + t(746, 100, '是（约 85%）', size=11, anchor='end', color='#2D6A4F', bold=True)
    b += f'<rect x="790" y="44" width="250" height="56" rx="10" fill="#F2F2F2" stroke="#8a8a8a" stroke-width="1.4"/>' + t(915, 68, '一致分支：直接输出共同标签', size=12, anchor='middle', bold=True) + t(915, 87, '答对率约 83%（不改）', size=11, anchor='middle', color='#555')
    b += arrow([(732, 155), (752, 155), (752, 232), (790, 232)]) + t(746, 226, '否（约 15%）', size=11, anchor='end', color='#C0392B', bold=True)
    b += f'<rect x="790" y="190" width="250" height="86" rx="10" fill="{NEW[0]}" stroke="{NEW[1]}" stroke-width="2"/>' + t(915, 213, '不一致分支（只在候选集 C 内选）', size=12, anchor='middle', bold=True)
    b += t(915, 234, 'v4：专家辩论 → 约等于随机', size=11, anchor='middle', color='#C0392B')
    for i, s in enumerate(['A', 'B', 'C', 'D']):
        b += f'<rect x="{812 + i * 54}" y="246" width="46" height="22" rx="6" fill="#fff" stroke="{NEW[1]}"/>' + t(835 + i * 54, 261, 'v5-' + s, size=10.5, anchor='middle', bold=True)
    b += out_box(1100, 130, 130, 56, ('最终标签', '6 或 7 选 1'))
    b += arrow([(1040, 72), (1165, 72), (1165, 130)]) + arrow([(1040, 232), (1165, 232), (1165, 186)])
    return svg(b, 300)


# ------------------------------------------------------------------------------------------- A
def fig_a():
    b = input_panel()
    # (1) anonymize
    b += module(286, 40, 210, 360, CODE[0], CODE[1], '匿名打包', 1, 'Anonymize · 每位专家各打包一次')
    b += code_tag(0, 50, right=496)
    cards = [('观点 1', ['f01 食指指向、双眉聚拢', 'No-no 加重 → anger']), ('观点 2', ['语速平缓、冷面调侃', '→ neutral']), ('观点 3', ['手势随发音、表情放松', '→ neutral'])]
    for i, (tt, ls) in enumerate(cards):
        b += doc(302, 92 + i * 68, 168, 56, ls, title=tt, size=10)
    b += t(391, 308, '随机打乱 · 去掉角色名', size=11, anchor='middle', color='#333', bold=True)
    b += t(391, 326, '不标哪一份是自己的', size=11, anchor='middle', color='#333', bold=True)
    b += t(391, 350, '（图像专家收到的池子；', size=10, anchor='middle', color='#777')
    b += t(391, 365, '观点 1 其实是它自己的）', size=10, anchor='middle', color='#777')
    b += arrow([(250, 220), (286, 220)])
    # (2) anonymous debate
    b += module(532, 40, 250, 360, NEW[0], NEW[1], '匿名辩论', 2, 'Debate · 一轮 · 三人同时')
    b += llm_tag(0, 50, 'LLM ×3', right=782)
    for i, k in enumerate(['G', 'A', 'I']):
        c, l, name = C_EXP[k]
        cy = 112 + i * 82
        b += doc(548, cy - 22, 44, 40, ['观点', '1–3'], size=9.5, fold=7)
        b += arrow([(594, cy - 2), (626, cy - 2)])
        b += agent(652, cy, 18, c, l, media=True)
        b += arrow([(676, cy - 2), (704, cy - 2)])
        b += label_chip(708, cy + 2, '?')
    b += t(657, 346, '每位：角色提示 + 原媒体 + 观点 1–3', size=10.5, anchor='middle', color='#333')
    b += t(657, 362, '→ 1 个答案 ∈ C，引用“观点k:E编号”', size=10.5, anchor='middle', color='#333')
    b += arrow([(782, 220), (812, 220)])
    # (3) decide
    b += diamond(872, 220, 60, 44, ['三人', '一致？'])
    b += arrow([(932, 220), (1110, 220)]) + t(990, 212, '是', size=11.5, color='#2D6A4F', bold=True)
    b += out_box(1110, 196)
    b += arrow([(872, 176), (872, 26), (391, 26), (391, 40)], '#999', True) + t(632, 20, '否，且只辩了 1 轮 → 第 2 轮（重新打乱，仍匿名）', size=11, anchor='middle', color='#777')
    b += arrow([(872, 264), (872, 312), (930, 312)]) + t(880, 296, '否（已 2 轮）', size=11, color='#C0392B')
    b += agent(956, 312, 18, CTRL[0], CTRL[1], media=True) + t(1000, 308, '汇总器', size=11.5, bold=True) + t(1000, 323, '（看匿名历史）', size=10, color='#555')
    b += arrow([(1080, 312), (1165, 312), (1165, 244)])
    b += f'<rect x="812" y="356" width="418" height="40" rx="8" fill="#F7F7F7" stroke="#ccc"/>' + t(824, 374, '诊断（不影响答案）：从众率 = 改成同伴上一轮答案的比例；', size=10.5, color='#444') + t(824, 389, '坚持率 = 保持自己答案的比例（先在 v4 已保存记录上计算）', size=10.5, color='#444')
    b += legend(426)
    return svg(b, 446)


# ------------------------------------------------------------------------------------------- B
def fig_b():
    b = input_panel(variant='traj')
    # (2) anti-conformity critique (B1)
    b += module(286, 40, 300, 236, NEW[0], NEW[1], '反从众批判（仅 B1）', 2, 'Critique · 一轮 · 三人同时')
    b += llm_tag(0, 50, 'LLM ×3', right=586)
    for i, k in enumerate(['G', 'A', 'I']):
        c, l, name = C_EXP[k]
        cx = 340 + i * 96
        b += agent(cx, 112, 18, c, l, media=True)
        b += f'<rect x="{cx - 38}" y="146" width="76" height="34" rx="6" fill="#fff" stroke="{c}"/>' + t(cx, 160, 'KEEP /', size=10.5, anchor='middle', bold=True) + t(cx, 174, 'REVISE (∈C)', size=10, anchor='middle', bold=True)
    b += doc(300, 194, 128, 66, ['你上一轮的答案', 'Peer #1, Peer #2', '（同伴匿名）'], title='看到', size=10)
    b += doc(440, 194, 132, 66, ['同伴可能出错：', '先指出具体错误；', '多数不算理由'], title='提示要点', size=10)
    b += arrow([(250, 200), (286, 160)])
    # B0 path
    b += arrow([(250, 300), (620, 300)], '#999', True)
    b += t(436, 318, 'B0：直接用 v4 已保存的辩论记录（0 次调用）', size=11, anchor='middle', color='#777')
    b += arrow([(586, 160), (620, 160)])
    # (3) scoring
    b += module(620, 40, 300, 360, CODE[0], CODE[1], '轨迹记分', 3, 'Score every round of every expert')
    b += code_tag(0, 50, right=920)
    rules = [('初始答案（k=0）', '+20'), ('保持原答案', '+20·f'), ('改答案：旧答案', '−25·f'), ('　　　　新答案', '+30·f')]
    for i, (a, s) in enumerate(rules):
        b += t(640, 96 + i * 21, a, size=11) + t(898, 96 + i * 21, s, size=11.5, anchor='end', bold=True)
    b += t(640, 186, 'f = 1/(k+1)：越晚的轮次权重越小', size=10.5, color='#555')
    b += f'<line x1="636" y1="200" x2="904" y2="200" stroke="#ccc"/>'
    b += t(640, 222, '示例（B0，按已保存记录手算）', size=11, bold=True, color='#8a6d00')
    for i, (lab, v) in enumerate([('neutral', 83.3), ('anger', 21.7)]):
        fg, bg = C_LAB[lab]
        y = 240 + i * 34
        b += t(640, y + 14, lab, size=11, color=fg, bold=True)
        b += f'<rect x="700" y="{y}" width="{v * 2.2:.1f}" height="20" rx="3" fill="{bg}" stroke="{fg}"/>' + t(706 + v * 2.2, y + 14, f'{v}', size=11, bold=True)
    b += t(640, 330, 'neutral = 20+20 +10+10 +6.7+6.7+10', size=10, color='#555')
    b += t(640, 346, 'anger = 20 +10 −8.3', size=10, color='#555')
    b += t(640, 372, '（只记主答案；不按人数归一化）', size=10, color='#777')
    b += arrow([(920, 220), (950, 220)])
    # (4) select
    b += diamond(1010, 220, 58, 44, ['最高分', '唯一？'])
    b += arrow([(1068, 220), (1110, 220)]) + t(1078, 212, '是', size=11.5, color='#2D6A4F', bold=True)
    b += out_box(1110, 196)
    b += arrow([(1010, 264), (1010, 318), (1050, 318)], '#999', True) + t(1018, 298, '平局', size=11, color='#777')
    b += f'<rect x="1050" y="300" width="120" height="36" rx="8" fill="#fff" stroke="#999"/>' + t(1110, 323, 'Direct 的答案', size=11, anchor='middle')
    b += arrow([(1170, 318), (1180, 318), (1180, 244)], '#999', True)
    b += t(1110, 370, '示例结果：B0 选 neutral（答错）', size=10.5, anchor='middle', color='#C0392B')
    b += legend(426)
    return svg(b, 446)


# ------------------------------------------------------------------------------------------- C
def fig_c():
    b = input_panel(variant='evidence')
    # (1)+(2) align
    b += module(286, 40, 330, 360, NEW[0], NEW[1], '对齐观察，找分歧点', 1, 'Align · 证据当作步骤，按“来源+位置”对齐')
    b += llm_tag(0, 50, 'LLM ×1 文字', right=616)
    b += f'<rect x="306" y="92" width="290" height="34" rx="8" fill="#EDEDED" stroke="#999"/>' + t(451, 106, '共同观察（不再争论）', size=11, anchor='middle', bold=True) + t(451, 120, 'f01 Joey 抬手指向同伴', size=10.5, anchor='middle', color='#444')
    for i, (where, a, bb) in enumerate([('◆ 分歧点 1：面部 f01–03', '双眉聚拢、表情严肃', '眉眼舒展、平顺'), ('◆ 分歧点 2：音轨 0–2 秒', 'No-no、kicked 急促加重', '语速均匀平缓')]):
        y = 150 + i * 112
        b += t(312, y, where, size=11.5, bold=True, color='#8a6d00')
        b += curve(330, y + 6, 360, y + 26) + curve(330, y + 6, 360, y + 66)
        b += f'<rect x="362" y="{y + 12}" width="236" height="30" rx="6" fill="#fff" stroke="#C0392B"/>' + t(370, y + 32, 'A：' + a, size=10.5) + t(592, y + 32, '→ anger', size=10.5, anchor='end', color='#C0392B', bold=True)
        b += f'<rect x="362" y="{y + 52}" width="236" height="30" rx="6" fill="#fff" stroke="#7F7F7F"/>' + t(370, y + 72, 'B：' + bb, size=10.5) + t(592, y + 72, '→ neutral', size=10.5, anchor='end', color='#7F7F7F', bold=True)
    b += t(451, 386, '源码用句向量 + 前缀树；我们的证据无先后，改为文字对齐', size=9.5, anchor='middle', color='#777', italic=True)
    b += arrow([(250, 220), (286, 220)])
    # (3) packets
    b += module(650, 40, 170, 360, CODE[0], CODE[1], '打包', 3, 'Packet · 每个分歧点一个')
    b += code_tag(0, 50, right=820)
    for i in range(2):
        b += doc(666, 92 + i * 132, 138, 112, ['共享：共同观察', '分支 A → anger', '分支 B → neutral', '（不写各有几人', '　支持）'], title=f'分歧包 {i + 1}', size=10)
    b += arrow([(616, 220), (650, 220)])
    # (4) auditor
    b += module(854, 40, 170, 360, NEW[0], NEW[1], '审计', 4, 'Audit · 每个包一次（≤3）')
    b += llm_tag(0, 50, 'LLM ×≤3', right=1024)
    for i in range(2):
        cy = 150 + i * 132
        b += agent(902, cy, 20, CTRL[0], CTRL[1], media=True)
        b += f'<circle cx="948" cy="{cy - 6}" r="9" fill="none" stroke="#444" stroke-width="2"/><line x1="954" y1="{cy}" x2="962" y2="{cy + 8}" stroke="#444" stroke-width="2.4"/>'
        b += t(939, cy + 38, '回看对应位置：A 还是 B？', size=10, anchor='middle', color='#333')
        b += label_chip(939, cy + 58, '?', anchor='middle')
        b += arrow([(820, 140 + i * 132), (878, cy)])
    # (5) vote
    b += arrow([(1024, 220), (1050, 220)])
    b += diamond(1090, 220, 40, 40, ['投票', '有胜者？'])
    b += arrow([(1130, 220), (1140, 220), (1140, 186), (1150, 186)])
    b += out_box(1140, 138, 96, 48)
    b += arrow([(1090, 260), (1090, 320), (1140, 320)], '#999', True) + t(1098, 300, '平局 / 无分歧点', size=10, color='#777')
    b += f'<rect x="1140" y="302" width="96" height="36" rx="8" fill="#fff" stroke="#999"/>' + t(1188, 325, 'Direct', size=11, anchor='middle')
    b += t(1188, 360, '胜出分支给它', size=10, anchor='middle', color='#555') + t(1188, 374, '导向的候选 1 票', size=10, anchor='middle', color='#555')
    b += legend(426)
    return svg(b, 446)


# ------------------------------------------------------------------------------------------- D
def fig_d():
    b = input_panel()
    # (1) evidence pool
    b += module(286, 40, 200, 360, CODE[0], CODE[1], '证据池', 1, 'Pool · 去掉谁说的、选了什么')
    b += code_tag(0, 50, right=486)
    b += doc(302, 92, 168, 236, ['P1 f01 右手食指指向同伴', 'P2 f01 双眉聚拢、表情严肃', 'P3 f03 快速外挥摆手', 'P4 音轨前段 No-no 加重', 'P5 音轨 语速适中、平缓', 'P6 画面 神情手势松弛', '', '只留“位置 + 观察”', '删专家名、答案、解释', '重复的合并'], title='证据池（匿名）', size=10)
    b += t(386, 348, '给取证一个起点，', size=10.5, anchor='middle', color='#555') + t(386, 364, '但不透露谁支持哪个标签', size=10.5, anchor='middle', color='#555')
    b += arrow([(250, 220), (286, 220)])
    # (2) per-candidate evidence
    b += module(520, 40, 300, 360, NEW[0], NEW[1], '逐个候选取证', 2, 'Gather · 每个候选一次，互相看不到')
    b += llm_tag(0, 50, 'LLM ×|C|', right=820)
    for i, (lab, sup, con, key) in enumerate([('anger', 'P1 P2 P4', 'P5', 'P2'), ('neutral', 'P5 P6', 'P2 P4', 'P5')]):
        cy = 140 + i * 140
        fg, bg = C_LAB[lab]
        b += agent(558, cy, 18, '#555', '#eee', media=True)
        b += t(558, cy + 36, '为', size=10.5, anchor='middle') + label_chip(558, cy + 54, lab, anchor='middle', size=10)
        b += t(558, cy + 72, '找证据', size=10.5, anchor='middle')
        b += arrow([(582, cy), (612, cy)])
        b += doc(614, cy - 40, 190, 104, [f'支持：{sup}', f'反对：{con}', f'区分点：{key}', '（可引用 P 编号，', '　也可写新的位置）'], title=f'{lab} 的证据清单', fill=bg, stroke=fg, size=10)
        b += arrow([(486, 200), (540, cy)])
    b += t(670, 386, '示例清单为示意，未运行', size=10, anchor='middle', color='#777', italic=True)
    # (3) controller
    b += module(854, 40, 230, 360, CTRL[1], CTRL[0], '控制器核对并比较', 3, 'Verify & compare')
    b += llm_tag(0, 50, 'LLM ×1', right=1084)
    b += agent(890, 114, 22, CTRL[0], CTRL[1], media=True)
    b += t(924, 108, '回到写明的位置', size=10.5) + t(924, 123, '逐条核对', size=10.5)
    hdr = ['候选', '成立', '区分', '模态', '反证']
    xs = [872, 934, 976, 1018, 1058]
    for x, h in zip(xs, hdr):
        b += t(x, 166, h, size=10, bold=True, color='#444')
    for i, lab in enumerate(['anger', 'neutral']):
        fg, bg = C_LAB[lab]
        y = 186 + i * 26
        b += t(872, y, lab, size=10.5, color=fg, bold=True)
        for x in xs[1:]:
            b += t(x + 6, y, '?', size=10.5, color='#8a6d00')
    b += f'<line x1="868" y1="236" x2="1072" y2="236" stroke="#ccc"/>'
    rules = ['只算核对成立的证据；同一事实算一次', '更看重能区分候选的证据', '覆盖的模态越多越好', '成立的强反证会削弱该候选', '差距不明显 → 写“不确定”']
    for i, r in enumerate(rules):
        b += t(870, 256 + i * 18, '· ' + r, size=10)
    b += t(969, 362, '看不到专家身份；清单顺序随机', size=10, anchor='middle', color='#555')
    b += arrow([(820, 220), (854, 220)])
    # (4) decide
    b += diamond(1132, 150, 36, 36, ['确定？'])
    b += arrow([(1084, 150), (1096, 150)])
    b += arrow([(1132, 114), (1132, 96), (1172, 96)]) + out_box(1150, 44, 86, 48)
    b += arrow([(1132, 186), (1132, 248)], '#999', True) + t(1138, 222, '不确定', size=10, color='#777')
    b += f'<rect x="1096" y="248" width="80" height="34" rx="8" fill="#fff" stroke="#999"/>' + t(1136, 270, 'Direct', size=11, anchor='middle')
    b += f'<path d="M520,412 V420 H1084 V412" fill="none" stroke="{NEW[1]}" stroke-width="1.4" stroke-dasharray="4 3"/>'
    b += t(802, 438, 'D-lite（消融）：把 ② 和 ③ 合成一次调用', size=10.5, anchor='middle', color='#8a6d00')
    b += legend(458)
    return svg(b, 478)
