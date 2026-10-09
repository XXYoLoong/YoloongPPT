# YoloongPPT

AI PPT 生成系统项目。Docker内已有任务校验、文本/Markdown解析、证据存储、真实模型规划、原生PPTX写入、PDF/PNG渲染、结构及模型视觉/事实检查和单个文本对象修订，均通过CLI/API共享核心。完整DEC链、全部QA与修订范围和系统验收仍待完成。

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

Markdown保留标题、列表、代码、表格、链接、引用与脚注结构；表格行宽不一致、重复脚注、未映射结构停止解析，原文未截断。块锚点精确回到原文，行内位置仅表示所属块范围。来源解析不推导意图；DEC-001另行按显式模式、调用方原文及附件角色判定。优先级/事实冲突检测和其他格式仍未实现。实际输入/解析样例见[source-runtime-example.json](validation/source-runtime-example.json)，验证见[source-runtime.json](validation/source-runtime.json)。

## 真实生成与局部修订

先用 `./scripts/configure-model.ps1` 读取已授权的系统环境变量，再 `./scripts/project.ps1 start`。密钥只保存到忽略的F盘runtime/data/secrets，不通过Docker build、TaskSpec或日志传递。

在app容器中执行 `python -m yoloongppt generate /workspace/validation/generation-task.json`；HTTP为POST `/generate`，输入同一TaskSpec。返回的是draft_generated和实际产物目录，不表示AC验收通过。生成前实际经过DEC-001核对，保存原始请求/能力快照/候选/选择/冲突与保护策略；旧TaskSpec.route作为显式断言，未伪造原文。当前后续执行只支持材料/从零新建、中文16:9及已验证文本/表格/分类图表/备注；未知硬约束、模板、样式或运行选项明确拒绝。可用 `resume <run_id>` 复用已保存模型阶段，来源变化会拒绝复用。

`python -m yoloongppt revise <run_id> <request.json>`（HTTP POST `/revise/{run_id}`）目前只编辑一个标题/正文原生对象；请求字段为object_id、replacement_text数组和reason。保存原稿与修订稿，逐字节保留未选OOXML parts和实体ID，再渲染/复审。`recheck <run_id>` 或POST `/recheck/{run_id}`只恢复QA，校验并复用已有PPTX/render字节，不重新生成。

实物：[原稿](validation/generation-artifacts/original/deck.pptx)、[局部修订稿](validation/generation-artifacts/revised/deck.pptx)、[修订稿PDF](validation/generation-artifacts/revised/render/deck.pdf)、[当前HTTP真实生成](validation/generation-artifacts/http-generated/deck.pptx)。[31项组件核验](validation/generation-runtime.json)与[实物说明](validation/首条真实生成与修订链路.md)记录模型调用、真实视觉/事实审查、ObjectMap、失败及修订差异；P0为0只适用于这些已执行检查，AC-001/GOV-008仍未通过。

## Git 工作约定

默认开发分支为 yoloongdevlop，远端为 origin。每个项目变更都要在 ailog/ 和 development-log/ 各创建一份同名中文摘要日志，再提交到该分支并推送到 origin/yoloongdevlop。具体约定见 AGENTS.md。

## 可独立运行的模式路由与原子能力

app内 `python -m yoloongppt route /workspace/validation/route-request.json` 或 HTTP POST `/route` 输入相同JSON。raw_request.request保留原文、附件ID、显式模式、输出；attachment_roles明确内容/风格/模板/已有deck/还原来源，single_slide可指定动作及目标。八种模式独立保护策略，无法唯一判断则needs_clarification，未实现的后续模式标明executable=false，不替换为新建。

节点结果与完整DecisionTrace保存到F盘运行目录；`generate`也实际消费该节点。TaskSpec可附raw_request，声明路线与原文判定冲突时停止。能力快照只探测当前本地子集，外部模型/Office完整探测仍待SYS-002；节点入口可注入能力快照进行调试，其来源标为caller_provided，不能改变生成入口的实际探测。

`capabilities`的atomic_registry含五项已登记的原生写入能力及稳定实现ID；执行DAG由planner实际选择，writer在任何写入前核对所有调用的绑定和输入，再校验真实输出。其他对象/后端及导入保真未升级支持状态。

实物与复现：[模式路由与能力登记](validation/模式路由与能力登记.md)、[当前生成PPTX](validation/route-artifacts/deck.pptx)、[渲染PDF](validation/route-artifacts/render/deck.pdf)。39项节点/登记/真实链路核验、26项核心及31项生成修订回归通过；DEC-002–040及完整AC仍未通过。
