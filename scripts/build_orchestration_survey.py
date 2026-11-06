"""Build docs/agent-orchestration-survey.html: recent, highly cited "orchestration" work for LLM agents.

Static HTML + inline SVG, no scripts, no model calls. Citation counts/venues/dates come from the saved snapshot
metrics/orchestration_citations_20261102.json (Semantic Scholar batch API, queried 2026-11-02). The routing
headroom table is computed from saved outputs. Usage: python scripts/build_orchestration_survey.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import build_confusion_view as BC  # noqa: E402
from build_debate_survey import CSS, arrow, box, diamond, e, lab, svg  # noqa: E402

SNAP = {p['id']: p for p in json.loads((ROOT / 'metrics/orchestration_citations_20261102.json').read_text(encoding='utf8'))['papers']}
VENUE = {'Neural Information Processing Systems': 'NeurIPS', 'International Conference on Learning Representations': 'ICLR',
         'International Conference on Machine Learning': 'ICML', 'Annual Meeting of the Association for Computational Linguistics': 'ACL',
         'International Joint Conference on Artificial Intelligence': 'IJCAI', 'North American Chapter of the Association for Computational Linguistics': 'NAACL',
         'arXiv.org': 'arXiv', '': 'arXiv'}

# id -> (kind, verified-level, what the abstract says / how I know, relevance to this project)
ROWS = {
    '主流"编排者—执行者"（一个中心 Agent 规划并调度其余 Agent）': {
        '2411.04468': ('Magentic-One', '摘要', '主导 Agent（Orchestrator）负责规划、跟踪进度、出错时重新规划，并调度专门 Agent（浏览器、文件、写并运行 Python 代码）；在 GAIA、AssistantBench、WebArena 上与当时最好方法有统计意义上的相当表现。', '最标准的"编排者"形态，可对照你的汇总器'),
        '2506.12508': ('层级规划', '摘要', '中心规划者协调专门子 Agent，并在运行中动态扩展能力；提出 TEA 协议，把工具、环境、Agent 统一成带版本与生命周期的一等资源；论文报告在 GAIA 测试集 89.04%。', '名字最接近 "Orchestra"；偏工程协议，与你的任务距离较远'),
        '2505.23885': ('任务自动化', '仅标题', '标题表明：面向真实任务自动化的通用多 Agent 助手，使用"优化的劳动力学习"。', '引用较高的近期工作，未核实细节'),
        '2505.13516': ('层级编排', '检索摘要', '检索结果只给出标题：层级、自主、面向逻辑的多 Agent 编排。', '引用很低，仅作线索'),
        '2509.05651': ('监控式编排', '检索摘要', '检索摘要：加入监控机制跟踪 Agent 与环境的动态，用主动推断优化系统行为。', '引用很低，仅作线索'),
        '2303.17580': ('LLM 当控制器', '摘要', '主张让 LLM 充当控制器来管理现有 AI 模型：任务规划 → 选择模型 → 执行子任务 → 汇总响应。', '"编排"思路的经典源头，不算近期'),
    },
    '学习型编排 / 路由（用训练得到的策略决定"谁来做、用什么做"）': {
        '2505.19591': ('RL 编排者', '摘要', '中心"牵线人"随任务状态动态指挥各 Agent，用强化学习学习调度顺序；报告以更低计算成本取得更好表现，并出现更紧凑、带环的推理结构。', '"学出来的调度"的代表；需要训练数据'),
        '2511.21689': ('小模型编排', '摘要', '训练 8B 的小编排者去协调各种模型和工具，奖励同时考虑结果、效率和用户偏好；HLE 上 37.1% 超过 GPT-5 的 35.1% 且效率约 2.5 倍，tau2-Bench 与 FRAMES 上以约 30% 成本大幅超过 GPT-5。', '引用已达 50，且是近期代表；训练门槛较高'),
        '2502.11133': ('逐级路由', '摘要', '级联控制器依次决定协作模式、角色分配、为每个角色路由 LLM；MBPP 上提升 1.8%~8.2%，HumanEval 上开销最多降低 52.07%。', '与"按样本选方法 / 选模型"最接近'),
        '2311.09758': ('大小模型路由', '摘要', '用样例池记录各模型更可靠的情境；推理时取 k 个最近邻样例，按多数票把输入路由给小模型或大模型；对话状态跟踪上成本降低超过 50%。', '最朴素的"按相似样例路由"，不需要训练'),
        '2605.14483': ('反事实 RL', '检索摘要', '检索标题：用反事实强化学习学习可执行的多 Agent 编排。', '新论文，引用 1'),
        '2605.02801': ('编排轨迹', '检索摘要', '检索标题：通过"编排轨迹"为多 Agent 系统做强化学习。', '新论文，引用 8'),
    },
    '自动设计工作流 / 拓扑（离线搜索出好的编排，再固定使用）': {
        '2410.10762': ('工作流搜索', '摘要', '把工作流表示成代码（节点调用 LLM、边连接节点），用蒙特卡洛树搜索迭代改进；六个数据集上平均比最好基线高 5.7%；特定任务上较小模型以 GPT-4o 4.55% 的推理成本超过它。', '"训练免费、靠搜索"的路线，可在 train 320 条上做'),
        '2502.04180': ('智能体超网', '摘要', '不再搜索单一系统，而是优化"智能体架构的概率分布"，按查询难度采样不同系统；只用现有系统 6%~45% 的推理成本，并在六个基准上高出 0.54%~11.82%。', '"按样本难度配系统"，与你的触发思路同向'),
        '2406.07155': ('规模化协作', '仅标题', '标题表明：研究基于 LLM 的多 Agent 协作如何随规模扩展。', '引用 311，未核实细节'),
        '2410.02506': ('通信剪枝', '仅标题', '标题表明：精简多 Agent 的通信流水线以节省成本。', '引用 176，未核实细节'),
        '2410.11782': ('图网络拓扑', '仅标题', '标题表明：用图神经网络设计多 Agent 通信拓扑。', '引用 144，未核实细节'),
        '2310.02170': ('动态 Agent 网络', '摘要', '两阶段：先用无监督的"Agent 重要性分数"做团队优化选出 Agent，再协作解题；在代码生成、决策、通用推理上以适度计算成本超过强基线；某些 MMLU 科目上团队优化最多提升 25.0%。', '"挑选哪几位专家"的思路'),
        '2402.16823': ('可优化的图', '仅标题', '标题表明：把语言 Agent 表示成可优化的图。', '引用 89，未核实细节'),
    },
    '综述与评测（先读这些建立全局图景）': {
        '2402.01680': ('综述', '仅标题', '标题：基于 LLM 的多 Agent——进展与挑战的综述。', '引用最高的综述之一，2024 年'),
        '2501.06322': ('综述', '仅标题', '标题：多 Agent 协作机制综述。', '引用 651，2025 年'),
        '2601.13671': ('综述', '检索摘要', '检索标题：多 Agent 系统的编排——架构、协议与企业落地。', '2026 年，引用 25'),
        '2605.14892': ('综述', '检索摘要', '检索摘要：把"编排"（拓扑）与"路由"（谁下一步行动）区分，并讨论失败归因与自进化。', '2026 年，引用 7'),
        '2509.23537': ('对比评测', '检索摘要', '检索摘要：研究多轮多 Agent 编排（多个 LLM 提案或投票直至共识）相对单个 LLM 的表现。', '与你的"多数投票 vs 辩论"问题直接相关；引用 9'),
    },
}


def route_stats():
    M = [m for m, _ in BC.METHODS]
    rows = ''
    for p in ('gpt', 'gemini', 'omni'):
        S = {m: BC.preds(m, p) for m in M}
        ids = [i for i in BC.GOLD if all(i in S[m] for m in M)]
        n = len(ids)
        ok = lambda m: sum(S[m][i] == BC.GOLD[i] for i in ids)
        any_ = lambda ms: sum(any(S[m][i] == BC.GOLD[i] for m in ms) for i in ids)
        ne = [i for i in ids if S['direct'][i] != S['ppct'][i]]
        nd = sum(S['direct'][i] == BC.GOLD[i] for i in ne)
        np_ = sum(S['ppct'][i] == BC.GOLD[i] for i in ne)
        rows += (f'<tr><td>{p}</td><td>{n}</td><td>{ok("direct")}</td><td>{ok("ppct")}</td><td>{ok("v3")}</td><td>{any_(["direct", "ppct"])}</td><td><b>{any_(M)}</b></td>'
                 f'<td>{len(ne)}</td><td>{nd}</td><td>{np_}</td></tr>')
    return rows


# ------------------------------------------------------------------ diagrams
def d_learned():
    b = box(20, 105, 120, 60, ['当前任务状态'], 'plain')
    b += box(200, 85, 240, 100, ['编排者策略（小模型）', '根据状态决定：', '下一个调用谁 / 何时停'], 'new') + arrow([(140, 135), (200, 135)])
    b += box(540, 40, 170, 56, ['Agent A'], 'exist') + box(540, 124, 170, 56, ['Agent B / 工具'], 'exist') + box(540, 208, 170, 56, ['大模型'], 'exist')
    for y in (68, 152, 236):
        b += arrow([(440, 135), (540, y)])
    b += arrow([(625, 264), (625, 290), (320, 290), (320, 185)], dashed=True) + lab(470, 284, '执行结果写回状态，循环直到停止', 'middle')
    b += box(790, 105, 170, 60, ['最终答案'], 'final') + arrow([(710, 152), (750, 152), (750, 135), (790, 135)])
    b += lab(20, 20, '训练：强化学习，奖励 = 结果正确 + 成本/效率（+ 用户偏好）', 'start', 'l b')
    return svg(980, 310, b, '学习型编排')


def d_router():
    b = box(20, 105, 110, 60, ['查询'], 'plain')
    b += box(180, 95, 170, 80, ['① 协作模式', '（单人 / 辩论 / 链…）'], 'new') + arrow([(130, 135), (180, 135)])
    b += box(400, 95, 170, 80, ['② 角色分配', '要几位、各自角色'], 'new') + arrow([(350, 135), (400, 135)])
    b += box(620, 95, 170, 80, ['③ 为每个角色', '选哪个 LLM'], 'new') + arrow([(570, 135), (620, 135)])
    b += box(830, 105, 130, 60, ['执行'], 'final') + arrow([(790, 135), (830, 135)])
    b += lab(180, 215, '级联控制器逐级决定，在质量与成本之间权衡（MasRouter）', 'start')
    b += lab(180, 245, 'OrchestraLLM 更简单：取最相似的 k 个历史样例，按它们的多数票把输入送给小模型或大模型', 'start')
    return svg(980, 270, b, '路由型编排')


def d_search():
    b = lab(20, 24, 'AFlow：离线搜索出一个固定工作流，之后所有样本都用它', 'start', 'l b')
    b += box(20, 50, 190, 70, ['候选工作流', '（代码：LLM 节点 + 边）'], 'plain') + box(270, 50, 190, 70, ['蒙特卡洛树搜索', '执行 → 打分 → 改写'], 'new') + arrow([(210, 85), (270, 85)])
    b += box(520, 50, 190, 70, ['最优工作流'], 'judge') + arrow([(460, 85), (520, 85)]) + box(770, 50, 190, 70, ['在线：每个样本都走它'], 'exist') + arrow([(710, 85), (770, 85)])
    b += lab(20, 164, 'MaAS：学一个"架构分布"，每个样本现场采样不同的系统', 'start', 'l b')
    b += box(20, 190, 190, 70, ['智能体超网', '（架构的概率分布）'], 'plain') + box(270, 190, 190, 70, ['按查询难度', '采样一个系统'], 'new') + arrow([(210, 225), (270, 225)])
    b += box(520, 190, 190, 70, ['简单题：少用 Agent', '难题：多用 Agent'], 'judge') + arrow([(460, 225), (520, 225)]) + box(770, 190, 190, 70, ['推理成本 6%~45%'], 'exist') + arrow([(710, 225), (770, 225)])
    return svg(980, 290, b, '工作流 / 架构搜索')


def d_project():
    b = box(20, 105, 160, 90, ['一个样本', '+ 当前用哪个模型'], 'plain')
    b += diamond(310, 150, 85, 55, ['编排者 / 路由', '选哪条路？']) + arrow([(180, 150), (225, 150)])
    paths = [('Direct', 30), ('原始 PPCT', 95), ('v3 三专家 + 汇总', 160), ('专家一致才采纳，否则辩论', 225)]
    for t, y in paths:
        b += box(500, y, 270, 52, [t], 'exist' if t != '专家一致才采纳，否则辩论' else 'new') + arrow([(395, 150), (500, y + 26)])
    b += box(840, 105, 120, 90, ['最终标签'], 'final')
    for t, y in paths:
        b += arrow([(770, y + 26), (840, 150)])
    b += lab(20, 312, '可用的路由信号（假设）：模型本身、数据集、Direct 与 PPCT 是否一致、专家是否一致、是否预测 neutral', 'start')
    return svg(980, 330, b, '在你们项目里"编排者"可能的位置')


def d_orchestrator():
    b = box(20, 120, 110, 60, ['任务'], 'plain')
    b += box(190, 100, 230, 100, ['编排者（Orchestrator）', '规划 · 跟踪进度', '出错时重新规划'], 'judge') + arrow([(130, 150), (190, 150)])
    for t, y in [('浏览器 Agent', 20), ('文件 Agent', 120), ('代码 Agent', 220)]:
        b += box(520, y, 190, 60, [t], 'exist') + arrow([(420, 150), (520, y + 30)])
    b += lab(470, 12, '① 指派子任务', 'middle')
    b += arrow([(615, 290), (615, 305), (305, 305), (305, 200)], dashed=True) + lab(460, 322, '② 结果与状态回传，编排者决定下一步（循环）', 'middle')
    b += box(790, 120, 170, 60, ['最终答案'], 'final') + arrow([(360, 100), (360, 90), (750, 90), (750, 150), (790, 150)])
    b += lab(560, 104, '③ 任务完成时由编排者输出', 'middle')
    return svg(980, 335, b, '编排者—执行者')


# ------------------------------------------------------------------ table
def table():
    h = ('<table style="table-layout:fixed"><colgroup><col style="width:23%"><col style="width:8%"><col style="width:6%"><col style="width:9%">'
         '<col style="width:30%"><col style="width:8%"><col style="width:16%"></colgroup>'
         '<tr><th>论文</th><th>发表场所 · arXiv 日期</th><th>引用量</th><th>类型</th><th>要点</th><th>我核实到什么程度</th><th>与你的项目的关系</th></tr>')
    for grp, items in ROWS.items():
        h += f'<tr class="grp"><td colspan="7">{e(grp)}</td></tr>'
        for aid, (kind, ver, find, rel) in sorted(items.items(), key=lambda kv: -(SNAP[kv[0]].get('citationCount') or 0)):
            p = SNAP[aid]
            date = (p.get('publicationDate') or str(p.get('year')))[:7]
            recent = int(date[:4]) >= 2024
            ven = VENUE.get(p.get('venue') or '', (p.get('venue') or 'arXiv')[:18])
            h += (f'<tr><td><a href="https://arxiv.org/abs/{aid}">{e(p["title"])}</a></td><td class="m">{e(ven)} · {e(date)}{"" if recent else "<br>（非近期）"}</td>'
                  f'<td class="c">{p["citationCount"]:,}</td><td><span class="tag">{e(kind)}</span></td><td>{e(find)}</td><td class="v">{e(ver)}</td><td>{e(rel)}</td></tr>')
    return h + '</table>'


def build():
    body = f'''<div class="eyebrow">AGENT ORCHESTRATION / SURVEY</div>
<h1>Orchestra 类工作调研：谁来调度、怎么调度</h1>
<p class="muted">这里的"orchestra"我理解为"编排"：用一个编排者（orchestrator）或路由器，决定调用哪些 Agent、模型、工具，以及怎么组合。名字里真有 Orchestra 的论文（OrchestraLLM、AgentOrchestra、ToolOrchestra）引用都不高（23 到 50），所以我把整类"编排 / 路由 / 工作流搜索"放在一起，按引用量和是否近期（2024 年起）排列。</p>

<div class="tldr">
<div class="tl k"><b>① 近期高引用的编排工作大致三条路线</b>中心编排者调度执行者（Magentic-One，引用 314）；用强化学习学编排策略或路由（Puppeteer 136、ToolOrchestra 50、MasRouter 117）；离线搜索出好的工作流或架构（AFlow 511、MaAS 212）。</div>
<div class="tl k"><b>② 引用最高的近期工作</b>AFlow（511）、Magentic-One（314）、MacNet（311）、MaAS（212）、AgentPrune（176）、OWL（166）；综述类：LLM 多 Agent 综述（1317）、协作机制综述（651）。</div>
<div class="tl w"><b>③ 名字叫 "Orchestra" 的都很新</b>ToolOrchestra（2025-11，50）、AgentOrchestra（2025-06，28）、OrchestraLLM（2023-11，23）。引用量低主要因为发表晚，不代表质量。</div>
<div class="tl w"><b>④ 对你们这个项目</b>"按样本选方法"这一层的空间很小：即使有完美的路由器，对 GPT 和 Gemini 也只比最好的单一方法多 2 到 6 条（80 条里）。学习型编排需要训练数据和调用预算，建议先用低成本的路由规则验证。</div>
</div>

<section class="panel"><h2>一、编排类工作的几种形态（示意图）</h2>
<p class="muted small">图是我按各论文摘要整理的示意，不是论文原图；"我核实到什么程度"见第三节表格。</p>
<h3>1. 编排者—执行者（Magentic-One、AgentOrchestra）</h3><div class="fig">{d_orchestrator()}</div><p class="cap">编排者负责规划与重规划；执行者各管一类能力；结果回到编排者形成循环。</p>
<h3>2. 学习型编排（Puppeteer、ToolOrchestra）</h3><div class="fig">{d_learned()}</div><p class="cap">编排者本身是一个被训练的策略；奖励同时看结果和成本，所以会学着少调用昂贵的大模型。</p>
<h3>3. 路由型编排（MasRouter、OrchestraLLM）</h3><div class="fig">{d_router()}</div><p class="cap">不规划多步，只决定"怎么组队、用谁"；一次决策，成本低。</p>
<h3>4. 工作流 / 架构搜索（AFlow、MaAS）</h3><div class="fig">{d_search()}</div><p class="cap">把编排当成搜索问题：AFlow 搜出一个固定工作流；MaAS 保留一个分布，每个查询现场采样。</p>
</section>

<section class="panel"><h2>二、放到你们的项目里</h2>
<div class="fig">{d_project()}</div>
<p class="cap">在你们的场景里，编排者最自然的位置是"为每个样本选一条处理路径"。下表估算这一层的空间。</p>
<h3>方法级路由的空间（80 条开发集）</h3>
<p class="muted small">"任一方法对" 是不现实的完美路由上限（事后知道答案才能选）。五种方法 = Direct、原始 PPCT、v1、v2、v3 汇总。Omni 只统计五种方法都有效的 65 条。</p>
<table><tr><th>模型</th><th>样本</th><th>Direct</th><th>PPCT</th><th>v3 汇总</th><th>Direct 或 PPCT 任一对</th><th>五种方法任一对</th><th>Direct ≠ PPCT 的条数</th><th>其中 Direct 对</th><th>其中 PPCT 对</th></tr>{route_stats()}</table>
<h3>怎么读</h3>
<ul>
<li><b>空间有限。</b>GPT 最好单一方法是 PPCT 的 62；Direct 或 PPCT 任一对是 64，五种方法任一对是 68，上限比最好单一方法只多 2 到 6 条。Gemini 的最好是 Direct 的 60，上限 63 到 66。这还是"事后选"的完美路由，真实路由器达不到。</li>
<li><b>最简单的路由规则已经拿到大部分。</b>Direct 与 PPCT 不一致时：GPT 是 PPCT 对 12、Direct 对 2；Gemini 是 Direct 对 9、PPCT 对 3。所以"GPT 用 PPCT、Gemini 用 Direct"这条按模型选的规则，几乎等于最好的单一方法。</li>
<li><b>要注意目标。</b>你的目标是"带 PPCT 流程的结果好于 Direct"。把 Gemini 路由到 Direct 并不满足这个目标，只是说明 PPCT 在 Gemini 上目前没有增益。</li>
<li><b>更细一层是"专家级调度"。</b>也就是 Puppeteer、DyLAN 那类：决定调用哪几位专家、何时停。你们的 v3 数据显示三位专家有 74% 到 81% 的样本意见一致（GPT 81%、Gemini 74%），只有 19% 到 26% 的样本有分歧，能调度的空间同样很小。</li>
<li><b>更大的空间在别处。</b>"三位专家一致地错"（GPT 15 条、Gemini 12 条）是最大的误差来源，编排和辩论都碰不到它们。文献里能缓解的方向是引入<b>异质</b>的来源（不同模型、工具），例如 ToolOrchestra 调度的是"模型和工具"，而不只是同一个模型的多个角色。</li>
</ul>
<h3>三种做法的成本与风险（我的建议，不是定论）</h3>
<table><tr><th>做法</th><th>参考</th><th>需要什么</th><th>风险</th></tr>
<tr><td><b>规则路由</b>：按模型 / 数据集 / Direct 与 PPCT 是否一致选路径</td><td>OrchestraLLM 的最近邻投票思路</td><td>几乎不需要新调用；用 train 的 320 条设定规则</td><td>规则容易在 80 条上过拟合；需先在服务器补跑 train 的感知（有费用，需授权）</td></tr>
<tr><td><b>工作流搜索</b>：在 train 上搜索提示词或流程的组合</td><td>AFlow、MaAS</td><td>大量 API 调用（每轮搜索都要整批评估）</td><td>样本太小，搜索出的流程可能只是拟合噪声</td></tr>
<tr><td><b>学习型编排者</b>：训练策略决定调用谁</td><td>Puppeteer、ToolOrchestra</td><td>训练数据、强化学习与算力；ToolOrchestra 训练的是 8B 模型</td><td>数据规模远不够；"training-free" 的项目定位被改变</td></tr></table>
<div class="warn">以上数字来自本机保存的结果，是复用多次的 80 条开发集；"完美路由上限"只是衡量空间的工具，不是可达成的成绩。</div>
</section>

<section class="panel"><h2>三、文献表（近期且引用量较高优先）</h2>
<p class="muted small">引用量、发表场所、日期来自 Semantic Scholar（2026-11-02 查询，快照见 <code>metrics/orchestration_citations_20261102.json</code>）。"我核实到什么程度"：摘要 = 读了 arXiv 摘要；检索摘要 = 只看到搜索结果里的概括；仅标题 = 只用标题和引用量。每组内按引用量排序；2026 年的论文引用量天然偏低。一篇检索到的论文（arXiv 2511.15755，多 Agent 编排用于事故响应）作者已撤稿，未收入。AutoGen（3,083）、MetaGPT（2,753）、CAMEL（2,121）、ChatDev（1,415）是常被一并引用的通用多 Agent 框架，不是编排方法；前三个已在辩论调研页列出。</p>
{table()}
</section>
<p class="muted small" style="margin-top:22px">由 scripts/build_orchestration_survey.py 生成；页面静态渲染，不依赖脚本，不调用模型。</p>'''
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Orchestra 类工作调研</title><style>{CSS}</style></head><body><main>{body}</main></body></html>'


def main():
    out = ROOT / 'docs' / 'agent-orchestration-survey.html'
    out.write_text(build(), encoding='utf8')
    print(out, out.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
