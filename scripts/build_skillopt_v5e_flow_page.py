"""Build docs/v6-skillopt-v5e-flow.html: one overview flow chart of the whole SkillOpt-V5E design (data preparation -> training loop
-> freeze / test). Design only, nothing run, no model calls. Details and numbers: docs/v6-skillopt-v5e-design.html.
Usage: python scripts/build_skillopt_v5e_flow_page.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_paper_figs import CODE, CTRL, NEW, OUT, arrow, code_tag, doc, group, legend, llm_tag, module, svg, t  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEAL = ('#1F7A7A', '#DDF1F0')
RED = '#C0392B'


def lines(x, y, items, size=10.0, step=15.5, color='#222'):
    return ''.join(t(x, y + i * step, s, size=size, color=color) for i, s in enumerate(items))


def box(x, y, w, h, color, title, num, tag, body, tag_kind):
    fl, st = color
    b = module(x, y, w, h, fl, st, title, num)
    if tag_kind == 'code':
        b += code_tag(0, y - 22, right=x + w)
    else:
        b += llm_tag(0, y - 22, tag, right=x + w)
    b += lines(x + 10, y + 48, body)
    return b


def flow():
    b = ''
    # ------------------------------------------------------------------ band 1: data
    b += group(14, 44, 1222, 184, '一、数据准备（程序，一次性；每个模型各一套）', color='#666', fill='#f6f6f6')
    xs = [20 + i * 246 for i in range(5)]
    w = 226
    y = 100
    h = 112
    b += box(xs[0], y, w, h, CODE, '候选池', 1, '', ['5 模型评测目录 3,779 条', '去掉旧 400 条（测试来源）', '→ 3,377 条', 'MER 969 + MELD 2,408'], 'code')
    b += box(xs[1], y, w, h, NEW, '图谱 + 三专家第 0 轮', 2, '已有，不新增调用', ['v6 pool.py 已跑完', '冻结 Gemini 图谱', '三专家各答一次', '候选集 C = 三人答案并集'], 'llm')
    b += box(xs[2], y, w, h, CODE, '不一致池 + 对话去重', 3, '', ['三人答案没有唯一共同标签', 'MELD 去掉与旧 400 条同对话的', 'Gemini：97 + 87 = 184 条', 'GPT：161 + 153 = 314 条'], 'code')
    b += box(xs[3], y, w, h, CODE, '按组切分 75 / 25', 4, '', ['Gemini 训练 137 / 验证 47', 'GPT 训练 233 / 验证 81', 'MELD 整段对话进同一边', '种子 42'], 'code')
    b += box(xs[4], y, w, h, TEAL[::-1], '混淆矩阵 top1 查表', 5, '', ['80 条旧样本，该提供方 5 组结果', '提供方 × 数据集 × 方向', '“答案是 c → 真实标签最常是 g”', '没有记录的标签不扩充'], 'code')
    for i in range(4):
        b += arrow([(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])
    # ------------------------------------------------------------------ band 2: training loop
    b += group(14, 238, 1222, 336, '二、训练循环（1 个 epoch：Gemini 4 步、GPT 6 步；一步 = 40 条训练样本）', color=TEAL[0], fill=TEAL[1] + '33')
    xs = [20 + i * 174 for i in range(7)]
    w = 156
    y = 304
    h = 150
    b += box(xs[0], y, w, h, CODE, '① 取一批', None, '', ['取 40 条训练样本', '每条：C′ = 原候选', '+ 混淆矩阵 top1 扩充', '（标明哪些是扩充）'], 'code')
    b += box(xs[1], y, w, h, NEW, '② Rollout', None, 'LLM（看媒体）', ['v5-E 带着技能 S', '首答 → 回看 → 反思', '答案只能在 C′ 内选', '得分：是否等于', '标准标签'], 'llm')
    b += box(xs[2], y, w, h, CODE, '③ 分类轨迹', None, '', ['失败 F1–F4', '成功 S1–S2', '分成失败堆、成功堆', '堆内按类型排序', '切成 8 条一组'], 'code')
    b += box(xs[3], y, w, h, CTRL[::-1], '④ 反思', None, 'LLM（看视频）', ['一位反思模型读一组：', '轨迹卡 + 样本信息', '+ 视频帧（Gemini 有音轨）', '写补丁，每条编辑', '标明改哪个模块'], 'llm')
    b += box(xs[4], y, w, h, CTRL[::-1], '⑤ 合并 + 裁剪', None, 'LLM（文本）', ['失败补丁优先合并', '按模块分开', '每个模块留前 L 条', 'L：4 → 2 余弦衰减'], 'llm')
    b += box(xs[5], y, w, h, CODE, '⑥ 检查 + 应用', None, '', ['只改自己的模块', '不含样本 id / 字幕原句', '不改输出格式', '全文 ≤ 1,500 字', '→ 候选 S′'], 'code')
    b += box(xs[6], y, w, h, NEW, '⑦ 分模块门控', None, 'LLM（看媒体）', ['S′ 在验证集跑 v5-E', '模块依次比较：', '首答模块 ≥ 当前 + 2', '回看、反思模块 ≥ 当前', '没有补丁的不验证'], 'llm')
    for i in range(6):
        b += arrow([(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])
    # skill doc + loop
    b += group(194, 484, 520, 78, '技能文档 S（一个提示词、三个模块；起点只有空标题）', color=TEAL[0], fill='#fff')
    b += doc(204, 512, 156, 44, ['A 区分线索 + B 不确定点'], title='首答模块', fill='#fff', stroke=TEAL[0], size=9.5, fold=6)
    b += doc(368, 512, 156, 44, ['C 回看时怎么看'], title='回看模块', fill='#fff', stroke=TEAL[0], size=9.5, fold=6)
    b += doc(532, 512, 172, 44, ['D 何时改答案'], title='反思模块', fill='#fff', stroke=TEAL[0], size=9.5, fold=6)
    b += arrow([(272, 484), (272, y + h)], TEAL[0])
    b += arrow([(620, 484), (620, y + h)], TEAL[0])
    b += t(280, 474, '读 S（三个阶段各带自己的模块）', size=9.8, color=TEAL[0])
    b += t(628, 474, '反思模型也读 S', size=9.8, color=TEAL[0])
    b += arrow([(xs[6] + w / 2, y + h), (xs[6] + w / 2, 468), (xs[0] + w / 2, 468), (xs[0] + w / 2, y + h)], '#999', True)
    b += t(800, 464, '接受 → S ← S′；拒绝 → S 不变；然后取下一批 40 条', size=9.8, color='#555', anchor='middle')
    b += doc(730, 484, 498, 78, [], fold=8, stroke='#999')
    b += lines(738, 502, ['没有 epoch 结束的机制：epoch = 1，Slow Update / Meta Skill 不触发', '被优化的目标模型：Gemini、GPT 各训一份技能', '反思 / 合并模型：Gemini 用 Gemini，GPT 用 GPT 6.1 SOL（实现时核对名称）'], size=9.6, step=16)
    # ------------------------------------------------------------------ band 3: freeze + test
    b += group(14, 596, 1222, 186, '三、冻结 → 测试（只跑一次）', color='#2D6A4F', fill=OUT[0] + '33')
    xs = [20 + i * 306 for i in range(4)]
    w = 288
    y = 664
    h = 104
    b += box(xs[0], y, w, h, CODE, '冻结', None, '', ['取验证分最高的那份 S', '= best_skill.md', '写入 SHA256'], 'code')
    b += box(xs[1], y, w, h, CODE, '人工审查', None, '', ['我通读一遍：样本泄漏、', '标签先验、过窄的规则', '你批准后才进入测试'], 'code')
    b += box(xs[2], y, w, h, NEW, '测试', None, 'LLM（看媒体）', ['旧 400 条里 v4 不一致的 117 条', 'Gemini 62 + GPT 55，同样做候选扩充', '另跑一次空技能 v5-E 估噪声'], 'llm')
    b += box(xs[3], y, w, h, OUT, '判据', None, '', ['合计 ≥ Direct 均值 + 4（≥ 64.4）', '两家各自不低于自己的均值', '首答 / 终答、回看改答案分开报告'], 'code')
    for i in range(3):
        b += arrow([(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])
    b += arrow([(xs[0] + w / 2, 574), (xs[0] + w / 2, y)], '#555')
    b += t(xs[0] + w / 2 + 8, 590, '训练结束', size=9.8, color='#555')
    b += legend(800)
    return svg(b, 824)


css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1260px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}
h1{font-size:25px}code{background:#eee;padding:0 4px;border-radius:3px}.muted{color:#666}.small{font-size:13px}
.fig{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px;margin:10px 0}.cap{font-size:14px;color:#333;margin:4px 6px 12px;line-height:1.7}
.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}'''
body = ('<h1>SkillOpt 针对 v5-E：总览流程图</h1>'
        '<p class="muted">日期 2026-11-05。<b>只有设计，没有实现、没有运行、没有结果。</b>橙色 = 大模型调用，蓝灰 = 程序，紫 = 反思 / 合并，青绿 = 技能文档。细节、参数与风险见 <code>docs/v6-skillopt-v5e-design.html</code>。</p>'
        '<div class="fig">' + flow() + '</div>'
        '<p class="cap"><b>怎么读这张图。</b>① 数据准备：从池里取三专家第 0 轮不一致的样本，去掉与测试同对话的 MELD 样本后切成训练 / 验证；另用 80 条旧样本的混淆矩阵建 top1 查表。'
        '② 训练：每一步取 40 条，用扩充后的候选集 C′ 让 v5-E 带着技能跑一遍；轨迹分类后交给一位能看视频的反思模型写补丁，合并、裁剪、检查后分模块过验证集门控，通过才更新技能。'
        '只训练 1 个 epoch。③ 冻结最好的技能，人工审查后在 117 条测试样本上只跑一次。</p>'
        '<div class="warn">已确认：回看、反思模块用“不降低”门控；GPT 优化器用 6.1 SOL（实现时核对名称）；R²-MAD 案例库不处理；样本规模先这样跑。待实现时核对：反思模型一次带 8 条样本的载荷。'
        '已知限制：80 条矩阵含 20 个测试样本的标准标签；测试的 117 条之前被反复分析过，结果只能当开发集结果。</div>')
html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>SkillOpt 针对 v5-E：总览流程图</title><style>%s</style></head><body>%s</body></html>' % (css, body)
out = ROOT / 'docs' / 'v6-skillopt-v5e-flow.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
