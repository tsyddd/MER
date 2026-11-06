"""Build docs/v6-skillopt-v5e-v2-design.html: design (nothing run) of the second version of SkillOpt-V5E for Gemini, fixing the problems
found in docs/v6-skillopt-v5e-report.html. Static HTML, no scripts, no model calls.
Numbers: metrics/v6_skillopt_v5e_report_data.json (results of version 1) and a read-only count of the v6 pool labels on the server (2026-11-06).
Usage: python scripts/build_skillopt_v5e_v2_design.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_paper_figs import CODE, CTRL, NEW, OUT, arrow, code_tag, diamond, doc, group, legend, llm_tag, module, svg, t  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / 'metrics' / 'v6_skillopt_v5e_report_data.json').read_text(encoding='utf8'))
G = D['gemini']
TEAL = ('#1F7A7A', '#DDF1F0')
RED = '#C0392B'
GREEN = '#2D6A4F'


def lines(x, y, items, size=10.0, step=15.5, color='#222'):
    return ''.join(t(x, y + i * step, s, size=size, color=color) for i, s in enumerate(items))


def box(x, y, w, h, color, title, tag, body, kind, badge=None):
    fl, st = color
    b = module(x, y, w, h, fl, st, title, None)
    b += code_tag(0, y - 22, right=x + w) if kind == 'code' else llm_tag(0, y - 22, tag, right=x + w)
    if badge:
        b += t(x + w - 8, y + 40, badge, size=10, anchor='end', color=RED, bold=True)
    b += lines(x + 10, y + 50, body)
    return b


def flow():
    b = ''
    # ---- band 1: data
    b += group(14, 44, 1222, 176, '一、数据（程序；Gemini 一套）', color='#666', fill='#f6f6f6')
    xs = [20 + i * 306 for i in range(4)]
    w, y, h = 288, 90, 118
    b += box(xs[0], y, w, h, CODE, '不一致池（同版本 1）', '', ['v6 池三专家第 0 轮不一致', 'MELD 去掉与测试同对话的', 'MER2024 97 条、MELD 87 条', '候选集 C = 三人答案并集'], 'code')
    b += box(xs[1], y, w, h, CODE, '按类分层切分', '', ['每类至少 3 条进验证（够 6 条的类）', 'MELD 仍按整段对话切', '验证：MER 25、MELD 22', '训练：其余（MER 72、MELD 65）'], 'code', '改')
    b += box(xs[2], y, w, h, CODE, '训练里按类加权抽样', '', ['每一步的 40 条按类均衡抽：', '各类等概率，类内随机', '（neutral 不再占一半）', '一个 epoch = 4 步'], 'code', '改')
    b += box(xs[3], y, w, h, CODE, '候选集：不扩充', '', ['版本 1 里扩充标签一次', '都没被选中，只是干扰', '→ 取消扩充，C 原样使用', '（可选对照见第五节）'], 'code', '改')
    for i in range(3):
        b += arrow([(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])
    # ---- band 2: loop
    b += group(14, 242, 1222, 360, '二、一步训练（红字 = 相对版本 1 的改动）', color=TEAL[0], fill=TEAL[1] + '33')
    xs = [20 + i * 174 for i in range(7)]
    w, y, h = 156, 306, 168
    b += box(xs[0], y, w, h, NEW, '① Rollout', 'LLM（看媒体）', ['40 条（按类均衡）', 'v5-E 带技能跑', '该数据集只读', '自己那一节技能'], 'llm', '改')
    b += box(xs[1], y, w, h, CODE, '② 分类分堆', '', ['F1–F4 / S1–S2', '按数据集分开成堆', '堆内同类相邻', '8 条一组'], 'code', '改')
    b += box(xs[2], y, w, h, CTRL[::-1], '③ 反思', 'LLM（看视频）', ['一位反思模型', '一组只含一个数据集', '看轨迹卡 + 视频', '写补丁：每条标明', '模块 + 数据集'], 'llm', '改')
    b += box(xs[3], y, w, h, CTRL[::-1], '④ 合并 + 裁剪', 'LLM（文本）', ['失败优先合并', '按（数据集, 模块）', '各留前 L 条', 'L：4 → 2'], 'llm')
    b += box(xs[4], y, w, h, CODE, '⑤ 检查', '', ['同版本 1，另加：', '不得出现该数据集', '没有的标签名', '不得写“一律判 X”', '这类方向性规则'], 'code', '改')
    b += box(xs[5], y, w, h, CTRL[::-1], '⑥ 超长先精简', 'LLM（文本）', ['某一节超过上限时：', '优化器把这一节', '改写合并到上限内', '再和补丁一起', '进门控'], 'llm', '新增')
    b += box(xs[6], y, w, h, NEW, '⑦ 门控', 'LLM（看媒体）', ['只在该数据集的', '验证样本上比较', '首答：类平均召回', '+0.05 且答对不降', '回看 / 反思：见下'], 'llm', '改')
    for i in range(6):
        b += arrow([(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])
    b += doc(20, 500, 520, 92, [], fold=8, stroke=TEAL[0])
    b += t(28, 518, '技能文档：按数据集分两节，每节三个模块', size=10.5, bold=True, color=TEAL[0])
    b += lines(28, 536, ['MER2024 节：首答 / 回看 / 反思　　MELD 节：首答 / 回看 / 反思', '每条样本只看自己数据集那一节；每节上限 900 字（两节合计 ≤ 1,800 字）',
                         '起点为空；训练前可选“种子”：版本 1 技能里的通用条目（见第五节，默认不用）'], size=9.8, step=17)
    b += doc(556, 500, 674, 92, [], fold=8, stroke=RED)
    b += t(564, 518, '回看 / 反思模块的门控（新）', size=10.5, bold=True, color=RED)
    b += lines(564, 536, ['只看“写了不确定点”的验证样本：候选必须至少改变 1 条答案，且', '改对的条数 − 改错的条数 ≥ 1；一条都没改变 → 视为无效，不接受',
                          '（版本 1 用“不降低”，12 步里接受了 9 次，epoch 2 只加了这类规则，测试 −4）'], size=9.8, step=17)
    b += arrow([(xs[6] + w / 2, y + h), (xs[6] + w / 2, 490), (xs[0] + w / 2, 490), (xs[0] + w / 2, y + h)], '#999', True)
    b += t(700, 486, '接受 → 该节更新；拒绝 → 不变，记入步骤缓冲；下一批', size=9.8, color='#555', anchor='middle')
    # ---- band 3: epochs + test
    b += group(14, 624, 1222, 168, '三、训练轮数与测试', color=GREEN, fill=OUT[0] + '33')
    xs = [20 + i * 306 for i in range(4)]
    w, y, h = 288, 668, 112
    b += box(xs[0], y, w, h, CODE, '3 个 epoch，早停', '', ['每个 epoch 结束在验证集重测当前技能', '两节都连续 1 个 epoch 没有接受', '任何补丁 → 提前结束'], 'code', '改')
    b += box(xs[1], y, w, h, CODE, '选最终技能', '', ['每个 epoch 结束各存一份', '按验证集“两个数据集类平均召回', '之和”选最高的一份（不是最后一份）'], 'code', '改')
    b += box(xs[2], y, w, h, NEW, '测试（62 条）', 'LLM（看媒体）', ['技能版本 2：跑 2 次（估噪声）', '对照：纯 v5-E 已有 1 次，再补 1 次', '同时报准确率和类平均召回'], 'llm', '改')
    b += box(xs[3], y, w, h, OUT, '判据（事先定）', '', ['两次均值比对照均值多 ≥ 3 条', '且两个数据集各自不低于对照', '否则判为无效'], 'code', '新增')
    for i in range(3):
        b += arrow([(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])
    b += legend(806)
    return svg(b, 830)


css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1260px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}
h1{font-size:25px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:18px 0 4px;color:#444}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 16px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:5px 8px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}.muted{color:#666}.small{font-size:13px}
.fig{background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px;margin:10px 0}.cap{font-size:14px;color:#333;margin:4px 6px 12px;line-height:1.7}
.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}.key{background:#eaf4ff;border-left:4px solid #48c;padding:10px 14px;margin:10px 0}
code{background:#eee;padding:0 4px;border-radius:3px}'''

gt = G['test']
P = []
P.append('<h1>SkillOpt-V5E 版本 2 设计（Gemini）</h1>')
P.append('<p class="muted">日期 2026-11-06。<b>只有设计，没有实现、没有运行。</b>针对 <code>docs/v6-skillopt-v5e-report.html</code> 找到的问题。'
         '橙色 = 大模型调用，蓝灰 = 程序，紫 = 反思 / 合并，红字 = 相对版本 1 的改动。</p>')

P.append('<section class="panel"><h2>零、版本 1 的问题与对应改法</h2><table><tr><th>版本 1 的问题（证据）</th><th>版本 2 的改法</th></tr>'
         f'<tr><td><b>学到“偏向 neutral”</b>：训练 / 验证的 MELD 里 neutral 占 32–46%，测试只占 6%；技能把测试 MELD 判成 neutral 的从 {gt["control"]["MELD"]["pred_neutral"]} 条推到 {gt["skill_8da2df63"]["MELD"]["pred_neutral"]} 条，MELD 答对 {gt["control"]["MELD"]["correct"]} → {gt["skill_8da2df63"]["MELD"]["correct"]}</td>'
         '<td>① 首答门控改用<b>类平均召回</b>（多判 neutral 拿不到好处）；② 训练批次按类均衡抽样；③ 验证集按类分层切分</td></tr>'
         '<tr><td><b>两个数据集互相拖累</b>：MER2024 一直升、MELD 一直降，但合在一起的总分过了门控；技能混用两个数据集的标签名</td>'
         '<td>技能<b>按数据集分节</b>，门控按数据集分别做；检查拒绝出现该数据集没有的标签</td></tr>'
         '<tr><td><b>回看 / 反思门控不设防</b>：“不降低”下 12 步接受了 9 次，epoch 2 只加了这类规则，测试 36 → 32</td>'
         '<td>只看写了不确定点的验证样本，<b>必须改变至少 1 条答案且净多对 ≥ 1</b></td></tr>'
         '<tr><td><b>epoch 3 空转</b>：技能 1,452 字，15 条编辑全被 1,500 字上限丢掉</td><td>超长时<b>先让优化器精简改写这一节</b>，再和补丁一起门控；每节上限 900 字</td></tr>'
         '<tr><td><b>扩充标签没用</b>：4 组测试里一次都没被选中，只让 3 条真实标签进入候选</td><td><b>取消候选扩充</b>（你之前要求加的；这里建议去掉，需要你同意）</td></tr>'
         '<tr><td><b>验证升、测试降</b>：验证 20 → 27，测试 37 → 32；单次测试运行噪声约 ±3 条</td><td>选最终技能按验证类平均召回而不是“最后一份”；测试跑 2 次，并<b>事先定好判据</b></td></tr></table></section>')

P.append('<section class="panel"><h2>一、总览流程图</h2><div class="fig">' + flow() + '</div>'
         '<p class="cap"><b>图 1　版本 2 的数据、一步训练、轮数与测试。</b>循环骨架（rollout → 分堆 → 看视频的反思 → 合并 → 裁剪 → 检查 → 门控）与版本 1 相同，'
         '改动集中在：按数据集分开、门控的指标与规则、训练批次的抽样、超长处理、选最终技能和测试判据。</p></section>')

P.append('<section class="panel"><h2>二、关键改动细节</h2>'
         '<h3>1. 首答模块的门控：类平均召回</h3>'
         '<p>类平均召回 = 每个真实类别的召回率取平均。版本 1 里多判 neutral 能在 neutral 多的验证集上多拿分；换成类平均召回后，neutral 只算一个类，其他类的召回下降会把它抵消。</p>'
         '<ul><li><b>接受条件</b>：候选在<b>该数据集</b>验证样本上的类平均召回 ≥ 当前 + 0.05，且该数据集答对条数不下降。</li>'
         '<li><b>0.05 的来由</b>：验证每个数据集 22–25 条，最小的类 3 条，单个样本对类平均召回的影响约 0.03–0.06；0.05 约等于“有一个小类多对了一条”。这是我定的值，可以调。</li>'
         '<li>按版本 1 的记录回看：GPT 第 2、4 步被接受的首答补丁，验证 MELD 类平均召回是 0.44 → 0.37 → 0.31，新规则下会被拒绝。</li></ul>'
         '<h3>2. 按数据集分节</h3>'
         '<ul><li>技能分 MER2024 节和 MELD 节，各自含首答 / 回看 / 反思三个模块；每条样本的提示词只带自己数据集那一节。</li>'
         '<li>分堆、反思、合并、裁剪、门控都按数据集分开；一组 8 条轨迹只来自一个数据集，反思模型只为这个数据集写补丁。</li>'
         '<li>检查新增两条：不得出现该数据集没有的标签名（例如 MELD 节里出现 worried）；不得写“一律 / 优先判为某个标签”这类不看证据的方向性规则（用关键词检查，会有漏网，冻结前人工通读）。</li></ul>'
         '<h3>3. 回看 / 反思模块的门控</h3>'
         '<p>只在验证集里“写了不确定点”的样本上比较（这两个模块只影响这些样本）。候选至少改变 1 条答案，且改对数 − 改错数 ≥ 1 才接受。版本 1 的 Gemini 验证集里写了不确定点的只有几条，所以这两个模块大概率很少被更新——这是我们要的：没有证据就不改。</p>'
         '<h3>4. 训练数据：分层切分 + 均衡抽样</h3>'
         '<p>不一致池的标签（Gemini，去掉同对话样本后）：MER2024 97 条 = neutral 23、sad 21、worried 17、surprise 14、happy 11、angry 11；'
         'MELD 87 条 = neutral 37、joy 14、anger 12、sadness 11、surprise 11、disgust 2、fear 0。</p>'
         '<ul><li><b>验证</b>：按类分层，够 6 条的类至少 3 条进验证。离线试算：MER2024 验证 25 条（neutral 6、sad 5、worried 4、surprise 4、happy 3、angry 3），'
         'MELD 验证 22 条（neutral 9、joy 4、anger 3、sadness 3、surprise 3）。MELD 仍按整段对话切。</li>'
         '<li><b>训练</b>：每步 40 条按类均衡抽（各类等概率，类内随机，不重复直到这一类用完），使 neutral 不再占一半。</li>'
         '<li><b>限制</b>：MELD 的 fear 在池里一条都没有、disgust 只有 2 条，而测试 MELD 有 fear 7 条、disgust 4 条；这两类在训练和验证里都几乎学不到。'
         '可选补救：让 v6 池继续处理 MELD 剩下的 523 条（其中 fear 5、disgust 7），需要约 10 小时的筛选调用（图谱 + 三专家第 0 轮），默认不做。</li></ul>'
         '<h3>5. 超长处理</h3>'
         '<p>某一节超过 900 字时，先调用一次“精简改写”（改写自 SkillOpt 的 rewrite_skill 提示词：合并重复、删去无效条目，保留有效指导），'
         '改写后的版本和本步的补丁一起作为候选进门控；改写结果本身不过门控就不生效。</p>'
         '<h3>6. 轮数、早停与选最终技能</h3>'
         '<ul><li>最多 3 个 epoch；两节都连续一个 epoch 没有接受任何补丁就提前结束。</li>'
         '<li>每个 epoch 结束在验证集上重测当前技能，按“两个数据集类平均召回之和”选最高的一份作为最终技能（版本 1 用的是最后一份）。</li></ul></section>')

P.append('<section class="panel"><h2>三、测试与判据（事先定好）</h2><ul>'
         '<li><b>测试集</b>：同版本 1，Gemini 62 条（MER2024 26、MELD 36）；候选集用 v4 的 candidate_labels，不扩充。</li>'
         '<li><b>运行</b>：版本 2 技能跑 2 次；对照（纯 v5-E、空技能、不扩充）版本 1 已有 1 次（37），再补 1 次。</li>'
         '<li><b>成功判据</b>：技能 2 次的均值比对照 2 次的均值多 ≥ 3 条，且 MER2024、MELD 各自不低于对照均值。达不到就判为“版本 2 无效”，不再据测试结果调整。</li>'
         '<li><b>同时报告</b>：准确率、每个数据集的类平均召回、判成 neutral 的条数、写了不确定点的条数与回看改判对错。</li></ul></section>')

P.append('<section class="panel"><h2>四、调用量与时间（粗算）</h2><table><tr><th>环节</th><th class="n">调用次数</th><th>说明</th></tr>'
         '<tr><td>训练 rollout</td><td class="n">≈ 210–630</td><td>每 epoch 137 条 × 1.3 次；1–3 个 epoch（早停）</td></tr>'
         '<tr><td>首答门控</td><td class="n">≈ 260–780</td><td>每步每个数据集一次，只跑该数据集的验证（22–25 条 × 1.3）</td></tr>'
         '<tr><td>回看 / 反思门控</td><td class="n">≈ 50–150</td><td>复用首答缓存，只重跑写了不确定点的样本</td></tr>'
         '<tr><td>反思（看视频）+ 合并 / 排序 / 精简（文本）</td><td class="n">≈ 60–180</td><td>每步按数据集分开，组数略多于版本 1</td></tr>'
         '<tr><td>测试</td><td class="n">≈ 240</td><td>62 条 × 3 次运行 × 1.3</td></tr>'
         '<tr><td><b>合计</b></td><td class="n"><b>≈ 800–2,000</b></td><td>Gemini 版本 1 的 epoch 1 用了约 30 分钟（4 步）；版本 2 门控按数据集分开、次数更多，估计 1–3 小时 + 测试约 30 分钟</td></tr></table></section>')

P.append('<section class="panel"><h2>五、需要你决定</h2><ol>'
         '<li><b>取消候选扩充</b>：版本 1 里扩充标签一次都没被选中。建议取消；如果你想保留，可以多跑一组“版本 2 + 扩充”作对照。</li>'
         '<li><b>首答门控阈值</b>：类平均召回 +0.05 且答对不降。合适吗？</li>'
         '<li><b>起点</b>：从空技能开始（默认），还是用版本 1 epoch-1 技能里人工挑出的通用条目做种子？我建议从空开始，避免把 neutral 偏向带进来。</li>'
         '<li><b>MELD 的 fear / disgust 太少</b>：接受这个限制（默认），还是先让 v6 池处理剩下的 523 条 MELD（约 10 小时）？</li>'
         '<li><b>GPT</b>：GPT 版本 1 仍在运行（epoch 1 第 5–6 步）。让它按版本 1 跑完作对照，还是停掉、之后改用版本 2？</li></ol>'
         '<div class="warn">你确认之前，我不会改代码、不会启动运行。版本 1 的代码和结果保留不动，版本 2 写在新目录（<code>versions/v6/skillopt_v5e_v2/</code>，输出 <code>outputs/v6_skillopt_v5e_v2/</code>）。<br>'
         '已知限制不变：测试的 62 条之前被反复分析过，是开发集；样本来自官方测试集。</div></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>SkillOpt-V5E 版本 2 设计（Gemini）</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v6-skillopt-v5e-v2-design.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
