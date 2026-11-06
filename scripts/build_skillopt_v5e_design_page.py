"""Build docs/v6-skillopt-v5e-design.html: design draft (flow charts only, nothing run) of SkillOpt applied to v5-E
(one full-modal agent: first answer -> named uncertainty -> look back -> reflect). Reuses the drawing helpers of scripts/v5_paper_figs.py.
Static HTML, no scripts, no model calls.
Sources of the numbers: update.md / metrics/findings_log.md (F11, F12); read-only server checks of 2026-11-05 on the v6 pool
(outputs/v6_rmad/pool/*/*/*/r0_summary.json, MELD dialogue ids from the 5-model evaluation manifests); the original SkillOpt loop is
drawn from the source of microsoft/SkillOpt (skillopt/engine/trainer.py, gradient/*.py, optimizer/clip.py, evaluation/gate.py, configs/_base_/default.yaml).
Usage: python scripts/build_skillopt_v5e_design_page.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_paper_figs import (CODE, CTRL, NEW, OUT, agent, arrow, chip, code_tag, diamond, doc, film, group, legend, llm_tag, module,  # noqa: E402
                           out_box, svg, t, wave)

ROOT = Path(__file__).resolve().parent.parent
TEAL = ('#1F7A7A', '#DDF1F0')  # (stroke, light) SkillOpt colour, same as the earlier design page
RED = '#C0392B'
GREEN = '#2D6A4F'


def lines(x, y, items, size=10.5, step=17, color='#222'):
    return ''.join(t(x, y + i * step, s, size=size, color=color) for i, s in enumerate(items))


def badge(x, y, s='新增'):
    return chip(x, y, s, fg=RED, bg='#fff', size=10, bold=True)[0]


# ------------------------------------------------------------------------------------------- figure 1: v5-E and where the skill plugs in
def fig1():
    b = group(14, 44, 176, 250, '输入：一条样本', sub='（不一致分支的样本）')
    b += film(30, 100, 46, 30) + wave(86, 103, 40, 24)
    b += t(53, 144, '8 帧', size=10, anchor='middle', color='#555') + t(106, 144, '音轨', size=10, anchor='middle', color='#555')
    b += doc(28, 158, 144, 40, ['字幕 / 台词'], size=10)
    b += lines(28, 216, ['候选集 C′ = 原候选 + 扩充', '原候选：三专家第 0 轮并集', '扩充：混淆矩阵 top1（程序加）', 'GPT 没有音轨'], size=10, color='#555', step=15)
    b += module(214, 44, 250, 250, NEW[0], NEW[1], '首次作答', 1, '一个全模态 agent')
    b += llm_tag(0, 22, 'LLM ×1', right=464)
    b += agent(339, 118, 15, '#C9A227', '#FFF8E6', label='全模态 agent', label_side='below')
    b += lines(226, 176, ['看 8 帧 + 字幕（+ 音轨），', '只能在 C′ 内作答，每个标签', '标明“原候选”或“扩充”：', '· 答案 + 1–3 条带位置的证据', '· 不确定点（可为空）：', '　一个具体问题 + 应回看的时间窗'], size=10.2, step=16)
    b += arrow([(190, 170), (214, 170)])
    b += diamond(532, 170, 52, 50, ['写了', '不确定点？'])
    b += arrow([(464, 170), (480, 170)])
    b += arrow([(532, 220), (532, 258)]) + t(540, 244, '否', size=11.5, color=RED, bold=True)
    b += out_box(476, 258, 112, 44, ('直接输出首答', '1 次调用'))
    b += arrow([(584, 170), (612, 170)]) + t(588, 160, '是', size=11.5, color=GREEN, bold=True)
    b += module(612, 44, 232, 250, NEW[0], NEW[1], '回看', 2, '程序取新输入 → LLM')
    b += code_tag(0, 22, right=722) + llm_tag(0, 22, 'LLM ×1', right=844)
    b += lines(624, 100, ['程序：按它指定的时间窗，', '取 16 帧 + 对应音轨片段', '', 'LLM 只回答那个问题：', '· 是 / 否 / 不确定', '· 回看时新看到的观察', '· 逐条检查首答的证据：', '　被支持 / 被削弱 / 不变'], size=10.2, step=16.5)
    b += module(872, 44, 232, 250, NEW[0], NEW[1], '反思', 3, '同一个 agent')
    b += llm_tag(0, 22, 'LLM ×1', right=1104)
    b += lines(884, 100, ['对照首答与回看结果：', '', 'KEEP　保持首答', 'REVISE　改成 C′ 里另一个标签，', '　必须引用回看得到的', '　新的、可定位的证据；', '　没有就只能 KEEP'], size=10.2, step=16.5)
    b += arrow([(844, 170), (872, 170)])
    b += arrow([(1104, 170), (1124, 170)])
    b += out_box(1124, 146, 112, 48, ('最终答案', '∈ 候选集 C′'))
    b += doc(1010, 302, 226, 82, [], fold=8, stroke='#999')
    b += t(1018, 318, 'v5-E 现状（无技能、无扩充）', size=10.5, bold=True)
    b += lines(1018, 333, ['117 条里答对 63（Direct 均值 60.4）', '只有 13 条写了不确定点，回看', '后只改了 2 条；答错的绝大多', '数没被标记 → 技能想改善这里'], size=9.6, step=13.5, color='#444')
    b += group(14, 388, 1222, 156, '技能文档 S（一个提示词、三个模块；每个模块单独更新；每个模型各一份；训练后冻结；起点只有空标题）', color=TEAL[0], fill=TEAL[1] + '55')
    specs = [('首答模块：A 区分线索 + B 何时写不确定点', ['A：原候选与扩充标签之间凭什么区分（优化器写）', 'B：什么情况值得回看、怎样写出可回看的具体问题']),
             ('回看模块：C 回看时怎么看', ['回看帧 / 音轨里先找什么、', '没有新信息时怎么答']),
             ('反思模块：D 何时改答案', ['什么算“新的、可定位的证据”、', '什么情况下应当 KEEP'])]
    for i, (ttl, body) in enumerate(specs):
        x0 = 30 + i * 400
        b += doc(x0, 430, 380, 74, body, title=ttl, fill='#fff', stroke=TEAL[0], size=10.2, fold=8)
    b += t(30, 530, '每个阶段的提示词只带自己那个模块；候选扩充块（图 5）由程序按样本写入三个阶段；输出字段与校验器不变（答案须在 C′ 内）；推理时 0 次额外调用。', size=10.2, color='#555')
    for x in (339, 728, 930):
        b += arrow([(x, 388), (x, 296)], TEAL[0])
    b += t(347, 372, '拼进提示词', size=10, color=TEAL[0])
    b += legend(562)
    return svg(b, 586)


# ------------------------------------------------------------------------------------------- figure 2: data split
def fig2():
    b = t(14, 36, '5 模型评测目录：MER2024 1,169 + MELD 2,610 = 3,779 条', size=12, bold=True)
    # left: old 400 -> test
    b += module(14, 52, 380, 80, CODE[0], CODE[1], '旧 400 条', None, '项目原来的 320 训练 + 80 验证')
    b += lines(26, 114, ['整体只用作测试来源，不参与训练、验证、调参'], size=10, color='#555')
    b += module(14, 150, 380, 150, NEW[0], NEW[1], '其中 v4 判定不一致的 117 条', None, '与 v5-E 无技能同一批')
    b += lines(26, 204, ['Gemini 62 条 + GPT 55 条', '共 102 个不同样本：82 个来自原 320 训练、', '　　20 个来自原 80 验证', '候选集沿用 v4 的 candidate_labels'], size=10.2, step=17)
    b += arrow([(204, 132), (204, 150)])
    b += out_box(14, 334, 380, 56, ('测试（只在冻结技能后跑一次）', '训练、门控、调参都不碰它'))
    b += arrow([(204, 300), (204, 334)])
    # right: pool chain
    xs = [430, 706, 982]
    w = 254
    b += module(xs[0], 52, w, 170, CODE[0], CODE[1], '① 池', None, '去掉旧 400 条')
    b += lines(xs[0] + 12, 118, ['3,779 − 旧 400 = 3,379', '过媒体质量 → 3,377 条', 'MER2024 969 + MELD 2,408', '', '（v6 已经在用，不新增调用）'], size=10.2, step=17)
    b += module(xs[1], 52, w, 170, NEW[0], NEW[1], '② 冻结图谱 + 三专家第 0 轮', None, 'v6 pool.py，每个模型一套')
    b += lines(xs[1] + 12, 118, ['MER2024：969 条基本处理完', 'MELD：只处理了 1,200 / 2,408 条', '两家的不一致数都超过配额 200，', '19:20 已自动停止——样本数是定数'], size=10.2, step=17)
    b += module(xs[2], 52, w, 170, CODE[0], CODE[1], '③ 不一致池', None, '三人答案集合没有唯一共同标签')
    b += lines(xs[2] + 12, 118, ['Gemini　MER2024 97　MELD 204', 'GPT　　MER2024 161　MELD 381', '', '候选集 C = 三人答案的并集'], size=10.2, step=17)
    b += arrow([(xs[0] + w, 137), (xs[1], 137)]) + arrow([(xs[1] + w, 137), (xs[2], 137)])
    # row 2
    y2 = 268
    b += module(xs[0], y2, w, 170, CODE[0], CODE[1], '④ MELD 对话去重', None, '防止训练 / 验证与测试同一段对话')
    b += lines(xs[0] + 12, y2 + 66, ['去掉与旧 400 条同一段对话的样本：', 'Gemini 204 → 87（去掉 117）', 'GPT 381 → 153（去掉 228）', '', 'MER2024 没有对话信息，', '做不了这项检查（已知限制）'], size=10.0, step=16)
    b += module(xs[1], y2, w, 170, CODE[0], CODE[1], '⑤ 按组切分 75 / 25', None, '程序，种子 42')
    b += lines(xs[1] + 12, y2 + 66, ['MELD：同一段对话整体进同一边', 'MER2024：按样本切', '两个数据集各自切，所以', '数据集比例在训练 / 验证里一致', '训练与验证的对话重叠 = 0', '（已核对）'], size=10.0, step=16)
    b += module(xs[2], y2, w, 170, TEAL[1], TEAL[0], '⑥ 每个模型的训练 / 验证', None, '互不重叠')
    b += doc(xs[2] + 12, y2 + 52, 230, 50, ['训练 137（MER 72 + MELD 65）', '验证 47（MER 25 + MELD 22）'], title='Gemini', fill='#fff', stroke='#4C78A8', size=10)
    b += doc(xs[2] + 12, y2 + 110, 230, 50, ['训练 233（MER 120 + MELD 113）', '验证 81（MER 41 + MELD 40）'], title='GPT', fill='#fff', stroke='#59A14F', size=10)
    b += arrow([(xs[2] + w / 2, 222), (xs[2] + w / 2, 244), (xs[0] + w / 2, 244), (xs[0] + w / 2, y2)])
    b += arrow([(xs[0] + w, y2 + 85), (xs[1], y2 + 85)]) + arrow([(xs[1] + w, y2 + 85), (xs[2], y2 + 85)])
    # purposes
    b += group(14, 460, 1222, 118, '三个集合各自的用途（每个模型各自一套）', color=TEAL[0], fill=TEAL[1] + '33')
    b += doc(28, 496, 388, 70, ['轨迹卡（含标准标签）给优化器看，用来写补丁；', '训练只过 1 个 epoch，', '每条样本只跑一遍'], title='训练', fill='#fff', stroke=TEAL[0], size=10, fold=8)
    b += doc(432, 496, 388, 70, ['只算分数：门控接受 / 拒绝补丁、挑验证分最高的版本；', '它们的轨迹和标签都不给优化器看，', '所以不会被写进技能文档'], title='验证（门控）', fill='#fff', stroke=TEAL[0], size=10, fold=8)
    b += doc(836, 496, 386, 70, ['冻结 best_skill 后一次性跑 117 条；', '对照：再跑一次空技能 v5-E；', '这 117 条之前被反复分析过，只是开发集'], title='测试', fill='#fff', stroke=GREEN, size=10, fold=8)
    b += legend(598)
    return svg(b, 622)


# ------------------------------------------------------------------------------------------- figure 3: the original SkillOpt loop
def fig3_original():
    b = group(14, 44, 1222, 30, '原版 SkillOpt 的训练循环（据 microsoft/SkillOpt 源码：engine/trainer.py、gradient/、optimizer/clip.py、evaluation/gate.py）', color='#666', fill='#f3f3f3')
    w, gap, x0, y0, h = 188, 18, 16, 118, 262
    specs = [
        ('① Rollout', 'LLM（目标模型）', NEW, ['每个 epoch 重新打乱训练集，', '每步取一批（默认 40 条）', '', '目标模型带着当前技能 S', '做任务，得到轨迹和得分', '（硬分 / 软分）']),
        ('② Reflect', 'LLM（优化器）', CTRL[::-1], ['先按成败拆成两堆：', '失败轨迹 / 成功轨迹', '各自随机分成 8 条一组', '每组一次优化器调用（并行）', '失败组：analyst_error', '成功组：analyst_success', '每组输出 ≤ L 条补丁']),
        ('③ Aggregate', 'LLM（优化器）', CTRL[::-1], ['失败补丁：每 8 个一合并，', '逐层合并直到一个', '成功补丁同样合并', '', '最后失败优先合并成', '一个补丁（merge_final）']),
        ('④ Select', 'LLM + 程序', CTRL[::-1], ['学习率调度给出本步', '编辑预算 L（默认 4→2，', '余弦衰减）', '', '补丁条数 > L：优化器排序，', '只留前 L 条', '≤ L：原样通过']),
        ('⑤ Update', '程序', CODE, ['把补丁（append / insert_after', '/ replace / delete）', '应用到技能文档', '', '受保护区块不允许改', '→ 得到候选 S′']),
        ('⑥ Evaluate / Gate', 'LLM（目标模型）', NEW, ['S′ 在验证集（selection）', '上跑一遍，算分数', '', '分数 > 当前分数 → 接受', '（当前分数是上次接受时', '记下的，不重新测）', '否则拒绝，并把被拒的补丁', '写进步骤缓冲']),
    ]
    for i, (ttl, tag, (fl, st), body) in enumerate(specs):
        x = x0 + i * (w + gap)
        b += module(x, y0, w, h, fl, st, ttl, None)
        b += (llm_tag(0, y0 - 24, tag, right=x + w) if 'LLM' in tag else code_tag(0, y0 - 24, right=x + w))
        b += lines(x + 10, y0 + 50, body, size=10.2, step=16.5)
        if i:
            b += arrow([(x - gap, y0 + h / 2), (x, y0 + h / 2)])
    b += doc(16, 408, 190, 46, ['技能文档 S', '起点：空文件或种子技能'], size=10, stroke='#666', fold=8)
    b += arrow([(110, 408), (110, 380)], '#666')
    b += arrow([(1140, 380), (1140, 398), (214, 398), (214, 431), (206, 431)], '#999', True)
    b += t(680, 394, '接受 → S ← S′；拒绝 → S 不变；然后下一步', size=10.2, color='#555', anchor='middle')
    b += doc(232, 410, 330, 108, [], fold=8, stroke='#999')
    b += t(240, 428, '步骤缓冲（只在同一个 epoch 内累积）', size=10.2, bold=True)
    b += lines(240, 446, ['前面各步的失败模式 + 被拒绝的补丁', '和分数变化，作为上下文喂给', '②③④ 的优化器，避免重复无效修改'], size=9.8, step=15.5)
    b += arrow([(397, 410), (397, 384), (300, 384), (300, 380)], '#999', True)
    b += group(580, 410, 656, 108, '每个 epoch 结束（从第 2 个 epoch 起）', color='#666', fill='#fff')
    b += lines(592, 450, ['Slow Update：抽 20 条训练样本，分别用上一个 epoch 和这一个 epoch 的 S 各跑一遍，',
                          '分成 变好 / 退步 / 一直错 / 一直对，优化器写一段全局指导放进受保护区块（默认不过门控）',
                          'Meta Skill：优化器写给自己的策略笔记，下一个 epoch 的 ②③④ 都会读',
                          '训练结束：报告验证分最高的那份 S 在测试集上的得分（默认三份数据按 train : val : test = 2 : 1 : 7）'], size=9.6, step=15.5)
    b += legend(546)
    return svg(b, 570)


# ------------------------------------------------------------------------------------------- figure 4: our loop (changes marked)
def fig3_ours():
    b = group(14, 44, 1222, 30, '我们的训练循环（一步 = 40 条训练样本；整个训练只有 1 个 epoch）。红色标签 = 与原版不同的地方；其余同原版', color=TEAL[0], fill=TEAL[1] + '33')
    w, gap, x0, y0, h = 188, 18, 16, 118, 262
    specs = [
        ('① Rollout', 'LLM（看媒体）', NEW, '改', ['取 40 条训练样本', '带当前技能 S，在扩充后的', '候选集 C′ 上跑完整 v5-E：', '首答 → 回看 → 反思', '', '每条 1–3 次调用', '得分：最终答案是否等于', '标准标签']),
        ('② 分类 + Reflect', '程序 + LLM（看媒体）', CTRL[::-1], '改', ['程序先给轨迹贴类型：', 'F1 漏报 / F2 回看无效 /', 'F3 改错 / F4 改了仍错 /', 'S1 改对 / S2 稳定对', '堆内按类型排序，切 8 条一组', '每组由一位反思模型读轨迹卡', '＋样本信息（候选与来源、字幕、', '标准标签）＋视频帧（8 帧；', 'Gemini 另有音轨），写补丁，', '每条编辑标明改哪个模块']),
        ('③ Aggregate', 'LLM（文本，只处理补丁）', CTRL[::-1], '改', ['同原版的逐层合并：', '失败补丁、成功补丁各自合并，', '最后失败优先合并', '', '合并后的编辑按所属模块', '分开，进入下一步', '', '输入里照样带步骤缓冲']),
        ('④ Select', 'LLM + 程序', CTRL[::-1], '改', ['编辑预算 L 取 4→2 余弦衰减', '（按总步数：Gemini 4 步，', 'GPT 6 步）', '', '每个模块各自：编辑多于 L 条', '就让优化器排序，只留前 L 条']),
        ('⑤ 检查 + Update', '程序', CODE, '新增', ['检查补丁，不通过就丢：', '· 只改自己模块', '· 不含样本 id / 字幕原句', '· 不改输出格式', '· 全文 ≤ 1,500 字', '通过的补丁应用到 S', '→ 候选 S′']),
        ('⑥ Gate', 'LLM（看媒体）', NEW, '改', ['按模块依次门控：', '首答模块：答对数 ≥ 当前 + 2', '回看、反思模块：答对数', '≥ 当前（不降低）', '才接受', '没有补丁的模块不验证', '拒绝 → 记入步骤缓冲']),
    ]
    for i, (ttl, tag, (fl, st), flag, body) in enumerate(specs):
        x = x0 + i * (w + gap)
        b += module(x, y0, w, h, fl, st, ttl, None)
        b += (llm_tag(0, y0 - 24, tag, right=x + w) if 'LLM' in tag else code_tag(0, y0 - 24, right=x + w))
        if flag:
            b += badge(x + 14, y0 - 6, flag)
        b += lines(x + 10, y0 + 50, body, size=10.0, step=16)
        if i:
            b += arrow([(x - gap, y0 + h / 2), (x, y0 + h / 2)])
    b += doc(16, 408, 190, 46, ['技能文档 S', '起点：三个模块的空标题'], size=10, stroke=TEAL[0], fold=8)
    b += arrow([(110, 408), (110, 380)], TEAL[0])
    b += arrow([(1140, 380), (1140, 398), (214, 398), (214, 431), (206, 431)], '#999', True)
    b += t(680, 394, '接受 → 成为新的 S；拒绝 → S 不变；换下一批 40 条', size=10.2, color='#555', anchor='middle')
    b += group(232, 410, 500, 112, '没有 epoch 结束的机制', color=TEAL[0], fill='#fff')
    b += badge(660, 428, '改')
    b += lines(244, 450, ['epoch = 1：Slow Update、Meta Skill（原版从第 2 个 epoch 才触发）不会发生', '也没有先验表的更新；A 里的混淆信息来自固定的 80 条混淆矩阵（图 5）', '训练结束：取验证分最高的那份 S 作为 best_skill'], size=9.6, step=17)
    b += group(752, 410, 484, 112, '设置', color='#999', fill='#fff')
    b += lines(764, 450, ['1 个 epoch（原版 4）；每步 40 条、每组 8 条（同原版）', 'Gemini：训练 137 → 4 步，L = 4, 3, 2, 2', 'GPT：训练 233 → 6 步，L = 4, 4, 3, 2, 2, 2', '优化器：Gemini 用 Gemini；GPT 用 GPT 6.1 SOL（实现时核对名称）'], size=9.6, step=17)
    b += legend(546)
    return svg(b, 570)


# ------------------------------------------------------------------------------------------- figure 5: statistics for section A
def fig_stats():
    b = group(14, 44, 1222, 30, '候选集扩充：由 80 条旧样本的混淆矩阵 top1 决定，agent 不能自己加标签', color=TEAL[0], fill=TEAL[1] + '33')
    w, gap, x0, y0, h = 226, 24, 16, 118, 236
    specs = [
        ('① 混淆矩阵', CODE, '程序，一次性', ['来源：80 条旧验证样本上，', '该提供方的 5 组结果', '（Direct / PPCT / v1 / v2 / v3）', '', '按数据集分开、区分方向：', '数“答案是 c 时，真实标签是 g”', '的次数 / 样本数']),
        ('② 取 top1', CODE, '程序', ['对候选集 C 里的每个标签 c：', 'g(c) = 真实标签里次数最高的 1 个', '（“被判成 c 时，真实标签最常是谁”）', '', '排序：先看不同样本数，', '再看事件数', '没有记录的标签：不扩充']),
        ('③ 合并并标来源', CODE, '程序', ['C′ = C ∪ { g(c) }', '', 'g(c) 已在 C 里 → 算“原候选”', 'g(c) 不在 C 里 → 算“扩充”', '', '（原本就有的，扩充里再出现，', '仍算原候选）']),
        ('④ 写进提示词', NEW, '三个阶段都带', ['候选标签：x、y（原候选）', '扩充标签：z', '（因为答案是 x 时，真实标签', '　常是 z）', '', 'agent 只能在 C′ 里选，', '不能自己再加标签']),
        ('⑤ 区分线索', CTRL[::-1], 'LLM（文本）', ['首答模块的 A 部分由优化器写：', '原候选与扩充标签之间', '凭什么线索区分', '', '每一步都可以改，', '和 B、C、D 一样', '过检查与门控']),
    ]
    for i, (ttl, (fl, st), tag, body) in enumerate(specs):
        x = x0 + i * (w + gap)
        b += module(x, y0, w, h, fl, st, ttl, None)
        b += (llm_tag(0, y0 - 24, tag, right=x + w) if ('LLM' in tag or '阶段' in tag) else code_tag(0, y0 - 24, right=x + w))
        b += lines(x + 10, y0 + 50, body, size=10.2, step=16.5)
        if i:
            b += arrow([(x - gap, y0 + h / 2), (x, y0 + h / 2)])
    b += doc(16, 380, 560, 112, [], fold=8, stroke='#999')
    b += t(24, 398, '一个例子（示意，不是真实结果）', size=10.5, bold=True)
    b += lines(24, 416, ['候选集 C = { neutral, sadness }', 'g(neutral) = anger　→ 不在 C 里，算“扩充”', 'g(sadness) = neutral → 已在 C 里，算“原候选”', 'C′ = { neutral, sadness | 扩充：anger }'], size=10, step=17)
    b += doc(600, 380, 636, 112, [], fold=8, stroke=RED)
    b += t(608, 398, '已知限制（用户已决定接受 1，其余需要留意）', size=10.5, bold=True, color=RED)
    b += lines(608, 416, ['· 这 80 条里有 20 个样本在 117 条测试里：矩阵含它们的标准标签，结果必须标注，不能说无泄漏', '· 矩阵很薄：按提供方 × 数据集拆开后，多数 top1 只有 1–2 个样本支持，还有标签没有任何记录（见下表）', '· 矩阵反映的是 Direct / PPCT / v1–v3 的错误，不是 v5-E 的；扩充不一定提高覆盖'], size=9.6, step=16)
    b += legend(516)
    return svg(b, 540)


# ------------------------------------------------------------------------------------------- figure 6: one trajectory -> one edit
def fig4():
    b = group(14, 44, 1222, 34, '一条失败轨迹如何变成对技能文档某个模块的一处修改（示例文字均为示意，不是真实结果）', color=TEAL[0], fill=TEAL[1] + '33')
    cols = [(14, 396), (448, 392), (878, 358)]
    y0, h = 100, 300
    ttl = ['反思模型看到的“轨迹卡”＋视频帧', '优化器输出的补丁', '技能文档 S → 候选 S′']
    for (x, w), tt in zip(cols, ttl):
        b += doc(x, y0, w, h, [], fold=10, stroke='#999')
        b += t(x + 10, y0 + 22, tt, size=11.5, bold=True)
    x = cols[0][0] + 10
    b += lines(x, y0 + 46, ['轨迹 #3　数据集 MELD　候选 {neutral, sadness, anger}', '', '首答：neutral', '理由：语气平淡，字幕是陈述句', '证据 E1　字幕：（原话）', '证据 E2　visual frame_03：面部放松', '不确定点：无　→ 没有回看', '最终答案：neutral', '', '标准标签：sadness', '类型：F1 漏报（首答错、没标不确定）'], size=10.0, step=17.5)
    b += t(x, y0 + 262, '轨迹不带样本 id，避免优化器记住具体样本', size=9.8, color=RED)
    x = cols[1][0] + 10
    b += lines(x, y0 + 46, ['failure_summary: F1 漏报 5 / 8 条，', '　多是“平淡语气下的负面情绪被判 neutral”', '', 'patch.edits:', '{ "op": "insert_after",', '  "target": "## 首答模块 / B 何时写不确定点",', '  "content": "- 候选里同时有 neutral 和', '    负面情绪时，只靠字幕字面判断就要写', '    不确定点，回看声音停顿与眉眼" }'], size=10.0, step=17.5)
    b += t(x, y0 + 236, '每组最多 L 条；多组的补丁再合并、排序、只留前 L 条', size=9.8, color='#555')
    x = cols[2][0] + 10
    b += lines(x, y0 + 46, ['  ## 首答模块 / A 区分线索', '  …', '  ## 首答模块 / B 什么时候写不确定点', '+ - 候选里同时有 neutral 和负面情绪时，', '+   只靠字幕字面判断就要写不确定点，', '+   回看声音停顿与眉眼', '  ## 回看模块 / C 回看时怎么看', '  ## 反思模块 / D 什么时候改答案'], size=10.0, step=17.5)
    b += lines(x, y0 + 214, ['检查通过 → 应用 → 得到 S′', 'Gate：S′ 在验证集上不比 S 多对 2 条', '→ 整处修改丢弃，S 不变'], size=10.0, step=17, color='#444')
    b += arrow([(cols[0][0] + cols[0][1], y0 + 140), (cols[1][0], y0 + 140)])
    b += arrow([(cols[1][0] + cols[1][1], y0 + 140), (cols[2][0], y0 + 140)])
    b += group(14, 424, 1222, 70, '技能文档里不允许出现的内容（程序检查）', color=RED, fill='#F9DEDB55')
    b += lines(28, 468, ['样本 id、字幕原句、“这个样本的标准标签是…”；改输出字段的要求；超出允许章节的修改。通过检查的技能文档，在冻结前我还会人工通读一遍。'], size=10.2)
    b += legend(514)
    return svg(b, 538)


# ------------------------------------------------------------------------------------------- figure 7: timeline
def fig5():
    b = ''
    xs = [14, 326, 638, 950]
    w = 286
    specs = [
        ('阶段 0 准备', CODE, '程序', ['按图 2 切分训练 / 验证', '读 80 条混淆矩阵，建立', '“标签 → top1 真实标签”查表', '', '写入空技能 S0（三个模块的标题）', 'S0 在验证集上的得分 = 基线分', '（= v5-E + 候选扩充，不含技能）']),
        ('阶段 1 训练', NEW, '1 个 epoch', ['图 4 的循环，每个模型各训一份', '', '每一步：Rollout → 分模块 Reflect →', '合并 → 检查 → 分模块 Gate', '', 'Gemini 4 步，GPT 6 步', '产物：验证分最高的技能 best_skill.md']),
        ('阶段 2 冻结 + 审查', CODE, '人工 + 程序', ['冻结 best_skill.md，写入 SHA256', '', '我通读一遍：有没有样本泄漏、', '标签先验、过窄的规则', '', '你审核通过才进入阶段 3']),
        ('阶段 3 测试', NEW, '117 条，只跑一次', ['Gemini 62 + GPT 55，带冻结技能', '', '对照：再跑一次空技能 v5-E', '（用来估单次运行的噪声）', '', '按判据报告，不据此再改技能']),
    ]
    for i, (ttl, (fl, st), tag, body) in enumerate(specs):
        x = xs[i]
        b += module(x, 52, w, 224, fl, st, ttl, None, tag)
        b += lines(x + 12, 118, body, size=10.2, step=16.5)
        if i:
            b += arrow([(x - 26, 164), (x, 164)])
    b += group(14, 300, 1222, 218, '怎么判断有没有用（沿用之前约定的判据）与已有的对照数字（117 条不一致样本答对数）', color=GREEN, fill=OUT[0] + '44')
    rows = [('方法', 'Gemini（62）', 'GPT（55）', '合计'),
            ('随机基线', '25.6', '22.8', '48.4'),
            ('v4 辩论', '26', '19', '45'),
            ('Direct 五次均值', '36.6', '23.8', '60.4'),
            ('v5-E 无技能、无扩充（已有，单次运行）', '39', '24', '63'),
            ('v5-E + 扩充 + 技能（本设计）', '待测', '待测', '待测'),
            ('候选集上限（未扩充）', '58', '49', '107')]
    for r, row in enumerate(rows):
        yy = 346 + r * 22
        for c, (cx, cell) in enumerate(zip((34, 330, 450, 560), row)):
            b += t(cx, yy, cell, size=10.5, bold=(r == 0 or r == 5), color=(TEAL[0] if r == 5 else '#222'))
    b += lines(660, 352, ['成功判据：合计比 Direct 均值至少多 4 条（≥ 64.4），', '且两个模型各自不低于自己的 Direct 均值。', '', '另外分开报告：', '· 首答准确率；写不确定点的比例与命中率', '· 回看改答案：错→对 / 对→错 的条数', '· 与“再跑一次空技能 v5-E”的差（噪声）', '· 注意：基线没有扩充，增益无法拆分（暂不处理）'], size=10.2, step=17)
    b += legend(540)
    return svg(b, 564)


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
P.append('<h1>SkillOpt 针对 v5-E 的设计（v6-SkillOpt-V5E，第三版）</h1>')
P.append('<p class="muted">日期 2026-11-05。<b>只有设计，没有实现、没有运行、没有结果。</b>图中橙色 = 大模型调用，蓝灰 = 程序，青绿 = 技能文档与 SkillOpt。'
         '第三版相对第二版：① A 改为“用 80 条混淆矩阵的 top1 扩充候选集（程序）+ 优化器写区分线索”，agent 不能自己加标签；② 技能分首答 / 回看 / 反思三个模块，分模块更新；'
         '③ epoch 设为 1，取消先验表更新；④ GPT 的优化器用 GPT 6.1 SOL。</p>')

P.append('<section class="panel"><h2>零、一句话</h2>'
         '<p>v5-E 是一个全模态 agent：先作答，自己写出拿不准的具体问题，再按它指定的时间窗回看，然后反思给最终答案。'
         'SkillOpt 要做的是：<b>训练一份 Markdown 技能文档</b>（三个模块），把“怎么区分易混标签、什么时候该写不确定点、回看怎么看、什么时候该改答案”这几类经验写进去，'
         '训练完冻结，拼进 v5-E 的三个提示词里。模型权重不动，推理时不增加调用。另外，候选集由程序按混淆矩阵扩充，agent 只能在扩充后的候选集里选。</p>'
         '<table><tr><th></th><th>此前设计页里的 SkillOpt-E</th><th>本页 SkillOpt-V5E</th></tr>'
         '<tr><td>被训练的对象</td><td>三位专家（图谱 / 音频字幕 / 图像）各一份技能</td><td>v5-E 单个 agent 一份技能（三个模块；每个模型各一份）</td></tr>'
         '<tr><td>候选集</td><td>三专家第 0 轮并集</td><td>原候选 + 混淆矩阵 top1 扩充，并标明哪些是原候选、哪些是扩充</td></tr>'
         '<tr><td>适用的样本</td><td>全部样本</td><td>只有三专家第 0 轮不一致的样本（v5-E 本来就只跑这些）</td></tr>'
         '<tr><td>训练 / 验证样本</td><td>新选的 400 条 + 60 条验证</td><td>v6 池里的不一致样本，去掉与旧 400 条同一段对话的 MELD 样本，75 / 25 按组切分（图 2）</td></tr>'
         '<tr><td>测试</td><td>旧 400 条全部</td><td>旧 400 条里的 117 条不一致样本（与 v5-E 无技能同一批）</td></tr></table></section>')

P.append('<section class="panel"><h2>一、技能文档放在哪里</h2><div class="fig">' + fig1() + '</div>'
         '<p class="cap"><b>图 1　v5-E 的流程，以及技能文档拼进哪里。</b>橙色三步是现有的 v5-E（<code>versions/v5/orchestra.py</code>）：首次作答 → 有不确定点才回看 → 反思。'
         '底部青绿色是新增的技能文档：一个提示词、三个模块（首答 = A 区分线索 + B 何时写不确定点；回看 = C；反思 = D），每个阶段只带自己的模块，输出字段与格式校验不变；'
         '起点只有空标题。候选集由程序扩充成 C′（图 5），三个阶段都只能在 C′ 里选。'
         '右侧是 v5-E 现有的表现：只有 13 条写了不确定点，答错的绝大多数没被标记——这是技能最可能起作用的地方。</p></section>')


P.append('<section class="panel"><h2>二、训练集、验证集、测试集怎么划分（含验证集的来源）</h2><div class="fig">' + fig2() + '</div>'
         '<p class="cap"><b>图 2　三个集合的来源与切分，每个模型各自一套。</b>数字是 2026-11-05 只读核对服务器得到的：不一致数来自 <code>outputs/v6_rmad/pool/*/*/*/r0_summary.json</code>，'
         'MELD 的对话编号来自 5 模型评测目录的清单。v6 的筛选池已在 19:20 结束，所以这些数是定数。</p>'
         '<h3>具体规则</h3><table><tr><th>集合</th><th>来源</th><th>规模（Gemini / GPT）</th><th>怎么用</th></tr>'
         '<tr><td style="white-space:nowrap"><b>训练</b></td><td>v6 池里三专家第 0 轮不一致的样本，去掉与旧 400 条同一段对话的 MELD 样本后，按 75 / 25 切出的 75%</td><td class="n">137 / 233</td><td>轨迹卡（含标准标签）给优化器看；每个 epoch 每条样本只跑一遍</td></tr>'
         '<tr><td style="white-space:nowrap"><b>验证</b></td><td>同一个池，同一次切分的 25%（MELD 按整段对话切，对话重叠为 0）</td><td class="n">47 / 81</td><td>只算分数，用于门控（接受 / 拒绝补丁）和挑验证分最高的版本；轨迹与标签不给优化器看</td></tr>'
         '<tr><td style="white-space:nowrap"><b>测试</b></td><td>旧 400 条里 v4 判定不一致的样本（Gemini 62 + GPT 55，共 102 个不同样本，其中 82 个来自原 320 训练、20 个来自原 80 验证）</td><td class="n">62 / 55</td><td>冻结技能后只跑一次；训练、门控、调参都不碰；另跑一次空技能 v5-E 作噪声对照</td></tr></table>'
         '<h3>验证集从哪里来</h3>'
         '<p>从训练用的同一个不一致池里切出 25%，不另找数据。考虑过并放弃的两个来源：</p>'
         '<ul><li><b>新选的 60 条验证</b>：它们按“至少 3 个模型答对”筛，偏容易，三专家不一致的只有 Gemini 2 / 42、GPT 7 / 42，没法当门控。</li>'
         '<li><b>项目原来的 80 条验证</b>：AGENTS.md 规定验证集不得参与方法调参；而且其中 20 条已经在 117 条测试里。</li></ul>'
         '<p class="small muted">所以三个集合互不重叠：训练和验证来自旧 400 条之外的池，测试是旧 400 条。新选的 460 条（200 + 30 × 2）这一版不使用。</p>'
         '<div class="warn"><b>新发现，需要你判断：MELD 对话泄漏。</b>池里不一致的 MELD 样本中，有一大半和旧 400 条（测试来源）来自同一段对话——Gemini 117 / 204，GPT 228 / 381（旧 400 条的 MELD 样本覆盖了 138 段对话）。'
         '同一段对话里说话人、场景、相邻话语的情绪都相关，如果训练 / 验证和测试共享对话，结果会偏乐观。所以本设计在 MELD 上去掉这些样本，代价是 Gemini 的 MELD 训练 + 验证只剩 87 条、GPT 的只剩 153 条。'
         'MER2024 没有对话 / 影片编号，做不了同类检查，这是已知限制。<br>'
         '<b>这也影响正在跑的 R²-MAD（v6）</b>：它的训练集是同一个池的前 200 条不一致样本，只按样本编号去掉旧 400 条，没有按对话去重；它又是检索式的（取相似案例的标准标签），受同对话邻居的影响比技能文档更直接。我没有改动正在运行的任何东西，是否处理由你决定。</div></section>')

P.append('<section class="panel"><h2>三、原版 SkillOpt 的训练循环</h2><div class="fig">' + fig3_original() + '</div>'
         '<p class="cap"><b>图 3　原版 SkillOpt（microsoft/SkillOpt，arXiv 2605.23904）的一步训练。</b>按源码画：<code>engine/trainer.py</code> 的六个阶段、<code>gradient/reflect.py</code> 的 minibatch 反思、'
         '<code>gradient/aggregate.py</code> 的失败优先逐层合并、<code>optimizer/clip.py</code> 的排序裁剪、<code>evaluation/gate.py</code> 的门控。'
         '默认值取自 <code>configs/_base_/default.yaml</code>。我没有拿到论文正文（arXiv 网页在本环境打不开），论文里的图表述可能与源码的叫法不同，这里以源码为准。</p></section>')

P.append('<section class="panel"><h2>四、我们的训练循环，以及与原版的差异</h2><div class="fig">' + fig3_ours() + '</div>'
         '<p class="cap"><b>图 4　我们的一步训练。</b>红色标签标出与图 3 不同之处；没有标签的模块照搬原版。</p>'
         '<table><tr><th>环节</th><th>原版</th><th>我们</th><th>为什么改</th></tr>'
         '<tr><td>任务与输入</td><td>文本 / 代码类任务，目标模型读文字</td><td>v5-E 三阶段轨迹，目标模型看 8 帧 + 音轨 + 字幕；反思模型也看视频帧（Gemini 另有音轨）+ 轨迹卡；合并、排序只处理补丁文字</td><td>用户要求：反思要结合视频判断，才能核对 agent 写的证据对不对</td></tr>'
         '<tr><td><b>候选集</b></td><td>无</td><td>原候选 + 混淆矩阵 top1 扩充，提示里标明来源；agent 只能在其中选</td><td>用户的设计：让模型看到“被判成 c 时真实标签常是谁”</td></tr>'
         '<tr><td>技能文档结构</td><td>一份自由格式文档，两个受保护区块（slow update、appendix）</td><td>三个模块（首答 = A + B；回看 = C；反思 = D），每个阶段只带自己的模块</td><td>三个阶段做的事不同，分模块才能分别更新、分别归因</td></tr>'
         '<tr><td>Reflect</td><td>先分失败 / 成功，各自随机分成 8 条一组，一组一次调用</td><td>先按“哪里出错”分类（F1–F4、S1–S2），堆内按类型排序后切 8 条一组；每组由一位反思模型读轨迹卡和样本信息，写补丁，每条编辑标明改哪个模块</td><td>让同一组的失败有共同原因；反思模型只有一位，同原版</td></tr>'
         '<tr><td>合并与裁剪</td><td>一个技能文档一条线</td><td>合并同原版；裁剪时按所属模块各自留 L 条</td><td>分模块更新</td></tr>'
         '<tr><td>补丁检查</td><td>没有（只有受保护区块规则）</td><td>程序检查：只改自己模块、不含样本 id / 字幕原句、不改输出格式、长度上限</td><td>防止技能里混进具体样本的信息</td></tr>'
         '<tr><td>门控</td><td>验证分 &gt; 当前分（当前分是上次接受时记下的，不重测）</td><td>按模块依次门控：首答模块 ≥ 当前 + 2；回看、反思模块 ≥ 当前（不降低）；没有补丁的模块不验证</td><td>验证集很小、单次运行噪声大；回看、反思只影响约 11% 的样本，+2 过不了；分模块归因</td></tr>'
         '<tr><td>epoch 数</td><td>4</td><td>1</td><td>用户决定；样本少</td></tr>'
         '<tr><td>Slow Update、Meta Skill</td><td>从第 2 个 epoch 起</td><td>epoch = 1，不会触发</td><td>—</td></tr>'
         '<tr><td>验证集</td><td>默认 train : val : test = 2 : 1 : 7，数据量大</td><td>从不一致池切出 25%（Gemini 47、GPT 81）；测试另有 117 条</td><td>可用的不一致样本很少（图 2）</td></tr>'
         '<tr><td>优化器模型</td><td>默认较强的单一模型</td><td>Gemini 用 Gemini；GPT 用 GPT 6.1 SOL</td><td>用户指定</td></tr>'
         '<tr><td>步骤缓冲、学习率调度、失败优先合并</td><td>有</td><td>同原版</td><td>—</td></tr></table></section>')

P.append('<section class="panel"><h2>五、候选集扩充（A）：用 80 条混淆矩阵的 top1</h2><div class="fig">' + fig_stats() + '</div>'
         '<p class="cap"><b>图 5　候选集扩充与 A 的区分线索。</b>程序按混淆矩阵给每条样本的候选集 C 加上扩充标签，得到 C′；提示词里明确哪些是原候选、哪些是扩充；agent 只能在 C′ 里选，不能自己加标签。'
         'A 里“凭什么线索区分”由优化器写，与 B、C、D 一样每一步都可以改。</p>'
         '<h3>规则</h3><ul>'
         '<li><b>矩阵口径</b>：只用 80 条旧验证样本；按提供方（Gemini、GPT）分开、按数据集分开、区分方向。方向的含义是：当前候选标签是 c，数“答案是 c 时真实标签是 g”的次数。</li>'
         '<li><b>取法</b>：对候选集 C 里的每个标签 c，取 top1 的 g(c)（先比不同样本数，再比事件数）；该 c 没有记录就不扩充。</li>'
         '<li><b>来源标记</b>：g(c) 已在 C 里 → 算原候选；不在 → 算扩充。原本就有的，即使扩充里也有，仍算原候选。</li>'
         '<li><b>作答</b>：agent 只能在 C′ 里选；首答、回看、反思三个阶段用同一个 C′。</li></ul>'
         '<h3>这张 top1 查表现在长什么样（按你的口径，用本机已保存的 80 条结果算的）</h3>'
         '<p>每项写作“c → g（支持的不同样本数 / 错判事件数）”。事件数是同一样本在 5 组结果里被重复计数的总和。</p>'
         '<table><tr><th></th><th>MER2024</th><th>MELD</th></tr>'
         '<tr><td><b>Gemini</b></td><td>sad→neutral（2/2）；worried→surprise（4/12）；surprise→angry（2/4）；neutral→angry（2/4）；<b>无记录</b>：happy、angry</td>'
         '<td>joy→surprise（1/5）；anger→disgust（2/9）；fear→sadness（1/1）；surprise→anger（2/3）；neutral→disgust（4/12）；<b>无记录</b>：sadness、disgust</td></tr>'
         '<tr><td><b>GPT</b></td><td>angry→sad（1/4）；sad→neutral（2/7）；worried→angry（4/15）；surprise→neutral（1/2）；neutral→happy（1/4）；<b>无记录</b>：happy</td>'
         '<td>joy→surprise（1/5）；anger→disgust（4/14）；sadness→joy（1/2）；fear→disgust（1/1）；surprise→fear（2/3）；neutral→anger（2/4）；<b>无记录</b>：disgust</td></tr></table>'
         '<div class="warn"><b>要留意的事实：</b>矩阵拆成“提供方 × 数据集 × 方向”之后非常薄。四张表里，只有各一个标签有 ≥ 3 个不同样本支持（Gemini：MER 的 worried、MELD 的 neutral；GPT：MER 的 worried、MELD 的 anger），其余 top1 只有 1–2 个样本，还有标签完全没有记录。'
         '也就是说大多数扩充标签依据很弱，可能只是噪声。你已决定不设最小支持数，我会照做，但结果里会逐项报告每个扩充的支持数。</div>'
         '<p class="small muted">已知限制（你已决定先不处理）：① 这 80 条里有 20 个样本在 117 条测试里（Gemini 15、GPT 8），矩阵含它们的标准标签，结果必须标注，不能声称无泄漏；② 矩阵反映的是 Direct / PPCT / v1–v3 的错误，不是 v5-E 的；'
         '③ 旧分析里，专家全错的样本中真实标签落进扩充后候选集的比例约 60%，随机期望约 63%（GPT，旧表、t = 5，不是本页的 top1 方向矩阵），所以扩充不一定提高覆盖；④ 基线没有扩充，增益无法拆成“扩充”和“技能”两部分，这一点你说先不管。</p></section>')


P.append('<section class="panel"><h2>六、一条轨迹怎么变成一处修改</h2><div class="fig">' + fig4() + '</div>'
         '<p class="cap"><b>图 6　数据流示意（B–D 节）。</b>反思模型除了看视频帧（Gemini 另有音轨），还看到 agent 写的答案、理由、证据、不确定点、回看结果、反思决定，以及标准标签，可以核对证据是否真的在视频里；'
         '它提出“增 / 删 / 改”补丁，经检查和门控后才改变技能文档。例子是我编的，用来说明格式。</p></section>')

P.append('<section class="panel"><h2>七、全流程与判据</h2><div class="fig">' + fig5() + '</div>'
         '<p class="cap"><b>图 7　四个阶段。</b>训练好的技能先冻结、人工审查，再在 117 条上只跑一次。'
         '对照数字来自 <code>metrics/findings_log.md</code>（F11、F12）；“v5-E + 技能”现在没有数，不要把待测当成结果。</p></section>')

PARAMS_HTML = '''
<h3>1. 训练循环：epoch、batch、步数</h3>
<table><tr><th>参数</th><th>原版默认</th><th>我们的值</th><th class="n">Gemini</th><th class="n">GPT</th><th>说明</th></tr>
<tr><td>训练集大小</td><td>数据决定</td><td>图 2</td><td class="n">137</td><td class="n">233</td><td>MER 72 + MELD 65；MER 120 + MELD 113</td></tr>
<tr><td>验证集大小（selection）</td><td>用整个验证划分</td><td>同</td><td class="n">47</td><td class="n">81</td><td>只算分数，用于门控</td></tr>
<tr><td><b>epoch 数</b></td><td>4</td><td><b>1</b></td><td class="n">1</td><td class="n">1</td><td>把训练集打乱后只完整过一遍</td></tr>
<tr><td><b>batch 大小</b></td><td>40</td><td>40</td><td class="n">40</td><td class="n">40</td><td>一步（一次技能更新）用的训练样本数</td></tr>
<tr><td>梯度累积</td><td>1</td><td>1</td><td class="n">1</td><td class="n">1</td><td>不累积</td></tr>
<tr><td><b>总步数</b>（= 每 epoch 步数）</td><td>⌈训练集 ÷ batch⌉</td><td>同</td><td class="n">4</td><td class="n">6</td><td>每步的批：Gemini 40、40、40、17；GPT 40×5、33</td></tr>
<tr><td>随机种子</td><td>42</td><td>42</td><td class="n">42</td><td class="n">42</td><td></td></tr></table>

<h3>2. Reflect / Aggregate：minibatch 与模块</h3>
<table><tr><th>参数</th><th>原版默认</th><th>我们的值</th><th>说明</th></tr>
<tr><td><b>minibatch 大小</b></td><td>8</td><td>8</td><td>失败堆、成功堆分别切；不足 4 条的尾组并入前一组（我们加的）</td></tr>
<tr><td>只分析失败 failure_only</td><td>false</td><td>false</td><td>成功堆也分析</td></tr>
<tr><td>合并批大小</td><td>8</td><td>8</td><td>每 8 个补丁合并一次，逐层合并；失败优先</td></tr>
<tr><td>反思模型</td><td>每组 1 位</td><td>每组 1 位（同原版）</td><td>读轨迹卡 + 样本信息（候选与来源、字幕、标准标签）+ 视频帧（每条样本的 8 帧，被标记回看的另有回看帧；Gemini 另有音轨），写补丁；每条编辑标明改哪个模块</td></tr>
<tr><td>分析并发</td><td>16</td><td>≤ 4</td><td>受 v6 请求限流约束，实现时再定</td></tr>
<tr><td>每步优化器调用</td><td>—</td><td>约 5 次看媒体的反思 + 5–6 次纯文本</td><td>反思每次带最多 8 条样本的帧（约 64 张图；Gemini 另有 8 段音轨）；合并 2–3 次、按模块的排序最多 3 次只处理补丁文字</td></tr></table>

<h3>3. Select：学习率 = 每个模块每步最多改几处</h3>
<table><tr><th>参数</th><th>原版默认</th><th>我们的值</th><th>说明</th></tr>
<tr><td>学习率（最大 / 最小）</td><td>4 / 2</td><td>4 / 2</td><td>每个分析员最多写 L 条；合并后超过 L 条，由优化器排序只留前 L 条</td></tr>
<tr><td>调度</td><td>cosine</td><td>cosine</td><td>按总步数从 4 衰减到 2</td></tr>
<tr><td>Gemini 每步的 L（4 步）</td><td colspan="2">4, 3, 2, 2</td><td>用源码里的余弦公式算出的</td></tr>
<tr><td>GPT 每步的 L（6 步）</td><td colspan="2">4, 4, 3, 2, 2, 2</td><td>同上</td></tr>
<tr><td>更新方式</td><td>patch</td><td>patch</td><td>增 / 删 / 改补丁，不整份重写</td></tr></table>

<h3>4. Gate：门控</h3>
<table><tr><th>参数</th><th>原版默认</th><th>我们的值</th><th>说明</th></tr>
<tr><td>指标</td><td>hard（答对比例）</td><td>hard（答对条数）</td><td>只有对错</td></tr>
<tr><td><b>接受条件</b></td><td>候选分 &gt; 当前分</td><td>首答模块：候选答对数 ≥ 当前 + <b>2</b>；回看、反思模块：≥ 当前（<b>不降低</b>）</td><td>用户决定；没有补丁的模块不验证</td></tr>
<tr><td>顺序</td><td>一个候选一次门控</td><td>按模块依次：首答 → 回看 → 反思；没有补丁的模块跳过</td><td>分模块归因</td></tr>
<tr><td>当前分的来源</td><td>上次接受时记下，不重测</td><td>同原版（S0 在验证集先跑一遍作为起点）</td><td>epoch = 1，没有“epoch 开头重测”</td></tr></table>

<h3>5. epoch 结束时的机制与其他</h3>
<table><tr><th>参数</th><th>值</th><th>说明</th></tr>
<tr><td>Slow Update、Meta Skill</td><td>不触发</td><td>原版从第 2 个 epoch 才开始</td></tr>
<tr><td>先验表更新</td><td>取消</td><td>用户决定；混淆信息固定来自 80 条矩阵</td></tr>
<tr><td>训练 / 验证切分</td><td>75 / 25，按组，种子 42</td><td>原版默认 2 : 1 : 7，我们的数据太少，不照搬</td></tr>
<tr><td>技能文档长度上限</td><td>1,500 字</td><td>防止提示词膨胀</td></tr>
<tr><td>优化器模型</td><td>Gemini → Gemini；GPT → GPT 6.1 SOL</td><td>用户指定为 6.1 SOL；实现时核对 API 里的名称（项目配置里目标 GPT 写作 gpt-6-sol）</td></tr>
<tr><td>目标模型每条样本的调用数</td><td>1–3 次（均值按 1.3 算）</td><td>首答 1 次；写了不确定点再加回看、反思各 1 次</td></tr></table>

<h3>failure batch 和 success batch</h3>
<p>沿用原版（failure_only = false）：一步的 40 条结果先按对错拆成失败堆和成功堆，各自切成 8 条一组，失败组找共同错因、成功组找该保留的做法，合并时失败优先。我们的两处改动：堆内先按类型排序再切（失败 F1→F4；成功 S1 在前、S2 在后），不足 4 条的尾组并入前一组。每组由一位反思模型读轨迹卡和样本信息，写出补丁，每条编辑标明改哪个模块。</p>
<table><tr><th>每步（40 条）估计</th><th>失败堆</th><th>成功堆</th></tr>
<tr><td>Gemini（正确率按 63% 估）</td><td>15 条 → 2 组（8、7）</td><td>25 条 → 3 组（8、8、9）</td></tr>
<tr><td>GPT（正确率按 44% 估）</td><td>23 条 → 3 组（8、8、7）</td><td>17 条 → 2 组（8、9）</td></tr></table>
<p class="small muted">比例是用 v5-E 无技能在 117 条测试上的正确率估的，只用来估组数。</p>
'''
P.append('<section class="panel"><h2>八、参数总表与调用量（粗算）</h2>' + PARAMS_HTML +
         '<table><tr><th>环节</th><th class="n">Gemini</th><th class="n">GPT</th><th>说明</th></tr>'
         '<tr><td>训练 rollout</td><td class="n">≈ 180</td><td class="n">≈ 300</td><td>每个训练样本跑一遍，按 1.3 次 / 条</td></tr>'
         '<tr><td>S0 基线（验证集）</td><td class="n">≈ 60</td><td class="n">≈ 105</td><td>验证 47（81）条 × 1.3</td></tr>'
         '<tr><td>门控</td><td class="n">≈ 490–730</td><td class="n">≈ 1,260–1,890</td><td>每次门控跑一遍验证集；每步 2–3 次（首答模块必有，回看、反思模块视有无补丁）</td></tr>'
         '<tr><td>反思（看媒体，载荷大）</td><td class="n">≈ 20</td><td class="n">≈ 30</td><td>每步约 5 次，每次带约 8 条样本的帧</td></tr>'
         '<tr><td><b>训练合计（看媒体）</b></td><td class="n"><b>≈ 700–1,000</b></td><td class="n"><b>≈ 1,700–2,300</b></td><td>含上一行的反思；没有 slow update、没有先验表更新</td></tr>'
         '<tr><td>合并 + 排序（纯文本）</td><td class="n">≈ 20–25</td><td class="n">≈ 30–35</td><td>每步 5–6 次</td></tr>'
         '<tr><td>测试 + 空技能对照</td><td class="n">≈ 160</td><td class="n">≈ 145</td><td>62（55）条 × 2 次运行 × 1.3</td></tr></table>'
         '<p class="small muted">1.3 次 / 条的来源：v5-E 无技能时 13 / 117 条触发回看，平均约 1.22 次；技能可能让触发变多，所以取 1.3。第 0 轮与图谱沿用 v6 已经跑完的结果，不重复计入。</p></section>')

P.append('<section class="panel"><h2>九、风险与对策</h2><table><tr><th>#</th><th>风险</th><th>依据</th><th>对策</th></tr>'
         '<tr><td>1</td><td><b>回看、反思模块的门控“不降低”会放进无效补丁</b>：这两个模块只影响被标记要回看的样本（v5-E 无技能时约 11%，13 / 117），验证集 47 / 81 条里只有约 5–9 条会触发回看，补丁多半不改变答对数，“不降低”会把它们当通过</td><td>F12；用户决定改用 ≥ 当前</td><td>已按你的决定；代价是这两个模块的补丁实际上几乎没有验证，结果里单独报告它们改了什么、有没有改变答案；冻结前人工通读</td></tr>'
         '<tr><td>2</td><td><b>门控被噪声带偏</b>：验证集只有 47 / 81 条</td><td>同一个 Direct 重跑五次，Gemini 62 条里答对 33–39、GPT 55 条里 20–26，极差 6 条（F11）</td><td>首答模块保留 +2 余量；测试时再跑一次空技能 v5-E 估噪声</td></tr>'
         '<tr><td>3</td><td><b>只有 1 个 epoch</b>：Gemini 4 步、GPT 6 步，技能最多被改 4–6 轮，改动可能很小</td><td>图 2、参数表</td><td>如实报告；若效果不明显，不能据此下结论说方法无效</td></tr>'
         '<tr><td>4</td><td><b>候选扩充依据很弱</b>：大多数 top1 只有 1–2 个样本支持，有的标签无记录</td><td>第五节的表</td><td>结果里逐项报告每个扩充的支持数；你已决定不设最小支持数</td></tr>'
         '<tr><td>5</td><td><b>80 条矩阵含 20 个测试样本的标准标签</b></td><td>80 条与 117 条测试的交集（Gemini 15、GPT 8）</td><td>你已决定先不处理；结果必须标注，不能声称无泄漏</td></tr>'
         '<tr><td>6</td><td>基线没有扩充，增益无法拆成“扩充”和“技能”</td><td>设计如此</td><td>你说先不管；结果里写明这一点</td></tr>'
         '<tr><td>7</td><td>回看贡献本身很小：技能能改善的主要是首答</td><td>v5-E 回看后只改了 2 条（F12）；首答 61 → 终答 63</td><td>报告里把“首答准确率”和“终答准确率”分开</td></tr>'
         '<tr><td>8</td><td>反思模型看视频后，可能把具体视频的内容写进规则；一次带 8 条样本的 64 张图，载荷大，各 API 的图片数 / 体积上限我还没核实；GPT 没有音轨</td><td>设计如此</td><td>补丁检查拦截样本 id 和字幕原句；实现前先做冒烟测试，必要时把每组缩小到 4 条</td></tr>'
         '<tr><td>9</td><td>训练的候选集（三专家第 0 轮并集）与测试的候选集（v4 的 candidate_labels）来源不同</td><td>我没有核对两者在 117 条上有多大差别</td><td>实现前先离线比较</td></tr>'
         '<tr><td>10</td><td>训练样本少，MER2024 无法按影片 / 说话人去重，MELD 的去重后 Gemini 只剩 87 条</td><td>图 2</td><td>已知限制；冻结前人工通读技能</td></tr>'
         '<tr><td>11</td><td>测试的 117 条之前被反复分析过，不是独立测试</td><td>F8–F12</td><td>结果一律标“开发集”，不宣称泛化</td></tr></table></section>')

P.append('<section class="panel"><h2>十、文件规划与已确认事项</h2><pre>'
         'versions/v6/skillopt_v5e/\n'
         '  skill_seed.md        三个模块的空标题（首答：A 区分线索 + B 何时写不确定点 / 回看：C / 反思：D）\n'
         '  split.py             按图 2 切分：对话去重 + 按组 75/25，写出 train / val / test 清单与 SHA256\n'
         '  confusion.py         读 80 条结果，建立“提供方 × 数据集 × 标签 → top1 真实标签（样本数 / 事件数）”查表；按候选集生成 C′ 与来源标记\n'
         '  prompts_opt/         SkillOpt 的 analyst_error / analyst_success / merge_final / ranking（MIT，注明出处）；加反思模型的任务说明（含三个模块的定义）\n'
         '  rollout.py           复用 versions/v5/orchestra.py 的 sample()，加参数：技能模块、C′ 来源、输出目录；校验器改为“答案 ∈ C′”\n'
         '  trajectory.py        给轨迹分类（F1–F4 / S1–S2），生成不含 id 的轨迹卡\n'
         '  lint.py              补丁检查（模块范围、无样本信息、不改格式、长度上限）\n'
         '  train.py             循环、按模块门控、断点续跑、日志\n'
         '  test.py              冻结技能跑 117 条 + 空技能对照\n'
         '修改 versions/v5/v5_prompts.py：first_answer / relook / reflect_final 各加一个可选的“技能模块 + 候选来源块”参数（默认 None，行为不变）\n'
         '服务器 outputs/v6_skillopt_v5e/&lt;provider&gt;/{split/, skills/step_XX.md, steps/step_XX.json, best_skill.md, test/, control/}\n'
         'metrics/v6_skillopt_v5e_&lt;provider&gt;.json，metrics/findings_log.md（新结论）</pre>'
         '<h3>已确认与默认</h3><ol>'
         '<li><b>已确认</b>：回看、反思模块的门控用“不降低”（≥ 当前），首答模块保留 +2；没有补丁的模块不验证。</li>'
         '<li><b>已确认</b>：GPT 的优化器用 6.1 SOL（实现时核对 API 名称；项目配置里目标 GPT 写作 gpt-6-sol）。</li>'
         '<li><b>已确认</b>：R²-MAD 的案例库不处理同对话问题（结果要标注这个风险）。</li>'
         '<li><b>已确认</b>：样本规模先按现在的来跑（Gemini 训练 137、GPT 233，1 个 epoch）。</li>'
         '<li><b>已确认</b>：只有反思模型看视频，合并和排序只处理补丁文字；反思模型每条样本看 8 帧（被标记回看的再加回看帧，Gemini 另有音轨），每组 8 条；若 API 载荷超限，缩小到每组 4 条。</li>'
         '<li><b>我的默认（你没有反对）</b>：每个阶段的提示词只带自己的模块。</li></ol>'
         '<div class="warn">你说“可以开始”之前，我不会写这些文件的代码，也不会调用任何模型。<br>已知限制：训练 / 验证样本来自官方测试集，测试的 117 条之前被反复分析过，80 条矩阵含 20 个测试样本的标准标签，结果只能当开发集结果。</div></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>SkillOpt 针对 v5-E 的设计</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v6-skillopt-v5e-design.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
