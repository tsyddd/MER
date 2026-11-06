"""Build docs/v3-prompt-wheel.html: where v3's emotion-wheel prompt text goes (experts / summary / organization).

The prompts are rendered by the real v3 code (versions/v3/emotion_wheel_prompts.py), so the page shows
exactly what is sent as system prompts. Static HTML, no scripts, no model calls.
Usage: python scripts/build_prompt_view.py
"""
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'versions' / 'v3'))
sys.path.insert(0, str(ROOT))
import emotion_wheel_prompts as P  # noqa: E402

DATASETS = list(P.WHEELS['datasets'])
KEY = {'MER2024': '没有独立fear类别', 'MELD': '担忧、焦虑、紧张不是自动fear'}
STAGE_INPUT = {
    'organization': '图谱（含字幕）；不接图片、音频',
    'expert_graph': '8 帧 + 字幕（+音轨）+ 图谱 + 组织文本',
    'expert_audio_subtitle': '8 帧 + 字幕（+音轨）；无图谱',
    'expert_image': '8 帧 + 字幕（+音轨）；无图谱',
    'summary': '8 帧 + 字幕（+音轨）+ 三位专家输出；无图谱',
}
LABEL = {'organization': '组织文本', 'expert_graph': '图谱专家', 'expert_audio_subtitle': '音频字幕专家',
         'expert_image': '图像专家', 'summary': '汇总器'}


def stages(ds):
    c = P.WHEELS['datasets'][ds]['labels']
    return {'organization': P.ORGANIZATION, 'expert_graph': P.expert('graph', c),
            'expert_audio_subtitle': P.expert('audio_subtitle', c), 'expert_image': P.expert('image', c),
            'summary': P.summary(c)}


def split(text):
    """role+rubric | wheel definition+principles | boundaries | v3 tail"""
    w = re.search(r'【[^】]*项目适配情绪轮】', text)
    if not w:
        return [('plain', text)]
    i_b = text.index('【易混边界与类别缺失】')
    tail = [text.find('【v3输出要求】'), text.find('【v3汇总】')]
    i_t = min(x for x in tail if x >= 0)
    return [('role', text[:w.start()]), ('wheel', text[w.start():i_b]), ('bound', text[i_b:i_t]), ('tail', text[i_t:])]


def seg_html(text, ds):
    out = ''
    for kind, s in split(text):
        body = escape(s)
        if kind == 'bound':
            body = '\n'.join(f'<mark>{escape(l)}</mark>' if KEY[ds] in l else escape(l) for l in s.split('\n'))
        out += f'<span class="seg {kind}">{body}</span>'
    return out


def bar(text):
    segs = split(text)
    total = sum(len(s) for _, s in segs)
    names = {'role': '角色 + 4 条 rubric', 'wheel': '情绪轮定义 + 映射原则', 'bound': '易混边界', 'tail': '本阶段输出要求', 'plain': '全文'}
    return '<div class="stack">' + ''.join(
        f'<div class="b {k}" style="width:{100 * len(s) / total:.1f}%" title="{names[k]}：{len(s)} 字符">{names[k]}<small>{len(s)}</small></div>'
        for k, s in segs) + '</div>'


def version_rows():
    rows = []
    for name, f in [('v1', 'frozen_graph_expert_prompts.py'), ('v2', 'shared_media_expert_prompts_v2.py'), ('v3', 'versions/v3/emotion_wheel_prompts.py')]:
        text = (ROOT / f).read_text(encoding='utf8')
        snippets = [escape(m.group(0)) for m in re.finditer(r'[^。\n]{0,28}情绪轮[^。\n]{0,24}', text)][:3]
        rows.append((name, f, len(re.findall('情绪轮', text)), snippets))
    return rows


CSS = '''
:root{--ink:#172c38;--muted:#607583;--paper:#f4f6f3;--line:#dce4de;--green:#137a68;--amber:#b47c20;--red:#c9533c}*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1240px;margin:auto;padding:34px 28px 60px}
.eyebrow{font-size:12px;color:var(--green);font-weight:700;letter-spacing:2px}h1{font-size:30px;margin:8px 0}h2{font-size:20px;margin:0 0 8px}h3{font-size:15px;margin:18px 0 6px}
.muted{color:var(--muted)}.small{font-size:12.5px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 24px;margin-top:18px}
.warn{margin-top:14px;padding:10px 14px;border-left:3px solid var(--amber);background:#fff8e9;font-size:13px}.note{margin-top:12px;padding:10px 14px;border-left:3px solid var(--green);background:#eef7f1;font-size:13.5px}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{padding:8px 10px;border-bottom:1px solid #edf1ed;text-align:left;vertical-align:top}th{color:var(--muted);font-size:12.5px;font-weight:600}
.y{color:#0d5a4a;font-weight:700}.n{color:#a2412d;font-weight:700}code{font:12.5px Consolas,monospace;background:#f1f5f1;padding:1px 5px;border-radius:4px}
.stack{display:flex;height:46px;border-radius:8px;overflow:hidden;margin:6px 0 14px;border:1px solid var(--line)}.b{display:flex;flex-direction:column;justify-content:center;padding:0 8px;font-size:12px;overflow:hidden;white-space:nowrap}.b small{font:11px Consolas,monospace;opacity:.7}
.b.role,.seg.role{background:#eaf1ff}.b.wheel,.seg.wheel{background:#e6f4ee}.b.bound,.seg.bound{background:#fff3da}.b.tail,.seg.tail{background:#f1e9fb}.b.plain,.seg.plain{background:#f4f6f3}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;margin:6px 0}.legend i{display:inline-block;width:13px;height:13px;border-radius:3px;vertical-align:-2px;margin-right:5px;border:1px solid #cfdcd4}
pre{white-space:pre-wrap;word-break:break-word;margin:8px 0;font:13px/1.8 "Microsoft YaHei",Consolas,monospace;border:1px solid var(--line);border-radius:10px;overflow:hidden}.seg{display:block;padding:10px 14px}
mark{background:#ffd9d2;color:#7a2616;font-weight:700;padding:1px 2px;border-radius:3px;display:inline}
details{margin:8px 0;border:1px solid var(--line);border-radius:10px;padding:8px 14px;background:#fcfdfc}summary{cursor:pointer;font-weight:600;color:var(--green)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:900px){.cols{grid-template-columns:1fr}main{padding:20px 14px}}
'''


def main():
    ds_main = 'MER2024'
    st = stages(ds_main)
    rows = ''
    for k, t in st.items():
        has = bool(re.search(r'项目适配情绪轮', t))
        fear = KEY[ds_main] in t
        rows += (f'<tr><td><b>{LABEL[k]}</b></td><td class="muted">{STAGE_INPUT[k]}</td>'
                 f'<td class="{"y" if has else "n"}">{"✓ 有" if has else "✗ 无"}</td><td class="{"y" if fear else "n"}">{"✓ 有" if fear else "✗ 无"}</td><td>{len(t)}</td></tr>')
    stacks = ''.join(f'<h3>{LABEL[k]}</h3>{bar(st[k])}' for k in ['expert_image', 'summary'])
    prompts = ''
    for ds in DATASETS:
        s = stages(ds)
        prompts += f'<h3>{ds}（{len(P.WHEELS["datasets"][ds]["labels"])} 类）</h3>'
        for k in ['expert_graph', 'expert_audio_subtitle', 'expert_image', 'summary', 'organization']:
            prompts += f'<details><summary>{LABEL[k]}：完整系统提示词（{len(s[k])} 字符）</summary><pre>{seg_html(s[k], ds)}</pre></details>'
    vrows = ''.join(f'<tr><td><b>{n}</b></td><td><code>{f}</code></td><td>{c}</td><td class="muted small">{"<br>".join(sn) or "—"}</td></tr>' for n, f, c, sn in version_rows())
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>v3 情绪轮提示词去向</title><style>{CSS}</style></head><body><main>
<div class="eyebrow">PPCT / V3 PROMPT</div><h1>v3 的情绪轮提示词给了谁</h1>
<p class="muted">下面的提示词文本由 v3 代码（<code>versions/v3/emotion_wheel_prompts.py</code>）实际渲染得到，就是发给模型的系统提示词；本页面不调用模型，内容为静态渲染。</p>
<div class="note"><b>一句话：</b>情绪轮（含“没有独立 fear 类别……近似映射 worried”）发给了<b>三个专家和汇总器</b>，没有发给<b>组织文本</b>。专家用它做“开放情绪词 → 标签”的映射；汇总器只用它“核对语义”，自己不做映射。</div>

<section class="panel"><h2>① 哪个阶段拿到了这段提示词（以 MER2024 为例）</h2>
<table><tr><th>阶段</th><th>该阶段的输入</th><th>含情绪轮</th><th>含 fear 规则</th><th>提示词长度（字符）</th></tr>{rows}</table>
<p class="muted small">MELD 的 7 类轮同样给了四个角色、不给组织文本；但 MELD 有独立的 fear 和 disgust，所以没有“没有独立 fear 类别”这一条，对应的是“担忧、焦虑、紧张不是自动fear”。</p></section>

<section class="panel"><h2>② 提示词是怎么拼起来的（MER2024，条宽按字符数）</h2>
<div class="legend"><span><i style="background:#eaf1ff"></i>角色 + 4 条 rubric</span><span><i style="background:#e6f4ee"></i>情绪轮定义 + 共同映射原则</span><span><i style="background:#fff3da"></i>易混边界（fear 规则在这里）</span><span><i style="background:#f1e9fb"></i>本阶段输出要求</span></div>
{stacks}
<div class="cols"><div><b>专家（图谱 / 音频字幕 / 图像）</b><p class="small muted">结尾是 <code>【v3输出要求】</code>：先给<b>一个开放情绪词</b>，再按上面的轮映射成<b>一个标签</b>，并写 <code>mapping_reason</code>。所以 fear 规则直接影响每个专家的映射。</p></div>
<div><b>汇总器</b><p class="small muted">结尾是 <code>【v3汇总】</code>：专家的开放情绪只是解释，answer 只是映射意见；“参考 mapping_reason 和原始证据判断，不能按映射标签多数投票”。汇总器只输出一个最终标签，不输出开放情绪。</p></div></div></section>

<section class="panel"><h2>③ 完整提示词（红色高亮 = 与 fear 有关的那一行）</h2>
<p class="muted small">点开每个阶段查看。颜色与上面的图例一致。组织文本的提示词里没有情绪轮。</p>{prompts}</section>

<section class="panel"><h2>④ 只有 v3 带情绪轮</h2>
<table><tr><th>版本</th><th>提示词文件</th><th>“情绪轮”出现次数</th><th>相关原文</th></tr>{vrows}</table>
<div class="warn">v1、v2 的专家提示词里要么没有情绪轮，要么明确写“不使用情绪轮”；v2 的汇总器写的是“不使用情绪轮映射”，v3 把它替换为“参考本数据集适配轮核对语义”。因此“worried 被过度预测”在 Direct、原始 PPCT、v1、v2 里同样出现（这些提示词都没有这条 fear 规则），不能归因于这条规则。</div></section>
<p class="muted small" style="margin-top:20px">由 scripts/build_prompt_view.py 生成。</p></main></body></html>'''
    out = ROOT / 'docs' / 'v3-prompt-wheel.html'
    out.write_text(page, encoding='utf8')
    print(out, len(page) // 1024, 'KB')


if __name__ == '__main__':
    main()
