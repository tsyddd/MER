# PPCT_emotion_training_free

多模态情绪识别与证据推理实验：MER2024六分类、MELD七分类，比较直接推理、PPCT、固定图谱三路专家及情绪轮适配。

## 版本

| 版本/方法 | 入口 | 输入与流程 |
|---|---|---|
| 直接推理/原PPCT | `engine.py` | 单阶段媒体推理；或感知节点→关系→程序组图→组织文本→最终预测 |
| v1 | `frozen_graph_experts.py` | 固定Gemini图谱；三路隔离输入；summary只读专家输出 |
| v2 | `shared_media_experts_v2.py` | 三路共享可用原媒体，graph专家独享图谱；summary接媒体与专家观点；四条rubric |
| v3 | `versions/v3/pipeline.py` | 独立快照；加入数据集适配情绪轮；专家一个开放情绪+一个映射标签，summary一个最终标签 |

| v4 | `versions/v4/pipeline.py` | 专家反思 + 共同标签路由；无唯一共同标签时辩论（≤2轮） |
| v5 | `versions/v5/pipeline.py`、`versions/v5/orchestra.py` | 不一致分支上的 A/B0/B1/D 变体；v5-E 单 agent 先答、拿不准再回看 |
| v6 R²-MAD | `versions/v6/run_rmad.py` | 辩论中按 bge-m3 检索训练样本经验 |
| v6 SkillOpt-V5E | `versions/v6/skillopt_v5e/`、`versions/v6/skillopt_v5e_v2/` | 在训练/验证子集上为 v5-E 优化技能文本，门控后在测试子集评估 |

v1/v2/v3结果分别位于`outputs/gemini_graph_three_experts_v1`、`outputs/gemini_graph_shared_media_v2`、`outputs/gemini_graph_emotion_wheel_v3`。最终输出包含证据解释与唯一`<answer>label</answer>`。

## 结果快照

每数据集40条，共80条；下列均为完整80条结果。

| 方法 | MER2024 ACC | MELD ACC | 合计ACC |
|---|---:|---:|---:|
| GPT direct | 60.00% | 70.00% | 65.00% |
| GPT 原PPCT | 77.50% | 77.50% | 77.50% |
| GPT v1 | 60.00% | 52.50% | 56.25% |
| GPT v2 | 60.00% | 67.50% | 63.75% |
| GPT v3 | 77.50% | 62.50% | 70.00% |
| Gemini direct | 82.50% | 67.50% | 75.00% |
| Gemini 原PPCT | 75.00% | 60.00% | 67.50% |
| Gemini v1 | 77.50% | 55.00% | 66.25% |
| Gemini v2 | 77.50% | 62.50% | 70.00% |
| Gemini v3 | 80.00% | 60.00% | 70.00% |
| Omni Instruct direct | 85.00% | 60.00% | 72.50% |
| Omni Instruct 原PPCT | 75.00% | 62.50% | 68.75% |

Omni v1仅70/80有效、v2仅76/80、v3仅77/80，本快照不提供其完整80条ACC。完整指标、失败记录与最初五模型比较见`metrics/`。

这是按既有模型正确性筛选、反复开发的子集；v2/v3已用其中样本做人工反思，不能声称官方完整测试集或独立泛化成绩。最初五模型4帧，新方法8帧。GPT只接图片/字幕，但共享Gemini图谱可含音频派生信息；Gemini/Omni另接真实音轨。API模型身份只按请求/返回名记录。

## v4–v6 结果摘要

v5/v6 都在 v4 的不一致分支（Gemini 62 条、GPT 55 条，共117条）上比较。详细数字、设置和限制见 `metrics/findings_log.md`（F3–F18）。

| 方法 | Gemini /62 | GPT /55 | 合计 /117 |
|---|---:|---:|---:|
| 随机（期望） | 25.6 | 22.8 | 48.4 |
| v4 辩论 | 26 | 19 | 45 |
| Direct 5次均值 | 36.6 | 23.8 | 60.4 |
| v5-E 首次作答 | 39 | 22 | 61 |
| v6 R²-MAD n0 / n3 | 25 / 26（n3缺1条） | 19 / 21 | 44 / 47 |
| v6 SkillOpt-V5E 版本1 技能 | 32（epoch 3） | 21 | — |
| v6 SkillOpt-V5E 版本2 技能（2次均值） | 33 | — | — |

- v4 在80条与400条上都没有超过三专家多数投票，不一致分支上约等于在候选里随机选（F3–F6）。
- v5 各变体没有稳定超过 Direct；Direct 单次运行本身波动约 ±3 条以上（F8、F11、F12）。
- v6 R²-MAD 的经验检索未达事先定的标准；SkillOpt-V5E 两个版本的技能都没有超过同设置对照（对照 Gemini 37–40、GPT 22）（F15–F18）。

## 结果页面（`docs/`）

静态 HTML，直接用浏览器打开。

- 总览：`project-journey.html`（项目回顾）、`work-log-20261102-03.html`、`ppct-flow.html`
- 数据与诊断：`dataset-label-distribution.html`、`confusion-matrices.html`、`expert-union-confusable.html`、`debate-vs-vote.html`
- v3/v4：`v3-gpt-stages.html`、`v3-prompt-wheel.html`、`v3-v4-prompt-diff.html`、`v4-80-debate-analysis.html`
- v5：`v5-design.html`、`v5-methods.html`、`v5-orchestra.html`、`v5-results.html`、`v5-results-details.html`
- v6：`v6-selfevolve-design.html`、`v6-rmad-report.html`、`v6-rmad-retrieval.html`、`v6-skillopt-v5e-design.html`、`v6-skillopt-v5e-flow.html`、`v6-skillopt-v5e-report.html`、`v6-skillopt-v5e-v2-design.html`、`self-evolving-*.html`
- 文献调研：`agent-debate-survey.html`、`agent-orchestration-survey.html`、`mad-*.html`、`ts-debate-mm-stancedet-methods.html`

生成这些页面的脚本在 `scripts/build_*.py`，分析脚本为 `scripts/analyze_*.py`，对应数据在 `metrics/`。

## 环境与配置

运行端为Linux、Python3.11+，依赖见`requirements.txt`。vLLM服务另行部署，不由该依赖清单安装。本仓库保留实验时服务器路径，启动前需调整数据清单中的`video`、`audio`与图谱清单路径，以及部署脚本中的目录和网络配置。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp configs/providers.example.json configs/providers.json
cp configs/private_api.example.json configs/private_api.json
chmod 600 configs/private_api.json
```

填写自有API地址/密钥及Omni端点。不要提交实际配置或密钥。原始数据需从对应官方渠道获得并放置到清单引用位置；模型权重、音视频、抽帧、虚拟环境与API原请求/响应不包含在导出中。图谱manifest含SHA及原始运行路径，搬迁时需单独制作路径适配副本，保留版本来源。

```bash
python shared_media_experts_v2.py --self-test
python versions/v3/pipeline.py --self-test
python shared_media_experts_v2.py --audit
python versions/v3/pipeline.py --audit
# 以下命令会产生实际API调用与费用：
python versions/v3/pipeline.py --controller --providers gpt gemini
```

不要同时重复运行同版本同provider；锁、成功样本和阶段签名缓存支持续跑。各版本独立保存，勿覆盖旧版本。引用格式采用宽松诊断，不等于所有证据语义经人工验证。

## 文件与来源

- `versions/v3/README.md`：v3协议、适配轮与独立源文件哈希。
- `REFLECT_SHARED_MEDIA_V2.md`：反思方法、所选案例说明与v2流程。
- `metrics/`、`outputs/`：汇总及精简阶段结果，不含原请求缓存。
- `EXPORT_MANIFEST.json`：从服务器导出的文件大小和SHA256；本README及上传配置是导出后新增文件。
- `metrics/findings_log.md`：已确认的结论（F1–F18），含设置、数字与限制。
- `LOCAL_WORKSPACE.md`：本机工作区迁入记录。
- `update.md`：实验历史；其中运行PID及网络信息属于历史快照，不代表当前部署。
- `AGENTS.md`：AI维护约定；更改或运行项目时更新`update.md`。
- `reference/provenance.json`：既有PPCT参考实现来源。仓库未重新授权第三方代码或数据，复用前请核对原始许可。

数据集：[MER2024](https://zeroqiaoba.github.io/MER2024-website/)、[MELD](https://github.com/declare-lab/MELD)。情绪轮层级参考：[AffectGPT](https://github.com/zeroQiaoba/AffectGPT)。项目适配轮不是这些作者发布的官方分类轮。
