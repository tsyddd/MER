"""Build docs/self-evolving-interactive-design.html: a training-free, self-evolving multi-expert method modelled on
Zhou et al. 2022, "Multi-Classifier Interactive Learning for Ambiguous Speech Emotion Recognition" (IEEE/ACM TASLP 30).

Design document only: no model calls, no server access. The evidence tables are computed from saved outputs
(v3 expert answers of GPT / Gemini / Omni) and from scripts/build_candidate_set_view.py. Gold labels are used only
for evaluation. Usage: python scripts/build_interactive_design.py
"""
import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import build_candidate_set_view as CS  # noqa: E402
from build_debate_survey import CSS, arrow, box, diamond, e, lab, svg  # noqa: E402

V3 = ROOT / 'outputs' / 'gemini_graph_emotion_wheel_v3'
ROLES = ['graph', 'audio_subtitle', 'image']
RN = {'graph': '图谱', 'audio_subtitle': '音频字幕', 'image': '图像'}
PROVS = ['gpt', 'gemini', 'omni']
GOLD = CS.GOLD


def jread(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf8'))
    except Exception:
        return None


ANS = {f'{p}:{r}': {i: (jread(V3 / p / i / f'expert_{r}.json') or {}).get('answer') for i in GOLD} for p in PROVS for r in ROLES}


def fleiss(ids, members):
    n = len(members)
    P, pj = [], Counter()
    for i in ids:
        c = Counter(ANS[m][i] for m in members)
        P.append((sum(v * v for v in c.values()) - n) / (n * (n - 1)))
        pj.update(c)
    tot = len(ids) * n
    Pe = sum((v / tot) ** 2 for v in pj.values())
    return (sum(P) / len(P) - Pe) / (1 - Pe)


def group_row(name, members):
    ids = [i for i in GOLD if all(ANS[m][i] for m in members)]
    n = len(ids)
    acc = [sum(ANS[m][i] == GOLD[i] for i in ids) for m in members]
    union = sum(any(ANS[m][i] == GOLD[i] for m in members) for i in ids)
    vote = ties = 0
    for i in ids:
        c = Counter(ANS[m][i] for m in members).most_common()
        if len(c) > 1 and c[0][1] == c[1][1]:
            ties += 1
        else:
            vote += c[0][0] == GOLD[i]
    pairs = list(combinations(members, 2))
    both = sum(sum(ANS[a][i] != GOLD[i] and ANS[b][i] != GOLD[i] for i in ids) for a, b in pairs) / (len(pairs) * n)
    indep = sum((sum(ANS[a][i] != GOLD[i] for i in ids) / n) * (sum(ANS[b][i] != GOLD[i] for i in ids) / n) for a, b in pairs) / len(pairs)
    same = sum(sum(ANS[a][i] == ANS[b][i] != GOLD[i] for i in ids) for a, b in pairs) / (len(pairs) * n)
    tie = f'（平票 {ties}）' if ties else ''
    return (f'<tr><td>{e(name)}</td><td class="n">{n}</td><td class="n">{min(acc)}–{max(acc)}</td><td class="n">{vote}{tie}</td>'
            f'<td class="n"><b>{union}（{100 * union / n:.1f}%）</b></td><td class="n">{fleiss(ids, members):.2f}</td>'
            f'<td class="n">{100 * both:.1f}% / {100 * indep:.1f}%</td><td class="n">{100 * same:.1f}%</td></tr>')


def hetero_table():
    rows = [('GPT 三角色', [f'gpt:{r}' for r in ROLES]), ('Gemini 三角色', [f'gemini:{r}' for r in ROLES]),
            ('Omni 三角色', [f'omni:{r}' for r in ROLES])]
    rows += [(f'跨模型·{RN[r]}专家（GPT / Gemini / Omni）', [f'{p}:{r}' for p in PROVS]) for r in ROLES]
    rows += [('GPT + Gemini 六位', [f'{p}:{r}' for p in ('gpt', 'gemini') for r in ROLES]),
             ('GPT + Gemini + Omni 九位', [f'{p}:{r}' for p in PROVS for r in ROLES])]
    h = ('<table><tr><th>成员组合</th><th>样本</th><th>单个成员答对</th><th>多数投票答对</th><th>任一成员答对（并集）</th><th>Fleiss κ</th>'
         '<th>两两同时答错 / 独立假设下</th><th>两两给出同一个错答案</th></tr>')
    return h + ''.join(group_row(n, m) for n, m in rows) + '</table>'


def candidate_table():
    h = '<table><tr><th>模型</th><th>只看专家答案 E</th><th>E ∪ 第 1 个易混淆标签</th><th>随机加 1 个的期望</th><th>E ∪ 前 2 个</th><th>随机加 2 个的期望</th><th>平均候选集大小（k=0→1）</th></tr>'
    for prov in ('gpt', 'gemini'):
        rows = CS.topk_stats(prov)
        n = len(rows)
        base = sum(1 for r in rows if r['pos'] is None)
        miss = [r for r in rows if r['pos'] is not None]
        k1 = base + sum(1 for r in miss if r['pos'] <= 1)
        k2 = base + sum(1 for r in miss if r['pos'] <= 2)
        r1 = base + sum(min(1, r['R']) / r['R'] for r in miss)
        r2 = base + sum(min(2, r['R']) / r['R'] for r in miss)
        sz0 = sum(len(r['E']) for r in rows) / n
        h += (f'<tr><td>{prov.upper()}</td><td class="n">{base}/{n}</td><td class="n"><b>{k1}/{n}</b></td><td class="n">{r1:.1f}</td>'
              f'<td class="n">{k2}/{n}</td><td class="n">{r2:.1f}</td><td class="n">{sz0:.2f} → {sz0 + 1:.2f}</td></tr>')
    return h + '</table>'


# ------------------------------------------------------------------ diagrams
def d_mcil():
    b = lab(20, 22, 'Zhou 等 2022 的 MCIL（论文图 1 的简化重绘）', 'start', 'l b')
    b += box(20, 60, 150, 70, ['D1：有精确标签', '（MAS 6,000 条）'], 'plain')
    b += box(220, 40, 170, 110, ['训练 N 个不同架构', '分类器（交叉熵）', 'ResNet / VGG /', 'DenseNet …'], 'exist') + arrow([(170, 95), (220, 95)])
    b += box(440, 40, 190, 110, ['D2：无标签', '（13,400 条）', '各分类器投票 →', '模糊标签 = 投票比例'], 'new') + arrow([(390, 95), (440, 95)])
    b += box(680, 40, 150, 110, ['交互学习', '用 KL 损失向', '模糊标签重训', '每个分类器'], 'new') + arrow([(630, 95), (680, 95)])
    b += box(870, 50, 150, 90, ['D3：测试', '选最好的单个', '分类器作最终决策'], 'judge') + arrow([(830, 95), (870, 95)])
    b += lab(20, 196, '理论依据（最优交互理论）：能力相近的个体交流后，联合敏感度 S_joint ≈ √(Σ S_i²) ≥ max S_i；但"群体很少胜过其最好的成员"，所以最后选最好的单个分类器。', 'start')
    return svg(1040, 215, b, 'MCIL 流程')


def d_design():
    b = lab(20, 22, '我们的训练免费版：多专家交互自进化（不改模型权重，只更新每位成员的"可进化状态"）', 'start', 'l b')
    # stage A
    b += box(20, 50, 210, 120, ['A. 能力评估', 'D1（train 的一半，有标签）', '每位成员的准确率 →', '权重 w、去掉弱成员、', '易混淆先验表'], 'plain')
    # stage B
    b += box(290, 50, 230, 120, ['B. 构造模糊标签', 'D2（train 另一半，不看标签）', '成员独立判断 → 加权投票分布 Ỹ', '候选集 C = 支撑集', '∪ 第 1 个易混淆标签（F1）'], 'new')
    # stage C
    b += box(580, 50, 230, 120, ['C. 交互学习（自进化）', '每位成员对照 Ỹ 更新状态：', 'C1 案例记忆', 'C2 规则补丁', 'C3 输出校准'], 'new')
    b += diamond(890, 110, 62, 52, ['D1 上', '变好了？'])
    b += arrow([(230, 110), (290, 110)]) + arrow([(520, 110), (580, 110)]) + arrow([(810, 110), (828, 110)])
    b += arrow([(890, 162), (890, 205), (405, 205), (405, 170)], dashed=True) + lab(650, 222, '是：接受更新，用更新后的成员重新构造 Ỹ（迭代 T 轮）', 'middle')
    b += lab(962, 100, '否：停止迭代', 'start', 'l b') + arrow([(952, 110), (990, 110), (990, 260)])
    # stage D
    b += box(700, 260, 330, 90, ['D. 决策（D3 = 80 条验证集，只评估一次）', '在 D1 上选：最好的单个成员', '或候选集 C 内的加权投票'], 'judge')
    b += box(20, 260, 600, 90, ['测试时每位成员独立判断、互不可见（保持独立性，避免辩论里看到的从众）；', '"交互"只发生在 D2 上，用来改变成员的先验，', '而不是在测试样本上互相说服。'], 'plain')
    return svg(1050, 370, b, '多专家交互自进化')


def d_state():
    b = lab(20, 22, '"重训"的三种训练免费替代（都只改成员的外部状态，不改模型权重）', 'start', 'l b')
    items = [('C1 案例记忆', ['把 D2 样本的简述、模糊标签 Ỹ、', '关键证据存成案例库；', '推理时检索相似案例作参考']),
             ('C2 规则补丁', ['统计成员与 Ỹ 的系统性偏离', '（如总把 Ỹ 以 angry 为主的判成 worried）', '→ 生成 1 条短规则，经门控才保留']),
             ('C3 输出校准', ['让成员在候选集 C 上输出概率；', '用 Ỹ 拟合每位成员的少量偏置参数', '（最接近论文的 KL 重训）'])]
    for k, (t, lines) in enumerate(items):
        x = 20 + k * 345
        b += box(x, 45, 320, 120, [t] + lines, 'new')
    b += lab(20, 195, '共同门控：任何更新只有在有标签的 D1 上不变差才被接受；所有提示词里都不含真实标签（只含群体分布 Ỹ）。', 'start')
    return svg(1060, 210, b, '三种状态更新')


PSEUDO = '''members = [(模型, 角色) for 模型 in {GPT, Gemini, Omni} for 角色 in {图谱, 音频字幕, 图像}]

# A. 能力评估（D1，有标签）
for m in members:
    acc[m], confusion[m] = evaluate(m, D1)
keep  = [m for m in members if acc[m] >= max(acc) - δ]         # 论文与理论：能力相近才有交互收益
w[m]  = log(acc[m] / (1 - acc[m]))                              # 建议：分类场景下的"逆方差加权"（独立投票者的最优加权）
prior = 错判次数表(pred → gold, D1)                             # 用于候选集扩展（F1）
state[m] = {cases: [], rules: [], calib: 恒等}                  # 可进化状态，不改模型权重

for t in 1..T:                                                  # B + C：自进化循环（D2，不看标签）
    for x in D2:
        votes  = {m: run(m, x, state[m]) for m in keep}          # 每位成员独立判断，互不可见
        Ỹ[x]   = normalize(Σ_m w[m] · onehot(votes[m]))          # 模糊标签
        C[x]   = support(Ỹ[x]) ∪ top1_confusable(support(Ỹ[x]), prior)
    for m in keep:
        cand = update(state[m], D2, Ỹ, C)                        # C1 / C2 / C3 之一或组合
        if acc_on(D1, m, cand) >= acc_on(D1, m, state[m]):       # 门控：用有标签数据决定接不接受
            state[m] = cand
    if group_acc_on(D1) 不再提升: break                          # 停止条件看准确率，不看一致性 κ

# D. 决策：在 D1 上（交叉验证）选"最好的单个成员"或"候选集 C 内加权投票"，
#    然后在 80 条验证集上只评估一次。'''


def build():
    body = f'''<div class="eyebrow">DESIGN · SELF-EVOLVING MULTI-EXPERT INTERACTION</div>
<h1>模仿 MCIL 的"最优交互"思路，设计一个训练免费的多专家自进化方法</h1>
<p class="muted">参考：Zhou, Liang, Gu, Yin, Yao. <i>Multi-Classifier Interactive Learning for Ambiguous Speech Emotion Recognition</i>. IEEE/ACM TASLP, vol. 30, 2022, pp. 695–705, doi 10.1109/TASLP.2022.3145287。以下论文内容取自我对全文的阅读；设计部分是我的建议，尚未实现、未运行、没有成绩。</p>

<div class="tldr">
<div class="tl k"><b>① 论文的核心不是"测试时讨论"，而是"离线用群体分布重训每个成员"</b>多个不同架构的分类器先在有标签数据上训练，再在无标签数据上投票得到"模糊标签"（投票比例），然后每个分类器用 KL 损失向这个分布重训。测试时各自独立判断，最后选最好的那一个。</div>
<div class="tl k"><b>② 我们的对应做法</b>把"重训"换成训练免费的状态更新（案例记忆、规则补丁、输出校准）；模糊标签用加权投票分布，候选集用"专家答案 ∪ 第 1 个易混淆标签"（发现 F1）；成员换成跨模型的九位专家（发现 F2）。</div>
<div class="tl w"><b>③ 和我们做过的辩论有本质区别</b>辩论是在测试样本上互相说服，结果几乎全是从众（辩论 ≈ 投票）。MCIL 式的交互发生在另一批数据上，测试时成员仍然独立，不会把测试判断拉向多数。</div>
<div class="tl w"><b>④ 需要先说清的限制</b>论文的增益来自梯度重训和大量无标签数据（MAS 的 D2 有 13,400 条）；我们只有 train 的 320 条、不改权重，效果可能小得多。论文最后用测试集准确率选分类器，这一步不能照搬。</div>
</div>

<section class="panel"><h2>一、论文讲了什么</h2>
<div class="fig">{d_mcil()}</div>
<h3>1. 最优交互理论（论文第 III-A 节）</h3>
<ul>
<li>来源：Bahrami 等 2010 年发表在 Science 上的"Optimally interacting minds"。论文引述其结论：能力相近的个体通过交流可以提高表现；同时也引用了该文的另一句话"群体很少胜过其最好的成员"。</li>
<li>心理测量曲线：每个分类器的准确率 P 随数据清晰度 Δc 上升，P(Δc) = H((Δc + b) / σ)，H 是累积高斯函数；σ 越小越敏感。敏感度 S = 1 / √(2πσ²)。</li>
<li>交互后的联合曲线：b<sub>joint</sub> = Σ w<sub>i</sub> b<sub>i</sub>，σ<sub>joint</sub><sup>2</sup> = Σ w<sub>i</sub><sup>2</sup> σ<sub>i</sub><sup>2</sup>，权重 w<sub>i</sub> 与 1/σ<sub>i</sub><sup>2</sup> 成正比（逆方差加权）；由此得到 S<sub>joint</sub> ≈ √(Σ S<sub>i</sub><sup>2</sup>) ≥ max S<sub>i</sub>。</li>
<li>我的理解：这个推导隐含"各成员的误差相互独立"。成员越相关，S<sub>joint</sub> 的提升越小。</li></ul>
<h3>2. MCIL 怎么做（论文第 III-C、III-D 节）</h3>
<ul>
<li><b>精确标签学习</b>：五个不同架构的网络（ResNet、DenseNet、SqueezeNet、VGG、AlexNet）在 D1 上用交叉熵训练。不同架构用来模拟"不同个体的不一致认知"。</li>
<li><b>构造模糊标签</b>：用训好的网络对无标签的 D2 投票，把投票比例当作每个样本的情绪分布，不需要人工标注。</li>
<li><b>交互学习</b>：每个网络在 D2 上用 KL 损失向模糊标签重训。</li>
<li><b>最终决策</b>：在 D3 上选最好的单个网络。论文原文写明这里用的是测试准确率作为衡量能力的标准。</li></ul>
<h3>3. 结果（论文表 III–XI 与图 4）</h3>
<table><tr><th>数据集</th><th>D1 / D2 / D3</th><th>MCIL（最好的单个网络）</th><th>多数投票</th><th>Fleiss κ 交互前 → 后</th></tr>
<tr><td>MAS（5 类）</td><td>6,000 / 13,400 / 1,000</td><td class="n">62.20%</td><td class="n">59.10%</td><td class="n">0.51 → 0.66</td></tr>
<tr><td>IEMOCAP（4 类）</td><td>1,710 / 3,421 / 400</td><td class="n">67.00%</td><td class="n">65.00%</td><td class="n">0.52 → 0.72</td></tr>
<tr><td>FAU-AIBO（2 类）</td><td>5,375 / 10,750 / 2,091</td><td class="n">65.47%</td><td class="n">62.20%</td><td class="n">0.36 → 0.61</td></tr></table>
<ul><li>5 个分类器最好；加到 7 个反而变差，论文解释为新增的两个本身较弱，拉低了群体能力。这与"能力相近"条件一致。</li>
<li>并非每个类别都变好：例如 MAS 上 DenseNet 的 sadness 从 66.0% 降到 59.0%，IEMOCAP 上的 happy 也下降。</li></ul>
</section>

<section class="panel"><h2>二、哪些能借鉴，哪些不能照搬</h2>
<table><tr><th>论文中的做法</th><th>我们这里的对应</th><th>备注</th></tr>
<tr><td>N 个不同架构的分类器</td><td>跨模型的九位专家：GPT / Gemini / Omni × 图谱 / 音频字幕 / 图像（可加 Direct、PPCT）</td><td>同模型三角色太相关（见第五节），必须跨模型</td></tr>
<tr><td>D1：有精确标签的训练集</td><td>train 清单的一半（160 条，有标签）</td><td>用于估计能力、权重、易混淆先验，以及门控</td></tr>
<tr><td>D2：无标签数据</td><td>train 清单的另一半（160 条，不看标签）</td><td>若服务器上还有未被筛选使用的 MER2024 / MELD 样本，可扩充 D2，需另外核实</td></tr>
<tr><td>D3：测试集</td><td>80 条验证集，最后只评估一次</td><td>符合项目约定：验证集不参与调参</td></tr>
<tr><td>模糊标签 = 投票比例</td><td>加权投票分布 Ỹ；候选集 C = 支撑集 ∪ 第 1 个易混淆标签</td><td>F1：k=1 覆盖率 GPT 75%→82.5%，Gemini 78.8%→83.8%</td></tr>
<tr><td>用 KL 损失重训网络权重</td><td>训练免费的状态更新：C1 案例记忆、C2 规则补丁、C3 输出校准</td><td>不改模型权重；C3 最接近 KL 重训</td></tr>
<tr><td>逆方差加权 w<sub>i</sub> ∝ 1/σ<sub>i</sub><sup>2</sup></td><td>按 D1 准确率加权，建议 w = log(acc / (1 − acc))</td><td>这是我建议的分类版对应，不是论文原式</td></tr>
<tr><td>用测试准确率选最好的网络</td><td><b>改为在 D1 上交叉验证选</b></td><td>不能照搬，否则等于在测试集上调参</td></tr>
<tr><td>Fleiss κ 上升作为效果之一</td><td>只作监控，停止条件看 D1 准确率</td><td>辩论实验里"一致但错"很多，κ 上升不代表变好</td></tr></table>
</section>

<section class="panel"><h2>三、方法设计</h2>
<div class="fig">{d_design()}</div>
<div class="fig">{d_state()}</div>
<h3>流程（伪代码）</h3><pre>{e(PSEUDO)}</pre>
<div class="note"><b>补充说明</b>：循环里"训练什么、怎么验证"的详细解释、图和算例见 <code>docs/self-evolving-training-explained.html</code>。要点：大模型全部冻结，只训练每位专家的校准偏置 b 和融合权重 w；若只做 C3 校准，伪代码里每轮的 run(m, x, …) 不需要重跑大模型，调用量粗估降到 5,000 到 6,000 次。</div>
<h3>为什么叫"自进化"</h3>
<ul><li>D2 上没有人工标签，成员靠"群体分布"互相学习，更新后的成员又产生新的群体分布，循环进行；这对应论文的"交互学习"。</li>
<li>有标签的 D1 只用于两件事：估计成员能力（权重、去掉弱成员）和门控（更新是否被接受、何时停止）。它不进入任何提示词。</li></ul>
<h3>三种状态更新的细节与风险</h3>
<table><tr><th>方式</th><th>做什么</th><th>主要风险</th></tr>
<tr><td>C1 案例记忆</td><td>为每位成员建 D2 案例库（样本简述、Ỹ、关键证据）；推理时检索相似案例，附在提示词里作参考</td><td>相似度怎么算需要选（字幕或组织文本的文本相似、或答案模式相似）；案例的 Ỹ 本身可能是错的</td></tr>
<tr><td>C2 规则补丁</td><td>统计成员与 Ỹ 的系统性偏离，让模型写 1 条短规则，例如"疑问句加皱眉不自动等于 worried"；只有在 D1 上不变差才保留</td><td>规则容易过拟合 D1；规则写进提示词需要做版本管理</td></tr>
<tr><td>C3 输出校准</td><td>让成员在候选集 C 上输出概率分布；用 Ỹ 拟合每位成员的标签偏置（每个标签一个参数），最小化 KL</td><td>LLM 自报的概率未必可靠；参数虽少，D2 只有 160 条</td></tr></table>
</section>

<section class="panel"><h2>四、已有数据给出的依据（只读已保存结果，80 条开发集，描述性）</h2>
<h3>F1：候选集"专家答案 ∪ 第 1 个易混淆标签"</h3>{candidate_table()}
<p class="muted small">覆盖率是上限，候选集里有真实标签不等于能选对；易混淆排序用留一法。详见 <code>docs/expert-union-confusable.html</code> 与 <code>metrics/findings_log.md</code>。</p>
<h3>F2：同模型角色 vs 跨模型成员</h3>{hetero_table()}
<ul>
<li><b>GPT、Gemini 的同模型三角色错误高度相关</b>：两两同时答错的比例约是独立假设下的 2.6 到 2.9 倍，而且多数是"同一个错答案"。最优交互理论的收益在这种情况下会很小，这也解释了条件辩论为什么没用。Omni 的三角色本身就比较分散（κ 0.66、并集 88.3%），但它单个成员也较弱。</li>
<li><b>跨模型成员更互补</b>：κ 更低、并集明显更高（GPT、Gemini 同模型三角色 75% 到 79%，跨模型约 86% 到 92%），"同一个错答案"的比例约减半。</li>
<li><b>成员能力相近</b>：九位专家单独答对 51 到 59 条，符合"能力相近"的条件。</li>
<li><b>但单靠投票还不够</b>：九位多数投票 61/77，并集 71/77；中间这 10 条正是需要"交互学习"去拿的空间。这只是描述，不是本方法的成绩。</li></ul>
</section>

<section class="panel"><h2>五、实验方案（建议）</h2>
<h3>数据划分</h3>
<ul><li>train 320 条（MER2024 160 + MELD 160）→ D1 160 条（有标签，两数据集各半）+ D2 160 条（不看标签）。</li>
<li>80 条验证集作为 D3，所有选择都在 D1 上做完之后只评估一次。</li></ul>
<h3>对照组</h3>
<table><tr><th>编号</th><th>做法</th><th>回答什么</th></tr>
<tr><td>B0</td><td>现状：v3 三专家 + 汇总器</td><td>基线</td></tr>
<tr><td>B1</td><td>同模型三专家多数投票</td><td>投票基线</td></tr>
<tr><td>B2</td><td>跨模型九位多数投票</td><td>异质成员本身带来多少</td></tr>
<tr><td>B3</td><td>九位加权投票（权重来自 D1）</td><td>"逆方差加权"带来多少</td></tr>
<tr><td>M1</td><td>B3 + 只在候选集 C 内投票</td><td>F1 候选集是否有用</td></tr>
<tr><td>M2 / M3 / M4</td><td>分别加入 C1 案例记忆 / C2 规则补丁 / C3 校准，迭代 1 轮</td><td>哪种状态更新有效</td></tr>
<tr><td>M*</td><td>最好的组合迭代 T 轮（T ≤ 3）</td><td>"自进化"多轮是否有收益</td></tr>
<tr><td>MCIL-style</td><td>D1 上选出的最好单个成员</td><td>对应论文的最终决策方式</td></tr></table>
<p><b>报告指标</b>：准确率、各标签召回、Fleiss κ、候选集覆盖率、每样本调用次数、相对 B2 的"由错变对 / 由对变错"翻转表。</p>
<h3>成本粗估（需要你授权才能跑）</h3>
<ul><li>train 320 条目前没有感知结果和 v3 专家输出，需要先在服务器上补跑：Gemini 固定图谱约 3 × 320 = 960 次；三个模型的组织文本加三位专家约 4 × 320 × 3 = 3,840 次。</li>
<li>自进化每轮在 D2 上重跑九位成员约 9 × 160 = 1,440 次，T = 2 时约 2,880 次；规则补丁的门控还要在 D1 上额外评估。</li>
<li>最终在 80 条上评估约 9 × 80 + 3 × 80 = 960 次。合计粗估 8,000 到 9,000 次调用。Omni 走服务器上的 vLLM，需要先确认服务状态与 GPU 是否空闲。</li></ul>
</section>

<section class="panel"><h2>六、风险与需要你决定的事</h2>
<ul>
<li><b>效果可能远小于论文</b>：论文改的是网络权重、D2 上万条；我们只改外部状态、D2 只有 160 条。</li>
<li><b>项目定位</b>：C1 到 C3 都不改模型权重，仍属于 training-free；但规则补丁会改提示词，需要作为新版本保存，不覆盖 v1 到 v3。</li>
<li><b>κ 不是目标</b>：论文把一致性提升当作成果之一；在我们的辩论实验里，一致后答错的样本很多，所以只把它当监控指标。</li>
<li><b>开发集复用</b>：80 条已被多次使用，即使只评估一次，也只能算开发集结果。</li></ul>
<div class="warn"><b>需要你决定：</b>① 是否授权在服务器上为 train 320 条补跑感知和三个模型的 v3 专家（约 4,800 次调用，含 Omni 的 vLLM 推理）；② 第一步先做哪种状态更新（我建议先做不改提示词、风险最低的 C3 输出校准，加上 B2、B3、M1 对照）。</div>
</section>
<p class="muted small" style="margin-top:20px">由 scripts/build_interactive_design.py 生成；静态页面，不依赖脚本，不调用模型。设计未实现、未运行。</p>'''
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>多专家交互自进化设计</title><style>{CSS}</style></head><body><main>{body}</main></body></html>'


def main():
    out = ROOT / 'docs' / 'self-evolving-interactive-design.html'
    out.write_text(build(), encoding='utf8')
    print(out, out.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
