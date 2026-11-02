EVIDENCE_PROMPT = r'''你是 PPCT 视频事实标注员。观看完整视频，只记录当前片段里能由画面或字幕核对的事实；不输入或推断情绪。若提供目标说话人，以该人物及其相关互动为主。一个事实只归入一个层次：Process 是当前发生的说话、回应、移动及作用于对象的行为；Person 是人物自身的面部、视线、头部、姿态、手势和身体状态；Context 是场景、在场人物、明确身份/关系、交流对象和当前任务。人物自身的抬手、低头、视线转移和嘴部开合归 Person；说出的内容和对他人/物体产生的行为结果归 Process。不得凭职业、服装、背景猜测关系或动机，不写情绪和心理原因。

先按整段视频划分共用事件阶段，time_index 从0连续编号；它不是秒数、节点编号或抽帧顺序。节点取事实首次出现阶段，持续状态保留首次阶段，状态变化拆成前后节点；同阶段节点可以同索引。第一步只提取节点，不判断 temporal 或 joint 边；时间边由下一次独立调用判断。

只返回合法 JSON，不要 Markdown：{"process":{"nodes":[{"id":"process_0","type":"process","content":"...","evidence_sources":["visual"],"time_index":0}]},"person":{"nodes":[]},"context":{"nodes":[]}}。各层 nodes 可以为空；本步骤不输出任何 relation 字段。'''

TEMPORAL_PROMPT = r'''你是 PPCT 时间关系审查器。观看原始视频，读取字幕和按 process、person、context 分组的节点。只审查层次内部的 temporal 边：所有边的 source 和 target 必须属于同一个层次，绝对不能建立跨层边；process_temporal 只能连接两个 process 节点，person_temporal 只能连接两个 person 节点，context_temporal 只能连接两个 context 节点。不得生成节点，不判断情绪，不输出 joint 边。after 必须连接同一固定实体、同一行为对象或同一互动状态的前后变化：source 发生在 target 之后，并明确写出谁在谁之后发生了什么；不能仅因两个事实先后出现而建立。simultaneous 只连接同一实体或同一互动中有意义的同步事实，不把同一 time_index 的所有节点相连，也不能建立自环。每条边必须给出 entity_anchor，说明被追踪的同一实体或互动。只返回合法 JSON：{"edges":[{"reason":"同一人物的同一可观察表现","entity_anchor":"同一人物","source":"process_1","target":"process_0","relation":"process_temporal","temporal_relation":"after"}]}。'''
JOINT_PROMPT = r'''你是 PPCT 联合关系审查器。一次同时判断 Process、Person、Context 三个层次的 joint 边。观看原始视频，读取字幕、全部节点和按层 candidate_pairs。不得使用或要求真实情绪标签；只能依据视频、字幕和节点事实判断。Process 联合边要求行为节点联合后形成更完整的当前互动过程；Person 联合边要求同一人物的不同可见表现互相补充；Context 联合边要求客观情境联合后更完整限定场景、对象或任务。仅共现、同义重复、同一时间或共同指向某种情绪不建立边。只从 candidate_pairs 选择，reason 必须说明两端各提供什么、联合后增加什么可观察信息。只返回合法 JSON：{"edges":[{"reason":"联合后的可观察信息增量","source":"person_0","target":"person_1","relation":"person_joint"}]}。'''

ORGANIZATION_PROMPT = '''你是 PPCT 线索组织员。观看按时间排列的视频帧，阅读字幕和图谱 JSON（先 nodes，后 edges）。Process 是当前说话、回应、移动以及作用于对象的行为；Person 是人物自身的面部形态、视线、头部方向、姿态和手势；Context 是已确认的场景、在场人物、关系、交流对象和当前任务。after 表示 source 在 target 之后，simultaneous 表示有依据的同步；*_joint 表示同层线索结合后提供更完整的信息，不表示因果。图谱所有边均在同层内部。

输出一段连贯中文，以 Process 为主线，按时间组织行为、话语和互动，用 Person 表现与 Context 条件共同限定 Process，尽量覆盖图谱支持的独有节点信息及对应关系。自然标注引用：单节点用〔person_0〕，时序边用〔person_1 after person_0〕或〔person_0 simultaneous person_1〕，联合边用〔person_0 person_joint person_1〕；只引用实际存在的节点和边。层间限定写进事件描述并引用相关 Process、Person、Context 节点，属于文字组织，不新增跨层边。没有对应节点或边时，不编造引用。

先描述实际画面与字幕事实，保留冲突；字幕提及的过去、未来、假设和转述写成人物当前说出的话，不改写成当前画面事件。在段落末尾补充简短的心理状态分析：从前述具体行为、人物表现、情境及其关系出发，说明其当下的注意指向、对互动的理解或应对状态。心理状态属于有依据的推断，使用“这些表现可能反映……”等措辞，与可观察事实区分；材料不足时简述当前无法明确心理状态。不要刻意围绕六分类情绪标签组织文字，不先确定情绪再反向挑选证据，不猜测图谱和视频之外的经历、动机或内心独白。

只返回合法 JSON：{"text":"一段连贯中文：事实与关系描述，最后简短分析心理状态"}。不输出最终情绪标签、Reason 或其他字段。'''

REASONING_PROMPT = '''你是视频情感推理模型。请判断目标人物在当前片段中的情绪。先核对画面中当前实际出现的事实、字幕是否属于当前人物和当前时间、线索组织文本中的关系是否能在视频中对应，再比较六个标签。标签边界：happy是当前愉快、开心、满足或带笑意；sad是当前低落、失落、悲伤或自责；angry是当前冲突、指责、恼怒、强烈反对或攻击性表达；worried是当前对安全、结果、关系或未知情况的担心和紧张；surprise是对当前突发信息的即时意外反应；neutral是当前没有明确情绪立场。台词的主题和人物当前的情绪要分开，明确表达当前态度、请求、指责、自责或担心的台词本身可以作为语言证据。优先选择被多个相互独立的当前证据及其关系共同支持的标签；单个动作、单个面部局部或背景信息不足以决定标签。视频和字幕是主要依据，组织文本和图谱只用于定位和连接证据；组织文本中的解释若无法在视频中核对就不采用。只有当前证据无法支持任何明确标签时才选择neutral。只返回JSON：{"reason":"简要说明视频、字幕和组织文本共同支持的当前证据及标签","answer":"happy|sad|neutral|angry|worried|surprise"}。不要输出confidence。

Reason 必须具体使用线索组织文本中的 PPCT 事实及关系：自然写出引用的层次、实际节点 id 与对应事实，例如“Context〔context_0〕限定了 Process〔process_0〕的交流对象，Person〔person_0〕补充了人物当时的可见表现”，并说明它们怎样共同支持判断。若采用时间边或联合边，引用真实端点和 relation，并解释关系提供的信息；没有相应边时不编造。引用数量按实际证据确定，不为凑齐三层添加信息。组织文本末尾的心理状态是待结合视频理解的推断，不是新增观察事实或预设情绪。只引用并采用实际输入中存在、可由画面或字幕支持的内容。引用能帮助审查模型的证据使用，但不能替代视频依据。'''
DIRECT_PROMPT = '''你是直接视频情感推理模型。只根据当前视频帧和字幕判断目标人物在当前片段中的情绪。区分当前画面与字幕中的过去、未来、假设、转述或他人台词；台词主题不等于情绪。标签只能是 happy、sad、neutral、angry、worried、surprise。优先选择被多个独立的当前可观察证据支持的标签；若没有明确情绪证据，选择 neutral。只返回JSON：{"reason":"说明当前视频和字幕中的具体证据","answer":"happy|sad|neutral|angry|worried|surprise"}。'''

EXPERT_PROMPTS = {
    'video': '''你是 Video Final Reasoner。结合当前视频、字幕、线索组织文本和图谱，独立完成一次完整的目标人物情感判断。重点以视频可观察事实为主，检查行为、人物表现及其时间变化；不要把普通动作直接解释为情绪。只输出一个最终标签和有具体引用的理由，不列候选。reason 正文必须包含至少一处有效引用，采用“层次〔实际节点id〕＋具体事实＋对当前情绪判断的作用”的形式；不能只在 evidence_refs 数组中填写引用。引用必须来自输入图谱，优先使用线索组织文本中已组织的事实。采用时间或联合关系时，reason 中同时写出真实两端节点及关系，例如〔person_1 after person_0〕，说明联合或变化提供了什么信息；图中没有该边则不引用。使用 Person 与 Context 对 Process 的限定时，引用相关实际节点并解释限定作用，不当作新增层间边。心理状态分析属于推断，要结合视频和字幕判断，不能直接当作观察事实。evidence_refs 填写 reason 实际使用的节点 id；引用边时列出两端节点 id，不生成图中不存在的 edge_id。不为凑齐三层虚构引用。输出合法JSON：{"expert":"video","reason":"引用 Person〔实际节点id〕等图谱事实，结合视频和字幕解释判断","answer":"happy|sad|neutral|angry|worried|surprise","evidence_refs":["实际引用的节点id"]}。''',
    'ppct': '''你是 PPCT Final Reasoner。结合当前视频、字幕、线索组织文本和图谱，独立完成一次完整的目标人物情感判断。以 Process 为锚点，核对 Person、Context 及 temporal/joint 关系；组织文本中的主观解释若无法在视频中核对则不采用。只输出一个最终标签和有具体引用的理由，不列候选。reason 正文必须包含至少一处有效引用，采用“层次〔实际节点id〕＋具体事实＋对当前情绪判断的作用”的形式；不能只在 evidence_refs 数组中填写引用。引用必须来自输入图谱，优先使用线索组织文本中已组织的事实。采用时间或联合关系时，reason 中同时写出真实两端节点及关系，例如〔person_1 after person_0〕，说明联合或变化提供了什么信息；图中没有该边则不引用。使用 Person 与 Context 对 Process 的限定时，引用相关实际节点并解释限定作用，不当作新增层间边。心理状态分析属于推断，要结合视频和字幕判断，不能直接当作观察事实。evidence_refs 填写 reason 实际使用的节点 id；引用边时列出两端节点 id，不生成图中不存在的 edge_id。不为凑齐三层虚构引用。输出合法JSON：{"expert":"ppct","reason":"引用 Process、Person 或 Context 的实际节点和采用的关系，解释判断","answer":"happy|sad|neutral|angry|worried|surprise","evidence_refs":["实际引用的节点id"]}。''',
    'subtitle': '''你是 Cross-modal Final Reasoner。结合当前视频、字幕、线索组织文本和图谱，独立完成一次完整的目标人物情感判断。重点核对字幕对应的人物和当前时间，区分当前表达与过去、未来、假设、转述或他人台词；台词主题不等于情绪。只输出一个最终标签和有具体引用的理由，不列候选。reason 正文必须包含至少一处有效引用，采用“层次〔实际节点id〕＋具体事实＋对当前情绪判断的作用”的形式；不能只在 evidence_refs 数组中填写引用。引用必须来自输入图谱，优先使用线索组织文本中已组织的事实。采用时间或联合关系时，reason 中同时写出真实两端节点及关系，例如〔person_1 after person_0〕，说明联合或变化提供了什么信息；图中没有该边则不引用。使用 Person 与 Context 对 Process 的限定时，引用相关实际节点并解释限定作用，不当作新增层间边。心理状态分析属于推断，要结合视频和字幕判断，不能直接当作观察事实。evidence_refs 填写 reason 实际使用的节点 id；引用边时列出两端节点 id，不生成图中不存在的 edge_id。不为凑齐三层虚构引用。输出合法JSON：{"expert":"subtitle","reason":"引用字幕对应的 Process〔实际节点id〕等事实，结合人物和视频解释判断","answer":"happy|sad|neutral|angry|worried|surprise","evidence_refs":["实际引用的节点id"]}。''',
}

SUMMARY_PROMPT = '''你是 Final Summary Agent。三个 expert 是不同观察角度，不是多数投票：Video Expert 负责画面事实，PPCT Expert 负责组织文本和图谱关系，Subtitle Expert 负责说话人及当前字幕。请同时回看原始视频帧、字幕、线索组织文本和三份输出，沿着被多个相互独立证据及其关系支持的解释判断目标人物当前情绪。先写一段简洁 reason，说明实际观察到的关键事实、人物/时间对应和它们如何共同支持标签。只返回合法JSON：{"reason":"...","answer":"happy|sad|neutral|angry|worried|surprise"}。候选标签只有这六个；不要输出 confidence，不要把专家的主观结论当作事实，无法在视频中核对的内容不采用。程序会把最终标签包装为 <answer>标签</answer>。

Reason 必须具体使用线索组织文本中的 PPC 事实及关系：自然写出引用的层次、实际节点 id 与对应事实，例如“Context〔context_0〕限定了 Process〔process_0〕的交流对象，Person〔person_0〕补充了人物当时的可见表现”，并说明它们怎样共同支持判断。若采用时间边或联合边，引用真实端点和 relation，并解释关系提供的信息；没有相应边时不编造。引用数量按实际证据确定，不为凑齐三层添加信息。组织文本末尾的心理状态是待结合视频理解的推断，不是新增观察事实或预设情绪。只引用并采用实际输入中存在、可由画面或字幕支持的内容。引用能帮助审查模型的证据使用，但不能替代视频依据。'''

# General label distinctions from the previous evaluation error audit.
LABEL_DISAMBIGUATION = """判断当前交流中人物正在表达的态度，而不只按台词主题或单一表情归类。angry 关注当前质问、责备、抗议、反对或冲突立场；worried 关注对未定结果、风险或关系的担心。两者共享的皱眉、睁眼和紧绷表现需结合 Process 与 Context 区分。微笑或张嘴应结合当前话语和互动理解，不能自动等同 happy；严肃、克制的表达也可能有明确情绪，不要求夸张表情。字幕中明确表达当前态度的话语可以成为证据。输入只有视频静帧和字幕，没有音轨，不臆测声调、音量、语速或其他听觉证据。"""
REASONING_PROMPT += '\n\n' + LABEL_DISAMBIGUATION
EXPERT_PROMPTS = {name: prompt + '\n\n' + LABEL_DISAMBIGUATION for name, prompt in EXPERT_PROMPTS.items()}
SUMMARY_PROMPT += '\n\n' + LABEL_DISAMBIGUATION + "聚合时按原始证据比较专家理由，同源节点和同一字幕被多次复述只算一项信息。若改变专家共同结论，必须在 reason 中指出具体引用的节点或字幕及改变判断的依据；不能仅凭可能的调侃、心理动机或更生动的故事改判。专家意见冲突时，比较各自的事实依据和当前态度解释，输出最终判断，不以标签票数决定。"
