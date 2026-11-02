# PPCT_emotion_training_free

多模态情绪识别与证据推理实验：MER2024六分类、MELD七分类，比较直接推理、PPCT、固定图谱三路专家及情绪轮适配。

## 版本

| 版本/方法 | 入口 | 输入与流程 |
|---|---|---|
| 直接推理/原PPCT | `engine.py` | 单阶段媒体推理；或感知节点→关系→程序组图→组织文本→最终预测 |
| v1 | `frozen_graph_experts.py` | 固定Gemini图谱；三路隔离输入；summary只读专家输出 |
| v2 | `shared_media_experts_v2.py` | 三路共享可用原媒体，graph专家独享图谱；summary接媒体与专家观点；四条rubric |
| v3 | `versions/v3/pipeline.py` | 独立快照；加入数据集适配情绪轮；专家一个开放情绪+一个映射标签，summary一个最终标签 |

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
- `update.md`：实验历史；其中运行PID及网络信息属于历史快照，不代表当前部署。
- `AGENTS.md`：AI维护约定；更改或运行项目时更新`update.md`。
- `reference/provenance.json`：既有PPCT参考实现来源。仓库未重新授权第三方代码或数据，复用前请核对原始许可。

数据集：[MER2024](https://zeroqiaoba.github.io/MER2024-website/)、[MELD](https://github.com/declare-lab/MELD)。情绪轮层级参考：[AffectGPT](https://github.com/zeroQiaoba/AffectGPT)。项目适配轮不是这些作者发布的官方分类轮。
