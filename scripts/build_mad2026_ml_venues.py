"""Build docs/mad-2026-ml-venues.html: NeurIPS / ICML / CVPR 2026 papers relevant to the PPCT disagreement-branch problem,
with source-code verification (gh api read-only checks, 2026-11-03).

Reads metrics/mad2026_ml_venues_checks.json. No model calls, no network. Usage: python scripts/build_mad2026_ml_venues.py
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / 'metrics/mad2026_ml_venues_checks.json').read_text(encoding='utf8'))
CHK, PAPERS = D['repos'], D['papers']


def e(s):
    return escape(str(s), quote=True)


def paper(sub):
    for p in PAPERS:
        if sub.lower() in p['title'].lower():
            return p
    raise KeyError(sub)


def repo_cell(key):
    r = CHK.get(key)
    if not r or not r.get('ok'):
        return '<span class="m">无</span>'
    lic = r.get('license') or '无许可证'
    return (f'<a href="https://github.com/{e(r["slug"])}">{e(r["slug"])}</a><br>'
            f'<span class="m">★{r["stars"]} · 更新 {r["pushed"]} · 源码文件 {r["n_code_files"]} · {e(lic)}</span>')


# (title-substring, repo-key, short title, what it says, what we can borrow, caveat)
G = [
    ('A', '诊断与度量：用我们已保存的日志就能算（对应 F3–F6）', [
        ('When Debate Helps', 'nips.when-debate-helps', 'When Debate Helps：提议供给与带验证的读出',
         '辩论要胜过多数投票需要两个条件：候选里确有正确的少数答案（供给），并且有验证证据能把它捞出来（读出）。用“潜在余量”（多数投票与“提议全知”之间的差距）衡量没被用上的正确答案。',
         '“提议命中 / 可恢复余量 / 恢复 / 损伤”这套指标可以在我们 v4 记录上事后计算，先量出不一致分支的上限（F6 里 Direct 的答案有 60/62、53/55 落在候选内，说明供给通常有）。',
         '论文构造“专家社会”的方法是对开源模型权重加高斯扰动，不适用 GPT / Gemini API；任务是文本推理。Apache-2.0。'),
        ('Measuring Collapse and Correction', 'nips.debateledger', 'DebateLedger：辩论的“转移账本”',
         '按“初始多数 / 最终多数是否正确”把每场辩论记为保持、坍缩（多数从对变错）、纠正（从错变对）、未修复，并记录首次破坏正确多数的轮次。在 6,925 场 MMLU-Pro 辩论里记录了 253 次坍缩。',
         '可直接套在 v4 的 Round 0 / 反思 / 辩论记录上，和 F5 已有的统计对齐口径。',
         '同质 panel（同一模型三份）+ 多选题；我们是三位异构专家（同一底座），口径需要调整。NeurIPS Evaluations & Datasets Track，MIT。'),
        ('Systematic Failures in Collective Reasoning', 'icml.hiddenbench', 'HiddenBench：信息分散时的集体推理',
         '65 个任务隔离“信息分散在各 agent 手里”的情形：多 agent 准确率只有 30.1%，单 agent 看到全部信息有 80.7%。原因是 agent 不会推断“别人可能知道、但还没说”的信息，过早收敛到共享信息；一个轻量的结构化沟通协议能明显改善。',
         '我们的三位专家各看不同模态，正是“信息分散”。可借“先说明各自独有的线索”的沟通协议来设计辩论提示。',
         '基准是文本的 Hidden Profile 任务，不是感知任务。MIT。'),
    ]),
    ('B', '不确定性与路由信号（何时辩论 / 何时升级）', [
        ('Sequential Probabilistic Uncertainty Estimation', 'nips.sauce', 'SAUCE：并行多 agent 的序贯不确定性估计',
         '免训练。每轮用“一致度”（众数答案数 / 初始人数）和“平均 token 熵”更新系统层信念，得到整条轨迹的不确定性分数。',
         '可作为“要不要升级到辩论或人工”的路由信号，和“恰好 1 个共同标签”的规则互补。',
         '需要每轮的 token 熵，我们保存的 API 输出里不一定有 logprobs；分数是排序信号，不是错误概率。MIT。'),
        ('UMAS', 'nips.umas', 'UMAS：多 agent 系统的系统级不确定性',
         '无参数、成本中性：用每次生成的内在置信度估计 agent 之间影响的可信度，逐节点更新不确定性再汇总；用 AUROC 衡量能否预测最终答案对错。',
         '同样可作路由 / 弃权信号。',
         '输入需要各节点的 token log-prob 和“谁读了谁”的图；仓库只有 2 个源码文件（算法本身很短）。MIT。'),
        ('Learning When to Collaborate', 'nips.smart-med', 'SMART-Med：学习“何时协作”',
         '把协作当作可学习的决定：多数问题单个 agent 就够，只有不确定的才召集专家 agent；用 GRPO 微调本地 agent。多模态医学 VQA 上推理时间减少 3.8 倍以上、token 减少 72%。',
         '“并非每个样本都值得多 agent”与我们“一致则直接输出”的路由同一思路。',
         '需要训练和本地模型，与训练免费约束冲突；无许可证。'),
    ]),
    ('C', '过程验证到底靠不靠谱（回应对 AgentAuditor 的疑问）', [
        ('MAS-ProVe', 'icml.mas-prove', 'MAS-ProVe：多 agent 系统里的过程验证',
         '在 6 种多 agent 框架上系统比较过程验证（LLM-as-a-Judge、奖励模型、过程奖励模型；agent 级与迭代级）：过程级验证并不稳定地提升效果，方差很高；LLM-as-a-Judge 一般好于奖励模型；评价“部分轨迹”本身就很难。',
         '为“不要在中间步骤上做仲裁”提供外部证据，支持我们对节点聚合的怀疑。',
         '推理类基准，不是情绪任务；源码文件很多（520 个），无许可证。'),
    ]),
    ('D', '情绪任务本身', [
        ('Omni-Perception Policy Optimization', 'icml.oppo', 'OPPO：多模态情绪推理的全模态感知优化',
         '发现情绪 Omni-MLLM 的感知不足：推理里没充分用多模态线索，且不忠实——常把一种模态的陈述幻觉成另一种模态的。用 RL 优化，并提供 MEP-Bench 诊断“利用度与忠实度”。',
         'MEP-Bench 的诊断思路可用来审查我们专家的“证据是否忠实于对应模态”。',
         '训练部分基于 Qwen2.5-Omni，需要 GPU；与免训练约束冲突。Apache-2.0。'),
        ('AffectGPT-RL', 'nips.affectgpt-rl', 'AffectGPT-RL：开放词汇情绪识别的强化学习',
         '用 RL 优化开放词汇多模态情绪识别（OV-MER，用情绪轮计算指标），在 MER-UniBench 上达到 SOTA；并分析推理过程与奖励设计的作用。',
         '情绪轮式的评价与我们“开放情绪 → 标签映射”相关；仓库含 MER 系列数据的 CSV。',
         '训练型；代码在 zeroQiaoba/AffectGPT 的 AffectGPT-RL 子目录，仓库很大（852 个源码文件）；无许可证。'),
        ('Nano-EmoX', 'cvpr.nano-emox', 'Nano-EmoX：从感知到共情的紧凑情绪模型',
         '2.2B 的紧凑情绪 MLLM，一个模型覆盖情感分析、情绪识别、开放词汇情绪识别、意图识别、情绪原因推断、共情回复；官方仓库带训练、评测脚本和权重。',
         '一种思路（我的建议，未验证）：把它当作一位“误差来源不同”的专用专家加入投票——F2 显示跨模型专家比同模型角色更互补。',
         '训练型模型，不是免训练方法；MIT。'),
    ]),
]

MINOR = [
    ('Hearing is Believing', 'nips.syaudio', 'SYAUDIO（NeurIPS）', '评测音频语言模型的谄媚：面对误导性反馈时是否放弃声学证据；与“专家被同伴说法带偏”相关，但是单模型基准。'),
    ('CARE: Class-Adaptive', 'icml.care', 'CARE（ICML）', '长尾 + 噪声标签下对尾部类要求更严格的专家一致，对头部类更宽松；与稀有类问题有关，但是需要训练的视觉语言方法。'),
    ('Beyond Correctness: Distance-Based', 'icml.social-dynamics', 'Distance-Based Social Dynamics（ICML）', '分析 agent 的改答案概率如何依赖与真值的距离；仓库只有 3 个源码文件。'),
    ('Emergence of Biased Consensus', 'icml.biased-consensus2', 'Emergence of Biased Consensus（ICML）', '用物理启发的社会动力学模型解释辩论里偏见共识的出现：从众超过临界阈值时出现相变，采样温度是关键驱动。偏见 / 公平方面的分析。【2026-11-03 更正：此前误写成“只有前作代码”，其实有本文代码（phys-ai/llm-biased-consensus）。】'),
]

NOCODE = [
    ('ADEPT（ICML 2026）', '最贴近我们的思路：把情绪识别改成多轮“提问”，维护演化的候选集，调用语义与声学探测工具，经“候选生成 → 证据收集 → 裁决”；把少数标注当作有信息的信号而非噪声；用 GRPO 训练。arXiv 2602.12714；论文与 arXiv 里没有代码链接，GitHub 未找到。'),
    ('Cross-Channel Agreement Beats Consensus（NeurIPS 2026）', '指出所有候选看同一张图，感知偏差造成相关错误、一致但错的共识；用“两条误差来源不同的通道（神经 / 符号）的一致”来门控共识，几何基准上比多数投票高 10.4 个百分点。和我们“同模型三专家”的处境几乎一样，但没找到代码。'),
    ('Efficient Multi-Agent Reasoning via Confidence-Guided Adaptive Debate / LASE（ICML）', '只在“非中性”的情形才触发辩论，采用领导者—支持者的非对称结构。arXiv 2610.16343；没有代码链接。'),
    ('AIM（NeurIPS）/ DEAR（NeurIPS）', 'AIM：多模态辩论里按样本自适应选择交互方式（文字、图、感兴趣区域）；DEAR：调节“相互引用关系”来缓解盲目从众。均未找到代码。'),
    ('Beyond Majority Voting: Higher-Order Information（ICML）', '用一阶、二阶信息设计 OW 与 ISP 两种聚合，考虑模型间的异质性与相关性。arXiv 2510.01499，没有代码链接。'),
    ('When and Why Does Multi-Agent Debate Fail（NeurIPS）/ HetMedAgent（ICML）', '分别是：对辩论激励结构的理论分析；异构专家 + 冲突感知证据融合。均没有可验证的代码。'),
    ('EMO-R3 / Consensus Entropy（CVPR）、SR-TTRL / L2-VMAS（ICML）', '论文里给了仓库链接，但 GitHub 返回 404（xiaomi-research/emo-r3、Aslanyulong/consensus-entropy、JIA-Lab-research/SR-TTRL、YU-deep/L2-VMAS）。【2026-11-03 补：Consensus Entropy 此前漏了链接，现已确认是 404。】'),
    ('The Value of Variance（ICML）', '只有匿名评审镜像 anonymous.4open.science/r/UDPO-5BE2，本次访问没有成功，未核验。需要训练。'),
    ('World-Model Inspired Emotion-aware Token Refinement（ICML）', '免训练的多模态情绪识别，题目最贴近。但从摘要看是对模型内部 token 做精炼，估计需要开源模型的内部访问（我的推断），也没找到代码。'),
    ('EmoThinker（CVPR）及其他', 'EmoThinker 论文里没有代码链接；Belief Engine、MaRiO、Rethinking Parallel MAS、SCG-HF、A Diagnostic Study、Humans Correct Their Judgements、Debate with Images、Iterative Critique-and-Routing 均未找到代码。'),
]

PROB = [
    ('P1', '同模型三位专家的错误高度相关', 'HiddenBench（信息分散）、Cross-Channel Agreement（无代码）', 'F2：同模型三角色“同时答错”23–26%'),
    ('P2', '辩论重说服不重对错', 'DebateLedger（坍缩 / 纠正账本）、DEAR（无代码）', 'F5：少数派改投多数 13/13，答对的少数派被说服 4/4'),
    ('P3', '不一致分支≈在候选里随机选', 'When Debate Helps（余量）、SAUCE / UMAS（路由信号）、MAS-ProVe（过程验证不稳）', 'F6：辩论分支 v4 答对 26/62、19/55，Direct 38、26'),
    ('P4', '情绪证据是否忠实于对应模态', 'OPPO / MEP-Bench（利用度与忠实度）', 'F5：adopted_evidence 前后不一致'),
    ('P5', '标签有歧义、稀有类漏判', 'ADEPT（无代码）、AffectGPT-RL（情绪轮评价）、CARE', 'F5：辩论后答错的标签以 worried / neutral / surprise 为主'),
]

CSS = """:root{--ink:#172c38;--muted:#607583;--paper:#f4f6f3;--line:#dce4de;--green:#137a68;--amber:#b47c20;--red:#c9533c}*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1240px;margin:auto;padding:34px 28px 70px}
.eyebrow{font-size:12px;color:var(--green);font-weight:700;letter-spacing:2px}h1{font-size:30px;margin:8px 0 6px;line-height:1.3}h2{font-size:21px;margin:0 0 8px}
.muted{color:var(--muted)}.small{font-size:12.5px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 26px;margin-top:20px}
a{color:var(--green)}code{font:12.5px Consolas,monospace;background:#f1f5f1;padding:1px 5px;border-radius:4px}
.tldr{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}.tl{border:1px solid var(--line);border-radius:12px;padding:14px 18px;background:#fff}.tl>b:first-child{display:block;margin-bottom:4px}
.tl.w{border-left:4px solid var(--amber)}.tl.k{border-left:4px solid var(--green)}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:9px 10px;border-bottom:1px solid #edf1ed;text-align:left;vertical-align:top}th{color:var(--muted);font-size:12px;font-weight:600}
.m{color:var(--muted);font-size:12px}.grp td{background:#eef2ef;font-weight:700}.warn{margin-top:14px;padding:10px 14px;border-left:3px solid var(--amber);background:#fff8e9;font-size:13.5px}
.tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:12px;background:#edf3f0;color:var(--green);white-space:nowrap}
ul,ol{padding-left:22px}li{margin:5px 0}
@media(max-width:900px){.tldr{grid-template-columns:1fr}main{padding:20px 14px}.panel{padding:16px}}"""


def venue_tag(p):
    return f'<span class="tag">{e(p["venue"])}</span>'


def build():
    n_code = sum(len(i) for _, _, i in G)
    h = [f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NeurIPS / ICML / CVPR 2026：多 agent 辩论与相关方法（含源码）</title><style>{CSS}</style></head><body><main>']
    h.append('<div class="eyebrow">LITERATURE / NEURIPS · ICML · CVPR 2026</div><h1>NeurIPS / ICML / CVPR 2026：与我们不一致分支问题相关的方法（只收有源码的）</h1>')
    h.append('<p class="muted">检索于 2026-11-03，只读论文页面与公开仓库，未运行任何论文代码，未调用被测模型。与 <a href="mad-2026-papers.html">ACL / EMNLP 论文清单</a>、<a href="mad-2026-frameworks.html">五篇框架图</a> 配套。</p>')
    h.append('<div class="tldr">'
             '<div class="tl k"><b>① 检索范围</b>三个会议网站的论文列表共约 1.98 万条（CVPR 4,042、ICML 6,628、NeurIPS 9,130；列表未区分赛道与研讨会）。按标题关键词筛出 658 篇候选，读了其中 42 篇的摘要，再核验代码。</div>'
             f'<div class="tl k"><b>② 有源码且值得看的 {n_code + 0} 篇</b>分四组：诊断与度量、不确定性路由、过程验证、情绪任务；另有 3 篇关联较弱的。最直接可用的是 DebateLedger 和 When Debate Helps 的指标，它们能在已保存的日志上零成本计算。</div>'
             '<div class="tl w"><b>③ 一个重要的外部证据</b>ICML 的 MAS-ProVe 系统比较发现：多 agent 系统里的“过程级验证”并不稳定提升效果，方差很高。这支持我们对 AgentAuditor 式节点聚合的怀疑。</div>'
             '<div class="tl w"><b>④ 思路最贴近、但没有可用代码</b>ADEPT（候选集 + 证据探测 + 裁决，处理情绪歧义）和 Cross-Channel Agreement（所有候选看同一输入造成相关错误）。第三节列出了所有没找到代码的论文和原因。</div></div>')
    h.append('<section class="panel"><h2>一、我们的问题与这批文献的对应</h2><table><tr><th></th><th>问题</th><th>最相关的文献</th><th>我们的证据（findings_log）</th></tr>')
    for a, b, c, d in PROB:
        h.append(f'<tr><td><b>{a}</b></td><td>{e(b)}</td><td>{e(c)}</td><td>{e(d)}</td></tr>')
    h.append('</table></section>')
    h.append('<section class="panel"><h2>二、推荐清单（有源码）</h2><p class="muted small">仓库列：星标 · 最近更新 · 源码文件数 · 许可证；2026-11-03 的 GitHub 快照；星标只反映热度。</p>')
    h.append('<table><tr><th style="width:22%">论文</th><th style="width:26%">它说了什么</th><th style="width:21%">我们能借用什么</th><th style="width:15%">注意</th><th style="width:16%">仓库</th></tr>')
    for gid, gname, items in G:
        h.append(f'<tr class="grp"><td colspan="5">{gid}　{e(gname)}</td></tr>')
        for sub, key, title, what, borrow, cav in items:
            p = paper(sub)
            h.append(f'<tr><td><b>{e(title)}</b><br>{venue_tag(p)}<br><a class="m" href="{e(p["url"])}">论文页面</a></td>'
                     f'<td>{e(what)}</td><td>{e(borrow)}</td><td>{e(cav)}</td><td>{repo_cell(key)}</td></tr>')
    h.append('</table><h3 style="margin:22px 0 6px;font-size:16px">有源码但关联较弱</h3><table><tr><th>论文</th><th>为什么排在后面</th><th>仓库</th></tr>')
    for sub, key, title, why in MINOR:
        p = paper(sub)
        h.append(f'<tr><td>{e(title)}<br><a class="m" href="{e(p["url"])}">论文页面</a></td><td>{e(why)}</td><td>{repo_cell(key)}</td></tr>')
    h.append('</table></section>')
    h.append('<section class="panel"><h2>三、没有可用源码（不推荐直接用，但思路值得知道）</h2><table><tr><th style="width:30%">论文</th><th>说明</th></tr>')
    for a, b in NOCODE:
        h.append(f'<tr><td><b>{e(a)}</b></td><td>{e(b)}</td></tr>')
    h.append('</table></section>')
    h.append('<section class="panel"><h2>四、几点判断（读完后的我的看法，未经实验验证）</h2><ol>'
             '<li><b>先量上限，再谈方法</b>：When Debate Helps 的“可恢复余量”和 DebateLedger 的“坍缩 / 纠正”都能在已保存的 v4 记录上事后算出，无需新调用。它们能回答“不一致分支里到底还有多少可恢复的正确答案、辩论又破坏了多少”。</li>'
             '<li><b>别在中间步骤上做仲裁</b>：MAS-ProVe 的结论与我们对节点聚合的直觉一致；情绪任务里“感知到了什么”本来就难以逐步核实。</li>'
             '<li><b>让专家的误差来源不同</b>：Cross-Channel Agreement 与 F2 指向同一件事——一致的前提是误差独立。一个可考虑的方向是引入误差来源不同的成员（例如专用的情绪模型，如 Nano-EmoX），这需要新的模型调用和授权，目前只是想法。</li>'
             '<li><b>情绪任务的特殊性</b>：ADEPT 把少数标注当信息而不是噪声，AffectGPT-RL 用情绪轮评价开放情绪，二者都提示“标签有歧义”要在评价和聚合里正面处理，而不是当作错误。</li></ol></section>')
    h.append('<section class="panel"><h2>五、方法与局限</h2><ul>'
             '<li>论文列表来自 openaccess.thecvf.com（CVPR）、icml.cc/virtual 和 neurips.cc/virtual 的公开列表页；OpenReview 的接口需要人机验证，没有访问。列表里的赛道 / 研讨会未区分。</li>'
             '<li>只按标题关键词筛选（debate、multi-agent、consensus、sycophancy、emotion、sentiment 等），标题没有这些词的相关论文会被漏掉；摘要从各论文页面读取，正文只在找代码时读过。</li>'
             '<li>代码链接来自论文页面、arXiv 版本正文或 CVPR 官方 PDF，再用 <code>gh api</code> 只读核验仓库是否存在、有多少源码文件；<b>没有运行、没有复现</b>，也没有评估代码质量。</li>'
             '<li>“没找到代码”只表示论文页面、arXiv 正文与按名称的搜索里都没有，不排除作者之后发布；一部分论文没有 arXiv 版本，正文未读。</li>'
             '<li>脚本：<code>scripts/lit2026/</code>（titles3.py、fetch3.py、code_hunt.py、verify_repos.py）、<code>scripts/build_mad2026_ml_venues.py</code>；核验数据：<code>metrics/mad2026_ml_venues_checks.json</code>。</li></ul></section>')
    h.append('</main></body></html>')
    out = ROOT / 'docs/mad-2026-ml-venues.html'
    out.write_text(''.join(h), encoding='utf8')
    print('wrote', out, out.stat().st_size, 'bytes; with-code papers:', n_code, 'minor:', len(MINOR))


if __name__ == '__main__':
    build()
