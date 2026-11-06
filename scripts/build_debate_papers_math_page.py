"""Build docs/mad-debate-papers-math.html: 辩论论文的理论与方法总结，公式用 MathML 渲染（无需网络）。

正文里 $...$ 为行内公式、$$...$$ 为独立公式，构建时由 latex2mathml 转成 MathML。
需要 latex2mathml（本机装在 Temp/litsearch/l2m，用 sys.path 引入）。只读文献整理，不调用模型。
Usage: python -X utf8 scripts/build_debate_papers_math_page.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, 'C:/Users/Admin/AppData/Local/Temp/litsearch/l2m')
import latex2mathml.converter as L2M  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

CSS = """
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;max-width:1040px;margin:32px auto;padding:0 20px;color:#1f2933;line-height:1.85;font-size:16px}
h1{font-size:25px;border-bottom:2px solid #1f2933;padding-bottom:8px}
h2{font-size:19px;margin-top:40px;border-left:4px solid #3b6ea8;padding-left:10px}
h3{font-size:16px;margin-top:22px;color:#274a73}
math{font-size:1.12em}
math[display=block]{margin:14px 0;overflow-x:auto}
.box{background:#f4f7fb;border:1px solid #cfd9e6;border-radius:6px;padding:10px 16px;margin:14px 0}
.note{background:#fff8e1;border:1px solid #f0d98a;border-radius:6px;padding:10px 16px;margin:14px 0}
.fix{background:#fdecea;border:1px solid #f1b0a8;border-radius:6px;padding:10px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px;line-height:1.6}
th,td{border:1px solid #cbd2d9;padding:6px 9px;vertical-align:top;text-align:left}
th{background:#eef2f6}
.muted{color:#6b7785;font-size:13px}
code{background:#f0f3f6;padding:1px 4px;border-radius:3px}
"""


def render_math(text):
    def disp(m):
        return L2M.convert(m.group(1).strip(), display='block')

    def inl(m):
        return L2M.convert(m.group(1).strip())

    text = re.sub(r'\$\$(.+?)\$\$', disp, text, flags=re.S)
    return re.sub(r'\$(.+?)\$', inl, text, flags=re.S)


BODY = r"""
<h1>多智能体辩论论文：理论与方法总结（公式渲染版）</h1>
<p class="muted">2026-11-04。依据 arXiv 全文（HTML 版）的章节提取整理，涉及 6 篇；抓取按字数截断，附录后段有未读部分（文末列出）。公式用 MathML 渲染，用 Chrome / Edge 直接打开即可，无需网络。只读文献，未运行代码，未调用模型。标注“我的推导”的是我按论文设定自己写出的代数，不是论文原文。</p>

<div class="fix"><b>更正（相对此前页面）</b>：① 2605.09618 的“66%”是 $H\le 1$（含分裂投票）的占比，全票一致且错误只有 $17/47\approx 36\%$；② 2601.19921 只证明了信念期望单调不降（次鞅），“优于多数投票”是实验结论，不是定理。</div>

<h2>0. 先弄懂“鞅”：一个公平赌局</h2>
<p>你有 10 元，每轮抛一枚公平硬币：正面 +1 元，反面 −1 元。设 $M_t$ 是第 $t$ 轮后的钱数，则</p>
$$\mathbb{E}[M_{t+1}\mid M_t]=\tfrac12(M_t+1)+\tfrac12(M_t-1)=M_t .$$
<p>“已知现在，下一步的期望等于现在”就是<b>鞅</b>。一般地，设 $\mathcal{F}_{t-1}$ 是到 $t-1$ 步为止的全部历史，则</p>
$$\text{鞅：}\ \mathbb{E}[X_t\mid\mathcal{F}_{t-1}]=X_{t-1},\qquad \text{次鞅：}\ \mathbb{E}[X_t\mid\mathcal{F}_{t-1}]\ge X_{t-1}.$$
<p>如果硬币偏向正面（正面概率 0.6），则 $\mathbb{E}[M_{t+1}\mid M_t]=0.6(M_t+1)+0.4(M_t-1)=M_t+0.2$，这是次鞅，有向上的漂移。</p>
<div class="box"><b>要点</b>：鞅的值会上下波动，只是<b>没有可预测的方向</b>。取总期望，有 $\mathbb{E}[X_T]=X_0$：玩多少轮，期望收益都是 0。</div>

<h2>1. 辩论为什么是鞅：2508.17536《Debate or Vote》（NeurIPS 2025 Spotlight）</h2>
<h3>模型</h3>
<ul>
<li>$K$ 个选项，选项 1 正确。agent $i$ 在第 $t$ 轮有 Dirichlet 参数 $\boldsymbol\alpha_{i,t}=(\alpha^{(1)}_{i,t},\dots,\alpha^{(K)}_{i,t})$。</li>
<li>它先抽信念 $\boldsymbol\theta\sim\mathrm{Dir}(\boldsymbol\alpha)$，再按 $\boldsymbol\theta$ 抽回答。选项 $k$ 被回答的边际概率为 $\alpha^{(k)}/\sum_j\alpha^{(j)}$。</li>
<li>agent 对正确答案的信念：$p_{i,t}=\alpha^{(1)}_{i,t}\big/\sum_k\alpha^{(k)}_{i,t}$。</li>
<li>辩论一轮就是把邻居回答的计数 $\mathbf{c}_{i,t}$ 加进参数（Dirichlet 与类别分布共轭）：$\boldsymbol\alpha_{i,t}=\boldsymbol\alpha_{i,t-1}+\mathbf{c}_{i,t}$。</li>
</ul>
<h3>定理 2（鞅）</h3>
<p>若第 $t-1$ 轮邻居的平均信念等于 agent 自己的信念，</p>
$$\frac{1}{|\mathcal{N}(i)|}\sum_{j\in\mathcal{N}(i)}p_{j,t-1}=p_{i,t-1},$$
<p>则</p>
$$\mathbb{E}[\,p_{i,t}\mid\text{历史}\,]=p_{i,t-1}.$$
<p>论文说明该结论在<b>同质且全连接</b>、<b>完全隔离</b>、<b>孤立的同质小团</b>三种情形下成立（Appendix D.3.1 Prop.1）；附录对异质 agent 的推广在我读到的文本之外。</p>
<h3>我的推导（帮助理解，不是原文）</h3>
<p>设有 $n$ 个邻居，每个邻居以概率 $p_j$ 给出正确回答，$S_{t-1}=\sum_k\alpha^{(k)}_{i,t-1}$。则新增正确计数的期望为 $\sum_j p_j$，总计数增加 $n$：</p>
$$\mathbb{E}[p_{i,t}\mid\text{历史}]=\frac{\alpha^{(1)}_{i,t-1}+\sum_{j}p_j}{S_{t-1}+n}.$$
<p>当邻居平均信念等于自己的信念（$\sum_j p_j=n\,p_{i,t-1}$，且 $\alpha^{(1)}_{i,t-1}=p_{i,t-1}S_{t-1}$）时，分子 $=p_{i,t-1}(S_{t-1}+n)$，于是期望就是 $p_{i,t-1}$。如果邻居平均比自己更相信正确答案，分子变大，就变成次鞅。</p>
<h3>定理 1（多数投票的“放大效应”）</h3>
<p>设正确选项与亚军的平均概率差为 $\Delta=\bar\theta_1-\bar\theta_2$。若 $N>K/\Delta^2$，则 $N$ 个 agent 做多数投票成功的概率满足</p>
$$P(y_{\mathrm{mv}}=1)\;\ge\;1-\exp\!\Big(-N\Big(\tfrac{\Delta}{\sqrt K}-\tfrac{1}{\sqrt N}\Big)^{2}\Big).$$
<p>二分类且 $p_0>1/2$ 时（Appendix C，Hoeffding）：$P(\bar X>1/2)\ge 1-\exp\!\big(-2N(p_0-1/2)^2\big)$。</p>
<h3>实验（Qwen2.5-7B-Instruct 平均准确率，Table 1 / 2）</h3>
<table>
<tr><th>方法</th><th>平均准确率</th></tr>
<tr><td>单 agent</td><td>0.7205</td></tr>
<tr><td>多数投票</td><td>0.7691</td></tr>
<tr><td>最好的普通辩论（Sparse，$T=2$）</td><td>0.7330</td></tr>
<tr><td>MAD-vanilla（$T=2$）/ Conformist / Follower</td><td>0.7332 / 0.7625 / 0.7629</td></tr>
<tr><td>MAD-oracle（锁定第一个正确答案，需要真值）</td><td>0.8236</td></tr>
</table>
<p>Llama3.1-8B：单 agent 0.6203，多数投票 0.7242，最好的普通辩论 0.6929。论文的“偏向正确更新”（第 5 节）只给了定性论证，没有定理。<b>结论</b>：实用变体仍略低于多数投票；论文建议先做好集成。</p>

<h2>2. 置信加权与多样性：2601.19921《Demystifying Multi-Agent Debate》</h2>
<h3>理论（沿用 Dirichlet 模型，Appendix D）</h3>
<p>无偏辩论仍是鞅：$\mathbb{E}[p_{i,t}\mid\mathcal{F}_{t-1}]=p_{i,t-1}$（Eq.14）。</p>
<p><b>多样化初始化（Prop.1 / Thm.2）</b>：令 $S$ 为初始池里不同的“有信息的假设”个数。若 $P(\text{正确}\mid S=s)$ 随 $s$ 不减，且多样化初始化在一阶随机占优意义上优于随机采样，则</p>
$$P(\text{correct}\mid\text{diverse init})\;\ge\;P(\text{correct}\mid\text{random init}).$$
<p>论文的示例形式是 $1-(1-p)^s$。动力学不变，只是起点变好。</p>
<p><b>置信加权（Thm.1，次鞅）</b>：用置信度 $w_j$ 对邻居投票加权，</p>
$$\tilde c^{(k)}=\sum_j w_j\,\mathbf{1}\{y_j=k\},\qquad \boldsymbol\alpha_t=\boldsymbol\alpha_{t-1}+\tilde{\mathbf c}_t,\qquad p_{i,t}=\frac{\alpha^{(1)}_{t-1}+\Delta^{(1)}}{S_{t-1}+\Delta}.$$
<p>Lemma 1 说明 $p_{i,t}$ 是 $p_{i,t-1}$ 与“置信加权后正确质量占比”的凸组合。在 <b>Assumption 1</b>（置信度与正确性正相关：$\rho_j\ge p_j$，且在正概率集合上严格）下，</p>
$$\mathbb{E}[p_{i,t}\mid\mathcal{F}_{t-1}]\;\ge\;p_{i,t-1}.$$
<p>条件：同质、全连接，且校准后置信度与正确性正相关。</p>
<h3>方法与是否黑盒</h3>
<ul>
<li><b>多样化初始化</b>：采样 $N_{\text{cand}}=10$ 个候选，贪心选出 5 个使答案种类最多（免训练，但多采样）。</li>
<li><b>置信调制辩论</b>：agent 输出 0–10 的口头置信度，并用 GRPO + LoRA（rank 64）训练表达与使用置信度。表达奖励 $r_{\text{conf}}=\frac{\lambda}{R_{\max}}\big[z\,\log w+(1-z)\,\log(1-w)\big]$，总奖励 $r_{\text{total}}=\lambda_1 z+\lambda_2 r_{\text{conf}}$。<b>需要训练，不是免训练方法。</b></li>
</ul>
<h3>结果（Table 1，部分）</h3>
<table>
<tr><th>Qwen-2.5-7B</th><th>GSM8K</th><th>CSQA</th><th>MMLU-PM</th><th>GPQA</th></tr>
<tr><td>单 agent</td><td>0.908</td><td>0.784</td><td>0.765</td><td>0.298</td></tr>
<tr><td>普通辩论 5×5</td><td>0.847</td><td>0.727</td><td>0.734</td><td>0.339</td></tr>
<tr><td>多数投票</td><td>0.908</td><td>0.808</td><td>0.806</td><td>0.335</td></tr>
<tr><td>仅多样化初始化</td><td>0.920</td><td>0.836</td><td>0.822</td><td>0.334</td></tr>
<tr><td>仅置信加权</td><td>0.910</td><td>0.810</td><td>0.818</td><td>0.350</td></tr>
<tr><td>多样化 + 置信</td><td><b>0.932</b></td><td>0.828</td><td>0.825</td><td><b>0.361</b></td></tr>
</table>
<p>并非处处获胜：Llama 上仅多样化的 GSM8K 为 0.863，低于多数投票 0.870；Qwen ARC-C 上仅置信（0.911）优于组合（0.890）。初始多样性与增益的相关系数很弱（$r=0.070$ 与 $0.019$，$n=26{,}624$）。</p>

<h2>3. 分歧会被压成错误共识：2609.38324（2026-09）</h2>
<h3>模型（均场）</h3>
<p>$N$ 个 agent，二元私人信念 $z$ 与公开陈述 $y$（1 表示正确），每个 agent 看到 $q$ 个随机邻居（$q\ge3$ 才出现阈值）。每个人初始正确的概率为 $p$。更新规则：</p>
<ul>
<li>可见多数与自己的信念一致：照说自己的信念。</li>
<li>不一致：以概率 $c$ <b>压制异议</b>，说多数的答案，再以概率 $a$ <b>内化</b>它；以概率 $1-c$ 说出自己的信念，并以概率 $\rho d$（$d$ 为可见异议比例）重新考虑，重新考虑后正确的概率为 $r$。</li>
</ul>
<p>定义净纠正率</p>
$$\gamma\equiv\rho\,(2r-1).$$
<h3>临界条件（Section 2.2，Appendix A.1）</h3>
<p>在全错状态 $(Z,Y)=(0,0)$ 附近，多数正确项是 $O(Y^2)$，系统线性化为 $Z_{t+1}=\Lambda(c)\,Z_t$，其中</p>
$$\Lambda(c)=1-c\,a+(1-c)\,\gamma .$$
<p>正确的少数派增长，当且仅当 $(1-c)\gamma>c\,a$，令 $\Lambda=1$ 得临界压制率（Eq.6）：</p>
$$\boxed{\,c^{*}=\frac{\gamma}{\gamma+a}\,}$$
<ul>
<li>$a\to0$ 时 $c^*\to1$：只压制、不内化，不会锁定错误共识。</li>
<li>$r>1/2$（即 $\gamma>0$）时，全正确状态对任意 $c$ 都稳定。</li>
<li>$c>c^*$ 时两个稳定态共存，由 $p$ 决定去向；相变点 $p^*(c)$ 用数值求得，略早于 $c^*$。“恢复区间”是 $p^*(c)<p<1/2$。</li>
</ul>
<div class="note"><b>性质</b>：这是线性化得到的一阶局部阈值，不是全局定理；作者承认“重新考虑与可见异议成正比”这一前提无法从日志识别，私人答案只是操作性测量。附录 A.2 用数值验证了闭式与模拟一致。</div>
<h3>什么能提高讨论的增益（Section 4，Appendix C.1）</h3>
<ul>
<li><b>提示“如实回答”</b>压低 $c$；强调“团队凝聚”的提示抬高 $c$，增益变小。</li>
<li><b>关闭推理</b>：对压制率没有稳定影响，但降低内化率 $a$，于是 $\gamma$ 与 $c^*$ 上升，增益上升。</li>
<li><b>强制 $c=1$</b> 几乎消除增益；强制 $c=0$ 只对 gpt-4o-mini 提高了增益。</li>
<li>增益的比较基线是同一聚合规则在第 0 轮（独立投票）的准确率，在 HiddenBench（65 题）、hidden profile（120 题）、MuSiQue、MedEInst 上评估。具体增益数字在原文图 2d–g，抽取文本里没有。</li>
</ul>

<h2>4. 博弈论视角：2510.20963《When and Why Does MAD Fail》</h2>
<p>设两位辩手 A、B 持有相反答案，裁判 $J$ 看原始回答 $X_0$ 与辩论消息 $M$。辩论有用当且仅当</p>
$$I(Y;M\mid X_0)>0 .$$
<table>
<tr><th>协议</th><th>建模</th><th>结论</th></tr>
<tr><td>竞争式 CopMAD</td><td>零和 + 廉价谈话（Prop.2.4）</td><td>均衡为“胡说”，风险 $V_{\text{cop}}=R_0$，等于不辩论的贝叶斯风险</td></tr>
<tr><td>共识式 CosMAD</td><td>辩手共享“达成一致”的效用（Prop.2.6）</td><td>只保留一致部分会丢信息：$R(X_0,\Phi\cap(M))\ge R(X_0,M)$，分歧含信息时严格</td></tr>
<tr><td>协作式 ColMAD</td><td>共享“求真”效用，非零和（Prop.2.8）</td><td>$V_{\text{col}}\le R(X_0)$，当 $I(Y;M_e\mid X_0)>0$ 时严格</td></tr>
</table>
$$\text{Cor.2.9：}\quad V_{\text{col}}\;\le\;V_{\text{cos}}\;\le\;R(X_0)=V_{\text{cop}}.$$
<div class="note"><b>注意</b>：Prop.2.8 的界主要来自“裁判可以忽略记录”，所以保证的是<b>不比单 agent 差</b>，不保证更好；是否有增益取决于消息的实际信息量。</div>
<h3>实验（错误检测，Table 1，Avg F2；GPT-4o-mini + Llama3.1-70B）</h3>
<table>
<tr><th>设置</th><th>Avg F2</th></tr>
<tr><td>单 agent：GPT-4o-mini / Llama3.1-70B / DeepSeek-R1</td><td>82.20 / 81.70 / 74.11</td></tr>
<tr><td>CopMAD / CosMAD / 投票</td><td>57.34 / 75.40 / 81.49</td></tr>
<tr><td><b>ColMAD</b></td><td><b>86.29</b></td></tr>
</table>
<ul>
<li>同等预算（约 14.7K token）：ColMAD 86.29，自一致性 81.98（GPT-4o-mini）、77.36（Llama）。</li>
<li>10 个随机种子下，只有 ColMAD 的 95% 置信区间同时排除两种单 agent（事实核查与平均 F2）。</li>
<li>关键设计：<b>异构辩手</b>（跨家族的组合才有明显收益，同家族改善很小）、<b>非零和框架</b>（两位都求真，互相补充）、<b>引文式证据核对</b>（精确匹配）。</li>
<li>实现是提示词级，论文说明当前不依赖 logprob，也没有训练。GSM8K 已接近饱和（约 90%），收益接近零。</li>
</ul>

<h2>5. 救回与带偏的拆分：2606.02866《When Helping Hurts》（2026-06）</h2>
<p>对一个条目：$p_g$ 是生成器本来就对的概率，$p_c$ 是批评者能识别出错误的概率，$p_r$ 是修正后变对的概率。辩论对该条目有益，当且仅当“救回”大于“带偏”（Eq.1）：</p>
$$(1-p_g)\,p_c\,p_r\;>\;p_g\,(1-p_c).$$
<p>等价的赔率形式：</p>
$$\frac{p_c}{1-p_c}\,p_r\;>\;\frac{p_g}{1-p_g}.$$
<p>任务级近似（Eq.2）：</p>
$$\Delta\mathrm{Perf}(T)\;\approx\;k\,\alpha\,[\cdots]\,(1-\rho\beta),$$
<p>其中 $k$ 为条目数，$\alpha$ 为批评被采纳的比例，$\rho$ 为输出依赖度，$\beta$ 为级联严重度（报告 AutoDCWorkflow 约 1.3，MaTElDa 约 0）。</p>
<div class="note"><b>性质</b>：这是推出来的判据，不是严格定理，完整推导在附录 L（我没读到）；$p_r$ 按答案空间类型粗取约 1.0 / 0.5 / 0.2，$p_c$ 常用代理量。</div>
<h3>有效的做法（数据清洗任务；Section 6–7，Table 9）</h3>
<table>
<tr><th>设置</th><th>结果</th></tr>
<tr><td>MaTElDa：自一致性 SC-5 / 单 agent / 辩论（F1）</td><td>0.176 / 0.191 / 0.465</td></tr>
<tr><td>纯文本对抗辩论（Claude，功能正确率）</td><td>下降 7.0 pp（显著）</td></tr>
<tr><td>+ 代码执行的批评者</td><td>0.817 对 0.814（持平，不显著）</td></tr>
<tr><td>+ 代码执行 + 证据门控</td><td><b>0.867 对 0.814（+5.3 pp，$p<0.05$，$n=84$）</b></td></tr>
<tr><td>单 agent + 同样的沙箱（无独立批评者）</td><td>0.801（−1.3 pp，不显著）</td></tr>
</table>
<p>作者归因：自我验证时 $p_c\approx p_g$，所以收益需要“对抗式分离 + 有依据的验证”两者同时具备。全程温度 0，无 token 概率，无训练。论文<b>没有</b>测试情感标注；它自己指出主观判断任务的效果混杂或为负。</p>

<h2>6. 经验分析：2605.09618《Statistical Scouting》（2026-05）</h2>
<p>在同一个 960 token 上限下比较三种协议：贪心（直接回答）、三次采样投票、两 agent 批评-修正辩论；模型为 Llama 3.1 8B 与 Ministral 3 8B，任务为 MuSiQue 与 GSM8K。没有形式化定理，主要结果：</p>
<ul>
<li>让一个“每条样本选对协议”的 oracle：在 MuSiQue 上比最好的固定协议高 +14.0 与 +13.7 pp（给出路由的上限）。</li>
<li>投票熵阈值控制器（三条链全不一致，$H>1$，才升级为辩论）：</li>
</ul>
<table>
<tr><th>模型</th><th>最好固定协议</th><th>阈值控制器</th><th>$\Delta$（pp）</th><th>95% CI（配对 bootstrap）</th></tr>
<tr><td>Llama 3.1 8B</td><td>43.7</td><td>45.0</td><td>+1.3</td><td>[−3.7, +5.3]</td></tr>
<tr><td>Ministral 3 8B</td><td>49.0</td><td>50.7</td><td>+1.7</td><td>[−1.7, +4.0]</td></tr>
</table>
<ul>
<li>联合检验：固定效应 meta 分析 $+1.6$ pp（$p=0.125$），Fisher 合并 $p=0.22$，<b>不显著</b>；学习型控制器没有超过阈值。</li>
<li>投票熵只能预测辩论<b>安全</b>（$H$ 高时反噬少），不能预测辩论<b>有用</b>（帮助率各层大致持平）。47 个辩论有益样本中，31 个（66%）属于 $H\le1$，其中全票一致且错误 17 个（约 36%）。</li>
<li>“一次性 CHANGE/KEEP 探针”在 127/127 个全票一致样本上都翻转，与辩论是否有益的互信息为零（作者提示可能是提示遵从的假象）。</li>
<li>作者的限制：两个约 8B 模型、两类 QA、$N=300$、只控制 token 上限而非实际消耗（辩论实际消耗更多）、所有个别 CI 都跨 0。</li>
</ul>

<h2>7. 一页对照</h2>
<table>
<tr><th>论文</th><th>核心公式 / 结论</th><th>什么能超过多数投票或直接回答</th><th>是否黑盒、免训练</th></tr>
<tr><td>2508.17536</td><td>$\mathbb{E}[p_t\mid\mathcal{F}_{t-1}]=p_{t-1}$（鞅）</td><td>没有：实用变体 0.763 &lt; 投票 0.769</td><td>黑盒、免训练</td></tr>
<tr><td>2601.19921</td><td>置信加权次鞅：$\mathbb{E}[p_t\mid\mathcal{F}_{t-1}]\ge p_{t-1}$</td><td>多样化 + 置信，GSM8K 0.932 对 0.908</td><td>多样化免训练；置信加权<b>需训练</b></td></tr>
<tr><td>2609.38324</td><td>$c^*=\gamma/(\gamma+a)$</td><td>不压制异议、关闭推理</td><td>提示词，黑盒、免训练</td></tr>
<tr><td>2510.20963</td><td>$V_{\text{col}}\le V_{\text{cos}}\le R(X_0)=V_{\text{cop}}$</td><td>ColMAD 86.29 对 82.20</td><td>提示词，黑盒、免训练；需异构模型</td></tr>
<tr><td>2606.02866</td><td>$(1-p_g)p_cp_r>p_g(1-p_c)$</td><td>代码执行批评者 + 证据门控，+5.3 pp</td><td>黑盒、免训练；需可执行验证对象</td></tr>
<tr><td>2605.09618</td><td>无定理；熵只预测“安全”</td><td>阈值控制器 +1.6 pp，不显著</td><td>黑盒、免训练</td></tr>
</table>

<h2>8. 局限</h2>
<ul>
<li>抓取工具按字数截断，未读到的部分：2609.38324 附录 C 后段，2601.19921 的 Lemma 2 证明，2510.20963 附录 F 表格，2508.17536 附录 D.3.2 之后，2606.02866 附录 L。</li>
<li>数字来自抓取工具的提取，没有逐一对照原表；关键公式（$c^*$、Eq.1、Thm.1）建议读 PDF 复核。</li>
<li>所有论文的任务都是 QA、数学或错误检测，没有情感或多模态分类；模型多为 7B–70B。</li>
<li>没有一篇论文在“分歧子集”上单独报告辩论超过 Direct。</li>
</ul>
<p class="muted">来源：arXiv:2508.17536（v2）、2601.19921（v3）、2609.38324（v1）、2510.20963（v2）、2606.02866（v1）、2605.09618（v1）。</p>
"""


def build():
    html = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>辩论论文的理论与方法总结（公式渲染版）</title><style>{CSS}</style></head><body>'
            f'{render_math(BODY)}</body></html>')
    out = ROOT / 'docs/mad-debate-papers-math.html'
    out.write_text(html, encoding='utf8')
    print('wrote', out, out.stat().st_size, 'bytes; math nodes:', html.count('<math'))


if __name__ == '__main__':
    build()
