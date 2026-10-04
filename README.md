# YoloongPPT

AI PPT 生成系统项目。当前仓库包含 V0.3 需求基线和隔离开发环境，尚未包含可启动的产品应用。

## 需求基线

- AI_PPT_PDR_完整需求定义_V0.3.docx：需求和规则说明。
- AI_PPT_完整需求与任务矩阵_V0.3.xlsx：Requirement ID、可执行任务、全链路、后端能力和验收矩阵。

基线覆盖 308 条主需求、453 个可执行任务、45 个端到端步骤、40 个决策节点、30 类 PowerPoint 原生对象能力、9 条 PowerPoint 后端路线和 30 个验收场景。实施任务应引用原始需求 ID。

## Docker 隔离开发环境

需要 Docker Desktop 和 Docker Compose。容器提供 Python 与 Node.js 开发运行时；源码目录挂载到容器供编辑，语言依赖保存在项目专属 Docker 卷中。

Windows PowerShell 管理命令：

1. 启动：pwsh -NoProfile -File .\scripts\project.ps1 start
2. 进入容器：pwsh -NoProfile -File .\scripts\project.ps1 shell
3. 查看状态：pwsh -NoProfile -File .\scripts\project.ps1 status
4. 查看日志：pwsh -NoProfile -File .\scripts\project.ps1 logs
5. 停止：pwsh -NoProfile -File .\scripts\project.ps1 stop

容器启动后会进入 /workspace。当前只有项目需求材料，因此该容器是隔离开发工作区，不是产品应用服务。应用入口、端口和生产启动命令应在架构确定及相应服务实现后补充。

## Git 工作约定

默认开发分支为 yoloongdevlop，远端为 origin。每个项目变更都要写入 ailog/，提交到该分支并推送到 origin/yoloongdevlop。具体约定见 AGENTS.md。
