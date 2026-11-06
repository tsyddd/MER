"""Build docs/mad-2026-blackbox.html: black-box, training-free methods (no logprobs / hidden states / weights) from
ACL / EMNLP / NeurIPS / ICML / CVPR 2026 that fit the PPCT disagreement-branch problem.

Reads metrics/mad2026_repo_checks.json and metrics/mad2026_ml_venues_checks.json (gh api read-only checks).
Code-level screening (grep for logprob/logits/hidden_state/... in shallow clones, nothing executed) is recorded in the page.
No model calls, no network. Usage: python scripts/build_mad2026_blackbox.py
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = json.loads((ROOT / 'metrics/mad2026_repo_checks.json').read_text(encoding='utf8'))['repos']
M = json.loads((ROOT / 'metrics/mad2026_ml_venues_checks.json').read_text(encoding='utf8'))
CHK = {**A, **M['repos']}
ML_PAPERS = M['papers']
AN = 'https://aclanthology.org/'


def e(s):
    return escape(str(s), quote=True)


def repo_cell(key):
    r = CHK.get(key)
    if not r or not r.get('ok'):
        return '<span class="m">无</span>'
    lic = r.get('license') or '无许可证'
    return (f'<a href="https://github.com/{e(r["slug"])}">{e(r["slug"])}</a><br>'
            f'<span class="m">★{r["stars"]} · 更新 {r["pushed"]} · 源码文件 {r["n_code_files"]} · {e(lic)}</span>')


def link(key, ml_sub=None):
    if ml_sub:
        for p in ML_PAPERS:
            if ml_sub.lower() in p['title'].lower():
                return f'<a class="m" href="{e(p["url"])}">论文页面</a>'
    return f'<a class="m" href="{AN}{key}/">{key}</a>'


# (key into CHK, ml title substring or None, short title, venue, what it does, what we can borrow, caveat)
METHODS = [
    ('2026.findings-emnlp.2014', None, 'MEDitor：分歧才升级的路由协议', 'Findings of EMNLP 2026',
     '两位轻量专家先答，一致就终止；分歧才进“深路径”：先构造“选项对齐的证据包”，再由候选约束的裁判在专家提出的候选里选一个或弃权（No-New-Option，不许引入新答案），最后有确定性的回退规则。',
     '结构和我们的 v4 几乎同构：“一致 → 直接输出；不一致 → 辩论 / 裁决”。可借的是两点：裁判只能在候选里选或弃权；证据先整理成按选项对齐的证据包再裁决。',
     'README 报告 4 个医学问答基准平均 78.03%（双专家 72.66%、仅辩论 75.29%、仅裁判 75.25%），深路径只触发 23.8%–55.1% 的题；论文摘要用的是 5 个英文医学 MCQA 基准（平均 65.94%），两处基准集合不同，数字以论文为准。任务是文本医学选择题，深路径含检索。'),
    ('2026.emnlp-main.830', None, 'Conformal Social Choice', 'EMNLP 2026 Main',
     '让异构 agent 把“概率”写在回复里（口头概率），线性意见池聚合后用 split conformal 得到预测集；单标签自动采纳，多标签升级。',
     '预测集可以代替人工的“专家答案 ∪ 易混淆标签”。代码核查：仓库里叫 logits 的变量其实是从回复文字里解析出来的口头概率，走的是文本接口。',
     '口头概率噪声较大（论文承认，覆盖保证不依赖它校准得好）；需要有标签的校准集，训练集 320 条由模型正确性筛选，会引入偏差；代码走 Amazon Bedrock，需改接 GPT / Gemini。'),
    ('2026.findings-acl.1600', None, 'Free-MAD', 'Findings of ACL 2026',
     '反从众提示 + 对整条辩论轨迹记分（初始答案加分、被放弃的扣分、新采纳的加分），不要求共识。',
     '只依赖“每位专家每一轮的答案”，可以在我们已保存的 Round 0 / 反思 / 辩论记录上事后计算。',
     '论文脚注给的仓库 jonathansantilli/freemad 的维护者不在作者名单里，README 自称“算法的 Python 实现”，不是论文实验代码；算法本身很短，可自行实现。'),
    ('2026.acl-long.650', None, 'Identity Bias：响应匿名化', 'ACL 2026 Long（Oral）',
     '把辩论提示里“谁说的”这类身份标记全部去掉（匿名化），并定义 Conformity / Obstinacy / IBC 指标。',
     '纯提示层的改动加日志统计，不需要任何内部输出。我们的专家以模态命名，辩论提示里“图谱专家说…”就是一种身份标记。',
     '论文设置是同质 agent、单 peer 环，我们是三位异构专家，指标要按附录的多 peer 做法调整；实验用开源模型，需改接 API。'),
    ('2026.findings-emnlp.1753', None, 'R²-MAD：经验记忆 + 置信度重加权', 'Findings of EMNLP 2026',
     '按辩论状态从历史辩论的经验库里检索相似经验，估计每个 agent 的可靠度，并把“可靠度 / 置信度”以文字形式写进提示来调制同伴影响。',
     '训练集 320 条可作经验库（遵守“验证集不参与调参”的约定）；代码核查未发现 logprob / 隐藏层相关调用。',
     '需要一个句向量模型做检索（外部工具，不是被测模型的内部状态）；任务是推理问答；MIT。'),
    ('2026.emnlp-main.2642', None, 'AgentAuditor（prompt-only 路径）', 'EMNLP 2026 Main',
     '把多条推理建成推理树，只在分叉点比较分支证据。仓库同时有训练 ACPO 的部分，但推理路径不需要训练。',
     '代码核查：涉及 logits 的只在 dataprep/ 的训练评估脚本里，推理路径是文本接口；步骤相似度用外部句向量模型。',
     '我们讨论过它不太适合情绪任务（步骤难以核实、专家推理骨架不同），MAS-ProVe 也发现过程级验证不稳定，所以不建议作为第一选择。'),
    ('2026.findings-acl.1649', None, 'ConSensus：按模态分 agent 的免训练协作', 'Findings of ACL 2026',
     '按模态拆成 agent，混合融合 = 语义聚合 + 统计共识。',
     '仓库自带 debate、MAD、ReConcile 等 baseline 实现，可直接对照；代码核查无内部输出调用。',
     '数据是传感器信号；默认用 Ollama 本地模型；无许可证。'),
    ('2026.emnlp-main.2572', None, 'TS-Debate：多模态零样本协作辩论', 'EMNLP 2026 Main',
     '按文本 / 视觉 / 数值模态分配专家，用“验证 — 冲突 — 校准”协议仲裁，reviewer 用轻量代码核对关键论断。',
     '结构与“三模态专家 + 汇总器”最像；代码核查无内部输出调用。',
     '数据是时间序列，不是情绪；其“可核查的论断”依赖代码执行，情绪感知里没有直接对应物。'),
    ('2026.acl-long.1450', None, 'MM-StanceDet：多模态多 agent 立场检测', 'ACL 2026 Long',
     '图文多模态分类：检索增强 → 多模态分析 agent → 推理增强的辩论 → 自我反思裁决。',
     '“多模态分类 + 辩论 + 裁决”的完整参考实现；代码核查无内部输出调用。',
     '作者署名与仓库所有者一致，但 README 称“reference implementation”、未标注论文，请自行核实是否为论文实验代码。'),
]

DIAG = [
    ('nips.debateledger', 'Measuring Collapse and Correction', 'DebateLedger', 'NeurIPS 2026（Evaluations & Datasets）',
     '按初始多数 / 最终多数是否正确记录“保持 / 坍缩 / 纠正 / 未修复”和首次破坏正确多数的轮次；并用“签名回放”评估干预：冻结到初始多数这类规则预防的坍缩少于损失的纠正（探针闸门：预防 29、损失 108）。',
     '可直接套在 v4 记录上；它对“冻结 / 一致就采纳”这类做法的负面证据，值得和我们的路由对照。'),
    ('nips.when-debate-helps', 'When Debate Helps', 'When Debate Helps 的指标部分', 'NeurIPS 2026',
     '“提议命中 / 可恢复余量 / 恢复 / 损伤”四个量，可量出多数投票漏掉了多少已经出现过的正确答案。',
     '这四个量只依赖各轮答案与真值，黑盒；论文构造“专家社会”的部分要改开源模型权重（仓库加载 HF 权重），那部分我们用不了。'),
    ('icml.hiddenbench', 'Systematic Failures in Collective Reasoning', 'HiddenBench', 'ICML 2026',
     '信息分散时，多 agent 过早收敛到共享信息；两阶段的轻量沟通协议（先交换 1–2 条决策相关事实并说明领先答案可能错在哪，再各自决定）明显改善。',
     '我们的三位专家各看不同模态，可借“先说独有线索再决定”的沟通协议。'),
    ('icml.teams-experts', 'Multi-Agent Teams Hold Experts Back', 'Multi-Agent Teams Hold Experts Back', 'ICML 2026',
     'LLM 团队即使被告知谁是专家，也达不到专家本人的水平（ML 基准上最多损失 41.1%）；瓶颈是“用好专家”而不是“找出专家”，表现为“整合式折中”——把专家与非专家的意见取平均。',
     '提醒我们辩论 / 汇总可能在“平均”各模态专家的意见；可检查辩论里是否出现折中而不是按证据加权。'),
]

NOCODE = [
    ('CAST（EMNLP 2026 Industry，2026.emnlp-industry.229）', '黑盒。“投票置信度”就是 K 条思维链样本的一致度；低于阈值才触发“对比式仲裁”：抽出各条竞争路径最强的论据并排呈现，让模型裁决；另有“不伤害”守卫的合并投票变体。论文报告在不确定题上最多比自一致性高 29%。论文里没有代码链接。'),
    ('Cascade-SC（EMNLP 2026 Main，2026.emnlp-main.1572）', '黑盒。“包含门”：强模型独立解出的答案落在弱模型候选集内才采纳，否则追加强模型采样。与我们 F6 里“Direct 的答案有 60/62、53/55 落在候选内”的现象很呼应。摘要写代码在 SUGAR-NLP/Cascade-SC，但该组织下没有此仓库（404）。'),
    ('Cross-Channel Agreement Beats Consensus（NeurIPS 2026）', '黑盒（测试时、不需要外部打分器）。所有候选看同一输入造成相关错误，用“误差来源不同的两条通道的一致”门控共识。没找到代码。'),
    ('Consensus Entropy（CVPR 2026）', '黑盒、免训练：用多个 VLM 的一致性熵估计输出可靠度并路由。论文给了 Aslanyulong/consensus-entropy，GitHub 返回 404。'),
    ('LASE（ICML）、OW / ISP 聚合（ICML）、DEAR（NeurIPS）、AIM（NeurIPS）、CascadeDebate（ACL Industry）、OrchDebate（EMNLP）、EAGLE（Findings EMNLP）', '均为黑盒思路（自适应触发辩论、考虑相关性的聚合权重、调节相互引用关系、多模态按需选交互方式、分层级联、自进化的辩论控制技能、视觉证据对齐的共识），但都没找到可验证的代码。'),
    ('AgendaFlow（Findings EMNLP 2026）', '论文给出 github.com/sunming-code/agendaflow，GitHub 返回 404（可能尚未公开）。'),
    ('Ringelmann Effect、Precise but Uncoupled（NeurIPS 2026）', '黑盒的分析：前者给出“有效独立 agent 数” N_eff 的标度律，后者发现“审阅者很准”不等于“批评被采纳”（与我们看到的反思几乎不改答案相呼应）。均没找到代码。'),
]

EXCLUDED = [
    ('SAUCE、UMAS（NeurIPS 2026）', '需要每轮的 token 熵 / token log-prob。'),
    ('ReFeri（EMNLP 2026）', '“forward confidence”由 logits 计算（代码 core/modeling.py 里有 logits 与 softmax）。'),
    ('SVote-2S（Findings EMNLP 2026）', '置信度加权用的 CISC 变体读取 token log-prob（eval_cisc_ptrue_vllm.py）。'),
    ('DMAD（Findings ACL 2026）', '“置信度调制”部分需要 GRPO 训练。'),
    ('When Debate Helps 的“专家社会”（NeurIPS 2026）', '靠给开源模型权重加高斯扰动构造，仓库加载 HF 权重。'),
    ('SexismDebate（ACL 2026 Long）', '路由依赖训练出来的专家模型的置信度（training/ 里按 logits 训练和校准）。'),
    ('World-Model Inspired Emotion-aware Token Refinement（ICML）', '免训练多模态情绪识别，但从摘要看是对模型内部 token 做精炼（我的推断），且没找到代码。'),
    ('EviaMAD（EMNLP）、OPPO / AffectGPT-RL / Nano-EmoX / SMART-Med / Latent Agents / The Value of Variance 等', '需要训练，或需要重新分配注意力 / 修改模型内部。'),
    ('PEAR（EMNLP 2026）', '仓库里加载本地 HF 因果语言模型；方法本身是否依赖内部输出我没有核实清楚，所以没放进黑盒清单。'),
]

MAP = [
    ('路由：何时算“一致”', 'MEDitor 的“两位专家一致就终止”；CAST 用 K 个样本的一致度作为触发信号；Conformal 用口头概率得到预测集，单标签才自动采纳。'),
    ('不一致时在候选里怎么选', 'MEDitor 的候选约束裁判（只能选专家提出的候选或弃权）；CAST 的“并排呈现各路径最强论据”的对比式仲裁；Cascade-SC 的“包含门”（强模型独立答案落在候选集内才采纳，对应 F6 里 Direct 答案 60/62、53/55 在候选内）。'),
    ('辩论过程里的从众', 'Identity Bias 的匿名化；Free-MAD 的反从众提示加轨迹记分；Multi-Agent Teams Hold Experts Back 提醒检查是否出现“折中平均”。'),
    ('怎么诊断', 'DebateLedger 的坍缩 / 纠正账本；When Debate Helps 的“可恢复余量”；HiddenBench 的沟通协议。'),
]

CSS = """:root{--ink:#172c38;--muted:#607583;--paper:#f4f6f3;--line:#dce4de;--green:#137a68;--amber:#b47c20;--red:#c9533c}*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1240px;margin:auto;padding:34px 28px 70px}
.eyebrow{font-size:12px;color:var(--green);font-weight:700;letter-spacing:2px}h1{font-size:30px;margin:8px 0 6px;line-height:1.3}h2{font-size:21px;margin:0 0 8px}
.muted{color:var(--muted)}.small{font-size:12.5px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 26px;margin-top:20px}
a{color:var(--green)}code{font:12.5px Consolas,monospace;background:#f1f5f1;padding:1px 5px;border-radius:4px}
.tldr{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}.tl{border:1px solid var(--line);border-radius:12px;padding:14px 18px;background:#fff}.tl>b:first-child{display:block;margin-bottom:4px}
.tl.w{border-left:4px solid var(--amber)}.tl.k{border-left:4px solid var(--green)}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:9px 10px;border-bottom:1px solid #edf1ed;text-align:left;vertical-align:top}th{color:var(--muted);font-size:12px;font-weight:600}
.m{color:var(--muted);font-size:12px}.warn{margin-top:14px;padding:10px 14px;border-left:3px solid var(--amber);background:#fff8e9;font-size:13.5px}
.tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:12px;background:#edf3f0;color:var(--green);white-space:nowrap}
ul,ol{padding-left:22px}li{margin:5px 0}
@media(max-width:900px){.tldr{grid-template-columns:1fr}main{padding:20px 14px}.panel{padding:16px}}"""


def build():
    h = [f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>2026 黑盒免训练的辩论 / 聚合方法（含源码）</title><style>{CSS}</style></head><body><main>']
    h.append('<div class="eyebrow">LITERATURE / BLACK-BOX · TRAINING-FREE</div><h1>黑盒、免训练的方法：不依赖 token 概率、隐藏层与权重</h1>')
    h.append('<p class="muted">按你的要求重新筛选：只收<b>只靠模型返回的文字</b>就能用的方法，可以直接用在 GPT / Gemini API 上。覆盖 ACL / EMNLP / NeurIPS / ICML / CVPR 2026。检索于 2026-11-03，只读，未运行任何论文代码，未调用被测模型。与 <a href="mad-2026-papers.html">ACL / EMNLP 清单</a>、<a href="mad-2026-ml-venues.html">NeurIPS / ICML / CVPR 清单</a> 配套。</p>')
    h.append('<div class="tldr">'
             '<div class="tl k"><b>① 最对口的是 MEDitor</b>“两位专家一致就终止，分歧才升级；裁判只能在专家提出的候选里选或弃权”，几乎就是我们 v4 的黑盒版本，有完整代码，关键词搜索未在代码里发现 logits / 隐藏层 / logprob 相关调用。</div>'
             f'<div class="tl k"><b>② 有代码的黑盒方法 {len(METHODS)} 篇 + 诊断度量 {len(DIAG)} 篇</b>诊断度量可以在已保存的日志上零成本计算（DebateLedger、可恢复余量等）。</div>'
             '<div class="tl w"><b>③ 思路对口但没有可用代码</b>CAST（分歧才触发的对比式仲裁）、Cascade-SC（“包含门”）、Cross-Channel Agreement。机制在摘要里写得清楚，但需要自己实现。</div>'
             '<div class="tl w"><b>④ 被排除的</b>SAUCE、UMAS、ReFeri、SVote-2S 等因为要 token 概率 / logits；DMAD、OPPO 等要训练。理由列在第四节。</div></div>')
    h.append('<section class="panel"><h2>一、筛选口径</h2><ul>'
             '<li><b>算黑盒</b>：只用模型返回的文字；让模型把“概率”或“置信度”写在回复里（口头置信度）也算，但它噪声较大；外部的句向量模型只是辅助工具，不是被测模型的内部状态。</li>'
             '<li><b>不算</b>：需要 token 概率 / logprob / logits / 熵，隐藏层 / 注意力 / 激活，修改权重，或任何微调 / RL 训练。</li>'
             '<li><b>怎么核验</b>：读摘要判断，再把仓库浅克隆后用文本搜索检查代码里是否出现 logprob、logits、hidden_state、output_scores、AutoModelForCausalLM 等（<b>只搜索，不运行</b>）。搜到的再逐处看是训练脚本里的、可选路径里的，还是方法本身依赖的。</li></ul></section>')
    h.append('<section class="panel"><h2>二、黑盒方法（有源码，代码核查通过）</h2><table><tr><th style="width:20%">论文</th><th style="width:26%">做什么</th><th style="width:22%">我们能借用什么</th><th style="width:16%">注意</th><th style="width:16%">仓库</th></tr>')
    for key, mls, title, venue, what, borrow, cav in METHODS:
        h.append(f'<tr><td><b>{e(title)}</b><br><span class="tag">{e(venue)}</span><br>{link(key, mls)}</td><td>{e(what)}</td><td>{e(borrow)}</td><td>{e(cav)}</td><td>{repo_cell(key)}</td></tr>')
    h.append('</table></section>')
    h.append('<section class="panel"><h2>三、黑盒的诊断 / 度量（在日志上零成本计算）</h2><table><tr><th style="width:20%">论文</th><th style="width:34%">它量什么</th><th style="width:28%">我们能借用什么</th><th style="width:18%">仓库</th></tr>')
    for key, mls, title, venue, what, borrow in DIAG:
        h.append(f'<tr><td><b>{e(title)}</b><br><span class="tag">{e(venue)}</span><br>{link(key, mls)}</td><td>{e(what)}</td><td>{e(borrow)}</td><td>{repo_cell(key)}</td></tr>')
    h.append('</table></section>')
    h.append('<section class="panel"><h2>四、被排除的，以及原因</h2><table><tr><th style="width:34%">论文 / 方法</th><th>原因</th></tr>')
    for a, b in EXCLUDED:
        h.append(f'<tr><td><b>{e(a)}</b></td><td>{e(b)}</td></tr>')
    h.append('</table></section>')
    h.append('<section class="panel"><h2>五、黑盒，但没有可用代码（思路值得知道）</h2><table><tr><th style="width:34%">论文</th><th>说明</th></tr>')
    for a, b in NOCODE:
        h.append(f'<tr><td><b>{e(a)}</b></td><td>{e(b)}</td></tr>')
    h.append('</table></section>')
    h.append('<section class="panel"><h2>六、对照我们的流水线（我的建议，未验证）</h2><table><tr><th style="width:24%">环节</th><th>可借用的黑盒做法</th></tr>')
    for a, b in MAP:
        h.append(f'<tr><td><b>{e(a)}</b></td><td>{e(b)}</td></tr>')
    h.append('</table><div class="warn">以上都是读完论文后的想法，没有实验验证。F6 的结论是不一致分支约等于在候选里随机选；先在已保存的日志上用诊断指标量出“上限”和“损失”，比直接改流水线更稳妥。</div></section>')
    h.append('<section class="panel"><h2>七、方法与局限</h2><ul>'
             '<li>NeurIPS / ICML / CVPR 的论文列表来自各会议公开页面，按标题关键词筛选后读了 657 篇摘要；ACL / EMNLP 用 Anthology 的全部摘要做关键词初筛。标题和摘要里没有这些词的相关论文会漏。</li>'
             '<li>这批黑盒方法里，NeurIPS / ICML / CVPR 中“可直接用的方法”很少，大多是分析型工作；真正能直接借用的方法主要来自 ACL / EMNLP。</li>'
             '<li><b>更正</b>：用更宽松的方式重扫 PDF 后，我发现此前有几处代码链接被漏掉或误判，已在前两个页面更正：AgendaFlow（有链接但仓库 404）、Diversity Collapse（有仓库）、Emergence of Biased Consensus（有本文代码）、Cascade-SC 与 Consensus Entropy（有链接但仓库 404）。</li>'
             '<li>只核验了“仓库存在、有源码、代码里是否使用内部输出”，<b>没有运行、没有复现</b>，也没有评估代码质量；“没找到代码”不排除作者之后发布。</li>'
             '<li>脚本：<code>scripts/lit2026/</code>、<code>scripts/build_mad2026_blackbox.py</code>；数据：<code>metrics/mad2026_repo_checks.json</code>、<code>metrics/mad2026_ml_venues_checks.json</code>。</li></ul></section>')
    h.append('</main></body></html>')
    out = ROOT / 'docs/mad-2026-blackbox.html'
    out.write_text(''.join(h), encoding='utf8')
    print('wrote', out, out.stat().st_size, 'bytes; methods', len(METHODS), 'diag', len(DIAG))


if __name__ == '__main__':
    build()
