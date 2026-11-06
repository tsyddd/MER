"""Draft prompts (2026-11-03, revised after user review round 1). NOT run.

Flow: Round 0 experts (1-2 answers when truly unsure) -> reflection (always) -> route on common label ->
debate (single answer within candidate union) -> summary. Unchanged from the previous version: ORGANIZATION, the four
rubrics per role (prompts_base.EXPERTS), the dataset emotion wheels and boundary rules. No version names appear in
any prompt text. Routing, output validation and stage order live in the (not yet written) pipeline, not here.
Dataset-adapted project wheel; not an official wheel.
"""
import json
from pathlib import Path
import prompts_base as base

CONFIG_PATH = Path(__file__).with_name('emotion_wheels.json')
WHEELS = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
ORGANIZATION = base.ORGANIZATION  # unchanged


def dataset_name(classes):
    matches = [name for name, spec in WHEELS['datasets'].items() if set(spec['labels']) == set(classes)]
    assert len(matches) == 1, 'Dataset must match original MER6 or MELD7 label space'
    return matches[0]


def wheel_text(classes):  # unchanged
    name = dataset_name(classes); spec = WHEELS['datasets'][name]
    lines = ['【' + name + '项目适配情绪轮】',
             '这是项目自定义层级参考，不是数据集或AffectGPT官方情绪轮。Level1严格保留本数据集标签。']
    for root, family in spec['families'].items():
        lines.append(root + '（' + family['name'] + '）：' + family['definition'] + ' 开放词示例：' + '；'.join(family['examples']))
    lines += ['【共同映射原则】'] + WHEELS['shared_rules'] + ['【易混边界与类别缺失】'] + spec['boundaries']
    return '\n'.join(lines)


# ----------------------------------------------------------------------------------------------- shared head
def head(role, classes):
    """Role rubric + common evidence rules (unchanged text) + dataset emotion wheel. Each stage appends its own
    output requirements."""
    text = base.EXPERTS[role].split('只返回JSON，字段恰好为：', 1)[0]
    old = '只从allowed_labels选一个原始标签，不改标签空间，不使用情绪轮转换。'
    assert text.count(old) == 1
    text = text.replace(old, '先识别一个开放情绪，再按本数据集情绪轮映射成allowed_labels中的原始标签，标签空间保持不变；答案的个数见本阶段的输出要求。')
    return text + '\n' + wheel_text(classes) + '\n'


EVIDENCE_ITEM = '{"id":"E1","source":"visual","anchor":"对应帧/音频/字幕/节点位置","observation":"观察事实","interpretation":"证据含义","polarity":"support"}'
CLOSING = '证据编号和定位写法是辅助格式；请给出非空的具体证据，并只使用实际提供的模态。你只需返回JSON，程序统一包装<answer>。'
BACKUP_RULE = ('通常给出一个答案。当两个标签在你核对过的证据下确实难以取舍（同一表情或同一句话在两个标签下都说得通，又找不到能区分它们的证据）时，'
               '可以再给一个备选：alt_answer填另一个allowed_labels标签，alt_open_emotion填它的开放情绪，uncertainty_reason写明为什么拿不准、需要什么证据才能区分；'
               'answer填你认为更可能的那个。没有这种两难时，三个备选字段填null。')
FIELDS_R0 = ('{"expert":"ROLE","reason":"有证据的情感推理","open_emotion":"一个开放情绪词或短语","answer":"一个原始Level1标签","mapping_reason":"结合轮中定义和当前证据解释映射",'
             '"alt_answer":null,"alt_open_emotion":null,"uncertainty_reason":null,"evidence":[' + EVIDENCE_ITEM + '],"counterevidence":"相反解释或限制"}')


# ----------------------------------------------------------------------------------------------- Round 0 experts
ROUND0_SCHEMA = '''【输出要求】
先依据本领域证据形成一个开放词汇情绪词（中文或英文的一个词/短语，尽量准确具体，不限于示例），再映射到上方情绪轮的一个Level1标签，这是你的主答案。
open_emotion是主答案的开放情绪；answer是映射后的数据集标签；mapping_reason说明该开放情绪为什么在当前语境下映射到answer，近似投影时写出其限制。三路专家各自独立判断，映射时保持证据原样。
''' + BACKUP_RULE + '''
只返回JSON，字段恰好为：''' + FIELDS_R0 + '\n' + CLOSING


def expert(role, classes):
    return head(role, classes) + ROUND0_SCHEMA.replace('ROLE', role)


# ----------------------------------------------------------------------------------------------- reflection
REFLECT_NOTE = '''【反思】
输入里的your_previous_output是你上一轮独立给出的完整输出（答案、备选、证据、反证）；你同样拿到与上一轮相同的原始媒体（8帧、可用音轨、字幕）。请回看媒体做一次自查：
1. 逐条对照你上一轮的每条证据，回到引用的帧、时间、字幕原话或节点确认它是否成立；成立的保留，写得过头或确认不了的修正，或把polarity改为uncertain。没有音轨时，听觉判断限于字幕与视觉。
2. 找出你上一轮最值得重视的反证或最强替代解释，说明它与当前答案相比强在哪里、弱在哪里，并对照情绪轮的定义和易混边界，检查开放情绪映射成标签是否恰当。
3. 决定主答案：出现新的、可定位的证据时，改为证据更充分的标签；证据没有变化时，保持原答案。一切以媒体为准。
4. 仍按“先开放情绪，再映射标签”作答，答案个数规则同上一轮。
''' + BACKUP_RULE + '''
只返回JSON，字段恰好为：''' + FIELDS_R0.replace('"counterevidence":"相反解释或限制"}', '"counterevidence":"相反解释或限制","changed":false,"reflection":"2到4句：核实了什么、发现了什么、为什么改或保持"}') + '''
changed表示主答案相对上一轮是否改变。
''' + CLOSING


def reflection(role, classes):
    return head(role, classes) + REFLECT_NOTE.replace('ROLE', role)


# ----------------------------------------------------------------------------------------------- debate
DEBATE_NOTE = '''【辩论】
你已在反思后给出判断。现在你拿到另外两位专家反思后的完整输出（答案、备选、证据、反证）和candidate_labels（三位到目前为止提出过的全部标签，含备选）；你同样拿到与上一轮相同的原始媒体。请：
1. 回到原始媒体，逐条核实对方引用的帧、时间、字幕或节点，写明你核实到了什么；同一事实的重复描述合并为一项证据。没有音轨时，听觉判断限于字幕与视觉。
2. 想改变自己的答案时，引用对方的具体证据（写法“角色:E编号”）并写出你在媒体里核实到的内容，放入adopted_evidence；核实后证据不足以改变结论时，保持原答案并说明原因。
3. 想让对方改变观点时，在response_to_others里为每一位专家写出：对方的关键论点、你的回应，以及支持你回应的证据（你自己的证据编号，或媒体里的具体位置，如frame_03、字幕原话、音频时间段）。每条回应至少带一条可定位的证据。
4. 本轮给出1个最终答案：answer从candidate_labels中选择一个。
只返回JSON，字段恰好为：{"expert":"ROLE","reason":"有证据的情感推理","open_emotion":"一个开放情绪词或短语","answer":"candidate_labels中的一个标签","mapping_reason":"结合轮中定义和当前证据解释映射","changed":false,"adopted_evidence":[{"from":"另一位专家的证据，如image:E2","verified":"我在原始媒体中核实到的内容"}],"response_to_others":[{"expert":"另一位专家角色名","their_claim":"对方的关键论点","my_response":"我的回应","evidence":["E1","frame_03 或字幕原话或音频时间段"]}],"evidence":[''' + EVIDENCE_ITEM + '''],"counterevidence":"相反解释或限制"}
changed表示answer相对你上一轮的主答案是否改变；changed为true时adopted_evidence至少一项，为false时写[]。response_to_others对另两位专家各写一项。
''' + CLOSING


def debate(role, classes):
    return head(role, classes) + DEBATE_NOTE.replace('ROLE', role)


# ----------------------------------------------------------------------------------------------- summary
SUMMARY_TAIL = '''【汇总输入与引用】
你收到原始媒体与字幕，以及三位专家的完整历史：Round 0（可能含备选）、反思、每轮辩论的答案、adopted_evidence与response_to_others；三位最后的单答案不一致。请先回看媒体独立核验，再综合历史：某位专家在辩论中改变答案时，查看其adopted_evidence所引用的证据是否成立；同一事实的重复描述合并为一项；自己核验到的新证据标为summary自己核验。
历史里每条证据带阶段标记（r0、reflect、debate1、debate2）。reason与evidence_refs都写作“角色:阶段:E编号”，例如“image:reflect:E1”；evidence_refs汇集你的理由实际引用的、来自三位专家任一阶段的全部证据，无重复。
只返回JSON：{"reason":"基于原媒体和专家证据的最终推理","answer":"一个本数据集Level1标签","evidence_refs":["graph:reflect:E1","audio_subtitle:r0:E2","image:debate1:E1"]}。程序只包装一次<answer>label</answer>。'''


def summary(classes):
    text = base.SUMMARY
    for old, new in [
        ('不使用情绪轮映射，', '参考本数据集适配轮核对语义，'),
        ('衡量有区分力且可信的非重复证据覆盖量，而非投票、篇幅或引用条数；', '衡量有区分力且可信的非重复证据覆盖量；'),
        ('引用专家证据格式[graph:E1]、[audio_subtitle:E1]、[image:E1]；', '引用专家证据格式[角色:阶段:E编号]，如[graph:reflect:E1]、[image:debate1:E2]；'),
    ]:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    text = text[:text.index('只返回JSON：')].rstrip('\n')
    return (text + '\n' + wheel_text(classes) + '\n'
            + '专家的open_emotion是情绪解释，answer是其映射意见；请结合mapping_reason与原始证据判断。开放情绪相同而映射不同时，核对语义边界；映射相同而证据同源时，合并为一项证据。summary只给一个最终answer及其reason。\n'
            + SUMMARY_TAIL)


def validate_open(value):  # unchanged
    phrase = value.get('open_emotion')
    assert isinstance(phrase, str) and phrase.strip() and len(phrase.strip()) <= 80, 'One nonempty open emotion required'
