"""Detailed flow charts (R2-MAD training-set construction / memory records / test-time flow / prompt structure; SkillOpt one-step data flow)
for docs/v6-selfevolve-design.html. Imported by scripts/build_selfevolve_design_page.py. All example strings inside the figures are
illustrative (nothing has been run). Reuses the drawing helpers of scripts/v5_paper_figs.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_paper_figs import (C_EXP, CODE, CTRL, NEW, OUT, agent, arrow, code_tag, diamond, doc, film, group, legend, llm_tag, module,  # noqa: E402
                           out_box, svg, t, tw, wave)

PUR = ('#7B4FA3', '#EFE6F7')
TEAL = ('#1F7A7A', '#DDF1F0')


def cyl(x, y, w, h, color, fill, lines_):
    ry = 9
    b = f'<path d="M{x},{y + ry} V{y + h - ry} A{w / 2},{ry} 0 0 0 {x + w},{y + h - ry} V{y + ry}" fill="{fill}" stroke="{color}" stroke-width="1.6"/>'
    b += f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{fill}" stroke="{color}" stroke-width="1.6"/>'
    for i, s in enumerate(lines_):
        b += t(x + w / 2, y + ry + 22 + i * 15, s, size=10.5, anchor='middle', bold=(i == 0))
    return b


def lines(x, y, items, size=10.5, step=17, color='#222'):
    return ''.join(t(x, y + i * step, s, size=size, color=color) for i, s in enumerate(items))


def agents3(cx, cy, r=13, gap=56):
    b = ''
    for i, k in enumerate('GAI'):
        c, l, name = C_EXP[k]
        b += agent(cx + (i - 1) * gap, cy, r, c, l, label=name.replace('专家', ''), label_side='below')
    return b


# ------------------------------------------------------------------------------------------------- R2-MAD: training-set construction
def fig_train_set():
    ws, gap = 285, 24
    xs = [14 + i * (ws + gap) for i in range(4)]
    b = ''
    # row 1
    b += module(xs[0], 44, ws, 210, '#fff', '#888', '候选池', 1, '目录里的全部样本，去掉旧 400 条')
    b += lines(xs[0] + 14, 104, ['emotion_eval_5models_4frames_20261030', 'MER2024：1169 条 − 旧 200 = 969', 'MELD：2610 条 → 过媒体过滤 2608', '　　　　　− 旧 200 = 2408', '', '合计 3,377 条', '旧 400 = self_evolution_mer_meld_200_20261101'], size=10, step=16.5)
    b += arrow([(xs[0] + ws, 150), (xs[1], 150)])
    b += module(xs[1], 44, ws, 210, NEW[0], NEW[1], '补冻结 Gemini 图谱', 2, '图谱专家要用；原 PPCT 流程，不发标签')
    b += llm_tag(0, 14, 'LLM ×1/条', right=xs[1] + ws)
    b += lines(xs[1] + 14, 104, ['现有图谱只有旧 80 + 320 条，', '候选池里的新样本都要补；', '约 3,377 次 Gemini 调用，', 'Gemini、GPT 共用同一份，只做一次', '', '只有图谱专家看图谱，其他两位不看'], size=10, step=16.5)
    b += arrow([(xs[1] + ws, 150), (xs[2], 150)])
    b += module(xs[2], 44, ws, 210, NEW[0], NEW[1], '三专家第 0 轮', 3, 'Gemini、GPT 各跑一遍，各留各的')
    b += llm_tag(0, 14, 'LLM ×3/条', right=xs[2] + ws)
    b += agents3(xs[2] + 145, 110)
    b += lines(xs[2] + 14, 168, ['v4 专家提示词，去掉反思；每位专家', '给 1–2 个标签 + 带位置的证据', '约 10,100 次/模型；结果写缓存', '（测试时的第 0 轮同样读缓存）'], size=10, step=16.5)
    b += arrow([(xs[2] + ws, 150), (xs[3], 150)])
    b += module(xs[3], 44, ws, 210, CODE[0], CODE[1], '按第 0 轮路由', 4, '程序；和测试时同一规则')
    b += code_tag(0, 14, right=xs[3] + ws)
    b += lines(xs[3] + 14, 104, ['三位专家答案集合取交集：', '· 恰好 1 个标签 → 一致 → 丢弃', '· 否则 → 不一致 → 进入候选池 D', '', 'Gemini、GPT 各得自己的 D_g、D_p', '（两者不相同）', '不一致比例：未知，跑完才知道'], size=10, step=16.5)
    # wrap arrow
    b += arrow([(xs[3] + ws / 2, 254), (xs[3] + ws / 2, 278), (xs[0] + ws / 2, 278), (xs[0] + ws / 2, 300)])
    # row 2
    b += module(xs[0], 300, ws, 210, CODE[0], CODE[1], '限量：训练集上限 400 条', 5, '程序；每个模型各做一次')
    b += code_tag(0, 306, right=xs[0] + ws)
    b += lines(xs[0] + 14, 360, ['每个数据集最多 200 条（合计 ≤ 400）', '· |D| ≤ 200：全部使用', '· |D| > 200：固定种子 42 随机抽取，', '　按该数据集不一致池里的标签占比分层', '　（最大余数法），标签只用于抽样，', '　不进任何提问', '“两个数据集合计 400”的解释待你确认'], size=10, step=16.5)
    b += arrow([(xs[0] + ws, 400), (xs[1], 400)])
    b += module(xs[1], 300, ws, 210, NEW[0], NEW[1], '题目 Q：Gemini 一次综合 Caption', 6, '只对抽中的样本做；两个模型共用')
    b += llm_tag(0, 306, 'LLM ×1/条', right=xs[1] + ws)
    b += film(xs[1] + 14, 356, 36, 24) + wave(xs[1] + 56, 358, 32, 20) + doc(xs[1] + 94, 352, 26, 30, [], fold=5)
    b += lines(xs[1] + 14, 402, ['同时给 Gemini 8 帧、音轨、字幕，', '输出一段综合 Caption（画面、声音、', '台词三方面；不给标签、不做情绪判断）', 'Q = Caption + 情感识别问题（含标签集）'], size=10, step=16.5)
    b += arrow([(xs[1] + ws, 400), (xs[2], 400)])
    b += module(xs[2], 300, ws, 210, PUR[1], PUR[0], '训练集 T（每个模型一份）', 7, '后面“建库”的输入')
    b += lines(xs[2] + 14, 360, ['T_gemini：≤ 400 条　T_gpt：≤ 400 条', '每条保存：样本 id、数据集、Q、', '第 0 轮三专家输出（缓存）、标准标签', '', '标准标签只在建库时用于判对错，', '不会出现在任何模型的提问里', '测试集（旧 400 条）不参与'], size=10, step=16.5)
    b += lines(xs[3] + 14, 330, ['建库一次的调用（每个模型）：', '≤ 400 条 × 8 次 = ≤ 3,200 次', '（辩论 3 + 3，摘要 1 + 1）', '', 'Caption：≤ 800 条 × 1 次', '（两个模型的并集，共用）'], size=10, step=16.5, color='#555')
    b += legend(534)
    return svg(b, 558)


# ------------------------------------------------------------------------------------------------- R2-MAD: memory records
def fig_records():
    ws, gap = 226, 24
    xs = [14 + i * (ws + gap) for i in range(5)]
    stages = [('第 0 轮（复用缓存）', '三位专家各 1–2 个标签', '复用，0 次', CODE), ('摘要 S0 + 共识率 c0', 'LLM 读第 0 轮三位专家的输出', 'LLM ×1', NEW),
              ('辩论 第 1 轮（无经验）', '每位专家看同伴第 0 轮输出', 'LLM ×3', NEW), ('摘要 S1 + 共识率 c1', 'LLM 读第 1 轮三位专家的输出', 'LLM ×1', NEW),
              ('辩论 第 2 轮（无经验）', '每位专家看同伴第 1 轮输出', 'LLM ×3', NEW)]
    b = ''
    for i, (x0, (ttl, sub, tg, col)) in enumerate(zip(xs, stages)):
        b += f'<rect x="{x0}" y="44" width="{ws}" height="96" rx="10" fill="{col[0]}" stroke="{col[1]}" stroke-width="1.6" filter="url(#sh)"/>'
        b += t(x0 + 12, 70, ttl, size=12.5, bold=True) + t(x0 + 12, 90, sub, size=10, color='#555') + t(x0 + 12, 112, tg, size=10.5, color='#8a6d00' if tg.startswith('LLM') else '#555', bold=True)
        if i:
            b += arrow([(x0 - gap, 92), (x0, 92)])
    recs = [(xs[0], 'r = 0', ['键：Q', '', '值：Q ｜ 标准标签 ｜ G 的第 0 轮', '　　输出 ｜ N/A ｜ 对 / 错', '', '元数据：专家 = G，轮 = 0，', '　上一轮共识率 = —，本轮对 / 错']),
            (xs[2], 'r = 1', ['键：Q ｜ G 的第 0 轮输出 ｜ S0', '', '值：Q ｜ 标准标签 ｜ G 的辩论 1', '　　输出 ｜ 是否改立场 ｜ 对 / 错', '', '元数据：专家 = G，轮 = 1，', '　上一轮共识率 = c0，本轮对 / 错']),
            (xs[4], 'r = 2', ['键：Q ｜ G 的辩论 1 输出 ｜ S1', '', '值：Q ｜ 标准标签 ｜ G 的辩论 2', '　　输出 ｜ 是否改立场 ｜ 对 / 错', '', '元数据：专家 = G，轮 = 2，', '　上一轮共识率 = c1，本轮对 / 错'])]
    for x0, ttl, body in recs:
        b += arrow([(x0 + ws / 2, 140), (x0 + ws / 2, 176)], PUR[0])
        b += doc(x0, 176, ws, 150, [], fold=9, stroke=PUR[0], fill=PUR[1])
        b += t(x0 + 8, 194, '一条记录（以专家 G 为例）· ' + ttl, size=10.5, bold=True, color=PUR[0])
        b += lines(x0 + 8, 214, body, size=9.6, step=15)
    b += arrow([(xs[1] + ws / 2, 140), (xs[1] + ws / 2, 160), (xs[2] + 40, 160), (xs[2] + 40, 176)], '#999', True)
    b += arrow([(xs[3] + ws / 2, 140), (xs[3] + ws / 2, 160), (xs[4] + 40, 160), (xs[4] + 40, 176)], '#999', True)
    b += t(xs[1] + 40, 158, 'S0 进入 r=1 的键', size=9.5, color='#777') + t(xs[3] + 40, 158, 'S1 进入 r=2 的键', size=9.5, color='#777')
    b += group(14, 348, 560, 138, '说明', color='#999', fill='#fff')
    b += lines(28, 394, ['· 每位专家每轮 1 条：每个训练样本 3 × 3 = 9 条记录，同时每条回答存一个向量（回答库）', '· 训练时强制跑满 2 轮辩论，不早停、不用经验；摘要 S2 没有后续轮用不到，不生成', '· 判对错：该专家这一轮的主答案（answer 字段）= 标准标签；第 0 轮的副答案不计', '· 共识率 c = 三位专家主答案里最多的同标签人数 / 3（1/3、2/3、1）', '· 辩论里每位专家只给 1 个标签，且必须在“第 0 轮出现过的标签”之内（沿用 v4）'], size=10, step=18)
    b += group(594, 348, 646, 138, '摘要 S 的格式（原版 R²-MAD 提示词，示意输出）', color='#999', fill='#fff')
    b += doc(608, 394, 616, 78, ['Dynamic: 三位专家分成两派，多数集中在同一类标签，少数坚持另一类，上一轮无人改变立场。', 'Insight: 分歧源于对语气强度的不同解读，少数派的理由还没有被反驳。'], size=10, fold=9)
    b += t(608, 384, '只写立场分布与论证模式，不出现具体标签、数字、答案值（防止泄露标准答案）', size=9.8, color='#555')
    b += legend(508)
    return svg(b, 532)


# ------------------------------------------------------------------------------------------------- R2-MAD: test-time flow
def fig_test_flow():
    b = ''
    # row 1
    w1, g1 = 214, 25
    x1 = [14 + i * (w1 + g1) for i in range(5)]
    specs = [('测试样本', '旧 400 条里被路由为不一致的', None, '#fff', '#888'),
             ('题目 Q', 'Gemini 一次综合 Caption + 问题', 'LLM ×1', NEW[0], NEW[1]),
             ('第 0 轮（读缓存）', 'v4 专家的第 0 轮输出', '0 次', CODE[0], CODE[1]),
             ('路由', '交集恰好 1 个标签 → 不进入', '程序', CODE[0], CODE[1]),
             ('摘要 S0 + 共识率 c0', '读第 0 轮三位专家输出', 'LLM ×1', NEW[0], NEW[1])]
    for i, (x0, (ttl, sub, tg, f, s_)) in enumerate(zip(x1, specs)):
        b += f'<rect x="{x0}" y="44" width="{w1}" height="104" rx="10" fill="{f}" stroke="{s_}" stroke-width="1.6" filter="url(#sh)"/>'
        b += t(x0 + 12, 70, ttl, size=12.5, bold=True) + t(x0 + 12, 90, sub, size=10, color='#555')
        if tg:
            b += t(x0 + 12, 118, tg, size=10.5, bold=True, color='#8a6d00' if tg.startswith('LLM') else '#555')
        if i:
            b += arrow([(x0 - g1, 96), (x0, 96)])
    b += film(x1[0] + 12, 100, 34, 22) + wave(x1[0] + 52, 102, 30, 18) + doc(x1[0] + 88, 98, 24, 26, [], fold=5)
    b += arrow([(x1[4] + w1 / 2, 148), (x1[4] + w1 / 2, 172), (14 + 165, 172), (14 + 165, 196)])
    # row 2: debate 1
    def debate_row(y0, rd, prev_s, nxt):
        r = ''
        r += module(14, y0, 330, 140, PUR[1], PUR[0], f'辩论 第 {rd} 轮（带经验）', rd)
        r += llm_tag(0, y0 - 26, 'LLM ×3', right=344)
        r += lines(28, y0 + 56, ['每位专家：检索（键 = Q + 自己上一轮输出 + ' + prev_s + '）', '→ 取 n 条案例 + 同伴可靠度 → 作答', '输出：1 个标签，必须在第 0 轮', '出现过的标签之内'], size=9.8, step=16)
        r += cyl(236, y0 + 78, 96, 52, PUR[0], '#fff', ['经验库（只读）'])
        r += diamond(444, y0 + 70, 62, 54, ['三人', '答案相同？'])
        r += arrow([(344, y0 + 70), (382, y0 + 70)])
        r += t(444, y0 + 142, '是：输出该标签，早停（沿用 v4）', size=9.6, anchor='middle', color='#2D6A4F')
        r += arrow([(506, y0 + 70), (560, y0 + 70)]) + t(512, y0 + 62, '否', size=11, color='#C0392B', bold=True)
        return r
    b += debate_row(214, 1, 'S0', None)
    b += f'<rect x="560" y="214" width="{w1 + 26}" height="104" rx="10" fill="{NEW[0]}" stroke="{NEW[1]}" stroke-width="1.6" filter="url(#sh)"/>'
    b += t(572, 240, '摘要 S1 + 共识率 c1', size=12.5, bold=True) + t(572, 260, '读第 1 轮三位专家输出', size=10, color='#555') + t(572, 288, 'LLM ×1', size=10.5, bold=True, color='#8a6d00')
    b += lines(836, 244, ['检索读的是训练集 T 建好的', '经验库，测试时不更新', '检索细节见图 5、图 6'], size=10, step=17, color=PUR[0])
    b += arrow([(560 + (w1 + 26) / 2, 318), (560 + (w1 + 26) / 2, 364), (14 + 165, 364), (14 + 165, 396)])
    b += debate_row(396, 2, 'S1', None)
    b += arrow([(506, 466), (560, 466)])
    b += f'<rect x="560" y="416" width="{w1 + 26}" height="104" rx="10" fill="{NEW[0]}" stroke="{NEW[1]}" stroke-width="1.6" filter="url(#sh)"/>'
    b += t(572, 442, '汇总器（静态，同 v4）', size=12.5, bold=True) + t(572, 462, '读媒体 + 三位专家完整历史', size=10, color='#555') + t(572, 490, 'LLM ×1', size=10.5, bold=True, color='#8a6d00')
    b += lines(572, 508, ['两轮后仍不一致才调用'], size=9.8, color='#777')
    b += arrow([(826, 468), (860, 468)])
    b += out_box(860, 444, 120, 48, ('最终标签', '∈ 第 0 轮标签'))
    b += lines(1010, 424, ['每条样本的调用：', 'Q 1 + S0 1 + 辩论 3 + S1 1', '+ 辩论 3 + 汇总 ≤ 1', '= 9–10 次（早停更少）', '', '第 0 轮读缓存，0 次'], size=10, step=16, color='#555')
    b += legend(568)
    return svg(b, 592)


# ------------------------------------------------------------------------------------------------- R2-MAD: prompt structure
def fig_prompt():
    b = group(14, 44, 760, 470, '一位专家在第 t 轮收到的内容（在 v4 辩论提示词上增加两块，示意）', color='#999', fill='#fff')
    rows = [
        ('S', 'system：专家角色提示词（同 v4，静态）。SkillOpt 版才在这里追加该角色的技能文档'),
        ('S', 'user（JSON）：该专家自己的媒体（8 帧 / 音轨 / 字幕；图谱专家另有图谱与组织文本）'),
        ('S', '　　　　　　　 round = t，candidate_labels = [第 0 轮三位专家提过的标签]'),
        ('S', '　　　　　　　 your_previous_output = { 该专家上一轮的完整输出 }'),
        ('R', '　　　　　　　 retrieved_examples = [   ← R²-MAD 新增（取 n 条）'),
        ('R', '　　　　　　　　 { example_question: 案例的 Q（Caption + 问题）,'),
        ('R', '　　　　　　　　　 example_solution: 案例的标准标签,'),
        ('R', '　　　　　　　　　 example_agent_response: 该专家在案例里的回答,'),
        ('R', '　　　　　　　　　 example_agent_stance_changed: 是否改变立场,'),
        ('R', '　　　　　　　　　 example_agent_response_correctness: “The response is correct / incorrect.” } ]'),
        ('W', '　　　　　　　 other_experts = {   ← R²-MAD 在每位同伴的输出后增加一项'),
        ('W', '　　　　　　　　 同伴 A: { 上一轮完整输出, reliability: “High，历史可靠” | “Low，历史不准” | 不写 },'),
        ('W', '　　　　　　　　 同伴 B: { …… } }'),
        ('S', '输出格式（同 v4 辩论）：answer ∈ candidate_labels、changed、adopted_evidence、response_to_others'),
        ('S', '　　　　　　　　　　　（改变观点必须引用证据，与每位同伴逐条回应）'),
    ]
    col = {'S': ('#F4F4F4', '#bbb'), 'R': (PUR[1], PUR[0]), 'W': ('#FCE9D5', '#D98C3F')}
    for i, (k, s_) in enumerate(rows):
        y0 = 78 + i * 26
        b += f'<rect x="26" y="{y0}" width="736" height="23" rx="4" fill="{col[k][0]}" stroke="{col[k][1]}" stroke-width="1"/>'
        b += t(34, y0 + 16, s_, size=10.3)
    b += lines(800, 90, ['图例', ''], size=11.5, step=18)
    for i, (k, s_) in enumerate([('S', '静态部分，同 v4'), ('R', '来自“取经验”（图 5 ②）'), ('W', '来自“同伴可靠度”（图 5 ③）')]):
        y0 = 110 + i * 34
        b += f'<rect x="800" y="{y0}" width="30" height="20" rx="4" fill="{col[k][0]}" stroke="{col[k][1]}"/>' + t(840, y0 + 15, s_, size=11)
    b += doc(800, 230, 436, 250, [], fold=9)
    b += t(810, 250, '几点说明', size=11.5, bold=True)
    b += lines(810, 272, ['· 案例只有文字（Caption、标签、回答），', '　不带帧：当前样本的媒体仍由该专家自己看。', '· 案例里回答的证据引用的是那个案例自己的帧，', '　当前样本没有，只能当“写法”参考。', '· 可靠度 > 0.55 标 High，< 0.45 标 Low，', '　其余不写；第 1 轮之前没有历史，不写。', '· 对应原版：<examples> 块与 <confidence> 标注；', '　原版放在纯文本题目前面，我们放进 v4 的 JSON。', '· 其余字段、校验规则、重试都沿用 v4 的 call_stage。'], size=10, step=17)
    b += legend(534)
    return svg(b, 558)


# ------------------------------------------------------------------------------------------------- SkillOpt: one step with data
def fig_skill_step():
    b = group(14, 44, 1226, 40, '一步（step）里的数据流：从训练样本到技能文档的一次修改（示例文字均为示意，不是真实结果）', color=TEAL[0], fill=TEAL[1] + '33')
    cols = [(14, 214), (252, 268), (544, 236), (804, 212), (1040, 200)]
    y0, h = 100, 330
    ttl = [('① Rollout', 'LLM（看媒体）'), ('② Reflect', 'LLM（纯文本）'), ('③ Aggregate + Select', 'LLM + 程序'), ('④ Update', '程序'), ('⑤ Gate', 'LLM（看媒体）')]
    fills = [NEW, CTRL[::-1], CTRL[::-1], CODE, NEW]
    for i, ((x0, w), (tt, tg), (fl, st)) in enumerate(zip(cols, ttl, fills)):
        b += module(x0, y0, w, h, fl, st, tt, None)
        b += (llm_tag(0, y0 - 24, tg, right=x0 + w) if 'LLM' in tg else code_tag(0, y0 - 24, right=x0 + w))
        if i:
            b += arrow([(cols[i - 1][0] + cols[i - 1][1], y0 + 160), (x0, y0 + 160)])
    # 1
    x0 = cols[0][0] + 10
    b += lines(x0, y0 + 46, ['从 400 条里取 40 条（一步）', '带当前技能 S 让专家作答', '', '每条轨迹：', '· 样本 id', '· 专家输出（答案 / 理由 / 证据）', '· 标准标签', '· 得分：主答案是否命中', '', '40 条 → 5 个 minibatch，', '每组 8 条，分成 “失败组”', '和 “成功组” 分别送去反思'], size=9.8, step=16)
    # 2
    x0 = cols[1][0] + 10
    b += doc(x0, y0 + 40, 248, 130, [], fold=8, stroke='#999')
    b += t(x0 + 6, y0 + 56, '失败组输入（analyst_error）', size=10, bold=True)
    b += lines(x0 + 6, y0 + 74, ['· 当前技能 S 全文', '· 8 条失败轨迹（含标准标签）', '· 编辑预算 L = 学习率 k', '输出 JSON：failure_summary +', 'patch.edits[ ]'], size=9.6, step=15.5)
    b += doc(x0, y0 + 182, 248, 136, [], fold=8, stroke='#999')
    b += t(x0 + 6, y0 + 198, '补丁示例（示意）', size=10, bold=True)
    b += lines(x0 + 6, y0 + 216, ['{ "op": "append", "content":', '  "- 语气平淡但内容在抱怨，', '   不要默认 neutral，先看…" }', '{ "op": "replace", "target": "…",', '  "content": "…" }', '成功组（analyst_success）同理'], size=9.4, step=15)
    # 3
    x0 = cols[2][0] + 10
    b += lines(x0, y0 + 46, ['5 个组的补丁 → 每 8 个一合并', '（merge_batch_size = 8），', '分层合并；失败补丁优先，', '成功补丁只补缺口', '', '排序（ranking 提示词）：', '系统性影响 > 互补 > 通用 >', '可操作；只保留前 k 条', '', 'k = 学习率：4 → 2，', '余弦衰减（每步越改越少）'], size=9.8, step=16)
    # 4
    x0 = cols[3][0] + 10
    b += doc(x0, y0 + 40, 190, 150, [], fold=8, stroke='#999')
    b += t(x0 + 6, y0 + 56, '技能文档 S → 候选 S′', size=10, bold=True)
    b += lines(x0 + 6, y0 + 76, ['  ## 通用规则', '  - 先写证据再选标签', '+ - 语气平淡但内容在抱怨，', '+   不要默认 neutral…', '- - （被删除的旧规则）'], size=9.6, step=16)
    b += lines(x0, y0 + 214, ['受保护区块不允许改：', 'SLOW_UPDATE 区由每个 epoch', '结束时的 slow update 负责'], size=9.6, step=15, color='#555')
    # 5
    x0 = cols[4][0] + 10
    b += lines(x0, y0 + 46, ['验证集 60 条：', '', 'S 　：41 / 60 答对', 'S′ ：43 / 60 答对', '', '严格更高 → 接受，', 'S ← S′', '', '否则丢弃，并把这次', '编辑记入拒绝缓冲，', '下一步提示优化器避开'], size=9.8, step=16)
    b += group(14, 456, 1226, 66, 'epoch 结束时', color=TEAL[0], fill='#fff')
    b += lines(28, 498, ['Slow Update：用上一轮和这一轮的 S 在同一批题上各跑一遍，分成 变好 / 退步 / 一直错 / 一直对，写一段全局指导放进受保护区块；Meta Skill：写给优化器自己的编辑经验笔记。'], size=10, step=16)
    b += arrow([(1140, 430), (1140, 446), (120, 446), (120, 430)], '#999', True)
    b += t(620, 442, '接受后，S 进入下一步', size=10, color='#555', anchor='middle')
    b += legend(546)
    return svg(b, 570)
