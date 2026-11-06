"""Build docs/v6-rmad-retrieval.html: how good is the R2-MAD (v6) retrieval on the test set? Static HTML, no scripts, no model calls.
Data (read-only, produced on the server with bge-m3 on CPU, no LLM call):
  metrics/v6_rmad_retrieval_analysis.json  (versions/v6/analyze_retrieval.py: every retrieval rebuilt and checked against the log)
  metrics/v6_rmad_retrieval_extra.json     (random baselines for top-k, label agreement split by whether the expert's own answer was right)
Usage: python scripts/build_v6_rmad_retrieval_page.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = json.loads((ROOT / 'metrics' / 'v6_rmad_retrieval_analysis.json').read_text(encoding='utf8'))
X = json.loads((ROOT / 'metrics' / 'v6_rmad_retrieval_extra.json').read_text(encoding='utf8'))
PROV = [('gemini', 'Gemini'), ('gpt', 'GPT')]
VARS = ['n1', 'n2', 'n3']


def pct(a, b, d=0):
    return f'{100 * a / b:.{d}f}%' if b else '–'


def row_cells(cells):
    return '<tr>' + ''.join(cells) + '</tr>'


def t_overview():
    head = ('<tr><th>模型</th><th>变体</th><th class="n">检索次数</th><th class="n">复现一致</th><th class="n">取回案例</th>'
            '<th class="n">案例标签 = 真实标签</th><th class="n">随机挑标签</th><th class="n">按库内标签占比猜</th>'
            '<th class="n">案例标签 = 专家自己的答案</th><th class="n">案例标签在候选里</th><th class="n">案例本身答对</th></tr>')
    rows = []
    for p, name in PROV:
        for v in VARS:
            c = A[p]['variants'][v]['counts']
            n = c['cases']
            rows.append(row_cells([f'<td>{name}</td>', f'<td>{v}</td>', f'<td class="n">{c["queries"]}</td>', f'<td class="n">{c["reproduced"]} / {c["queries"]}</td>',
                                   f'<td class="n">{n}</td>', f'<td class="n hi">{pct(c["case_label_eq_gold"], n)}</td>', f'<td class="n">{pct(c["chance_eq_gold"], n)}</td>',
                                   f'<td class="n">{pct(c["prior_eq_gold"], n)}</td>', f'<td class="n">{pct(c["case_label_eq_own_answer"], n)}</td>',
                                   f'<td class="n">{pct(c["case_label_in_union"], n)}</td>', f'<td class="n">{pct(c["case_correct"], n)}</td>']))
    return '<table>' + head + ''.join(rows) + '</table>'


def t_rank():
    head = ('<tr><th rowspan="2">模型</th><th rowspan="2">变体</th><th colspan="2">相似度排第 1 的案例</th><th colspan="2">前 3 名里有</th><th colspan="2">前 9 名里有</th>'
            '<th rowspan="2" class="n">实际取回的案例<br>= 真实标签</th><th rowspan="2" class="n">库的大小<br>（同专家同数据集）</th></tr>'
            '<tr><th class="n">= 真实标签</th><th class="n">随机</th><th class="n">真实标签</th><th class="n">随机</th><th class="n">真实标签</th><th class="n">随机</th></tr>')
    rows = []
    for p, name in PROV:
        for v in VARS:
            o = A[p]['variants'][v]['oracle_rank']
            c = A[p]['variants'][v]['counts']
            e = X[f'{p}_{v}']
            q = o['n']
            rows.append(row_cells([f'<td>{name}</td>', f'<td>{v}</td>',
                                   f'<td class="n hi">{pct(o["within_top1"], q)}</td>', f'<td class="n">{pct(e["rand_top1"], e["q"])}</td>',
                                   f'<td class="n">{pct(o["within_top3"], q)}</td>', f'<td class="n">{pct(e["rand_top3"], e["q"])}</td>',
                                   f'<td class="n">{pct(o["within_top9"], q)}</td>', f'<td class="n">{pct(e["rand_top9"], e["q"])}</td>',
                                   f'<td class="n">{pct(c["case_label_eq_gold"], c["cases"])}</td>', f'<td class="n">{o["mean_slice"]:.0f}</td>']))
    return '<table>' + head + ''.join(rows) + '</table>'


def t_sim():
    head = '<tr><th>模型</th><th>变体</th><th>相似度四分位（低 → 高）：区间与“案例标签 = 真实标签”的比例</th><th class="n">命中案例的平均相似度</th><th class="n">未命中</th></tr>'
    rows = []
    for p, name in PROV:
        for v in VARS:
            x = A[p]['variants'][v]
            cells = '　'.join(f'{b["sim_from"]:.3f}–{b["sim_to"]:.3f}：<b>{100 * b["hit"]:.0f}%</b>' for b in x['sim_buckets'])
            rows.append(row_cells([f'<td>{name}</td>', f'<td>{v}</td>', f'<td>{cells}</td>', f'<td class="n">{x["sim_mean_hit"]:.3f}</td>', f'<td class="n">{x["sim_mean_miss"]:.3f}</td>']))
    return '<table>' + head + ''.join(rows) + '</table>'


def t_echo():
    head = ('<tr><th rowspan="2">模型</th><th rowspan="2">变体</th><th colspan="3">专家当前答案<b>错</b>时</th><th colspan="2">专家当前答案<b>对</b>时</th></tr>'
            '<tr><th class="n">案例数</th><th class="n">案例标签 = 专家的错答案</th><th class="n">案例标签 = 真实标签</th><th class="n">案例数</th><th class="n">案例标签 = 真实标签</th></tr>')
    rows = []
    for p, name in PROV:
        for v in VARS:
            e = X[f'{p}_{v}']
            rows.append(row_cells([f'<td>{name}</td>', f'<td>{v}</td>', f'<td class="n">{e["own_wrong_cases"]}</td>',
                                   f'<td class="n hi">{pct(e["own_wrong_eq_own"], e["own_wrong_cases"])}</td>', f'<td class="n">{pct(e["own_wrong_eq_gold"], e["own_wrong_cases"])}</td>',
                                   f'<td class="n">{e["own_right_cases"]}</td>', f'<td class="n">{pct(e["own_right_eq_own"], e["own_right_cases"])}</td>']))
    return '<table>' + head + ''.join(rows) + '</table>'


def t_move():
    head = ('<tr><th rowspan="2">模型</th><th rowspan="2">变体</th><th colspan="4">第 1 条案例的标签 ≠ 专家上一轮答案时，专家这一轮</th><th colspan="2">改成案例标签的那些</th></tr>'
            '<tr><th class="n">次数</th><th class="n">保持原答案</th><th class="n">改成案例标签</th><th class="n">改成别的标签</th><th class="n">改对</th><th class="n">原来对、改错</th></tr>')
    rows = []
    for p, name in PROV:
        for v in VARS:
            m = A[p]['variants'][v]['move']
            tot = m.get('kept', 0) + m.get('moved_to_case', 0) + m.get('moved_elsewhere', 0)
            rows.append(row_cells([f'<td>{name}</td>', f'<td>{v}</td>', f'<td class="n">{tot}</td>', f'<td class="n">{m.get("kept", 0)}</td>',
                                   f'<td class="n">{m.get("moved_to_case", 0)}</td>', f'<td class="n">{m.get("moved_elsewhere", 0)}</td>',
                                   f'<td class="n ok">{m.get("moved_to_case_right", 0)}</td>', f'<td class="n bad">{m.get("moved_to_case_wrong_from_right", 0)}</td>']))
    return '<table>' + head + ''.join(rows) + '</table>'


def t_rel():
    head = ('<tr><th>模型</th><th>变体</th><th class="n">标 high 的同伴</th><th class="n">其中实际答对</th><th class="n">标 low 的同伴</th><th class="n">其中实际答对</th><th class="n">不标</th></tr>')
    rows = []
    for p, name in PROV:
        for v in VARS:
            r = A[p]['variants'][v]['reliability']
            rows.append(row_cells([f'<td>{name}</td>', f'<td>{v}</td>', f'<td class="n">{r["high_n"]}</td>', f'<td class="n hi">{pct(r["high_peer_right"], r["high_n"])}</td>',
                                   f'<td class="n">{r["low_n"]}</td>', f'<td class="n hi">{pct(r["low_peer_right"], r["low_n"])}</td>', f'<td class="n">{r["none_n"]}</td>']))
    return '<table>' + head + ''.join(rows) + '</table>'


def agg(p, key_num, key_den='cases'):
    return sum(A[p]['variants'][v]['counts'][key_num] for v in VARS), sum(A[p]['variants'][v]['counts'][key_den] for v in VARS)


css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1180px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}
h1{font-size:25px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:18px 0 4px;color:#444}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 16px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:13.5px}th,td{border:1px solid #ccc;padding:4px 7px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}td.hi{background:#fff3da}td.ok{color:#2D6A4F;font-weight:700}td.bad{color:#C0392B;font-weight:700}
.muted{color:#666}.small{font-size:12.5px}.key{background:#eaf4ff;border-left:4px solid #48c;padding:10px 14px;margin:10px 0}
code{background:#eee;padding:0 4px;border-radius:3px}'''

gm = A['gemini']['variants']
P = []
P.append('<h1>R²-MAD（v6）的召回效果分析</h1>')
P.append('<p class="muted">日期 2026-11-06。测试集 = 旧 400 条里 v4 判为不一致的样本（Gemini 62、GPT 55）。只读已保存的结果；检索查询在服务器上用 bge-m3（CPU）重新编码，'
         '没有调用大模型。脚本 <code>versions/v6/analyze_retrieval.py</code>；数据 <code>metrics/v6_rmad_retrieval_analysis.json</code>、<code>metrics/v6_rmad_retrieval_extra.json</code>。'
         '整体结果见 <code>docs/v6-rmad-report.html</code>。</p>')

g_hit, g_n = agg('gemini', 'case_label_eq_gold')
t_hit, t_n = agg('gpt', 'case_label_eq_gold')
P.append('<section class="panel"><h2>一、结论</h2><div class="key"><ol>'
         f'<li><b>召回到的案例只比随机略有用。</b>案例的标签等于当前样本真实标签的比例：Gemini {pct(g_hit, g_n)}、GPT {pct(t_hit, t_n)}；随机挑一个标签是 15%，按库里的标签占比去猜是 13–16%。</li>'
         '<li><b>相似度排序只在第 1 名有用，往后不比随机好。</b>相似度最高的那条案例的标签等于真实标签：24–28%（随机 13–16%）；但“前 3 名里有真实标签”只有 34–36%（随机 32–35%），“前 9 名里有”56–64%（随机 59–63%）。</li>'
         '<li><b>实际取回的案例比“直接取第 1 名”还差。</b>MMR（按“相似度 × 是否答对”打分，再减去和已选案例的相似度）选出的案例只有 18–23% 命中真实标签，比直接取相似度第 1 名低 2–6 个百分点（GPT n1 只低 2 个点，Gemini n1 低 5 个点）。</li>'
         '<li><b>Gemini 的召回主要在“回声”。</b>专家当前答案错的时候，取回案例的标签等于这个错答案的有 34–35%，等于真实标签的只有 14–20%：检索把错误答案加强了约一倍。原因很可能是检索键里含有专家自己上一轮的回答（这是 R²-MAD 原版的设计）。GPT 上这个现象弱得多（21–28% 对 20–22%）。</li>'
         '<li><b>一半左右的案例标签根本不能选。</b>案例标签落在当前候选里的只有 Gemini 57–61%、GPT 39–48%；其余案例对这道题没有直接用处。</li>'
         '<li><b>专家跟着案例改答案时，Gemini 改错多于改对，GPT 改对多于改错，但次数都很少。</b>Gemini 改对 8–11 次、把原本对的改错 14–18 次；GPT 改对 8–9 次、改错 4–5 次。</li>'
         '<li><b>同伴可靠度标记几乎没有信息。</b>标 high 的同伴实际答对 38–50%，标 low 的 39–47%；GPT n1 甚至是反的。</li></ol>'
         '<p>合起来：召回本身质量很低（找不到带正确标签的案例，相似度区分不出情绪），这是 R²-MAD 在这个任务上没有效果的直接原因，而不是专家“不会用”经验。</p></div></section>')

P.append('<section class="panel"><h2>二、怎么测的</h2><ul>'
         '<li>对每条测试样本、每个变体（n1 / n2 / n3）、每轮辩论、每位专家，按 <code>run_rmad.py</code> 的做法重建检索查询：Caption + 任务说明 + 该专家上一轮的精简回答 + 上一轮的辩论状态摘要（标签名已替换），用 bge-m3 编码，再调用同一个 <code>Memory.retrieve</code>。</li>'
         '<li><b>先核对复现</b>：重算出的案例与日志里记录的案例逐条比较，1,395 次检索里 1,391 次完全一致（表 1 “复现一致”一列）；不一致的 4 次可能来自 CPU 与 GPU 编码的数值差异让相似度并列的案例换了顺序。所以下面的数字测的就是当时真实发生的检索。</li>'
         '<li>“命中”= 案例的标准标签等于当前测试样本的标准标签。标准标签只在这里读，不进任何模型请求。</li>'
         '<li>“随机挑标签”= 1 / 标签数；“按库内标签占比猜”= 该专家、该数据集的经验库里，标签等于当前真实标签的记录所占比例；“前 k 名随机”= 从这部分库里随机取 k 条，至少一条标签等于真实标签的概率。</li></ul></section>')

P.append('<section class="panel"><h2>三、取回的案例对不对</h2>' + t_overview() +
         '<p class="small muted">每行的分母是取回案例数（n2 每次 2 条、n3 每次 3 条）。“案例本身答对”= 经验库记录里该专家当时答对了（MMR 偏好这类案例），它和“案例标签 = 当前真实标签”是两回事。</p></section>')

P.append('<section class="panel"><h2>四、相似度排序有没有用</h2>' + t_rank() +
         '<p>相似度第 1 名命中真实标签的比例约是随机的 2 倍；但只要往后多看几名，命中率就和随机抽取一样。实际取回的案例（MMR 选出的）比直接取第 1 名还低。</p>' + t_sim() +
         '<p>相似度越高，命中率有所上升（最低四分位 10–17%，最高四分位 26–33%），但相似度挤在很窄的区间里（大多 0.79–0.85），命中与未命中的平均相似度只差 0.008–0.017。'
         '我猜这是因为检索键里有大量相同的模板文字（任务说明、候选标签、回答格式），让所有样本看起来都很像；这一点没有验证。</p></section>')

P.append('<section class="panel"><h2>五、召回在“加强”专家自己的答案</h2>' + t_echo() +
         '<p>检索键 = 题目 + <b>专家自己上一轮的回答</b> + 辩论摘要。于是检索更容易找到“当时那位专家也这么回答”的案例，这些案例的真实标签往往和这个回答相同。'
         'Gemini 在自己答错时，看到的案例有三分之一标签就是这个错答案，指向真实标签的不到五分之一。GPT 的这个比例接近持平，回声弱得多。</p></section>')

P.append('<section class="panel"><h2>六、专家怎么用这些案例</h2>' + t_move() +
         '<p>只统计“第 1 条案例的标签和专家上一轮答案不同”的情况。专家大多保持原答案或改成别的标签，改成案例标签的只有 15–34 次。'
         'Gemini 跟着案例改时，把原本对的改错（14–18 次）多于改对（8–11 次）；GPT 跟得更少，改对（8–9）多于改错（4–5）。这些改动也可能是同伴意见引起的，这里只是统计上的关联。</p></section>')

P.append('<section class="panel"><h2>七、同伴可靠度标记准不准</h2>' + t_rel() +
         '<p>可靠度标记来自案例库：看案例里与当前同伴说法相似的专家后来是否答对。被标 high 和 low 的同伴，实际答对的比例相差不到 10 个百分点，GPT n1 还是反的；而且几乎每个同伴都被标了（不标的只占 7–13%）。它没有提供“该信谁”的信息。</p></section>')

P.append('<section class="panel"><h2>八、限制</h2><ul>'
         '<li>每个变体只跑了一次；测试集只有 117 条，且之前被反复分析过。</li>'
         '<li>MELD 的经验库与测试有同对话的样本（findings_log F18），这里没有剔除；剔除后命中率应更低，不影响“召回质量低”的结论。</li>'
         '<li>“回声”的原因（检索键含专家自己的回答）和“相似度挤在一起”的原因（模板文字）都是推断，没有做对照实验（例如去掉回答再检索）。</li>'
         '<li>行为统计（第六节）是相关，不是因果。</li></ul></section>')

P.append('<section class="panel"><h2>九、如果还要改召回，可以先离线试（都不需要调用大模型）</h2><ol>'
         '<li>检索键去掉专家自己的回答和模板文字，只用 Caption 编码，看命中率是否提高、回声是否消失。</li>'
         '<li>只在候选标签范围内检索（过滤掉标签不在当前候选里的案例）。</li>'
         '<li>直接取相似度第 1 名，不用 MMR 的“是否答对”加权，比较命中率。</li></ol>'
         '<p>这三项都可以用现有的经验库和本页的复现脚本离线算出命中率；只有命中率明显高于随机（例如 ≥ 35%）时，才值得重新跑辩论。</p></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>R²-MAD 召回效果分析</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P))
out = ROOT / 'docs' / 'v6-rmad-retrieval.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
