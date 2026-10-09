# YoloongPPT

AI PPT 生成系统项目。当前已有Docker产品核心：TaskSpec校验、Schema/CapabilityRegistry、文本/Markdown来源解析与证据存储，以及CLI/API入口。生成、渲染、QA和局部修订的完整链路仍待实现，不能把核心启动作为AI PPT交付。

完整交付目标与防偏离规则见 [GOAL.md](GOAL.md)，执行计划见 [PROJECT_PLAN.md](PROJECT_PLAN.md)，17 小时进度审计见 [PROGRESS_AUDIT.md](PROGRESS_AUDIT.md)。

## 需求基线

- AI_PPT_PDR_完整需求定义_V0.3.docx：需求和规则说明。
- AI_PPT_完整需求与任务矩阵_V0.3.xlsx：Requirement ID、可执行任务、全链路、后端能力和验收矩阵。

基线覆盖 308 条主需求、453 个可执行任务、45 个端到端步骤、40 个决策节点、30 类 PowerPoint 原生对象能力、9 条 PowerPoint 后端路线和 30 个验收场景。实施任务应引用原始需求 ID。

## Docker 隔离开发环境

需要 Docker Desktop 和 Docker Compose。workspace提供通用编辑工作区；app使用已选Python 3.13.16核心，运行依赖只安装在镜像内。选型依据、版本与未验证能力见[ARCHITECTURE.md](ARCHITECTURE.md)，不从主机工具版本推导。

Windows PowerShell 管理命令：

1. 启动：pwsh -NoProfile -File .\scripts\project.ps1 start
2. 进入应用容器：pwsh -NoProfile -File .\scripts\project.ps1 shell（通用工作区使用 -Service workspace）
3. 查看状态：pwsh -NoProfile -File .\scripts\project.ps1 status
4. 查看日志：pwsh -NoProfile -File .\scripts\project.ps1 logs
5. 停止：pwsh -NoProfile -File .\scripts\project.ps1 stop

启动脚本先核验Docker数据盘在非C盘，再管理本项目两个服务；HTTP仅绑定127.0.0.1:8000，临时/运行产物位于F盘runtime/data。`/health`返回core_ready，同时明确generation_ready=false。

已实现命令与API：

```powershell
docker --context desktop-linux compose exec -T app python -m yoloongppt validate validation/core-task.json
docker --context desktop-linux compose exec -T app python -m yoloongppt capabilities
docker --context desktop-linux compose exec -T app python -m yoloongppt schemas
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/capabilities
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/validate -ContentType 'application/json; charset=utf-8' -Body ([System.IO.File]::ReadAllBytes('F:/YoloongPPT/validation/core-task.json'))
```

TaskSpec例子只校验已给出的路由与输入形状，未执行DEC-001或生成。失败返回结构化错误/trace，不回显输入值；能力目录保留30×9未验证状态，组件health不替代PPT对象支持。实际Docker组件核验见[validation/runtime-core.json](validation/runtime-core.json)。

## 来源解析与证据

`python -m yoloongppt inspect <TaskSpec.json>`或HTTP POST `/inspect`解析prompt/text/markdown来源，返回SourceBundle、结构化文档、原文证据ID与trace；`python -m yoloongppt evidence <evidence_id>`或GET `/evidence/{id}`查询同一持久证据。SQLite与原文快照位于F盘绑定的runtime/data，不进入Git。文件路径只接受工作区或运行目录内的UTF-8 .md/.markdown/.txt，其他输入明确报错。

Markdown保留标题、列表、代码、表格、链接、引用与脚注结构；表格行宽不一致、重复脚注、未映射结构停止解析，原文未截断。块锚点精确回到原文，行内位置仅表示所属块范围。自然语言意图提取、优先级/事实冲突检测和其他格式仍未实现。实际输入/解析样例见[source-runtime-example.json](validation/source-runtime-example.json)，验证见[source-runtime.json](validation/source-runtime.json)。

## Git 工作约定

默认开发分支为 yoloongdevlop，远端为 origin。每个项目变更都要在 ailog/ 和 development-log/ 各创建一份同名中文摘要日志，再提交到该分支并推送到 origin/yoloongdevlop。具体约定见 AGENTS.md。
