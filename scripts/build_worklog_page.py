"""Build docs/work-log-20261102-03.html: what was done on 2026-11-02 and 2026-11-03, with the tables of this work consolidated.

Facts come from update.md, metrics/findings_log.md, LOCAL_WORKSPACE.md and the saved metrics files; the v4 numbers are read
from metrics/reflect_debate_v4_*.json. Static HTML, no scripts, no model calls.
Usage: python scripts/build_worklog_page.py
"""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = {(p, s): json.loads((ROOT / 'metrics' / (f'reflect_debate_v4_{p}.json' if s == 'validation' else f'reflect_debate_v4_{p}_{s}.json')).read_text(encoding='utf8'))
     for p in ['gemini', 'gpt'] for s in ['validation', 'train', 'all']}


def st(p, s, k):
    return M[(p, s)]['stats'].get(k, 0)


def rt(p, s, route, k):
    return M[(p, s)]['by_route'].get(route, {}).get(k, 0)


def table(head, rows, cls=None):
    out = '<table><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr>'
    for r in rows:
        out += '<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>'
    return out + '</table>'


css = '''body{font:15px/1.65 "Microsoft YaHei",sans-serif;max-width:1180px;margin:24px auto;padding:0 18px;color:#222;background:#fafafa}
h1{font-size:24px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:18px 0 6px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 18px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}th,td{border:1px solid #ccc;padding:4px 8px;text-align:left;vertical-align:top}th{background:#eef}
.muted{color:#666}.small{font-size:13px}.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}
.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}code{background:#eee;padding:0 4px;border-radius:3px}'''

P = []
P.append('<h1>工作记录与表格汇总（2026-11-02 至 2026-11-03）</h1>')
P.append('<p class="muted">整理自 <code>update.md</code>、<code>metrics/findings_log.md</code>、<code>LOCAL_WORKSPACE.md</code> 和已保存的指标文件；v4 数字由 <code>metrics/reflect_debate_v4_*.json</code> 读出。所有结果都基于 MER2024 40 + MELD 40 的验证集（反复用于开发，不是独立证据）；训练集 320 条只用于 v4 的复核。昨天指 2026-11-02。</p>')

# ------------------------------------------------------------------ timeline
P.append('<section class="panel"><h2>一、时间线</h2><h3>2026-11-02（昨天）：理解现状、分析错误、调研辩论、做出条件辩论实验与自进化设计</h3>')
P.append(table(['内容', '产出', '关键事实'], [
    ['本机工作区迁入与核对', '<code>LOCAL_WORKSPACE.md</code>', '5,871 个受版本控制文件；46 个源码/指标文件哈希匹配；与服务器抽查的 27 个文件一致；未启动推理。'],
    ['PPCT 流程页与“方案 A”（去掉组织文本末尾心理推断）', '<code>docs/ppct-flow.html</code>', 'Gemini PPCT 预测 neutral 30 条（真实 13，Direct 19）；更正：组织文本“无法明确心理状态”GPT 75/80、Gemini 0/80（此前 77/5 是关键词误匹配）。'],
    ['分析统计文档', '<code>metrics/analysis_stats_20261102.md</code>', 'Direct→PPCT 配对（McNemar）、neutral 预测次数、各角色 ACC、三专家一致时汇总器表现。'],
    ['v3 GPT 各阶段输出可视化页', '<code>docs/v3-gpt-stages.html</code>', 'GPT v3 汇总器答错 24 条：仅 4 条“有专家答对而汇总答错”，20 条三位同错；三专家完全一致 65/80，其中 15 条一致地错。'],
    ['混淆矩阵页', '<code>docs/confusion-matrices.html</code>', 'GPT+Gemini 合并：MER2024 错判 109/400（surprise→worried 24、angry→worried 24），MELD 146/400（disgust→anger 23）；混淆多为稀有类被吸收进常见类，Direct 中同样存在。'],
    ['v3 情绪轮提示词去向页', '<code>docs/v3-prompt-wheel.html</code>', '情绪轮只进入专家与汇总器的系统提示词；只有 v3 带情绪轮，worried 过度预测在 Direct/PPCT/v1/v2 同样出现，不能归因于该规则（更正此前表述）。'],
    ['Agent Debate 调研页', '<code>docs/agent-debate-survey.html</code>', '三专家多数投票 GPT 57、Gemini 59、Omni 55（77 有效），不低于汇总器 56/56/54；触发辩论比例 19%/26%/43%。'],
    ['条件辩论实验（三次）', '<code>scripts/run_conditional_debate.py</code>；<code>metrics/*_conditional_debate_v4_*.json</code>', '一致则直接采纳，不一致才辩论；Gemini 文本 59、Gemini 带媒体 58、GPT 带媒体 56；辩论等价于多数投票。见表 T2。'],
    ['辩论 vs 投票对比页', '<code>docs/debate-vs-vote.html</code>', '辩论与投票结果不同的样本三次合计 5 条（改对 1、改错 3、都错 1）；其余 52 条触发样本辩论只是重复确认多数派；对的少数派被说服到多数。'],
    ['Orchestra 类工作调研页', '<code>docs/agent-orchestration-survey.html</code>', '四类编排方法 + 高引用文献表（Semantic Scholar 快照）；已标注核实程度，撤稿论文未收入。'],
    ['候选集统计与页（F1）', '<code>docs/expert-union-confusable.html</code>；F1', '专家答案集合 ∪ 第 1 个易混淆标签：覆盖率 GPT 75.0%→82.5%、Gemini 78.8%→83.8%，只比随机多 1–2 条。见表 T3。'],
    ['同模型 vs 跨模型互补性（F2）', '<code>metrics/findings_log.md</code>', '同模型三角色错误高度相关；跨模型更互补（九位并集 92.2%）。见表 T4。'],
    ['MCIL 论文阅读与自进化设计', '<code>docs/self-evolving-interactive-design.html</code>、<code>docs/self-evolving-training-explained.html</code>', '训练免费版：冻结模型，只训练校准偏置 b 与融合权重 w；仅设计，未实现、未运行、无成绩。'],
    ['辩论方案修订图', '<code>docs/agent-debate-survey.html</code> 第七节', '用户确认的流程：第一次独立判断（可 1–2 个答案）→ 一律反思 → 有恰好 1 个共同标签则输出，否则辩论 → 汇总。'],
]))
P.append('<h3>2026-11-03（今天）：命名 v4、写提示词、审核、实现、跑 80 条与 400 条、分析原因</h3>')
P.append(table(['时间', '内容', '产出', '关键事实'], [
    ['00:00 前后', '命名 v4；用户确认“共同标签可由备选凑出”没有关系；起草 v4 提示词', '<code>versions/v4/</code>；<code>docs/v3-v4-prompt-diff.html</code>', '先给 v3/v4 提示词差异供审核，审核后才运行。'],
    ['审核', '用户 4 点意见：提示词不出现 v3/v4；辩论提示词写输出格式并要求改变观点时引用证据；汇总器删“按人数投票”、evidence_refs 考虑多位专家；减少禁止语', '提示词与差异页修订', 'v3 原文里的禁止语未改（约 15 处/提示词），待用户决定。'],
    ['00:37–00:59', '实现 <code>versions/v4/pipeline.py</code>；冒烟；跑 Gemini、GPT 各 80 条', '服务器 <code>outputs/reflect_debate_v4/</code>；F3', '80/80 成功，0 回退，约 22 分钟。见表 T6。'],
    ['约 00:59–04:33', '训练集 320 条先用原 PPCT + Gemini 生成图谱（约 1 小时 50 分，0 失败），再各跑 v4 400 条（并发 4）', '<code>data/gemini_graph_train_v4</code>；<code>scripts/gen_train_graphs.py</code>；F4', '400/400 成功，0 回退。见表 T7。'],
    ['今天', '整理工作记录；分析 80 条为什么效果不好', '本页；<code>docs/v4-80-debate-analysis.html</code>；<code>scripts/analyze_v4_debate_80.py</code>', '大多数错误是三位专家同错、不进入辩论；辩论路径≈多数投票，少数派全部改口。'],
]))
P.append('</section>')

# ------------------------------------------------------------------ tables
P.append('<section class="panel"><h2>二、汇总表格</h2>')
P.append('<h3>T1　各方法在 80 条验证集上的成绩（ACC）</h3>')
P.append(table(['方法', 'GPT', 'Gemini', 'Omni'], [
    ['Direct', '65.00%（52/80）', '75.00%（60/80）', '72.50%'],
    ['原 PPCT', '77.50%（62/80）', '67.50%（54/80）', '68.75%'],
    ['v1（固定图谱 + 隔离三专家）', '56.25%', '66.25%', '未完成，70/80'],
    ['v2（专家共享原媒体）', '63.75%', '70.00%', '未完成，76/80'],
    ['v3（情绪轮 + 开放情绪）汇总器', '70.00%（56/80）', '70.00%（56/80）', '未完成，77/80'],
    ['v3 三专家多数投票（平票算错）', '57/80', '59/80', '55（77 有效）'],
    ['<b>v4 最终</b>', f'<b>{st("gpt", "validation", "v4 final")}/80</b>', f'<b>{st("gemini", "validation", "v4 final")}/80</b>', '未跑'],
]))
P.append('<p class="small muted">来源：<code>LOCAL_WORKSPACE.md</code> 与已保存的逐样本结果；v4 为 2026-11-03 的新结果。Omni 的 v1/v2/v3 因失败样本未完成，不报告完整 80 条 ACC。</p>')

P.append('<h3>T2　条件辩论 vs 投票（v3 专家输出为第 0 轮，80 条）</h3>')
P.append(table(['运行', 'v3 汇总器', '三专家多数投票', '辩论 R=1 / R=2 / R=2+裁判', '触发辩论的样本'], [
    ['Gemini · 纯文本', '56', '59', '59 / 59 / 59', '21 条（26%）'],
    ['Gemini · 带原媒体', '56', '59', '— / — / 58', '21 条'],
    ['GPT · 带原媒体', '56', '57', '57 / 56 / 56', '15 条（19%）'],
]))
P.append('<p class="small muted">来源：<code>update.md</code> 中 2026-11-02 三条记录。Gemini 纯文本：21 条的最终答案全部等于第 0 轮多数派。</p>')

P.append('<h3>T3　F1：候选集 E ∪ 第 1 个易混淆标签的覆盖率</h3>')
P.append(table(['模型', '只看 E', 'E ∪ k=1', '随机加 1 个期望', 'E ∪ k=2', '随机加 2 个期望'], [
    ['GPT', '60/80（75.0%）', '66/80（82.5%）', '63.8', '68/80（85.0%）', '67.6'],
    ['Gemini', '63/80（78.8%）', '67/80（83.8%）', '66.3', '72/80（90.0%）', '69.6'],
]))
P.append('<p class="small muted">覆盖率只是上限，只比随机多 1–2 条，属于噪声量级。</p>')

P.append('<h3>T4　F2：同模型三角色 vs 跨模型专家</h3>')
P.append(table(['成员组合', '成员准确率', '多数投票', '任一成员答对', 'Fleiss κ', '两两给出同一错答案'], [
    ['GPT 三角色（80）', '54–59', '57', '60（75.0%）', '0.86', '22.1%'],
    ['Gemini 三角色（80）', '54–59', '59', '63（78.8%）', '0.80', '18.8%'],
    ['跨模型·图谱专家（77）', '51–57', '58', '67（87.0%）', '0.65', '10.8%'],
    ['跨模型·音频字幕专家（77）', '52–56', '56', '68（88.3%）', '0.63', '11.7%'],
    ['跨模型·图像专家（77）', '52–54', '54', '66（85.7%）', '0.65', '12.6%'],
    ['GPT + Gemini + Omni 九位（77）', '51–57', '61', '71（92.2%）', '0.67', '12.9%'],
]))

P.append('<h3>T5　v4 流程与相对 v3 的变化</h3>')
P.append(table(['环节', '相对 v3', '说明'], [
    ['组织文本、三位专家的四条 rubric、情绪轮、易混边界', '不变', '验证集的组织文本直接复用同模型已保存输出；训练集按相同提示词新生成。'],
    ['Round 0 专家', '改', '默认 1 个答案；真正两难时可再给 1 个备选（alt_answer / alt_open_emotion / uncertainty_reason）。'],
    ['反思（新增，每条样本）', '新增', '只看原媒体与自己的 Round 0 输出；核对证据、找最强反证、检查映射；仍允许 1–2 个答案。'],
    ['路由（代码）', '新增', '三位答案集合的交集恰好 1 个标签 → 直接输出；否则辩论。'],
    ['辩论（≤2 轮）', '新增', '读另两位反思后的完整输出；改自己需引用对方证据（adopted_evidence），劝对方需带可定位证据；答案限定在候选并集内。'],
    ['汇总器', '小改', '只在辩论后仍不一致时调用；evidence_refs 汇集三位专家任一阶段的证据（角色:阶段:E编号）。'],
]))

P.append('<h3>T6　v4 在 80 条验证集上的结果</h3>')
P.append(table(['指标', 'Gemini', 'GPT'], [
    ['v4 最终', f'{st("gemini", "validation", "v4 final")}（{100 * st("gemini", "validation", "v4 final") / 80:.2f}%）', f'{st("gpt", "validation", "v4 final")}（{100 * st("gpt", "validation", "v4 final") / 80:.2f}%）'],
    ['v3 汇总器 / v3 专家多数投票', '56 / 59', '56 / 57'],
    ['Round 0 主答案多数投票 / 反思后多数投票', f'{st("gemini", "validation", "r0 primary majority (ties wrong)")} / {st("gemini", "validation", "reflect primary majority (ties wrong)")}', f'{st("gpt", "validation", "r0 primary majority (ties wrong)")} / {st("gpt", "validation", "reflect primary majority (ties wrong)")}'],
    ['直接输出（共同标签）样本 / 答对', f'{rt("gemini", "validation", "common_label", "n")} / {rt("gemini", "validation", "common_label", "correct")}', f'{rt("gpt", "validation", "common_label", "n")} / {rt("gpt", "validation", "common_label", "correct")}'],
    ['辩论后一致 样本 / 答对', f'{rt("gemini", "validation", "debate_consensus", "n")} / {rt("gemini", "validation", "debate_consensus", "correct")}', f'{rt("gpt", "validation", "debate_consensus", "n")} / {rt("gpt", "validation", "debate_consensus", "correct")}'],
    ['进入汇总器', '0', '0'],
    ['反思改变主答案的专家次数（共 240）', str(st('gemini', 'validation', 'reflect changed primary')), str(st('gpt', 'validation', 'reflect changed primary'))],
    ['Round 0 给备选的专家次数', str(st('gemini', 'validation', 'experts giving a backup (r0)')), str(st('gpt', 'validation', 'experts giving a backup (r0)'))],
    ['真实标签在 Round 0 主答案内 / 含备选的候选并集内', f'{st("gemini", "validation", "gold in r0 primaries")} / {st("gemini", "validation", "gold in candidate union")}', f'{st("gpt", "validation", "gold in r0 primaries")} / {st("gpt", "validation", "gold in candidate union")}'],
]))

P.append('<h3>T7　v4 扩大到 400 条（训练 320 + 验证 80）</h3>')
rows7 = []
for name, key in [('v4 最终', 'v4 final'), ('Round 0 主答案多数投票', 'r0 primary majority (ties wrong)'), ('反思后多数投票', 'reflect primary majority (ties wrong)')]:
    rows7.append([name] + [f'{st(p, s, key)}' for p in ['gemini', 'gpt'] for s in ['train', 'all']])
for name, route in [('直接输出 样本 / 答对', 'common_label'), ('辩论后一致 样本 / 答对', 'debate_consensus'), ('汇总器 样本 / 答对', 'summary')]:
    rows7.append([name] + [f'{rt(p, s, route, "n")} / {rt(p, s, route, "correct")}' for p in ['gemini', 'gpt'] for s in ['train', 'all']])
P.append(table(['指标', 'Gemini 训练 320', 'Gemini 全部 400', 'GPT 训练 320', 'GPT 全部 400'], rows7))
P.append('<p class="small muted">训练集样本由模型正确性筛选而来，没有训练集的 Direct / v3 对照；训练集从未用于 v4 的提示词或规则开发。</p>')

P.append('<h3>T8　产出文件</h3>')
P.append(table(['类型', '文件'], [
    ['静态页（docs/）', 'ppct-flow、v3-gpt-stages、confusion-matrices、v3-prompt-wheel、agent-debate-survey、agent-orchestration-survey、debate-vs-vote、expert-union-confusable、self-evolving-interactive-design、self-evolving-training-explained、v3-v4-prompt-diff、v4-80-debate-analysis、work-log-20261102-03（本页）'],
    ['代码', '<code>versions/v4/{pipeline,emotion_wheel_prompts,prompts_base}.py</code>、<code>scripts/{gen_train_graphs,run_v4_400.sh,analyze_v4_debate_80,build_*}.py</code>、<code>scripts/run_conditional_debate.py</code>'],
    ['指标与台账', '<code>metrics/findings_log.md</code>（F1–F4）、<code>metrics/reflect_debate_v4_*.json</code>、<code>metrics/v4_val80_debate_analysis.json</code>、<code>metrics/analysis_stats_20261102.md</code>'],
    ['服务器输出', '<code>outputs/reflect_debate_v4/{gemini,gpt}</code>、<code>data/gemini_graph_train_v4</code>（均在服务器，未提交到本机 Git）'],
]))
P.append('</section>')

# ------------------------------------------------------------------ corrections and open items
P.append('<section class="panel"><h2>三、更正记录与未决事项</h2><h3>已更正的说法</h3>')
P.append(table(['说法', '更正'], [
    ['“组织文本弃权 GPT 77/80、Gemini 5/80”', '关键词误匹配；严格口径 GPT 75/80、Gemini 0/80。'],
    ['“v3 的 fear 规则影响所有方法”', '情绪轮只有 v3 带；v1/v2 提示词无，worried 过度预测在 Direct/PPCT/v1/v2 同样出现。'],
    ['把某个已列入的文献说成“ChatDev 已列”', '已修正调研页。'],
    ['汇总缓存导致的旧裁判结果', 'judge.json 增加 rounds 字段，缓存按轮数校验。'],
]))
P.append('<h3>未决事项</h3><ul>'
         '<li>v3 原文里的禁止语（约 15 处/提示词）是否也改成正向写法，需要你决定；改了就不再是“只改流程”的对照。</li>'
         '<li>自进化设计（冻结模型，训练校准偏置与融合权重）仍是设计，没有实现；训练集现在已有 Gemini 图谱和 v4 的 Round 0/反思输出，但三模型 v3 专家和 Omni 没有跑。</li>'
         '<li>v4 没有在 Omni 上跑；训练集没有 Direct / v3 对照。</li>'
         '<li>为什么 v4 效果不好的分析见 <code>docs/v4-80-debate-analysis.html</code>；其中“改进方向”都是未验证的假设。</li></ul></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>工作记录与表格汇总</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'work-log-20261102-03.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
