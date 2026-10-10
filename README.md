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

实物与复现：[模式路由与能力登记](validation/模式路由与能力登记.md)、[该次生成PPTX](validation/route-artifacts/deck.pptx)、[渲染PDF](validation/route-artifacts/render/deck.pdf)。39项模式节点/登记核验是前次版本证据；当前核心26项及生成修订31项回归通过，完整AC仍未通过。

## 约束归一化与来源分流

容器内 `python -m yoloongppt context /workspace/validation/context-generation-task.json` 或 POST `/context` 消费TaskSpec；`source-roles <input.json>` 或 POST `/source-roles` 消费包含task与已解析source_bundle的JSON。两节点可独立运行，并保存输入、候选、选择、规则、输出、时长和错误。

DEC-002按硬约束、偏好、调用方默认、系统默认的顺序选择，同级不同值阻断；原始请求中明确的页数、比例、语言、输出要求也参与处理。当前原文识别是有界规则，非任意自然语言理解。模板、品牌等值可归一化保留，但尚未支持的执行要求明确拒绝。输出要求不能静默忽略，偏好无法满足须保存原因。

DEC-003绑定真实source_id/asset_ref，保留事实、模板、风格、素材、已有deck及还原来源六种角色。来源解析仍限原有文本/Markdown范围；角色分类不等于模板/图片/其他格式解析已实现。生成、QA及后续修订/复查只消费事实集合，全部原材料另行保存；角色冲突和身份未绑定在模型调用前阻断。

[40项检查与说明](validation/约束归一化与来源分流.md)、[本次8页原生PPTX](validation/context-artifacts/deck.pptx)、[PDF](validation/context-artifacts/render/deck.pdf)记录真实DeepSeek调用和三节点轨迹。这是当时三节点版本的QA记录；当前新增事实决策见下文，全部QA/AC仍未完成。

## 当前页面编译与真实产物

SYS-010/012/013现在消费七类原生版式目录：开场、宽栏正文、双栏、文本面板、结尾、表格、图表。选择实际检查文字/表格容量、开场结尾位置及相邻变化，全部候选不适配时失败；不删文字、缩字号或用截图替换原生对象。稳定槽位维持恢复时对象ID，逐页填充、描边、边距及字号进入已登记能力调用。DEC-030/031/033/034仍为进行中，完整语义、品牌、素材、模板与多后端条件待实现。

多栏QA按实际PDF字词坐标核对每个对象，独立删除PDF词反例仍检出缺字；旧单栏产物保持既有检查兼容。[23项组件核验](validation/layout-runtime.json)、[本版10页PPTX](validation/layout-artifacts/deck.pptx)、[PDF](validation/layout-artifacts/render/deck.pdf)及[实施说明](validation/版式编译与链路进度修复.md)保留初次9个P0问题、修正后当前P0=0及真实复审。当前模型内容从真实初次调用断点复用，引用修正和复审是新增实际调用；完整AC仍未通过。

原Excel“0-1全链路”已按实物同步进行中状态与剩余条件，“总览”完成数缓存与主表核对；阶段运行不表示完整系统交付。

## 来源冲突与事实边界

生成已接通DEC-004/005，独立CLI为 `resolve-evidence <input.json>`、`fact-boundaries <input.json>`，HTTP为 `/resolve-evidence`、`/fact-boundaries`。TaskSpec可附evidence_policy明确source_precedence/conflict_selections/missing_rules；未知或无关规则字段被拒绝，不自动挑选冲突值。

真实模型事实解释逐字核对来源；未决/必需缺失停止主内容生成，已选值和原始上下文进入文案投影，完整来源/冲突留存。假设/精确推算需稳定assumption_refs和可见标记；占位、询问/失败有记录。修订/复查验证快照hash并沿用边界，被否决数值在修订写入前失败；resume支持事实解释阶段的实际断点。

[35项节点与16项实物检查说明](validation/来源冲突与事实边界.md)、[四页已选事实PPTX](validation/fact-artifacts/generated/deck.pptx)、[PDF](validation/fact-artifacts/generated/render/deck.pdf)、[单对象修订稿](validation/fact-artifacts/revised/deck.pptx)与初次失败证据保留。当前已执行P0=0；语义抽取完整性、DEC-006–040及完整AC尚未通过。
