# v3：数据集适配情绪轮＋开放情绪映射

独立版本目录：`versions/v3/`。2026-11-01用户明确要求新增版本，不覆盖v1/v2。v3文件以`source_manifest.json`记录哈希；创建器拒绝覆盖内容不同的既有v3文件。主项目`engine.py`作为公共客户端/媒体基础设施复用，不修改它。

## 情绪轮

配置`emotion_wheels.json`；示意图`MER2024_emotion_wheel.svg`、`MELD_emotion_wheel.svg`。

- MER2024 Level1：`happy / angry / sad / worried / surprise / neutral`。
- MELD Level1：`joy / anger / sadness / fear / disgust / surprise / neutral`。
- 内圈任务标签、外圈开放词示例，中性放在中心展示。几何位置不意味着心理距离、对立关系或混合比例。
- 此配置是项目自定义语义层级，参考AffectGPT分层思路，不是官方轮，也不是官方测评映射。开放词不局限示例；映射依赖当前证据与语义，不做无条件词表替换。
- MER没有独立fear/disgust，需要说明近似投影的限制；MELD的担忧/焦虑不是自动fear。neutral不能代替“未知”或“词表未收录”。

## 流程与输出

沿用v2固定Gemini图谱、模型组织文本、三路独立专家、summary。三路各自接全部可用原始8帧/字幕/音轨；只有graph专家额外接图谱和组织文本。summary接原媒体及三路输出，不接原图谱/组织文本。GPT不接原音轨，Gemini/Omni接真实音轨。没有新增debate轮次。

每个专家与summary的系统提示词都嵌入**当前数据集**的完整情绪轮定义、边界规则，保留每角色4条rubric与宽松引用策略。生成组织文本的步骤仍不做分类，不注入轮。

专家在同一次响应中，先识别一个开放情绪，再映射一个原始标签：

```json
{
  "expert": "image",
  "reason": "依据实际媒体的情感推理",
  "open_emotion": "忐忑",
  "answer": "worried",
  "mapping_reason": "对可能负面结果的预期和不安，属于本任务担忧家族",
  "evidence": [{"id":"E1","source":"visual","anchor":"frame_02","observation":"具体可见事实","interpretation":"该事实的意义","polarity":"support"}],
  "counterevidence": "相反解释或当前限制"
}
```

该片段仅为schema示意，未指定样本，也不证明视觉事实。`open_emotion`是一个词或短语，不允许数组、同义词并列或多情绪列表；`answer`必须在当前数据集标签空间。映射理由非空；程序不按样本真值修改映射，也不宣称已自动核实全部语义。

summary继续输出情感推理与**一个最终标签**，不输出开放分类或第二个映射分类：

```json
{"reason":"核查证据、整合互补观点、处理关键冲突后的推理","answer":"worried","evidence_refs":[]}
```

最终`result.json`保留`prediction`、`emotion_analysis`和唯一`<answer>label</answer>`，另存三路`expert_emotions`，每路只有一个`open_emotion`和`mapped_label`及其`mapping_reason`。

## 隔离、验证与运行

- 新脚本：`versions/v3/pipeline.py`；提示词：`emotion_wheel_prompts.py`、独立快照`prompts_base.py`。
- 引用策略快照：`citation_policy_v3.py`；引用样式、缺失行内编号与未解析定位只记诊断，不因此重试。原模态、有效单标签、非空推理/证据与禁止gold泄漏检查仍保留。
- 图谱只读复用`data/gemini_graph_three_experts_v1/manifest.json`，不重新生成图谱。
- 新输出：`outputs/gemini_graph_emotion_wheel_v3/`；新报告：`metrics/gemini_graph_emotion_wheel_v3_comparison.md`、`_audit.json`。
- 系统提示词包含轮文本，签名含提示词、版本、输入与媒体哈希，不能误用v2预测。没有修改v2正在运行的进程、提示词、缓存或结果。

在主项目根目录运行：

```bash
.venv/bin/python versions/v3/pipeline.py --self-test
.venv/bin/python versions/v3/pipeline.py --init
.venv/bin/python versions/v3/pipeline.py --controller --providers gpt gemini
.venv/bin/python versions/v3/pipeline.py --audit
```

本次创建v3，只做编译、离线自检、初始化与空结果审计，**未启动模型调用或80条推理**。实际检查状态应以update.md及v3状态/报告为准。

已有80条是反复查看与迭代的开发子集；v3即使在同80条提升，也不是独立测试集泛化证据。创建本版本未再次基于对错挑选/优化规则。
