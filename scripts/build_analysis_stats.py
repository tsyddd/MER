"""Generate metrics/analysis_stats_20261102.md from saved outputs (no model calls).

All numbers in the document are computed here from outputs/ and data/manifests/validation.jsonl.
Gold labels are used only for evaluation. Usage: python scripts/build_analysis_stats.py
"""
import json
import re
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs'
PROVS = ['gpt', 'gemini', 'omni']
VERS = {'v1': 'gemini_graph_three_experts_v1', 'v2': 'gemini_graph_shared_media_v2', 'v3': 'gemini_graph_emotion_wheel_v3'}
ROLES = ['graph', 'audio_subtitle', 'image']
RNAME = {'graph': '图谱专家', 'audio_subtitle': '音频字幕专家', 'image': '图像专家', 'summary': '汇总器'}
ORDER = {'MER2024': ['happy', 'angry', 'sad', 'worried', 'surprise', 'neutral'],
         'MELD': ['joy', 'anger', 'sadness', 'fear', 'disgust', 'surprise', 'neutral']}
ABSTAIN = re.compile('无法(进一步)?(明确|判断|确定|得出)|无法仅凭|无法凭|材料不足|不足以(明确|判断|确定)|仍无法|无从判断')
EMO = re.compile('紧张|困惑|沮丧|无助|焦急|焦虑|愉悦|愉快|轻松|戏谑|调侃|嘲讽|讽刺|低落|沉郁|沉抑|不满|愤怒|恼|惊讶|意外|错愕|期待|担忧|顾虑|忧虑|尴尬|局促|从容|平静|冷静|沉稳|笃定|悲伤|难过|开心|高兴|恐惧|害怕|慌|疑惑|怀疑|质疑|愧疚|无奈|失落|兴奋|热情|自信|耐心|关切|关心|焦躁|不安|犹豫|庆幸|勉强|享受|得意|满意|厌恶|反感|心理状态|应对状态|互动状态|心理应对')
FLAT = re.compile('平缓|平稳|平静|平和|克制|自然|适中|放松|温和|日常')
AFFECT = re.compile('皱眉|蹙|紧锁|紧皱|瞪|圆睁|睁大|微笑|笑|哭|泪|哽咽|颤|叹|咬|撇|咧|扬起|上扬|皱|紧绷|高亢|急促|尖|低沉|颤抖|怒|惊|冷笑')

ROWS = [json.loads(x) for x in (ROOT / 'data/manifests/validation.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
GOLD = {r['id']: r['label'] for r in ROWS}
DS = {r['id']: r['dataset'] for r in ROWS}


def jread(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf8'))
    except Exception:
        return None


def results(mode, prov):
    out = {}
    for i in GOLD:
        r = jread(OUT / mode / prov / i / 'result.json')
        if r and r.get('status') == 'success':
            out[i] = r
    return out


def pct(a, b):
    return f'{100 * a / b:.1f}%' if b else '-'


def table(head, rows):
    return '\n'.join(['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] * len(head)) + '|'] + ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows])


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def last_sentence(text):
    k = text.rfind('这些表现可能反映')
    if k >= 0:
        return text[k:]
    s = [x for x in re.split('(?<=。)', text.strip()) if x]
    return s[-1] if s else ''


def expert_answers(ver, prov, i):
    f = OUT / VERS[ver] / prov / i
    es = [jread(f / f'expert_{r}.json') for r in ROLES]
    s = jread(f / 'summary.json')
    if not s or any(e is None or 'answer' not in e for e in es):
        return None
    return [e['answer'] for e in es], s['answer']


def sec_paired():
    rows = []
    for p in PROVS:
        D, P = results('direct', p), results('ppct', p)
        ids = [i for i in P if i in D]
        k = Counter()
        for i in ids:
            d, q = D[i]['prediction'] == GOLD[i], P[i]['prediction'] == GOLD[i]
            k['both' if d and q else 'fix' if q else 'break' if d else 'none'] += 1
        n = len(ids)
        dacc, pacc = sum(D[i]['prediction'] == GOLD[i] for i in ids), sum(P[i]['prediction'] == GOLD[i] for i in ids)
        rows.append([p, n, f'{dacc} ({pct(dacc, n)})', f'{pacc} ({pct(pacc, n)})', k['both'], k['fix'], k['break'], k['none'],
                     f"{k['fix'] - k['break']:+d}", f"{mcnemar(k['fix'], k['break']):.3f}"])
    return table(['模型', '样本', 'Direct 答对', '原始 PPCT 答对', '都对', 'Direct 错→PPCT 对', 'Direct 对→PPCT 错', '都错', '净变化(条)', 'McNemar 精确 p'], rows)


def sec_neutral():
    rows = []
    for p in PROVS:
        D, P = results('direct', p), results('ppct', p)
        for ds in ORDER:
            ids = [i for i in P if i in D and DS[i] == ds]
            gn = sum(GOLD[i] == 'neutral' for i in ids)
            dn = sum(D[i]['prediction'] == 'neutral' for i in ids)
            pn = sum(P[i]['prediction'] == 'neutral' for i in ids)
            dtp = sum(D[i]['prediction'] == 'neutral' == GOLD[i] for i in ids)
            ptp = sum(P[i]['prediction'] == 'neutral' == GOLD[i] for i in ids)
            rows.append([p, ds, len(ids), gn, f'{dn}（命中 {dtp}）', f'{pn}（命中 {ptp}）'])
    return table(['模型', '数据集', '样本', '真实 neutral', 'Direct 预测 neutral', '原始 PPCT 预测 neutral'], rows)


def sec_org():
    rows, grows = [], []
    for p in PROVS:
        P = results('ppct', p)
        n = ab = emo = abacc = nonabacc = 0
        nodes, flat, aff = [], [], []
        for i, r in P.items():
            org = jread(OUT / 'ppct' / p / i / 'organization.json')
            if not org:
                continue
            n += 1
            tail = last_sentence(org['text'])
            is_ab = bool(ABSTAIN.search(tail))
            ab += is_ab
            emo += bool(EMO.search(tail)) and not is_ab
            if is_ab:
                abacc += r['prediction'] == GOLD[i]
            else:
                nonabacc += r['prediction'] == GOLD[i]
            g = jread(OUT / 'ppct' / p / i / 'graph.json')
            if g:
                nodes.append(len(g['nodes']))
                pn = [x['content'] for x in g['nodes'] if x['type'] == 'person']
                flat.append(sum(bool(FLAT.search(c)) for c in pn) / max(1, len(pn)))
                aff.append(sum(bool(AFFECT.search(c)) for c in pn) / max(1, len(pn)))
        m = lambda xs: f'{sum(xs) / len(xs):.2f}' if xs else '-'
        rows.append([p, n, f'{ab}/{n}', f'{emo}/{n}', f'{abacc}/{ab}' if ab else '-', f'{nonabacc}/{n - ab}' if n - ab else '-'])
        grows.append([p, len(nodes), m(nodes), m(flat), m(aff)])
    return (table(['模型', '组织文本数', '末句写“无法明确心理状态”', '末句含情绪/心理状态词（下限）', '弃权组 PPCT 答对', '非弃权组 PPCT 答对'], rows),
            table(['模型', '图谱数', '节点数/样本', 'Person 节点含“平缓/克制”类词的比例', 'Person 节点含表情/语气质感词的比例'], grows))


def sec_roles(ver='v3'):
    rows = []
    for p in PROVS:
        cell = {r: [0, 0, 0, 0] for r in ROLES + ['summary']}
        for i in GOLD:
            f = OUT / VERS[ver] / p / i
            s = jread(f / 'summary.json')
            es = {r: jread(f / f'expert_{r}.json') for r in ROLES}
            if not s or any(e is None or 'answer' not in e for e in es.values()):
                continue
            for r in ROLES + ['summary']:
                a = s['answer'] if r == 'summary' else es[r]['answer']
                idx = 0 if DS[i] == 'MER2024' else 2
                cell[r][idx] += a == GOLD[i]
                cell[r][idx + 1] += 1
        for r in ROLES + ['summary']:
            c = cell[r]
            t, n = c[0] + c[2], c[1] + c[3]
            rows.append([p, RNAME[r], f'{c[0]}/{c[1]}', f'{c[2]}/{c[3]}', f'**{t}/{n} = {pct(t, n)}**'])
    return table(['模型', '角色', 'MER2024', 'MELD', '合计'], rows)


def sec_labels(prov):
    D, P = results('direct', prov), results('ppct', prov)
    cols = ['direct', 'ppct', 'graph', 'audio_subtitle', 'image', 'summary']
    head = ['真实标签', '条数', 'Direct', '原始 PPCT', '图谱专家', '音频字幕专家', '图像专家', 'v3 汇总']
    text = ''
    for ds in ORDER:
        acc = {g: {c: [0, 0] for c in cols} for g in ORDER[ds]}
        pred = {c: Counter() for c in cols}
        gold = Counter()
        for i, g in GOLD.items():
            if DS[i] != ds:
                continue
            f = OUT / VERS['v3'] / prov / i
            s = jread(f / 'summary.json')
            es = {r: jread(f / f'expert_{r}.json') for r in ROLES}
            a = {'direct': D.get(i, {}).get('prediction'), 'ppct': P.get(i, {}).get('prediction'),
                 'summary': s['answer'] if s else None, **{r: (es[r] or {}).get('answer') for r in ROLES}}
            gold[g] += 1
            for c in cols:
                acc[g][c][0] += a[c] == g
                acc[g][c][1] += 1
                pred[c][a[c]] += 1
        rows, tot = [], {c: [0, 0] for c in cols}
        for g in ORDER[ds]:
            rows.append([g, gold[g]] + [f'{acc[g][c][0]}/{acc[g][c][1]} ({100 * acc[g][c][0] / max(1, acc[g][c][1]):.0f}%)' for c in cols])
            for c in cols:
                tot[c][0] += acc[g][c][0]
                tot[c][1] += acc[g][c][1]
        rows.append(['**合计**', sum(gold.values())] + [f'**{tot[c][0]}/{tot[c][1]}**' for c in cols])
        text += f'\n#### {prov.upper()} · {ds}（按真实标签的召回）\n\n' + table(head, rows) + '\n'
        prow = [[g, gold[g]] + [pred[c][g] for c in cols] for g in ORDER[ds]]
        text += f'\n{prov.upper()} · {ds}：每个标签被**预测**的次数（对比“真实”列看是否过度预测）\n\n' + table(['标签', '真实'] + head[2:], prow) + '\n'
    return text


def sec_unanimous():
    rows = []
    samples = defaultdict(set)
    for v in VERS:
        for p in PROVS:
            n = un = keep = ov = ovbad = wrong = uw = 0
            for i in GOLD:
                r = expert_answers(v, p, i)
                if not r:
                    continue
                a, s = r
                n += 1
                wrong += s != GOLD[i]
                if len(set(a)) == 1:
                    un += 1
                    if s == a[0]:
                        keep += 1
                    else:
                        ov += 1
                        ovbad += s != GOLD[i]
                    if s != GOLD[i] and a[0] != GOLD[i]:
                        uw += 1
                        samples[(v, p)].add(i)
            rows.append([v, p, n, un, keep, ov, wrong, uw, pct(uw, wrong)])
    text = table(['版本', '模型', '有效样本', '三专家一致', '一致且汇总采纳', '**一致但汇总推翻**', '汇总答错总数', '专家一致且错（汇总跟着错）', '占汇总答错'], rows)
    both = sorted(samples[('v3', 'gpt')] & samples[('v3', 'gemini')])
    text += f"\n\nv3 中 GPT 与 Gemini 都“专家一致地错”的样本（{len(both)} 条）：{', '.join(both)}\n"
    return text


def sec_v3_gpt_summary():
    rows = []
    for p in ['gpt', 'gemini']:
        n = unan = unan_ok = agree = agree_ok = over = over_ok = bad = split = lost = 0
        for i in GOLD:
            r = expert_answers('v3', p, i)
            if not r:
                continue
            a, s = r
            n += 1
            bad += s != GOLD[i]
            split += len(set(a)) > 1
            lost += s != GOLD[i] and GOLD[i] in a
            if len(set(a)) == 1:
                unan += 1
                unan_ok += a[0] == GOLD[i]
            c = Counter(a).most_common(1)[0]
            if c[1] >= 2:
                if s == c[0]:
                    agree += 1
                    agree_ok += s == GOLD[i]
                else:
                    over += 1
                    over_ok += s == GOLD[i]
        rows.append([p, n, f'{unan}（其中答对 {unan_ok}）', split, f'{agree}（答对 {agree_ok}）', f'{over}（答对 {over_ok}）', bad, lost, bad - lost])
    return table(['模型', '样本', '三专家完全一致', '专家意见分歧', '汇总采纳多数（≥2 位一致）', '汇总推翻多数', '汇总答错', '其中“有专家答对但汇总错”', '其中“没有专家答对”'], rows)


def main():
    org_t, graph_t = sec_org()
    doc = f'''# 分析统计汇总（2026-11-02）

本文件由 `scripts/build_analysis_stats.py` 从本机保存的 `outputs/` 与 `data/manifests/validation.jsonl` 生成，**不调用模型**；重新运行脚本即可复现全部数字。真实标签只用于评估统计，不进入任何模型请求。

## 0. 读数前必读

- **开发集**：MER2024 40 条 + MELD 40 条，共 80 条，是按既有模型表现从官方测试集筛出、并已多次用于 v2/v3 开发的子集，**不是独立测试集**，下面的数字不能作为泛化证据。
- **样本很小**：按标签拆分后每格只有 5 到 7 条，一条样本 = 14 到 20 个百分点，只能看趋势。
- **口径**：Omni 的 v1/v2/v3 并未完整（分母为有效样本数），不能与 80 条的结果直接比较。原始 PPCT 中每个模型使用**自己生成的**图谱；v1/v2/v3 使用**固定的 Gemini 图谱**，二者不是同一条件。
- **原始 PPCT 没有专家角色**；图谱/音频字幕/图像三个专家只存在于 v1/v2/v3。
- **更正记录**：对话中早期曾报“GPT 77/80、Gemini 5/80 组织文本弃权”，是关键词过宽造成的误匹配（Gemini 的“难以置信”等被算入），以本文第 3 节的严格口径为准。早期还把“三位专家都答错（含答案各不相同）20 条”与“三位专家给出同一个错误答案 15 条”混用，以第 6 节为准。
- 关键词统计（弃权句、情绪词、“平缓”类词）是启发式匹配，属人工设计的规则，会有漏判，表中“下限”即此意。

## 1. Direct → 原始 PPCT 逐样本配对

{sec_paired()}

读法：净变化 = “Direct 错→PPCT 对” − “Direct 对→PPCT 错”。McNemar 精确检验只看这两个不一致格；p 越小越不像随机波动。

## 2. neutral 被预测的次数

{sec_neutral()}

## 3. 组织文本末句与图谱写法

“末句”取组织文本中“这些表现可能反映……”起的最后一句。弃权 = 末句匹配“无法明确/仅凭……无法/材料不足”等短语。

{org_t}

图谱写法（来自原始 PPCT 各模型自己生成的图谱）：

{graph_t}

## 4. v3 各角色准确率

{sec_roles('v3')}

## 5. v3 按真实标签的准确率

“Direct / 原始 PPCT”列为同模型的参照。
{sec_labels('gpt')}
{sec_labels('gemini')}

## 6. 三个专家一致时汇总器的表现

“一致但汇总推翻”表示三位专家给出同一答案、汇总器却给出不同答案；“专家一致且错”表示三位专家同一个错误答案且汇总器最终也错。

{sec_unanimous()}

v3 汇总器与专家的关系：

{sec_v3_gpt_summary()}

## 7. 复现

```
python scripts/build_analysis_stats.py
python scripts/build_v3_stage_view.py gpt   # 单样本链路页面 docs/v3-gpt-stages.html
```
'''
    out = ROOT / 'metrics' / 'analysis_stats_20261102.md'
    out.write_text(doc, encoding='utf8')
    print(out, len(doc), 'chars')


if __name__ == '__main__':
    main()
