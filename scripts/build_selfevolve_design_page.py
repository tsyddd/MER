"""Build docs/v6-selfevolve-design.html: design draft (flow charts only, nothing run) for two self-evolving methods on the
disagreement branch: R2-MAD (experience recall, caption-based retrieval key) and SkillOpt (trained skill documents for the three
experts, then debate-round-1/2 and the summarizer). Reuses the drawing helpers of scripts/v5_paper_figs.py. Static HTML, no scripts, no model calls.
Usage: python scripts/build_selfevolve_design_page.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_paper_figs import (C_EXP, CODE, CTRL, NEW, OUT, agent, arrow, chip, code_tag, diamond, doc, film, group, legend, llm_tag, module,  # noqa: E402
                           out_box, svg, t, tw, wave)

ROOT = Path(__file__).resolve().parent.parent
from selfevolve_figs_detail import fig_prompt, fig_records, fig_skill_step, fig_test_flow, fig_train_set  # noqa: E402
PUR = ('#7B4FA3', '#EFE6F7')   # R2-MAD
TEAL = ('#1F7A7A', '#DDF1F0')  # SkillOpt


def cyl(x, y, w, h, color, fill, lines):
    ry = 9
    b = f'<path d="M{x},{y + ry} V{y + h - ry} A{w / 2},{ry} 0 0 0 {x + w},{y + h - ry} V{y + ry}" fill="{fill}" stroke="{color}" stroke-width="1.6"/>'
    b += f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{fill}" stroke="{color}" stroke-width="1.6"/>'
    for i, s in enumerate(lines):
        b += t(x + w / 2, y + ry + 22 + i * 15, s, size=10.5, anchor='middle', bold=(i == 0))
    return b


def lines(x, y, items, size=10.5, step=17, color='#222'):
    return ''.join(t(x, y + i * step, s, size=size, color=color) for i, s in enumerate(items))


def three_agents(cx, cy, r=15, gap=58):
    b = ''
    for i, k in enumerate('GAI'):
        c, l, name = C_EXP[k]
        b += agent(cx + (i - 1) * gap, cy, r, c, l, label=name.replace('专家', ''), label_side='below')
    return b


# ------------------------------------------------------------------------------------------- figure 1: overview
def fig1():
    b = group(14, 44, 176, 250, '输入：一条样本', sub='（两个数据集各自的标签集）')
    b += film(30, 100, 46, 30) + wave(86, 103, 40, 24)
    b += t(53, 144, '8 帧', size=10, anchor='middle', color='#555') + t(106, 144, '音轨', size=10, anchor='middle', color='#555')
    b += doc(28, 158, 144, 46, ['字幕 / 台词'], size=10)
    b += lines(28, 226, ['候选 = 数据集的全部标签', 'GPT 没有音轨'], size=10.5, color='#555')
    # 1 experts
    b += module(214, 44, 236, 250, NEW[0], NEW[1], '三专家 第 0 轮', 1, '沿用 v4 专家提示词，去掉反思')
    b += llm_tag(0, 14, 'LLM ×3', right=450)
    b += three_agents(332, 128)
    b += lines(228, 188, ['各自独立作答：1–2 个标签', '+ 带位置的证据'], size=10.5)
    b += lines(228, 232, ['图谱专家额外拿到冻结的', 'Gemini 图谱与组织文本'], size=10, color='#555')
    b += arrow([(190, 170), (214, 170)])
    # route
    b += diamond(510, 186, 54, 52, ['交集恰好', '1 个标签？'])
    b += arrow([(450, 186), (456, 186)])
    b += t(510, 256, '程序判定', size=10.5, anchor='middle', color='#555')
    b += arrow([(510, 134), (510, 62)]) + t(518, 106, '是', size=11.5, color='#2D6A4F', bold=True)
    b += out_box(456, 14, 108, 48, ('输出共同标签', '一致分支 ≈85%'))
    b += arrow([(564, 186), (590, 186)]) + t(566, 176, '否', size=11.5, color='#C0392B', bold=True)
    # 2 debate 1 / 3 debate 2
    for x0, n, ttl in [(590, 2, '辩论 第 1 轮'), (808, 3, '辩论 第 2 轮')]:
        b += module(x0, 44, 200, 250, NEW[0], NEW[1], ttl, n)
        b += llm_tag(0, 14, 'LLM ×3', right=x0 + 200)
        b += three_agents(x0 + 100, 118, r=13, gap=56)
        b += lines(x0 + 12, 172, ['每位专家看同伴上一轮的', '答案与理由，可改答案；', '改变观点必须引用证据', '', '输出：答案 + 理由 + 证据'], size=10.5)
    b += arrow([(790, 186), (808, 186)])
    b += module(1026, 44, 128, 250, NEW[0], NEW[1], '汇总器', 4)
    b += llm_tag(0, 14, 'LLM ×1', right=1154)
    b += agent(1090, 118, 16, CTRL[0], CTRL[1])
    b += lines(1036, 166, ['读完整辩论', '历史，给出', '最终标签'], size=10.5)
    b += arrow([(1008, 186), (1026, 186)])
    b += arrow([(1154, 186), (1166, 186)])
    b += out_box(1166, 162, 76, 48, ('最终', '标签'))
    # R2-MAD band
    b += group(590, 316, 418, 140, 'R²-MAD 外挂：经验召回（只改辩论两轮）', color=PUR[0], fill=PUR[1] + '66')
    b += cyl(606, 372, 92, 64, PUR[0], '#fff', ['经验库', '训练集辩论'])
    b += lines(712, 376, ['每位专家各检索自己的条目', '检索键 = 题目（综合 Caption + 情感识别问题）', '　　　+ 自己上一轮回答 + 上一轮辩论摘要', '取回案例 + 给同伴答案标“可靠 / 不可靠”', '第 0 轮不检索；①和④沿用静态提示词'], size=10.2, step=15.5)
    b += arrow([(700, 316), (700, 294)], PUR[0]) + arrow([(918, 316), (918, 294)], PUR[0])
    # SkillOpt band
    b += group(214, 478, 940, 136, 'SkillOpt 外挂：训练得到的技能文档（拼进该角色的 system prompt；训练后冻结）', color=TEAL[0], fill=TEAL[1] + '66')
    docs = [(232, '技能·图谱', '①'), (332, '技能·音频字幕', '①'), (452, '技能·图像', '①'), (590, '技能·辩论1', '②'), (808, '技能·辩论2', '③'), (1026, '技能·汇总器', '④')]
    for x0, name, tag in docs:
        w = 96 if x0 not in (332,) else 110
        b += doc(x0, 520, w, 56, [name, '(.md)'], size=10, fold=8, stroke=TEAL[0])
        b += f'<circle cx="{x0 + w - 6}" cy="{520}" r="9" fill="{TEAL[0]}"/>' + t(x0 + w - 6, 524, tag, size=10, anchor='middle', color='#fff', bold=True)
    b += t(232, 600, '阶段一先训练 ① 的三份；冻结后阶段二依次训练 ② ③ ④', size=10.5, color='#555')
    b += legend(640)
    return svg(b, 664)


# ------------------------------------------------------------------------------------------- figure 2: R2-MAD offline memory
def fig2():
    b = group(14, 44, 150, 330, '训练样本', sub='先筛出不一致样本')
    b += lines(24, 112, ['目录全部样本', '去掉旧 400 条：', 'MER2024 969', '+ MELD 2408', '= 3,377 条', '', '各模型先跑三专家', '第 0 轮，只留', '不一致的样本', '', '标准标签只写进', '经验库，不进提问'], size=10.2, step=17)
    b += arrow([(164, 200), (190, 200)])
    b += module(190, 44, 256, 330, NEW[0], NEW[1], 'Caption（Gemini 一次）', 1, '同时看三个模态，写一段综合描述')
    b += llm_tag(0, 14, 'LLM ×1', right=446)
    b += film(206, 104, 40, 26) + wave(252, 106, 36, 22) + doc(296, 100, 30, 34, [], fold=6)
    b += t(206, 152, '一次调用，同时给 Gemini：', size=10.5, bold=True)
    b += lines(206, 170, ['· 8 帧画面', '· 音轨', '· 字幕 / 台词'], size=10.2, step=16)
    b += lines(206, 226, ['输出：一段 Caption，涵盖画面、', '声音、台词三方面（不给标签、', '不做情绪判断）'], size=10.2, step=16)
    b += doc(206, 280, 224, 80, ['题目 Q ='], title=None, size=10.5)
    b += lines(214, 310, ['Gemini 的综合 Caption', '+ 情感识别问题（含该数据集标签集）', '两个模型的经验库共用这份 Caption'], size=10, step=15)
    b += arrow([(446, 200), (472, 200)])
    b += module(472, 44, 252, 330, NEW[0], NEW[1], '训练辩论（无经验）', 2, '强制跑满 2 轮，每轮都记录')
    b += llm_tag(0, 14, 'LLM ×8', right=724)
    steps = [('第 0 轮：三专家（筛选时已跑）', '复用，0 次'), ('辩论第 1 轮 + 摘要', 'LLM×3+1'), ('辩论第 2 轮 + 摘要', 'LLM×3+1')]
    for i, (s, c) in enumerate(steps):
        y0 = 104 + i * 72
        b += f'<rect x="488" y="{y0}" width="220" height="52" rx="8" fill="#fff" stroke="{NEW[1]}" stroke-width="1.3"/>' + t(498, y0 + 22, s, size=11, bold=True) + t(498, y0 + 40, c + ('，' if i else '；') + '用标准标签判对错', size=10, color='#555')
        if i:
            b += arrow([(598, y0 - 20), (598, y0)])
    b += t(488, 336, '摘要 = “Dynamic: … Insight: …”，只写', size=10, color='#555') + t(488, 351, '立场分布与论证模式，不含具体标签', size=10, color='#555')
    b += arrow([(724, 200), (750, 200)])
    b += module(750, 44, 262, 330, CODE[0], CODE[1], '写入经验库', 3, '程序，每位专家每轮一条')
    b += code_tag(0, 14, right=1012)
    b += lines(764, 104, ['检索键（embedding）：', '　Q + 该专家上一轮回答', '　+ 上一轮辩论摘要', '', '内容（取回后放进提示词）：', '　Q、标准标签、', '　该专家本轮回答、', '　是否改变立场、本轮是否答对', '', '元数据：专家、轮次、', '　上一轮共识率、是否答对'], size=10.3, step=16)
    b += arrow([(1012, 200), (1032, 200)])
    b += cyl(1032, 110, 100, 78, PUR[0], PUR[1], ['主经验库', '按专家、数据集', '过滤'])
    b += cyl(1032, 220, 100, 78, PUR[0], PUR[1], ['回答库', '每条回答的', 'embedding'])
    b += t(1140, 150, '检索', size=10.5, color=PUR[0]) + t(1140, 260, '算同伴', size=10.5, color=PUR[0]) + t(1140, 275, '可靠度', size=10.5, color=PUR[0])
    b += legend(396)
    return svg(b, 418)


# ------------------------------------------------------------------------------------------- figure 3: R2-MAD online round
def fig3():
    b = group(14, 44, 200, 396, '第 t 轮（t = 1, 2）', sub='一位专家 i 的视角')
    b += lines(26, 100, ['已有：', '· 题目 Q（综合 Caption + 问题）', '· 专家 i 上一轮回答', '· 同伴上一轮回答', '· 上一轮辩论摘要', '· 上一轮共识率', '　（最多同标签人数 / 3）', '', '测试样本：只用于检索，', '不读标签'], size=10.3, step=17)
    b += arrow([(214, 240), (240, 240)])
    b += module(240, 44, 214, 396, CODE[0], CODE[1], '检索键', 1, '程序')
    b += code_tag(0, 14, right=454)
    b += doc(254, 104, 186, 120, ['key ='], size=10.5)
    b += lines(262, 138, ['题目 Q', '+ 专家 i 上一轮回答', '+ 上一轮辩论摘要'], size=10.5)
    b += lines(254, 250, ['与建库时同一套格式，', '用 embedding 模型编码', '（bge-m3，本地）'], size=10.2, color='#555')
    b += arrow([(454, 240), (480, 240)])
    b += module(480, 44, 262, 396, PUR[1], PUR[0], '取经验', 2, '只在专家 i 自己的条目里取')
    b += code_tag(0, 14, right=742)
    b += lines(494, 104, ['a. 按相似度取 top-3n 候选', 'b. MMR 重排，选出 n 条（原版脚本 n = 1）：', '　得分 = λ·相似度·r − (1−λ)·', '　　　　与已选的最大相似度', '　r = 该案例当时是否答对（1/0）', '', 'c. λ = 1 − γ·上一轮共识率（γ = 0.9）', '　共识高 → λ 小 → 偏多样性', '　共识低 → λ 大 → 偏相关且答对', '', '取回的案例可能对，也可能错，', '都会带上“是否答对”的标注'], size=10.2, step=16.5)
    b += arrow([(742, 240), (768, 240)])
    b += module(768, 44, 222, 396, PUR[1], PUR[0], '同伴可靠度', 3, '用候选池估计，程序')
    b += code_tag(0, 14, right=990)
    b += lines(782, 104, ['对每位同伴 o：', '拿 o 当前的回答，和 o 在', '候选案例里的历史回答比较，', '相似度 s 作权重：', '', '可靠度(o) = Σ s·(当时是否答对)', '　　　　　 / Σ s', '', '> 0.55 → 标“High，历史可靠”', '< 0.45 → 标“Low，历史不准”', '其余不标'], size=10.2, step=16.5)
    b += arrow([(990, 240), (1016, 240)])
    b += module(1016, 44, 218, 396, NEW[0], NEW[1], '拼提示词并作答', 4)
    b += llm_tag(0, 14, 'LLM ×1', right=1234)
    b += lines(1030, 104, ['提示词依次放入：', '1) <examples> n 条案例', '2) 同伴回答 + 可靠度标注', '3) 静态辩论提示词（输出', '　　格式、引用证据）', '', '输出：答案 + 理由 + 证据'], size=10.3, step=16.5)
    b += doc(1030, 232, 190, 56, ['共识检查 → 摘要(LLM×1)', '→ 第 t+1 轮 / 汇总'], size=10.2, fold=8)
    b += lines(1030, 312, ['结束规则沿用 v4：三人答案相同', '→ 早停输出；否则下一轮；两轮后', '仍不一致 → 静态汇总器（见图 4）'], size=10, color='#555')
    b += legend(462)
    return svg(b, 486)


# ------------------------------------------------------------------------------------------- figure 4: SkillOpt stage 1
def loop_modules(b, y=84, h=170):
    xs = [20, 258, 496, 734, 972]
    specs = [
        ('Rollout', 'LLM（看媒体）', ['目标模型带着当前技能 S', '处理一批训练样本', '', '得分：该专家的答案', '是否命中标准标签'], NEW),
        ('Reflect', 'LLM（纯文本）', ['优化器读 8 条一组的轨迹：', '失败组 → 找共同错因', '成功组 → 找该保留的做法', '写“增 / 删 / 改”补丁'], CTRL[::-1]),
        ('Aggregate + Select', 'LLM + 程序', ['相似补丁合并（失败优先）', '按重要性排序，只保留', '前 k 条（k = 学习率：', '4 → 2 余弦衰减）'], CTRL[::-1]),
        ('Update', '程序', ['把选中的编辑', '应用到技能文档 S', '得到候选 S′'], CODE),
        ('Gate', 'LLM（看媒体）', ['S′ 在验证集 60 条上', '重新作答、算准确率', '严格高于 S 才接受，', '否则丢弃并记入拒绝缓冲'], NEW),
    ]
    for i, (x0, (ttl, tag, body, col)) in enumerate(zip(xs, specs)):
        fill, stroke = col
        b += module(x0, y, 232, h, fill, stroke, ttl, i + 1)
        b += llm_tag(0, y - 30, tag, right=x0 + 232) if 'LLM' in tag else code_tag(0, y - 30, right=x0 + 232)
        b += lines(x0 + 14, y + 64, body, size=10.5, step=17)
        if i:
            b += arrow([(x0 - 26, y + h / 2), (x0, y + h / 2)])
    return b


def fig4():
    b = group(14, 44, 1226, 330, '一个专家的 SkillOpt 训练循环（图谱 / 音频字幕 / 图像专家各跑一遍，各自一份技能文档）', color=TEAL[0], fill=TEAL[1] + '33')
    b = loop_modules(b, y=100)
    b += doc(20, 302, 200, 52, ['技能文档 S', '起点：空文件'], size=10.5, stroke=TEAL[0])
    b += arrow([(60, 302), (60, 270)], TEAL[0])
    b += arrow([(1088, 270), (1088, 288), (180, 288), (180, 302)], '#999', True)
    b += t(640, 282, '接受 S′ → 成为新的 S，进入下一步；拒绝 → S 不变', size=10.5, color='#555', anchor='middle')
    b += group(250, 392, 520, 112, '每个 epoch 结束', color=TEAL[0], fill='#fff')
    b += lines(262, 436, ['Slow Update：同一批题分别用上一轮、这一轮的 S 再跑，', '分成 变好 / 退步 / 一直错 / 一直对，写一段全局指导，防遗忘', 'Meta Skill：给优化器自己看的编辑经验笔记，不进专家提示词'], size=10.2, step=16)
    b += group(790, 392, 450, 112, '设置（SkillOpt 默认值，待你确认）', color='#999', fill='#fff')
    b += lines(802, 436, ['训练：新 400 条；验证（门控）：60 条', '每步 40 条，每 8 条一组；3–4 个 epoch', '优化器：与被优化模型同家（待确认）', '真实标签只用于打分和给优化器看错因'], size=10.2, step=16)
    b += legend(526)
    return svg(b, 550)


# ------------------------------------------------------------------------------------------- figure 5: SkillOpt stage 2
def fig5():
    b = ''
    xs = [14, 262, 510, 758, 1006]
    w = 228
    # freeze + R0 + route
    b += module(xs[0], 44, w, 360, TEAL[1], TEAL[0], '冻结专家，取辩论样本', 0, '阶段一产物')
    b += doc(xs[0] + 14, 100, 96, 40, ['技能·图谱', '(冻结)'], size=9.8, fold=7, stroke=TEAL[0]) + doc(xs[0] + 118, 100, 96, 40, ['技能·音频字幕', '(冻结)'], size=9.8, fold=7, stroke=TEAL[0])
    b += doc(xs[0] + 14, 150, 96, 40, ['技能·图像', '(冻结)'], size=9.8, fold=7, stroke=TEAL[0])
    b += lines(xs[0] + 14, 222, ['用冻结的专家在训练集', '上跑第 0 轮（LLM×3/条）', '', '路由：交集恰好 1 个标签', '→ 一致，不参与；', '否则 → 不一致样本池', '（约 15%，约 60 条）', '', '训练样本数很少 → 待确认'], size=10.2, step=16.5)
    stages = [
        (xs[1], '训练 辩论第 1 轮 的技能', ['得分：第 1 轮三位专家', '答案命中标准标签的比例', '', '上游：冻结专家 + 空技能', '之后各轮 / 汇总器：', '暂用无技能的静态提示词']),
        (xs[2], '训练 辩论第 2 轮 的技能', ['得分：第 2 轮三位专家', '答案命中标准标签的比例', '', '上游：冻结专家 +', '冻结的辩论 1 技能']),
        (xs[3], '训练 汇总器 的技能', ['得分：最终标签', '是否等于标准标签', '', '上游：冻结专家 +', '冻结的辩论 1、2 技能']),
    ]
    for i, (x0, ttl, body) in enumerate(stages):
        b += module(x0, 44, w, 360, NEW[0], NEW[1], ttl, i + 1)
        b += lines(x0 + 14, 104, ['循环同图 7、8：', 'Rollout → Reflect →', 'Aggregate/Select → Update', '→ Gate'], size=10.3, step=16.5)
        b += lines(x0 + 14, 190, body, size=10.2, step=16.5)
        b += doc(x0 + 14, 330, 120, 56, ['新技能文档', '起点：空文件'], size=10, fold=8, stroke=TEAL[0])
        if i:
            b += arrow([(x0 - 20, 224), (x0, 224)])
    b += arrow([(xs[0] + w, 224), (xs[1], 224)])
    b += module(xs[4], 44, 228, 360, OUT[0], OUT[1], '组装并部署', 4)
    b += arrow([(xs[3] + w, 224), (xs[4], 224)])
    b += lines(xs[4] + 14, 104, ['3 份专家技能 + 辩论 1、', '辩论 2、汇总器各 1 份', '= 每个模型共 6 份', '', '测试流程（旧 400 条）：', '三专家 R0 → 路由 →', '一致：共同标签', '不一致：辩论 1 → 辩论 2', '→ 汇总器', '', '评估只在测试集上做，', '不再改任何技能'], size=10.2, step=16.5)
    b += legend(426)
    return svg(b, 450)


# ------------------------------------------------------------------------------------------- figure 6: SkillOpt experts only
def fig6():
    b = group(14, 44, 560, 300, '训练（只训练三位专家，第 0 轮提示词）', color=TEAL[0], fill=TEAL[1] + '33')
    b += lines(28, 98, ['训练：新 400 条；验证（门控）：新 60 条（全部 60 条都能用，', '因为专家在每条样本上都作答，不受“不一致样本太少”影响）'], size=10.3, step=16)
    for i, k in enumerate('GAI'):
        c, l, name = C_EXP[k]
        y0 = 140 + i * 66
        b += agent(52, y0 + 22, 15, c, l)
        b += f'<rect x="84" y="{y0}" width="296" height="54" rx="8" fill="#fff" stroke="{c}" stroke-width="1.4"/>'
        b += t(94, y0 + 22, name + '：独立跑一遍图 7 的循环', size=11, bold=True) + t(94, y0 + 40, '得分 = 该专家第 0 轮答案是否命中标准标签', size=10, color='#555')
        b += arrow([(380, y0 + 27), (410, y0 + 27)], TEAL[0])
        b += doc(410, y0 + 4, 148, 46, ['技能·' + name.replace('专家', ''), '(.md，训练后冻结)'], size=10, fold=8, stroke=TEAL[0])
    b += arrow([(574, 194), (610, 194)])
    b += group(610, 44, 630, 300, '测试：旧 400 条，其余流程完全不变（静态提示词）', color='#999', fill='#fff')
    b += lines(624, 96, ['三位专家带上各自冻结的技能作答（第 0 轮）', '→ 路由 → 一致：共同标签；不一致：辩论 1 → 辩论 2 → 汇总器', '辩论、汇总器沿用静态提示词，没有任何技能或经验'], size=10.5, step=17)
    xs = [624, 770, 916, 1062]
    for x0, ttl, tag in [(xs[0], '三专家 R0', 'LLM×3'), (xs[1], '路由', '程序'), (xs[2], '辩论 1 → 2', 'LLM×6'), (xs[3], '汇总器', 'LLM×1')]:
        col = CODE if tag == '程序' else NEW
        b += f'<rect x="{x0}" y="164" width="130" height="64" rx="8" fill="{col[0]}" stroke="{col[1]}" stroke-width="1.5"/>' + t(x0 + 65, 192, ttl, size=11.5, anchor='middle', bold=True) + t(x0 + 65, 212, tag, size=10, anchor='middle', color='#555')
    for a, c in zip(xs, xs[1:]):
        b += arrow([(a + 130, 196), (c, 196)])
    b += doc(624, 250, 592, 80, ['评价（和同一批旧 400 条上缓存的 v4 第 0 轮、v4 全流程比）：'], size=10.5, fold=8)
    b += lines(632, 288, ['① 每位专家第 0 轮的准确率：加技能前 vs 后（加技能前是缓存，0 次调用）', '② 一致 / 不一致分支的大小与各自准确率；不一致样本有没有变少', '③ 整体 400 条的最终准确率，以及相对 Direct 均值的差'], size=10.2, step=16)
    b += legend(360)
    return svg(b, 384)


css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1260px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}
h1{font-size:25px}h3{font-size:16px;margin:18px 0 4px;color:#444}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 16px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:5px 8px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.muted{color:#666}.small{font-size:13px}.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}
.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}code{background:#eee;padding:0 4px;border-radius:3px}
.fig{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px;margin:10px 0}.cap{font-size:14px;color:#333;margin:4px 6px 12px;line-height:1.7}
pre{background:#f4f4f4;padding:10px 14px;border-radius:6px;font-size:13px;line-height:1.55;overflow-x:auto}'''

P = []
P.append('<h1>自进化设计草案：R²-MAD 与 SkillOpt（不一致分支，辩论 2 轮）</h1>')
P.append('<p class="muted">日期 2026-11-05。<b>只有设计，没有实现、没有运行、没有结果。</b>名字暂定 v6-R²MAD、v6-SkillOpt，你可以改。图中橙色 = 大模型调用，蓝灰 = 程序，紫 = R²-MAD 独有，青绿 = SkillOpt 独有。</p>')
P.append('<section class="panel"><h2>零、现在共有三个版本</h2><table><tr><th>版本</th><th>训练什么</th><th>训练样本</th><th>测试</th></tr>'
         '<tr><td><b>R²-MAD</b></td><td>不训练提示词；用训练集建经验库</td><td>目录全部样本去掉旧 400 条，其中不一致的</td><td>旧 400 条里的不一致样本</td></tr>'
         '<tr><td><b>SkillOpt-E</b>（新增）</td><td>只训练三位专家的技能（判断一致前）</td><td>新 400 条训练 + 新 60 条验证</td><td>旧 400 条全部</td></tr>'
         '<tr><td><b>SkillOpt-全</b></td><td>专家 → 冻结 → 辩论 1、辩论 2、汇总器</td><td>阶段一同上；阶段二只用不一致样本</td><td>旧 400 条全部</td></tr></table>'
         '<p class="small muted">SkillOpt-E 就是 SkillOpt-全 的阶段一，所以先做 E：它的产物直接成为全版本的起点，不会重复花费。</p></section>')
P.append('<section class="panel"><h2>一、你定下的要求，和我对它们的理解</h2><table><tr><th>你说的</th><th>我的理解（默认）</th></tr>'
         '<tr><td>引用会话里的 400 条作训练集</td><td>新 400 条（MER2024 200 + MELD 200，标签分布对齐全集）= 训练集；同一次选出的 60 条（各 30）= 验证集；都与旧 400 条无重叠。</td></tr>'
         '<tr><td>总共辩论 2 轮；去掉反思</td><td>流程 = 三专家第 0 轮 → 路由 → 辩论 1 → 辩论 2 → 汇总器。分支判定只用第 0 轮答案：交集恰好 1 个标签 = 一致，否则不一致。</td></tr>'
         '<tr><td>R²-MAD：检索题目 = 每个模态的 Caption + 情感识别问题</td><td>只把原版 R²-MAD 检索键里的“题目”换成 Caption + 问题，其余（自己上一轮回答、上一轮摘要）保持原版；Caption 统一由 Gemini 生成。</td></tr>'
         '<tr><td>R²-MAD 只跑不一致样本</td><td>测试时只对不一致样本做辩论（第 0 轮沿用 v4 缓存，0 次调用）。</td></tr>'
         '<tr><td>R²-MAD 的训练集 = 目录全部样本去掉旧 400 条中的不一致样本；Gemini、GPT 先各跑一轮筛出来</td><td>候选池 = MER2024 969 + MELD 2408 = 3,377 条（已核对服务器清单，均通过媒体过滤）；每个模型对全部候选跑三专家第 0 轮，按同一路由规则留下“不一致”的样本，Gemini、GPT 各留各的、各建各的经验库；不一致样本太多时训练集上限 400 条（默认每个数据集 ≤ 200，分层抽样）；留下的样本再强制辩论满 2 轮（第 0 轮复用）。</td></tr>'
         '<tr><td>SkillOpt：先训练不同专家，冻结后再训练辩论 1、辩论 2 和汇总器</td><td>阶段一：三位专家各一份技能文档；阶段二：依次训练辩论 1、辩论 2、汇总器各一份（共 6 份/每个模型）。SkillOpt 跑全部 400 条（测试时受训专家会改变分支，所以必须全跑）。</td></tr>'
         '<tr><td>目录 emotion_eval_5models_4frames_20261030 去掉旧 400 条</td><td>训练、验证样本都从这里选且不含旧 400 条，已满足。</td></tr></table></section>')
P.append('<section class="panel"><h2>二、流程图</h2>'
         '<h3>总览</h3>'
         '<div class="fig">' + fig1() + '</div><p class="cap"><b>图 1　共同骨架与两种自进化的挂载点。</b>主流程（橙）对两个方法完全相同：三专家 → 一致则直接输出 → 否则辩论 2 轮 → 汇总器。R²-MAD 只改两轮辩论（给每位专家带上检索到的经验和同伴可靠度），不动专家和汇总器；SkillOpt 改全部四个模块（给每个角色的 system prompt 加一份训练出来的技能文档），不检索。</p>'
         '<h3>R²-MAD</h3>'
         '<div class="fig">' + fig_train_set() + '</div><p class="cap"><b>图 2　R²-MAD 训练集怎么来。</b>候选池 3,377 条 → 补图谱 → Gemini、GPT 各跑三专家第 0 轮 → 按第 0 轮路由留下不一致样本 → 超过上限就分层抽样 → 对留下的样本做 Caption 合成 Q → 得到每个模型自己的训练集 T（≤ 400 条）。</p>'
         '<div class="fig">' + fig_records() + '</div><p class="cap"><b>图 3　用训练集 T 建库：一个训练样本产生哪些记录。</b>复用第 0 轮，再强制跑满 2 轮辩论（不用经验），中间各生成一次摘要和共识率；每位专家每轮写一条记录，键由“题目 + 自己上一轮输出 + 上一轮摘要”拼成，值由“题目 + 标准标签 + 本轮输出 + 是否改立场 + 对错”拼成。</p>'
         '<div class="fig">' + fig_test_flow() + '</div><p class="cap"><b>图 4　测试时的完整流程。</b>只对不一致样本：读第 0 轮缓存 → 摘要 S0 → 辩论 1（每位专家检索并作答）→ 三人相同则早停，否则摘要 S1 → 辩论 2 → 仍不一致才调用静态汇总器。结束规则沿用 v4（不是原版的多数票）。</p>'
         '<div class="fig">' + fig3() + '</div><p class="cap"><b>图 5　一位专家在一轮里做的四步。</b>②③是 R²-MAD 的两个贡献：“辩论状态感知的检索”（共识越高越偏多样）和“用历史经验估计同伴是否可信”。</p>'
         '<div class="fig">' + fig_prompt() + '</div><p class="cap"><b>图 6　检索结果怎么进到提示词里。</b>在 v4 辩论提示词的 JSON 上只增加两处：案例块和同伴可靠度标注，其余全部沿用。</p>'
         '<h3>SkillOpt</h3>'
         '<div class="fig">' + fig4() + '</div><p class="cap"><b>图 7　SkillOpt 阶段一：训练一个专家的循环。</b>目标模型不动，只改一份 Markdown 技能文档；每次修改要过验证集门控。三位专家各自独立训练。</p>'
         '<div class="fig">' + fig_skill_step() + '</div><p class="cap"><b>图 8　循环里一步的数据流（含示意内容）。</b>40 条样本 → 5 个 minibatch → 失败组 / 成功组各自写补丁 → 分层合并并排序，只保留前 k 条 → 应用到技能文档 → 在验证集上严格更高才接受。</p>'
         '<div class="fig">' + fig5() + '</div><p class="cap"><b>图 9　SkillOpt 阶段二：冻结专家后，依次训练辩论 1、辩论 2、汇总器。</b>每一段的循环和图 7、图 8 相同，只是被训练的角色、得分不同；上游已训练好的技能被冻结。</p>'
         '<div class="fig">' + fig6() + '</div><p class="cap"><b>图 10　新增版本 SkillOpt-E：只训练三位专家（图 7 的循环），其余流程不动。</b>它等于图 9 的“阶段一”单独成一个版本：不训练辩论与汇总器，所以不受不一致样本太少的影响；也是对整个 SkillOpt 路线最便宜的先行检验——如果专家技能本身就没有提升，阶段二不必做。</p></section>')
P.append('<section class="panel"><h2>二·补　R²-MAD 的检索键与值（逐字段，来自原版源码 <code>memory_utils.py</code>、<code>agent.py</code>，换成我们的数据）</h2>'
         '<p class="small muted">每条记录对应（一条训练样本 s，一位专家 e，一轮 r ∈ {0,1,2}）。Q = Gemini 一次综合 Caption + 情感识别问题（含该数据集标签集）。</p>'
         '<table><tr><th style="width:15%">部分</th><th>内容</th><th style="width:30%">用在哪</th></tr>'
         '<tr><td><b>键 K(s,e,r)</b></td><td>Q<br>+ 专家 e 第 <b>r−1</b> 轮的回答（r = 0 时没有）<br>+ 第 <b>r−1</b> 轮的辩论摘要（r = 0 时没有）<br>三者拼成一段文本，用 embedding 模型编码。键描述的是“专家 e 在作第 r 轮回答<b>之前</b>的状态”。</td><td>测试时第 t 轮，用当前的 Q + 专家 e 第 t−1 轮回答 + 第 t−1 轮摘要编码成查询向量，和库里同一位专家的键算余弦相似度。</td></tr>'
         '<tr><td><b>值 V(s,e,r)</b></td><td>① 题目 Q<br>② 标准标签（原版是完整标准解答，我们只有标签）<br>③ 专家 e <b>第 r 轮</b>的完整回答（答案 + 理由 + 证据）<br>④ 这一轮有没有改变立场（r = 0 为 N/A）<br>⑤ 这一轮的回答是对还是错</td><td>取回后原样放进提示词的 &lt;examples&gt; 块。含义是“在类似的状态下，专家后来是这样答的，结果是对 / 错”。</td></tr>'
         '<tr><td><b>元数据</b></td><td>专家、轮次 r、<b>上一轮共识率</b>（三人里最多的同标签人数 / 3：1/3、2/3 或 1）、本轮是否答对、最终是否答对（、数据集）</td><td>过滤（只取同一位专家；我们再加：只取同一个数据集）；MMR 里的 r(case) = 本轮是否答对；同伴可靠度里的“当时是否答对”。</td></tr>'
         '<tr><td><b>回答库</b></td><td>键 = (样本, 轮次, 专家) 的编号；向量 = 该专家该轮回答的 embedding</td><td>估计同伴可靠度：对每个候选案例，取该案例里另外两位专家在第 r−1 轮的回答向量，和现在同伴的回答比相似度。</td></tr></table>'
         '<div class="note"><b>读源码得到的三个细节</b><ul>'
         '<li>检索时<b>只按“专家”过滤，不限制轮次</b>：测试第 1 轮的查询，也可能取到库里第 0 轮的条目（它们的键只有 Q，没有回答和摘要，相似度通常更低）。</li>'
         '<li>“题目”在键和值里<b>都出现</b>：键里的 Q 决定“像不像”，值里的 Q 让模型看到那个案例在说什么。因为我们的 Q 含一段综合 Caption，一条案例会较长；每位专家带 n 条案例，n 越大提示词越长。</li>'
         '<li>值里的证据引用的是那条训练样本自己的帧编号和时间，当前样本没有这些帧；只能把它当作“答案与理由的写法”参考，这是视频任务和原版文本任务的差别。</li></ul></div></section>')
P.append('<section class="panel"><h2>三、数据与评价</h2><table><tr><th>用途</th><th>样本</th><th>说明</th></tr>'
         '<tr><td>训练（R²-MAD）</td><td>3,377 条里的不一致样本</td><td>建经验库。每个模型各自的不一致样本，上限 400 条；比例未知，要跑完第 0 轮才知道（旧 400 条是按“≥3 模型答对”筛的偏容易，约 15%，整体池预计更高，很可能触到上限）。</td></tr>'
         '<tr><td>训练（SkillOpt）</td><td>新 400 条</td><td>rollout 与反思。标签只在训练里用。</td></tr>'
         '<tr><td>验证（门控）</td><td>新 60 条</td><td>SkillOpt 每次修改的接受 / 拒绝；R²-MAD 默认不用验证集，超参取论文默认值。</td></tr>'
         '<tr><td>测试</td><td>旧 400 条</td><td>SkillOpt：全部 400 条（受训专家改变分支）；R²-MAD：其中不一致的 117 条（Gemini 62 + GPT 55），可直接和 v4 / Direct / v5 对比。</td></tr></table>'
         '<ul><li><b>对照</b>：Direct 单次均值 60.4（Gemini 36.6 + GPT 23.8）、Direct 三次投票 61.8、v4 辩论 45、v5 最好的 E（63）。</li>'
         '<li><b>“有提升”的标准沿用</b>：不一致 117 条合并后比 Direct 均值多至少 4 条，且两个模型各自不低于自己的均值；SkillOpt 另报全 400 条合并后的总数。</li>'
         '<li><b>必须报告</b>：每个阶段后的准确率（专家 R0、辩论 1、辩论 2、最终）、被改答案数及改对 / 改错、路由后不一致样本数的变化、调用数。</li>'
         '<li><b>噪声</b>：Direct 单次运行波动 6 条，门控又只有 60 条验证样本，所以任何 1–3 条的差别都不解读。</li></ul></section>')
P.append('<section class="panel"><h2>四、调用量估计（粗算，未实测；每个模型）</h2><table><tr><th>环节</th><th class="n">调用</th><th>备注</th></tr>'
         '<tr><td>筛选：3,377 条各跑三专家第 0 轮</td><td class="n">≈ 10,100</td><td>3 × 3,377。图谱专家还要一份冻结的 Gemini 图谱：对这 3,377 条补生成约 3,377 次 Gemini 调用（两个模型共用，一次）</td></tr>'
         '<tr><td>Caption（两个模型共用，只做一次）</td><td class="n">≤ ≈ 900–1,000</td><td>≤ 400 条训练样本（两个模型的并集，最多约 800）+ 测试集不一致样本，各 × 1 次</td></tr>'
         '<tr><td>R²-MAD 建库：不一致样本强制辩论 2 轮</td><td class="n">≤ 3,200</td><td>每条 3 + 3 + 2 次摘要 = 8（第 0 轮复用）；上限 400 条 × 8；不到上限则更少</td></tr>'
         '<tr><td>R²-MAD 测试（不一致 117 条）</td><td class="n">≈ 500</td><td>每条 3 + 1 + 3 + 1 = 8；第 0 轮复用缓存</td></tr>'
         '<tr><td>SkillOpt 阶段一：三位专家</td><td class="n">≈ 9,000</td><td>每位 3 epoch × 10 步 × (40 rollout + 最多 60 门控) 约 3,000 次看媒体的调用；优化器纯文本调用另算约 300 / 位</td></tr>'
         '<tr><td>SkillOpt 阶段二：辩论 1 / 辩论 2 / 汇总器</td><td class="n">≈ 3,000</td><td>只用不一致样本，每步 rollout 3 次/条；门控样本很少</td></tr>'
         '<tr><td>SkillOpt 测试（旧 400 条全跑）</td><td class="n">≈ 1,700</td><td>1,200 次 R0 + 约 60 条不一致 × 8</td></tr></table>'
         '<p class="small muted">SkillOpt 阶段一最贵，可通过每步 20 条、2 个 epoch 降到约 1/3；这是一个需要你拍板的取舍。</p></section>')
P.append('<section class="panel"><h2>五、文件规划（先列，批准后才建）</h2><pre>'
         'versions/v6/\n'
         '  base_flow.py        共同骨架：三专家 R0（沿用 v4 提示词）→ 路由 → 辩论 1 → 辩论 2 → 汇总器（去掉反思），可插入“经验”或“技能”\n'
         '  captions.py         Gemini 一次综合 Caption（同时看帧 / 音轨 / 字幕）+ 缓存\n'
         '  rmad/\n'
         '    prompts_rmad.py   经验块与同伴可靠度标注的拼接、辩论摘要提示词（静态，改写自原版）\n'
         '    memory.py         经验库：写入、检索（numpy 余弦 + MMR，不依赖 ChromaDB）、同伴可靠度\n'
         '    build_memory.py   训练集强制辩论 2 轮 → 写入经验库\n'
         '    run_rmad.py       不一致样本的辩论 2 轮（带检索）→ 汇总 → 指标\n'
         '  skillopt/\n'
         '    prompts_skillopt/ 直接用 SkillOpt 仓库的 analyst / merge / ranking / slow_update / meta_skill 提示词（MIT，注明出处）\n'
         '    skill_loop.py     最小训练循环：rollout → reflect → aggregate → select → update → gate\n'
         '    train_experts.py  阶段一：三位专家各训练一份技能\n'
         '    train_debate.py   阶段二：依次训练辩论 1、辩论 2、汇总器\n'
         '    run_skillopt.py   用冻结技能跑测试集 → 指标\n'
         'scripts/\n'
         '  build_selfevolve_design_page.py   本页\n'
         '  build_selfevolve_results_page.py  结果页（跑完之后再做）\n'
         'docs/v6-selfevolve-design.html      本页\n'
         '服务器 outputs/v6_rmad/&lt;provider&gt;/…  与  outputs/v6_skillopt/&lt;provider&gt;/{expert_skills, debate_skills, runs}/…\n'
         'metrics/v6_rmad_*.json，metrics/v6_skillopt_*.json，metrics/findings_log.md（新结论）</pre>'
         '<p class="small muted">实现方式的取舍：SkillOpt 官方包的目标模型接口以文本为主，我们的输入是 8 帧 + 音轨 + 字幕，且已有 v4 的缓存与格式修复，所以默认只借用它的提示词和循环思想，自己写最小循环（约 300 行），而不是直接依赖它的包。</p></section>')
P.append('<section class="panel"><h2>六、请你确认（<b>1–5 必须先定</b>，括号里是我的默认）</h2><ol>'
         '<li><b>训练样本太少。</b>新 400 条里不一致样本约 60 条（每个模型），验证集 60 条里只有约 9 条。阶段二的辩论 1、2 和汇总器只有这点样本可训练，门控几乎没有统计意义。怎么办？（默认：阶段二只用训练集的不一致样本，从中留出 1/3 做门控，再并入验证集里的不一致样本；接受“结果主要看趋势”。备选：放宽不一致定义，R0 三专家标签不完全相同就算，样本约 2–3 倍，但与测试时的分布不一致。）</li>'
         '<li><b>测试集。</b>SkillOpt 测旧 400 条全部，R²-MAD 测其中 v4 判定的 117 条不一致样本，对吗？分支改为只用 R0 判定（没有反思）后，不一致集合会和 v4 的 117 条略有出入；R²-MAD 测试时是沿用这 117 条，还是按 R0 重新判定？（默认：按 R0 重新判定，两边都报；R0 缓存可复用，0 次调用。）</li>'
         '<li><b>R²-MAD 训练池（已按你的话定为：全目录去掉旧 400 条 → 先筛不一致）。</b>三个细节：(a) 池里要不要也去掉新选的 230 + 230（SkillOpt 的训练 / 验证样本）？默认不去掉：R²-MAD 不用验证集，只要别和旧 400 条的测试集重叠；(b) 上限已按你的话定为 ≤ 400：“两个数据集合计 400”（默认：每个数据集 ≤ 200，在该数据集的不一致池里按标签占比分层抽样、种子 42）还是“每个数据集各 400”？若一个数据集不足 200，是否让另一个补满合计 400？ (c) 筛选的“不一致”按第 0 轮判定（没有反思），与测试时的路由一致。</li>'
         '<li><b>R²-MAD 的检索键</b>：只把“题目”换成 综合 Caption + 问题，保留“自己上一轮回答 + 上一轮辩论摘要”（需要每轮多 1 次摘要调用）。（默认：保留，最接近原版；备选：只用 Caption + 问题，更简单，但就不再是“辩论状态感知”。）</li>'
         '<li><b>（已按 v4 规则处理，仍请确认）两轮后仍不一致怎么出最终答案？</b>R²-MAD 原版是最后一轮多数票。（默认：用 v4 的静态汇总器提示词做一次汇总；SkillOpt 则由训练出的汇总器技能负责。）</li>'
         '<li><b>SkillOpt-E 的测试流程（新）：</b>专家换成带技能的版本后，下游辩论与汇总器怎么处理？默认：沿用 v4 静态提示词、去掉反思、辩论 2 轮（与图 1 一致，这样和 R²-MAD / SkillOpt-全 可比）；备选：完全按 v4 原流程（保留反思，辩论 ≤2 轮），这样可直接和 v4 的 319 / 307 对比。还有一个对照：同一流程不加技能，用缓存的 v4 第 0 轮结果，0 次调用。</li>'
         '<li><b>SkillOpt 优化器模型</b>（写技能编辑的模型）：默认与被优化模型同家（Gemini 优化 Gemini 专家，GPT 优化 GPT 专家）；它看到的是专家的文字回答和证据、标准标签、Caption，<b>不看视频帧</b>。要不要让它也看帧？</li>'
         '<li><b>辩论技能的粒度</b>：每轮一份、三位专家共用（默认），还是每位专家每轮一份（6 份，样本更少更难训）？专家自己的技能在辩论里是否保留？（默认：保留。）</li>'
         '<li><b>技能训练时专家的输出打分</b>：专家可以给 1–2 个标签。“是否命中”默认按第一个标签算 hard 分，两个里含正确标签算 soft 分，门控用 hard。同意吗？</li>'
         '<li><b>SkillOpt 的轮数与批量</b>：默认 3 epoch、每步 40 条；降本版 2 epoch、每步 20 条。选哪个？</li>'
         '<li><b>检索模型与取几条</b>：原版用 BAAI/bge-m3 编码（<code>configs.yaml</code> 与 <code>run_mad.py</code> 默认），向量用余弦；先取 top-3n 个语义最近的候选，再用 MMR 重排选 n 条放进提示词。n 在原版里有两个默认：<code>run_mad.py</code> 和论文评测脚本 <code>batch_run_r2mad.sh</code> 用 <b>n = 1</b>，<code>Agent</code> 类的代码默认是 3。我们的案例很长，默认 n = 1（候选池 3 条）；要不要试 n = 2 / 3？bge-m3 默认在服务器本地运行，需能下载权重。</li></ol>'
         '<div class="warn">你审核通过前，我不会写这些文件的代码，也不会调用任何模型。<br>注意（已知限制）：训练集和验证集都按“至少 3 个模型答对”筛选，偏容易，两个方法学到的东西可能不适用于真正难的样本；这和旧 400 条的偏差一致，所以相对比较仍然成立。</div></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>自进化设计草案：R²-MAD 与 SkillOpt</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v6-selfevolve-design.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
