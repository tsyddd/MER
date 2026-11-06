"""Build docs/v5-methods.html: v5 design draft = four separate replacements of the v4 disagreement branch, each with a
detailed architecture diagram written for readers who do not know this project:
  v5-A anonymized debate (Identity Bias, ACL 2026; refined from its official code deeplearning-wisc/MAD-identity-bias)
  v5-B Free-MAD trajectory scoring (refined from the third-party implementation jonathansantilli/freemad)
  v5-C AgentAuditor divergence audit (refined from weiyang930/AgentAuditor; idea only, the repo has no license)
  v5-D candidate-evidence controller (our own design, no source code)
Static HTML with inline SVG, no scripts, no model calls; nothing on this page has been run. The worked example uses the
saved v4 outputs of Gemini MELD/dia198_utt2 (abridged); only the v5-B0 score is computed, by hand, from those records.
Usage: python scripts/build_v5_variants_page.py
"""
import re
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIND = {  # fill, stroke, badge colour
    'input': ('#ffffff', '#6b6b6b'), 'reuse': ('#eeeeee', '#8a8a8a'), 'code': ('#e8f0fb', '#5b7fb5'),
    'llm': ('#fff3c4', '#b8860b'), 'llmm': ('#ffe2b8', '#d9780a'), 'out': ('#d8f3dc', '#2d6a4f'), 'del': ('#fdecea', '#c0392b')}
W = 1250


def t(x, y, s, size=12, anchor='start', color='#222', bold=False, italic=False):
    fw = ' font-weight="700"' if bold else ''
    fs = ' font-style="italic"' if italic else ''
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{fw}{fs}>{e(s)}</text>'


def arrow(pts, color='#444', dashed=False):
    d = ' '.join(f'{x},{y}' for x, y in pts)
    dash = ' stroke-dasharray="5 4"' if dashed else ''
    return f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.8"{dash} marker-end="url(#ah)"/>'


DEFS = '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#444"/></marker></defs>'


def text_w(s, size):
    return sum(size if ord(c) > 255 else size * 0.56 for c in s)


TOKEN = re.compile(r"[A-Za-z0-9_./:#'’\-]+|.", re.S)


def wrap(s, maxw, size):
    """Greedy wrap by display width; ASCII words are kept whole (split only if a word alone is too wide);
    continuation lines keep a leading full-width space if the original line had one."""
    if not s:
        return ['']
    indent = '　' if s.startswith('　') else ''
    out, cur = [], ''
    for tok in TOKEN.findall(s):
        if text_w(cur + tok, size) <= maxw or not cur.strip() or tok in '）)，。、；：”」':  # closing punctuation never starts a line
            if text_w(cur + tok, size) > maxw:  # a single over-long token: split by character
                for ch in tok:
                    if text_w(cur + ch, size) > maxw and cur.strip():
                        out.append(cur)
                        cur = indent
                    cur += ch
            else:
                cur += tok
        else:
            out.append(cur.rstrip())
            cur = indent + tok.lstrip()
    out.append(cur)
    return out


def step_lines(w, lines, src, size=11.5):
    body = [x for ln in lines for x in wrap(ln, w - 20, size)]
    srcl = [x for x in wrap(src, w - 20, 10)] if src else []
    return body, srcl


def body_top(w, head, badge):
    hn = len(wrap(head, w - 20, 12.5))
    return 8 + hn * 17 + (26 if badge else 8) + 14


def step_height(w, head, lines, src, badge, size=11.5):
    body, srcl = step_lines(w, lines, src, size)
    return body_top(w, head, badge) + len(body) * (size + 5.5) + (14 + len(srcl) * 14 if srcl else 4)


def step_box(x, y, w, h, kind, head, lines, src=None, badge=None, size=11.5):
    f, s = KIND[kind]
    dash = ' stroke-dasharray="6 4"' if kind == 'del' else ''
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{f}" stroke="{s}" stroke-width="1.6"{dash}/>'
    hl_ = wrap(head, w - 20, 12.5)
    for i, hl in enumerate(hl_):
        out += t(x + 10, y + 20 + i * 17, hl, size=12.5, bold=True)
    if badge:
        bw = 16 + text_w(badge, 10.5) * 1.12
        by = y + 8 + len(hl_) * 17 + 4
        out += f'<rect x="{x + w - bw - 8}" y="{by}" width="{bw}" height="18" rx="9" fill="{s}"/>' + t(x + w - bw / 2 - 8, by + 13, badge, size=10.5, anchor='middle', color='#fff', bold=True)
    body, srcl = step_lines(w, lines, src, size)
    yy = y + body_top(w, head, badge)
    for ln in body:
        out += t(x + 10, yy, ln, size=size)
        yy += size + 5.5
    if srcl:
        top = y + h - 6 - len(srcl) * 14
        out += f'<line x1="{x + 8}" y1="{top}" x2="{x + w - 8}" y2="{top}" stroke="#ccc"/>'
        for i, sl in enumerate(srcl):
            out += t(x + 10, top + 13 + i * 14, sl, size=10, color='#666', italic=True)
    return out


def ex_height(w, lines, size=11):
    return 14 + sum(len(wrap(ln, w - 16, size)) for ln in lines) * (size + 5)


def ex_box(x, y, w, h, lines, size=11):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#fbfbf7" stroke="#b9b29c" stroke-dasharray="4 3"/>'
    yy = y + 17
    for ln in lines:
        for x2 in wrap(ln, w - 16, size):
            out += t(x + 8, yy, x2, size=size, color='#333')
            yy += size + 5
    return out


def method_fig(title, cols, examples, footer, loop=None):
    """cols: list of (kind, head, lines, src, badge); examples: list of line lists (same length as cols or None)."""
    n = len(cols)
    gap = 24
    x0 = 14
    weights = [0.86 if k == 'input' else 0.62 if k == 'out' else 1.0 for k, *_ in cols]
    unit = (W - 2 * x0 - gap * (n - 1)) / sum(weights)
    widths = [unit * wt for wt in weights]
    xs = [x0 + sum(widths[:i]) + gap * i for i in range(n)]
    step_h = max(step_height(w, c[1], c[2], c[3], c[4]) for w, c in zip(widths, cols)) + 6
    ex_h = max((ex_height(w, ex) for w, ex in zip(widths, examples) if ex), default=0) + 6
    b = DEFS
    for i, ln in enumerate(wrap(title, W - 40, 15)):
        b += t(14, 24 + i * 20, ln, size=15, bold=True, color='#5a4500')
    y = 40
    for i, (kind, head, lines, src, badge) in enumerate(cols):
        b += step_box(xs[i], y, widths[i], step_h, kind, head, lines, src, badge)
        if i < n - 1:
            b += arrow([(xs[i] + widths[i], y + 40), (xs[i + 1], y + 40)])
    extra = 0
    if loop:
        b += loop(xs, widths, y, step_h)
        extra = 26
    ey = y + step_h + 36 + extra
    b += t(14, ey - 10, '示例：MELD/dia198_utt2（Gemini；内容节选自已保存的 v4 输出；v5 的结果栏是示意，尚未运行）', size=12, color='#8a6d00', bold=True)
    for i, ex in enumerate(examples):
        if ex:
            b += ex_box(xs[i], ey, widths[i], ex_h, ex)
    fy = ey + ex_h + 24
    k = 0
    for ln in footer:
        for x2 in wrap(ln, W - 30, 12.5):
            b += t(14, fy + k * 19, x2, size=12.5, color='#333')
            k += 1
    lg = fy + k * 19 + 8
    for i, (kk, name) in enumerate([('reuse', '沿用 v4 已保存的输出'), ('code', '程序（不调用模型）'), ('llm', '大模型调用（不看媒体）'), ('llmm', '大模型调用（看原始媒体）'), ('out', '输出')]):
        f, s = KIND[kk]
        xx = 14 + i * 236
        b += f'<rect x="{xx}" y="{lg}" width="16" height="16" rx="3" fill="{f}" stroke="{s}"/>' + t(xx + 22, lg + 13, name, size=12)
    return f'<svg viewBox="0 0 {W} {lg + 30}" width="100%" role="img" font-family="Microsoft YaHei,sans-serif">{b}</svg>'


# ---------------------------------------------------------------------------------------------------------- overview
def overview_fig():
    b = DEFS + t(18, 24, '整体流程：一段视频 → 三位专家 → 一致就输出，不一致才进入 v5', size=15, bold=True)
    b += step_box(18, 42, 190, 172, 'input', '① 输入：一段短视频', ['8 张按时间排列的画面', '字幕（说话内容）', '音轨（GPT 没有音轨）', '要回答：画面里这个人', '现在是什么情绪？', '从 6 或 7 个标签里选 1 个'])
    b += step_box(236, 42, 230, 172, 'reuse', '② 三位“专家”各自判断', ['同一个大模型，扮演 3 个角色：', '· 图谱专家（看事件关系图）', '· 音频字幕专家（看说话与语气）', '· 图像专家（看表情与动作）', '每位给 1 个答案（拿不准可再给', '1 个备选）＋带位置的证据'], badge='LLM×3')
    b += step_box(494, 42, 170, 172, 'reuse', '③ 反思', ['每位专家只看原始', '视频和自己上一轮', '的回答，检查一遍', '（实际几乎不改答案）'], badge='LLM×3')
    b += f'<polygon points="780,50 870,117 780,184 690,117" fill="#fff8e6" stroke="#b8860b" stroke-width="1.6"/>'
    b += t(780, 110, '三人的答案有没有', size=12, anchor='middle') + t(780, 128, '恰好 1 个共同标签？', size=12, anchor='middle')
    b += step_box(906, 42, 150, 70, 'reuse', '有 → 直接输出', ['约 85% 的样本', '（一致分支，不改）'])
    b += step_box(1086, 52, 146, 50, 'out', '最终标签', [])
    b += step_box(906, 140, 326, 64, 'llmm', '没有 → 不一致分支（约 15%）', ['v4：专家辩论；v5：换成下面四种方法之一'])
    b += arrow([(208, 117), (236, 117)]) + arrow([(466, 117), (494, 117)]) + arrow([(664, 117), (690, 117)])
    b += arrow([(870, 117), (888, 117), (888, 77), (906, 77)]) + arrow([(870, 117), (888, 117), (888, 172), (906, 172)])
    b += arrow([(1056, 77), (1086, 77)]) + arrow([(1159, 140), (1159, 102)])
    b += t(18, 246, '名词：', size=12.5, bold=True)
    terms = ['候选集 C：三位专家在 ② 和 ③ 里提到过的全部标签（含备选），通常只有 2 个，例如 {neutral, anger}。不一致分支只在 C 里选。',
             '证据：专家写下的、能在视频里定位的观察，例如“frame_01（0.58 秒）右手食指指向同伴”。每条有来源（画面 / 音频 / 字幕 / 图谱）和位置。',
             'Direct：不经过专家，直接让大模型看视频回答一次。它在不一致分支里比 v4 的辩论准（Gemini 38/62 对 26/62，GPT 26/55 对 19/55），所以作为对照和兜底。',
             '辩论（v4）：三位专家互相看到对方的答案和理由，最多 2 轮，三人一致就采纳，否则交给“汇总器”裁决。问题是少数派几乎总是改投多数（13/13、6/7），选得约等于随机。']
    for i, s in enumerate(terms):
        b += t(30, 268 + i * 21, '· ' + s, size=12.5)
    return f'<svg viewBox="0 0 {W} 360" width="100%" role="img" font-family="Microsoft YaHei,sans-serif">{b}</svg>'


EX_HEAD = ['字幕：“No-no, she kicked our butts. You could be on the Olympic standing-there team.”',
           '图谱专家：neutral（平常平稳）', '音频字幕专家：neutral（平常调侃）', '图像专家：anger（恼火反驳）',
           '候选集 C = {neutral, anger}', 'Direct 的答案：anger', '真实标签：anger（只用于事后评分）']


# ---------------------------------------------------------------------------------------------------------- A
def fig_a():
    cols = [
        ('input', '输入：一条不一致样本', ['· 原始媒体（8 帧、字幕、音轨）', '· 候选集 C', '· 三位专家反思后的输出', '　（答案、理由、证据）', '· 每位专家自己的角色提示词', '　（规则不变）'], None, None),
        ('code', '① 匿名打包', ['对每位专家分别打包：', '· 自己的 + 另两位的输出放进', '　同一个池子，共 3 份', '· 删掉角色名、专家答案前缀；', '　证据编号 image:E2 → 观点k:E2', '· 随机打乱顺序，编为', '　“观点1 / 观点2 / 观点3”', '· 不标出哪一份是自己的', '· 每位专家、每一轮都重新打乱'], '源码：debate/prompts.py · build_anonymized_prompt', '代码'),
        ('llmm', '② 匿名辩论（一轮）', ['三位专家同时各调用一次：', '输入 = 角色提示词 + 原始媒体', '　+ C + 观点1–3', '要求：参考这些观点，给出更新', '后的 1 个答案（只能在 C 里），', '改答案要引用“观点k:E编号”，', '并写出在媒体里核对到了什么', '（其余格式与 v4 辩论相同）'], '源码：debate/runner.py · _build_round_messages', 'LLM×3·看媒体'),
        ('code', '③ 判定', ['三个答案一致 → 采纳', '不一致且只辩了 1 轮', '　→ 回到 ① 再来一轮', '　（重新打乱、仍匿名）', '辩了 2 轮仍不一致', '　→ 汇总器（看到的历史', '　　也是匿名的）', '注：源码最后用多数投票；', '我们沿用 v4 的规则'], '源码：debate/evaluator.py（多数投票）', '代码'),
        ('out', '输出', ['最终标签（C 内）', '', '诊断（不影响答案）：', '从众率 Conformity', '坚持率 Obstinacy', '（定义见下表，', '　源码 debate/metrics.py）'], None, None),
    ]
    def loop(xs, widths, y, h):
        xj = xs[3] + widths[3] / 2
        xp = xs[1] + widths[1] / 2
        return arrow([(xj, y + h), (xj, y + h + 20), (xp, y + h + 20), (xp, y + h)], '#888', True) + t((xj + xp) / 2, y + h + 16, '不一致 → 第 2 轮（最多 2 轮，重新打乱）', size=11.5, anchor='middle', color='#666')
    ex = [EX_HEAD,
          ['图像专家收到的池子（顺序随机）：', '观点1：“frame_01 右手食指指向', '　同伴、双眉聚拢；No-no 和', '　kicked 急促加重 → anger”', '观点2：“语速适中、声调平缓，', '　冷面调侃 → neutral”', '观点3：“手势随发音、表情放松', '　→ neutral”', '（观点1 其实是它自己的）'],
          ['v4 里图像专家看到“另两位都', '说 neutral”后改口为 neutral，', '并写“重新听取音轨，语速均匀', '平缓”。', '匿名后它不知道哪份是自己的，', '只看到“2 份 neutral、1 份', 'anger”——多数仍然可见。', '结果：未运行。'],
          ['若三人一致 → 采纳；', '否则第 2 轮或汇总器。'],
          ['（未运行）']]
    foot = ['为什么：论文把辩论建模为“按身份加权”的更新，发现 agent 更多是顺从同伴（sycophancy），而不是偏爱自己；去掉“这是我的 / 这是别人的”这一信息，就只能按内容判断。',
            '我们的担心：我们的少数派是被“多数”拉走，而匿名后多数仍然看得见；另外内容本身会泄露身份（图谱专家会引用 person_1 之类的节点，图像专家多写 frame）。',
            '新增调用：与 v4 辩论相同，每个不一致样本每轮 3 次，最多 2 轮，仍不一致再加 1 次汇总器。']
    return method_fig('v5-A 匿名化辩论：辩论照旧，但看不出哪份观点是谁的（依据官方源码细化）', cols, ex, foot, loop=loop)


# ---------------------------------------------------------------------------------------------------------- B
def fig_b():
    cols = [
        ('reuse', '输入：三位专家的轨迹', ['每位专家在各轮的主答案：', 'k=0 Round 0', 'k=1 反思', 'k=2,3 辩论（B0 用 v4 已有的', '　普通辩论；B1 换成 ②）', '', '只记主答案；备选只用于', '组成候选集，不参与记分'], None, None),
        ('code', '① 记初始分（k=0）', ['每位专家的 Round 0 主答案', '　+w1·f', 'f = 1/(k+1) 是轮次衰减，', '　k=0 时 f=1', 'w = (w1,w2,w3,w4)', '　= (20, 25, 30, 20)'], '源码：scoring/scorer.py · record_initial', '代码'),
        ('llmm', '② 反从众批判（仅 B1，一轮）', ['三位专家同时各调用一次：', '看到自己的上一轮答案和', '匿名的同伴答案“Peer #k”', '提示：同伴可能出错，先找出', '同伴推理里的具体错误；', '输出 DECISION: KEEP 或', 'REVISE（新答案限 C 内）', '+ 理由，引用 Peer #k'], '源码：prompts/templates.py · build_critique_prompt', 'LLM×3·看媒体'),
        ('code', '③ 逐轮记分（k≥1）', ['每位专家每一轮：', '保持原答案 → 该答案 +w4·f', '改答案 → 旧答案 −w2·f，', '　　　　　新答案 +w3·f', '（反思和每轮辩论都按这个记）', '源码另有“按支持人数归一化”', '的选项（默认开），论文算法', '没有；我们按论文，不归一化'], '源码：scorer.py · record_keep / record_change', '代码'),
        ('code', '④ 选答案', ['总分最高的标签即最终答案，', '不要求三人一致', '平局：源码按校验器置信度，', '　再按字母序；我们没有校验', '　器 → 若 Direct 的答案在', '　平局里就用它，否则按字母', '　序并标记为“平局”'], '源码：orchestrator.py · AnswerSelector.select', '代码'),
        ('out', '输出', ['最终标签（C 内）', '', 'B0：零成本，直接用', 'v4 已保存的记录记分', 'B1：新跑一轮反从众', '批判后再记分'], None, None),
    ]
    ex = [EX_HEAD,
          ['k=0（f=1）：', '图谱 neutral +20', '音频字幕 neutral +20', '图像 anger +20', '→ neutral 40，anger 20'],
          ['B1 示意（未运行）：', '图像专家被要求先指出', '“两份 neutral 观点”里的', '具体错误，只有明确发现', '自己错了才改。'],
          ['B0 按已保存记录算（已核对）：', 'k=1 反思都保持（f=1/2）：', '　neutral 40+10+10=60', '　anger 20+10=30', 'k=2 v4 辩论（f=1/3）：', '　图谱、音频保持：neutral +6.7×2', '　图像 anger→neutral：', '　anger −8.3，neutral +10'],
          ['B0：neutral 83.3，anger 21.7', '→ 选 neutral（答错）', 'B0 和 v4 一样，因为三位', '专家的记录本身都偏向', 'neutral；B1 能否改变要', '看运行结果。'],
          ['B0 结果：neutral', 'B1：未运行']]
    foot = ['为什么：v4 只看最后一轮是否一致；Free-MAD 不要求一致，而是看一个答案在整个过程中被保持、被放弃、被采纳的记录——被放弃会扣分，最初的立场不会被抹掉；反从众提示用来减少无依据的改口。',
            '说明：这个仓库是第三方按论文算法写的实现（维护者不在论文作者里）。论文的 c / n 两个变体由实验者选择：B0 相当于 c（普通辩论 + 记分），B1 相当于 n（反从众辩论 + 记分）。',
            '新增调用：B0 无；B1 每个不一致样本 3 次（一轮），117 条约 351 次。']
    return method_fig('v5-B Free-MAD：不要求一致，按整条轨迹给每个标签记分（依据第三方实现细化）', cols, ex, foot)


# ---------------------------------------------------------------------------------------------------------- C
def fig_c():
    cols = [
        ('input', '输入：一条不一致样本', ['· 三位专家反思后的输出：', '　每位 1–4 条证据，每条有', '　来源、位置、观察、解释', '　+ 最终答案', '· 候选集 C', '· 原始媒体', '· Direct 的答案（只用于兜底）'], None, None),
        ('code', '① 拆成“推理步骤”', ['源码：把每个 agent 的推理', '拆成一步一步（一步 = 一个', '论断或计算），末尾加', '“[FINAL_ANSWER] 答案”', '我们：专家的证据本来就是', '一条条的，直接当作步骤：', '“位置：观察”+ 最终答案'], '源码：core/splitters.py', '代码'),
        ('llm', '② 合并相同的观察', ['源码：逐步做句向量，与已有', '节点余弦相似 ≥0.82 就合并，', '否则开新分支 → 前缀树；', '每个节点记下“哪些 agent 经过”', '我们：证据没有先后顺序，前缀', '树不适用；改为一次文字调用，', '按“来源+位置”对齐，分成', '共同观察 / 分歧点 / 独有论断'], '源码：core/trie.py · insert_trace', 'LLM×1·文字'),
        ('code', '③ 为每个分歧点打包', ['源码：共享上下文（前缀最后', '5 步）+ 每个分支后续 3 步', '+ 支持人数 + 答案分布', '（标注“仅供参考”）', '我们：共享上下文 = 共同观察；', '每个分支 = 该位置的一种描述', '+ 它导向的候选标签；默认不给', '支持人数（避免多数拉力）'], '源码：core/packets.py · build_packets', '代码'),
        ('llmm', '④ 逐个分歧点审计', ['每个分歧点调用一次（最多 3）', '源码评判：按过程质量而非人气，', '看事实、逻辑、约束、假设等，', '输出 JSON：胜出分支、置信度、', '是否有致命错误、理由', '我们加：必须回到媒体的对应', '位置核对，判断哪个描述与', '媒体吻合'], '源码：core/auditor.py · _build_prompt', 'LLM×≤3·看媒体'),
        ('code', '⑤ 得出答案', ['源码：沿树往下，每个分歧点', '走胜出分支，最后取该子树的', '最终答案；胜出无效时取答案', '最一致的分支', '我们：每个胜出分支给它导向的', '候选 1 票，票多者胜；平局或', '没有分歧点 → Direct'], '源码：core/adjudicator.py · adjudicate', '代码'),
    ]
    ex = [EX_HEAD,
          ['图像专家的步骤：', 'frame_01：食指指向、双眉聚拢', 'frame_03：快速外挥摆手', '音轨前段：No-no、kicked 加重', '→ anger', '音频字幕专家的步骤：', '音轨：语速适中、声调平缓', '画面：神情与手势自然 → neutral'],
          ['共同观察：', 'frame_01 Joey 抬手指向同伴', '分歧点 1（frame_01–03 面部）：', '　“双眉聚拢、表情严肃”', '　vs “眉眼舒展、平顺”', '分歧点 2（音轨 0–2 秒）：', '　“急促加重”vs“语速平缓”'],
          ['分歧点 1 的包：', '共享：Joey 抬手指向同伴', '分支 A：双眉聚拢 → anger', '分支 B：眉眼舒展 → neutral', '（不写 A 有 1 人、B 有 2 人）'],
          ['审计员回看 frame_01–03 和', '音轨 0–2 秒，逐个分歧点', '判断 A 还是 B 与媒体吻合。', '结果：未运行。'],
          ['两个分歧点各投 1 票；', '若一胜一负 → 平局 →', '用 Direct（anger）。', '结果：未运行。']]
    foot = ['为什么：v4 的辩论在“标签”上争论，并用语言复述对方的观察；这里只把真正有分歧的观察拿出来，让审计员回到媒体对应位置核对，共同的观察不再争论。',
            '不借用：ACPO 偏好训练（不训练）、多分支束搜索、“推翻多数守卫”（源码 guards.py 用文字规则判断多数的推理是否没写完、是否自认出错，针对数学题，不适用）。仓库没有许可证，只借思路，不复制代码。',
            '新增调用：每个不一致样本 1 次对齐 + 每个分歧点 1 次审计（最多 3），即 2–4 次，117 条约 234–468 次。论文的任务是文本推理，感知证据是否适用要靠实验。']
    return method_fig('v5-C AgentAuditor：只在专家有分歧的观察上回看媒体核对（依据源码细化）', cols, ex, foot)


# ---------------------------------------------------------------------------------------------------------- D
def fig_d():
    cols = [
        ('input', '输入：一条不一致样本', ['· 候选集 C（通常 2 个）', '· 原始媒体', '· 三位专家写下的证据', '· 本数据集情绪轮里与 C 相关', '　的易混边界说明', '· Direct 的答案（只用于兜底）'], None, None),
        ('code', '① 整理证据池', ['把三位专家的证据合在一起：', '· 只保留“位置 + 观察”', '· 删掉专家名、专家的答案和', '　“这说明什么”的解释', '· 重复的合并，编号 P1, P2…', '为了：给取证一个起点，但不', '透露谁支持哪个标签'], '我们的设计（无源码）', '代码'),
        ('llmm', '② 逐个候选取证', ['控制器为 C 里每个标签各派一次', '调用，互相看不到：', '“请在媒体里为标签 X 找证据”', '· 支持 X 的证据（引用 P 编号', '　或新的位置）', '· 反对 X 的证据', '· 哪条能把 X 和其他候选区分开', '每条都要写位置'], '我们的设计（无源码）', 'LLM×|C|·看媒体'),
        ('llmm', '③ 控制器核对并比较', ['控制器看到：媒体 + C + 各候选', '的证据清单（顺序随机，不知', '道来自哪位专家）', 'a. 逐条回看位置，标记成立 /', '　不成立 / 无法核对', 'b. 每个候选：成立且有区分力的', '　支持证据有几条、覆盖几种', '　模态、最强反证是否成立', 'c. 选证据更充分的；差距不明显', '　就写“不确定”'], '我们的设计（无源码）', 'LLM×1·看媒体'),
        ('code', '④ 决定', ['控制器选出的候选 → 输出', '“不确定” → 用 Direct 的答案', '　（它在 C 内时）', '', '消融 D-lite：把 ② 和 ③ 合成', '一次调用（即上一版的“候选', '内对比裁决”），看分开取证', '是否有必要'], '我们的设计（无源码）', '代码'),
        ('out', '输出', ['最终标签（C 内）', '+ 每个候选的证据表', '（成立 / 不成立）', '便于人工抽查'], None, None),
    ]
    ex = [EX_HEAD,
          ['P1 frame_01：右手食指指向同伴', 'P2 frame_01：双眉聚拢、表情严肃', 'P3 frame_03：快速外挥摆手', 'P4 音轨前段：No-no、kicked 加重', 'P5 音轨：语速适中、声调平缓', 'P6 画面：神情与手势自然松弛', '（不写 P2 来自图像专家）'],
          ['为 anger 取证：支持 P1、P2、', 'P4；反对 P5；区分点 P2', '为 neutral 取证：支持 P5、', 'P6；反对 P2、P4；区分点 P5', '（示意，未运行）'],
          ['控制器回看 frame_01–03 和', '音轨 0–2 秒：', 'P2 成立吗？P5 成立吗？', '再比较两边成立的、有区分力', '的证据。', '结果：未运行。'],
          ['若控制器写“不确定”→', '用 Direct 的 anger。'],
          ['（未运行）']]
    foot = ['为什么：v4 里专家是在为“自己已经选的标签”辩护，并且看得到多数；这里改成按候选取证——每个候选都有同等机会被找证据，然后由一个看不到专家身份的控制器回到媒体核对证据，按证据充分度选择。',
            '与 C 的区别：C 只处理专家已经写下的分歧观察；D 允许为每个候选重新在媒体里找证据（可以引用证据池，也可以写新的位置）。',
            '新增调用：每个不一致样本 |C| 次取证 + 1 次控制器，即 3–4 次（|C| 平均约 2.3），117 条约 390 次。']
    return method_fig('v5-D 候选取证控制器：为每个候选分别找证据，再由控制器核对、按证据充分度选（我们的设计）', cols, ex, foot)


# ---------------------------------------------------------------------------------------------------------- page
# Paper-style figures (replace the step-box figures above, which are kept only as a fallback).
import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_paper_figs import overview_fig, fig_a, fig_b, fig_c, fig_d  # noqa: E402,F811

css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1260px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}
h1{font-size:25px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:16px 0 6px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 16px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:5px 8px;text-align:left;vertical-align:top}th{background:#eef}
.muted{color:#666}.small{font-size:13px}.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}
.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}code{background:#eee;padding:0 4px;border-radius:3px}
.fig{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px;margin:10px 0}.cap{font-size:14px;color:#333;margin:4px 6px 12px;line-height:1.7}'''

P = []
P.append('<h1>v5 设计草案：用四种方法替换 v4 的不一致分支</h1>')
P.append('<p class="muted">日期 2026-11-03。<b>设计草案，尚未实现、未运行，没有任何 v5 结果。</b>四个方法互相独立，都只替换 v4 的“不一致分支”（三位专家没有共同标签时的辩论），其余沿用 v4 已保存的输出。A、B、C 依据公开源码细化（我读了源码，没有运行），D 是我们自己的设计。示例样本的内容节选自已保存的 v4 输出；唯一算出数字的是 v5-B0（用已保存的记录按规则手算，没有调用模型）。</p>')

P.append('<section class="panel"><h2>零、给不熟悉这项工作的读者：任务与流程</h2><div class="fig">' + overview_fig() + '</div><p class="cap"><b>图 0　整体流程。</b>同一个大模型扮演三位专家，各自判断并反思一次；三人的答案集合恰好有一个共同标签时直接输出（约 85% 的样本），否则进入不一致分支。v5 只替换不一致分支，四种方法（A–D）互相独立。</p>'
         '<p>任务是多模态情绪识别：给一段几秒的视频（画面、字幕、声音），判断指定人物此刻的情绪，从数据集规定的标签里选一个（MER2024 有 6 个：happy、angry、sad、worried、surprise、neutral；MELD 有 7 个：joy、anger、sadness、fear、disgust、surprise、neutral）。这里不训练任何模型，全部靠调用现成的大模型（GPT 或 Gemini）。</p>'
         '<p>v4 的做法：让同一个大模型扮演三位专家各自判断，再各自反思一次；如果三人的答案里恰好有一个共同标签，就直接输出（约 85% 的样本，答对率约 83%）；否则进入<b>不一致分支</b>（约 15%），v4 在这里让专家辩论。不一致分支是全流程最弱的一块：400 条样本里 Gemini 答对 26/62、GPT 19/55，约等于在候选里随机选（期望 25.6、22.8），而不经过专家的 Direct 答对 38 和 26。<b>v5 只改这一块。</b></p></section>')

P.append('<section class="panel"><h2>一、v5-A：匿名化辩论</h2><div class="fig">' + fig_a() + '</div><p class="cap"><b>图 1　v5-A 匿名化辩论。</b>①每位专家收到的三份观点（含它自己的）被去掉角色名、随机打乱、不标出哪份是自己的；②三位专家同时看原媒体和匿名观点，各给一个候选内的答案；③三人一致就采纳，否则重新打乱再辩一轮，两轮后仍不一致交给汇总器。其余规则与 v4 相同，因此与 v4 的差别只有“匿名”。</p>'
         '<table><tr><th>项目</th><th>内容</th></tr>'
         '<tr><td>论文与源码</td><td>When Identity Skews Debate: Anonymization for Bias-Reduced Multi-Agent Reasoning（ACL 2026 Long，Choi、Zhu、Li）。官方仓库 deeplearning-wisc/MAD-identity-bias（MIT）。</td></tr>'
         '<tr><td>源码里的做法</td><td><code>build_vanilla_prompt</code>：自己的回答写成“This was your most recent opinion”，同伴写成“Agent Opinion 1”。<code>build_anonymized_prompt</code>：把自己的和同伴的回答放进同一个列表、随机打乱，都写成“Agent Opinion 1 / 2”，不再区分自己与同伴。拓扑是单个同伴的环（agent i 只看 agent i+1），所有 agent 同时更新，最后对各 agent 的答案做多数投票（平票随机）。</td></tr>'
         '<tr><td>我们的适配</td><td>三位专家每人看到全部 3 份（自己 + 两位同伴），去掉角色名和证据前缀后随机编为观点1–3；每位专家、每一轮都重新打乱；汇总器的历史同样匿名。终止与汇总沿用 v4（一致才采纳，最多 2 轮，否则汇总器），这样与 v4 的差别只有“匿名”。</td></tr>'
         '<tr><td>诊断指标（源码 debate/metrics.py）</td><td>只看“自己上一轮与同伴不同”的情况：从众率 Conformity = P[本轮答案 = 同伴上一轮答案]；坚持率 Obstinacy = P[本轮答案 = 自己上一轮答案]；Δ = 从众率 − 坚持率；身份偏差系数 IBC = Δ(普通) − Δ(匿名)。源码是单个同伴，我们有两个同伴，定义为“本轮答案等于某位与自己不同的同伴的上一轮答案”。先在 v4 已保存的辩论记录上算普通版的 Δ（零成本）。</td></tr>'
         '<tr><td>风险</td><td>匿名后“多数”仍然看得见；回答的内容会暴露身份（图谱专家引用节点 ID，图像专家多写帧号）。</td></tr></table></section>')

P.append('<section class="panel"><h2>二、v5-B：Free-MAD（轨迹记分）</h2><div class="fig">' + fig_b() + '</div><p class="cap"><b>图 2　v5-B Free-MAD 轨迹记分。</b>不要求三人一致，而是把每位专家在每一轮的答案按“初始、保持、改口”加减分，取总分最高的标签；平局时用 Direct。B0 直接对 v4 已保存的辩论记录记分（零成本）；B1 先跑一轮反从众批判（同伴匿名，提示“先挑错，多数不算理由”）再记分。右侧数字是示例样本按已保存记录手算的 B0 结果。</p>'
         '<table><tr><th>项目</th><th>内容</th></tr>'
         '<tr><td>论文与源码</td><td>Free-MAD: Consensus-Free Multi-Agent Debate（arXiv 2509.11035；页面标注 Findings of ACL 2026）。仓库 jonathansantilli/freemad（MIT）是第三方按论文算法写的实现，不是论文实验代码。</td></tr>'
         '<tr><td>源码里的做法</td><td>生成轮：各 agent 独立作答（SOLUTION / REASONING）。批判轮：提示开头是“Anti-conformity critique. Analyze peers for flaws and improvements.”，看到自己的上一轮答案和匿名的同伴答案（Peer #k，默认全连接），输出 DECISION: KEEP 或 REVISE。记分（<code>ScoreTracker</code>）：初始 +w1·f，保持 +w4·f，改答案时旧答案 −w2·f、新答案 +w3·f，f = 1/(k+1)，默认权重 (20, 25, 30, 20)；默认还会把每个答案的分数除以支持过它的 agent 数（normalize=True）。选答案（<code>AnswerSelector</code>）：最高分；平局看校验器置信度，再按字母序。</td></tr>'
         '<tr><td>我们的适配</td><td>轨迹的轮次：k=0 Round 0、k=1 反思、k≥2 辩论。只记主答案。不做归一化（按论文算法），归一化作为附加对照。平局用 Direct 的答案（在平局内时）。B0 用 v4 已保存的普通辩论记录（零成本，相当于论文 c 变体）；B1 新跑一轮反从众批判（相当于 n 变体），批判时同伴匿名、答案限 C 内。</td></tr>'
         '<tr><td>示例里的计算</td><td>dia198_utt2 按已保存记录：neutral = 20+20（k=0）+10+10（k=1）+6.7+6.7+10（k=2）= 83.3；anger = 20 + 10 − 8.3 = 21.7。选 neutral，答错。原因是三位专家的记录本身都偏向 neutral，记分规则改不了这一点。</td></tr>'
         '<tr><td>风险</td><td>在三人都不太对的样本上，记分只是投票的变体；我之前测过的软投票在不一致分支是 29 / 24（Gemini / GPT），低于 Direct 的 38 / 26。</td></tr></table></section>')

P.append('<section class="panel"><h2>三、v5-C：AgentAuditor（分歧点审计）</h2><div class="fig">' + fig_c() + '</div><p class="cap"><b>图 3　v5-C AgentAuditor 分歧点审计。</b>①把三位专家的证据按“来源 + 位置”对齐，共同观察不再争论，只留下描述不同的分歧点；③每个分歧点打包为“共享上下文 + 分支 A / B”，不写各有几人支持；④审计员看原媒体、回到对应位置判断哪个分支成立；⑤每个胜出分支给它导向的候选一票，平局或没有分歧点时用 Direct。</p>'
         '<table><tr><th>项目</th><th>内容</th></tr>'
         '<tr><td>论文与源码</td><td>Auditing Multi-Agent LLM Reasoning Trees Outperforms Majority Vote and LLM-as-Judge（EMNLP 2026 Main；arXiv 2602.09341）。仓库 weiyang930/AgentAuditor，<b>没有许可证</b>：只借思路，不复制代码。</td></tr>'
         '<tr><td>源码里的做法</td><td><code>ReasoningTrie.insert_trace</code>：每一步做句向量，与当前节点子节点的余弦相似度 ≥ 0.82 就合并，否则开新分支，节点记录支持的 agent。<code>PacketExtractor.build_packets</code>：在有两个以上子节点的地方，给每个分支打包共享上下文（前缀最后 5 步）、分支证据（后续最多 3 步，遇到下一个分歧点就停）、支持人数、答案分布（提示里写“仅供参考”）。<code>Auditor._build_prompt</code>：“按过程质量而非人气”，用事实、逻辑、约束、假设、简洁 5 条评判，输出 JSON（胜出分支、置信度、是否致命、理由）。<code>Adjudicator.adjudicate</code>：从根往下，每个分歧点调用一次审计员，最后取胜出子树里的最终答案；胜出无效时选答案最一致的分支。</td></tr>'
         '<tr><td>我们的适配</td><td>①专家证据直接当作步骤；②证据没有先后顺序，前缀树不适用，改为一次文字调用按“来源 + 位置”对齐，分出共同观察和分歧点（这是与源码最大的不同）；③共享上下文 = 共同观察，默认不给支持人数；④审计员必须看媒体并回到对应位置核对（源码只看文字）；⑤分歧点之间是并列的，不是沿树往下，所以改为每个分歧点给胜出分支导向的候选投 1 票，平局或没有分歧点用 Direct。</td></tr>'
         '<tr><td>风险</td><td>可能找不到有区分力的分歧点；同一位置的描述不同，也可能只是措辞不同。论文是文本推理任务。</td></tr></table></section>')

P.append('<section class="panel"><h2>四、v5-D：候选取证控制器（我们的设计）</h2><div class="fig">' + fig_d() + '</div><p class="cap"><b>图 4　v5-D 候选取证控制器（我们的设计）。</b>①把专家证据整理成匿名的证据池；②为候选集里的每个标签分别调用一次，在媒体里找支持、反对和能区分候选的证据；③控制器回到写明的位置逐条核对，按“成立、区分力、模态覆盖、反证”比较各候选的证据充分度；④有明确胜者就输出，否则用 Direct。D-lite 把 ② 和 ③ 合成一次调用作为消融。</p>'
         '<table><tr><th>项目</th><th>内容</th></tr>'
         '<tr><td>来源</td><td>你提出的思路：不一致时由一个控制器基于候选集去找证据（引用证据），最后看哪个候选的证据更充分就采用哪个。没有对应的源码，以下每一步都是我的细化，等你审核。</td></tr>'
         '<tr><td>谁看到什么</td><td>取证调用：看媒体、C、匿名证据池，只负责一个候选，看不到其他取证调用的结果，也不知道专家各自选了什么。控制器：看媒体、C、各候选的证据清单（顺序随机），看不到专家的身份、答案和理由。</td></tr>'
         '<tr><td>“证据充分”的判断规则（写进控制器提示词）</td><td>①先逐条核对：回到写明的位置，看观察是否成立；②只算成立的证据，同一事实只算一次；③更看重能把这个候选和其他候选区分开的证据；④覆盖的模态越多越好（画面、声音、字幕）；⑤成立的最强反证会削弱这个候选；⑥两边差距不明显时写“不确定”，交给 Direct。</td></tr>'
         '<tr><td>位置偏差</td><td>候选大多只有 2 个，控制器可能偏向先出现的那个（ACL 2024《Large Language Models are not Fair Evaluators》）。先用随机顺序；如需要，再加“交换顺序各判一次”作为附加对照（调用数 +1）。</td></tr>'
         '<tr><td>风险</td><td>取证调用可能为每个候选都“找”出看似合理的证据；控制器的核对仍是语言判断，没有工具。翻转样本要人工抽查证据是否真能在媒体里定位。</td></tr></table></section>')

P.append('<section class="panel"><h2>五、四种方法对比</h2><table><tr><th></th><th>v5-A 匿名化辩论</th><th>v5-B 轨迹记分</th><th>v5-C 分歧点审计</th><th>v5-D 候选取证控制器</th></tr>'
         '<tr><td>一句话</td><td>辩论照旧，看不出谁说的</td><td>不要求一致，按轨迹记分</td><td>只在分歧观察上回看媒体</td><td>每个候选单独取证，控制器按证据选</td></tr>'
         '<tr><td>专家之间是否交流</td><td>是（匿名）</td><td>B0 用 v4 的；B1 一轮匿名批判</td><td>否</td><td>否</td></tr>'
         '<tr><td>最后谁决定</td><td>一致或汇总器</td><td>记分规则（程序）</td><td>审计员逐点投票</td><td>控制器</td></tr>'
         '<tr><td>是否回看媒体</td><td>辩论时</td><td>B1 批判时</td><td>审计时（定点）</td><td>取证和核对时</td></tr>'
         '<tr><td>依据</td><td>官方源码</td><td>第三方源码</td><td>官方源码（无许可证）</td><td>无源码</td></tr>'
         '<tr><td>每个不一致样本的新增调用</td><td>3–7</td><td>B0：0；B1：3</td><td>2–4</td><td>3–4</td></tr>'
         '<tr><td>117 条大约</td><td>与 v4 辩论相当</td><td>B0：0；B1：约 351</td><td>约 234–468</td><td>约 390</td></tr></table></section>')

P.append('<section class="panel"><h2>六、统一的评价方法（先定好，再跑）</h2><ul>'
         '<li>样本：400 条里的不一致分支，Gemini 62 条、GPT 55 条，共 117 条。对照组是 Direct（38、26），同时列出 v4（26、19）、随机期望（25.6、22.8）、候选集上限（58、49）和三位专家各自的答对数。</li>'
         '<li><b>算“有提升”</b>：合并 117 条比 Direct 多答对至少 4 条，并且两个模型各自都不低于 Direct。</li>'
         '<li>会同时比较 A、B0、B1、C、D（加可选的 D-lite）五到六个结果，只挑最好的会高估，所以“达标”只表示值得在新样本上验证；所有结果都要报告。</li>'
         '<li>每个方法都报告：答对数（按模型、数据集、验证和训练拆开）、与 Direct 的逐条翻转（改对 / 改错）、整体 400 条（一致用 v4、不一致用该方法）、调用数和 token 数、无效样本数，以及翻转样本的人工抽查。A 另报从众率和坚持率；C 另报有分歧点的样本比例；D 另报“不确定”回退的比例和证据核对结果。</li>'
         '<li>提示词运行前冻结，不在这 117 条上调；每个方法跑一次；真实标签只在算分时读取。训练集样本是按模型正确性筛选的，验证集是开发复用数据，重点看相对 Direct 的差值。</li>'
         '<li>建议顺序：先做零成本的 B0 和 A 的诊断（v4 记录上的从众率），再做 D 和 C，最后 A、B1。</li></ul></section>')

P.append('<section class="panel"><h2>七、请你审核的点（括号里是我的默认）</h2><ol>'
         '<li>A：每位专家看到全部 3 份观点（含自己的）、不标注、每轮重新打乱；终止规则沿用 v4，而不是源码的多数投票。（是）</li>'
         '<li>B：k=0 Round 0、k=1 反思、k≥2 辩论；只记主答案；不归一化；平局用 Direct。（是）</li>'
         '<li>C：用一次文字调用代替向量前缀树；默认不给支持人数；审计员看媒体；分歧点最多 3 个，逐点投票。（是）</li>'
         '<li>D：证据池去掉专家名、答案和解释；每个候选一次取证调用；控制器按第四节的 6 条规则判断；“不确定”回退到 Direct；D-lite 作为消融。（是）</li>'
         '<li>四个方法都只在不一致分支上跑，代码放 <code>versions/v5/</code>，不改 v4；每个方法先做 2–3 条冒烟。（是）</li></ol>'
         '<div class="warn">你审核通过前，我不会写流水线代码，也不会调用任何模型。上一版“三种方案”页面已由本页取代。</div></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>v5 设计草案：四种方法</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v5-methods.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
