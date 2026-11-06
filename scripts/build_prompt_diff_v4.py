"""Build docs/v3-v4-prompt-diff.html: v3 vs v4 DRAFT prompts (MER2024 rendering), for review before any v4 run.

The prompts are rendered by the real code (versions/v3 and versions/v4/emotion_wheel_prompts.py). Static HTML, no
scripts, no model calls. Usage: python scripts/build_prompt_diff_v4.py
"""
import difflib
import importlib
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(version):
    for m in ('prompts_base', 'emotion_wheel_prompts'):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(ROOT / 'versions' / version))
    mod = importlib.import_module('emotion_wheel_prompts')
    sys.path.pop(0)
    return mod


V3, V4 = load('v3'), load('v4')
CLASSES = ['happy', 'angry', 'sad', 'worried', 'surprise', 'neutral']
ROLE = {'graph': '图谱专家', 'audio_subtitle': '音频字幕专家', 'image': '图像专家'}


def diff_block(old, new):
    """Line diff; changed line pairs get a word-level highlight so long Chinese lines stay readable."""
    out = []
    a, b = old.split('\n'), new.split('\n')
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            n = i2 - i1
            if n > 2:
                out.append('<div class="ctx">%s</div>' % escape(a[i1]))
                out.append('<div class="fold">… 此处 %d 行与 v3 完全相同，已折叠 …</div>' % (n - 2))
                out.append('<div class="ctx">%s</div>' % escape(a[i2 - 1]))
            else:
                out += ['<div class="ctx">%s</div>' % escape(x) for x in a[i1:i2]]
        else:
            if tag == 'replace' and i2 - i1 == 1 and j2 - j1 == 1:
                s = difflib.SequenceMatcher(None, a[i1], b[j1], autojunk=False)
                d1, d2 = [], []
                for t, x1, x2, y1, y2 in s.get_opcodes():
                    if t == 'equal':
                        d1.append(escape(a[i1][x1:x2])); d2.append(escape(b[j1][y1:y2]))
                    else:
                        if x2 > x1: d1.append('<mark>%s</mark>' % escape(a[i1][x1:x2]))
                        if y2 > y1: d2.append('<mark>%s</mark>' % escape(b[j1][y1:y2]))
                out.append('<div class="del">%s</div><div class="add">%s</div>' % (''.join(d1), ''.join(d2)))
            else:
                out += ['<div class="del">%s</div>' % escape(x) for x in a[i1:i2]]
                out += ['<div class="add">%s</div>' % escape(x) for x in b[j1:j2]]
    return '<div class="diff">%s</div>' % ''.join(out)


def plain(text):
    return '<div class="diff">%s</div>' % ''.join('<div class="add">%s</div>' % escape(x) for x in text.split('\n'))


def stat(old, new):
    ops = difflib.SequenceMatcher(None, old.split('\n'), new.split('\n'), autojunk=False).get_opcodes()
    same = sum(i2 - i1 for t, i1, i2, _, _ in ops if t == 'equal')
    return len(old.split('\n')), len(new.split('\n')), same


css = '''body{font:15px/1.65 "Microsoft YaHei",sans-serif;max-width:1180px;margin:24px auto;padding:0 18px;color:#222;background:#fafafa}
h1{font-size:24px}h2{font-size:19px;border-bottom:2px solid #ddd;padding-bottom:4px;margin-top:34px}h3{font-size:16px;margin:22px 0 6px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 18px 16px;margin:14px 0}
table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border:1px solid #ccc;padding:5px 9px;text-align:left;vertical-align:top}th{background:#eef}
.muted{color:#666}.warn{background:#fff4e0;border-left:4px solid #e90;padding:8px 12px;margin:10px 0}.note{background:#eaf4ff;border-left:4px solid #48c;padding:8px 12px;margin:10px 0}
.diff{font:12.5px/1.55 Consolas,"Microsoft YaHei",monospace;border:1px solid #ccc;border-radius:4px;overflow:hidden;margin:6px 0}
.diff div{padding:1px 8px;white-space:pre-wrap;word-break:break-all}.ctx{color:#555;background:#fff}.fold{color:#888;background:#f0f0f0;font-style:italic}
.add{background:#e6ffed;border-left:3px solid #2a2}.del{background:#ffeef0;border-left:3px solid #c33}
mark{background:#ffd54f;padding:0}.tag{display:inline-block;background:#fde;border-radius:3px;padding:0 6px;font-size:12px;margin-left:6px}
code{background:#eee;padding:0 4px;border-radius:3px}'''

p = []
p.append('<h1>v4 与 v3 的提示词区别（草案，待审核）</h1>')
p.append('<p class="muted">日期 2026-11-03。以下全部由真实代码渲染（<code>versions/v3/emotion_wheel_prompts.py</code> 与 <code>versions/v4/emotion_wheel_prompts.py</code>，MER2024 六类）。'
         '<b>v4 尚未运行，没有调用任何模型</b>；你审核通过后才会开始实现流水线并运行。绿色 = v4 新增或改动，红色 = v3 原文被替换，黄色高亮 = 同一行里具体改了哪几个字。</p>')

p.append('<section class="panel"><h2>一、一页看懂：哪些没变，哪些变了</h2>')
rows = [
    ('组织文本（organization）', '不变', 'v4 直接 <code>ORGANIZATION = base.ORGANIZATION</code>，与 v3 逐字相同；图谱专家仍用组织文本。'),
    ('三位专家的角色与四条评分准则', '不变', '每个角色的 4 条 rubric、情绪轮、易混边界、证据格式沿用 v3，一个字没改。'),
    ('Round 0 专家：输出模式', '<b>改</b>', '默认仍是 1 个答案；<b>只在真正两难时</b>才可再给 1 个备选（<code>alt_answer</code> / <code>alt_open_emotion</code> / <code>uncertainty_reason</code>）。没有两难时这三个字段写 null。'),
    ('反思（reflection）', '<b>新增</b>', '每位专家对每条样本都做；只看原媒体 + 自己 Round 0 的完整输出；逐条核对证据、找最强反证、检查映射；可改可不改；输出多 <code>changed</code>、<code>reflection</code>；仍允许 1–2 个答案。'),
    ('辩论（debate）', '<b>新增</b>', '只在“三位答案集合没有恰好 1 个共同标签”时触发；看到另两位反思后的答案（含备选）、证据、反证和原媒体；<b>给出 1 个答案</b>，从候选并集中选；输出格式已写入提示词（<code>changed</code>、<code>adopted_evidence</code>、<code>response_to_others</code>）；<b>改变自己或劝说对方都需要引用证据</b>。'),
    ('汇总器（summary）', '<b>小改</b>', 'v3 汇总提示词主体保留；删去“而非投票、篇幅或引用条数”和“不能按映射标签多数投票”两处；末尾追加 <code>【汇总输入与引用】</code>：看到完整历史；<code>evidence_refs</code> 汇集<b>三位专家任一阶段</b>的证据，写作“角色:阶段:E编号”。'),
    ('路由', '代码，非提示词', '“共同标签”= 三位答案集合的交集。恰好 1 个 → 直接输出；0 个或多于 1 个 → 辩论；辩论后三个单答案一致 → 采纳，否则 → 汇总器。按你的决定，共同标签可以只靠备选凑出，不做额外限制。'),
]
p.append('<table><tr><th>环节</th><th>相对 v3</th><th>说明</th></tr>%s</table>' % ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % r for r in rows))
p.append('<div class="note">这些文本里没有出现“多数专家怎么说”的提示，也没有告诉专家真实标签的先验分布；备选答案的规则改写为正向说法（什么情况下可以给、怎么填），不再出现“不是保险”之类的禁止语。<br><b>已按你的 4 点修改</b>：① 所有 v4 提示词文本中不含 v3/v4 字样；② 辩论提示词写明完整输出格式，并要求改变自己或劝说对方时引用证据；③ 汇总器删掉“按人数投票”一句，evidence_refs 改为可汇集多位专家；④ 新增文本全部改成“可以做什么”的写法。<br><b>仍保留的禁止语</b>：来自 v3 原文的四条 rubric、通用证据规则和情绪轮边界（每个专家提示词里约 15 处，如“不自动等于neutral”“不把图谱当真值”），这些我没有动，因为改了就不再是“只改流程”的对照；如果你也想改成正向写法，告诉我，我另出一版。</div></section>')

# --- Round 0
p.append('<section class="panel"><h2>二、Round 0 专家：v3 → v4 的逐行差异</h2>')
p.append('<p class="muted">三位专家的改动完全相同（只有角色名和各自的 rubric 不同，而 rubric 没有改），所以下面先展示图谱专家的完整差异，另两位只给统计。</p>')
for k, role in enumerate(ROLE):
    a, b = V3.expert(role, CLASSES), V4.expert(role, CLASSES)
    n_old, n_new, same = stat(a, b)
    if k == 0:
        p.append('<h3>%s</h3>%s' % (ROLE[role], diff_block(a, b)))
    p.append('<p class="muted"><b>%s</b>：v3 共 %d 行、%d 字符；v4 共 %d 行、%d 字符；其中 %d 行逐字相同。</p>' % (ROLE[role], n_old, len(a), n_new, len(b), same))
p.append('</section>')

# --- reflection / debate: new text
p.append('<section class="panel"><h2>三、新增：反思提示词</h2>')
p.append('<p class="muted">反思用的 system prompt = 角色 rubric + 通用证据规则 + 情绪轮（与 Round 0 相同）+ 下面这一段（含输出格式；对三位专家相同）。用户消息里除原媒体外，附上 <code>your_previous_output</code>（自己 Round 0 的完整 JSON）；<b>不附</b>另两位专家的任何内容。</p>')
p.append(plain(V4.REFLECT_NOTE.strip('\n')))
p.append('</section>')

p.append('<section class="panel"><h2>四、新增：辩论提示词</h2>')
p.append('<p class="muted">辩论的 system prompt = 角色 rubric + 通用证据规则 + 情绪轮（与 Round 0 相同）+ 下面这一段（含输出格式）。用户消息里除原媒体外，附上：自己反思后的输出、另两位反思后的完整 JSON（含备选、证据、反证）、<code>candidate_labels</code>（三位到目前为止提出过的全部标签并集）。第二轮辩论额外附上上一轮另两位的单答案与 <code>response_to_others</code>。</p>')
p.append(plain(V4.DEBATE_NOTE.strip('\n')))
p.append('<div class="warn">与之前条件辩论的提示词（<code>DEBATE_NOTE_MEDIA</code>）相比：增加了完整输出格式、<code>adopted_evidence</code>（改变自己时引用对方证据）、<code>response_to_others</code> 每条必须带可定位证据、答案限定在 <code>candidate_labels</code> 内。实现时我打算对输出做校验（见第七节第 3 点，待你确认）。</div></section>')

# --- summary
p.append('<section class="panel"><h2>五、汇总器：v3 → v4 的逐行差异</h2>')
p.append(diff_block(V3.summary(CLASSES), V4.summary(CLASSES)))
n_old, n_new, same = stat(V3.summary(CLASSES), V4.summary(CLASSES))
p.append('<p class="muted">v3 共 %d 行，v4 共 %d 行，%d 行逐字相同；只在末尾追加 <code>【汇总输入与引用】</code> 段，并改了上面三处。汇总器的用户消息：原媒体 + 三位专家 Round 0、反思、辩论各轮的完整输出 + 三位最后的单答案。</p></section>' % (n_old, n_new, same))

# --- I/O + cost
p.append('<section class="panel"><h2>六、每一步用户消息里放什么（提示词之外的输入）</h2>')
p.append('''<table><tr><th>阶段</th><th>媒体</th><th>文本输入</th><th>输出 JSON 新增字段</th></tr>
<tr><td>Round 0</td><td>与 v3 相同（8 帧、可用音轨、字幕；图谱专家另有图谱与组织文本）</td><td>与 v3 相同</td><td><code>alt_answer</code>、<code>alt_open_emotion</code>、<code>uncertainty_reason</code>（多数为 null）</td></tr>
<tr><td>反思</td><td>同上</td><td>自己 Round 0 的完整输出</td><td>+ <code>changed</code>、<code>reflection</code></td></tr>
<tr><td>辩论 R1 / R2</td><td>同上</td><td>自己反思后输出；另两位反思后输出；<code>candidate_labels</code>；（R2：上一轮另两位的答案与回应）</td><td><code>alt_*</code> 固定 null；+ <code>changed</code>、<code>response_to_others</code></td></tr>
<tr><td>汇总</td><td>同上</td><td>三位完整历史</td><td>与 v3 相同：<code>reason</code>、<code>answer</code>、<code>evidence_refs</code></td></tr></table>''')
p.append('<h3>调用量（80 条验证集，每个模型）</h3>')
p.append('<p>Round 0：240 次（需要重跑，不能复用 v3 已保存的专家输出，因为 schema 变了）；反思：240 次；辩论与汇总只对没有“恰好 1 个共同标签”的样本触发，比例要跑完才知道（此前条件辩论的不一致比例 19%–26%，v4 的路由更宽松或更严格取决于备选的使用频率）。每条触发辩论的样本最多再加 3×2 次辩论调用 + 1 次汇总。</p>')
p.append('</section>')

p.append('<section class="panel"><h2>七、需要你确认的点（审核通过后我才会开始跑）</h2><ol>'
         '<li><b>备选答案的措辞</b>（第二节绿色段落）：“通常给一个；确实难以取舍时可以再给一个备选”。是否要更严或更松？</li>'
         '<li><b>证据引用写法</b>：汇总器里证据带阶段标记，写作“角色:阶段:E编号”（如 image:reflect:E1），因为各阶段的 E1、E2 会重复。是否同意？</li>'
         '<li><b>反思取向</b>：“出现新的可定位证据时才改，证据没变就保持原答案”（第三节第 3 条）。是否同意？</li>'
         '<li><b>辩论的无效输出处理（我的提议）</b>：答案不在候选并集内或带备选 → 重试 1 次 → 仍无效沿用上一轮主答案并记录。是否同意？</li>'
         '<li>跑哪些模型：GPT、Gemini 各 80 条 MER2024 验证集？MELD 40 条是否一并跑（提示词已按数据集自动渲染）？</li></ol>'
         '<p class="muted">本验证集是开发过程中反复使用的数据，不是独立证据；v4 结果只能与同一 80 条上的 Direct / v3 / 多数投票对比，不能作为泛化结论。</p></section>')

html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>v3 与 v4 提示词区别（草案）</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(p))
out = ROOT / 'docs' / 'v3-v4-prompt-diff.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html))
