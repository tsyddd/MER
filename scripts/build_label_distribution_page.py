"""Build docs/dataset-label-distribution.html: label distribution of every split used so far (full sets, old 400, v6 pool, disagreement pools,
R2-MAD memory, SkillOpt train / val / test). One panel per dataset, one 100%-stacked horizontal bar per split, hover tooltips, table view,
light / dark palettes validated with the dataviz validator. Static HTML (the tooltips use a small inline script; all bars are pre-rendered SVG).
Data: metrics/dataset_label_distribution.json (read-only count on the server, 2026-11-06).
Usage: python scripts/build_label_distribution_page.py
"""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / 'metrics' / 'dataset_label_distribution.json').read_text(encoding='utf8'))

# label order: neutral first (it is the story), then by full-set frequency; fixed slot order, never cycled
LABELS = {'MER2024': ['neutral', 'sad', 'happy', 'angry', 'worried', 'surprise'],
          'MELD': ['neutral', 'joy', 'anger', 'surprise', 'sadness', 'disgust', 'fear']}
# categorical slots of the reference palette (validated: MER = slots 1-6, MELD = slots 1-5, 7, 8; light and dark)
SLOT = {'MER2024': [1, 2, 3, 4, 5, 6], 'MELD': [1, 2, 3, 4, 5, 7, 8]}

ROWS = [  # (key, label, group)
    ('full', '完整数据集', '原始'),
    ('old400', '旧 400 条（当初按类均衡选出；测试来源）', '原始'),
    ('pool', 'v6 候选池（去掉旧 400 条）', '原始'),
    ('gemini_pool_disagree', 'Gemini：池中三专家不一致', 'Gemini'),
    ('gemini_rmad_train', 'Gemini：R²-MAD 经验库', 'Gemini'),
    ('gemini_v1_train', 'Gemini：SkillOpt 版本 1 训练', 'Gemini'),
    ('gemini_v1_val', 'Gemini：SkillOpt 版本 1 验证', 'Gemini'),
    ('gemini_v2_train', 'Gemini：SkillOpt 版本 2 训练', 'Gemini'),
    ('gemini_v2_val', 'Gemini：SkillOpt 版本 2 验证（按类分层）', 'Gemini'),
    ('gemini_v1_test', 'Gemini：测试（117 条中的 Gemini 部分）', 'Gemini'),
    ('gpt_pool_disagree', 'GPT：池中三专家不一致', 'GPT'),
    ('gpt_rmad_train', 'GPT：R²-MAD 经验库', 'GPT'),
    ('gpt_v1_train', 'GPT：SkillOpt 版本 1 训练', 'GPT'),
    ('gpt_v1_val', 'GPT：SkillOpt 版本 1 验证', 'GPT'),
    ('gpt_v1_test', 'GPT：测试（117 条中的 GPT 部分）', 'GPT'),
]
TEST_KEYS = {'gemini_v1_test', 'gpt_v1_test', 'old400'}

LW, BW, RW = 330, 640, 64  # label column, bar width, n column
BAR_H, GAP = 20, 9


def panel(ds):
    labs = LABELS[ds]
    x0 = LW
    h_head = 30
    y = h_head
    out = []
    prev_group = None
    for key, name, group in ROWS:
        c = D[ds].get(key)
        if not c:
            continue
        if group != prev_group and prev_group is not None:
            y += 10
            out.append(f'<line x1="8" x2="{LW + BW + RW}" y1="{y - 6}" y2="{y - 6}" class="sep"/>')
        prev_group = group
        n = sum(c.values())
        is_test = key in TEST_KEYS
        out.append(f'<text x="{LW - 10}" y="{y + BAR_H / 2 + 4.5}" text-anchor="end" class="rl{" strong" if is_test else ""}">{e(name)}</text>')
        x = x0
        for i, lab in enumerate(labs):
            k = c.get(lab, 0)
            if not k:
                continue
            w = BW * k / n
            share = 100 * k / n
            tip = f'{name}｜{lab}：{k} / {n}（{share:.1f}%）'
            out.append(f'<rect x="{x:.2f}" y="{y}" width="{max(w - 2, 0.6):.2f}" height="{BAR_H}" class="s{SLOT[ds][i]}" data-tip="{e(tip)}"><title>{e(tip)}</title></rect>')
            if lab == 'neutral' and w >= 38:
                out.append(f'<text x="{x + 6:.2f}" y="{y + BAR_H / 2 + 4.5}" class="in">{share:.0f}%</text>')
            x += w
        out.append(f'<text x="{LW + BW + 8}" y="{y + BAR_H / 2 + 4.5}" class="nl">n = {n}</text>')
        y += BAR_H + GAP
    # axis ticks
    ticks = ''.join(f'<line x1="{LW + BW * t / 4:.1f}" x2="{LW + BW * t / 4:.1f}" y1="{h_head - 6}" y2="{y - GAP + 2}" class="grid"/>'
                    f'<text x="{LW + BW * t / 4:.1f}" y="{h_head - 10}" text-anchor="middle" class="tick">{25 * t}%</text>' for t in range(5))
    legend = ''
    lx = LW
    for i, lab in enumerate(labs):
        legend += f'<rect x="{lx}" y="{y + 10}" width="12" height="12" rx="3" class="s{SLOT[ds][i]}"/><text x="{lx + 17}" y="{y + 20.5}" class="lg">{lab}</text>'
        lx += 24 + 8.2 * len(lab) + 18
    height = y + 34
    return (f'<svg viewBox="0 0 {LW + BW + RW + 10} {height}" width="100%" role="img" aria-label="{ds} 各数据划分的标签分布">'
            + ticks + ''.join(out) + legend + '</svg>')


def table(ds):
    labs = LABELS[ds]
    head = '<tr><th>数据划分</th><th class="n">n</th>' + ''.join(f'<th class="n">{l}</th>' for l in labs) + '</tr>'
    body = []
    for key, name, _ in ROWS:
        c = D[ds].get(key)
        if not c:
            continue
        n = sum(c.values())
        body.append(f'<tr><td>{e(name)}</td><td class="n">{n}</td>' + ''.join(
            f'<td class="n">{c.get(l, 0)}<span class="muted">（{100 * c.get(l, 0) / n:.0f}%）</span></td>' for l in labs) + '</tr>')
    return '<table>' + head + ''.join(body) + '</table>'


def share(ds, key, lab='neutral'):
    c = D[ds][key]
    return 100 * c.get(lab, 0) / sum(c.values())


css = '''.viz-root{color-scheme:light;--surface-1:#fcfcfb;--text-primary:#0b0b0b;--text-secondary:#52514e;--muted:#898781;--grid:#e1e0d9;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--s6:#008300;--s7:#6250d6;--s8:#e34948}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface-1:#1a1a19;--text-primary:#f0efec;--text-secondary:#c3c2b7;--grid:#2c2c2a;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--text-primary:#f0efec;--text-secondary:#c3c2b7;--grid:#2c2c2a;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767}
body{margin:0;background:var(--surface-1);color:var(--text-primary);font:15px/1.7 "Microsoft YaHei","Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:24px auto;padding:0 18px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:26px 0 6px}
.sub{color:var(--text-secondary);margin:0 0 14px}.muted{color:var(--muted);font-size:12px}
.key{border-left:4px solid var(--s1);padding:8px 14px;margin:12px 0;color:var(--text-primary)}
svg text{font-family:"Microsoft YaHei","Segoe UI",sans-serif}.rl{font-size:12.5px;fill:var(--text-secondary)}.rl.strong{fill:var(--text-primary);font-weight:700}
.nl{font-size:12px;fill:var(--muted);font-variant-numeric:tabular-nums}.tick{font-size:11px;fill:var(--muted)}.lg{font-size:12.5px;fill:var(--text-secondary)}
.in{font-size:11.5px;fill:#fff;font-weight:700}.grid{stroke:var(--grid);stroke-width:1}.sep{stroke:var(--grid);stroke-width:1;stroke-dasharray:3 3}
rect.s1{fill:var(--s1)}rect.s2{fill:var(--s2)}rect.s3{fill:var(--s3)}rect.s4{fill:var(--s4)}rect.s5{fill:var(--s5)}rect.s6{fill:var(--s6)}rect.s7{fill:var(--s7)}rect.s8{fill:var(--s8)}
rect[data-tip]:hover{opacity:.82;cursor:default}
details{margin:8px 0 18px}summary{cursor:pointer;color:var(--text-secondary)}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:6px}th,td{border-bottom:1px solid var(--grid);padding:4px 6px;text-align:left}th{color:var(--text-secondary);font-weight:600}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
#tip{position:fixed;pointer-events:none;background:var(--text-primary);color:var(--surface-1);font-size:12.5px;padding:4px 8px;border-radius:4px;display:none;z-index:9}'''

js = '''const t=document.getElementById('tip');document.querySelectorAll('rect[data-tip]').forEach(r=>{r.addEventListener('mousemove',ev=>{t.textContent=r.dataset.tip;t.style.display='block';t.style.left=(ev.clientX+12)+'px';t.style.top=(ev.clientY+12)+'px'});r.addEventListener('mouseleave',()=>{t.style.display='none'})});'''

body = ('<div class="wrap">'
        '<h1>各数据划分的标签分布</h1>'
        '<p class="sub">日期 2026-11-06。每条横条是一个数据划分，按标签的占比堆叠（总长 = 100%），右侧是样本数。加粗的是测试或测试来源。'
        '颜色只表示标签；悬停可看条数与比例，每张图下有数据表。数据：<code>metrics/dataset_label_distribution.json</code>（服务器只读统计）。</p>'
        '<div class="key">'
        f'<b>要点：</b>测试来自旧 400 条，当初是按类均衡选出的（MER2024 每类 33–34 条、MELD 每类 28–29 条）；'
        f'而所有训练 / 验证 / 经验库都来自保持自然分布的候选池。MELD 里 neutral 在完整数据集占 {share("MELD", "full"):.0f}%，'
        f'在 Gemini / GPT 的 SkillOpt 训练集占 {share("MELD", "gemini_v1_train"):.0f}% / {share("MELD", "gpt_v1_train"):.0f}%，'
        f'在测试里只占 {share("MELD", "gemini_v1_test"):.0f}% / {share("MELD", "gpt_v1_test"):.0f}%。'
        'MELD 的 fear 在 SkillOpt 训练集里是 0 条（池中不一致样本只有 1–3 条），测试里却有 7–8 条；disgust 训练 1–3 条，测试 3–4 条。</div>'
        '<h2>MELD（7 类）</h2>' + panel('MELD') + '<details><summary>数据表（MELD）</summary>' + table('MELD') + '</details>'
        '<h2>MER2024（6 类）</h2>' + panel('MER2024') + '<details><summary>数据表（MER2024）</summary>' + table('MER2024') + '</details>'
        '<p class="muted">说明：“池中三专家不一致”只统计已处理的样本（MER2024 968–969 条全部处理完；MELD 处理了 1,196–1,197 / 2,408 条）。'
        'SkillOpt 的训练 / 验证在 MELD 里去掉了与旧 400 条同一段对话的样本；R²-MAD 经验库没有去掉。测试的 Gemini 部分（62 条）与 GPT 部分（55 条）有 15 个样本重合，按样本去重是 102 个。</p>'
        '</div><div id="tip"></div>')

html = ('<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>各数据划分的标签分布</title><style>%s</style></head>'
        '<body class="viz-root">%s<script>%s</script></body></html>') % (css, body, js)
out = ROOT / 'docs' / 'dataset-label-distribution.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
