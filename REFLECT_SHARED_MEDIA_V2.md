# 一次开发集反思与共享媒体专家协议 v2

2026-11-01，Asia/Shanghai。用户明确要求从已有正确/错误样本做一次简单reflect，并修改三路专家和summary输入及rubric。

## 反思依据与边界

从v1已完成的GPT、Gemini结果，各选MER2024/MELD一个正确和一个错误结果，共8个模型—样本结果、6段唯一视频。优先选择三路标签分歧较大的结果，其次优先旧PPCT正确的结果，再按sample_id排序。选择有意聚焦冲突，不代表全量错误分布。

检查了原始8帧合成图（共64格，含重复视频）、字幕、图谱、组织文本、三路专家和summary。没有独立听审原音轨；关于音频的发现属于对原响应及来源处理的诊断，不是听觉事实的人工认证。分类对错以已有标签计算，不等于每句解释都正确。

完整快照：`metrics/reflect_v2_cases.json`；可视对照：`metrics/reflect_v2_frames.jpg`。以下标签和样本ID仅用于离线记录，不进入新版推理请求。

| Provider | 样本 | 标签→v1预测 | 发现与保留的经验 |
|---|---|---|---|
| GPT | MER2024/sample_00004468 | surprise→surprise | 图谱与时间变化帮助区分追问中的惊讶与视觉紧张；单看皱眉不足以判愤怒。 |
| GPT | MER2024/samplenew_00034373 | sad→worried | 图谱专家给出含泪与哽咽的转述；summary将“GPT没有音轨”当作声音转述存在冲突。缺少直接模态不等于间接证据虚假，应明确来源与核验限制。 |
| GPT | MELD/dia237_utt3 | disgust→disgust | 字幕“keeping it down”支持反感；summary没有把“happy”字面词、其他专家的泛化状态当主要依据。少量明确语义可胜过更多弱线索。 |
| GPT | MELD/dia109_utt4 | surprise→anger | 视觉专家把抱臂、张口、手势解释为对抗，summary无法回看原媒体纠正。新视觉rubric要求定位特征、变化和替代解释，而非直接写情绪形容词。 |
| Gemini | MER2024/sample_00004468 | surprise→surprise | 语言/韵律解释与图谱事件可互补，视觉紧张并不必然推翻惊讶；保留明确冲突处理。未独立确认原音频描述。 |
| Gemini | MER2024/samplenew_00005588 | neutral→sad | summary根据视觉“泪光”将低平声音解释为压抑；暗光帧不足以在本次小图审核中确认该微细观察。需避免把不清楚的眼部反光写成确定泪水，也不能把克制自动等同于压抑悲伤。 |
| Gemini | MELD/dia109_utt4 | surprise→surprise | 选取更有区分力的语言/声音报告，没有按两个neutral投票。这是保留非投票汇总的正例。 |
| Gemini | MELD/dia119_utt5 | fear→joy | summary用“情景喜剧中的调侃”重新解释急促声音，偏向视觉专家的微笑。题材不能作为排除真实负面情绪的依据；需用目标的实际语义、表情与声音处理冲突。 |

这些例子支持修改核查流程，不能证明修改一定提高ACC。新版不包含上述样本、字幕特例、答案或某角色固定优先级。

## 输入与四条rubric

每个专家独立调用相同provider；GPT接8帧+已有字幕，Gemini/Omni另接真实音轨。共享信息不意味着共享其他专家结论。原音轨能力差异继续披露。

| 角色 | 额外输入 | 四条rubric概要 |
|---|---|---|
| 线索组织文本专家 graph | 固定Gemini图谱+本模型组织文本 | 当前目标事件链；原媒体核查图谱；同源去重与关系互补；间接来源和缺失模态区别 |
| 音频字幕专家 audio_subtitle | 无图谱、无组织文本 | 当前话语与语用；定位韵律及模态限制；语义/视觉交叉核查；替代解释与信息不足 |
| 视觉专家 image | 无图谱、无组织文本 | 目标定位与帧证据；动态组合及观察/解释区别；跨模态消歧；反证、弱表现与成见限制 |
| summary | 三路专家；无原图谱、无组织文本 | 原媒体核实关键来源；可信非重复证据覆盖而非计票；整合互补及处理冲突；反证与最终单标签取舍 |

组织文本生成步骤仍只用冻结图谱与目标信息，沿用v1提示词。专家主要领域通过rubric指定，但都可用原媒体交叉核查。没有新增debate轮次。没有加入情绪轮或开放词汇映射。

专家输出结构化1—4条证据：`id/source/anchor/observation/interpretation/polarity`，加推理、单标签与反证。`source`区分visual/audio/subtitle/graph。summary通过`[image:E1]`等引用专家实际证据；独立核实的新发现直接定位原媒体。不能靠扩写、重复引用或多个专家同意增加证据权重。最终程序仍输出推理和唯一`<answer>label</answer>`。

## 文件、运行和状态

- 提示词：`shared_media_expert_prompts_v2.py`。
- 新版运行/审计：`shared_media_experts_v2.py`，构建工具`build_shared_media_v2.py`。
- 输出目录：`outputs/gemini_graph_shared_media_v2/{provider}/{dataset}/{sample_id}/`。
- 图谱只读复用：`data/gemini_graph_three_experts_v1/manifest.json`，不重新生成。
- 汇总报告：`metrics/gemini_graph_shared_media_v2_comparison.md`、`_audit.json`。
- v1代码、提示词、输出和原六组评测全部保留。新版输出独立；缓存签名包含新版提示词、输入与媒体哈希，不复用旧预测。

```bash
.venv/bin/python shared_media_experts_v2.py --self-test
.venv/bin/python shared_media_experts_v2.py --init
.venv/bin/python shared_media_experts_v2.py --provider omni --smoke
.venv/bin/python shared_media_experts_v2.py --provider omni
.venv/bin/python shared_media_experts_v2.py --controller
.venv/bin/python shared_media_experts_v2.py --audit
```

本次只准备新版协议并运行离线检查，未启动新版API/Omni推理或全80评测，尚无v2 ACC。controller入口可执行三provider两条跨数据集smoke后各80条，成功样本与阶段缓存可续跑；Omni默认4workers，GPT/Gemini各2。不得与其他健康实验无控制地并发启动。

## 评测解释

本次明确用此前验证80里的样本进行人工reflect，因用户最新明确授权而覆盖项目旧的“验证集不得调参”限制。后续同80结果属于开发集迭代；不能声称未见验证集泛化，不能作为独立测试提升。图谱由Gemini生成也有教师图谱来源差异。需要另留未参与反思/选择的新样本评价泛化。真实标签只供离线评分，不进入生成请求。

## 2026-11-01T19:03:41+08:00 引用宽松策略（用户最新指令）

推理中缺少[E1]、括号形式不同、summary引用列表与正文不同、帧/节点定位写法不同不再阻塞或触发格式重试。未知引用保留原文并记警告，不替模型创造或补写引用。证据列表、非空推理、原始单标签、实际提供的模态与无gold检查仍保留。每阶段*_citation_diagnostics.json记录宽松检查；citation_policy.json是当前策略入口。逐样本审计“有效”不表示全部引用真实或语义已核验。原始已接受响应不改写；此前仅因引用失败且有同签名原响应的阶段允许离线恢复，恢复耗时未知以seconds=0并标志缺失，不算真实0秒推理。
