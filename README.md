# YoloongPPT

AI PPT 生成系统项目。Docker 内已有多格式输入/证据、DEC-001–040 有界消费、真实模型规划、可编辑 PPTX、最多八图图文/原生流程/表格/图表、真实模板槽位与显式品牌锁、完整正文和大表格自适应分页、PDF/PNG 渲染、部分结构/视觉/事实检查、质量驱动局部几何/颜色修订及已有 PPT 定向编辑；CLI/API/MCP 共享核心，长任务有持久状态、取消、重试和显式恢复。全 308/453 与完整节点/对象/后端/系统 AC 验收仍未完成。

完整交付目标与防偏离规则见 [GOAL.md](GOAL.md)，执行计划见 [PROJECT_PLAN.md](PROJECT_PLAN.md)，17 小时进度审计见 [PROGRESS_AUDIT.md](PROGRESS_AUDIT.md)。

2026-10-12按用户要求阶段收尾：[当前实现与剩余报告](当前实现与阶段收尾报告_20261012.md)。单段描述实际生成六页24原生对象，再局部修订封面两个对象并复审，15项流程与8项原生实物检查通过，P0=0/2警告、final_allowed=false。[当前修订PPTX](validation/stage-closure-artifacts/description-revised/deck.pptx)、[PDF](validation/stage-closure-artifacts/description-revised/render/deck.pdf)可检查。自动QA未检出初稿操作指令外泄，人工查看后局部修复；完整内容适用性仍未验收。

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

上面的 validate 例子只校验已给出的路由与输入形状，不执行生成；generate/debug 实际消费对应节点。失败返回结构化错误/trace，不回显敏感输入值；能力目录分别记录 30×9 的 partial/unsupported/untested 范围，组件 health 不替代 PPT 对象支持。实际Docker组件核验见[validation/runtime-core.json](validation/runtime-core.json)。

## 来源解析与证据

`python -m yoloongppt inspect <TaskSpec.json>`或HTTP POST `/inspect`支持prompt/text/markdown、DOCX、XLSX/CSV、PPTX/POTX、文本PDF、图片、JSON/XML，返回结构与证据锚点；二进制使用工作区或/runtime中的locator，限制16MiB并拒绝敏感目录。原始字节/数据库只在F盘runtime/data。图片与空结构保留，未执行OCR，不作为文字事实。

Markdown保留原文结构；原生格式保留表格/对象/媒体关系及格式锚点。外部链接只登记，不自动执行下载；未知语义、OCR、单位/显示格式或模板容量明确报告。DEC-003分角色，DEC-004/005选择事实、冲突与缺失策略。格式边界与31项实物检查见[输入格式与原生模板实装](validation/输入格式与原生模板实装.md)。

## 真实生成与局部修订

先用 `./scripts/configure-model.ps1` 读取已授权的系统环境变量，再 `./scripts/project.ps1 start`。密钥只保存到忽略的F盘runtime/data/secrets，不通过Docker build、TaskSpec或日志传递。

在app容器中执行 `python -m yoloongppt generate /workspace/validation/generation-task.json`；HTTP为POST `/generate`，输入同一TaskSpec。返回的是draft_generated和实际产物目录，不表示AC验收通过。生成前实际经过DEC-001核对，保存原始请求/能力快照/候选/选择/冲突与保护策略；旧TaskSpec.route作为显式断言，未伪造原文。当前后续执行支持材料/从零新建、中文 16:9及文本/原生表格/分类图表/单图或最多八图图文/有来源节点与边的原生图示/备注。模型从已登记真实 asset_id 中选择图片，实际文件和 hash 由资产解析补入；不猜路径、关系或因果。所选模板需匹配尺寸和 hash，实际选择原生 layout 并填写 text/picture/table/chart placeholder，保留 master/layout/theme 和未知部件；槽位/容量/品牌锁不符时失败，fallback 仅按调用者显式策略。未知硬约束、样式、运行选项和未实现高级能力明确拒绝。可用 `resume <run_id>` 复用已保存模型阶段，来源变化会拒绝复用。

`python -m yoloongppt revise <run_id> <request.json>`（HTTP POST `/revise/{run_id}`）保留单标题/正文请求 object_id、replacement_text 数组和 reason；请求包含 `plan` 时消费 DEC-039 的 RevisionPlan，当前支持有明确范围的几何/颜色修复。写入前核对 parent run、before spec、对象/页面范围和锁，非法/过期/事实修改请求拒绝。保存原稿、before/after、实际差异与局部复审，逐字节保留未选 OOXML parts 和实体 ID；完整内容/对象/模板重排仍按原验收推进。`recheck <run_id>` 或POST `/recheck/{run_id}`只恢复QA，校验并复用已有PPTX/render字节，不重新生成。

同一 `revise` 入口也消费 [批量请求契约](contracts/revision-batch-request.schema.json)：`instruction` 配合可选 `scope.slide_ids/object_ids`、`locked_object_ids` 和 `edits`。明确 edits 使用逻辑 object_id 或唯一 selector（slide_id/index、shape_id/name/text/placeholder_idx）；没有 edits 时，真实模型依据登记对象与已选事实解释指令，保存目标候选和原文依据，歧义或越界失败。CLI、API、MCP `revise_deck` 与既有作业路由共享消费者。

批次支持文字、登记且已授权图片、分类图表数据、表格单元格、几何、文本 color/bold/font_size、图片/形状替代文字及备注。`mode: "beautify"` 只允许几何/格式，保留事实、数据与锁。图片当前要求 contain，无旧裁切，并在原对象范围内按真实比例适配；共享媒体/图表工作簿/备注可能影响未选对象时明确拒绝。连接线端点重排、任意 section 语义、全部格式/模板/复杂对象尚未接入，不把低层原生编辑支持当成全系统支持。每次保存父子 run、版本/hash、逐操作准备状态和最终 before/after、原生差异、实际渲染及选页独立模型复审；未选页的原 issue 保留。

复现与当前实物见 [批量局部修订与原生保真](validation/批量局部修订与原生保真.md)。五次实际 API 修订分别覆盖两页文案、图表系列重排、换图、故障注入美化及再次换图，P0=0，仍有警告且 final_allowed=false；AC-008/009/010/028 均未通过完整原验收。

实物：[原稿](validation/generation-artifacts/original/deck.pptx)、[局部修订稿](validation/generation-artifacts/revised/deck.pptx)、[修订稿PDF](validation/generation-artifacts/revised/render/deck.pdf)、[当前HTTP真实生成](validation/generation-artifacts/http-generated/deck.pptx)。[31项组件核验](validation/generation-runtime.json)与[实物说明](validation/首条真实生成与修订链路.md)记录模型调用、真实视觉/事实审查、ObjectMap、失败及修订差异；P0为0只适用于这些已执行检查，AC-001/GOV-008仍未通过。

## 原生模板、八图与完整内容分页（2026-10-11）

本轮对照 AC-006/012/014/015、TPL-002/003/004/006/008/015/016、AST-007 与 DEC-014–021 接入以下运行行为；原完整验收仍未通过。

- 模板：字段按实际 idx/name 映射到现有原生槽位，测量实际字体文件与行高；明确锁定 logo/页脚/安全区/颜色字体 token，保持原母版、布局、主题及未知 OOXML 部件。缺字体、容量不足和未经授权 fallback 均拒绝。
- 图文：保留指定的全部 1–8 张真实图片、来源/许可/hash、题注与引用；不同比例图片使用 contain、明确焦点 cover 或显式 crop，原生图片保持可编辑。人脸/对象感知裁切及完整素材服务仍待验收。
- 正文/大表格：保留完整可见正文、原标题和全部单元格；按容量生成可追溯续页，横向拆表要求调用者明确重复关键列。硬页数不够时失败，软/default 预算才允许在明确范围内增页；不截字、不删格、不把核心正文藏到备注或缩成不可读字号。

| 已执行的限定验证 | 分版本证据 |
| --- | --- |
| 模板 68 项组件/正式编译写入检查，另 2 项增量输入边界 | [原生模板与品牌锁](validation/模板原生槽位与品牌锁.md) |
| 图文 32 项，另 5 项长标题增量检查 | [图库报告](validation/gallery-artifacts/b81e5a47-0d59-4963-87a5-daa257d654ef/gallery-runtime.json)、[长标题报告](validation/gallery-artifacts/long-title-ae033e62/gallery-long-title-runtime.json) |
| 自适应 161 项，另 228 项同一已保存 PDF 的单元格核对 | [完整正文与大表格](validation/完整正文和大表格自适应分页.md) |

这些数字属于各自版本的人工夹具组件与实物检查，未合并成一次全套重跑。真实 API 新调用已生成四页；修复资源ID误判、混合标题语言识别和可见分页说明后，恢复逐字复用真实内容，重新渲染及模型审查，9项集成检查通过，P0=0、5警告保留、final_allowed=false。另有15项上下文/断点和10项分页说明增量检查。[当前PPTX](validation/native-capacity-live-artifacts/current-resumed/deck.pptx)、[PDF](validation/native-capacity-live-artifacts/current-resumed/render/deck.pdf)、[版本与失败证据](validation/native-capacity-integration.json)。自定义模板多图原生槽位尚不支持；模板 cover 仅 focal、没有已解析 crop 时明确拒绝；三上游模板兼容、锁定模板自适应、完整语义拆合、所有 QA/修订/对象/后端及原 AC 仍需完成。

## Git 工作约定

默认开发分支为 yoloongdevlop，远端为 origin。每个项目变更都要在 ailog/ 和 development-log/ 各创建一份同名中文摘要日志，再提交到该分支并推送到 origin/yoloongdevlop。具体约定见 AGENTS.md。

## 并行实装的入口与产物

`POST /create` 返回202及job_id；`GET /jobs/{job_id}` 查询，`POST /jobs/{job_id}/cancel`取消，`POST /jobs/{job_id}/retry`显式重试。`GET /artifacts/{run_id}`核对并列出产物路径。`POST /jobs`可提交generate/revise/resume/recheck/inspect/validate；恢复请求可显式提供 `task_patch.evidence_policy` 处理原未决事实，来源和已保存模型响应不改写。

`python -m yoloongppt mcp-serve` 在Docker内启动stdio MCP；客户端应通过 `docker --context desktop-linux compose exec -T app python -m yoloongppt mcp-serve` 的stdin/stdout连接，不能使用TTY。工具至少包含create_deck/revise_deck/inspect/validate/capabilities/debug，另有已有PPT、模板、资产与原生执行入口。当前只实现stdio，有界初始化和串行调用；完整客户端/取消能力仍待验收。

新CLI命令 `inspect-deck/edit-deck/parse-template/instantiate-template/compose-native/inventory-assets/compare-runs` 接收JSON文件；HTTP对应 `/inspect-deck`、`/edit-deck`、`/parse-template`、`/instantiate-template`、`/compose-native`、`/inventory-assets`、`/compare-runs`。AI 生成入口消费声明的原生版式与 caller 模板实际槽位；`register-template/get-template/resolve-assets` 对应 HTTP `/register-template`、`/get-template`、`/resolve-assets`。登记时保存显式 template_policy，已登记策略不能由调用 metadata 改写；模板文本槽位实例化仍有独立入口。当前 text/picture/table/chart 与明确品牌锁已有实物，复杂槽位、全比例/完整 style 和三上游兼容仍待按原验收补齐，未支持模板不会替换为默认模板。

本轮真实产物：[8页可编辑PPTX](validation/parallel-artifacts/generated/deck.pptx)、[PDF](validation/parallel-artifacts/generated/render/deck.pdf)。[并行集成记录](validation/并行核心功能集成.md)说明177项检查、初次失败、真实恢复及剩余条件。整体仍为部分交付，P0=0不表示系统AC通过。

## 可独立运行的模式路由与原子能力

app内 `python -m yoloongppt route /workspace/validation/route-request.json` 或 HTTP POST `/route` 输入相同JSON。raw_request.request保留原文、附件ID、显式模式、输出；attachment_roles明确内容/风格/模板/已有deck/还原来源，single_slide可指定动作及目标。八种模式独立保护策略，无法唯一判断则needs_clarification，未实现的后续模式标明executable=false，不替换为新建。

节点结果与完整DecisionTrace保存到F盘运行目录；`generate`也实际消费该节点。TaskSpec可附raw_request，声明路线与原文判定冲突时停止。能力快照只探测当前本地子集，外部模型/Office完整探测仍待SYS-002；节点入口可注入能力快照进行调试，其来源标为caller_provided，不能改变生成入口的实际探测。

`capabilities`的atomic_registry 含当前生成主链路八项写入能力（slide/text/table/chart/notes/image/shape/connector），native_objects另列30类能力与CRUD/保真/渲染限制；`compose-native`入口实际执行七类对象。已有PPT编辑保留未选部件，但不将未知对象保留升级为可编辑支持；其他后端保持原状态。

实物与复现：[模式路由与能力登记](validation/模式路由与能力登记.md)、[该次生成PPTX](validation/route-artifacts/deck.pptx)、[渲染PDF](validation/route-artifacts/render/deck.pdf)。39项模式节点/登记核验是前次版本证据；当前核心26项及生成修订31项回归通过，完整AC仍未通过。

## 约束归一化与来源分流

容器内 `python -m yoloongppt context /workspace/validation/context-generation-task.json` 或 POST `/context` 消费TaskSpec；`source-roles <input.json>` 或 POST `/source-roles` 消费包含task与已解析source_bundle的JSON。两节点可独立运行，并保存输入、候选、选择、规则、输出、时长和错误。

DEC-002按硬约束、偏好、调用方默认、系统默认的顺序选择，同级不同值阻断；原始请求中明确的页数、比例、语言、输出要求也参与处理。当前原文识别是有界规则，非任意自然语言理解。模板、品牌等值可归一化保留；当前真实原生槽位和显式品牌策略已接入，其余未满足的品牌/槽位/容量要求明确拒绝。精确硬页数不可改成软预算；输出要求不能静默忽略，偏好无法满足须保存原因。

DEC-003绑定真实source_id/asset_ref，保留事实、模板、风格、素材、已有deck及还原来源六种角色。来源解析现覆盖上节列出的有界格式；角色分类本身仍不等于语义抽取、OCR、完整模板或图片意义已通过验收。生成、QA及后续修订/复查只消费事实集合，全部原材料另行保存；角色冲突和身份未绑定在模型调用前阻断。

[40项检查与说明](validation/约束归一化与来源分流.md)、[本次8页原生PPTX](validation/context-artifacts/deck.pptx)、[PDF](validation/context-artifacts/render/deck.pdf)记录真实DeepSeek调用和三节点轨迹。这是当时三节点版本的QA记录；当前新增事实决策见下文，全部QA/AC仍未完成。

## 当前页面编译与真实产物

SYS-010/012/013 保留开场、宽栏、双栏、面板、结尾、表格和图表版式，并加入最多八图图文、原生图示、实际模板槽位和完整内容自适应。DEC-030–038 实际消费候选、评分、槽位/引用/notes、几何、实测字体容量、固色/文字对比度、明确图片适配、静态增强与 PP-05 能力预检查。可读容量分页后全部候选仍不适配时失败，不删文字、缩字号或用截图替代原生对象；稳定旧槽位维持恢复对象 ID。复杂语义评分、完整品牌策略/模板槽位、RTL/字体 fallback、效果/动画与多后端原验收仍进行中。

多栏QA按实际PDF字词坐标核对每个对象，独立删除PDF词反例仍检出缺字；旧单栏产物保持既有检查兼容。[23项组件核验](validation/layout-runtime.json)、[本版10页PPTX](validation/layout-artifacts/deck.pptx)、[PDF](validation/layout-artifacts/render/deck.pdf)及[实施说明](validation/版式编译与链路进度修复.md)保留初次9个P0问题、修正后当前P0=0及真实复审。当前模型内容从真实初次调用断点复用，引用修正和复审是新增实际调用；完整AC仍未通过。

原Excel“0-1全链路”已按实物同步进行中状态与剩余条件，“总览”完成数缓存与主表核对；阶段运行不表示完整系统交付。

## 来源冲突与事实边界

生成已接通DEC-004/005，独立CLI为 `resolve-evidence <input.json>`、`fact-boundaries <input.json>`，HTTP为 `/resolve-evidence`、`/fact-boundaries`。TaskSpec可附evidence_policy明确source_precedence/conflict_selections/missing_rules；未知或无关规则字段被拒绝，不自动挑选冲突值。

真实模型事实解释逐字核对来源；未决/必需缺失停止主内容生成，已选值和原始上下文进入文案投影，完整来源/冲突留存。假设/精确推算需稳定assumption_refs和可见标记；占位、询问/失败有记录。修订/复查验证快照hash并沿用边界，被否决数值在修订写入前失败；resume支持事实解释阶段的实际断点。

[35项节点与16项实物检查说明](validation/来源冲突与事实边界.md)、[四页已选事实PPTX](validation/fact-artifacts/generated/deck.pptx)、[PDF](validation/fact-artifacts/generated/render/deck.pdf)、[单对象修订稿](validation/fact-artifacts/revised/deck.pptx)与初次失败证据保留。上述历史样例已执行 P0=0；现已扩展到 DEC-006–040 的有界消费者，但完整语义抽取、节点原验收与全部 AC 仍未通过。

## 新视觉链路、质量决策与 QA-only 恢复

真实模型六页样例含 text/image/diagram/table/chart 和 26 个原生对象：[PPTX](validation/visual-live-artifacts/generated/deck.pptx)、[PDF](validation/visual-live-artifacts/generated/render/deck.pdf)。初次 `74a0567c` 的 QA_REVIEW_INCOMPLETE 保留；[成功 QA-only 恢复报告](validation/visual-live-artifacts/qa-recovered-success-39a2dbf3/quality-report.json) 保持原 PPTX/PDF/PNG 字节、复用已有真实审查响应，未增加模型或渲染调用。P0=0、四警告仍在，[终止判定](validation/visual-live-artifacts/qa-recovered-success-39a2dbf3/completion-decision.json) 为 warning/final_allowed=false，完整覆盖和 AC 仍未通过。

[另一父 run 的实际局部修订](validation/revision-plan-artifacts/revised/deck.pptx) 有 24 项范围/锁/过期/非法输入/部件保持/复审检查，使用真实生成父稿上的人工几何/颜色故障注入；不是六页样例已完成全自动修订。人工四页组件验证另有 23 项与 25 个 master/layout/theme 字节保留证据，不冒称 AI 生成。

`debug-node <JSON文件>`、HTTP `/debug-node` 或 MCP debug 接收 `{node_id,input}`，可独立调用 DEC-001–040 的当前消费者。新节点保留输入、候选、原因、规则、输出与局限；已选事实与真实资产继续约束修订/复查。[本工作包证据与边界](validation/并行接通视觉与质量修订.md) 记录实际失败、修复与下一原需求动作，不以接口存在或 P0=0 宣称全部交付。


[19项恢复与 HTTP/CLI/MCP 检查](validation/visual-live-artifacts/checks/recovery-checks-45a1db3f0580.json) 和 [10项重复恢复边界检查](validation/visual-live-artifacts/checks/repeat-recovery-90b93f62be10.json) 已通过。第二次显式复用 QA-only run `95bdc3f0-0d60-46b7-a8ce-418d3962e49c` 继续保留六页审查范围、原模型响应和 PPTX/render 字节，无新模型/渲染；警告不丢失、不重复，损坏 checkpoint 在默认及复用路径均阻断。默认 recheck 发起真实新审查，`reuse_saved_review=true` 仅在已验证的保存响应/请求/manifest 一致时复用；恢复成功仍是 warning，不能冲销完整系统验收。
