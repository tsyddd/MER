---
name: project-update
description: Maintain update.md when an AI modifies files or runs downloads, deployment, data preparation, or experiments in PPCT_emotion_training_free. Use at task start, material progress, and handoff.
---

# 项目进度与交接记录

项目根目录是本文件向上四级所在目录。工作前阅读根目录 `AGENTS.md` 与 `update.md`，再读取本次任务需要的文件。

维护 `update.md` 的当前概览、已完成、进行中、待办、限制和按时间排列的工作记录；时间统一使用 Asia/Shanghai。保留既有记录，以追加方式记录变更，同时更新概览中的过期状态。其他 AI 已写的新进度不覆盖。

- 开始工作：写明本次目标和正在处理的事项。
- 文件修改、下载/服务/实验启动、结果核验或失败后：及时记录变更文件、运行命令或配置入口、PID、日志路径、结果和下一步。不能只在最终回复中记录。
- 结束、暂停或交接前：写清完成项与尚未完成项、最新可靠数量、错误原因、恢复命令及需要用户输入的事项。运行中不能标成已完成。
- 数值和完成状态以实际日志、文件校验、服务探测和结果统计为依据。预测正确不代表推理已人工核验；文本API通过不代表图像/音频通过；权重开始下载不代表部署成功。
- 不写 API 密钥、Authorization 值或凭证；只记录受限配置文件路径。必要错误信息先脱敏。
- 如无法写入，明确报告原因和未记录内容，不宣称已更新。

保持记录简洁但可恢复工作；详细逐样本日志留在相应输出目录，在 `update.md` 链接它们。遵守项目原有授权范围，本技能不授权额外的外部调用或实验。
