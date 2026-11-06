"""Build docs/mad-2026-frameworks.html: framework diagrams of five ACL/EMNLP 2026 papers, drawn from their
method sections (read from the Anthology PDFs on 2026-11-03), plus a figure placing them on the PPCT pipeline.

Static HTML with inline SVG, no scripts, no network, no model calls. Usage: python scripts/build_mad2026_frameworks.py
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WARN = []


def e(s):
    return escape(str(s), quote=True)


def tw(s, size=13):
    return sum(size if ord(c) > 0x2E7F else size * 0.58 for c in s)


class Fig:
    def __init__(self, fid, w, h, label):
        self.fid, self.w, self.h, self.label, self.p = fid, w, h, label, []

    def add(self, s):
        self.p.append(s)

    def rect(self, x, y, w, h, kind='p', rx=9, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<rect class="r-{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"{d}/>')

    def text(self, x, y, s, cls='tx', anchor='middle'):
        self.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{e(s)}</text>')

    def lines(self, cx, cy, ls, anchor='middle', lh=17, maxw=None, white=False):
        n = len(ls)
        y0 = cy - (n - 1) * lh / 2 + 5
        for i, l in enumerate(ls):
            cls, size = 'tx', 13
            if l.startswith('*'):
                l, cls = l[1:], 'tx tx-b'
            elif l.startswith('~'):
                l, cls, size = l[1:], 'tx tx-l', 12
            elif l.startswith('#'):
                l, cls = l[1:], 'tx tx-m'
            if white:
                cls += ' tx-w'
            if maxw and tw(l, size) > maxw:
                WARN.append(f'[{self.fid}] overflow {tw(l, size):.0f}>{maxw}: {l}')
            self.text(cx, y0 + i * lh, l, cls, anchor)

    def box(self, x, y, w, h, ls, kind='p', dash=None, white=False):
        self.rect(x, y, w, h, kind, dash=dash)
        self.lines(x + w / 2, y + h / 2, ls, maxw=w - 14, white=white)

    def left(self, x, y, w, h, ls, kind='p', dash=None):
        """Left-aligned multi-line box."""
        self.rect(x, y, w, h, kind, dash=dash)
        self.lines(x + 14, y + h / 2, ls, anchor='start', maxw=w - 24)

    def arrow(self, x1, y1, x2, y2, dash=False, label=None, lx=None, ly=None):
        d = ' stroke-dasharray="6 5"' if dash else ''
        self.add(f'<line class="ar" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#a{self.fid})"{d}/>')
        if label:
            self.text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 - 6, label, 'tx tx-l')

    def path(self, d, dash=False, label=None, lx=0, ly=0):
        ds = ' stroke-dasharray="6 5"' if dash else ''
        self.add(f'<path class="ar" d="{d}" fill="none" marker-end="url(#a{self.fid})"{ds}/>')
        if label:
            self.text(lx, ly, label, 'tx tx-l')

    def dot(self, x, y, n):
        self.add(f'<circle cx="{x}" cy="{y}" r="11" fill="#c9533c"/>')
        self.text(x, y + 4.5, str(n), 'tx tx-w tx-b')

    def render(self):
        defs = (f'<defs><marker id="a{self.fid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                '<path d="M0 0 L10 5 L0 10 Z" fill="#6b8179"/></marker></defs>')
        return (f'<div class="fig"><svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{e(self.label)}">{defs}'
                + ''.join(self.p) + '</svg></div>')


# ---------------------------------------------------------------------------- 1 AgentAuditor
def fig_auditor():
    f = Fig('1', 1000, 610, 'AgentAuditor 框架：推理树、分叉点审计、条件 beam 与 ACPO 训练')
    f.text(20, 24, '推理期（prompt-only 即可）', 'tx tx-b tx-g', 'start')
    f.box(20, 40, 110, 80, ['*问题 q'], 'p')
    f.box(160, 40, 160, 80, ['*N 个 agent', '各出推理', 'oᵢ = (rᵢ, ŷᵢ)'], 'b')
    f.box(350, 40, 200, 80, ['*① Trace Atomization', '把 rᵢ 切成原子步骤', 'Tᵢ = (sᵢ₁ … sᵢLᵢ)'], 'a')
    f.box(580, 40, 400, 80, ['*② 构建 Reasoning Tree', '逐步插入：与当前节点的子节点比余弦相似度', '≥ 阈值 → 并入该节点，记支持集 S_v；否则新开分支'], 'a')
    f.arrow(130, 80, 160, 80); f.arrow(320, 80, 350, 80); f.arrow(550, 80, 580, 80)
    # mini tree
    f.text(20, 160, '示意：推理树（节点旁为支持集 S_v）', 'tx tx-l', 'start')
    nodes = {'root': (60, 205, '根(虚拟)'), 'n1': (160, 205, 'n₁'), 'n2': (260, 205, 'n₂'),
             'x1': (380, 180, 'x₁'), 'x2': (480, 180, 'ŷ=B'), 'y1': (380, 250, 'y₁'), 'y2': (480, 250, 'ŷ=C')}
    edges = [('root', 'n1'), ('n1', 'n2'), ('n2', 'x1'), ('x1', 'x2'), ('n2', 'y1'), ('y1', 'y2')]
    for a, b in edges:
        f.add(f'<line x1="{nodes[a][0] + 18}" y1="{nodes[a][1]}" x2="{nodes[b][0] - 18}" y2="{nodes[b][1]}" stroke="#8aa196" stroke-width="1.8"/>')
    for k, (x, y, t) in nodes.items():
        fill = '#fff3da' if k == 'n2' else '#f4f6f3'
        f.add(f'<ellipse cx="{x}" cy="{y}" rx="22" ry="16" fill="{fill}" stroke="#9aaea5" stroke-width="1.6"/>')
        f.text(x, y + 4, t, 'tx tx-s')
    f.add('<ellipse cx="260" cy="205" rx="30" ry="22" fill="none" stroke="#c9533c" stroke-width="2.2"/>')
    f.text(260, 252, 'CDP（≥2 个子节点）', 'tx tx-s tx-r')
    f.text(160, 232, '{a₁ a₂ a₃}', 'tx tx-s tx-l')
    f.text(398, 160, '{a₁ a₂}', 'tx tx-s tx-l'); f.text(398, 276, '{a₃}', 'tx tx-s tx-l')
    f.left(560, 150, 420, 130, ['*③ 找 Critical Divergence Point（CDP）', '子节点 ≥ 2 的节点；为每个 CDP 造 Divergence Packet', '#Δu = ⟨ H_u , {(E_v , S_v)} ⟩', '~H_u 分叉前的共同前缀；E_v 各分支接下来的几步；', '~S_v 走该分支的 agent（只作辅助信息，不当证据）'], 'a')
    f.arrow(520, 215, 560, 215)
    f.left(30, 320, 320, 110, ['*④ Auditor 在每个 CDP 选一个分支', '不重新解题，只比较分支证据', '~rubric：事实准确 · 逻辑 · 约束 · 假设有效 · 简洁'], 'g')
    f.left(380, 320, 330, 110, ['*⑤ 条件 beam（可选）', '可保留多条候选谱系，防早期误剪', '存活谱系答案一致 → 直接返回；不一致 → 最终裁决', '~仍不行 → 回退到多数支持的候选'], 'g')
    f.box(740, 320, 240, 110, ['*输出 ŷ', '~不按频数投票，按分叉点处的', '~证据逐步选出一条谱系'], 'k', white=True)
    f.path('M780 280 L780 300 L190 300 L190 320')
    f.arrow(350, 375, 380, 375); f.arrow(710, 375, 740, 375)
    f.text(20, 470, '训练期（ACPO，可选；需要 GPU 与有标准答案的数据）', 'tx tx-b tx-r', 'start')
    f.box(20, 490, 200, 90, ['*有标准答案的', '多 agent 推理轨迹'], 'p')
    f.box(250, 490, 230, 90, ['*建树，找最早分叉点', 'b_gt（通向正确答案）', 'b_err（通向错误答案）'], 'p')
    f.box(510, 490, 230, 90, ['*抽 Divergence Packet', '平衡两分支的出现位置', '与支持数，防止走捷径'], 'p')
    f.box(770, 490, 210, 90, ['*DPO 偏好 (x, y_w, y_l)', '让 Auditor 不再“多数', '支持 = 更对”'], 'r')
    f.arrow(220, 535, 250, 535); f.arrow(480, 535, 510, 535); f.arrow(740, 535, 770, 535)
    f.path('M875 490 L875 456 L190 456 L190 430', dash=True, label='训练后的 Auditor 用在 ④', lx=560, ly=448)
    return f.render()


# ---------------------------------------------------------------------------- 2 Conformal
def fig_conformal():
    f = Fig('2', 1000, 520, 'Conformal Social Choice 四阶段流程')
    xs = [20, 265, 510, 755]
    f.left(xs[0], 40, 225, 215, ['*Stage 1  辩论 + 口头概率', 'N 个异构 LLM，共 T 轮', '每轮每个 agent 输出', '#πᵢ⁽ᵗ⁾(y|x) ≥ 0，Σᵧ = 1', '只传上一轮的摘要', '~解析失败 → 用均匀分布'], 'b')
    f.left(xs[1], 40, 225, 215, ['*Stage 2  社会概率聚合', '线性意见池', '#P_social(y|x) = Σ wᵢ · πᵢ(y|x)', '默认 wᵢ = 1/N', '~保留“把握有多大”，', '~而不是一人一票'], 'a')
    f.left(xs[2], 40, 225, 215, ['*Stage 3  split conformal', '校准集上每题算：', '#s = 1 − P_social(y_真|x)', '#q̂ = Quantile(', '#   (n+1)(1−α)/n )', '~每个固定轮次各算一个 q̂ₜ'], 'g')
    f.left(xs[3], 40, 225, 215, ['*Stage 4  预测集 + 行动', '#C(x) = {y :', '#   P_social(y|x) ≥ 1−q̂}', '|C| = 1 → 自动采纳', '|C| > 1 → 升级给人，', '~并带上缩小后的候选', '|C| = 0 → 全面复核'], 'r')
    for i in range(3):
        f.arrow(xs[i] + 225, 148, xs[i + 1], 148)
    f.left(20, 290, 470, 200, ['*保证的范围（论文 §3.4）', '边际覆盖：Pr[Y ∈ C(X)] ≥ 1 − α', '前提：校准与测试样本可交换；', '~不要求单个 agent 的概率本身校准好', '是对“固定轮次”的保证；', '~对“第一次出现单标签就停”不保证', '~也不是逐题正确率'], 'p')
    f.left(510, 290, 470, 200, ['*为什么要它（论文 §5.2）', '“一致就停”：1,963 道初始有分歧的题里，', '469 道（23.9%）收敛成一致的错误', '提前出现单标签时的高准确率是选择效应，', '~不是推理变强', '~设置：MMLU-Pro 等，Claude Haiku 4.5 / DeepSeek-R1 /', '~Qwen-3 32B，4 轮，温度 0.7，校准 / 测试各 50%'], 'p')
    return f.render()


# ---------------------------------------------------------------------------- 3 Free-MAD
def fig_freemad():
    f = Fig('3', 1000, 560, 'Free-MAD：反从众辩论加基于轨迹的得分决策')
    f.text(20, 24, '辩论阶段', 'tx tx-b tx-g', 'start')
    f.left(20, 40, 450, 80, ['*Round 0  N 个 agent 独立作答', '每人给出答案 + 详细推理'], 'b')
    f.left(20, 150, 450, 120, ['*Round k ≥ 1  读上一轮其他 agent 的答案与推理', '+ 反从众 CoT 提示：设想存在对抗 agent，', '逐条核对自己与同伴的分歧，再决定是否改答案', '~对照：常规提示只是“其他 agent 的回答如下”'], 'b')
    f.left(20, 300, 450, 80, ['*更新答案 rᵢᵏ', '写入答案矩阵 A ∈ R^{N×(R+1)}'], 'b')
    f.arrow(245, 120, 245, 150); f.arrow(245, 270, 245, 300)
    f.path('M470 340 L495 340 L495 210 L470 210', label='共 R 轮', lx=520, ly=280)
    f.text(20, 420, '两个变体（共用得分决策）', 'tx tx-b', 'start')
    f.left(20, 435, 215, 100, ['*FREE-MAD-N', '反从众辩论 + 得分决策'], 'g')
    f.left(255, 435, 215, 100, ['*FREE-MAD-C', '从众式辩论 + 得分决策', '~简单任务上避免过度固执'], 'g')
    f.text(540, 24, '决策阶段：边辩论边记分（Algorithm 1）', 'tx tx-b tx-r', 'start')
    f.left(540, 40, 440, 60, ['#修正因子 f = 1/(k+1)；权重 W = {w₁,w₂,w₃,w₄} = {20,25,30,20}', '~越到后面轮次，观点变化的影响越小（防从众）'], 'a')
    rows = [('k = 0（初始答案 r）', ['#S[r] += w₁·f']),
            ('k ≥ 1 且答案改变', ['#S[旧答案] −= w₂·f', '#S[新答案] += w₃·f', '~放弃 = 更可能错，新采纳 = 更可能对']),
            ('k ≥ 1 且答案不变', ['#S[r] += w₄·f'])]
    f.text(556, 124, '情形', 'tx tx-l', 'start'); f.text(760, 124, '更新得分字典 S', 'tx tx-l', 'start')
    ys = [134, 204, 304]
    hs = [60, 90, 60]
    for (a, rs), y, hh in zip(rows, ys, hs):
        f.rect(540, y, 440, hh, 'p')
        f.text(556, y + hh / 2 + 5, a, 'tx', 'start')
        f.lines(760, y + hh / 2, rs, anchor='start', maxw=210)
    f.box(540, 380, 440, 60, ['*最终答案 = argmax S', '~并列时随机选；不要求最后一轮达成共识'], 'k', white=True)
    f.left(540, 460, 440, 85,['~读图说明：论文 Algorithm 1 第 13 行的比较符号在 PDF 文本里丢失，', '~这里按正文“放弃的答案更可能错、新采纳的更可能对”解读为“答案改变”。', '~论文在 SoM（Du 等）之上实现，主实验 8 个推理基准。'], 'p', dash='5 4')
    return f.render()


# ---------------------------------------------------------------------------- 4 Identity bias
def fig_identity():
    f = Fig('4', 1000, 570, '身份偏差：度量、贝叶斯信念模型与响应匿名化')
    f.text(20, 24, '原版 debate 提示（回答带身份标记）', 'tx tx-b tx-r', 'start')
    f.text(520, 24, '匿名化提示（去掉全部身份标记）', 'tx tx-b tx-g', 'start')
    f.rect(20, 36, 460, 170, 'r')
    f.rect(520, 36, 460, 170, 'g')
    for i, (t, idl) in enumerate([('1 apple.', 'Id: SELF'), ('2 apples.', 'Id: PEER')]):
        x = 40 + i * 210
        f.box(x, 56, 190, 50, [f'*{t}', f'~[{idl}]'], 'p')
    for i, t in enumerate(['1 apple.', '2 apples.']):
        x = 540 + i * 210
        f.box(x, 56, 190, 50, [f'*{t}', '~[Id: NULL]'], 'p')
    f.lines(250, 150, ['agent 能判断“这是我说的还是同伴说的”，', '于是可以按身份加权：同伴说的多信一点（sycophancy），', '或自己说的多信一点（self-bias）'], maxw=430)
    f.lines(750, 150, ['agent 分不出谁是谁，', '只能按内容判断；身份权重被迫相等'], maxw=430)
    f.left(20, 230, 470, 170, ['*度量（同质 agent、单 peer 环）', '#Conformity_i = P[ y_i,t = y_j,t−1 | y_i,t−1 ≠ y_j,t−1 ]', '#Obstinacy_i  = P[ y_i,t = y_i,t−1 | y_i,t−1 ≠ y_j,t−1 ]', '#Δ_i = Conformity_i − Obstinacy_i', '~意见不一致时，是更常跟同伴，还是更常坚持自己'], 'a')
    f.left(510, 230, 470, 170, ['*DCM 贝叶斯信念模型（§4.1）', '信念 α ~ Dirichlet，回答 y ~ Categorical', '#α_i,t = α_i,t−1 + w_i·e_自己 + Σ w_j·e_同伴', '#Δ_i = [ (信念差) + (w_j − w_i) ] / ‖α‖₁', '~匿名化 ⇒ w_i = w_j ⇒ 身份项消失'], 'b')
    f.box(20, 430, 960, 60, ['*IBC_i = Δ_i(原版) − Δ_i(匿名) = (w_j − w_i) / ‖α‖₁', '~IBC > 0：偏向同伴（sycophancy）；IBC < 0：偏向自己（self-bias）'], 'k', white=True)
    f.left(20, 505, 960, 50, ['结果（论文 Table 1）：20 个“模型 × 数据集”组合里 18 个 IBC > 0、2 个 < 0——sycophancy 远比 self-bias 常见；匿名化后差距基本消失。'], 'p')
    return f.render()


# ---------------------------------------------------------------------------- 5 Selection effect
def fig_selection():
    f = Fig('5', 1000, 640, 'Selection Effect：编码器优先的选择性路由与 LLM verifier 对照')
    f.box(20, 60, 110, 70, ['*输入 x'], 'p')
    f.box(160, 52, 200, 86, ['*编码器 f(x)', '~微调 RoBERTa 等', '~温度缩放 p = softmax(z/T)'], 'b')
    f.box(390, 52, 220, 86, ['*置信度 κ(p)', '~margin / max-prob /', '~1 − H(p)/log K（三选一）'], 'a')
    f.add('<polygon points="690,45 760,95 690,145 620,95" class="r-p"/>')
    f.text(690, 99, 'κ > τ ?', 'tx tx-b')
    f.box(810, 40, 170, 56, ['*接受集 A', '直接输出 ŷ = argmax p'], 'g')
    f.box(810, 118, 170, 72, ['*转发集 R', 'abstain，或交给', '一个 verifier g'], 'r')
    f.arrow(130, 95, 160, 95); f.arrow(360, 95, 390, 95); f.arrow(610, 95, 620, 95)
    f.arrow(750, 80, 810, 68, label='是', lx=782, ly=64); f.arrow(750, 108, 810, 148, label='否', lx=772, ly=140)
    f.left(560, 230, 420, 150, ['*7 种 verifier 候选', 'zero-shot Qwen3.5-4B · LoRA 微调的 Qwen', 'k=3 投票 · k=5 自一致', '异构角色投票 · MultiAgentESC 式路由', '第二个编码器（非 LLM 对照）', '~另有 g = ∅：直接弃权，作为零成本选项'], 'r')
    f.path('M895 190 L895 215 L770 215 L770 230', dash=False)
    f.left(20, 230, 500, 110, ['*split-conformal 替代闸门（灰色通道）', '#S(x) = { y : p_y ≥ 1 − q̂ }', '仅当 S(x) 是单标签才接受编码器预测，', '否则弃权'], 'p', dash='5 4')
    f.left(20, 360, 500, 130, ['*NSGA-II 搜索（置信度函数, 阈值, verifier, 温度）', '目标：接受集 F1 ↑ · 5% 错误约束下的覆盖 ↑ · 成本 ↓', '成本模型：编码器 1.0，置信度 0.1，一次紧凑 LLM 10.0', '~这低估了实测成本（一次 LLM 调用 = 编码器的 70–102 倍）'], 'p')
    f.left(560, 400, 420, 90, ['*再把每个 verifier 在 6 种别的闸门', '以及 error oracle 下重测', '~排除“结论只取决于某个触发条件”'], 'p')
    f.left(20, 515, 960, 105, ['*发现（“选择效应”）：在转发集 R 上，最强的紧凑 verifier 只与编码器持平，其余明显更差；', '换 6 种闸门、加 error oracle、verifier 从 4B 放大到 397B，都不改变。', '~精确前提：编码器见过该任务自己的标签（GoEmotions）。EmpatheticDialogues 上编码器是迁移来的，', '~同样的测量发现升级是值得的——决定因素不是领域或模型大小，而是编码器有没有见过这个任务的标签。'], 'a')
    return f.render()


# ---------------------------------------------------------------------------- 6 placement
def fig_placement():
    f = Fig('6', 1000, 560, '五个方法可能接入 PPCT v4 流水线的位置（我的建议，未验证）')
    f.box(20, 70, 150, 70, ['*三位专家', 'Round 0'], 'b')
    f.box(200, 70, 120, 70, ['*反思'], 'b')
    f.box(350, 70, 170, 70, ['*共同标签路由', '~答案集合交集', '~恰好 1 个标签？'], 'a')
    f.box(570, 30, 190, 56, ['*直接输出', '~一致分支'], 'g')
    f.box(570, 124, 190, 56, ['*辩论 ≤ 2 轮', '~不一致分支'], 'r')
    f.box(800, 124, 180, 56, ['*汇总器'], 'r')
    f.arrow(170, 105, 200, 105); f.arrow(320, 105, 350, 105)
    f.arrow(520, 90, 570, 60, label='是', lx=538, ly=62); f.arrow(520, 120, 570, 148, label='否', lx=538, ly=148)
    f.arrow(760, 152, 800, 152)
    f.text(20, 24, '当前 v4 流水线（见 update.md / F3–F6）', 'tx tx-b', 'start')
    f.dot(640, 196, 1); f.dot(685, 196, 2)
    f.dot(890, 196, 3); f.dot(435, 62, 4); f.dot(60, 62, 5)
    items = [(1, 'Identity Bias（ACL Long）', '辩论提示里匿名化专家身份；先用已保存的辩论日志只读地算 Conformity / Obstinacy。', 'r'),
             (2, 'Free-MAD（Findings ACL）', '用 Round 0 / 反思 / 辩论的答案变化事后记分，代替“只看最后一轮”。权重 {20,25,30,20} 来自论文，是否适用要验证。', 'r'),
             (3, 'AgentAuditor（EMNLP Main）', '替换汇总器：把三位专家的推理建成推理树，只在分叉点审计。证据是多模态感知，需先把推理切成可比较的步骤。', 'r'),
             (4, 'Conformal Social Choice（EMNLP Main）', '在路由处，把专家概率聚合成预测集；单标签自动，多标签进辩论。需要校准集，训练集 320 条的选择偏差是风险。', 'a'),
             (5, 'Selection Effect（EMNLP Main）', '不是组件，是评估协议：不一致分支是“难样本切片”，要在同一切片上比较各方法与 Direct（F6 已经这么做）。', 'p')]
    for i, (n, t, d, k) in enumerate(items):
        y = 225 + i * 64
        f.dot(40, y + 28, n)
        f.rect(62, y, 918, 56, 'p')
        f.text(76, y + 22, t, 'tx tx-b', 'start')
        f.text(76, y + 42, d, 'tx tx-l', 'start')
        if tw(d, 12) > 890:
            WARN.append(f'[6] long desc {tw(d, 12):.0f}: {d[:20]}')
    return f.render()


CSS = """:root{--ink:#172c38;--muted:#607583;--paper:#f4f6f3;--line:#dce4de;--green:#137a68;--amber:#b47c20;--red:#c9533c}*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1100px;margin:auto;padding:34px 28px 70px}
.eyebrow{font-size:12px;color:var(--green);font-weight:700;letter-spacing:2px}h1{font-size:30px;margin:8px 0 6px;line-height:1.3}h2{font-size:21px;margin:0 0 8px}
.muted{color:var(--muted)}.small{font-size:12.5px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 26px;margin-top:20px}
a{color:var(--green)}code{font:12.5px Consolas,monospace;background:#f1f5f1;padding:1px 5px;border-radius:4px}
.fig{margin:12px 0 4px;border:1px solid var(--line);border-radius:12px;background:#fcfdfc;padding:8px}.fig svg{width:100%;height:auto;display:block}
ol,ul{padding-left:22px}li{margin:5px 0}.meta{font-size:12.5px;color:var(--muted);margin:2px 0 8px}
.warn{margin-top:14px;padding:10px 14px;border-left:3px solid var(--amber);background:#fff8e9;font-size:13.5px}
svg .r-p{fill:#f4f6f3;stroke:#c9d6cf;stroke-width:1.6}svg .r-b{fill:#eaf1ff;stroke:#9db2ee;stroke-width:1.6}svg .r-g{fill:#e6f4ee;stroke:#8cc4b0;stroke-width:1.6}
svg .r-a{fill:#fff3da;stroke:#e1c48d;stroke-width:1.6}svg .r-r{fill:#fdebe6;stroke:#e3aa9c;stroke-width:1.6}svg .r-k{fill:#172c38;stroke:#172c38;stroke-width:1.6}
svg .tx{font:13px "Microsoft YaHei","Segoe UI",sans-serif;fill:#172c38}svg .tx-b{font-weight:700}svg .tx-l{fill:#607583;font-size:12px}svg .tx-s{font-size:11.5px}
svg .tx-m{font-family:Consolas,"Microsoft YaHei",monospace;font-size:12.5px}svg .tx-w{fill:#fff}svg .tx-g{fill:#137a68}svg .tx-r{fill:#c9533c}
svg .ar{stroke:#6b8179;stroke-width:1.8}"""

SECTIONS = [
    ('一、AgentAuditor：非投票聚合（EMNLP 2026 Main · 2026.emnlp-main.2642）', fig_auditor,
     ['<b>要解决的问题</b>（§3）：多数投票在 “confabulation consensus” 下失效——相关的 agent 共享偏差、收敛到同一个错误推理，正确推理只出现在少数轨迹里。',
      '<b>推理流程</b>（§4）：① 把每个 agent 的推理切成原子步骤；② 把所有轨迹逐步插入同一棵 Reasoning Tree（语义相近的步骤合并，并记录哪些 agent 经过）；③ 子节点 ≥ 2 的节点是分叉点（CDP），为它造 Divergence Packet（共同前缀 + 各分支的后续证据 + 支持者）；④ Auditor 在每个 CDP 按 rubric 选分支，而不是给整条轨迹打分；⑤ 可选的条件 beam 防止早期误剪。',
      '<b>训练部分</b>（§5，可选）：ACPO 用有标准答案的轨迹构造“共识陷阱”偏好对（正确分支 vs 错误分支，且平衡支持数），用 DPO 训练 Auditor，减少对多数支持的偏好。仓库同时提供 prompt-only 推理，所以不训练也能用。',
      '<b>对我们的意义</b>：输入就是“问题 + K 条 agent 推理”，对应三位专家的输出；但论文评测的是文本 QA 与数学，我们的证据来自多模态感知，切步骤的方式需要自己定。']),
    ('二、Conformal Social Choice：把候选集做成有覆盖保证的预测集（EMNLP 2026 Main · 2026.emnlp-main.830）', fig_conformal,
     ['<b>要解决的问题</b>：agent 可能通过社会强化一致地答错，“一致就停”会把这个错误当成最终决定。',
      '<b>四个阶段</b>（§3.2–3.5）：异构 agent 辩论并输出口头概率 → 线性意见池聚合成 P_social → 用校准集上“真实标签的 1 − P_social”分位数得到阈值 q̂ → 预测集 C(x)，再按集合大小决定自动采纳、升级还是全面复核。',
      '<b>保证与边界</b>：固定轮次的边际覆盖保证，不要求单个模型校准；对自适应停止、对逐题正确率都没有保证。论文自己指出，单标签提前出现时的高准确率是选择效应。',
      '<b>对我们的意义</b>：预测集可以代替人工的“专家答案 ∪ 易混淆标签”候选集；难点是需要有标签的校准集，而训练集 320 条是按模型正确性筛选的。']),
    ('三、Free-MAD：反从众 + 基于整条轨迹的得分（Findings of ACL 2026 · 2026.findings-acl.1600）', fig_freemad,
     ['<b>要解决的问题</b>（§1）：LLM 天然从众，起初答对的 agent 会被答错的带偏；多数投票只看最后一轮。',
      '<b>辩论阶段</b>（§4.2）：在常规提示后追加反从众 CoT 提示，让 agent 设想存在对抗者、逐条核对分歧。<b>决策阶段</b>（§4.3）：边辩论边给每个候选答案记分——初始答案加分，被放弃的答案扣分，新采纳的答案加分，没变的答案加分；轮次越靠后，影响越小。最终取得分最高的答案，不要求共识。',
      '<b>对我们的意义</b>：得分只依赖“每个 agent 每一轮的答案”，我们已保存的 Round 0 / 反思 / 辩论记录可以直接事后计算。注意论文仓库的情况见推荐页；算法本身只有十几行。']),
    ('四、Identity Bias：用匿名化去掉“谁说的”这个捷径（ACL 2026 Long · 2026.acl-long.650）', fig_identity,
     ['<b>要解决的问题</b>：debate 里的 agent 不中立——会因“这是同伴说的”而盲从（sycophancy），或因“这是我说的”而固执（self-bias）。',
      '<b>做法</b>（§3–§4）：定义 Conformity 与 Obstinacy 两个可直接从日志统计的指标；用 Dirichlet-Compound-Multinomial 信念模型证明两者之差由“信念差”和“身份权重差”组成；把提示里的身份标记全部去掉后，身份权重相等，身份项消失。IBC 就是匿名化前后 Δ 的差。',
      '<b>对我们的意义</b>：我们的专家本来就以模态命名，辩论提示里“图谱专家说…”就是一种身份标记；而指标本身不需要任何新调用。论文的设置是同质 agent、单 peer 环，我们是三位异构专家，指标需要按多 peer 的附录做法调整。']),
    ('五、Selection Effect：编码器优先的路由，为什么 LLM verifier 帮不上忙（EMNLP 2026 Main · 2026.emnlp-main.1049）', fig_selection,
     ['<b>问题</b>：已有一个有监督编码器时，把不确定的样本转发给紧凑 LLM verifier，值不值？',
      '<b>方法</b>（§2）：编码器先预测并给出校准后的置信度，超过阈值的直接接受，其余弃权或转发给 verifier；用 NSGA-II 在 F1、覆盖、成本三个目标上搜索，并把 7 种 verifier（含多 agent 路由与异构投票）和 split-conformal 弃权放在同一个搜索里比较。',
      '<b>结论与边界</b>：转发出去的恰是人类标注者也分歧的难样本，LLM 在这块不比编码器好，放大模型也不改善。论文明确说前提是编码器见过任务自己的标签，否则升级可能值得。',
      '<b>对我们的意义</b>：我们没有监督编码器，“三位专家一致”扮演了闸门的角色，不一致分支就是被转发的难样本切片。这篇论文提示：评估方法时要在同一个切片上和基线比，不能拿全量准确率说话。']),
    ('六、这五个方法可以接在我们流水线的哪里', fig_placement,
     ['位置是我读完方法后的建议，<b>没有任何一处被实验验证</b>；论文本身都不是针对多模态情绪识别。',
      '编号 1、2 只读已保存日志即可试；3 需要新的模型调用，4 需要有标签的校准集，5 是评估原则。是否执行、先做哪个，请你决定。']),
]


def build():
    h = [f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>五篇 2026 辩论论文的框架图</title><style>{CSS}</style></head><body><main>',
         '<div class="eyebrow">LITERATURE / FRAMEWORKS</div><h1>五篇 2026 年 ACL / EMNLP 辩论论文的框架图</h1>',
         '<p class="muted">按各论文方法章节的流程绘制（论文 PDF 取自 ACL Anthology，2026-11-03 阅读），图中的公式、权重、数字来自原文；标注“示意”“读图说明”的是我的解读。只读文献，没有运行任何代码或调用模型。与 <a href="mad-2026-papers.html">论文与源码清单</a> 配套。</p>']
    for title, fn, notes in SECTIONS:
        h.append(f'<section class="panel"><h2>{e(title)}</h2>{fn()}<ul>' + ''.join(f'<li>{n}</li>' for n in notes) + '</ul></section>')
    h.append('<section class="panel"><h2>读图的局限</h2><ul>'
             '<li>图是对方法章节的压缩，省略了实现细节（提示词、超参、附录里的多 peer 扩展等）；复现请读原文与仓库。</li>'
             '<li>Free-MAD 的 Algorithm 1 有一处比较符号在 PDF 文本里丢失，已按正文含义解读，并在图中注明。</li>'
             '<li>各论文的实验数字只引用了与框架直接相关的几处（Identity Bias 的 18/20、Conformal 的 469/1,963），未逐篇核对实验表。</li></ul></section>')
    h.append('</main></body></html>')
    out = ROOT / 'docs/mad-2026-frameworks.html'
    out.write_text(''.join(h), encoding='utf8')
    print('wrote', out, out.stat().st_size, 'bytes; warnings:', len(WARN))
    for w in WARN:
        print('  ', w)


if __name__ == '__main__':
    build()
