"""Build docs/debate-vs-vote.html: debate transcripts + statistics of how the debate result differs from plain voting.

Reads only saved outputs (no model calls). Gold labels are used for evaluation display only.
Runs covered: Gemini text-only debate, Gemini media debate, GPT media debate (all with round 0 = saved v3 expert outputs).
Usage: python scripts/build_debate_vs_vote.py
"""
import json
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs'
ROLES = ['graph', 'audio_subtitle', 'image']
RN = {'graph': '图谱专家', 'audio_subtitle': '音频字幕专家', 'image': '图像专家'}
RUNS = [
    ('gt', 'Gemini · 纯文本辩论', 'gemini', 'gemini_conditional_debate_v4_textonly'),
    ('gm', 'Gemini · 带原媒体辩论', 'gemini', 'gemini_conditional_debate_v4_media'),
    ('pm', 'GPT · 带原媒体辩论', 'gpt', 'gpt_conditional_debate_v4_media'),
]
GOLD = {}
for line in (ROOT / 'data/manifests/validation.jsonl').read_text(encoding='utf8').splitlines():
    if line.strip():
        r = json.loads(line)
        GOLD[r['id']] = r['label']


def e(s):
    return escape('' if s is None else str(s), quote=True)


def jread(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf8'))
    except Exception:
        return None


def load_run(code, name, prov, ver):
    base = OUT / ver / prov
    v3 = OUT / 'gemini_graph_emotion_wheel_v3' / prov
    samples = []
    for sid, g in GOLD.items():
        res = jread(base / sid / 'result.json')
        if not res:
            continue
        r0 = {r: jread(v3 / sid / f'expert_{r}.json') for r in ROLES}
        labels0 = {r: r0[r]['answer'] for r in ROLES}
        c = Counter(labels0.values()).most_common()
        vote = c[0][0] if (len(c) == 1 or c[0][1] > c[1][1]) else None
        rounds = []
        for rd in (1, 2):
            outs = {r: (jread(base / sid / f'round{rd}_{r}.json') or {}).get('output') for r in ROLES}
            if all(outs.values()):
                rounds.append(outs)
        s = dict(id=sid, gold=g, trig=res['triggered'], r0=r0, labels0=labels0, vote=vote, final=res['final'], rounds=rounds,
                 judge=res.get('judge'), summary=(jread(v3 / sid / 'summary.json') or {}).get('answer'))
        # trim rounds actually used (result.rounds_run)
        s['rounds'] = s['rounds'][:res['rounds_run']]
        samples.append(s)
    return dict(code=code, name=name, prov=prov, ver=ver, samples=samples)


def status(s):
    v, d, g = s['vote'], s['final'], s['gold']
    if v == d:
        return ('same_ok', '相同 · 都对') if d == g else ('same_bad', '相同 · 都错')
    if v == g:
        return ('break', '辩论改错（投票对）')
    if d == g:
        return ('fix', '辩论改对（投票错）')
    return ('diff_bad', '不同 · 都错')


def run_stats(run):
    S = run['samples']
    T = [s for s in S if s['trig']]
    st = Counter(status(s)[0] for s in T)
    vote_ok = sum(s['vote'] == s['gold'] for s in S)
    deb_ok = sum(s['final'] == s['gold'] for s in S)
    cons = [s for s in T if len({s['rounds'][-1][r]['answer'] for r in ROLES}) == 1] if T else []
    cons_ok = sum(s['final'] == s['gold'] for s in cons)
    return dict(n=len(S), trig=len(T), vote_ok=vote_ok, deb_ok=deb_ok, st=st, cons=len(cons), cons_ok=cons_ok,
                judged=sum(1 for s in T if s['judge']), vote_ok_trig=sum(s['vote'] == s['gold'] for s in T),
                deb_ok_trig=sum(s['final'] == s['gold'] for s in T), summ_ok=sum(s['summary'] == s['gold'] for s in S))


def expert_changes(run):
    """Expert-level label movements during debate, relative to gold."""
    c = Counter()
    for s in run['samples']:
        if not s['trig']:
            continue
        prev = dict(s['labels0'])
        for rd in s['rounds']:
            maj = Counter(prev.values()).most_common(1)[0][0]
            for r in ROLES:
                new = rd[r]['answer']
                old = prev[r]
                others_prev = {prev[o] for o in ROLES if o != r}
                if new == old:
                    c['held_right' if old == s['gold'] else 'held_wrong'] += 1
                else:
                    kind = 'wrong_to_right' if (old != s['gold'] and new == s['gold']) else 'right_to_wrong' if (old == s['gold'] and new != s['gold']) else 'wrong_to_wrong'
                    c[kind] += 1
                    c['toward_others' if new in others_prev else 'to_new_label'] += 1
                    c['toward_majority' if new == maj else 'away_from_majority'] += 1
            prev = {r: rd[r]['answer'] for r in ROLES}
    return c


def minority_dynamics(run):
    """For 2-1 splits: what the lone dissenter does in round 1, split by whether the dissenter is right."""
    c = Counter()
    for s in run['samples']:
        if not s['trig'] or not s['rounds']:
            continue
        lab = s['labels0']
        cnt = Counter(lab.values())
        if len(cnt) != 2:
            continue
        maj = cnt.most_common(1)[0][0]
        mino_roles = [r for r in ROLES if lab[r] != maj]
        if len(mino_roles) != 1:
            continue
        m = mino_roles[0]
        mino_label = lab[m]
        right = mino_label == s['gold']
        r1 = s['rounds'][0]
        yielded = r1[m]['answer'] == maj
        majority_flipped = any(r1[r]['answer'] != maj for r in ROLES if r != m)
        key = 'minority_right' if right else ('majority_right' if maj == s['gold'] else 'both_wrong')
        c[(key, 'n')] += 1
        c[(key, 'yield')] += yielded
        c[(key, 'majority_member_flipped')] += majority_flipped
    return c


# ---------------------------------------------------------------- html
CSS = '''
:root{--ink:#172c38;--muted:#607583;--paper:#f4f6f3;--line:#dce4de;--green:#137a68;--amber:#b47c20;--red:#c9533c}*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1280px;margin:auto;padding:34px 28px 70px}
.eyebrow{font-size:12px;color:var(--green);font-weight:700;letter-spacing:2px}h1{font-size:30px;margin:8px 0}h2{font-size:21px;margin:0 0 8px}h3{font-size:16px;margin:20px 0 6px}
.muted{color:var(--muted)}.small{font-size:12.5px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 26px;margin-top:20px}
.note{padding:10px 14px;border-left:3px solid var(--green);background:#eef7f1;font-size:14px;margin:12px 0}.warn{padding:10px 14px;border-left:3px solid var(--amber);background:#fff8e9;font-size:13.5px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:7px 9px;border-bottom:1px solid #edf1ed;text-align:left;vertical-align:top}th{color:var(--muted);font-size:12px;font-weight:600;background:#f7f9f7}
td.n{text-align:right;font-family:Consolas,monospace;white-space:nowrap}tr.differ td{background:#fff8e9}.grp td{background:#eef2ef;font-weight:700}
.tag{display:inline-block;font-size:11.5px;padding:1px 8px;border-radius:12px;white-space:nowrap}.ok{background:#e3f3ea;color:#0d5a4a}.bad{background:#fbe4de;color:#8b3524}.neu{background:#edf1ed;color:#4a5f56}
.l{font:12.5px Consolas,monospace}.l.ok{background:#e3f3ea;padding:0 5px;border-radius:4px}.l.bad{background:#fbe4de;padding:0 5px;border-radius:4px}
details{margin:6px 0;border:1px solid var(--line);border-radius:10px;padding:8px 14px;background:#fcfdfc}summary{cursor:pointer;font-weight:600;color:var(--green)}
.turn{margin:6px 0;padding:8px 12px;border-left:3px solid #cfdcd4;font-size:13px}.turn.changed{border-color:var(--amber);background:#fffaf0}.who{font-weight:700}
.bars{display:grid;grid-template-columns:140px 1fr 60px;gap:8px;align-items:center;font-size:13px;margin:4px 0}.bar{display:flex;height:18px;border-radius:4px;overflow:hidden;border:1px solid var(--line)}.bar i{display:block;height:100%}
ul{padding-left:22px}li{margin:5px 0}code{font:12.5px Consolas,monospace;background:#f1f5f1;padding:1px 5px;border-radius:4px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:900px){.cols{grid-template-columns:1fr}main{padding:20px 14px}}
'''


def lab(l, gold):
    return f'<span class="l {"ok" if l == gold else "bad"}">{e(l)}</span>'


def seq(labels, gold):
    return ' → '.join(lab(l, gold) for l in labels)


def summary_table(runs, stats):
    h = ('<table><tr><th>运行</th><th>触发辩论</th><th>投票答对（80 条）</th><th>辩论答对（80 条）</th><th>辩论 = 投票</th><th>辩论改对</th><th>辩论改错</th><th>不同但都错</th>'
         '<th>辩论后一致</th><th>其中对</th><th>现状汇总器答对</th></tr>')
    for run in runs:
        s = stats[run['code']]
        same = s['st']['same_ok'] + s['st']['same_bad']
        h += (f'<tr><td><b>{e(run["name"])}</b></td><td class="n">{s["trig"]}</td><td class="n">{s["vote_ok"]}</td><td class="n"><b>{s["deb_ok"]}</b></td>'
              f'<td class="n">{same}/{s["trig"]}</td><td class="n">{s["st"]["fix"]}</td><td class="n">{s["st"]["break"]}</td><td class="n">{s["st"]["diff_bad"]}</td>'
              f'<td class="n">{s["cons"]}/{s["trig"]}</td><td class="n">{s["cons_ok"]}</td><td class="n">{s["summ_ok"]}</td></tr>')
    return h + '</table>'


def sample_table(run):
    h = ('<table><tr><th>样本</th><th>真实</th><th>第 0 轮（图谱 / 音频字幕 / 图像）</th><th>投票</th><th>辩论各轮后（三位专家）</th><th>辩论最终</th><th>投票 vs 辩论</th></tr>')
    for i, s in enumerate(x for x in run['samples'] if x['trig']):
        k, txt = status(s)
        l0 = ' / '.join(lab(s['labels0'][r], s['gold']) for r in ROLES)
        rds = '<br>'.join('第%d轮：' % (n + 1) + ' / '.join(lab(rd[r]['answer'], s['gold']) for r in ROLES) for n, rd in enumerate(s['rounds'])) or '—'
        cls = 'differ' if k in ('fix', 'break', 'diff_bad') else ''
        tcls = 'ok' if k in ('same_ok', 'fix') else 'bad' if k in ('same_bad', 'break', 'diff_bad') else 'neu'
        judge = '（经裁判）' if s['judge'] else ''
        h += (f'<tr class="{cls}"><td><a href="#{run["code"]}-{s["id"].replace("/", "-")}">{e(s["id"])}</a></td><td>{e(s["gold"])}</td><td>{l0}</td><td>{lab(s["vote"], s["gold"])}</td>'
              f'<td>{rds}</td><td>{lab(s["final"], s["gold"])}{judge}</td><td><span class="tag {tcls}">{txt}</span></td></tr>')
    return h + '</table>'


def transcripts(run):
    out = ''
    for s in (x for x in run['samples'] if x['trig']):
        k, txt = status(s)
        out += f'<details id="{run["code"]}-{s["id"].replace("/", "-")}"><summary>{e(s["id"])} · 真实 {e(s["gold"])} · 投票 {e(s["vote"])} · 辩论 {e(s["final"])} · {txt}</summary>'
        out += '<div class="turn"><span class="who">第 0 轮（独立判断，已保存的 v3 输出）</span>'
        for r in ROLES:
            o = s['r0'][r]
            out += f'<br>{RN[r]}：{lab(o["answer"], s["gold"])} · 开放情绪「{e(o.get("open_emotion"))}」 — {e((o.get("reason") or "")[:220])}…'
        out += '</div>'
        for n, rd in enumerate(s['rounds']):
            out += f'<div class="turn"><span class="who">第 {n + 1} 轮辩论</span></div>'
            for r in ROLES:
                o = rd[r]
                ch = bool(o.get('changed'))
                out += (f'<div class="turn {"changed" if ch else ""}"><span class="who">{RN[r]}</span> → {lab(o["answer"], s["gold"])} · 开放情绪「{e(o.get("open_emotion"))}」'
                        f'{" · <b>改变了答案</b>" if ch else " · 坚持"}<br>{e(o.get("response_to_others"))}</div>')
        if s['judge']:
            out += f'<div class="turn changed"><span class="who">裁判</span> → {lab(s["judge"]["answer"], s["gold"])}<br>{e((s["judge"].get("reason") or "")[:500])}</div>'
        out += '</details>'
    return out


def change_table(runs, ch):
    h = ('<table><tr><th>运行</th><th>坚持且答案对</th><th>坚持但答案错</th><th>错 → 对</th><th>对 → 错</th><th>错 → 另一个错</th><th>改答案总数</th><th>其中向"其他专家上一轮的答案"靠拢</th><th>其中向多数靠拢</th></tr>')
    for run in runs:
        c = ch[run['code']]
        tot = c['wrong_to_right'] + c['right_to_wrong'] + c['wrong_to_wrong']
        h += (f'<tr><td><b>{e(run["name"])}</b></td><td class="n">{c["held_right"]}</td><td class="n">{c["held_wrong"]}</td><td class="n">{c["wrong_to_right"]}</td>'
              f'<td class="n">{c["right_to_wrong"]}</td><td class="n">{c["wrong_to_wrong"]}</td><td class="n"><b>{tot}</b></td><td class="n">{c["toward_others"]}/{tot}</td><td class="n">{c["toward_majority"]}/{tot}</td></tr>')
    return h + '</table>'


def minority_table(runs, md):
    h = '<table><tr><th>运行</th><th>孤立的那位专家是…</th><th>样本数</th><th>他在第 1 轮改投多数</th><th>多数方有人被他拉走</th></tr>'
    names = {'minority_right': '对的（少数派答对）', 'majority_right': '错的（多数派答对）', 'both_wrong': '错的（多数也错）'}
    for run in runs:
        c = md[run['code']]
        first = True
        for key in ('minority_right', 'majority_right', 'both_wrong'):
            n = c[(key, 'n')]
            if not n:
                continue
            h += (f'<tr><td>{"<b>" + e(run["name"]) + "</b>" if first else ""}</td><td>{names[key]}</td><td class="n">{n}</td>'
                  f'<td class="n">{c[(key, "yield")]}/{n}</td><td class="n">{c[(key, "majority_member_flipped")]}/{n}</td></tr>')
            first = False
    return h + '</table>'


def build():
    runs = [load_run(*r) for r in RUNS]
    stats = {r['code']: run_stats(r) for r in runs}
    ch = {r['code']: expert_changes(r) for r in runs}
    md = {r['code']: minority_dynamics(r) for r in runs}
    body = f'''<div class="eyebrow">DEBATE VS VOTE</div>
<h1>辩论的过程，以及它和投票到底差在哪</h1>
<p class="muted">"投票"= 三位专家第 0 轮标签取多数（GPT 与 Gemini 的分歧样本都是 2 比 1，没有三方平票）；"辩论"= 不一致时让专家互相看到对方的标签和证据后至多辩论 2 轮。三位专家意见一致的样本两者相同，所以差别只可能出现在触发辩论的样本里。下面汇总三次运行：Gemini 纯文本、Gemini 带原媒体、GPT 带原媒体。</p>
<div class="warn">80 条是被反复使用的开发集；触发辩论的样本只有 15 到 21 条，一条样本等于 1.25 个百分点。以下是现象描述，不是显著性结论。真实标签只用于对错标注。</div>

<section class="panel"><h2>① 总览</h2>{summary_table(runs, stats)}
<p class="muted small">"辩论改对"= 辩论结果对而投票错；"辩论改错"= 投票对而辩论结果错。"辩论后一致"= 辩论结束时三位专家标签相同（其余由裁判决定）。</p></section>

<section class="panel"><h2>② 投票和辩论的结果差在哪</h2>
<div class="note">三次运行里，辩论结果和投票结果不同的样本一共只有 5 条：Gemini 纯文本 0 条，Gemini 带媒体 1 条，GPT 带媒体 4 条。其余 52 条触发样本里，辩论只是把"多数派答案"重新确认了一遍。</div>
{''.join(f'<h3>{e(r["name"])}</h3>{sample_table(r)}' for r in runs)}</section>

<section class="panel"><h2>③ 专家层面：辩论里答案是怎么动的</h2>
<h3>每位专家每轮的答案变化（相对真实标签）</h3>{change_table(runs, ch)}
<p class="muted small">"向多数靠拢"= 新答案等于上一轮三位专家的多数标签。</p>
<h3>2 比 1 分歧里，孤立的那位专家在第 1 轮做了什么</h3>{minority_table(runs, md)}
<p class="muted small">这回答一个关键问题：辩论是在"保护对的少数"，还是只在"确认多数"？</p></section>

<section class="panel"><h2>④ 投票和辩论各有什么好处</h2>
{benefits(runs, stats, ch, md)}</section>

<section class="panel"><h2>⑤ 辩论过程原文</h2>
<p class="muted small">点开每个样本，看第 0 轮判断、每一轮每位专家的答案、是否改变、以及他们对另两位论点的回应（<code>response_to_others</code> 原文）。黄色底的条目表示该专家改变了答案。</p>
{''.join(f'<h3>{e(r["name"])}（{stats[r["code"]]["trig"]} 条）</h3>{transcripts(r)}' for r in runs)}</section>
<p class="muted small" style="margin-top:20px">由 scripts/build_debate_vs_vote.py 生成；静态页面，不依赖脚本，不调用模型。</p>'''
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>辩论与投票</title><style>{CSS}</style></head><body><main>{body}</main></body></html>', runs, stats, ch, md


def benefits(runs, stats, ch, md):
    g = {r['code']: stats[r['code']] for r in runs}
    def chg(code):
        c = ch[code]
        tot = c['wrong_to_right'] + c['right_to_wrong'] + c['wrong_to_wrong']
        return c['wrong_to_right'], c['right_to_wrong'], tot, c['toward_majority']
    def dis(code):
        c = md[code]
        wn = c[('majority_right', 'n')] + c[('both_wrong', 'n')]
        wy = c[('majority_right', 'yield')] + c[('both_wrong', 'yield')]
        return c[('minority_right', 'yield')], c[('minority_right', 'n')], wy, wn
    a, b, t, m_ = chg('gt'); a2, b2, t2, m2 = chg('gm'); a3, b3, t3, m3 = chg('pm')
    d1 = dis('gt'); d2 = dis('gm'); d3 = dis('pm')
    return f'''<div class="cols"><div><h3>投票的好处</h3><ul>
<li><b>几乎零成本。</b>不需要任何新调用；辩论在这批数据里多花了 66 到 73 次调用（Gemini）、59 次（GPT），其中带媒体版约 87 万 / 35.5 万输入 token。</li>
<li><b>稳定，不翻车。</b>投票是确定性的。辩论在 5 个样本上和投票不同，其中 3 个（Gemini 带媒体 1 个、GPT 2 个）是"投票本来对、辩论改错"，这些是投票替你挡住的损失。</li>
<li><b>在这批数据上不比辩论差。</b>三次运行里投票答对 59、59、57；辩论 59、58、56，没有一次高于投票。</li>
<li><b>多数派确实经常是对的。</b>触发的样本里多数派答对的比例：Gemini {g["gm"]["vote_ok_trig"]}/{g["gm"]["trig"]}、GPT {g["pm"]["vote_ok_trig"]}/{g["pm"]["trig"]}，约一半到六成，所以"跟多数走"并不差，但也不能保证。</li></ul></div>
<div><h3>辩论的好处（在这批数据里的证据）</h3><ul>
<li><b>能救回少数派：偶尔。</b>GPT 里有 1 条少数派答对且最终胜出（dia0_utt2），投票在这条是错的。这是三次运行里辩论相对投票唯一"改对"的样本（dia131_utt3 也被辩论判对，但那是相对现状汇总器，投票在那条本来就是对的）。</li>
<li><b>会推翻错误的多数：很少。</b>多数派答错的触发样本里，辩论改对的只有 GPT 的 1 条；Gemini 一条都没有。</li>
<li><b>单个专家平均会变准一点。</b>专家改答案时，错→对多于对→错：Gemini 纯文本 {a} 次对 {b} 次，带媒体 {a2} 对 {b2}，GPT {a3} 对 {b3}。但改答案的绝大多数是向多数靠拢（{m_}/{t}、{m2}/{t2}、{m3}/{t3}），这种改进等价于"少数派服从多数"，没有产生超出投票的新信息。</li>
<li><b>有"解释"可读。</b>辩论留下了专家互相反驳的文字，便于排查是感知问题还是推理问题（见第 ⑤ 节）。投票只有一个标签。</li>
<li><b>促成一致。</b>辩论后大多数样本三位专家意见一致（Gemini 纯文本 20/21、带媒体 21/21，GPT 13/15，其余由裁判决定）。但一致不等于正确：一致后答错的有 Gemini 纯文本 9 条、带媒体 10 条，GPT 7 条。</li></ul></div></div>
<h3>两者都碰不到的</h3><ul>
<li><b>三位专家一致地错。</b>这些样本既不触发辩论，投票也无能为力：Gemini 12 条、GPT 15 条（v3）。</li>
<li><b>辩论不会区分对的少数和错的少数。</b>孤立的那位专家改投多数的比例：Gemini 纯文本 对的 {d1[0]}/{d1[1]}、错的 {d1[2]}/{d1[3]}；Gemini 带媒体 对的 {d2[0]}/{d2[1]}、错的 {d2[2]}/{d2[3]}；GPT 对的 {d3[0]}/{d3[1]}、错的 {d3[2]}/{d3[3]}。Gemini 里对的和错的几乎一样容易被说服；GPT 样本太少，只能说方向略有差别。</li>
<li><b>少数派答对但被多数压过。</b>Gemini 的 4 条少数派答对（多数都判 neutral）两个版本都全部丢了；GPT 的 3 条里丢了 2 条。辩论没有表现出"保护对的少数"的能力。</li></ul>
<div class="note"><b>小结：</b>在这批数据里，辩论 ≈ 投票 + 额外成本 + 少量双向翻转（有改对，也有改错）。它的价值不在准确率，而在留下可读的论证记录。要让辩论真正胜过投票，需要新信息进入辩论（异质模型、工具、不同的数据来源），而不是同一个模型的多个角色再讨论一轮。</div>'''


def main():
    html, runs, stats, ch, md = build()
    out = ROOT / 'docs' / 'debate-vs-vote.html'
    out.write_text(html, encoding='utf8')
    print(out, out.stat().st_size // 1024, 'KB')
    for r in runs:
        s = stats[r['code']]
        print(f"\n== {r['name']}: n={s['n']} triggered={s['trig']} vote_ok={s['vote_ok']} debate_ok={s['deb_ok']} summary_ok={s['summ_ok']}")
        print('   vs-vote:', dict(s['st']), '| consensus', s['cons'], 'correct', s['cons_ok'], '| judged', s['judged'], '| vote_ok_on_triggered', s['vote_ok_trig'], 'debate_ok_on_triggered', s['deb_ok_trig'])
        print('   expert changes:', {k: v for k, v in ch[r['code']].items()})
        print('   minority:', {f'{k[0]}:{k[1]}': v for k, v in md[r['code']].items()})


if __name__ == '__main__':
    main()
