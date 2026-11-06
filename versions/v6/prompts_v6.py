"""Prompts of the R2-MAD pipeline (v6). Built from the v4 prompt text with string replacements that are asserted, so nothing drifts silently.

Flow without reflection: Round 0 experts -> (summary) -> debate 1 -> (summary) -> debate 2 -> summarizer. The debate and summarizer prompts
are the v4 prompts with the reflection stage removed. With memory, the debate prompt gets one extra block that explains retrieved
examples and peer reliability marks. No version names appear in any prompt text.
"""
import emotion_wheel_prompts as P4


def _swap(text, pairs):
    for old, new in pairs:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


DEBATE_NOTE = _swap(P4.DEBATE_NOTE, [
    ('你已在反思后给出判断。现在你拿到另外两位专家反思后的完整输出（答案、备选、证据、反证）和candidate_labels（三位到目前为止提出过的全部标签，含备选）',
     '你已给出自己的判断（your_previous_output）。现在你拿到另外两位专家上一轮的完整输出（答案、备选、证据、反证）和candidate_labels（三位在第0轮提出过的全部标签，含备选）'),
])

MEMORY_NOTE = '''【经验案例与同伴可靠度】
输入里可能有retrieved_examples：它们是其他样本的历史案例。每个案例含：该样本的综合描述与任务（example_question）、该样本的标准标签（example_solution）、与你同一角色的专家当时的回答（example_agent_response）、他当时是否改变了立场、这个回答是否正确。请把它们当作类比参考：比较案例描述与当前样本的异同，用来校准你对当前样本的先验，不要直接照搬案例的标签；对当前样本的判断以你亲自在原始媒体里核实到的证据为准。案例回答里的帧号、证据编号属于那个案例，不适用于当前样本。
other_experts里某位专家可能带reliability字段：high表示这位专家在相似案例里历史上更可靠，low表示历史上更不可靠；没有该字段表示没有明确倾向。它只影响你对其观点的权重，不能替代你核实证据。
'''


def debate(role, classes, memory=False):
    return P4.head(role, classes) + DEBATE_NOTE.replace('ROLE', role) + (MEMORY_NOTE if memory else '')


def summarizer(classes):
    """Final summarizer = the v4 summary prompt with the reflection stage removed from its text."""
    text = P4.summary(classes)
    for old, new in [('Round 0（可能含备选）、反思、每轮辩论的答案', 'Round 0（可能含备选）、每轮辩论的答案'),
                     ('历史里每条证据带阶段标记（r0、reflect、debate1、debate2）', '历史里每条证据带阶段标记（r0、debate1、debate2）'),
                     ('例如“image:reflect:E1”', '例如“image:r0:E1”'),
                     ('[graph:reflect:E1]、[image:debate1:E2]', '[graph:r0:E1]、[image:debate1:E2]'),
                     ('"graph:reflect:E1"', '"graph:debate1:E1"')]:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    assert '反思' not in text and 'reflect' not in text
    return text


CAPTION = '''你是视频内容描述员。你会收到一个视频片段的8帧画面、可用的音轨（如果提供）和字幕。请用一段连贯的中文（约200到400字）综合描述这个片段：
画面：人物的外观、动作、表情、手势、场景；
声音：语气、音量、语速、停顿、背景声；没有提供音轨时写“未提供音轨”；
台词：说了什么、对谁说、处在什么语境。
只描述你实际看到和听到的事实与表现，不要判断说话者属于哪一类情绪，也不要使用情绪类别的名称。
只返回JSON：{"caption":"你的综合描述"}'''

STATE = '''你是观察多位专家辩论的分析员。请为刚刚结束的这一轮写一段简短的“辩论状态摘要”，概括这一轮的关键动态。
输入：question（样本的描述与任务）、previous_summary（上一轮摘要，可能为"None"）、agents（每位专家本轮的答案与理由；第二轮起还有上一轮答案和stance_changed）、consensus_ratio（本轮最多专家共同持有的同一个答案占三位专家的比例）。
分析：
1. 立场分布：现在有几种不同立场、各有几位专家；若有专家改变了立场，是什么论据推动的；若没有人改变，是什么在维持当前的一致或分歧。
2. 辩论走向：是在收敛、发散还是停滞；区分“被实质论据说服”的改变与“放弃少数意见、没有被反驳”的改变；指出最有影响的论据或尚未解决的争议点。
输出格式，恰好两句，放进JSON的summary字段：
"Dynamic: [一句话：立场分布、共识模式、与上一轮相比的立场变化]\\nInsight: [一句话：最有影响的论据、未解决的争议或推动走向的社会动态]"
每一句必须：客观（只描述发生了什么，不评判谁对）；抽象、聚焦策略（描述推理方式和辩论模式，不出现具体的标签名称、标签词或台词内容）；立场中立（用“多数/少数”或描述性的立场称呼，不用专家名）。
不要判断或猜测哪一种立场正确；若有上一轮摘要，不要重复其中已经说过的内容。
只返回JSON：{"summary":"Dynamic: ...\\nInsight: ..."}'''
