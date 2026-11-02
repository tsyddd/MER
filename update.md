## Omni v2/v3已排队（2026-11-02T00:07:03+08:00）

用户明确授权Omni启动后运行v2及v3各80条。run_omni_v2_v3.py持久顺序调度，日志logs/omni_v2_v3_scheduler.log；状态logs/omni_v2_v3/status.json，PID logs/omni_v2_v3/pid.json。先等待既有部署验证器621320的两条真实8帧+音频+字幕通过，再只启动Omni v2两条smoke→80条，结束后Omni v3两条smoke→80条；各4workers。原v1结果/版本源码不改，v2/v3独立输出/缓存。仅Omni，不重跑GPT/Gemini。当前dashan1632939从原盘加载，刚核对4/15分片，未就绪，不重启健康加载。

## v2/v3最新核验与恢复（2026-11-02T00:03:40+08:00）

v2 GPT80/80：MER24/40=60%、MELD27/40=67.5%、总51/80=63.75%；Gemini80/80：MER31/40=77.5%、MELD25/40=62.5%、总56/80=70%。v3 Gemini80/80：MER32/40=80%、MELD24/40=60%、总56/80=70%。v3 GPT66/80，MER31/40=77.5%，MELD16/26已完成部分；完整ACC未出。旧controller已结束，14条HTTP429服务商用量冷却错误，现仅恢复缺失项：resume_v3_gpt_cooldown.py，日志logs/v3_gpt_cooldown_recovery.log，状态logs/v3_gpt_cooldown_recovery/status.json；顺序运行并按返回冷却有界等待，不重跑成功样本/阶段。版本源码、轮和提示词不修改。

## Omni服务重启（2026-11-02T00:00:15+08:00）

用户明确要求kill当前占卡进程并启动Omni。已核对并停止dashan human_preference的Qwen3.8-27B vLLM543928进程树，仅该树；旧PPCT服务402491早已退出。新Omni PID1632939，日志dashan serving/logs/vllm_omni_restart_20261101_235917.log；原磁盘Instruct/TP4/4并发/KV2GiB/8帧音频配置不变。正在加载，尚未实际验证。liang后台verify_omni_restart_20261101.py等待服务后做MER/MELD各一条真实8帧+音频+字幕验证，状态logs/omni_restart_20261101_235917_verification/status.json；不自动重跑任何v1/v2/v3实验。

## v3已启动（2026-11-01T19:55:02+08:00）

v3独立controller337275，GPT/Gemini各80条，先跨MER/MELD两条smoke，通过后全量；状态outputs/gemini_graph_emotion_wheel_v3/controller_status.json，主日志logs/emotion_wheel_v3_api_controller.log。阶段当前{'gpt': {'organization': 2, 'expert_graph': 1, 'expert_audio_subtitle': 0, 'expert_image': 0, 'summary': 0}, 'gemini': {'organization': 2, 'expert_graph': 2, 'expert_audio_subtitle': 2, 'expert_image': 2, 'summary': 1}}。v2 Gemini80/80已审计ACC70%（MER77.5%、MELD62.5%），v2 GPT仍运行，旧进程和结果保留。v3尚无完整成绩，不能把已启动当完成；Omni未启动。

## 最新独立版本 v3（2026-11-01T19:53:00+08:00）

已创建versions/v3/，新实验ID gemini_graph_emotion_wheel_v3；独立pipeline.py、emotion_wheel_prompts.py、prompts_base.py快照、citation_policy_v3.py快照、emotion_wheels.json及MER2024/MELD情绪轮SVG、README、source_manifest.json。MER6/MELD7 Level1保持原标签，项目适配非官方轮。每专家输出一个open_emotion、一个answer及mapping_reason；summary仍推理+一个answer，无open_emotion。各专家/summary嵌入当前数据集轮，保持4rubric/8帧/可用音频字幕/独享图谱路由与宽松引用策略。

编译、自检、初始化、空结果审计及两provider五阶段离线模拟回环/缓存检查通过；模拟产物在临时目录删除，0真实模型调用，无v3 ACC。旧v1/v2文件、提示词、输出与进程未改动；固定Gemini图谱只读复用。v3所有输出在outputs/gemini_graph_emotion_wheel_v3/，报告metrics/gemini_graph_emotion_wheel_v3_*。创建器拒绝覆盖不同内容，源文件哈希已核对。实际运行入口见versions/v3/README.md，当前未启动v3实验。

## 当前引用策略与运行状态（2026-11-01T19:03:41+08:00）

引用格式已放宽，controller274792正在继续GPT/Gemini v2；原controller266536已退出。主日志logs/shared_media_v2_api_soft_citations.log。当前有效{'gpt': 2, 'gemini': 8}，未完成不能给最终ACC。只因引用写法不规范不再重试，原始证据和结果保留。

## v2 API运行状态（2026-11-01T19:00:04+08:00）

用户已授权GPT/Gemini各80条，后台controller266536正在运行；仅这两个provider，不启动Omni。状态outputs/gemini_graph_shared_media_v2/controller_status.json；日志logs/shared_media_v2_api_controller.log；当前逐条审计{'gpt': 0, 'gemini': 2}。成功阶段跳过，失败有限重试；完成后metrics/gemini_graph_shared_media_v2_comparison.md/_audit.json。此前“未启动v2”的条目为历史记录。

## 最新提示词迭代 v2（2026-11-01T18:54:43+08:00）

已按用户明确指令完成一次人工reflect：8个GPT/Gemini正确/错误结果、6段唯一视频；查看8帧、字幕、图谱与推理，未独立听审音轨。新版本gemini_graph_shared_media_v2：三路独立专家都接全部可用原媒体/字幕，仅graph专家额外接图谱/组织文本；summary接媒体/字幕/三路结构化证据，不接原图谱/组织文本。每角色4条rubric，证据按具体、可信、非重复及互补程度衡量而非计票。提示词shared_media_expert_prompts_v2.py，运行审计shared_media_experts_v2.py，反思与协议REFLECT_SHARED_MEDIA_V2.md，案例metrics/reflect_v2_cases.json。离线路由/引用/无音频限制/标签/gold隔离/缓存签名检查通过；初始化与空结果审计通过。未调用v2模型，未跑v2全80，暂无新版ACC。旧v1与原六组保留。

并发最新核验：4路实际8帧+音频请求成功，observed_running_peak=4；dashan服务402491健康。v1续跑已有限重试结束，GPT80/80、Gemini80/80、Omni70/80有效，剩余10条保留失败原因，不宣称完成。恢复监督227214已结束，勿按旧PID当作仍在跑。用户本轮授权明确使用已有验证结果反思，故这80仅作开发迭代，后续同集提升不代表独立泛化；未将标签或样本特例写入提示词。

## 最新并发状态（2026-11-01 Asia/Shanghai）

用户最新要求4路：dashan服务402491从原磁盘重载，max-num-seqs=4、每卡KV2GiB；日志logs/vllm_concurrency4.log（dashan）。liang恢复监督227214，logs/concurrency4_supervisor.log，状态logs/concurrency4/status.json；待服务就绪后自动四条实际8帧+音频请求验证，成功后仅Omni4workers续跑，逐条复用成功样本/阶段。当前新实验GPT80/80、Gemini80/80、Omni62/80审计有效。尚未完成实际四路验证，不能宣称服务已就绪。此次并发配置变化不会修改提示词、图谱、情绪轮或缓存签名；批处理浮点差异可能影响后续生成。恢复入口resume_omni_concurrency4.py，进程已持久运行，勿重复启动。

# PPCT_emotion_training_free 工作记录

更新时间：2026-11-01（Asia/Shanghai）。本文件必须由每个改动或运行本项目的 AI 同步维护，入口约定见 [AGENTS.md](AGENTS.md)，具体技能见 [.agents/skills/project-update/SKILL.md](.agents/skills/project-update/SKILL.md)。

## 当前进行中的新实验：固定Gemini图谱＋三路专家

- 实验gemini_graph_three_experts_v1：固定Gemini80张图谱，三个模型各自生成组织文本，再独立运行图谱/组织文本、音频字幕、8帧图片专家；同模型summary只读取三路输出。GPT字幕路无音频，但图谱路间接获得音频派生线索。
- 三模型MER/MELD各一条实际试跑均通过输出及模态隔离审计，已自动进入全80条，尚未完成，不能沿用旧ACC作为新结果。
- controller142090；当前全量worker GPT145102、Gemini143854、Omni145103。状态outputs/gemini_graph_three_experts_v1/controller_status.json；主日志logs/gemini_graph_three_experts_v1_controller.log。
- 提示词frozen_graph_expert_prompts.py；运行/审计脚本frozen_graph_experts.py；说明FROZEN_GRAPH_EXPERTS.md；固定图谱data/gemini_graph_three_experts_v1/manifest.json。
- 完成后自动逐样本审计并写metrics/gemini_graph_three_experts_v1_comparison.md与_audit.json。旧六组结果不覆盖；健康任务保留，失败阶段有限重试并保留缓存。

## 当前核验结果（2026-11-01 16:45最终审计）

- 六组全部80/80逐条通过流程/格式审计，缺失0、当前错误0；已完成480条方法-样本结果。固定验证集MER2024/MELD各40，MER6类、MELD7类。
- Omni Instruct直接：MER34/40=85%、MELD24/40=60%、合计58/80=72.5%；PPCT：MER30/40=75%、MELD25/40=62.5%、合计55/80=68.75%。
- GPT直接：MER24/40=60%、MELD28/40=70%、合计52/80=65%；PPCT：两集各31/40=77.5%、合计62/80=77.5%。
- Gemini直接：MER33/40=82.5%、MELD27/40=67.5%、合计60/80=75%；PPCT：MER30/40=75%、MELD24/40=60%、合计54/80=67.5%。
- 最终统一报告metrics/validation_comparison.md及.json，同时保留all_methods_validation_report.md/.json；包含既有五模型4帧和新六组8帧对照、用量、有效/错误数、成功阶段耗时及统计限制。审计metrics/full_stage_format_audit.json。
- dashan原磁盘Instruct服务3243931保持运行，http://10.102.138.2:18030/v1，served ID omni30b-instruct；Thinking权重校验后保留，本次不用。调度器已正常完成退出；不重跑成功样本。
- PPCT Omni结构容错包含完整截断节点恢复，原始响应、修复日志及归档保留；与GPT/Gemini严格策略的差异写入报告。解释事实正确性未逐条人工审查。数据是筛选开发子集，非原始完整测试集。
- 六组全部通过后按用户授权停用本次小时自动化；vLLM服务不随自动化停止。

## 目标与实验约定

- 项目：liang `/media/liang/12T/han/open_source_generated/PPCT_emotion_training_free`。
- 最新授权：在dashan用已有 **Qwen3-Omni-30B-A3B-Instruct** 部署vLLM供liang调用；用户明确允许有Instruct则直接使用，覆盖此前仅Thinking要求。已下载Thinking权重保留，当前实验以Instruct为准。
- MER2024、MELD各200条；每集训练160、验证40，合计训练320、验证80。MER2024为6分类，MELD为7分类；标签并集有8个展示类别，不合并 worried 与 fear。
- 保存既有5模型的推理与分类输出，并在固定80条验证集统计ACC。
- Omni直接推理80条作为baseline。Omni、GPT、Gemini各自运行PPCT：事实节点 → temporal/joint边 → 程序组图 → 组织文本 → 原始媒体与组织文本联合推理。最终类别用 `<answer></answer>` 包装。
- 新baseline/PPCT均抽8帧；既有5模型对比是4帧，必须披露差异。Omni/Gemini优先音频＋字幕＋8帧；GPT若音频不支持则记录后省略。没有字幕时不添加虚构字幕。
- 参考实现位于dashan：`/media/4t_2/hhp/open_source_generated/ppct_training_free_api`，脱敏源码已存入本项目 `reference/ppct_api/`，溯源信息在 `reference/provenance.json`。

## 已完成

- 创建项目目录与 `.gitignore`。
- 将400条筛选样本的视频、音频、4帧缓存实际复制到 `data/media/`；迁入 `data/manifests/{train,validation}.jsonl`，路径指向项目内副本。保留原数据，未破坏其他实验。
- 五模型原始三数据集JSONL已复制到 `outputs/five_models/raw/`；400条对应的推理、分类与原始输出位于 `outputs/five_models/selected/<model>/{train,validation}.jsonl`。
- 固定80条验证集ACC保存在 `metrics/five_models_validation_acc.json` 与 `.md`。
- 创建项目虚拟环境 `.venv`，继承 `/home/liang/miniconda3/envs/vllm-qwen3vl` 的只读包。检测到 Python3.11.15、vLLM0.11.2、Torch2.9.0+cu126、Transformers4.57.6；CUDA可识别，vLLM包含 `qwen3_omni_moe_thinker.py`。尚未完成实际模型加载验证。
- API文本探测通过，状态在 `configs/api_probe.json`：请求 `gpt-6-sol` 成功；Gemini列表提供 `gemini-3.8-flash-high`，请求成功，服务返回模型名 `gemini-3.8-flash-n`。这只是服务报告的名称，未独立证明底层模型身份。8帧图像测试通过；GPT明确返回Audio input is not available，按用户授权省略音频；Gemini音频测试通过，见 configs/multimodal_probe.json。
- 密钥存于 `configs/private_api.json`，权限0600并被忽略；日志和文档不含密钥。

## 既有5模型验证集ACC（4帧）

| 模型 | MER2024 40条 | MELD 40条 | 合计80条 |
|---|---:|---:|---:|
| Emotion-LLaMA | 33/40，82.50% | 26/40，65.00% | 59/80，73.75% |
| AffectGPT | 27/40，67.50% | 31/40，77.50% | 58/80，72.50% |
| AffectGPT-RL | 31/40，77.50% | 15/40，37.50% | 46/80，57.50% |
| OPPO | 32/40，80.00% | 22/40，55.00% | 54/80，67.50% |
| VidEmo-7B | 27/40，67.50% | 28/40，70.00% | 55/80，68.75% |

## 进行中

- 官方Thinking权重现由 `download_modelscope.py` 下载；当前PID见 `logs/download_modelscope.pid`。旧HF下载PID3207949已停止，保留其缓存。
- 固定HF版本：`2f443cfc4c54b14a815c0e2bb9a9d6cbcd9a748b`；官方文件总大小 **63,447,489,451字节**，16个safetensors分片。清单：`models/official_download_manifest.json`。
- 目标：`models/Qwen3-Omni-30B-A3B-Thinking`；日志：`logs/download_omni.log`；状态：`logs/download_omni_status.json`。必须等状态verified及分片大小/SHA校验通过，才能宣称下载完成。
- ModelScope全部3791分段已收齐，正在按固定HF SHA校验；download_guard.py持久监督，下载PID文件现指向守护进程，实际worker见logs/download_worker.pid。失败补下载已降为8线程并复用范围标记。进度日志已修复，不再因单分段失败停更。未见download_verified.json前不能宣称校验完成。
- 项目内 `update.md`、项目级技能、`AGENTS.md` 已生效并验证，另有CLAUDE.md、GEMINI.md入口。

## 待办

1. 后续每次实质工作按已生效的项目级技能更新本文件。
2. 【已完成】80条验证视频均生成8帧，全部8帧互异；采样索引、时间及哈希见data/frames8，核验见verification.json。
3. 【已完成】GPT支持8帧但拒绝音频；Gemini支持8帧和音频。能力记录configs/multimodal_probe.json。
4. 【实现完成】engine.py按各数据集标签和实际模态实现五步PPCT，最终直接联合推理。两模型首条端到端成功，继续核验第二条与全量。
5. 对节点、边端点/层次/时序、组织文本引用、最终单标签及无真实标签泄漏做必要验证；保存每阶段请求摘要、原始响应和结构化结果，支持按阶段恢复。
6. 下载验证后启动四卡vLLM，先用单样本测试纯文本与音视频，再跑80条Omni直接基线。
7. Omni、GPT、Gemini各跑80条PPCT。先各选两个跨数据集样本做端到端检查，成功后跑全量；准确记录失败，不用猜测标签补齐。
8. 生成比较报告：每数据集及合计ACC、完成数、错误数、帧数/模态差异、调用用量、耗时、版本与数据清单哈希。

## 重要限制与接续入口

- 这是从官方测试集根据5模型正确率筛出的、类别近似均衡的开发数据，验证结果有选择偏差，不可称为未见测试集整体表现。
- 400条中329条至少3模型正确，71条为稀缺类别补充；MELD有1条0模型正确，详情见 `data/selection_report.json` 的来源记录。模型候选推理并未人工核验。
- MELD训练/验证对话互斥；MER2024缺原始影视剧/对话分组，未证明来源或演员独立。
- 4×RTX3090合计96GiB在容量上可尝试装入BF16权重，但KV缓存、多模态编码和运行时会额外占用，必须实际试跑；不能仅凭容量宣称部署成功。计划TP=4、并发1、较短上下文、限制8图＋1音频，绑定127.0.0.1。
- 使用remote-servers技能脚本连接liang；不要读取或展示技能凭证。开始/接续先查GPU、下载状态和进程，避免重复任务。

## 工作记录

- 2026-11-01：创建项目、迁入400条媒体与清单、导出5模型推理分类、统计80条验证ACC；确认Thinking版本；启动官方权重下载；API文本调用成功；建立项目更新约定。下一步：将本记录与技能同步远端，完成多模态探测与PPCT实现。

- 2026-11-01：部署 engine.py（五步PPCT、每阶段缓存、原始响应和错误、标签隔离）、probe_multimodal.py（80条8帧＋API多模态探测）。增加作者ModelScope分段下载器，权重必须与固定HF清单SHA一致；停止本项目慢速HF下载PID3207949，保留其已下载部分，改用16并发范围下载。技能通过quick_validate。

- 2026-11-01 01:02:13（Asia/Shanghai）：完成80条8帧预处理和外部API多模态探测；结果 configs/multimodal_probe.json，实际模态写入 configs/providers.json。

- 2026-11-01：80条验证视频全部生成8帧，无重复采样帧。GPT仅图像＋字幕，Gemini图像＋音频＋字幕；完成能力探测。部署 start_vllm.sh 和 orchestrate.py；调度器先做2条跨数据集PPCT测试，通过后运行80条。Omni等待权重验证后启动，不将未运行结果当作baseline。

- 2026-11-01 01:06:41（Asia/Shanghai）：调度 gpt_ppct_smoke，PID=3225363，日志 logs/gpt_ppct_smoke_attempt1.log。

- 2026-11-01 01:06:41（Asia/Shanghai）：调度 gemini_ppct_smoke，PID=3225364，日志 logs/gemini_ppct_smoke_attempt1.log。

- 2026-11-01 01:06:41（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 01:06:41（Asia/Shanghai）：后台进度：运行任务 gpt_ppct_smoke, gemini_ppct_smoke；下载范围 208/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:06:41（Asia/Shanghai）：启动 gpt/ppct，2条，workers=1；结果目录 outputs/ppct/gpt。

- 2026-11-01 01:06:41（Asia/Shanghai）：启动 gemini/ppct，2条，workers=1；结果目录 outputs/ppct/gemini。

- 2026-11-01 01:10:03（Asia/Shanghai）：gemini/ppct 本轮结束：1/2有效；错误1；统计 outputs/ppct/gemini/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:11:41（Asia/Shanghai）：后台进度：运行任务 gpt_ppct_smoke；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:12:31（Asia/Shanghai）：按用户要求优先推进GPT/Gemini各80条验证。核查发现Gemini第二条在DNS解析失败，GPT也记录同类网络错误；排查项目专用网络恢复，不改变样本或评测规则。

- 2026-11-01 01:16:41（Asia/Shanghai）：后台进度：运行任务 gpt_ppct_smoke；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:18:22（Asia/Shanghai）：优先推进GPT/Gemini验证。直连DNS/网络和旧17897代理失败；新建18097到本地7897专用转发并验证连通。Windows转发进程54680，本地SSH配置有PPCT dedicated forwarding 18097标记。重启本项目API任务接续缓存。

- 2026-11-01 01:18:24（Asia/Shanghai）：engine.Client增加项目级proxy_url配置，GPT和Gemini使用18097代理；保持全部提示词、标签、媒体及成功缓存，重新检查后跑各80条。Omni本地连接不变。

- 2026-11-01 01:18:24（Asia/Shanghai）：调度 gpt_ppct_smoke，PID=3230310，日志 logs/gpt_ppct_smoke_attempt1.log。

- 2026-11-01 01:18:24（Asia/Shanghai）：调度 gemini_ppct_smoke，PID=3230311，日志 logs/gemini_ppct_smoke_attempt1.log。

- 2026-11-01 01:18:24（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 01:18:24（Asia/Shanghai）：后台进度：运行任务 gpt_ppct_smoke, gemini_ppct_smoke；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:18:24（Asia/Shanghai）：启动 gpt/ppct，2条，workers=1；结果目录 outputs/ppct/gpt。

- 2026-11-01 01:18:24（Asia/Shanghai）：启动 gemini/ppct，2条，workers=1；结果目录 outputs/ppct/gemini。

- 2026-11-01 01:18:45（Asia/Shanghai）：gpt/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gpt/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:18:54（Asia/Shanghai）：调度 gpt_ppct，PID=3230886，日志 logs/gpt_ppct_attempt1.log。

- 2026-11-01 01:18:54（Asia/Shanghai）：启动 gpt/ppct，80条，workers=2；结果目录 outputs/ppct/gpt。

- 2026-11-01 01:19:03（Asia/Shanghai）：用户询问整体进度：项目、400媒体、5模型归档及80验证ACC、8帧和API能力核验已完成。新的18097代理恢复后GPT第二条已完成感知/边/组织，Gemini第二条已完成感知。重启调度器PID3230115，两个API工作进程3230310、3230311；检查通过后各跑80条，不等待Omni。全量结果未完成。

- 2026-11-01 01:19:27（Asia/Shanghai）：gemini/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gemini/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:19:39（Asia/Shanghai）：调度 gemini_ppct，PID=3231611，日志 logs/gemini_ppct_attempt1.log。

- 2026-11-01 01:19:39（Asia/Shanghai）：启动 gemini/ppct，80条，workers=2；结果目录 outputs/ppct/gemini。

- 2026-11-01 01:23:24（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:24:45（Asia/Shanghai）：用户要求创建每小时持续检查与恢复任务，并授权Omni图谱更宽松、优先线索组织文本质量；GPT/Gemini须确保各80条五步PPCT完成且格式正确。

- 2026-11-01 01:24:45（Asia/Shanghai）：已通过Codex应用创建当前聊天每小时自动化 omni-gpt-gemini-ppct，状态ACTIVE。配置入口configs/hourly_monitor.json；每次核查下载/API/进程并修复或接续，避免重复任务。Omni SHA校验及服务试跑通过后接续80直接基线和80 PPCT；GPT/Gemini各80 PPCT须全量审计。Omni宽松图谱策略尚需在本地推理启动前落实到代码，现有GPT/Gemini不受影响。全部完成且审计通过后自动停用。

- 2026-11-01 01:28:24（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:33:24（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:38:24（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:43:24（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:48:24（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:49:04（Asia/Shanghai）：gpt/ppct 本轮结束：4/80有效；错误76；统计 outputs/ppct/gpt/summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:49:09（Asia/Shanghai）：gemini/ppct 本轮结束：3/80有效；错误77；统计 outputs/ppct/gemini/summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:49:09（Asia/Shanghai）：调度 gpt_ppct，PID=3242772，日志 logs/gpt_ppct_attempt2.log。

- 2026-11-01 01:49:09（Asia/Shanghai）：调度 gemini_ppct，PID=3242773，日志 logs/gemini_ppct_attempt2.log。

- 2026-11-01 01:49:10（Asia/Shanghai）：启动 gpt/ppct，80条，workers=2；结果目录 outputs/ppct/gpt。

- 2026-11-01 01:49:10（Asia/Shanghai）：启动 gemini/ppct，80条，workers=2；结果目录 outputs/ppct/gemini。

- 2026-11-01 01:52:59（Asia/Shanghai）：gpt/ppct 本轮结束：4/80有效；错误76；统计 outputs/ppct/gpt/summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:53:05（Asia/Shanghai）：gemini/ppct 本轮结束：3/80有效；错误77；统计 outputs/ppct/gemini/summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:53:24（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:54:03（Asia/Shanghai）：进度核查：GPT4/80、Gemini3/80成功，其余因18097代理Connection refused失败；本地新增keep_forward.ps1断线20秒重连监督，保持7897代理，重启本项目调度器续跑缓存。下载实际2257/3791分段完成，日志汇总滞后，未校验完成。

- 2026-11-01 01:54:03（Asia/Shanghai）：调度 gpt_ppct_smoke，PID=3248848，日志 logs/gpt_ppct_smoke_attempt1.log。

- 2026-11-01 01:54:03（Asia/Shanghai）：调度 gemini_ppct_smoke，PID=3248849，日志 logs/gemini_ppct_smoke_attempt1.log。

- 2026-11-01 01:54:03（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 01:54:03（Asia/Shanghai）：后台进度：运行任务 gpt_ppct_smoke, gemini_ppct_smoke；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 01:54:03（Asia/Shanghai）：启动 gemini/ppct，2条，workers=1；结果目录 outputs/ppct/gemini。

- 2026-11-01 01:54:03（Asia/Shanghai）：gemini/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gemini/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:54:03（Asia/Shanghai）：启动 gpt/ppct，2条，workers=1；结果目录 outputs/ppct/gpt。

- 2026-11-01 01:54:03（Asia/Shanghai）：gpt/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gpt/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 01:54:18（Asia/Shanghai）：调度 gpt_ppct，PID=3249287，日志 logs/gpt_ppct_attempt1.log。

- 2026-11-01 01:54:18（Asia/Shanghai）：调度 gemini_ppct，PID=3249288，日志 logs/gemini_ppct_attempt1.log。

- 2026-11-01 01:54:18（Asia/Shanghai）：启动 gemini/ppct，80条，workers=2；结果目录 outputs/ppct/gemini。

- 2026-11-01 01:54:18（Asia/Shanghai）：启动 gpt/ppct，80条，workers=2；结果目录 outputs/ppct/gpt。

- 2026-11-01 01:59:03（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:00:29（Asia/Shanghai）：18097存在监听但连通测试超时，用户手动隧道绑定失败。将外部API代理配置改为已检查无监听的18099，等待用户建立独立SSH转发；已有进程仍用旧配置，隧道核验后需接续失败项。

- 2026-11-01 02:01:07（Asia/Shanghai）：用户要求重新测试GPT/Gemini，检查18099代理与实际认证接口，连通后接续验证任务。

- 2026-11-01 02:01:11（Asia/Shanghai）：API重新探测：{"provider": "gpt", "http_status": 200, "seconds": 4.14, "response_model": "gpt-6-sol", "content": "OK", "usage": {"completion_tokens": 5, "total_tokens": 312, "prompt_tokens": 307, "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0, "cached_creation_tokens": 0}, "completion_tokens_details": {"reasoning_tokens": 0}}}

- 2026-11-01 02:01:19（Asia/Shanghai）：API重新探测：{"provider": "gemini", "error": "HTTPSConnectionPool(host='api2.mcben.top', port=443): Read timed out. (read timeout=8)"}

- 2026-11-01 02:01:38（Asia/Shanghai）：18099代理GPT文本实测HTTP200；Gemini第一次网络读超时。停止本项目旧配置API任务和调度器，准备通过新18099重启；保留成功样本与阶段缓存。

- 2026-11-01 02:01:58（Asia/Shanghai）：新隧道多模态探测：{"provider": "gpt", "success": false, "error": "HTTPSConnectionPool(host='api2.mcben.top', port=443): Read timed out. (read timeout=20)"}

- 2026-11-01 02:02:18（Asia/Shanghai）：新隧道多模态探测：{"provider": "gemini", "success": false, "error": "HTTPSConnectionPool(host='api2.mcben.top', port=443): Read timed out. (read timeout=20)"}

- 2026-11-01 02:02:19（Asia/Shanghai）：调度 gpt_ppct_smoke，PID=3259551，日志 logs/gpt_ppct_smoke_attempt1.log。

- 2026-11-01 02:02:19（Asia/Shanghai）：调度 gemini_ppct_smoke，PID=3259552，日志 logs/gemini_ppct_smoke_attempt1.log。

- 2026-11-01 02:02:19（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 02:02:19（Asia/Shanghai）：后台进度：运行任务 gpt_ppct_smoke, gemini_ppct_smoke；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:02:19（Asia/Shanghai）：启动 gpt/ppct，2条，workers=1；结果目录 outputs/ppct/gpt。

- 2026-11-01 02:02:19（Asia/Shanghai）：启动 gemini/ppct，2条，workers=1；结果目录 outputs/ppct/gemini。

- 2026-11-01 02:02:19（Asia/Shanghai）：gemini/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gemini/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 02:02:19（Asia/Shanghai）：gpt/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gpt/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 02:02:34（Asia/Shanghai）：调度 gpt_ppct，PID=3259975，日志 logs/gpt_ppct_attempt1.log。

- 2026-11-01 02:02:34（Asia/Shanghai）：调度 gemini_ppct，PID=3259976，日志 logs/gemini_ppct_attempt1.log。

- 2026-11-01 02:02:34（Asia/Shanghai）：启动 gpt/ppct，80条，workers=2；结果目录 outputs/ppct/gpt。

- 2026-11-01 02:02:34（Asia/Shanghai）：启动 gemini/ppct，80条，workers=2；结果目录 outputs/ppct/gemini。

- 2026-11-01 02:03:29（Asia/Shanghai）：继续GPT 8帧+字幕测试；对比GPT/Gemini文本请求，区分代理CONNECT握手与模型响应超时。保持现有验证任务，不重复调度。

- 2026-11-01 02:04:29（Asia/Shanghai）：继续接口测试：{"provider": "gemini", "mode": "text", "success": false, "seconds": 60.01, "error": "HTTPSConnectionPool(host='api2.mcben.top', port=443): Read timed out. (read timeout=60)"}

- 2026-11-01 02:04:29（Asia/Shanghai）：继续接口测试：{"provider": "gpt", "mode": "8frames_subtitle", "success": false, "seconds": 60.01, "error": "HTTPSConnectionPool(host='api2.mcben.top', port=443): Read timed out. (read timeout=60)"}

- 2026-11-01 02:07:19（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:11:34（Asia/Shanghai）：按用户授权整理隧道：删除本机SSH配置中项目自动18097转发段，停止旧keep_forward监督及子进程，保留VSCode和其他SSH会话。remote.ps1增加NoUserConfig/ReverseForward可选参数，已有行为兼容且保留ppct-backup。新监督器仅18101到7897、进程互斥、保活和30秒重连，日志本机logs/forward18101*。旧18099占用归属无法确认，未强杀。开始新隧道验证。

- 2026-11-01 02:12:10（Asia/Shanghai）：新18101隧道HTTPS连通通过，GPT/Gemini配置切换18101；停止旧配置本项目任务，保留所有成功样本和阶段缓存。进行连续链路和真实多模态核验。

- 2026-11-01 02:12:20（Asia/Shanghai）：专用隧道多模态实测：{"provider": "gemini", "success": true, "seconds": 9.78, "content": "- **Visible fact:** A woman with brown bangs and a ponytail is wearing a high-collared black short-sleeved top (cheongsam style).\n- **Audible fact:** A female voice speaks out in Mandarin Chinese, beginning with an exclamation.", "response_model": "gemini-3.8-flash-n", "frames": 8, "audio": true}

- 2026-11-01 02:12:20（Asia/Shanghai）：专用隧道多模态实测：{"provider": "gpt", "success": true, "seconds": 10.22, "content": "A woman wearing a black top is standing indoors, with Chinese subtitles visible at the bottom.", "response_model": "gpt-6-sol", "frames": 8, "audio": false}

- 2026-11-01 02:12:46（Asia/Shanghai）：调度 gpt_ppct_smoke，PID=3272832，日志 logs/gpt_ppct_smoke_attempt1.log。

- 2026-11-01 02:12:46（Asia/Shanghai）：调度 gemini_ppct_smoke，PID=3272833，日志 logs/gemini_ppct_smoke_attempt1.log。

- 2026-11-01 02:12:46（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 02:12:46（Asia/Shanghai）：后台进度：运行任务 gpt_ppct_smoke, gemini_ppct_smoke；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:12:46（Asia/Shanghai）：启动 gemini/ppct，2条，workers=1；结果目录 outputs/ppct/gemini。

- 2026-11-01 02:12:46（Asia/Shanghai）：gemini/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gemini/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 02:12:46（Asia/Shanghai）：启动 gpt/ppct，2条，workers=1；结果目录 outputs/ppct/gpt。

- 2026-11-01 02:12:46（Asia/Shanghai）：gpt/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/gpt/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 02:13:01（Asia/Shanghai）：调度 gpt_ppct，PID=3273540，日志 logs/gpt_ppct_attempt1.log。

- 2026-11-01 02:13:01（Asia/Shanghai）：调度 gemini_ppct，PID=3273541，日志 logs/gemini_ppct_attempt1.log。

- 2026-11-01 02:13:01（Asia/Shanghai）：启动 gemini/ppct，80条，workers=2；结果目录 outputs/ppct/gemini。

- 2026-11-01 02:13:01（Asia/Shanghai）：启动 gpt/ppct，80条，workers=2；结果目录 outputs/ppct/gpt。

- 2026-11-01 02:13:28（Asia/Shanghai）：隧道整理完成：本机单实例监督PID69196，新18101。连续3次HTTPS检查通过（未认证接口401，6.12/10.82/8.40秒）；GPT8帧+字幕实测成功10.22秒，Gemini8帧+音频+字幕成功9.78秒，记录configs/stable_tunnel_*.json。调度器已重启PID3272640，复用成功缓存续跑；每小时自动化已同步新代理。此为短时核验，不保证网络今后无中断。用户无需再手工建18099隧道，可Ctrl+C停止旧重连循环。

- 2026-11-01 02:17:46（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:22:46（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:24:31（Asia/Shanghai）：每小时检查开始：下载实际3612/3791范围，日志汇总卡在288但进程仍活跃；四卡现有高显存任务，禁止抢占。检查API唯一结果/最近错误并实现Omni专用容错和阶段格式审计。

- 2026-11-01 02:27:46（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 288/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:28:16（Asia/Shanghai）：权重下载进程已退出且未生成验证标记；Omni队列暂停，需检查下载错误。

- 2026-11-01 02:28:36（Asia/Shanghai）：已部署Omni专用omni_tolerance.py：格式/字段归一、移除无效或重复边并保存修复记录，要求真实非空节点和可对应节点的组织文本；GPT/Gemini结构规则不放宽。必要离线检查通过。engine.py增加45秒连接等待及网络错误30/60秒退避，活跃进程不受文件替换影响，新恢复进程生效。部署audit_outputs.py逐条核对80唯一ID、五步文件、图/组织、标签/answer格式、8帧及请求无真实标签键。下载器改为8线程、单分段错误不再中断进度收集，守护器将等待现有健康传输退出后顺序恢复失败分段，禁止并发重复下载。

- 2026-11-01 02:29:07（Asia/Shanghai）：原下载已退出未校验；顺序恢复第1次，8线程复用已完成分段，worker PID=3294265。

- 2026-11-01 02:29:36（Asia/Shanghai）：Omni组织文本允许直接返回非JSON正文，再做非空和节点可追溯检查，仍保存原文与归一记录。已释放本项目旧18101 SSH会话，部署tunnel_session.py记录sshd PID及进程启动标记；本机监督器40444在重连前只清理匹配标记的项目会话，防止旧监听占用。最新18101 HTTPS约0.64秒连通。原32线程下载在3756/3791分段后因历史DNS失败退出，download_guard PID3293243接管且将以8线程只补缺失35段，已完成数据保留。四卡被他人emo-opsd及vLLM占用，等待空闲，不抢占。

- 2026-11-01 02:30:45（Asia/Shanghai）：全部3791分段已收齐，worker3294265正在SHA校验。旧调度器曾在守护接管前记录下载失败；已修复调度器支持接管现有GPT/Gemini进程并重置已恢复的本地队列状态，仅重启调度器、不停止健康API调用。全部四组完成时必须调用全量审计通过后才能标完成。GPU占用仍等待。

- 2026-11-01 02:30:46（Asia/Shanghai）：接管现有健康任务gpt_ppct PID=3273540，不重复启动API调用。

- 2026-11-01 02:30:46（Asia/Shanghai）：接管现有健康任务gemini_ppct PID=3273541，不重复启动API调用。

- 2026-11-01 02:30:46（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 02:30:46（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 3791/3791；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:31:15（Asia/Shanghai）：本轮检查交接：所有3791/3791下载分段已收齐，SHA校验进行中，尚不能标下载验证完成；审计有效数{"direct/omni": 0, "ppct/omni": 0, "ppct/gpt": 10, "ppct/gemini": 10}（每组80）。调度器PID3296820已接管原GPT3273540/Gemini3273541，无重复API进程；下载守护3293243、worker见logs/download_worker.pid；隧道监督40444，服务端会话标记logs/tunnel_session.json。Omni直接/PPCT尚未启动，因四卡被其他emo-opsd/vLLM作业占用，自动等待空闲。下一轮优先核查SHA结果和GPU、持续API恢复及全量审计；每小时自动化保持ACTIVE。

- 2026-11-01 02:35:07（Asia/Shanghai）：官方Thinking权重分片SHA及文件大小校验完成，下载已验证。

- 2026-11-01 02:35:46（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:40:48（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:45:50（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:46:25（Asia/Shanghai）：gemini/ppct 本轮结束：46/80有效；错误34；统计 outputs/ppct/gemini/summary.json。未成功项可按阶段恢复。

- 2026-11-01 02:46:35（Asia/Shanghai）：调度 gemini_ppct，PID=3315944，日志 logs/gemini_ppct_attempt2.log。

- 2026-11-01 02:46:36（Asia/Shanghai）：启动 gemini/ppct，80条，workers=2；结果目录 outputs/ppct/gemini。

- 2026-11-01 02:50:52（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 02:55:54（Asia/Shanghai）：后台进度：运行任务 gpt_ppct, gemini_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:00:34（Asia/Shanghai）：gemini/ppct 本轮结束：79/80有效；错误1；统计 outputs/ppct/gemini/summary.json。未成功项可按阶段恢复。

- 2026-11-01 03:00:55（Asia/Shanghai）：后台进度：运行任务 gpt_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:05:57（Asia/Shanghai）：后台进度：运行任务 gpt_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:09:30（Asia/Shanghai）：gpt/ppct 本轮结束：55/80有效；错误25；统计 outputs/ppct/gpt/summary.json。未成功项可按阶段恢复。

- 2026-11-01 03:09:43（Asia/Shanghai）：调度 gpt_ppct，PID=3342980，日志 logs/gpt_ppct_attempt2.log。

- 2026-11-01 03:09:44（Asia/Shanghai）：启动 gpt/ppct，80条，workers=2；结果目录 outputs/ppct/gpt。

- 2026-11-01 03:10:59（Asia/Shanghai）：后台进度：运行任务 gpt_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:16:01（Asia/Shanghai）：后台进度：运行任务 gpt_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:18:52（Asia/Shanghai）：gpt/ppct 本轮结束：80/80有效；错误0；统计 outputs/ppct/gpt/summary.json。未成功项可按阶段恢复。

- 2026-11-01 03:21:03（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:23:13（Asia/Shanghai）：本轮开始：官方Thinking权重已verified，GPT80/80审计通过ACC62/80=77.5%，Gemini79/80。最后MELD/dia9_utt11因同time_index的person节点被连after边而结构校验失败。修复engine.stage：重试时向同模型反馈结构错误与上一响应，要求按原节点修正/省略无支持边，保存每次请求；不含gold、不按分类正确性优化。已成功缓存不重跑。四卡仍被其他任务占用，Omni自动等待。

- 2026-11-01 03:23:14（Asia/Shanghai）：启动 gemini/ppct，80条，workers=1；结果目录 outputs/ppct/gemini。

- 2026-11-01 03:23:33（Asia/Shanghai）：调度器将接管Gemini结构恢复进程3359500，GPT已完成不重跑；不重复启动任何下载或API任务。

- 2026-11-01 03:23:33（Asia/Shanghai）：调度 gemini_ppct_smoke，PID=3360456，日志 logs/gemini_ppct_smoke_attempt1.log。

- 2026-11-01 03:23:33（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 03:23:33（Asia/Shanghai）：后台进度：运行任务 gemini_ppct_smoke；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:24:01（Asia/Shanghai）：gemini/ppct 本轮结束：80/80有效；错误0；统计 outputs/ppct/gemini/summary.json。未成功项可按阶段恢复。

- 2026-11-01 03:24:07（Asia/Shanghai）：修复调度器接管时仅识别绝对engine.py路径的问题：同时核验engine.py命令及/proc/PID/cwd为本项目，可接管相对路径运行。一次误启动的smoke被runner锁阻止，未产生重复API调用；原Gemini恢复进程3359500继续。

- 2026-11-01 03:24:07（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 03:24:08（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:25:24（Asia/Shanghai）：本轮核验完成：官方Thinking 26文件总63447489451字节、16分片SHA均与固定HF清单一致。GPT与Gemini均80/80通过逐条五步/格式/8帧/模态/请求无gold键审计（包括结构重试请求）。Gemini最后一条仅通过模型结构反馈修正非法同阶段after边，保留原响应和重试请求。已生成metrics/api_validation_report.json及.md、full_stage_format_audit.json、model_download_verification.json，比较表已刷新。GPU仍占用，Omni两组未开始，调度器3361740继续等待空闲。每小时自动化继续ACTIVE，不将整体任务标完成。

- 2026-11-01 03:29:09（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:34:11（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:39:13（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:44:15（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:49:17（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:54:18（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 03:59:20（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:04:22（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:09:24（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:14:26（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:19:28（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:19:32（Asia/Shanghai）：04时定时核查：Thinking权重仍verified；GPT/Gemini各80条任务已完成，本轮再次运行逐条流程/格式审计。调度器3361740健康且无错误；Omni两组0/80，当前GPU0-2各约21GiB且100%利用率，GPU3被其他vLLM约22GiB占用，不能安全部署四卡模型。未停止或抢占他人任务，保留现有等待调度和每小时自动化；资源释放后由调度器自动启动服务及两组验证。未重跑已完成API，未产生额外付费探测。

- 2026-11-01 04:24:29（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:29:31（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:34:33（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:39:35（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:44:36（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:49:38（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:54:40（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 04:59:42（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:04:43（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:09:45（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:14:47（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:19:49（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:24:50（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:28:27（Asia/Shanghai）：05时定时核查：下载校验已完成，GPT/Gemini80条完成审计记录完整，无新增API调用。调度器3361740健康运行且errors为空；四卡显存分别约22241/21385/21405/22595MiB，仍由其他作业占用，GPU3约89%利用率。Omni直接基线0/80、PPCT0/80，仅等待资源；不停止他人任务，不重复启动服务，维持自动接续和小时检查。

- 2026-11-01 05:29:52（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:34:54（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:39:56（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:44:58（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:49:59（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 05:55:01（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:00:03（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:05:05（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:10:07（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:15:08（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:20:10（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:25:12（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:28:25（Asia/Shanghai）：06时定时核查：权重已verified，GPT/Gemini各80条已审计完成、无需重跑。调度器3361740运行正常且errors为空。四卡显存22361/21405/21445/22595MiB仍被既有作业占用（GPU1/2利用率100%），资源不足以启动四卡Thinking。Omni直接及PPCT均0/80；保持自动等待，不抢占他人进程，不新增API调用。下一轮继续查GPU释放和服务状态。

- 2026-11-01 06:30:14（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:35:16（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:40:17（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:45:19（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:50:21（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 06:55:23（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:00:24（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:05:26（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:10:28（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:15:30（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:20:32（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:24:22（Asia/Shanghai）：07时定时核查：调度器3361740健康且无错误，官方权重verified，GPT/Gemini各80条完成审计记录有效，未重复调用API。GPU显存22141/21345/21425/22595MiB，其他作业仍占用四卡（GPU3利用率87%）；Omni直接及PPCT仍0/80。保持自动等待和资源释放后接续，不抢占其他作业，自动化继续ACTIVE。

- 2026-11-01 07:25:34（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:30:35（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:35:37（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:40:39（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:45:41（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:50:43（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 07:55:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:00:46（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:05:48（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:10:50（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:15:52（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:20:53（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:25:55（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:28:26（Asia/Shanghai）：08时定时核查：四卡显存22121/21345/21885/22595MiB，GPU3利用率70%，既有其他作业未释放资源。调度器3361740健康无错误；权重已verified，Omni直接及PPCT0/80，继续等待不抢占。GPT/Gemini各80条完整审计记录和结果报告仍在，无重复付费调用。已核对调度进程存活，保持每小时自动化。

- 2026-11-01 08:30:57（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:35:59（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:41:00（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:46:02（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:51:04（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 08:56:06（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:01:07（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:06:09（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:11:11（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:16:13（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:21:15（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:26:16（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:29:54（Asia/Shanghai）：09时定时核查：权重verified，GPT/Gemini已各80条完成审计。四卡显存22121/21365/21485/22595MiB，其他作业仍占用全部显存（GPU3利用率80%），不足以部署四卡Thinking。调度器3361740存活且errors为空，Omni直接与PPCT各0/80；保留等待自动接续，不停止他人任务、不重复付费API请求，每小时自动化继续。

- 2026-11-01 09:31:18（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:36:20（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:41:22（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:46:24（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:51:25（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 09:56:27（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:01:29（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:06:31（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:11:33（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:16:34（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:21:36（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:26:38（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:31:40（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:34:04（Asia/Shanghai）：10时定时核查：四卡显存21839/21103/21803/22595MiB，GPU0-2仍在训练；调度器3361740健康且errors为空，Omni直接和PPCT仍0/80，权重verified。此前10:32只读查询占用任务：emo-opsd为20epoch、2863/21780步，近50-200步43.5-45.1秒/步，预计还需229-237小时（约11月10日深夜至11日上午，速度可变）；rollout服务可能不随训练退出。不得终止该任务或抢占GPU。GPT/Gemini已80/80审计完成，无新增付费调用。保持小时监控；现有调度器有48小时上限，若后续达到上限需确认无活跃服务/推理后恢复调度，复用已完成API结果。

- 2026-11-01 10:36:53（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:42:06（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:44:18（Asia/Shanghai）：按用户最新授权新增GPT和Gemini各80条直接推理基线；沿用同一验证集和8帧，GPT字幕、Gemini音频及字幕，无PPCT图谱/线索组织输入。部署独立run_direct_api.py及审计扩展，原Omni等待调度和已完成PPCT不受影响。

- 2026-11-01 10:44:18（Asia/Shanghai）：用户新增授权：GPT/Gemini分别80条直接基线，8帧及可用字幕，Gemini另含音频；每条单阶段输出解释与标签，不使用PPCT上下文，格式失败不模型修复，仅传输失败有限重试。

- 2026-11-01 10:44:18（Asia/Shanghai）：启动单阶段直接基线gpt，80条，PID=3871288，日志logs/direct_gpt_attempt1.log。

- 2026-11-01 10:44:18（Asia/Shanghai）：启动单阶段直接基线gemini，80条，PID=3871289，日志logs/direct_gemini_attempt1.log。

- 2026-11-01 10:44:19（Asia/Shanghai）：启动 gpt/direct，80条，workers=2；结果目录 outputs/direct/gpt。

- 2026-11-01 10:44:19（Asia/Shanghai）：启动 gemini/direct，80条，workers=2；结果目录 outputs/direct/gemini。

- 2026-11-01 10:45:39（Asia/Shanghai）：直接基线已启动并确认成功响应，当前唯一成功数{"gpt": 5, "gemini": 19}，每组目标80；runner PID3871096，GPT3871288、Gemini3871289，锁及进度logs/direct_api_status.json。用户要求一次输入输出，direct收到模型响应后不做模型结构修复；只对网络失败有限重试。报告入口metrics/direct_api_baseline_comparison.md及.json，原PPCT结果不改动。已将两组新增基线纳入现有每小时自动化，直到两组80条完成审计才算完成。

- 2026-11-01 10:47:08（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:49:55（Asia/Shanghai）：gemini/direct 本轮结束：80/80有效；错误0；统计 outputs/direct/gemini/summary.json。未成功项可按阶段恢复。

- 2026-11-01 10:52:10（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 10:57:12（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:02:13（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:03:54（Asia/Shanghai）：gpt/direct 本轮结束：80/80有效；错误0；统计 outputs/direct/gpt/summary.json。未成功项可按阶段恢复。

- 2026-11-01 11:04:03（Asia/Shanghai）：两API直接基线调度结束，完整审计通过；报告metrics/direct_api_baseline_comparison.md。

- 2026-11-01 11:07:15（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:07:17（Asia/Shanghai）：用户新授权迁至dashan部署vLLM供liang调用；dashan四张3090当前空闲。用户进一步明确：若dashan已有完整Instruct权重则直接改用Instruct，覆盖之前仅Thinking约束；需在配置和结果明确模型版本。正在检查现有权重与环境，尚未启动服务。

- 2026-11-01 11:11:43（Asia/Shanghai）：dashan找到完整Instruct：/media/4t_2/hhp/llm_related/models/Qwen3-Omni-30B-A3B-Instruct，15分片共70523299202字节。按用户新授权改为Instruct；liang Omni endpoint=http://10.102.138.2:18030/v1，served ID omni30b-instruct。调度器改为等待远端模型就绪，不再等待liang四卡；服务尚未就绪，不宣称部署成功。GPT/Gemini直接基线均80/80审计完成，ACC65%/75%，PPCT仍77.5%/67.5%。

- 2026-11-01 11:11:44（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 11:11:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:14:22（Asia/Shanghai）：dashan服务已以SSD环境启动PID3061743，当前加载中；liang远端调度PID3904430等待/models就绪，尚未确认音视频推理成功。部署信息configs/omni_deployment.json。小时自动化已同步Instruct、dashan路径和远程接续规则，避免误恢复旧Thinking部署。

- 2026-11-01 11:16:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:21:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:26:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:31:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:35:40（Asia/Shanghai）：11:35定时检查发现dashan首启失败：15/15权重已加载但采样器JIT找不到ninja。已修正服务项目PATH/CUDA_HOME，使用支持的VLLM_USE_FLASHINFER_SAMPLER=0切PyTorch采样器，并启用权重预取；未修改共享环境或权重，原失败日志已保留。已重新启动dashan服务，尚未就绪。liang远程调度3904430继续等待，Omni两组仍0/80。GPT/Gemini四组均80/80完成不重跑。

- 2026-11-01 11:36:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:38:47（Asia/Shanghai）：本轮交接：dashan重新加载进程3127964存活，首次启动缺ninja路径已修复并验证二进制可执行，当前权重预取/加载中，18030未监听，尚未实际推理成功。liang调度器3904430继续等待远端就绪，Omni直接及PPCT仍0/80；GPT/Gemini直接65%/75%、PPCT77.5%/67.5%均80/80审计通过。未重跑完成API、未修改共享环境、未停止他人作业。下次先查新服务日志/模型接口，按两条跨数据集实际音视频检查后接续全量。

- 2026-11-01 11:41:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:46:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:48:41（Asia/Shanghai）：11:47用户查部署：预取加载10分钟仅1/15，确认FUSE源盘瓶颈，SSD可用264GB。已停止仅本项目旧服务树，保留原模型文件；dashan后台migrate_dashan_model_ssd.py PID3156866复制至SSD，逐文件比较源与副本SHA后自动以SSD权重启动（logs/vllm_ssd.log，PID仍记录logs/vllm.pid）。尚未部署成功，Omni两组0/80；liang调度器3904430继续等待，不重跑其他四组。

- 2026-11-01 11:50:43（Asia/Shanghai）：用户截图旧worker仍占显存；核查引擎已退出但SIGTERM未终止线程池，18030未监听。已在dashan仅针对确认身份的项目旧worker3130535/3130536/3130537/3130544、旧API3127964及其资源跟踪进程强制清理，四卡均确认降至1MiB。SSD复制进程3156866保留，当前约807MB/70.53GB；复制校验后自动启动SSD服务。显存分配不等于部署成功，当前仍未就绪。

- 2026-11-01 11:51:37（Asia/Shanghai）：用户明确改回直接从磁盘读：已停止本项目SSD复制3156866（不再自动恢复），保留未用partial副本；dashan从原4t_2模型路径默认mmap加载，无prefetch，保留修复PATH/CUDA_HOME及原生采样器。服务PID3165304，新日志logs/vllm_disk.log，尚未就绪。liang远端调度继续等待并自动接续两组Omni测试。

- 2026-11-01 11:51:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 11:56:44（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:01:45（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:04:30（Asia/Shanghai）：dashan Instruct模型接口已从liang探测就绪；开始两条音视频直接推理检查，之后接续80直接基线与PPCT。

- 2026-11-01 12:04:30（Asia/Shanghai）：调度 omni_direct_smoke，PID=3968803，日志 logs/omni_direct_smoke_attempt1.log。

- 2026-11-01 12:04:30（Asia/Shanghai）：启动 omni/direct，2条，workers=1；结果目录 outputs/direct/omni。

- 2026-11-01 12:04:42（Asia/Shanghai）：omni/direct 本轮结束：0/2有效；错误2；统计 outputs/direct/omni/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 12:04:45（Asia/Shanghai）：实验调度结束，有实质故障待处理，见 orchestrator_status.json；未将不完整实验标记为完成。

- 2026-11-01 12:17:55（Asia/Shanghai）：12:14接口已从liang可达，但两条Omni音视频smoke失败，根因为dashan项目环境缺音频依赖（非音频文件损坏）。已在.venv_ssd补齐av/soundfile/librosa/soxr，CPU8图+音频完整预处理通过；在线复测确认旧服务缓存PlaceholderModule，已仅重启自己的服务，dashan新PID3243931。liang调度恢复等待重载、重做两条smoke；保持原磁盘加载及无prefetch，不重跑已完成API，Omni两组仍0/80。

- 2026-11-01 12:17:55（Asia/Shanghai）：启动持久实验调度器：先完成外部API两条试跑与全量；官方权重SHA校验完成且四卡空闲后启动vLLM，再完成Omni基线与PPCT。

- 2026-11-01 12:17:55（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:22:55（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:27:55（Asia/Shanghai）：后台进度：运行任务 等待权重/服务；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:28:40（Asia/Shanghai）：dashan Instruct模型接口已从liang探测就绪；开始两条音视频直接推理检查，之后接续80直接基线与PPCT。

- 2026-11-01 12:28:40（Asia/Shanghai）：调度 omni_direct_smoke，PID=3999023，日志 logs/omni_direct_smoke_attempt1.log。

- 2026-11-01 12:28:41（Asia/Shanghai）：启动 omni/direct，2条，workers=1；结果目录 outputs/direct/omni。

- 2026-11-01 12:28:58（Asia/Shanghai）：omni/direct 本轮结束：2/2有效；错误0；统计 outputs/direct/omni/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 12:29:10（Asia/Shanghai）：调度 omni_direct，PID=3999975，日志 logs/omni_direct_attempt1.log。

- 2026-11-01 12:29:11（Asia/Shanghai）：启动 omni/direct，80条，workers=1；结果目录 outputs/direct/omni。

- 2026-11-01 12:32:31（Asia/Shanghai）：12:32定时核验：dashan Instruct部署实际成功，服务PID3243931，liang两条跨MER/MELD的8帧+音频+字幕试跑均有效，证据configs/omni_media_verified.json；非仅/models可达。当前Omni直接基线已32/80有效、无失败，worker3999975；调度器3986079健康，将完成80直接基线后接续PPCT两条试跑及80条。已更新公开能力配置与部署状态，不重启健康服务、不重复其他四组。

- 2026-11-01 12:32:56（Asia/Shanghai）：后台进度：运行任务 omni_direct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:36:14（Asia/Shanghai）：omni/direct 本轮结束：80/80有效；错误0；统计 outputs/direct/omni/summary.json。未成功项可按阶段恢复。

- 2026-11-01 12:36:26（Asia/Shanghai）：调度 omni_ppct_smoke，PID=4009261，日志 logs/omni_ppct_smoke_attempt1.log。

- 2026-11-01 12:36:26（Asia/Shanghai）：启动 omni/ppct，2条，workers=1；结果目录 outputs/ppct/omni。

- 2026-11-01 12:37:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct_smoke；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:38:15（Asia/Shanghai）：omni/ppct 本轮结束：2/2有效；错误0；统计 outputs/ppct/omni/smoke_summary.json。未成功项可按阶段恢复。

- 2026-11-01 12:38:26（Asia/Shanghai）：调度 omni_ppct，PID=4012550，日志 logs/omni_ppct_attempt1.log。

- 2026-11-01 12:38:26（Asia/Shanghai）：启动 omni/ppct，80条，workers=1；结果目录 outputs/ppct/omni。

- 2026-11-01 12:42:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:47:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:52:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 12:57:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:02:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:07:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:12:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:17:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:22:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:27:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:31:10（Asia/Shanghai）：13:30定时核查：dashan服务3243931健康；Omni直接80/80审计通过，MER34/40=85%、MELD24/40=60%、合计58/80=72.5%。Omni PPCT已37/80审计有效，worker4012550健康、尚无失败，不重启不调参。部署summarize_all_methods.py生成统一11行对照及六组审计/用量/成功阶段耗时，未完成组不报告最终ACC。

- 2026-11-01 13:32:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:33:34（Asia/Shanghai）：本轮交接：六组全量流程审计中，Omni direct、GPT direct/PPCT、Gemini direct/PPCT均80/80通过；Omni PPCT最新38/80通过，剩余42条尚未完成，非42条失败。调度3986079、PPCT worker4012550、dashan服务3243931健康，不重启、不重复API。统一报告已生成 metrics/all_methods_validation_report.md 与 .json（原五模型4帧+六组新方法8帧；未完成组ACC为pending）。下一轮继续保留健康任务，结束后运行 .venv/bin/python summarize_all_methods.py 全量重审并汇总，六组全部通过后才暂停自动化。

- 2026-11-01 13:37:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:42:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:47:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:52:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 13:57:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:02:56（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:07:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:12:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:17:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:22:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:27:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:30（Asia/Shanghai）：小时核查开始：已有Omni PPCT进程4012550及调度3986079健康，日志成功54/80，dashan服务3243931持续HTTP200。保留健康任务，运行summarize_all_methods.py逐条重审和更新统一报告，不新增推理请求。

- 2026-11-01 14:31（Asia/Shanghai）：本轮交接：summarize_all_methods.py逐条核验，Omni PPCT54/80有效、余26条未完成；其他五组均80/80。已刷新统一报告及当前概览，无新增API请求或服务重启。调度错误字典为空，继续健康任务；自动化保持ACTIVE。

- 2026-11-01 14:32:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:37:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:42:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:47:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:52:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 14:57:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:02:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:07:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:12:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:17:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:22:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:27:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:32:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:37:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:39（Asia/Shanghai）：小时核查开始：Omni PPCT日志67/80成功，调度错误为空；保留现有任务，本轮只运行统一报告脚本逐条审计，不新增推理请求或重复已完成API。

- 2026-11-01 15:43（Asia/Shanghai）：诊断MELD/dia200_utt2三次感知均finish_reason=length，重复节点耗尽4096 token，旧解析误取内层对象。修复Omni专用截断容错：只恢复完整显式类型/内容节点、删除完全重复内容与不完整尾部；保留原响应和归档，不合成事实。部署engine.py/omni_tolerance.py，活动worker不重启；为该失败样本恢复可验证感知缓存，下轮仅恢复缺失阶段。

- 2026-11-01 15:45（Asia/Shanghai）：交接：六组重审中五组80/80，Omni PPCT66/80有效；13条未完成、1条失败待续跑。MELD/dia200_utt2原始三次响应均长度截断，已仅从第三次原响应提取17个完整去重节点，schema及逐字来源检查通过，未新增模型调用。原文件归档outputs/recovery_archive/omni_MELD_dia200_utt2_20261101_1543；修复记录perception_repairs_attempt3.json；没有伪造尾部/事实。引擎与Omni解析器编译通过；活动worker4012550保留，调度3986079在本轮结束后自动有限重试失败项，已成功样本不重跑。dashan服务3243931健康。每小时自动化继续，下一轮重点核验该条后续图谱与组织文本及全部80条审计。

- 2026-11-01 15:42:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:47:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:52:57（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 15:57:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:02:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:07:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:12:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:17:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:22:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:23:17（Asia/Shanghai）：omni/ppct 本轮结束：78/80有效；错误2；统计 outputs/ppct/omni/summary.json。未成功项可按阶段恢复。

- 2026-11-01 16:23:28（Asia/Shanghai）：调度 omni_ppct，PID=81312，日志 logs/omni_ppct_attempt2.log。

- 2026-11-01 16:23:28（Asia/Shanghai）：启动 omni/ppct，80条，workers=1；结果目录 outputs/ppct/omni。

- 2026-11-01 16:27:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:32:58（Asia/Shanghai）：后台进度：运行任务 omni_ppct；下载范围 ?/?；详见 orchestrator_status.json 和 metrics/validation_comparison.md。

- 2026-11-01 16:36:54（Asia/Shanghai）：omni/ppct 本轮结束：80/80有效；错误0；统计 outputs/ppct/omni/summary.json。未成功项可按阶段恢复。

- 2026-11-01 16:36:58（Asia/Shanghai）：80条验证集的Omni直接基线及三模型PPCT均有效完成；比较报告 metrics/validation_comparison.md。vLLM服务继续保留。

- 2026-11-01 16:42（Asia/Shanghai）：最终核验开始：调度器报告16:36完成，Omni PPCT第二轮仅恢复失败/缺失项后80/80有效。服务3243931仍健康保留；运行summarize_all_methods.py全量重新审计六组、更新最终对照，不重复模型调用。

- 2026-11-01 16:45（Asia/Shanghai）：最终交接：summarize_all_methods.py重新审计六组，均80/80有效、缺失/当前错误0；调度器16:36正常完成退出。统一报告补充调用用量、成功阶段耗时和Omni截断恢复策略，并发布到metrics/validation_comparison.md/.json（保留pre_final版本）。GPT/Gemini底层身份仅按服务返回名记录。成功响应数/用量不保证覆盖历史被覆盖的重试，耗时非端到端墙钟。两台服务器记录同步；保留dashan服务3243931，暂停小时自动化，无剩余本轮实验阶段。

- 2026-11-01（Asia/Shanghai）：图谱质量评估开始：比较现有三模型各80张图谱及组织文本，固定抽取每数据集清单第4/20/36条，共6段，核对8帧与字幕，不依据分类正确与否挑样本、不调提示词、不新增API调用。仅保存离线诊断报告。

- 2026-11-01T16:53:19.111804+08:00：图谱离线评估完成，metrics/graph_quality_review.md/.json。各80张结构统计+固定6段8帧/字幕抽查，实用选择倾向Gemini，其次GPT，当前Omni不优先。记录了目标人物漂移、背景噪声、时序稀疏、重复与组织文本推断等证据；音频未独立听审，非全量语义金标准，不以最终ACC代替图谱质量。无API调用、提示词/模型/图谱变更。

- 2026-11-01（Asia/Shanghai）：用户授权新实验：固定Gemini已有80张图谱，GPT/Gemini/Omni各自生成组织文本，分为组织文本/图谱、音频+字幕、8帧图片三路独立专家，再由同模型summary仅基于三路输出给最终推理和单标签。GPT音频路仅用字幕，共享图谱含音频派生线索须披露。新增独立脚本/提示词、冻结图谱副本和独立输出，不覆盖原六组、不重生成图谱、不依据验证标签调提示词。先两数据集各一条端到端检查，再全80条/模型并行后台执行，保留缓存与全部原响应，有限重试失败阶段。

- 2026-11-01 17:15:25（Asia/Shanghai）：gemini_graph_three_experts_v1启动gpt/smoke第1轮，PID142281，日志logs/gemini_graph_three_experts_v1_gpt_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 17:15:25（Asia/Shanghai）：gemini_graph_three_experts_v1启动gemini/smoke第1轮，PID142282，日志logs/gemini_graph_three_experts_v1_gemini_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 17:15:25（Asia/Shanghai）：gemini_graph_three_experts_v1启动omni/smoke第1轮，PID142283，日志logs/gemini_graph_three_experts_v1_omni_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 17:16:25（Asia/Shanghai）：gemini_graph_three_experts_v1启动gemini/full第1轮，PID143854，日志logs/gemini_graph_three_experts_v1_gemini_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01（Asia/Shanghai）：新实验已部署并持久启动controller142090；固定Gemini80张图谱已复制与SHA核验。三个provider分别先做MER/MELD各一条实际试跑，成功后自动全80条。提示词frozen_graph_expert_prompts.py；脚本frozen_graph_experts.py；协议FROZEN_GRAPH_EXPERTS.md。离线模态隔离、非法引用/标签、gold泄漏与缓存签名检查通过。日志logs/gemini_graph_three_experts_v1_controller.log；状态outputs/gemini_graph_three_experts_v1/controller_status.json；每阶段原响应与所有请求持久保存，跨重试编号不覆盖网络失败记录。当前尚不能宣称80条完成。

- 2026-11-01 17:16:55（Asia/Shanghai）：gemini_graph_three_experts_v1启动gpt/full第1轮，PID145102，日志logs/gemini_graph_three_experts_v1_gpt_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 17:16:55（Asia/Shanghai）：gemini_graph_three_experts_v1启动omni/full第1轮，PID145103，日志logs/gemini_graph_three_experts_v1_omni_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01T17:18:11.931705+08:00：新实验交接：三模型2/2跨数据集试跑均已通过逐条审计，三路隔离与summary仅专家输入符合协议，实际调用GPT/Gemini与dashan Omni成功。全80条各自后台运行中（PID见当前概览）；不重复旧六组，不生成新图谱。当前外部代理18101可用，vLLM服务保留。无需额外用户操作，后续只检查状态及最终审计报告。

- 2026-11-01 18:19:42（Asia/Shanghai）：gemini_graph_three_experts_v1启动omni/full第2轮，PID217403，日志logs/gemini_graph_three_experts_v1_omni_full_2.log；复用固定图谱与已成功阶段。

- 2026-11-01（Asia/Shanghai）：用户授权开启并发。当前dashan四卡各约6156MiB空闲，拟vLLM max-num-seqs=2、每卡KV=2GiB，TP4/原磁盘/16K上下文/8帧与真实音频不变。先停止本项目调度142090与Omni worker217403，保留成功样本、所有阶段缓存与原响应；服务重启并通过两条同时实际音视频请求后，Omni客户端2workers仅续跑未完成样本。此次不改提示词、情绪轮或分类规则。

- 2026-11-01 Asia/Shanghai: User explicitly requested4-way concurrency, superseding2. Omni client now defaults4 workers (PPCT_OMNI_WORKERS override), server max-num-seqs4 with KV2GiB/rank. Original graph/prompt/signature/cache semantics unchanged. Existing GPT/Gemini80/80 results must not rerun. Preparing persistent readiness -> four simultaneous8-frame+audio probes -> Omni-only resume. Model reload pending; not yet verified concurrency.

- 2026-11-01 18:36:25（Asia/Shanghai）：4路实际8帧+音频请求全部成功，客户端区间重叠，服务metrics最高Running=4.0。Omni客户端4workers，保留成功样本与阶段缓存；仅恢复未完成Omni，不调用GPT/Gemini。验证logs/concurrency4/verification.json。

- 2026-11-01 18:36:27（Asia/Shanghai）：Omni4workers续跑第1轮PID238457，日志logs/concurrency4/omni_resume_attempt1.log；成功缓存保留。

- 2026-11-01 18:40:31（Asia/Shanghai）：Omni4workers续跑第2轮PID243643，日志logs/concurrency4/omni_resume_attempt2.log；成功缓存保留。

- 2026-11-01 18:43:35（Asia/Shanghai）：4路并发续跑结束，逐条审计数量{'gpt': 80, 'gemini': 80, 'omni': 70}；未通过项保留失败原因，不宣称完成。

- 2026-11-01 Asia/Shanghai: User explicitly authorized one simple reflect on correct/wrong existing samples and revised prompts: all experts receive all available raw media/subtitles, only graph/organization expert additionally receives graph; summary receives raw media/subtitle + experts, no graph. Each expert and summary3-4 evidence rubrics. This supersedes validation-not-for-tuning restriction for this requested development iteration; selected80 are now explicitly reused development data, not held-out evidence. Do not put gold/sample-specific corrections into inference. Preserve v1, create versioned v2; inspect cases before drafting. No new full-run authorization inferred from prompt authoring.

- 2026-11-01T18:54:43+08:00：v2提示词/独立运行审计脚本/反思记录已落地；旧v1没有修改。构建器两处离线错误（末函数边界、Counter导入）均已修复后重新编译、自检、初始化与审计通过。待用户安排推理运行；尚无v2 API调用。

- 2026-11-01 Asia/Shanghai: User authorized running v2 GPT/Gemini first,80 each, MER/MELD40 each. No Omni calls. Preflight no v2 process; add controller provider selection, then smoke2/provider -> full80, finite retry missing stages only. Preserve graph snapshots/old results, do not change rubric based on outputs.

- 2026-11-01 18:57:22（Asia/Shanghai）：gemini_graph_shared_media_v2启动gpt/smoke第1轮，PID266734，日志logs/gemini_graph_shared_media_v2_gpt_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 18:57:22（Asia/Shanghai）：gemini_graph_shared_media_v2启动gemini/smoke第1轮，PID266735，日志logs/gemini_graph_shared_media_v2_gemini_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 18:59:07（Asia/Shanghai）：gemini_graph_shared_media_v2启动gemini/full第1轮，PID269240，日志logs/gemini_graph_shared_media_v2_gemini_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01T19:00:04+08:00：v2 API两组持久启动，controller266536（--providers gpt gemini），主日志logs/shared_media_v2_api_controller.log，状态outputs/gemini_graph_shared_media_v2/controller_status.json。每provider2workers，Gemini两条跨数据集端到端已完成并进入full80；GPT试跑进行中，部分reason未显式引用E编号按原协议有限格式重试，成功阶段缓存保留。逐条审计当前有效数{'gpt': 0, 'gemini': 2}；暂无最终ACC。仅GPT8帧+字幕、Gemini8帧+音轨+字幕；Omni未启动。每专家都接其provider可用原媒体，仅graph专家接图谱/组织文本；summary原媒体+专家输出，无原图谱。公开/私密配置沿用，不打印密钥。

- 2026-11-01 19:02:37（Asia/Shanghai）：gemini_graph_shared_media_v2启动gpt/full第1轮，PID273467，日志logs/gemini_graph_shared_media_v2_gpt_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 Asia/Shanghai: User explicitly relaxed evidence citation strictness. Keep prompts/media/labels fixed; make reason bracket syntax, E-ID list consistency, noncanonical frame/node citation nonblocking diagnostics. Retain nonempty reason/evidence and valid single label, actual modality/source and no-gold checks. Preserve raw outputs, reuse saved formerly rejected responses without new model calls where signature and substantive checks pass. Applying policy then restarting only own v2 API processes; successful stages retained.

- 2026-11-01 19:02:54（Asia/Shanghai）：gemini_graph_shared_media_v2启动gpt/smoke第1轮，PID274983，日志logs/gemini_graph_shared_media_v2_gpt_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 19:02:54（Asia/Shanghai）：gemini_graph_shared_media_v2启动gemini/smoke第1轮，PID274984，日志logs/gemini_graph_shared_media_v2_gemini_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 19:03:09（Asia/Shanghai）：gemini_graph_shared_media_v2启动gpt/full第1轮，PID275499，日志logs/gemini_graph_shared_media_v2_gpt_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 19:03:09（Asia/Shanghai）：gemini_graph_shared_media_v2启动gemini/full第1轮，PID275500，日志logs/gemini_graph_shared_media_v2_gemini_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01T19:03:41+08:00：引用宽松策略已应用并通过离线测试，旧v2本项目进程受控重启，现controller274792，日志logs/shared_media_v2_api_soft_citations.log，仅GPT/Gemini。离线恢复1个已有Gemini阶段，原文未改、无新API调用；其余成功阶段保留。当前逐条有效{'gpt': 2, 'gemini': 8}。缺失/格式不一致的E编号及定位只记录警告，未知引用不伪造修复；实际模态、非空推理/证据、单标签和gold隔离继续检查。详见outputs/gemini_graph_shared_media_v2/citation_policy.json及每阶段citation_diagnostics。后续有界续跑未完成项，Omni未启动。

- 2026-11-01 Asia/Shanghai: User authorized independent v3 with project-adapted MER6/MELD7 emotion wheels included in each expert and summary prompt. Experts output one open emotion plus one mapped dataset label; summary keeps reason plus one closed label, no open emotion. Every version must be separately created without overwriting old versions. New files/config/output only; v1/v2 inference processes and artifacts untouched. Preserve soft citation diagnostics and8-frame/full-available-media routing. No new v3 full inference requested yet.

- 2026-11-01T19:53:00+08:00：独立v3创建与离线验证完成；未覆盖v1/v2、未新增API任务。待运行时使用独立pipeline与新输出目录，不能误报模拟结果为真实效果。

- 2026-11-01T19:53:57+08:00：用户授权启动v3，沿用先运行GPT/Gemini两provider、各80条，Omni不启动。启动前无v3进程，源文件哈希通过。v2 Gemini80/80审计完成，MER31/40=77.5%、MELD25/40=62.5%、总56/80=70%；v2 GPT33/80仍健康，保留原进程。v3使用独立输出/锁/日志/快照，先跨集各1条smoke再全80；不覆盖旧版本。

- 2026-11-01 19:53:58（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动gpt/smoke第1轮，PID337466，日志logs/gemini_graph_emotion_wheel_v3_gpt_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 19:53:58（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动gemini/smoke第1轮，PID337467，日志logs/gemini_graph_emotion_wheel_v3_gemini_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-01T19:55:02+08:00：v3持久调度与两provider实际worker已核对，保持独立版本/缓存/原响应，完成后报告metrics/gemini_graph_emotion_wheel_v3_comparison.md；当前先smoke再自动80条。

- 2026-11-01 19:55:13（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动gemini/full第1轮，PID339512，日志logs/gemini_graph_emotion_wheel_v3_gemini_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 19:57:58（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动gpt/full第1轮，PID342580，日志logs/gemini_graph_emotion_wheel_v3_gpt_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-01 20:28:43（Asia/Shanghai）：gemini_graph_shared_media_v2调度结束，逐条审计完成数{'gpt': 80, 'gemini': 80, 'omni': 0}，全部完成=False；报告metrics/gemini_graph_shared_media_v2_comparison.md。服务保留。

- 2026-11-01 20:56:14（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动gpt/full第2轮，PID409087，日志logs/gemini_graph_emotion_wheel_v3_gpt_full_2.log；复用固定图谱与已成功阶段。

- 2026-11-01 21:11:42（Asia/Shanghai）：gemini_graph_emotion_wheel_v3调度结束，逐条审计完成数{'gpt': 66, 'gemini': 80, 'omni': 0}，全部完成=False；报告metrics/gemini_graph_emotion_wheel_v3_comparison.md。服务保留。

- 2026-11-02T00:00:15+08:00：按用户指令完成特定占卡服务切换，持久启动跨服务器实际模态验证；加载/验证未完成，保留所有版本与已有结果。

- 2026-11-02T00:03:40+08:00：用户查询进度时核验发现v3 GPT因上游用量冷却退出，按原已授权80条任务恢复剩余14条；没有重跑已完成API组或更换模型。

- 2026-11-02 00:03:40（Asia/Shanghai）：恢复v3 GPT未完成14条，限额感知顺序续跑，仅缺失阶段；已有66条/全部Gemini保留。恢复PID626300，状态logs/v3_gpt_cooldown_recovery/status.json。

- 2026-11-02T00:07:03+08:00：Omni两版本顺序任务已部署；通过进程/锁避免重复，健康加载及既有音视频验证保留。状态以各版本逐样本审计报告为准，尚无Omni v2/v3成绩。

- 2026-11-02 00:07:03（Asia/Shanghai）：用户授权Omni加载验证后依次运行v2、v3各80条。监督PID630918；logs/omni_v2_v3/status.json。4workers，独立版本/结果，GPT/Gemini不重跑。

- 2026-11-02 00:12:56（Asia/Shanghai）：dashan Omni重启后两条跨MER/MELD实际8帧+音频+字幕请求成功，服务已核验；证据logs/omni_restart_20261101_235917_verification/status.json。仅部署验证，不自动启动任何版本实验。

- 2026-11-02 00:13:03（Asia/Shanghai）：Omni v2启动控制器638946，先跨MER/MELD各1条检查再80条，日志logs/omni_v2_v3/v2_controller.log，保留成功缓存。

- 2026-11-02 00:13:04（Asia/Shanghai）：gemini_graph_shared_media_v2启动omni/smoke第1轮，PID639142，日志logs/gemini_graph_shared_media_v2_omni_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-02 00:16:01（Asia/Shanghai）：gemini_graph_shared_media_v2启动omni/full第1轮，PID643343，日志logs/gemini_graph_shared_media_v2_omni_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-02 00:22:55（Asia/Shanghai）：v3 GPT恢复结束，有效80/80，状态logs/v3_gpt_cooldown_recovery/status.json；报告metrics/gemini_graph_emotion_wheel_v3_comparison.md。

- 2026-11-02 01:05:54（Asia/Shanghai）：gemini_graph_shared_media_v2启动omni/full第2轮，PID712921，日志logs/gemini_graph_shared_media_v2_omni_full_2.log；复用固定图谱与已成功阶段。

- 2026-11-02 01:11:34（Asia/Shanghai）：gemini_graph_shared_media_v2调度结束，逐条审计完成数{'gpt': 80, 'gemini': 80, 'omni': 76}，全部完成=False；报告metrics/gemini_graph_shared_media_v2_comparison.md。服务保留。

- 2026-11-02 01:12:03（Asia/Shanghai）：Omni v2本轮结束，逐条有效76/80；仍有失败/缺失，原响应保留。

- 2026-11-02 01:12:03（Asia/Shanghai）：Omni v3启动控制器720163，先跨MER/MELD各1条检查再80条，日志logs/omni_v2_v3/v3_controller.log，保留成功缓存。

- 2026-11-02 01:12:04（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动omni/smoke第1轮，PID720358，日志logs/gemini_graph_emotion_wheel_v3_omni_smoke_1.log；复用固定图谱与已成功阶段。

- 2026-11-02 01:15:04（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动omni/full第1轮，PID724217，日志logs/gemini_graph_emotion_wheel_v3_omni_full_1.log；复用固定图谱与已成功阶段。

- 2026-11-02 02:13:37（Asia/Shanghai）：gemini_graph_emotion_wheel_v3启动omni/full第2轮，PID791676，日志logs/gemini_graph_emotion_wheel_v3_omni_full_2.log；复用固定图谱与已成功阶段。

- 2026-11-02 02:17:43（Asia/Shanghai）：gemini_graph_emotion_wheel_v3调度结束，逐条审计完成数{'gpt': 80, 'gemini': 80, 'omni': 77}，全部完成=False；报告metrics/gemini_graph_emotion_wheel_v3_comparison.md。服务保留。

- 2026-11-02 02:18:03（Asia/Shanghai）：Omni v3本轮结束，逐条有效77/80；仍有失败/缺失，原响应保留。

- 2026-11-02 02:18:03（Asia/Shanghai）：Omni v2/v3顺序任务结束：{'v2': 76, 'v3': 77}；完整=False。服务保留。
