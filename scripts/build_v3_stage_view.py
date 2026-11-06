"""Build docs/v3-<provider>-stages.html: an offline viewer for every stage output of v3.

Fully pre-rendered static HTML: all tables, the sample matrix and every sample's stage chain are
written at build time, so the page shows its content even when scripts are disabled or blocked.
The small script at the end only adds filter buttons and the current-cell highlight.
Reads only saved outputs (no model calls). Gold labels are shown for evaluation display only.
Usage: python scripts/build_v3_stage_view.py [gpt|gemini|omni]
"""
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V3 = ROOT / 'outputs' / 'gemini_graph_emotion_wheel_v3'
GRAPHS = ROOT / 'data' / 'gemini_graph_three_experts_v1'
ROLES = ['graph', 'audio_subtitle', 'image']
NAME = {'graph': '图谱专家', 'audio_subtitle': '音频字幕专家', 'image': '图像专家', 'summary': '汇总器'}


def read(path):
    return json.loads(path.read_text(encoding='utf8')) if path.exists() else None


def esc(value):
    return escape('' if value is None else str(value), quote=True)


def refs(text):
    return re.sub(r'〔([^〕]*)〕', r'<span class="ref">〔\1〕</span>', esc(text))


def load(provider, row):
    sid = row['id']
    folder = V3 / provider / sid
    result = read(folder / 'result.json')
    if not result or result.get('status') != 'success':
        return None
    return dict(
        id=sid, dataset=row['dataset'], speaker=row.get('speaker'), subtitle=row.get('subtitle', ''),
        label=row['label'], classes=row['classes'],
        graph=read(GRAPHS / sid / 'graph.json') or {'nodes': [], 'edges': []},
        organization=(read(folder / 'organization.json') or {}).get('text', ''),
        experts={r: read(folder / f'expert_{r}.json') for r in ROLES}, summary=read(folder / 'summary.json'),
        audio=result.get('raw_audio_provided'), graph_audio=result.get('graph_contains_audio_derived_nodes'),
        direct=(read(ROOT / 'outputs/direct' / provider / sid / 'result.json') or {}).get('prediction'),
        ppct=(read(ROOT / 'outputs/ppct' / provider / sid / 'result.json') or {}).get('prediction'))


def ans(s, role):
    if role == 'summary':
        return (s['summary'] or {}).get('answer')
    return (s['experts'].get(role) or {}).get('answer')


def ok(s, role):
    return ans(s, role) == s['label']


def majority(s):
    counts = {}
    for role in ROLES:
        a = ans(s, role)
        if a:
            counts[a] = counts.get(a, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])
    return top[0][0] if top and top[0][1] >= 2 else None


def pct(a, b):
    return f'{100 * a / b:.2f}%' if b else '-'


def pill(answer, gold):
    good = answer == gold
    return f'<span class="pill {"ok" if good else "bad"}">{esc(answer)} {"✓" if good else "✗"}</span>'


def role_table(S):
    def row(role):
        cells = []
        for ds in ('MER2024', 'MELD'):
            sub = [s for s in S if s['dataset'] == ds]
            cells.append(f'{sum(ok(s, role) for s in sub)}/{len(sub)}')
        t = sum(ok(s, role) for s in S)
        label = NAME[role] + ('（最终输出）' if role == 'summary' else '')
        return (f'<tr><td>{label}</td><td class="num">{cells[0]}</td><td class="num">{cells[1]}</td>'
                f'<td class="num"><b>{t}/{len(S)} = {pct(t, len(S))}</b></td>'
                f'<td><span class="bar" style="width:{t / len(S) * 200:.0f}px"></span></td></tr>')
    d = sum(s['direct'] == s['label'] for s in S)
    p = sum(s['ppct'] == s['label'] for s in S)
    ref = lambda name, n: (f'<tr><td class="muted">{name}</td><td></td><td></td><td class="num muted">{n}/{len(S)} = {pct(n, len(S))}</td>'
                           f'<td><span class="bar g" style="width:{n / len(S) * 200:.0f}px"></span></td></tr>')
    html = '<table><tr><th>角色</th><th>MER2024</th><th>MELD</th><th>合计</th><th></th></tr>'
    html += ''.join(row(r) for r in ROLES + ['summary'])
    html += ref('参照：Direct（同模型）', d) + ref('参照：原始 PPCT（同模型自己的图谱）', p) + '</table>'

    withmaj = [s for s in S if majority(s)]
    agree = [s for s in withmaj if s['summary']['answer'] == majority(s)]
    over = [s for s in withmaj if s['summary']['answer'] != majority(s)]
    unan = [s for s in S if len({ans(s, r) for r in ROLES}) == 1]
    stats = (f'<div class="stat"><b>{len(unan)}/{len(S)}</b>三个专家意见完全一致（其中答对 {sum(ok(s, "graph") for s in unan)}）</div>'
             f'<div class="stat"><b>{len(agree)} 条</b>汇总采纳了多数专家意见，其中答对 {sum(ok(s, "summary") for s in agree)}'
             f'（{pct(sum(ok(s, "summary") for s in agree), len(agree))}）</div>'
             f'<div class="stat"><b>{len(over)} 条</b>汇总推翻了多数专家意见，其中答对 {sum(ok(s, "summary") for s in over)}'
             f'（{pct(sum(ok(s, "summary") for s in over), len(over))}）</div>')
    return html + f'<div class="stats">{stats}</div>'


FILTERS = [('all', '全部', lambda s: True),
           ('bad', '汇总答错', lambda s: not ok(s, 'summary')),
           ('split', '专家意见分歧', lambda s: len({ans(s, r) for r in ROLES}) > 1),
           ('over', '汇总推翻多数专家', lambda s: bool(majority(s)) and s['summary']['answer'] != majority(s)),
           ('lost', '专家有人对、汇总错', lambda s: not ok(s, 'summary') and any(ok(s, r) for r in ROLES))]


def matrix(S):
    chips = ''.join(f'<button class="chip{" on" if k == "all" else ""}" data-f="{k}">{label}（{sum(map(f, S))}）</button>'
                    for k, label, f in FILTERS)
    html = f'<div class="controls" id="filters">{chips}</div>'
    for ds in ('MER2024', 'MELD'):
        sub = [s for s in S if s['dataset'] == ds]
        html += f'<div class="grid-title">{ds}（{len(sub)} 条）</div><div class="grid">'
        for s in sub:
            i = S.index(s)
            short = s['id'].split('/')[1].replace('samplenew_', 'n_').replace('sample_', 's_')
            flags = ' '.join(f'data-{k}="1"' for k, _, f in FILTERS if k != 'all' and f(s))
            dots = ''.join(f'<i class="{"y" if ok(s, r) else ""}"></i>' for r in ROLES)
            html += (f'<a class="cell {"ok" if ok(s, "summary") else "bad"}" href="#s{i}" {flags} '
                     f'title="{esc(s["id"])}：汇总 {esc(s["summary"]["answer"])}，真实 {esc(s["label"])}">'
                     f'{esc(short)}<span class="dots">{dots}</span></a>')
        html += '</div>'
    return html


def graph_html(g):
    cols = ''
    for layer in ('process', 'person', 'context'):
        nodes = ''.join(
            f'<div class="node"><b>{esc(n["id"])}</b> t={n["time_index"]} '
            f'<span class="tag {esc((n.get("evidence_sources") or [""])[0])}">{esc("+".join(n.get("evidence_sources") or []))}</span>'
            f'{esc(n["content"])}</div>' for n in g['nodes'] if n['type'] == layer)
        empty = '<span class="muted small">无</span>'
        cols += f'<div><h3 class="muted small">{layer.upper()}</h3>{nodes or empty}</div>'
    edges = ''.join(
        f'<div class="edge"><b class="small">{esc(e["source"])}</b> <em>{esc(e["relation"])}</em> '
        f'<b class="small">{esc(e["target"])}</b><br><span class="muted small">{esc(e["reason"])}</span></div>'
        for e in g['edges']) or '<span class="muted small">无边</span>'
    return (f'<div class="gcols"><div>{cols}</div><div><h3 class="muted small">EDGES（{len(g["edges"])}）</h3>{edges}</div></div>')


def evidence(e):
    return (f'<div class="ev {esc(e.get("polarity"))}"><span class="tag {esc(e.get("source"))}">{esc(e.get("source"))}</span>'
            f'<span class="tag">{esc(e.get("id"))} · {esc(e.get("polarity"))}</span><span class="muted small">{esc(e.get("anchor"))}</span><br>'
            f'<b>观察：</b>{esc(e.get("observation"))}<br><b>含义：</b>{esc(e.get("interpretation"))}</div>')


def expert_card(s, role):
    e = s['experts'].get(role)
    if not e:
        return f'<div class="ex bad"><h3>{NAME[role]}</h3><p class="muted">无输出</p></div>'
    evs = e.get('evidence') or []
    return (f'<div class="ex {"ok" if e["answer"] == s["label"] else "bad"}"><h3><span>{NAME[role]}</span>{pill(e["answer"], s["label"])}</h3>'
            f'<div class="map">开放情绪 <b>{esc(e.get("open_emotion"))}</b> → 映射 <b>{esc(e["answer"])}</b><br>'
            f'<span class="muted">{esc(e.get("mapping_reason"))}</span></div><p>{refs(e.get("reason"))}</p>'
            f'<details><summary>证据 {len(evs)} 条</summary>{"".join(evidence(x) for x in evs)}</details>'
            f'<details><summary>最强反证 / 限制</summary><p>{esc(e.get("counterevidence"))}</p></details></div>')


def detail(s, i, provider, default):
    audio_note = '实际音轨已提供' if s['audio'] else '该模型没有收到音轨：音频字幕专家实际只读字幕和画面'
    refs_used = ''.join(f'<span class="tag">{esc(x)}</span>' for x in (s['summary'].get('evidence_refs') or [])) or '无'
    opinions = ' · '.join(f'{NAME[r].replace("专家", "")} <b>{esc(ans(s, r))}</b>' for r in ROLES)
    mark = lambda a: '✓' if a == s['label'] else '✗'
    return f'''<section class="sample{" default" if default else ""}" id="s{i}" aria-label="{esc(s["id"])}">
<h2>③ 单样本链路 <span class="muted small">· {esc(s["id"])}</span></h2>
<dl class="meta"><dt>说话人</dt><dd>{esc(s["speaker"] or "-")}</dd><dt>真实标签</dt><dd>{esc(s["label"])}</dd><dt>汇总预测</dt><dd>{pill(s["summary"]["answer"], s["label"])}</dd><dt>候选标签</dt><dd style="font-weight:400">{esc(" / ".join(s["classes"]))}</dd></dl>
<p><b>字幕：</b>{esc(s["subtitle"] or "（无字幕）")}</p>
<p class="small muted">对照（同模型）：Direct → <b>{esc(s["direct"] or "-")}</b> {mark(s["direct"])}　原始 PPCT → <b>{esc(s["ppct"] or "-")}</b> {mark(s["ppct"])}　v3 汇总 → <b>{esc(s["summary"]["answer"])}</b> {mark(s["summary"]["answer"])}</p>
<div class="rail">
<div class="step frozen"><span class="no">1</span><div class="card frozen"><div class="sh"><h3>固定图谱（Gemini 生成，冻结）</h3><span class="in">{len(s["graph"]["nodes"])} 个节点 · {len(s["graph"]["edges"])} 条边{" · 含音频派生节点（非该模型亲耳听到）" if s["graph_audio"] else ""}</span></div>{graph_html(s["graph"])}</div></div>
<div class="step"><span class="no">2</span><div class="card org"><div class="sh"><h3>组织文本（{esc(provider.upper())} 自己生成）</h3><span class="in">输入：图谱（含字幕）；不接图片和音频</span></div><div class="org">{refs(s["organization"])}</div></div></div>
<div class="step"><span class="no">3</span><div><div class="sh"><h3>三个角色专家（互相看不到对方）</h3><span class="in">输入：8 帧 + 字幕 + 数据集情绪轮；{audio_note}；仅图谱专家另收图谱和组织文本</span></div><div class="experts">{"".join(expert_card(s, r) for r in ROLES)}</div></div></div>
<div class="step final"><span class="no">4</span><div class="card fin"><div class="sh"><h3>汇总器 → 最终标签</h3><span class="in">输入：8 帧 + 字幕 + 三位专家的结构化输出 + 情绪轮；不接图谱和组织文本</span></div>
<p>{pill(s["summary"]["answer"], s["label"])} 专家意见：{opinions}</p><p>{refs(s["summary"].get("reason"))}</p><p class="small muted">引用的专家证据：{refs_used}</p></div></div>
</div></section>'''


SCRIPT = '''<script>
(function(){var cells=[].slice.call(document.querySelectorAll('a.cell')),chips=[].slice.call(document.querySelectorAll('[data-f]'));
chips.forEach(function(c){c.addEventListener('click',function(){var f=c.getAttribute('data-f');chips.forEach(function(x){x.classList.toggle('on',x===c)});
cells.forEach(function(a){a.classList.toggle('dim',f!=='all'&&!a.hasAttribute('data-'+f))})})});
function mark(){cells.forEach(function(a){a.classList.toggle('cur',a.getAttribute('href')===location.hash)})}
window.addEventListener('hashchange',mark);mark();})();
</script>'''


def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else 'gpt'
    rows = [json.loads(x) for x in (ROOT / 'data/manifests/validation.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
    S = [s for s in (load(provider, r) for r in rows) if s]
    css = (Path(__file__).with_name('v3_stage_view.css')).read_text(encoding='utf8')
    first = next((i for i, s in enumerate(S) if not ok(s, 'summary')), 0)
    note = f'<p class="muted small">仅 {len(S)}/{len(rows)} 条成功，分母按成功条数计。</p>' if len(S) < len(rows) else ''
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>v3 · {provider.upper()} 各阶段输出</title><style>
{css}</style></head>
<body><main>
<div class="eyebrow">PPCT / V3 STAGE VIEWER</div>
<h1>v3 · {provider.upper()}：每个阶段到底输出了什么</h1>
<p class="muted">固定 Gemini 图谱 → 组织文本 → 三个角色专家（各给一个开放情绪 + 一个映射标签）→ 汇总器给最终标签。点矩阵中的任意样本，向下看它的完整链路。</p>
<div class="warn">这 {len(rows)} 条是已被反复用于开发的子集，不是独立测试集；真实标签仅用于在页面上标注对错，不进入任何模型请求。数据来自本机保存的 outputs，本页面不调用模型，可离线打开；全部内容为静态渲染，不依赖脚本。</div>
<section class="panel"><h2>① 各角色准确率</h2>{role_table(S)}{note}</section>
<section class="panel"><h2>② 样本总览</h2>
<p class="muted small">每格一个样本，点击后在下方显示该样本。底色 = 汇总器是否答对；底部三个点依次是 图谱专家 / 音频字幕专家 / 图像专家 是否答对。</p>
{matrix(S)}
<div class="legend"><span><b style="background:var(--okbg)"></b>汇总答对</span><span><b style="background:var(--badbg)"></b>汇总答错</span><span><b style="background:var(--green)"></b>专家答对（点）</span><span><b style="background:var(--red)"></b>专家答错（点）</span></div>
<p class="nojs">筛选按钮需要脚本；若脚本被禁用，矩阵与样本详情仍可正常点击查看。</p></section>
<section class="panel" id="detail">{"".join(detail(s, i, provider, i == first) for i, s in enumerate(S))}</section>
<p class="muted small" style="margin-top:20px">依据：versions/v3/pipeline.py · emotion_wheel_prompts.py。由 scripts/build_v3_stage_view.py 生成，页面无外部依赖。</p>
</main>{SCRIPT}</body></html>'''
    out = ROOT / 'docs' / f'v3-{provider}-stages.html'
    out.write_text(page, encoding='utf8')
    print(out, len(S), 'samples of', len(rows), f'{len(page) // 1024} KB')


if __name__ == '__main__':
    main()
