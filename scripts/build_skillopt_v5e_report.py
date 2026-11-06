"""Build docs/v6-skillopt-v5e-report.html: analysis report of the current SkillOpt-V5E version (Gemini: 3 epochs + 4 test runs;
GPT: epoch 1 still running). Static HTML, no scripts, no model calls.
Data: metrics/v6_skillopt_v5e_report_data.json (collected read-only from the server outputs outputs/v6_skillopt_v5e/<provider>/).
Reference numbers (v5-E without skill, Direct five-run mean) are from metrics/findings_log.md F11 / F12.
Usage: python scripts/build_skillopt_v5e_report.py
"""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / 'metrics' / 'v6_skillopt_v5e_report_data.json').read_text(encoding='utf8'))
G, P = D['gemini'], D['gpt']
DS = ('MER2024', 'MELD')
REF = {'gemini': dict(v5e=39, direct=36.6, n=62), 'gpt': dict(v5e=24, direct=23.8, n=55)}
TEST_NAMES = [('control', '纯 v5-E 再跑一次（对照）', '空技能、不扩充'), ('expand_only', '只扩充', '空技能 + 候选扩充'),
              ('skill_4b9033ca', 'epoch-1 技能', '技能（1 个 epoch）+ 扩充'), ('skill_8da2df63', 'epoch-3 技能（最终）', '技能（3 个 epoch）+ 扩充')]


def tot(x, k):
    return sum(x[d][k] for d in DS)


def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else '–'


def neutral_share(labels, ds):
    c = labels[ds]
    n = sum(c.values())
    return c.get('neutral', 0), n


# ------------------------------------------------------------------------------------------- tables
def test_table():
    rows = []
    for key, name, desc in TEST_NAMES:
        t = G['test'][key]
        cells = [f'<td><b>{e(name)}</b><br><span class="small muted">{e(desc)}</span></td>', f'<td class="n"><b>{tot(t, "correct")}</b></td>']
        for d in DS:
            cells.append(f'<td class="n">{t[d]["correct"]} / {t[d]["n"]}</td><td class="n">{t[d]["bal"]:.2f}</td><td class="n">{t[d]["pred_neutral"]}</td>')
        cells.append(f'<td class="n">{tot(t, "flagged")}</td><td class="n">{tot(t, "revise_wr")} / {tot(t, "revise_rw")}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    head = ('<tr><th rowspan="2">设置</th><th rowspan="2" class="n">合计答对<br>/ 62</th><th colspan="3">MER2024（26 条）</th><th colspan="3">MELD（36 条）</th>'
            '<th rowspan="2" class="n">写了不确定点</th><th rowspan="2" class="n">回看改判<br>错→对 / 对→错</th></tr>'
            '<tr><th class="n">答对</th><th class="n">类平均召回</th><th class="n">判成 neutral</th><th class="n">答对</th><th class="n">类平均召回</th><th class="n">判成 neutral</th></tr>')
    ref = (f'<tr class="ref"><td>参照：此前 v5-E 无技能（一次运行）</td><td class="n">{REF["gemini"]["v5e"]}</td><td colspan="8" class="muted">没有按数据集拆分的记录</td></tr>'
           f'<tr class="ref"><td>参照：Direct 五次均值</td><td class="n">{REF["gemini"]["direct"]}</td><td colspan="8" class="muted">F11</td></tr>')
    return '<table>' + head + ''.join(rows) + ref + '</table>'


def val_table(prov):
    x = D[prov]
    rows = [f'<tr><td>S0（空技能 + 扩充）</td><td>—</td><td class="n">{tot(x["val"]["S0"], "correct")}</td>'
            + ''.join(f'<td class="n">{x["val"]["S0"][d]["correct"]} / {x["val"]["S0"][d]["n"]}</td><td class="n">{x["val"]["S0"][d]["bal"]:.2f}</td>' for d in DS) + '<td>起点</td></tr>']
    for s in x['steps']:
        for g in s['gates']:
            name = f'step{s["step"]:02d}_{g["module"]}'
            v = x['val'].get(name)
            if not v:
                continue
            verdict = '<span class="ok">接受</span>' if g['acc'] else '<span class="bad">拒绝</span>'
            rows.append(f'<tr><td>第 {s["step"]} 步（epoch {s["epoch"]}）{ {"first": "首答", "relook": "回看", "reflect": "反思"}[g["module"]] }模块，{g["n_edits"]} 条编辑</td>'
                        f'<td>{verdict}</td><td class="n">{g["cand"]}（当前 {g["cur"]}）</td>'
                        + ''.join(f'<td class="n">{v[d]["correct"]} / {v[d]["n"]}</td><td class="n">{v[d]["bal"]:.2f}</td>' for d in DS) + '<td></td></tr>')
    head = ('<tr><th>候选技能</th><th>门控</th><th class="n">验证答对</th><th class="n">MER 答对</th><th class="n">MER 类平均召回</th>'
            '<th class="n">MELD 答对</th><th class="n">MELD 类平均召回</th><th></th></tr>')
    return '<table>' + head + ''.join(rows) + '</table>'


def dist_table():
    rows = []
    for prov, name in (('gemini', 'Gemini'), ('gpt', 'GPT')):
        lab = D[prov]['labels']
        cells = [f'<td><b>{name}</b></td>']
        for split in ('train', 'val', 'test'):
            for d in DS:
                k, n = neutral_share(lab[split], d)
                cls = ' class="n hi"' if d == 'MELD' else ' class="n"'
                cells.append(f'<td{cls}>{k} / {n}（{pct(k, n)}）</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    head = ('<tr><th rowspan="2"></th><th colspan="2">训练</th><th colspan="2">验证</th><th colspan="2">测试</th></tr>'
            '<tr><th class="n">MER2024</th><th class="n">MELD</th><th class="n">MER2024</th><th class="n">MELD</th><th class="n">MER2024</th><th class="n">MELD</th></tr>')
    return '<table>' + head + ''.join(rows) + '</table>'


def epoch3_table():
    rows = []
    for s in G['steps']:
        if s['epoch'] != 3:
            continue
        sel = sum((s['selected'] or {}).values())
        rej = sum(s['apply_rejected'].values())
        rows.append(f'<tr><td class="n">{s["step"]}</td><td class="n">{s["L"]}</td><td class="n">{s["rollout_correct"]} / {s["batch"]}</td><td class="n">{sel}</td><td class="n">{rej}</td><td class="n">{len(s["gates"])}</td></tr>')
    return ('<table><tr><th class="n">步</th><th class="n">L</th><th class="n">rollout 答对</th><th class="n">选中的编辑</th><th class="n">因超 1,500 字被丢弃</th><th class="n">门控次数</th></tr>'
            + ''.join(rows) + '</table>')


def skill_block(mods):
    title = {'first': '首答模块', 'relook': '回看模块', 'reflect': '反思模块'}
    out = []
    for m in ('first', 'relook', 'reflect'):
        text = mods.get(m, '') or '（空）'
        out.append(f'<h4>{title[m]}（{len(mods.get(m, ""))} 字）</h4><pre class="skill">{e(text)}</pre>')
    return ''.join(out)


def gpt_progress():
    x = P
    done = len(x['steps'])
    acc = [f'第 {s["step"]} 步 {g["module"]}' for s in x['steps'] for g in s['gates'] if g['acc']]
    return (f'<p>GPT 训练还没跑完第 1 个 epoch：已完成 {done} / 6 步，验证集 {x["baseline"]["val_correct"]} / {x["baseline"]["val_n"]} → '
            f'{x["steps"][-1]["cur_after"]} / {x["baseline"]["val_n"]}。还没有任何 GPT 测试结果。被接受的门控：{e("、".join(acc))}。</p>')


# ------------------------------------------------------------------------------------------- page
css = '''body{font:15px/1.7 "Microsoft YaHei",sans-serif;max-width:1180px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}
h1{font-size:25px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:30px}h3{font-size:16px;margin:18px 0 4px;color:#444}h4{font-size:14px;margin:12px 0 2px;color:#555}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 16px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:13.5px}th,td{border:1px solid #ccc;padding:4px 7px;text-align:left;vertical-align:top}th{background:#eef}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}td.hi{background:#fff3da}tr.ref td{background:#f6f6f6}
.ok{color:#2D6A4F;font-weight:700}.bad{color:#C0392B;font-weight:700}.muted{color:#666}.small{font-size:12.5px}
.key{background:#eaf4ff;border-left:4px solid #48c;padding:10px 14px;margin:10px 0}.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}
pre.skill{white-space:pre-wrap;background:#f6f8f8;border:1px solid #dde;border-radius:4px;padding:8px 10px;font:13px/1.65 "Microsoft YaHei",sans-serif}
code{background:#eee;padding:0 4px;border-radius:3px}'''

gt = G['test']
c_ctl, c_e3 = tot(gt['control'], 'correct'), tot(gt['skill_8da2df63'], 'correct')
P_ = []
P_.append('<h1>SkillOpt-V5E 当前版本分析报告</h1>')
P_.append('<p class="muted">日期 2026-11-06。范围：Gemini 已完成 3 个 epoch 的训练和 4 组测试；GPT 仍在跑第 1 个 epoch，没有测试结果，只报告进度。'
          '所有数字读自服务器上已保存的结果（<code>metrics/v6_skillopt_v5e_report_data.json</code>），没有新增模型调用。设计见 <code>docs/v6-skillopt-v5e-design.html</code>。</p>')

P_.append('<section class="panel"><h2>一、结论</h2><div class="key"><ol>'
          f'<li><b>这一版没有效果。</b>Gemini 测试 62 条：纯 v5-E 对照 {c_ctl}，只扩充 {tot(gt["expand_only"], "correct")}，epoch-1 技能 {tot(gt["skill_4b9033ca"], "correct")}，'
          f'epoch-3 技能 {c_e3}。技能没有超过对照，训练越多越差；只有 epoch-3 与对照的差（{c_e3 - c_ctl}）超出了单次运行的噪声（约 ±3 条）。</li>'
          '<li><b>验证集上的提升没有转移到测试集。</b>验证集从 20 / 47 升到 27 / 47，测试反而下降。</li>'
          '<li><b>主要原因：训练 / 验证与测试的标签分布不同，技能学到了“偏向 neutral”。</b>MELD 里 neutral 在训练、验证占 32–60%，在测试只占 6–12%。'
          '技能把测试 MELD 上判成 neutral 的样本从 3 条推到 12 条，MELD 答对从 26 降到 16；MER2024 上没有这个问题，答对从 11 升到 16–17。</li>'
          '<li><b>回看、反思模块的“不降低”门控放进了没起作用的规则。</b>它们几乎每次都被接受（验证分不变），epoch 2 新增的全是这类规则，测试比 epoch-1 又少 4 条。</li>'
          '<li><b>候选扩充没有被用上。</b>4 组测试里 agent 一次都没有选扩充出来的标签；扩充让真实标签进入候选的只有 3 条。</li>'
          '<li><b>epoch 3 实际没有训练</b>（实现问题）：技能已经 1,452 字，选中的编辑全部因 1,500 字上限被丢弃，一次门控都没做。</li></ol></div></section>')

P_.append('<section class="panel"><h2>二、跑了什么</h2><ul>'
          '<li><b>方法</b>：v5-E（首答 → 有不确定点才回看 → 反思）+ 候选扩充（80 条旧样本混淆矩阵 top1）+ 一份三模块技能文档，用 SkillOpt 的循环训练：'
          'rollout 40 条 → 失败 / 成功分堆、8 条一组 → 一位看视频的反思模型写补丁 → 合并 → 每模块留前 L 条 → 检查 → 分模块门控。</li>'
          '<li><b>门控</b>：首答模块验证答对 ≥ 当前 + 2；回看、反思模块 ≥ 当前（不降低）。</li>'
          '<li><b>数据</b>：训练 / 验证来自 v6 池里三专家第 0 轮不一致的样本（MELD 去掉与测试同对话的），Gemini 137 / 47，GPT 233 / 81；'
          '测试是旧 400 条里 v4 判定不一致的样本，Gemini 62、GPT 55。</li>'
          '<li><b>模型</b>：目标 Gemini = gemini-3.8-flash-high，反思 / 合并 = 同一模型；GPT 目标 gpt-6-sol，反思 / 合并 gpt-6.1-sol。</li>'
          '<li><b>训练过程</b>：先跑 1 个 epoch（Gemini 4 步），按你的要求续跑到 3 个 epoch（共 12 步）。</li></ul></section>')

P_.append('<section class="panel"><h2>三、Gemini 测试结果（62 条，每种设置一次运行）</h2>' + test_table() +
          '<p class="small muted">类平均召回 = 每个真实类别的召回率取平均，不受类别多少影响。测试集接近均衡，所以它和准确率的方向应一致；'
          '“判成 neutral”是预测为 neutral 的条数，测试里真实 neutral 只有 MER2024 6 条、MELD 2 条。</p>'
          '<h3>按数据集看</h3><ul>'
          f'<li><b>MER2024</b>：对照 {gt["control"]["MER2024"]["correct"]} → 只扩充 {gt["expand_only"]["MER2024"]["correct"]} → 技能 {gt["skill_4b9033ca"]["MER2024"]["correct"]} / {gt["skill_8da2df63"]["MER2024"]["correct"]}，一直在升；技能组相对对照只多对、没有丢掉任何一条。</li>'
          f'<li><b>MELD</b>：对照 {gt["control"]["MELD"]["correct"]} → 只扩充 {gt["expand_only"]["MELD"]["correct"]} → 技能 {gt["skill_4b9033ca"]["MELD"]["correct"]} / {gt["skill_8da2df63"]["MELD"]["correct"]}，一直在降。'
          'epoch-1 技能相对对照丢掉的 9 条里 8 条改判成 neutral；epoch-3 技能丢掉的 12 条里 7 条改判成 neutral。</li>'
          '<li><b>回看</b>：技能让写不确定点的样本从 3 条增加到 7–9 条，但回看后改判只有 2 条（一对一错），回看环节仍然几乎不起作用。</li></ul></section>')

P_.append('<section class="panel"><h2>四、为什么验证集在升、测试在降</h2>'
          '<h3>1. 标签分布不一致（主要原因）</h3>' + dist_table() +
          '<p>表中是 neutral 占各子集的比例。训练 / 验证样本来自 v6 池，保持数据集的自然分布；测试样本来自旧 400 条，当初是按近似均衡的标签配额选的。'
          '于是 MELD 的 neutral 在训练和验证里很多，在测试里很少。</p>'
          '<p>技能是从训练集的失败里学的，验证集按准确率门控：多判 neutral 在验证集上更容易答对，门控就接受了它。到了几乎没有 neutral 的测试集，这条规则就变成了系统性错误。</p>'
          '<h3>2. 按类平均召回看，验证集上其实已经有迹象</h3>'
          '<p>Gemini 验证集各候选技能（只列做过门控的）：</p>' + val_table('gemini') +
          '<p>GPT 验证集到目前为止：</p>' + val_table('gpt') +
          '<p>GPT 第 2、4 步被接受的首答补丁，在验证 MELD 上的类平均召回是下降的（0.44 → 0.37 → 0.31），只因为 MER2024 上升、总答对数过了 +2 才被接受。'
          '如果门控当时按数据集分别看类平均召回，这两次都会被拒绝。Gemini 的验证 MELD 类平均召回反而上升（0.36 → 0.47），但测试 MELD 照样下降，说明 22 条的验证集本身也不够可靠。</p>'
          '<h3>3. 回看、反思模块的门控几乎不设防</h3>'
          '<p>这两个模块只影响写了不确定点的样本（验证集里只有少数几条），补丁多半不改变任何答案，“不降低”就把它们当作通过。Gemini 在 12 步里一共接受了 '
          f'{sum(1 for s in G["steps"] for g in s["gates"] if g["acc"] and g["module"] != "first")} 次回看 / 反思补丁，'
          f'首答补丁只接受了 {sum(1 for s in G["steps"] for g in s["gates"] if g["acc"] and g["module"] == "first")} 次。epoch 2 只新增了这类规则，测试从 36 降到 32。</p>'
          '<h3>4. epoch 3 空转</h3>' + epoch3_table() +
          '<p>原因是长度上限按“整批编辑应用后”判断，而技能已经 1,452 字；优化器只会追加，不会先删旧规则。这是实现问题，不是方法本身的结论。</p>'
          '<h3>5. 候选扩充</h3>'
          f'<p>扩充出现在 54 / 62 条测试样本的候选里，但只让 {tot(gt["expand_only"], "gold_only_via_expansion")} 条的真实标签进入候选；4 组测试里 agent 选中扩充标签 0 次。'
          '只扩充组的得失（MER2024 +4、MELD −3）都不是因为选了扩充标签，属于运行之间的差别。扩充在这一版里基本是无效的干扰项。</p></section>')

P_.append('<section class="panel"><h2>五、Gemini 最终技能（epoch 3，1,452 字）</h2>' + skill_block(G['best_skill.json']) +
          '<p class="small muted">我通读后的看法：没有样本 id、字幕原句或数字；但规则里有明显的方向性（多处“应果断改判 neutral”“归为 neutral”），并混用了两个数据集的标签名'
          '（worried 只属于 MER2024，sadness 只属于 MELD）。这与测试 MELD 上偏向 neutral 的现象一致。</p></section>')

P_.append('<section class="panel"><h2>六、GPT 进度</h2>' + gpt_progress() +
          '<p>GPT 的技能已 1,189 字，按当前代码大概率在第 2 个 epoch 撞到 1,500 字上限；验证 MELD 的类平均召回在下降，预计会重复 Gemini 的问题。</p></section>')

P_.append('<section class="panel"><h2>七、限制</h2><ul>'
          '<li>每种测试设置只跑了一次；单次运行的噪声约 ±3 条（F11）。</li>'
          '<li>验证集小（Gemini 47 条，每个数据集 22–25 条，部分类别只有 1–2 条），门控和类平均召回都噪声大。</li>'
          '<li>测试的 62 条之前被反复分析过，是开发集；80 条混淆矩阵含 20 个测试样本的标准标签。</li>'
          '<li>“偏向 neutral”是从预测分布和丢分样本推断的，没有做因果检验（例如只删掉技能里涉及 neutral 的规则再测）。</li></ul></section>')

P_.append('<section class="panel"><h2>八、建议的改法（待你决定，未实施）</h2><ol>'
          '<li><b>门控改用“按数据集分别计算的类平均召回”，两个数据集都不得下降</b>：直接针对 neutral 偏向，最关键。</li>'
          '<li><b>回看、反思模块的门控改为“至少改变一条验证答案、且净多对 ≥ 1”</b>，不再放进没起作用的规则。</li>'
          '<li><b>技能按数据集分节</b>：每条样本只看自己数据集的那一节；补丁检查拒绝出现该数据集没有的标签。</li>'
          '<li><b>超过长度上限时，先让优化器精简改写再门控</b>，避免空转。</li>'
          '<li>（可选）让训练 / 验证的标签分布接近测试，或在测试同时报告类平均召回。</li></ol>'
          '<div class="warn">GPT 仍在按旧设计运行。如果采用这些改法，需要停掉 GPT 和驱动脚本，两家都重新训练；旧结果保留作对照。</div></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>SkillOpt-V5E 当前版本分析报告</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(P_))
out = ROOT / 'docs' / 'v6-skillopt-v5e-report.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
