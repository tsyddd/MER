# 本机工作区与研究现状

核验日期：2026-11-02（Asia/Shanghai）。本文记录本机迁入边界与已保存实验结果，不代表服务器服务实时健康状态。

## 工作区来源

- 本机：`C:/Users/Admin/Documents/ppct`，后续开发与研究工作区。
- Git：`https://github.com/tsyddd/MER`，分支 `main`，迁入基线 `b444710`，保留原提交历史与 `origin`。
- 服务器：`liang@10.102.138.3:/media/liang/12T/han/open_source_generated/PPCT_emotion_training_free`。
- 克隆包含 5,871 个受版本控制文件；本机原有 `.omx/` 保留。
- 服务器完整目录约 67 GB，其中模型约 61 GB、数据约 6.6 GB。本机复制的是 GitHub 开发/研究导出快照，不是服务器完整磁盘镜像。
- 已包含：代码、独立版本、提示词、数据清单、固定图谱、精简结果、指标、实验记录和配置模板。
- 未包含：模型权重、原始音视频、抽帧缓存、真实服务配置/密钥、请求响应缓存、运行日志和 Linux 虚拟环境。服务器部署验证脚本 `verify_omni_restart_20261101.py` 也不在 GitHub 导出中。
- 服务器 `update.md` 比导出副本多三条 GitHub 导出/上传记录；最新一条记录 2026-11-02 11:59:15 上传成功。历史记录中的 PID 不代表当前仍运行。

## 迁入核验

- `git fsck --no-progress` 通过。
- 46 个导出清单内的 Python 源码及 comparison 指标文件 SHA256 匹配；比较时仅归一化 Windows CRLF 为 LF。
- 与服务器实时抽查的 27 个对应源码/指标文件哈希全部一致；另一个服务器验证脚本未被原导出收录。
- 使用标准库逐条读取结果与验证清单重新计算正确数，完整组与报告一致；审计条目重算的有效数也一致。train/validation 分别为 320/80，样本 ID 无交集；这不改变筛选与开发复用限制。
- 本次未安装实验依赖、未执行模型推理、未启动训练、未推送 GitHub。验证的是复制与静态结果，不是本机运行能力。

## 方法脉络

1. Direct：原媒体与字幕直接分类。
2. 原 PPCT：感知节点 → 时序/联合关系 → 程序组图 → 组织文本 → 原媒体、图谱及组织文本联合分类。入口 `engine.py`。
3. v1：固定 Gemini 图谱；同一 provider 的图谱、音频字幕、图像三路专家分别读取隔离信息；summary 只读专家输出。入口 `frozen_graph_experts.py`。
4. v2：三个专家均读取该 provider 可用的原媒体，仅图谱专家额外读取图谱与组织文本；summary 读取原媒体及专家输出。入口 `shared_media_experts_v2.py`。
5. v3：在 v2 基础上加入 MER6/MELD7 适配情绪轮，专家输出开放情绪、映射标签及理由，summary 输出一个最终类别。入口 `versions/v3/pipeline.py`。

三路专家是同一 provider 的不同角色，不是 GPT/Gemini/Omni 跨模型投票。原 PPCT 与专家方法通常每样本至少五次模型调用；固定图谱还有前置生成成本。

## 已保存结果

下表为 MER2024 40 条与 MELD 40 条合计 ACC；不完整实验不填完整 ACC。

| 方法 | GPT | Gemini | Omni Instruct |
|---|---:|---:|---:|
| Direct | 65.00% | 75.00% | 72.50% |
| 原 PPCT | 77.50% | 67.50% | 68.75% |
| v1 | 56.25% | 66.25% | 未完成，70/80 |
| v2 | 63.75% | 70.00% | 未完成，76/80 |
| v3 | 70.00% | 70.00% | 未完成，77/80 |

证据：`metrics/validation_comparison.md` 及三个版本的 `*_comparison.md`、`*_audit.json`。本机重新核对结果不等于重新运行实验。

Omni 审计失败记录：v1 为 9 条专家真实节点引用失败和 1 条组织文本引用失败；v2 为 3 条组织文本引用失败及 1 条 expert_graph 空错误文本（具体原因未确定）；v3 为 3 条组织文本引用失败。错误结果文件存在不等于推理成功，需按状态和审计计算有效数。

解读：当前结果支持“原 PPCT 在该 GPT 开发子集上优于直接推理”，不能支持跨模型稳定收益。v3 相比 v2 的 GPT 合计提升 6.25 个百分点，Gemini 合计持平；GPT v3 仍低于原 PPCT。失败原因与语义机制不能仅由 ACC 判断。

## 研究边界与本机运行条件

- 数据清单合计训练分区 320 条、验证分区 80 条；方法为 training-free，存在 train 清单不等于已训练模型。
- 样本从官方测试集按既有模型正确性筛选；80 条又用于已授权的人工反思与 v2/v3 开发。这里的结果是复用开发子集结果，不是独立测试泛化证据。
- 原五模型对照使用 4 帧，新方法使用 8 帧。GPT 无直接音轨输入，Gemini/Omni 有音轨；GPT 图谱分支仍可获得 Gemini 的音频派生信息。
- 结构/格式审计不等于解释内容真实；计费用量与成功阶段耗时也不等于完整成本及端到端墙钟时间。
- 数据及图谱清单保留服务器绝对路径；主要流水线使用 Linux `fcntl`，无法直接在原生 Windows 环境完整运行。后续实验需沿用 Linux 服务器，或先进行独立的路径/平台适配。
- `start_vllm.sh` 保留早期 Thinking 部署设置，不能直接视为当前 Instruct 服务的部署入口。

入口阅读顺序：`README.md` → 本文 → `metrics/validation_comparison.md` → 三版 comparison → `REFLECT_SHARED_MEDIA_V2.md` → `versions/v3/README.md` → 对应代码。后续修改遵守 `AGENTS.md` 与 `.agents/skills/project-update/SKILL.md`，同步维护 `update.md`。
