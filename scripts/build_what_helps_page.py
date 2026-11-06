"""Build docs/mad-what-helps-our-case.html: 针对 PPCT 不一致分支困境，哪些文献方法可能有帮助（含 F7 诊断数字）。

数字来自 metrics/findings_log.md 的 F6 / F7 与 metrics/disagreement_branch_diagnostic.json；文献部分来自 docs/mad-debate-papers-math.html 已读的论文。
Usage: python -X utf8 scripts/build_what_helps_page.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_debate_papers_math_page as M  # noqa: E402

ROOT = M.ROOT

BODY = r"""
<h1>哪些方法能帮我们解决“不一致分支”的困境</h1>
<p class="muted">2026-11-04。先看我们自己的日志里辩论到底发生了什么（F7，只读已保存输出），再按“是否针对这个失败机制、是否黑盒免训练、是否符合 AGENTS.md”给文献方法排序。全部是开发集上的探索，不是独立泛化证据。</p>

<div class="note"><b>先承认一个疏漏</b>：上一页（<a href="mad-debate-papers-math.html">论文总结</a>）只把 6 篇论文各自讲清楚，没有对照我们的失败机制。这一页补上。</div>

<h2>1. 我们的困境到底是什么：先看数据</h2>
<p>不一致分支 = 三位专家没有唯一共同标签的样本（Gemini 62 条，GPT 55 条，共 400 条）。F6 已知：这里 v4 答对 26/62 与 19/55，Direct 答对 38/62 与 26/55。F7 进一步拆开辩论内部：</p>
<table>
<tr><th>量</th><th>Gemini</th><th>GPT</th><th>含义</th></tr>
<tr><td>真实标签在专家反思后答案里（提议命中）</td><td>55 / 62</td><td>48 / 55</td><td>上限很高</td></tr>
<tr><td>多数错但标签在提议里（可恢复余量 $H$）</td><td>31</td><td>25</td><td>约一半样本“本可救回”</td></tr>
<tr><td>其中最终答对（恢复）</td><td>7（23%）</td><td>4（16%）</td><td>实际救回很少</td></tr>
<tr><td>多数对而最终答错（损伤）</td><td>6 / 24</td><td>8 / 23</td><td>同时还在带偏</td></tr>
<tr><td>专家改答案：错→对 / 对→错</td><td>34 / 34</td><td>23 / 30</td><td>近似公平赌局</td></tr>
<tr><td>孤立正确专家：改从众 / 总数</td><td>18 / 22</td><td>14 / 19</td><td>正确少数几乎都让步</td></tr>
<tr><td>孤立错误专家：改从众 / 总数</td><td>22 / 28</td><td>20 / 29</td><td>错的也一样让步</td></tr>
<tr><td>v3 汇总器在该分支答对</td><td>5 / 62</td><td>3 / 55</td><td>文本聚合几乎无用</td></tr>
</table>
<div class="box"><b>读法</b>：辩论的问题不是“没有正确答案可选”（提议命中：Gemini 89%、GPT 87%），而是<b>它不会区分该坚持还是该让步</b>。孤立专家无论对错都约 75%–80% 转向另两位，所以错→对与对→错相抵：这正是“辩论是鞅”在我们数据里的样子。文献里的理论 $\mathbb{E}[p_t\mid\mathcal{F}_{t-1}]=p_{t-1}$ 给出的预期就是“不改变期望正确率”。</div>
<p>此外，在 Gemini 上 Direct（38/62）高于任何一位专家（三位反思后答对 24、32、24，共 62 条），GPT 上则不然（graph 专家 31/55 高于 Direct 26/55）。所以“换成最强专家”并不稳定。</p>

<h2>2. 按“能不能治这个病”给方法排序</h2>
<p>评判三条：① 是否针对“不会区分坚持与让步 / 聚合弱于一次完整判断”；② 是否黑盒免训练；③ 是否符合 AGENTS.md（真实标签等不进入推理请求）。</p>
<table>
<tr><th>排名</th><th>做法</th><th>来源</th><th>针对哪个失败</th><th>黑盒免训练</th><th>证据强度与风险</th></tr>
<tr><td><b>1</b></td><td><b>不一致分支直接由 Direct（全模态一次判断）决定</b></td><td>Cascade-SC 的“强教师”思路；2605.09618 / 2508.17536 的“先用简单规则”；我们的 F6</td><td>聚合弱于一次完整判断；辩论≈随机</td><td>是，零新增调用（Direct 已有）</td><td>F6：事后组合 319/400（Direct 311）、307/400（Direct 294）。<b>同一批开发数据上的事后组合</b>，训练 320 条由模型正确性筛选，需要新样本确认。文献没有在分歧子集上直接证明。</td></tr>
<tr><td><b>2</b></td><td><b>候选受限的全模态裁判</b>：把专家候选限定为选项，裁判看原始媒体（不是专家文字），可弃权并回退到 Direct</td><td>MEDitor（受限裁判 + 弃权回退）、CAST（并排对比最强两条论据）</td><td>汇总器在该分支只对 5/62，3/55（文字聚合失效）</td><td>是，但需要新的模型调用</td><td>Direct 的答案有 60/62、53/55 落在候选并集内，所以限定候选几乎无损；<b>能否超过 Direct 没有证据</b>，且 F5 显示专家“证据”前后不一致，喂文字证据可能反而有害。建议只在这 117 条分支样本上 A/B。</td></tr>
<tr><td><b>3</b></td><td>辩论规则：要求<b>有可核对证据才允许改答案</b>，并明确允许保留异议</td><td>2609.38324（不压制异议、关闭推理，$c^*=\gamma/(\gamma+a)$）；2606.02866（证据门控）；2510.20963（协作式、引用核对）</td><td>孤立正确专家 78% 让步</td><td>是（提示词）</td><td>2606.02866 里纯文本门控在 $n=50$ 上不显著，只有加代码执行才显著；我们没有可执行的验证对象。2510.20963 依赖异构模型家族。我们的三位专家是同一模型的不同模态视角，前提不同。<b>属于探索，不建议先做。</b></td></tr>
<tr><td>4</td><td>诊断：账本与可恢复余量（零成本）</td><td>DebateLedger、When Debate Helps</td><td>弄清哪里在损失</td><td>是</td><td>已完成（F7）。它告诉我们余量 $H$ 大、恢复低，不告诉怎么修。</td></tr>
<tr><td>5</td><td>用投票熵决定何时升级辩论</td><td>2605.09618</td><td>决定何时辩论</td><td>是</td><td>该论文自己的结果不显著（+1.6 pp，$p=0.125$）；我们的路由本来就是“不一致→辩论”，用处小。</td></tr>
</table>

<h3>不建议或暂不适用</h3>
<ul>
<li><b>置信加权辩论（2601.19921）</b>：需要 GRPO + LoRA 训练，不符合免训练约束。</li>
<li><b>R²-MAD 的经验库</b>：经验来自带标签的历史辩论，与 AGENTS.md 对标签的约定是否冲突需要你判断，在此之前不推荐。</li>
<li><b>AgentAuditor 类的节点聚合</b>：此前已分析，不适合情感任务，且步骤级验证不稳定。</li>
<li><b>多样化初始化（2601.19921）</b>：我们的提议命中已有 87%–89%，缺的不是多样性，是选择；而且文献里增益不稳定。</li>
</ul>

<h2>2.5 目标是“不低于 Direct”：先算清能赢多少、会输多少</h2>
<p>设裁判只在它认为 Direct 错时才改答案，改动集合为 $S$。则相对 Direct 的净变化为</p>
$$\Delta = a - b,\qquad a=\#\{\text{Direct 错}\to\text{对}\},\quad b=\#\{\text{Direct 对}\to\text{错}\}.$$
<p>全部弃权（$S=\varnothing$）时 $\Delta=0$，恰好等于 Direct，所以“回退到 Direct”在构造上保证不低于 Direct。裁判是否有价值，只取决于改动的精度：必须 $a>b$。用已保存的 Direct 两次运行（<code>metrics/direct_rerun_117.json</code>，117 条分支样本）算上限与风险：</p>
<table>
<tr><th>量</th><th>Gemini（62 条）</th><th>GPT（55 条）</th></tr>
<tr><td>Direct 答对（可能被改坏的上限 $b$）</td><td>38</td><td>26</td></tr>
<tr><td>Direct 答错且真实标签在专家反思答案里（可能被改对的上限 $a$）</td><td>18</td><td>22</td></tr>
<tr><td>Direct 答错且标签不在专家答案里（候选约束救不了）</td><td>6</td><td>7</td></tr>
<tr><td>Direct 两次运行答案不同的样本</td><td>18（29%）</td><td>13（24%）</td></tr>
<tr><td>两次运行都对 / 至少一次对</td><td>31 / 46</td><td>20 / 30</td></tr>
<tr><td>两次运行各自答对</td><td>38、39</td><td>26、24</td></tr>
</table>
<div class="box"><b>三个结论</b>
<ol>
<li><b>想超过 Direct，裁判必须是个很准的“Direct 出错探测器”。</b>它要在 Direct 错的 18 / 22 条里改对，同时几乎不碰 Direct 对的 38 / 26 条。Direct 本来就有 61% / 47% 的准确率，随便改动大概率先亏。</li>
<li><b>裁判和 Direct 看的是同一份媒体、同一个模型，错误高度相关。</b>它很可能和 Direct 同错，也就是很少真正改变答案；这是风险，不是已证事实。</li>
<li><b>Direct 自己并不稳定</b>：两次运行在约四分之一的样本上给出不同答案（总准确率只差 1–2 条）。这说明“Direct 答对”里有一部分是运气；也说明<b>对 Direct 多采样后投票</b>是一条不需要候选、不需要新设计的黑盒免训练路径（文献：Debate or Vote 的结论是多数投票解释了大部分收益）。“至少一次对”比一次对多出 8 / 4 条，只是 oracle 上限，不是可得到的收益。</li>
</ol>
<b>噪声底</b>：Direct 重跑自身的差距就有 ±1–2 条，所以任何与 Direct 相差 2 条以内的结果都无法与 Direct 区分。</div>
<p>注意：此处“专家反思答案”只含主答案；F6 的并集还含备选标签，所以 F6 里 Direct 落在候选内是 60/62、53/55，这里按主答案算是 57/62、52/55，口径不同。</p>

<h3>实验设计（待授权，未运行）</h3>
<table>
<tr><th>组</th><th>做法</th><th>新增调用（117 条分支样本）</th></tr>
<tr><td>A0</td><td>Direct（已保存的 run1）</td><td>0</td></tr>
<tr><td>A1</td><td><b>Direct 自一致</b>：同一个 Direct 提示再采样 4 次，与已有结果合成 5 次后多数投票；平票取已保存的 run1</td><td>Gemini 62×4 + GPT 55×4 = 468</td></tr>
<tr><td>A2</td><td><b>门控裁判</b>：候选 = 三位专家反思主答案的并集；裁判看与 Direct 相同的原始媒体，只输出候选之一或弃权；采样 3 次，<b>仅当 3 次一致选中同一个与 Direct 不同的候选才改，其余一律回退 Direct</b></td><td>Gemini 62×3 + GPT 55×3 = 351</td></tr>
</table>
<ul>
<li><b>不把 Direct 的答案放进裁判请求</b>：AGENTS.md 规定既有预测不得进入被测模型的推理请求。回退由代码在调用之后确定，裁判看不到 Direct 答案；也不给专家的理由文字（F5 显示这些“证据”前后不一致，F7 显示文字聚合几乎无用）。</li>
<li><b>参数事先固定，不看结果调</b>：采样次数 3 和 4 次、门控规则都写在这里，不根据 117 条的结果再改。其中 23 条属于验证集（Gemini 15、GPT 8），按 AGENTS.md 验证集不得参与本轮方法调参，所以不调参就是必须的。</li>
<li><b>成功标准事先定</b>：每组、每家模型报告“改对 $a$ / 改坏 $b$ / 净 $\Delta$”。“达到 Direct”= 两家都是 $\Delta\ge0$（A1 因为不是回退型，要报告 $\Delta$ 而不是假定）；“超过 Direct”要求净增超出 ±2 的噪声底，并给出配对检验。</li>
<li>总共 819 次新调用（468 + 351）。只读已保存输出之外，这是第一次需要模型调用，需要你授权。</li>
</ul>

<h2>3. 我的建议（一条）</h2>
<div class="box">
<ol>
<li><b>先把方案 1 当作基线定下来</b>：不一致分支用 Direct。它不需要任何新调用，也是目前唯一有我们自己数据支持的做法。但它只是开发集上的事后组合，要在没参与过选择的新样本上确认。</li>
<li><b>要继续追“不低于 / 超过 Direct”，做 2.5 节的 A1 和 A2 两组</b>：在 117 条分支样本上比较“Direct”“Direct 自一致”“门控裁判（不确定就回退 Direct）”，指标用改对 / 改坏 / 净变化，不只看总准确率。A1 不依赖候选，是更便宜、证据更足的一条；A2 才是“候选受限裁判”的检验。这需要新的模型调用，所以要你先授权。</li>
<li>方案 3（辩论规则）和别的辩论变体先不做：F7 显示辩论过程本身没有方向，改提示词也许能让它从“公平赌局”变成“稍微偏向某一边”，但能否超过一个看原始媒体的强裁判，没有证据；这是我的判断，未验证。</li>
</ol>
</div>

<h2>4. 需要你决定的两点</h2>
<ul>
<li>是否授权上面 2.5 节的实验（A1 + A2，共 819 次新调用，参数和成功标准已事先固定）。</li>
<li>如果要采用方案 1，对外表述时需要写明“事后组合、开发集、训练集经模型正确性筛选”。</li>
</ul>

<h2>5. 局限</h2>
<ul>
<li>所有数字来自开发集的已保存输出；孤立专家“从众”不等于被说服，也可能是正确的重新判断。</li>
<li>文献里没有任何一篇在“分歧子集”上证明辩论超过 Direct；方案 2 是否有效完全没有证据，只是基于我们数据的假设。</li>
<li>Direct 的 400 条逐样本结果在服务器上，本机只有验证 80 条，Direct 的分支数字沿用 F6 汇总。</li>
</ul>
<p class="muted">来源：metrics/findings_log.md 的 F6、F7；metrics/disagreement_branch_diagnostic.json；论文 arXiv:2508.17536、2601.19921、2609.38324、2510.20963、2606.02866、2605.09618，MEDitor（2026.findings-emnlp.2014）、CAST（2026.emnlp-industry.229）、Cascade-SC（2026.emnlp-main.1572）。</p>
"""


def build():
    html = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>哪些方法能帮我们解决不一致分支的困境</title><style>{M.CSS}</style></head><body>'
            f'{M.render_math(BODY)}</body></html>')
    out = ROOT / 'docs/mad-what-helps-our-case.html'
    out.write_text(html, encoding='utf8')
    print('wrote', out, out.stat().st_size, 'bytes; math nodes:', html.count('<math'))


if __name__ == '__main__':
    build()
