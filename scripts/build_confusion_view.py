"""Build docs/confusion-matrices.html: confusion matrices per provider x method x dataset.

Static pre-rendered HTML (works without scripts). Reads only saved outputs, no model calls.
Rows = gold label, columns = predicted label. Gold is used for evaluation display only.
Usage: python scripts/build_confusion_view.py
"""
import json
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs'
PROVS = ['gpt', 'gemini', 'omni']
VERS = {'v1': 'gemini_graph_three_experts_v1', 'v2': 'gemini_graph_shared_media_v2', 'v3': 'gemini_graph_emotion_wheel_v3'}
ORDER = {'MER2024': ['happy', 'angry', 'sad', 'worried', 'surprise', 'neutral'],
         'MELD': ['joy', 'anger', 'sadness', 'fear', 'disgust', 'surprise', 'neutral']}
METHODS = [('direct', 'Direct'), ('ppct', '原始 PPCT'), ('v1', 'v1 汇总'), ('v2', 'v2 汇总'), ('v3', 'v3 汇总')]
ROLES = [('graph', '图谱专家'), ('audio_subtitle', '音频字幕专家'), ('image', '图像专家')]
ROWS = [json.loads(x) for x in (ROOT / 'data/manifests/validation.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
GOLD = {r['id']: r['label'] for r in ROWS}
DS = {r['id']: r['dataset'] for r in ROWS}


def jread(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf8'))
    except Exception:
        return None


def preds(method, prov):
    """id -> predicted label for successful samples of one result set."""
    out = {}
    for i in GOLD:
        if method in ('direct', 'ppct'):
            r = jread(OUT / method / prov / i / 'result.json')
            ok = r and r.get('status') == 'success'
            a = r.get('prediction') if ok else None
        elif method in VERS:
            r = jread(OUT / VERS[method] / prov / i / 'result.json')
            s = jread(OUT / VERS[method] / prov / i / 'summary.json')
            a = s.get('answer') if r and r.get('status') == 'success' and s else None
        else:  # v3 expert role
            r = jread(OUT / VERS['v3'] / prov / i / 'result.json')
            e = jread(OUT / VERS['v3'] / prov / i / f'expert_{method}.json')
            a = e.get('answer') if r and r.get('status') == 'success' and e else None
        if a is not None:
            out[i] = a
    return out


def matrix(pred, ds):
    labels = ORDER[ds]
    m = {g: Counter() for g in labels}
    for i, a in pred.items():
        if DS[i] == ds:
            m[GOLD[i]][a] += 1
    return m


def render(m, ds, title):
    labels = ORDER[ds]
    n = sum(sum(c.values()) for c in m.values())
    correct = sum(m[g][g] for g in labels)
    h = f'<div class="mx"><h4>{escape(title)}<span>{correct}/{n}</span></h4><table><tr><th class="corner">真实＼预测</th>'
    h += ''.join(f'<th class="col">{l}</th>' for l in labels) + '<th class="col">召回</th></tr>'
    for g in labels:
        tot = sum(m[g].values())
        h += f'<tr><th class="row">{g}<small>{tot}</small></th>'
        for p in labels:
            c = m[g][p]
            if tot == 0 or c == 0:
                h += '<td class="z">·</td>'
                continue
            a = min(0.95, 0.12 + 0.88 * c / tot)
            color = f'rgba(19,122,104,{a:.2f})' if g == p else f'rgba(201,83,60,{a:.2f})'
            h += f'<td style="background:{color}" title="真实 {g} → 预测 {p}：{c}/{tot}">{c}</td>'
        h += f'<td class="rc">{100 * m[g][g] / tot:.0f}%</td></tr>' if tot else '<td class="rc">-</td></tr>'
    return h + '</table></div>'


def pair_table(sets, ds, top=10):
    """Aggregate off-diagonal confusions over result sets; unordered pair with both directions."""
    d = Counter()
    total = 0
    for pred in sets:
        for g, row in matrix(pred, ds).items():
            for p, c in row.items():
                total += c
                if g != p:
                    d[(g, p)] += c
    pairs = defaultdict(lambda: [0, 0, 0])
    for (g, p), c in d.items():
        k = tuple(sorted((g, p)))
        idx = 0 if g == k[0] else 1
        pairs[k][idx] += c
        pairs[k][2] += c
    rows = sorted(pairs.items(), key=lambda kv: -kv[1][2])[:top]
    h = '<table class="pairs"><tr><th>混淆对</th><th>A→B</th><th>B→A</th><th>合计</th><th>占全部错判</th></tr>'
    wrong = sum(d.values())
    for (a, b), (ab, ba, t) in rows:
        h += (f'<tr><td><b>{a}</b> ⇄ <b>{b}</b></td><td>{a}→{b}：{ab}</td><td>{b}→{a}：{ba}</td>'
              f'<td><b>{t}</b><span class="bar" style="width:{t / rows[0][1][2] * 120:.0f}px"></span></td><td>{100 * t / wrong:.0f}%</td></tr>')
    return h + f'</table><p class="muted small">共 {total} 次判断，其中 {wrong} 次错判（{100 * wrong / total:.0f}%）。</p>'


CSS = '''
:root{--ink:#172c38;--muted:#607583;--paper:#f4f6f3;--line:#dce4de;--green:#137a68}*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1380px;margin:auto;padding:34px 30px 60px}
.eyebrow{font-size:12px;color:var(--green);font-weight:700;letter-spacing:2px}h1{font-size:30px;margin:8px 0}h2{font-size:21px;margin:0 0 6px}h3{font-size:16px;margin:22px 0 8px}h4{margin:0 0 6px;font-size:13.5px;display:flex;justify-content:space-between}h4 span{font:12px Consolas,monospace;color:var(--muted)}
.muted{color:var(--muted)}.small{font-size:12.5px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 24px;margin-top:18px}
.warn{margin-top:14px;padding:10px 14px;border-left:3px solid #b47c20;background:#fff8e9;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}.mx{border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:#fcfdfc}
.mx table{border-collapse:collapse;width:100%;font-size:12px;table-layout:fixed}.mx th,.mx td{text-align:center;padding:3px 1px;border:1px solid #edf1ed;height:26px}
.mx th.col{font-weight:600;color:var(--muted);font-size:10.5px;overflow:hidden}.mx th.row{text-align:left;padding-left:5px;font-weight:600;color:var(--muted);font-size:11px;width:78px}.mx th.row small{margin-left:5px;font-weight:400;color:#9bb0a8}
.mx th.corner{font-size:9.5px;color:#9bb0a8;width:78px}.mx td.z{color:#cfd9d3}.mx td.rc{color:var(--muted);font-size:11px;background:#f7f9f7;width:40px}
table.pairs{border-collapse:collapse;width:100%;font-size:13.5px}.pairs th,.pairs td{padding:7px 10px;border-bottom:1px solid #edf1ed;text-align:left}.pairs th{color:var(--muted);font-size:12.5px;font-weight:600}
.bar{display:inline-block;height:9px;margin-left:8px;border-radius:3px;background:#c9533c;vertical-align:middle}
.legend{display:flex;gap:16px;font-size:12px;color:var(--muted);margin:8px 0}.legend b{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-2px;margin-right:5px}
details{margin-top:12px}summary{cursor:pointer;color:var(--green);font-size:13.5px}.cols2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:900px){.cols2{grid-template-columns:1fr}main{padding:20px 14px}}
'''


def main():
    sets = {(p, m): preds(m, p) for p in PROVS for m, _ in METHODS}
    roles = {(p, r): preds(r, p) for p in PROVS for r, _ in ROLES}
    body = ''
    for ds in ORDER:
        body += f'<section class="panel"><h2>{ds}</h2><p class="muted small">行 = 真实标签（小字为条数），列 = 模型预测；格内为条数，颜色深浅 = 占该真实标签的比例。绿色在对角线（答对），红色在非对角线（混淆）。</p>'
        body += '<div class="legend"><span><b style="background:rgba(19,122,104,.7)"></b>答对</span><span><b style="background:rgba(201,83,60,.7)"></b>混淆</span></div>'
        body += f'<h3>最容易混淆的标签对</h3><div class="cols2">'
        for name, group in [('GPT 与 Gemini 合并（Direct、PPCT、v1、v2、v3 汇总，共 10 组结果）', ['gpt', 'gemini']),]:
            body += f'<div><p><b>{name}</b></p>{pair_table([sets[(p, m)] for p in group for m, _ in METHODS], ds)}</div>'
        # per-provider top pairs (3 each)
        body += '<div>'
        for p in ['gpt', 'gemini']:
            body += f'<p><b>{p.upper()} 单独（5 种方法）</b></p>{pair_table([sets[(p, m)] for m, _ in METHODS], ds, top=6)}'
        body += '</div></div>'
        for p in PROVS:
            n_note = ''
            if p == 'omni':
                n_note = '（v1/v2/v3 仅部分样本有效，括号内为答对/有效条数）'
            body += f'<h3>{p.upper()} {n_note}</h3><div class="grid">'
            for m, label in METHODS:
                body += render(matrix(sets[(p, m)], ds), ds, label)
            body += '</div>'
            body += '<details><summary>v3 三位专家的混淆矩阵</summary><div class="grid" style="margin-top:10px">'
            for r, label in ROLES:
                body += render(matrix(roles[(p, r)], ds), ds, 'v3 ' + label)
            body += '</div></details>'
        body += '</section>'
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>类别混淆矩阵</title><style>{CSS}</style></head><body><main>
<div class="eyebrow">PPCT / CONFUSION MATRICES</div><h1>哪些类别更容易混淆</h1>
<p class="muted">每个模型、每种方法在 80 条样本上的混淆矩阵，以及按错判次数排序的“易混淆标签对”。MER2024（6 类）与 MELD（7 类）标签集不同，分开统计。</p>
<div class="warn">这 80 条是已被反复用于开发的子集，不是独立测试集；每个真实标签只有 5 到 7 条，一条样本 = 14 到 20 个百分点，只能看趋势。真实标签仅用于评估显示。数据来自本机保存的 outputs，页面不调用模型，内容为静态渲染，不依赖脚本。Omni 的 v1/v2/v3 并不完整，只统计有效样本。</div>
{body}
<p class="muted small" style="margin-top:20px">由 scripts/build_confusion_view.py 生成。</p></main></body></html>'''
    out = ROOT / 'docs' / 'confusion-matrices.html'
    out.write_text(page, encoding='utf8')
    print(out, len(page) // 1024, 'KB')
    # plain-text digest for the chat
    for ds in ORDER:
        for name, group in [('GPT+Gemini', ['gpt', 'gemini'])]:
            d = Counter()
            for p in group:
                for m, _ in METHODS:
                    for g, row in matrix(sets[(p, m)], ds).items():
                        for q, c in row.items():
                            if g != q:
                                d[(g, q)] += c
            print(ds, name, d.most_common(8))


if __name__ == '__main__':
    main()
