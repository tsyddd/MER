# 现有PPCT图谱质量评估

建议优先使用Gemini作为本项目的多模态图谱生成器；GPT适合作为较保守的视觉/字幕对照；当前实现下不优先选择Omni。

| 指标（各80张） | GPT | Gemini | Omni |
|---|---:|---:|---:|
| 平均节点数 | 6.58 | 7.03 | 8.51 |
| 平均边数 | 4.94 | 6.08 | 4.81 |
| 含时序关系的图谱 | 59 | 79 | 12 |
| 所有节点时间索引均为0的图谱 | 10 | 9 | 63 |
| 完全相同类型与内容的重复节点数 | 0 | 0 | 31 |
| 组织文本不含节点ID的样本 | 0 | 0 | 14 |

## 内容抽查

按每数据集清单第4/20/36条固定选6段，检查全部8帧、字幕、三模型节点/边与组织文本；没有按最终预测筛选。
- MELD/dia21_utt6: Target speaker Phoebe; Omni organization shifts its psychological conclusion to Chandler, while GPT/Gemini keep Phoebe as focal speaker.
- MELD/dia115_utt3: GPT allocates2 of6 nodes to producer credits, low relevance to target emotion; Gemini instead captures utterance segments and speech pause. Omni organization mistranslates backhand as slap.
- MELD/dia40_utt0: Gemini links visible smile with an audio-tagged rising/lively tone; tone not independently verified here. Omni describes a living room although frames show a populated cafe-like setting.
- MER2024/sample_00004468: Omni leftward-gaze claim contradicts sampled screen-right gaze; Gemini/GPT track visible facial changes. Gemini organization also has pronoun inconsistency.
- MER2024/samplenew_00035950: Gemini retains utterance sequence and scene-cut sequence; GPT is more sparse; Omni lacks temporal edges and gives opposite screen gaze direction.

## 解释与限制

Gemini在抽查中保留了更完整的话语阶段、表情动作及视听关系，但组织文本也会加入心理推断，且有代词不一致。GPT事实表述较保守，但部分图谱缺少时序和情绪相关线索，纳入片尾/制作人员字幕等背景噪声。Omni在时间标注、重复节点、目标人物保持和组织文本引用方面较弱。

时序边多不是正确性证明；静态片段没有时序边也未必错误。该评估不是全量语义金标准打分，不给虚构的质量分数。Gemini/Omni有音频而GPT没有，且Omni经过额外结构修复，不能宣称纯模型能力排名。音轨本次未独立听审。

若共享Gemini图谱给GPT，须记录GPT间接获得音频派生线索；固定8帧/目标人物/模态来源。组织文本的情绪推断与可核验事实应区分。保留原图谱，后续教师图谱作为独立版本，不覆盖原对照结果。
