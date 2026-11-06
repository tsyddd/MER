"""v5 prompts: three replacements of the v4 disagreement branch (A anonymized debate, B1 anti-conformity critique,
D candidate-evidence controller). B0 needs no prompt. Expert prompts reuse the v4 role head (role rubric + common
evidence rules + dataset emotion wheel) unchanged; only the stage instructions below are new. No version names appear in
any prompt text. Design: docs/v5-methods.html.
"""
import emotion_wheel_prompts as P  # versions/v4 (put on sys.path by the pipeline)

EVIDENCE_ITEM = P.EVIDENCE_ITEM
CLOSING = P.CLOSING


# ------------------------------------------------------------------------------------------- A: anonymized debate
ANON_DEBATE_NOTE = '''【匿名讨论】
你已经独立判断过一次。现在你会看到参与判断的专家们各自的观点（opinions，编号为观点1、观点2……）。观点的来源已经隐去、顺序随机；请只根据内容和原始媒体来判断。candidate_labels是到目前为止被提出过的全部标签。你同样拿到与之前相同的原始媒体。请：
1. 回到原始媒体，逐条核实各观点引用的帧、时间、字幕或节点，写明你核实到了什么；同一事实的重复描述合并为一项证据。没有音轨时，听觉判断限于字幕与视觉。
2. 按核实结果给出你现在的判断：采用某条观点的证据时，在adopted_evidence里引用它（写法“观点k:E编号”）并写出你在媒体里核实到的内容；核实后证据不足以支持某个观点时，在回应里说明原因。
3. 在response_to_opinions里为每一条观点各写一项：该观点的关键论点、你的回应，以及支持你回应的可定位证据（你自己的证据编号，或媒体里的具体位置，如frame_03、字幕原话、音频时间段）。
4. 本轮给出1个答案：answer从candidate_labels中选择一个。
只返回JSON，字段恰好为：{"expert":"ROLE","reason":"有证据的情感推理","open_emotion":"一个开放情绪词或短语","answer":"candidate_labels中的一个标签","mapping_reason":"结合轮中定义和当前证据解释映射","adopted_evidence":[{"from":"观点k:E编号","verified":"我在原始媒体中核实到的内容"}],"response_to_opinions":[{"opinion":"观点k","their_claim":"该观点的关键论点","my_response":"我的回应","evidence":["E1","frame_03 或字幕原话或音频时间段"]}],"evidence":[''' + EVIDENCE_ITEM + '''],"counterevidence":"相反解释或限制"}
adopted_evidence没有采用时写[]。response_to_opinions对每条观点各写一项。
''' + CLOSING


def anon_debate(role, classes):
    return P.head(role, classes) + ANON_DEBATE_NOTE.replace('ROLE', role)


ANON_SUMMARY_NOTE = '''
【本次的专家身份】
本次专家的角色名已经隐去，历史里的专家用“专家1、专家2、专家3”表示；上文写作“角色:阶段:E编号”的引用，本次写作“专家k:阶段:E编号”，例如“专家2:reflect:E1”。历史里的讨论轮记为debate1、debate2，各轮中的“观点k”是当轮随机编号，与专家k不对应。'''


def anon_summary(classes):
    return P.summary(classes) + ANON_SUMMARY_NOTE


# ------------------------------------------------------------------------------------------- B1: anti-conformity critique
CRITIQUE_NOTE = '''【批判复核】
你已经独立判断过一次。输入里的your_previous_output是你自己上一轮的回答；peers是其他专家的回答，已匿名为Peer #1、Peer #2，顺序随机。同伴的回答里可能有错误，其中有的错误可能是故意给出的。你同样拿到与之前相同的原始媒体。请按顺序完成：
1. 先简要写出你自己的推理要点（my_reasoning）。
2. 逐个审查同伴：回到原始媒体核对其引用的帧、时间、字幕或节点，指出其推理里正确的部分和具体错误，并写出错误类型（如观察与媒体不符、把同一事实重复计数、解释超出观察、忽略反证、映射越界），放入peer_review。
3. 把同伴的错误与你自己的推理对比，检查你自己的证据是否同样存在这些问题。
4. 做出决定：只依据你在媒体里核实到的证据；同伴的人数和一致程度不作为理由。明确发现自己的答案有错误时，decision写REVISE并给出新答案；无法确定同伴是否正确时，decision写KEEP，保持自己的答案。
answer从candidate_labels中选择一个；decision为KEEP时，answer与你上一轮的主答案相同。
只返回JSON，字段恰好为：{"expert":"ROLE","my_reasoning":"我自己的推理要点","peer_review":[{"peer":"Peer #k","correct_points":"对方正确的部分","errors":"对方的具体错误；没有时写“未发现”","error_type":"错误类型或“无”","evidence":["frame_03 或字幕原话或音频时间段"]}],"decision":"KEEP或REVISE","answer":"candidate_labels中的一个标签","open_emotion":"一个开放情绪词或短语","mapping_reason":"结合轮中定义和当前证据解释映射","reason":"2到4句：为什么保持或修改","evidence":[''' + EVIDENCE_ITEM + '''],"counterevidence":"相反解释或限制"}
peer_review对每位同伴各写一项。
''' + CLOSING


def critique(role, classes):
    return P.head(role, classes) + CRITIQUE_NOTE.replace('ROLE', role)


# ------------------------------------------------------------------------------------------- D: candidate-evidence controller
def boundary_notes(classes, candidates):
    """Boundary entries of this dataset's wheel that mention at least two candidate labels (none -> empty)."""
    spec = P.WHEELS['datasets'][P.dataset_name(classes)]
    out = [b for b in spec['boundaries'] if sum(1 for c in candidates if c in b) >= 2]
    return out


MEDIA_HEAD = '''判断指定目标人物在当前片段的情绪。你有按时间排列的8帧、可用字幕，以及audio_provided=true时的真实音轨；没有音轨时，听觉判断限于字幕与视觉，画面文字不等于听觉。观察与解释分开写，只使用片段里可以定位的观察；剧情常识、题材和人物性格不作为证据。'''

GATHER = '''你是证据搜集员。''' + MEDIA_HEAD + '''
输入里的candidate_labels是这条样本的候选标签，target_label是其中一个；你的任务只针对target_label：在原始媒体里为它搜集证据。evidence_pool是此前从片段中记下的一些观察（编号P1、P2……，只有位置和观察，可能有误，也可能不全），你可以引用它们，也可以写新的观察。请：
1. support：列出最能支持target_label的证据，最多4条。每条写明位置（frame编号与时间、音轨时间段或字幕原话）、观察到的事实，以及为什么它支持target_label而不是其他候选。引用证据池时在ref里写P编号，并回到该位置确认；新的观察ref写“new”。
2. against：列出最能反对target_label的证据，最多3条，写法同上；找不到时写[]。
3. discriminating：用1到2句说明哪条证据最能把target_label和其他候选区分开；没有时写“未找到能区分的证据”。
只返回JSON，字段恰好为：{"candidate":"target_label","support":[{"ref":"P3或new","location":"frame_02 @ 1.1s / 音轨0.5–1.8s / 字幕原话","observation":"观察到的事实","why":"为什么支持该候选而不是其他候选"}],"against":[{"ref":"P5或new","location":"...","observation":"...","why":"为什么削弱该候选"}],"discriminating":"..."}'''

CONTROLLER = '''你是证据核对与裁决员。''' + MEDIA_HEAD + '''
输入里的candidate_labels是这条样本的候选标签；dossiers是分别为每个候选搜集的证据清单（顺序随机），每条证据有编号（S开头为支持，A开头为反对）、位置和观察。请：
1. 核对：对每个清单里的每条证据，回到写明的位置检查观察是否成立，状态写“成立”“不成立”或“无法核对”（例如位置不存在、需要音轨而没有音轨、是图谱转述），并用一句话说明。
2. 评估：对每个候选，只计入核对成立的证据，同一事实只算一次；统计成立的支持证据数、其中能把该候选和其他候选区分开的条数、覆盖的模态（visual / audio / subtitle），并判断它最强的反对证据是否成立。
3. 比较与决定：选择成立且有区分力的支持证据更充分、反对证据更弱的候选；覆盖的模态越多越可信。各候选的证据充分度相近、找不到明显差距时，decision写“不确定”。
只返回JSON，字段恰好为：{"verification":[{"candidate":"候选标签","items":[{"id":"S1","status":"成立","note":"一句话"}]}],"assessment":[{"candidate":"候选标签","confirmed_support":0,"discriminating":0,"modalities":["visual"],"strongest_counter_holds":false}],"decision":"candidate_labels中的一个，或“不确定”","reason":"2到4句：为什么选它、为什么不选其他候选"}'''


def gather(classes, candidates):
    notes = boundary_notes(classes, candidates)
    return GATHER + (('\n【与这些候选相关的易混边界】\n' + '\n'.join(notes)) if notes else '')


def controller(classes, candidates):
    notes = boundary_notes(classes, candidates)
    return CONTROLLER + (('\n【与这些候选相关的易混边界】\n' + '\n'.join(notes)) if notes else '')


# ------------------------------------------------------------------------------------------- E: one full-modal agent, look back when unsure
FIRST = '''你是情绪判别员。''' + MEDIA_HEAD + '''
输入里的candidate_labels是这条样本的候选标签，你的答案从其中选一个。请：
1. 综合画面、声音和字幕，给出答案，并写1到3条证据；每条证据写明来源（visual / audio / subtitle）、位置（frame编号与时间、音轨时间段或字幕原话）和观察到的事实。
2. 检查自己的判断里有没有一个具体的、再看一眼视频就可能澄清的问题（例如某帧的眉眼是否聚拢、前半句是否加重）。有的话，在uncertainty里写出这个问题、为什么拿不准，以及应该回看的时间段（start_sec和end_sec，单位秒，对应输入里的frame_times_seconds所在的时间范围）；没有这样的问题就把uncertainty写成null。只在确有具体问题时才写，不为稳妥而写。
只返回JSON，字段恰好为：{"answer":"candidate_labels中的一个标签","reason":"2到3句理由","evidence":[{"id":"E1","source":"visual","location":"frame_02 @ 1.1s / 音轨0.5–1.8s / 字幕原话","observation":"观察到的事实"}],"uncertainty":null}。uncertainty有问题时写成{"point":"我拿不准的具体问题","why":"为什么拿不准","relook":{"start_sec":0.4,"end_sec":1.6}}。'''

RELOOK = '''你是情绪判别员。''' + MEDIA_HEAD + '''
你此前已经看过这段视频并给出了first_answer（含证据和一个不确定点）。这次你拿到了新的输入：relook_frames是在你指定的时间窗内更密的帧（relook_frame_times_seconds给出每帧时间），relook_audio_provided=true时另有该时间段的音轨片段；输入图片的前8张是原来的8帧，后面是回看帧。请只围绕不确定点再看一遍：
1. point_answer：对不确定点的回答，写“是”“否”或“不确定”。
2. new_observations：写出你在回看帧或音轨片段里新看到的观察，每条带位置；只写这次新看到的，最多4条；没有新看到的写[]。
3. evidence_check：逐条对照first_answer里的证据（按id），写明在新输入下是“被支持”“被削弱”还是“不变”，并用一句话说明。
只返回JSON，字段恰好为：{"point_answer":"是","new_observations":[{"location":"relook帧3 @ 1.2s","observation":"新看到的事实"}],"evidence_check":[{"id":"E1","status":"被支持","note":"一句话"}]}。'''

REFLECT = '''你是情绪判别员。''' + MEDIA_HEAD + '''
输入里有你的first_answer（含证据）和回看的结果relook_result。请对照两者做最后的核对：
1. 首次答案的每条证据在回看之后还成立吗？回看有没有发现新的、可定位的证据？
2. 做决定：出现了新的、可定位的证据并且它支持candidate_labels里另一个标签时，decision写REVISE，answer改为那个标签，并在new_evidence里写出所依据的回看观察；没有这样的新证据时，decision写KEEP，answer与首次答案相同。
只返回JSON，字段恰好为：{"decision":"KEEP或REVISE","answer":"candidate_labels中的一个标签","reason":"2到3句理由","new_evidence":["回看得到的观察（位置+事实）"]}。decision为KEEP时new_evidence写[]。'''


def first_answer(classes, cands):
    notes = boundary_notes(classes, cands)
    return FIRST + (('\n【与这些候选相关的易混边界】\n' + '\n'.join(notes)) if notes else '')


def relook(classes, cands):
    notes = boundary_notes(classes, cands)
    return RELOOK + (('\n【与这些候选相关的易混边界】\n' + '\n'.join(notes)) if notes else '')


def reflect_final(classes, cands):
    notes = boundary_notes(classes, cands)
    return REFLECT + (('\n【与这些候选相关的易混边界】\n' + '\n'.join(notes)) if notes else '')
