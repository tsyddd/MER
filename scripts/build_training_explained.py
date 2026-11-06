"""Build docs/self-evolving-training-explained.html: what exactly is "trained" in the self-evolving design and how to
verify it. Contains (1) diagrams, (2) a fully computed toy example of C3 calibration (made-up numbers, clearly labelled),
(3) real per-label prediction bias of the saved v3 experts (motivation). No model calls.
Usage: python scripts/build_training_explained.py
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from build_debate_survey import CSS, arrow, box, e, lab, svg  # noqa: E402

V3 = ROOT / 'outputs' / 'gemini_graph_emotion_wheel_v3'
ROLES = ['graph', 'audio_subtitle', 'image']
ROWS = [json.loads(x) for x in (ROOT / 'data/manifests/validation.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
ORDER = {'MER2024': ['happy', 'angry', 'sad', 'worried', 'surprise', 'neutral'],
         'MELD': ['joy', 'anger', 'sadness', 'fear', 'disgust', 'surprise', 'neutral']}

# ------------------------------------------------------------------ toy calibration (made-up numbers)
L = ORDER['MER2024']
EPS = 0.01
TOY_D2 = {'x1': ([0, .15, 0, .60, .15, .10], [0, .40, 0, .45, .15, 0]),
          'x2': ([0, .40, 0, .45, .10, .05], [0, .55, 0, .30, .15, 0]),
          'x3': ([0, .05, .05, .50, .30, .10], [0, .10, 0, .35, .55, 0]),
          'x4': ([.70, 0, 0, .10, .05, .15], [.80, 0, 0, 0, 0, .20]),
          'x5': ([0, 0, .60, .30, 0, .10], [0, 0, .75, .15, 0, .10]),
          'x6': ([.05, 0, 0, .20, .05, .70], [0, 0, 0, .10, 0, .90])}
TOY_D1 = {'c1': ([0, .40, 0, .45, .10, .05], 'angry'), 'c2': ([0, .10, 0, .70, .10, .10], 'worried'),
          'c3': ([0, .05, 0, .45, .40, .10], 'surprise'), 'c4': ([.60, 0, 0, .10, 0, .30], 'happy'),
          'c5': ([0, .38, 0, .42, .10, .10], 'worried'), 'c6': ([0, 0, .55, .30, 0, .15], 'sad')}


def smooth(p):
    q = [max(x, EPS) for x in p]
    s = sum(q)
    return [x / s for x in q]


def softmax(z):
    m = max(z)
    ex = [math.exp(v - m) for v in z]
    s = sum(ex)
    return [v / s for v in ex]


def calib(p, b):
    return softmax([math.log(x) + bb for x, bb in zip(smooth(p), b)])


def kl(y, q):
    return sum(a * math.log(a / c) for a, c in zip(y, q) if a > 0)


def arg(p):
    return L[max(range(len(p)), key=lambda k: p[k])]


def fit_toy():
    b = [0.0] * 6
    hist = []
    for it in range(800):
        if it in (0, 50, 200, 799):
            hist.append((it, sum(kl(y, calib(p, b)) for p, y in TOY_D2.values()) / len(TOY_D2)))
        g = [0.0] * 6
        for p, y in TOY_D2.values():
            q = calib(p, b)
            for k in range(6):
                g[k] += (q[k] - y[k]) / len(TOY_D2)
        b = [bb - 0.5 * (gg + 0.02 * bb) for bb, gg in zip(b, g)]
        m = sum(b) / 6
        b = [v - m for v in b]
    return b, hist


def pct(v):
    return f'{100 * v:.0f}%'


def dist_cell(p):
    top = sorted(range(len(p)), key=lambda k: -p[k])[:3]
    return '，'.join(f'{L[k]} {pct(p[k])}' for k in top)


def toy_section():
    b, hist = fit_toy()
    loss0, loss1 = hist[0][1], hist[-1][1]
    btab = ''.join(f'<td class="n">{v:+.2f}</td>' for v in b)
    h = (f'<table><tr><th>标签</th>{"".join(f"<th>{l}</th>" for l in L)}</tr><tr><td>拟合出的偏置 b</td>{btab}</tr></table>'
         f'<p class="muted small">含义：这位成员相对群体<b>偏爱 worried</b>（b = {b[3]:+.2f}，压低），<b>低估 angry、surprise</b>（b = {b[1]:+.2f}、{b[4]:+.2f}，抬高）。校准后的分布 = softmax(log p + b)。</p>')
    h += ('<h3>训练过程：D2 上的平均 KL 损失（越小表示越贴近群体分布 Ỹ）</h3><table><tr><th>迭代步数</th>'
          + ''.join(f'<th>{it}</th>' for it, _ in hist) + '</tr><tr><td>平均 KL</td>' + ''.join(f'<td class="n">{v:.3f}</td>' for _, v in hist) + '</tr></table>')
    h += '<h3>D2 上（没有标签）：校准前后，这位成员的判断</h3><table><tr><th>样本</th><th>校准前（前三）</th><th>前 → 后</th><th>校准后（前三）</th><th>群体 Ỹ 的最大项</th></tr>'
    for k, (p, y) in TOY_D2.items():
        q = calib(p, b)
        a0, a1 = arg(smooth(p)), arg(q)
        h += (f'<tr class="{"differ" if a0 != a1 else ""}"><td>{k}</td><td>{dist_cell(smooth(p))}</td><td><b>{a0} → {a1}</b></td><td>{dist_cell(q)}</td><td>{arg(y)}</td></tr>')
    h += '</table>'
    h += '<h3>D1 留出部分（有标签）：门控用的验证</h3><table><tr><th>样本</th><th>真实标签</th><th>校准前</th><th>校准后</th><th>结果</th></tr>'
    a0n = a1n = 0
    for k, (p, g) in TOY_D1.items():
        q = calib(p, b)
        a0, a1 = arg(smooth(p)), arg(q)
        a0n += a0 == g
        a1n += a1 == g
        res = '改对' if (a0 != g and a1 == g) else '改错' if (a0 == g and a1 != g) else ('仍对' if a1 == g else '仍错')
        cls = 'ok' if res in ('改对', '仍对') else 'bad'
        h += f'<tr><td>{k}</td><td>{g}</td><td><span class="l {"ok" if a0 == g else "bad"}">{a0}</span></td><td><span class="l {"ok" if a1 == g else "bad"}">{a1}</span></td><td><span class="tag {cls}">{res}</span></td></tr>'
    h += f'</table><p><b>门控结论</b>：校准前 {a0n}/6，校准后 {a1n}/6，没有变差 → 接受这次更新。注意其中有 1 条（c5）被改错，所以验证必须看净变化和翻转明细，不能只看拟合损失下降。</p>'
    return h, loss0, loss1, a0n, a1n


# ------------------------------------------------------------------ real bias (motivation)
def real_bias():
    gold = {r['id']: r['label'] for r in ROWS}
    ds = {r['id']: r['dataset'] for r in ROWS}
    h = '<table><tr><th>模型</th><th>数据集</th><th>标签</th><th>真实条数 × 3 位专家</th><th>三位专家实际预测次数</th><th>偏差</th></tr>'
    focus = {('MER2024', 'worried'), ('MER2024', 'angry'), ('MER2024', 'neutral'), ('MELD', 'neutral'), ('MELD', 'anger'), ('MELD', 'disgust'), ('MELD', 'fear')}
    for prov in ('gpt', 'gemini'):
        cnt = Counter()
        for i in gold:
            for r in ROLES:
                a = (json.loads((V3 / prov / i / f'expert_{r}.json').read_text(encoding='utf8')) or {}).get('answer')
                cnt[(ds[i], a)] += 1
        gcnt = Counter((ds[i], g) for i, g in gold.items())
        for d, l in sorted(focus):
            exp, got = gcnt[(d, l)] * 3, cnt[(d, l)]
            diff = got - exp
            h += f'<tr><td>{prov.upper()}</td><td>{d}</td><td>{l}</td><td class="n">{exp}</td><td class="n">{got}</td><td class="n"><b>{diff:+d}</b></td></tr>'
    return h + '</table>'


# ------------------------------------------------------------------ diagrams
def d_what():
    b = lab(20, 22, '图 1　被"训练"的是什么：大模型冻结，只训练外面两层很小的参数', 'start', 'l b')
    b += box(20, 120, 120, 70, ['一个样本', '8 帧 + 字幕', '（+ 音轨、图谱）'], 'plain')
    ys = [45, 120, 195]
    names = ['GPT · 三位专家', 'Gemini · 三位专家', 'Omni · 三位专家']
    for y, n in zip(ys, names):
        b += box(190, y, 190, 60, [n, '冻结，不训练'], 'exist') + arrow([(140, 155), (190, y + 30)])
        b += box(430, y, 190, 60, ['输出分布 p（每位专家）', '例：worried 45%，angry 40%'], 'plain') + arrow([(380, y + 30), (430, y + 30)])
        b += box(670, y, 150, 60, ['校准偏置 b', '每位 6 或 7 个数'], 'new') + arrow([(620, y + 30), (670, y + 30)])
        b += arrow([(820, y + 30), (865, 155)])
    b += box(865, 115, 160, 80, ['融合权重 w', '9 个数', '→ 最终标签'], 'new')
    b += lab(670, 278, '橙色 = 要训练的参数：b 用 D2 上的群体分布 Ỹ 拟合（无标签），w 用 D1 的标签算', 'middle')
    b += lab(670, 300, '另有两种不是参数的"状态"：案例记忆（检索库）、规则补丁（一段文字），可选', 'middle')
    return svg(1040, 315, b, '被训练的部分')


def d_loop():
    b = lab(20, 22, '图 2　一轮"自进化"训练：只用 D2 上的群体分布，不看标签', 'start', 'l b')
    b += box(20, 60, 170, 80, ['① 九位专家在 D2 上', '各输出分布 p', '（只需跑一次大模型）'], 'exist')
    b += box(240, 60, 190, 80, ['② 群体分布', 'Ỹ = Σ w · 校准后的 p', '（模糊标签）'], 'new') + arrow([(190, 100), (240, 100)])
    b += box(480, 60, 210, 80, ['③ 拟合每位专家的 b', '最小化 KL(Ỹ ‖ softmax(log p + b))', '→ 训练损失下降'], 'new') + arrow([(430, 100), (480, 100)])
    b += box(740, 60, 280, 80, ['④ 门控（D1 留出部分，有标签）', '准确率不变差 → 接受新的 b', '变差 → 丢弃，保留旧的 b'], 'judge') + arrow([(690, 100), (740, 100)])
    b += arrow([(880, 140), (880, 175), (335, 175), (335, 140)], dashed=True) + lab(600, 195, '接受后用新的 b 重算 Ỹ，再拟合（最多 T = 3 轮；D1 上不再提升就停）', 'middle')
    b += lab(20, 228, '要点：校准只是在已有输出上做加权，第 ① 步的大模型调用只需一次，后面的迭代都在本地计算，几乎零成本。', 'start')
    return svg(1040, 245, b, '一轮训练')


def d_split():
    b = lab(20, 22, '图 3　数据怎么分：哪些数据用来训练，哪些用来验证', 'start', 'l b')
    segs = [('D1-fit · 80 条', '有标签：算权重 w、易混淆先验', 'plain', 250), ('D1-check · 80 条', '有标签：门控、停止、选方案', 'judge', 250),
            ('D2 · 160 条', '不看标签：构造 Ỹ、拟合 b', 'new', 500)]
    x = 20
    for t, s, cls, w in segs:
        b += box(x, 50, w - 10, 70, [t, s], cls)
        x += w
    b += lab(20, 145, '上面三块都来自 train 清单的 320 条（MER2024 160 + MELD 160）；目前这 320 条还没有感知和专家输出，需要先在服务器补跑。', 'start')
    b += box(20, 165, 1000, 60, ['D3 · 80 条验证集：所有选择都做完以后，只评估一次，和投票等基线比较'], 'exist')
    return svg(1040, 240, b, '数据划分')


def d_verify():
    b = lab(20, 22, '图 4　三层验证：每层回答不同的问题', 'start', 'l b')
    rows = [('第 1 层 · 拟合', 'D2（无标签）', '平均 KL(Ỹ ‖ p\') 是否下降', '训练是否收敛、有没有贴近群体分布', 'new'),
            ('第 2 层 · 门控与停止', 'D1-check（有标签）', '准确率、各标签召回、翻转明细', '学到的东西能否推广到真实标签', 'judge'),
            ('第 3 层 · 最终评估', 'D3 = 80 条（只一次）', '准确率、相对投票的翻转表、McNemar 检验', '方法是否真的比投票 / 现状好', 'exist')]
    for k, (t, d, m, q, cls) in enumerate(rows):
        y = 45 + k * 85
        b += box(20, y, 210, 70, [t], cls) + box(250, y, 200, 70, ['用什么数据', d], 'plain')
        b += box(470, y, 270, 70, ['看什么指标', m], 'plain') + box(760, y, 260, 70, ['回答什么问题', q], 'plain')
    b += lab(20, 310, '只看第 1 层会误判：损失下降只说明"更像群体"，群体本身可能错（尤其是所有专家共有的偏差）。', 'start')
    return svg(1040, 325, b, '三层验证')


def build():
    toy, loss0, loss1, a0n, a1n = toy_section()
    body = f'''<div class="eyebrow">DESIGN · WHAT IS TRAINED AND HOW TO VERIFY</div>
<h1>自进化循环里，到底训练什么？怎么判断训练得好不好？</h1>
<p class="muted">针对 <code>docs/self-evolving-interactive-design.html</code> 里的伪代码。本页是设计说明：图 1 到图 4 是示意图；第三节的例子是<b>人为构造的示意数字</b>（由本页的生成脚本实际计算，保证前后一致），不是实验结果；第四节是从已保存结果统计的真实数据。</p>

<div class="tldr">
<div class="tl k"><b>① 训练的不是大模型</b>GPT、Gemini、Omni 全部冻结。被训练的是两组很小的参数：每位专家的<b>校准偏置 b</b>（每个标签一个数，MER 6 个、MELD 7 个），以及九位专家的<b>融合权重 w</b>（9 个数）。案例记忆和规则补丁不是参数，是可选的"状态"。</div>
<div class="tl k"><b>② b 怎么训练</b>在 D2 上，让每位专家校准后的输出分布贴近群体分布 Ỹ，最小化 KL 散度。这一步不用任何标签，对应论文"用 KL 损失向模糊标签重训"。大模型只需要跑一次，迭代全在本地。</div>
<div class="tl w"><b>③ 怎么判断好坏：三层</b>拟合（D2 上 KL 是否下降）→ 门控（D1 留出部分的准确率是否不变差）→ 最终（80 条只评估一次，和投票比）。只看第一层会误判。</div>
<div class="tl w"><b>④ 一个关键限制</b>向群体分布校准只能修正"某位专家和群体不一致"的偏差；如果<b>所有专家共有</b>同一个偏差（例如都偏爱 worried），群体分布本身就带着这个偏差，校准修不了。这时需要用 D1 的标签直接校准（变体 C3b）。</div>
</div>

<section class="panel"><h2>一、训练什么</h2><div class="fig">{d_what()}</div>
<table><tr><th>要训练的东西</th><th>是什么</th><th>参数量</th><th>用什么数据训练</th><th>训练目标</th></tr>
<tr><td><b>校准偏置 b（C3）</b></td><td>对每位专家的输出分布做 softmax(log p + b)，b 是每个标签一个加性偏置</td><td>每位专家 6 个（MER）+ 7 个（MELD）；九位共 117 个</td><td>D2（160 条，不看标签）</td><td>最小化 KL(Ỹ ‖ 校准后的 p)，即贴近群体分布</td></tr>
<tr><td><b>变体：有监督校准 b（C3b）</b></td><td>同上</td><td>同上</td><td>D1-fit（80 条，有标签）</td><td>最小化交叉熵（贴近真实标签）；能修正所有专家共有的偏差，但已不是 MCIL 的"无标签交互"</td></tr>
<tr><td><b>融合权重 w</b></td><td>每位专家的投票权重，建议 w = log(acc / (1 − acc))</td><td>9 个</td><td>D1-fit（有标签）</td><td>按能力加权（逆方差加权的分类版）</td></tr>
<tr><td>案例记忆（C1，可选）</td><td>检索库：D2 样本简述 + Ỹ + 关键证据</td><td>非参数</td><td>D2</td><td>推理时作为参考案例，需要重跑大模型</td></tr>
<tr><td>规则补丁（C2，可选）</td><td>写进提示词的一两条短规则</td><td>一段文字</td><td>D2 上与 Ỹ 的系统性偏离</td><td>需要重跑大模型；门控决定保留与否</td></tr></table>
<p><b>前提</b>：专家要输出<b>概率分布</b>，而不是只给一个标签。现有的 v3 专家只输出单标签，所以需要一个新版本的专家提示词，让它在候选标签上给出分布（或者使用接口提供的概率信息，这一点需要先核实接口是否支持）。</p></section>

<section class="panel"><h2>二、怎么训练、怎么分数据</h2><div class="fig">{d_loop()}</div><div class="fig">{d_split()}</div>
<h3>修正后的伪代码（以 C3 为例，把"训练什么"写明）</h3><pre>{e(PSEUDO)}</pre>
<p class="muted small">与设计页上一版的区别：上一版每轮都"run(m, x, state[m])"重跑大模型；对 C3 校准来说不需要，大模型输出只取一次。因此只做 C3 时，调用量约为：train 320 条补跑感知与专家 + 80 条验证集各一次，粗估 5,000 到 6,000 次，而不是 8,000 到 9,000 次。</p></section>

<section class="panel"><h2>三、例子（示意数字，不是实验结果）</h2>
<p>假设"Gemini · 图像专家"在 D2 的 6 条样本上给出下面的分布，群体分布 Ỹ 来自九位专家的加权投票。用 b 拟合后：</p>{toy}
<div class="note">这个例子说明三件事：① 训练损失下降（{loss0:.3f} → {loss1:.3f}）只代表这位专家更像群体；② 真正的检验在有标签的 D1-check 上，这里净提升 1 条（{a0n}/6 → {a1n}/6），但有 1 条被改错；③ 这位专家在 x1 上仍判 worried，因为群体分布本身也是 worried 略高，校准不会超越群体。</div></section>

<section class="panel"><h2>四、在真实数据里，校准要修的偏差长什么样（已保存的 v3 专家，80 条）</h2>
{real_bias()}
<p class="muted small">"真实条数 × 3"是三位专家都答对时该标签应出现的次数。正数 = 预测过多，负数 = 预测过少。</p>
<ul>
<li>MER 的 worried 被两个模型同时大量多判（GPT +14、Gemini +15）；MELD 上 GPT 多判 anger（+19），Gemini 多判 neutral（+20）；两个模型都少判 disgust、fear。这些正是校准偏置 b 能动的地方。</li>
<li>两个模型的偏差方向不完全相同（MELD 上一个偏 anger、一个偏 neutral），这正是跨模型群体分布能部分抵消的部分。</li>
<li>但这些偏差是<b>多位专家共有的</b>，群体分布 Ỹ 里同样存在。所以仅靠 MCIL 式的"向群体校准"（C3）效果可能有限，需要和有监督校准（C3b）对比，并且只在 D1-check 上决定用哪个。</li></ul></section>

<section class="panel"><h2>五、怎么判断"训练得好"：具体的验收标准（建议）</h2>
<table><tr><th>层次</th><th>数据</th><th>指标</th><th>合格标准（建议）</th><th>不合格时怎么办</th></tr>
<tr><td>第 1 层 · 拟合</td><td>D2</td><td>平均 KL 损失；Fleiss κ 只作监控</td><td>损失下降并趋于平稳</td><td>检查专家是否真的输出了分布、学习率是否过大</td></tr>
<tr><td>第 2 层 · 门控</td><td>D1-check（80 条，或 D1 的 5 折交叉验证）</td><td>准确率、各标签召回、改对 / 改错条数</td><td>准确率不下降，且改对多于改错；因为 1 条 = 1.25 个百分点，建议要求至少多对 2 条才算"提升"</td><td>拒绝本次更新；若连续拒绝就停止迭代</td></tr>
<tr><td>第 3 层 · 最终</td><td>D3（80 条验证集，只一次）</td><td>准确率；相对九位多数投票（B2）的翻转表；McNemar 检验；各标签召回</td><td>高于 B2 与现状汇总器；报告 p 值，样本小时如实说明不显著</td><td>不再回头调参，记录为负结果</td></tr></table>
<div class="warn">两条纪律：① 80 条验证集不参与任何选择，只在最后看一次；② 所有提示词里都不出现真实标签，标签只在计算准确率和门控时使用。</div></section>
<p class="muted small" style="margin-top:20px">由 scripts/build_training_explained.py 生成；静态页面，不依赖脚本，不调用模型。设计未实现、未运行。</p>'''
    extra = ('.tag.ok{background:#e3f3ea;color:#0d5a4a}.tag.bad{background:#fbe4de;color:#8b3524}'
             '.l{font:12.5px Consolas,monospace;padding:0 5px;border-radius:4px}.l.ok{background:#e3f3ea}.l.bad{background:#fbe4de}'
             'tr.differ td{background:#fff8e9}.note{padding:10px 14px;border-left:3px solid #137a68;background:#eef7f1;font-size:14px;margin:12px 0}'
             'td.n{text-align:right;font-family:Consolas,monospace}')
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>自进化：训练什么、怎么验证</title><style>{CSS}{extra}</style></head><body><main>{body}</main></body></html>'


PSEUDO = '''# 只跑一次大模型：九位专家在 D1-fit、D1-check、D2、D3 上各输出一个分布 p[m][x]
w = {m: log(acc(m, D1_fit) / (1 - acc(m, D1_fit))) for m in members}      # 训练 1：融合权重（有标签）
b = {m: zeros(K) for m in members}                                        # 训练 2：校准偏置（初始为 0）

for t in 1..T:                                                            # 自进化（不看 D2 标签）
    Ỹ = {x: normalize(Σ_m w[m] · softmax(log p[m][x] + b[m])) for x in D2}  # 群体分布
    for m in members:
        b_new = argmin_b  mean_x KL(Ỹ[x] ‖ softmax(log p[m][x] + b))        # 拟合（第 1 层验证：看这个损失）
        if acc(m, D1_check, b_new) >= acc(m, D1_check, b[m]):             # 门控（第 2 层验证）
            b[m] = b_new
    if group_acc(D1_check) 没有提升: break

final(x) = argmax Σ_m w[m] · softmax(log p[m][x] + b[m])                  # 在 D3（80 条）上只评估一次（第 3 层验证）'''


def main():
    out = ROOT / 'docs' / 'self-evolving-training-explained.html'
    out.write_text(build(), encoding='utf8')
    print(out, out.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
