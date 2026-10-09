# YoloongPPT 项目目标与执行计划

## 项目目标

依据《AI_PPT_PDR_完整需求定义_V0.3.docx》和《AI_PPT_完整需求与任务矩阵_V0.3.xlsx》，交付一个可追溯的 AI PPT 生成系统。用户输入经过统一决策链后，系统至少能生成可编辑 PPTX，并完成渲染、结构、视觉、事实、可编辑性检查及局部修订闭环。

完整目标与防偏离规则见 [GOAL.md](GOAL.md)，本计划用于安排工作包与保留历史。需求矩阵是逐项执行与验收的工作台；开始或完成任何实现、研究、验证任务时，都关联稳定的 Requirement ID 或 Task ID，并在矩阵中保存状态和证据。2026-10-09 审计时应用目标为 paused；当前工具不能编辑旧 objective，本次已持久化项目执行目标，不宣称应用内文本已替换。

## 完成判定

- 308 条需求与 453 条任务逐项满足原验收；不得以未经用户授权的 N/A、Blocked 或 Partial 消除必需任务。
- S00–S44 全链路按基线落地；具体路径不适用步骤有依据及状态，但系统必需能力不能排除。DEC-001–040 决策节点可运行、可解释，有契约与实际证据。
- 5 个开源项目有可复现的研究记录；9 条 PowerPoint 后端路线完成需求对照和必要 PoC；PPT-001–030 对象能力有明确支持状态。
- AC-001–AC-030 验收通过。至少一个端到端路径从真实输入走到可编辑 PPTX、QA 与局部修订。
- Docker 仅管理本项目隔离开发环境。产品架构、语言、运行时和依赖版本须先由需求、PoC、平台限制及许可证据决定；容器环境观测不构成产品选型。

## 执行阶段

里程碑用于组织范围，不改写 Excel 中的任务依赖。依赖列与实际输入条件须满足；可以独立推进的组件不因阶段编号而等待。撤销旧“全部治理/研究/契约/后端完成后才实现产品”的串行方式。

| 阶段 | 需求范围 | 主要交付 |
|---|---|---|
| 1. 收束选型证据 | RES-P01–RES-P05、RES-031–RES-033；相关后端证据 | 复用现有成果，收尾研究验收、横向对照与复用许可决策；无依赖的系统准备可推进 |
| 2. 选型并建立产品入口 | GOV、SYS、IN；所选后端 ADP/PPT | 记录有证据的架构与版本，配置项目 Docker 应用服务，接入 TaskSpec、能力注册、错误与 trace；组件验收仍按原 E2E 条件 |
| 3. 首条真实完整链路 | AC-001、GOV-008、AC-027/028/030；对应 DEC/IN/CNT/TPL/AST/SYS/QA/REV | 文本/Markdown → 可编辑 PPTX → 渲染/QA → 局部修订；交付产物和复现命令，不以单条链路宣称项目完成 |
| 4. 扩展全部要求 | 全部 308/453；PP-01–09、PPT-001–030、S00–S44、AC-002–030 | 按原依赖与优先级扩展模式、来源、对象、后端、接口和平台，完成所有研究、质量、安全、运维及系统验收 |

治理、安全、来源追溯和质量验证贯穿实现。每个工作包结束时统一回填、双日志、提交、推送，不另拆成功推送状态补记。

## 2026-10-09 纠偏后的当前工作

- 审计基线：需求完成 14/308、进行中 55、未开始 239；任务完成 21/453、进行中 59、未开始 373；AC 0/30 执行。数字对应审计前 HEAD `171fc08`，不自动当作后续实时进度。详情见 [PROGRESS_AUDIT.md](PROGRESS_AUDIT.md)。
- 已收尾 TASK/VERIFY-RES-P04-04、TASK/VERIFY-RES-P04-05：5模板/8布局数据、30对象与QA/修订边界，禁网正常/边界/失败探针通过；真实发现高度截断和图表/演讲稿未消费，不代表产品能力通过。RES-P01-05 已按下述记录收尾；下一主工作包为 P02/P05 剩余研究。
- 后续关键依赖：P02/P05 剩余研究 → RES-031 → RES-032 和决策实现；RES-033 按原依赖交付。SYS-001/SYS-007 等无研究前置的准备可独立推进，但未经过真实 E2E 不标为完成。
- 不增加另一份需求状态台账；以下历史条目保留，若与矩阵或后来证据冲突，先核对对应原行和制品并在相关工作包修正。

## 当前进度

### TASK/VERIFY-RES-P04-04/05（2026-10-09 收尾）

- 状态：两条候选研究需求及四个 TASK/VERIFY 已完成；Excel 主表 N30:P31、任务 L50:M53 回填，其他任务/AC 未改。
- 证据：`research/P04/template-map.json`、`capability-map.json`、`template-capability-map.md`、`validation/verify-res-p04-04-05.json`；5模板/8布局原值与21份固定源码哈希对照，3份实际PPTX产物及正常/边界/失败结果。
- 关键结论：topic writer不执行flex布局；60条长bullet写4条、56条无报告遗漏；chartData与speakerNotes未消费；包装器缺真实QA、局部修订和既有PPT读改链。仅候选研究，无真实模型/Office/产品AC验证。
- 环境解阻：获用户授权重启全局WSL。常规Docker重启/WSL shutdown及服务停止挂起，管理员定点终止并重启WslService后恢复发行版枚举、Ubuntu内核和Docker API，项目workspace已启动；数据位置保持F盘。未删除、重建或改密码。

### TASK-GOV-001

- Requirement ID：GOV-001；P0；无前置任务。
- 状态：已完成。将 Excel“需求主表”中的 `RES-031`、`RES-032`、`RES-033` 按原规则、输入、约束、交付、验收、依赖、优先级与任务 ID 补入 DOCX 第 3.6 节；没有增加或改写需求范围。
- 验证：DOCX 与 Excel 的 308 个 Requirement ID 全部可定位；453 个 Task ID 唯一且均引用现有需求；DOCX 原有 13 张表和原段落顺序保留。Excel 回填完成状态和证据路径。
- 证据：Excel“需求主表”`N2:P2`、“可执行任务”`L2:M2`；本文件第 3.6 节；`ailog/` 与 `development-log/` 本次同名任务日志。

### TASK-GOV-002

- Requirement ID：GOV-002；P0；DEC-001；S02。
- 状态：进行中。已建立语言/运行时无关的 TaskRoute schema 与八模式契约目录草案；每种模式都列有输入、流程、输出、独立保护策略和验收场景。另列 8 个常规路由场景与 1 个边界冲突场景。
- 当前边界：Excel 的“数据对象”表列出 `RawTaskRequest`、`TaskSpec.route` 和 `RuntimeCapabilitySnapshot`，但未单列 `TaskRoute` 的正式字段定义。因此 `contracts/task-route.schema.json` 中的路由结果/trace 字段仍是待评审草案。运行时路由、候选生成算法、冲突优先级、与 `TaskSpec.route` 的正式版本关系及 P01–P05 实现映射尚未完成；不能据此宣称系统已支持八种模式。
- 静态核验：目录含 8 个唯一模式，每个均有 input/flow/output/acceptance_case 与独立 protection_policy_id；新增 `contracts/task-route.fixtures.json`，为 8 个常规场景和 1 个边界冲突场景给出完整预期 TaskRoute，逐项保留路由理由、DEC-001 候选/选择依据和保护策略；fixture 与 catalog 的场景 ID、请求文本、预期 mode/policy 一致。JSON 解析及契约字段/模式/策略映射静态检查通过。当前没有运行 JSON Schema 标准验证器，也未运行路由器测试。
- 证据：`contracts/task-route.schema.json`、`contracts/task-route.catalog.json`、`contracts/task-route.fixtures.json`；Excel“需求主表”`N3:P3`、“可执行任务”`L3:M3`、“决策链”`M2`、“0-1全链路”`G4:I4`。

### TASK-GOV-003

- Requirement ID：GOV-003；P0；无前置任务。
- 状态：进行中。已建立 `ConstraintSet` 的语言/运行时无关契约草案，顶层字段严格对应数据对象基线 `hard`、`soft`、`defaults`、`conflicts`；并定义约束来源、偏好降级说明与硬约束冲突报告结构。
- 当前边界：字段子结构与标识格式尚未由基线定义，均标为草案。合同 fixture 覆盖两个互斥硬约束、soft preference 降级、默认值来源三种场景，但只是预期结果；冲突检测、用户澄清和偏好降级的运行时行为尚无实现。
- 静态核验：三个 JSON 文件解析成功；三组 fixture 均满足手工结构约束，硬冲突示例指出字段、硬约束引用、不同取值及阻断处理结果；soft 降级含理由；默认值标识为系统来源。当前环境无 JSON Schema 标准验证器，未进行标准 Schema 或运行时测试。
- 证据：`contracts/constraint-set.schema.json`、`contracts/constraint-set.catalog.json`、`contracts/constraint-set.fixtures.json`；Excel“需求主表”`N4:P4`、“可执行任务”`L4:M4`、“数据对象”`I5:J5`。

### TASK-GOV-004

- Requirement ID：GOV-004；P0；无前置任务。
- 状态：进行中。已建立 `FallbackRecord[]` 契约草案；`reason_code` 精确复用矩阵“错误Fallback”表中的 32 个 Error Code，另以 `fallback_category` 描述扁平化、字体替换、图表转图像、模板替换、数据裁剪和页数偏差等实际动作。
- 当前边界：原因码表达触发原因，fallback 动作单独记录；目录按实际根因提示可用的既有代码，不能一概套码。需求矩阵“数据对象”表未单列 FallbackRecord，故不改动 49 项对象覆盖计数。Trace 与最终报告的正式引用格式、记录器及安全脱敏实现均待架构/运行时确定。
- 静态核验：3 个 JSON 文件解析成功；契约枚举与矩阵 ERR-001–ERR-032 的 32/32 Error Code 对齐；六种 GOV-004 示例动作均有 fixture，记录含 reason_code、前后行为、影响、user_visible、trace_ref 和 report_ref。当前未找到 `jsonschema`/AJV 标准验证器；上述为静态 fixture 检查，不是实际 fallback 执行结果。
- 进度边界：TASK-GOV-004 进行中；VERIFY-GOV-004 仍未开始。故意触发实际 fallback 并在最终报告中定位，需待应用执行链与 trace/report 落地后验证。
- 证据：`contracts/fallback-record.schema.json`、`contracts/fallback-record.catalog.json`、`contracts/fallback-record.fixtures.json`；Excel“需求主表”`N5:P5`、“可执行任务”`L5:M5`。

### TASK-GOV-005

- Requirement ID：GOV-005；P0；无前置任务。
- 状态：进行中。已建立 `CapabilityStatus` Draft 2020-12 契约草案，并逐项登记 Excel“PowerPoint对象矩阵”的 PPT-001–030 × PP-01–09 共 270 个状态。当前 PP-04 有 12 项能力为 `Partial`，其余 18 项为 `Untested`；其他 8 条路线的 240 项能力仍为 `Untested`。每项均保留证据、版本和范围边界。
- 当前边界：PP-04 的候选 PoC 依赖已固定为 `DocumentFormat.OpenXml` 3.5.1、`DocumentFormat.OpenXml.Framework` 3.5.1、`System.IO.Packaging` 10.0.2；隔离容器实际观察到 .NET SDK 10.0.401。它们只描述此次实验，不是产品语言、运行时或后端选型。PP-08/PP-09 仍只固定候选源码 commit；其余六条路线版本仍未冻结。所有路线的产品后端、API set/Office build 选型均未完成。`SYS-007` Capability Registry 尚未开始，基线也未枚举系统级非 PPT 原子能力或具体运行时 Adapter 实例；catalog 明确登记这两类范围缺口。`VERIFY-GOV-005` 仍未开始。
- 静态核验：30 项能力 × 9 条路线共 270 条记录；PP-04 当前 12 项 `Partial`、18 项 `Untested`，其余路线保持原状态；3 条候选路线的版本已固定，其他 6 条仍未冻结。PoC 已在锁定 Docker 镜像内运行并生成结构校验、形状修改、图片往返、表格单元格文本往返和图表系列数据往返报告；能力矩阵和 catalog 状态相符。
- 证据：`contracts/capability-status.schema.json`、`contracts/capability-status.catalog.json`、`contracts/capability-status.fixtures.json`；Excel“PowerPoint对象矩阵”`H2:H31`、“PowerPoint后端”`H5:N5`；`research/poc/PP-04/README.md`、`research/poc/PP-04/artifacts/report.json`。

### TASK-ADP-PP-04-01 / VERIFY-ADP-PP-04-01

- Requirement ID：ADP-PP-04-01；P0。两个任务仍为进行中：已完成一轮可运行 PoC 和正常/边界/失败验证，但后端行要求的能力清单尚未全部实测。
- 已验证：在固定镜像 `mcr.microsoft.com/dotnet/sdk@sha256:e70cdb7f80b0348f5cb85f19a8f670fca061f033d57eed12fa003d58b0e06317`（实验中观察到 SDK 10.0.401）中，以锁定依赖运行 PoC。固定 MIT 样例含 1 个 master、11 个 layouts、1 个 theme、0 张 slides；正常用例新增带 title/body 占位符的 1 张 slide。形状用例保存并重新打开 PPTX 后修改矩形探针文本；shape ID/name、preset `rect`、fill/stroke 与 x/y/cx/cy 全部保持，EMU 为 914400/457200/3657600/1828800。图片用例嵌入 1×1 PNG 后重新打开并原位替换图像字节；relationship、content type、alt text、shape ID/name 与 x/y/cx/cy 保持，图像 SHA-256 按预期改变。表格用例新建 2×2 table、保存并重开、读取四个单元格，再更新右下单元格文本；table shape ID/name、x/y/cx/cy 与行列数保持。图表用例新建含一个系列和 Q1–Q3 三个类别的柱形图，并绑定内嵌 XLSX；保存重开后将 Q2 数据从 18 更新为 20，同时更新图表数据缓存和 XLSX 单元格；series/category 公式、标题、图例、数值标签、坐标轴 ID、图表身份和 EMU 边界保持。PPTX 的五个输出均通过 Office 2019 `OpenXmlValidator`（0 错误），图表内嵌 XLSX 亦通过 Office 2019 校验（0 错误）。未知部件往返 SHA-256 一致；64 字节截断包按预期以 `System.IO.FileFormatException` 失败；无 slide 的模板作为边界输入被记录。
- 往返边界：`slideLayout1.xml` 与 `slideLayout11.xml` 原始字节哈希变化，但母版/布局/主题 XML 经过 namespace declaration、attribute order 和 insignificant formatting whitespace 规范化后相同。该结构比较不代表 Office 渲染保真。探针形状由同一 PoC 新建，不是预先填充的第三方 slide。
- 尚待验证：图片的 crop/contain/cover/rotation/transparency/compress/link-vs-embed 与渲染；表格的合并、边框/填充/字体/对齐、行列编辑、表头、分页、渲染及第三方既有表格读改保存；图表组合图、误差线、日期轴、其他类型、image fallback、PowerPoint 编辑数据行为、渲染及第三方既有图表读改保存；media、notes/comments、transitions/animations 及其读改保存；其他 AutoShape/adjustment/rotation、PowerPoint/LibreOffice 渲染与广泛第三方模板兼容性。此清单未实测前，TASK/VERIFY 保持进行中。
- 实验依赖和 SDK 版本仅是候选实验记录，产品架构/运行时/后端仍未选定。
- 证据：`research/poc/PP-04/PP04PoC.csproj`、`packages.lock.json`、`fixtures/`、`artifacts/pp04-output.pptx`、`artifacts/existing-shape-mutation.pptx`、`artifacts/image-roundtrip.pptx`、`artifacts/table-roundtrip.pptx`、`artifacts/chart-roundtrip.pptx`、`artifacts/report.json`、Excel“PowerPoint后端”`H5:N5`、“PowerPoint对象矩阵”`H2:H31`、“可执行任务”`L276:M277`。

### TASK-GOV-006

- Requirement ID：GOV-006；P0；无前置任务。
- 状态：进行中。建立语言/运行时无关的 ConfigSchema 草案，登记 GOV-006 明确列出的 20 类参数，并把 NFR-005 的分项 timeout、NFR-006 的重试限制与 NFR-007 的并发/Office 约束列为可追溯项。
- 当前边界：基线未指定各参数的 JSON 类型、默认值、取值范围或来源优先级。DEC-004 要决定优先级或保留 unresolved，且 TASK-DEC-004 依赖 RES-031；因此 catalog 明确记录待决策，不设置产品默认值。产品架构和运行时尚未选定，应用 trace 也未实现；pending fixture 只验证草案结构，不满足运行时有效配置快照验收。
- 静态核验：Draft 2020-12 元模式校验通过；ConfigSchema catalog 的 20 个参数项和 pending trace fixture 均通过 schema 实例校验；仅用于结构校验的 synthetic effective snapshot 正例通过，缺少值来源、未解参数或未解来源策略的负例均被拒绝。未运行应用配置加载或 trace 集成测试。
- 证据：`contracts/config-schema.schema.json`、`contracts/config-schema.catalog.json`、`contracts/config-schema.fixtures.json`；Excel“需求主表”`N7:P7`、“可执行任务”`L9:M9`。

### TASK-GOV-007

- Requirement ID：GOV-007；P0；无前置任务。
- 状态：进行中。建立语言/运行时无关的稳定 ID 约定草案：运行时实体使用类型前缀 + RFC 9562 UUIDv4，决策定义继续使用基线的 DEC-001–040；矩阵 Requirement/Task ID 与运行时 ID 分开。
- 对象映射：TaskSpec.task_id、ArtifactManifest.deck_id、SlideSpec.slide_id、SourceRecord.source_id、SourceEvidence.evidence_id、Assumption.assumption_id、AssetRecord.asset_id、PagePlan.section_id、LayoutTemplate.layout_id、LayoutSlot.slot_id、ObjectMap.logical_object_id、AtomicCapability.capability_id、CapabilityImplementation.implementation_id、PowerPointAdapter.adapter_id、DecisionCandidate.candidate_id、DecisionTrace.node_id/trace_id、QualityIssue.issue_id、RenderArtifact/ArtifactManifest.artifact_id 均有明确映射；其余显式 ID 字段的引用关系见 catalog。逻辑对象 ID 与后端 shape ID 分离；ObjectMap.source_ref 与 SlideSpec.source_refs[] 在草案中引用 evidence_id，可追到 SourceEvidence 和 SourceRecord。
- 基线对齐：数据对象表没有单列 Deck；本草案将 deck_id 纳入既有 ArtifactManifest 最低字段，不新增对象行。其他对象的完整 schema 与运行时实现仍待后续任务。
- 当前边界：Schema、catalog 和 fixtures 仅是格式及引用关系约定；静态验证不能证明真实 PPT shape 已可追溯。对象拆分/合并及跨修订实体识别仍待架构评审。
- 验证：Draft 2020-12 Schema 自校验通过；19 类 ID 映射、有效 ID 样例、4 个无效样例及跨对象引用链检查通过；Excel 数据对象覆盖仍为 49 项。未运行 ID 生成器或真实 PPT 端到端追溯。
- 证据：`contracts/object-id.schema.json`、`contracts/object-id.catalog.json`、`contracts/object-id.fixtures.json`；Excel“需求主表”`N8:P8`、“可执行任务”`L10:M10`、“数据对象”第 3、6–7、10、17、23、29–30、32–49 行。

### TASK-GOV-008

- Requirement ID：GOV-008；P0；无前置任务。
- 状态：进行中。建立项目级 E2E 完成门槛草案，验收矩阵仍是 30 个场景的唯一输入与通过条件来源。主验证路径采用 AC-002 的 DOCX 材料生成；由 AC-027 检查对象追溯、AC-030 检查 S00–S44 步骤账本。
- 验收要求：输出真实可编辑 PPTX，并为渲染、结构、视觉、事实和可编辑性分别留存通过证据；至少一条真实质量问题或用户局部修改必须经过 QualityIssue → RevisionPlan → RevisionAction → 新产物 → 定向 QA 复查，同时证明未修改内容保持。每个 S 步骤均需状态及产物/证据；N/A 必须记录理由与影响，不允许出现无解释断点。
- 整体范围：AC-001–AC-030 全部通过；完整项目还须覆盖并关闭 308 条 Requirement、453 个 Task，不能用单个 demo、图片输出或单次 PPTX 导出替代。
- 当前边界：验收矩阵 30 个 AC 均为“未执行”；S00–S44 共 45 步，其中 S02 仅有路由契约草案、其余 44 步未开始。仓库尚无产品运行链路，故 gate 保持 pending；本任务不选择产品架构、语言或运行时，也不宣称 AC 已通过。
- 验证：Draft 2020-12 Schema 与 catalog 实例校验；AC ID 与验收矩阵 30 项逐项一致；S00–S44 与全链路表 45 项逐项一致；6 个 gate policy fixture 的逻辑预期通过。未运行端到端应用或 PowerPoint 验收。
- 证据：`contracts/e2e-acceptance.schema.json`、`contracts/e2e-acceptance.catalog.json`、`contracts/e2e-acceptance.fixtures.json`；Excel“需求主表”`N9:P9`、“可执行任务”`L11:M11`、“0-1全链路”`A2:I46`、“验收矩阵”`A2:I31`。

### TASK-GOV-010

- Requirement ID：GOV-010；P0；无前置任务。
- 状态：进行中。已建立 Draft 2020-12 VersionManifest 契约、资源清单及正/负例；固定项目基线提交、PDR 与需求矩阵 SHA-256、P01–P05 研究 refs、PP-08/PP-09 候选源码 commit，以及 Docker Debian 多架构基础镜像索引 digest。
- 冻结范围：P01 main 与 v6.6.0 tag target 分别记录；P02 main/Skill、v0.2.0、v1.1.38（含 annotated tag object 与 peeled commit）；P03–P05 main refs；PP-08/PP-09 main commits 仅用于源码研究。候选仓库版本固定不等于产品后端选型。
- 未决范围：P01 requirements 与容器 APT 包未精确锁定；产品语言/运行时、产品库、模型、Office API set、Adapter、模板、renderer 和验收测试数据均未选定。九条 PowerPoint PoC 尚未执行，当前没有产品 E2E 验收结果。
- 验证边界：完成 Draft 2020-12 Schema/fixtures 静态校验、矩阵单元格回读，以及导出前后工作簿结构检查；容器基础镜像只核对 registry digest，未构建镜像或启动应用。
- 证据：contracts/version-manifest.schema.json、contracts/version-manifest.catalog.json、contracts/version-manifest.fixtures.json；Excel“需求主表”N11:P11、“可执行任务”L13:M13、“开源项目研究对象”第 3–6 行、“PowerPoint后端”J9:J10；Dockerfile。

### TASK-RES-P01-01

- Requirement ID：RES-P01-01；P0；无前置任务。
- 状态：`TASK-RES-P01-01`、`VERIFY-RES-P01-01` 与 Requirement `RES-P01-01` 均已完成。固定研究快照为 PPT Master `main` commit `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d`；上游 `v6.6.0` tag 指向另一提交 `a50758ac29ec027e85966db33e2ae80031446756`。这项研究不选择 YoloongPPT 的架构、语言或运行时。
- 上游声明 Python `3.10+`，根 `requirements.txt` 只有下限约束且无锁文件；源码根许可证 MIT。全量安装观测到 88 个发行包；可选 PyMuPDF `1.28.2`（AGPL-3.0）仅在本次临时研究容器中安装，不成为产品依赖决定。`requirements.txt` SHA-256、镜像 ID、完整版本清单和许可边界见 `research/P01/artifacts/quick-smoke/environment.json` 与 `pip-list.json`。
- Docker 当前可用。本次在镜像 `sha256:9cc4943354564a8d71825420752552f989afc8c85a66c7d396df0d0f6a5dab56` 中观察到 Debian 12 / Python `3.11.2`；这是符合上游最低要求的实验环境事实，不是 YoloongPPT 选型。源码克隆只读挂载；全量依赖装入独立的临时研究目录，未改动 Windows 主机 Python 环境或项目 `compose.yaml`。
- 官方 Quick 烟测：`project_manager.py` 初始化三页 Hello World 项目，Quick 最终检查通过且 0 warnings/0 errors；`svg_to_pptx.py --quick-generate --no-notes --no-animations` 输出可编辑 PPTX，Postflight 通过。ZIP 和 `python-pptx` 读取通过；3 页、17 个文本对象、40 个 DrawingML 形状，0 图片/图表/备注/转场/timing。输出 SHA-256 `c39b6b596b6c6df0c69d8bdc2886eac5d1339cab5f148833951f1370095acd25`。
- 正常/边界/失败证据已登记。只读安装目录作为默认写入目标时按预期以 `OSError errno=30` 失败，改为明确可写 `--dir` 后成功；无外部事实的空 `facts[]` 边界输入被接受。Docker 实验镜像没有 Office 渲染器；随后使用本机 Microsoft PowerPoint 16.0 只读打开 PPTX，并导出三张 1920×1080 PNG。视觉复核通过，未见裁切、遮挡或缺字。本机 PowerPoint 仅是 QA 工具，不构成产品运行时选择。
- `TASK-RES-P01-02` 的前置 Requirement `RES-P01-01` 已满足，且其源码调用链和验证证据已在后续章节完成。
- 证据：`research/P01/README.md`；`research/P01/projects/hello_world_research.md`、`hello_world_research.facts.json`；`research/P01/projects/p01_hello_world_20261007/` 下的 SVG、PPTX、Postflight、`verify-res-p01-01.json` 与 `validation/native-render/`；`research/P01/artifacts/quick-smoke/`；Excel“需求主表”`N12:O12`、“可执行任务”`L14:M15`、“开源项目研究对象”第 2 行。

### TASK-RES-P01-02

- Requirement ID：RES-P01-02；P0；依赖 RES-P01-01。
- 状态：`TASK-RES-P01-02`、`VERIFY-RES-P01-02` 与 Requirement `RES-P01-02` 均已完成。按固定 PPT Master commit 建立 Default 源码调用链、Quick 独立路线及 SourceIndex，明确分别属于静态源码追踪、实际运行观察和外部黑盒的节点。
- 主要发现：PPT Master 是供 Agent Host 加载的工作流包，不含通用模型执行循环。Default 包含 Strategist 两阶段规划、确认、`design_spec`/`spec_lock` 校验、SVG 质量门、`finalize_svg.py`、PPTX 导出与 postflight；Quick 在 Agent 上下文中规划，省略 Strategist/Confirm UI/spec/lock，执行 SVG 检查后直接导出。PowerPoint/LibreOffice 渲染在上游生成链外。
- 实际证据：Quick 正常生成链由 `workflow.log` 记录，三页 PPTX、质量门、postflight 与本机 PowerPoint 16.0 独立渲染通过；只读默认写入路径初始化失败并记录 `OSError errno=30`，改用显式可写挂载成功。Default 只做静态追踪，未声称运行通过。
- 静态核验：`source_index.json` 含 12 个节点、13 条边；引用文件存在，源码行范围均在文件内。工作簿任务状态/证据见 Excel“需求主表”`N13:P13`、“可执行任务”`L16:M17`。
- 环境边界：实验容器中的 Python 版本仅为当时观察值；不代表 YoloongPPT 选型。没有更改项目 Docker 应用配置，也未选择产品语言、运行时或依赖。
- 证据：`research/P01/call_graph.md`、`research/P01/source_index.json`、`research/P01/projects/p01_hello_world_20261007/validation/verify-res-p01-02.json`、`research/P01/projects/p01_hello_world_20261007/validation/workflow.log`、`research/P01/projects/p01_hello_world_20261007/exports/p01-hello-world.pptx`；Excel“需求主表”`N13:P13`、“可执行任务”`L16:M17`。

### TASK-RES-P01-03

- Requirement ID：RES-P01-03；P0；依赖 RES-P01-02。
- 状态：`TASK-RES-P01-03`、`VERIFY-RES-P01-03` 与 Requirement `RES-P01-03` 均已完成。针对固定 PPT Master commit 提取影响页面结构/视觉的上游决策，并按输入、候选、机制、输出、fallback、源码位置形成 24 节点 ProjectDecisionMap。
- DEC 对照：覆盖 DEC-001–DEC-040 全部 40 个 ID。crosswalk 表示来源机制相近，不表示 DEC 等价、YoloongPPT 已实现或产品验收通过。Quick/Default 分流、两阶段 Agent/用户确认、flat/structured SVG 契约、Executor 直接 SVG 落笔为 PPT Master 特有机制。
- 主要边界：多数审美、内容及版式选择是 Prompt 引导的 Agent/LLM 判断；上游未定义确定性评分器时保留未定义。Quick smoke 仅观察最终输出，不能还原隐式推理；Default 仅静态追踪。
- 静态核验：JSON 解析；24 节点均含所需字段；源码文件及行范围有效；40/40 DEC ID 均有关联节点。验证样例复核 Quick 正常输出、Quick/Default 路由边界和只读挂载初始化失败 `OSError errno=30`；失败为 P01-01 已留证，未重复触发。
- 证据：`research/P01/decision_map.md`、`research/P01/project_decision_map.json`、`research/P01/projects/p01_hello_world_20261007/validation/verify-res-p01-03.json`；Excel“需求主表”`N14:P14`、“可执行任务”`L18:M19`。

### TASK-RES-P01-04

- Requirement ID：RES-P01-04；P0；依赖 RES-P01-02。
- 状态：TASK-RES-P01-04、VERIFY-RES-P01-04 与 Requirement RES-P01-04 均已完成。固定 PPT Master commit 上建立 ProjectTemplateMap，涵盖 Brand/Style/Layout/Deck 索引及全部 7 组 Layout 原型。
- 资产结构：21 个 Brand、14 个 Style、7 个 Layout、2 个 Deck；7 组 Layout 共 86 个 SVG、53 种页面类型、320 个显式 slot、287 个 Design Spec token。每页包含画布 viewBox、layout key、picker name、用途、Design Spec tokens、slot role 与几何 bounds。核对 86/86 SVG 对应 roster、86/86 有 viewBox、320/320 bounds 有效；Blank 页保留零 slot。
- 规则与 IR：四种模板类型是正交组合，没有继承层级；记录 library/explicit、standard/fidelity/mirror、style/layout/mirror、strict/adaptive 与 flat/structured 的适用条件和显式元数据约束。Design Spec、spec_lock Schema、逐页 SVG 与可选 native visualization payload 分开记录；不宣称存在统一规范化 IR。
- 容量限制：bounds 是几何容量区域；固定源码未声明通用字符数或行数上限，文本容量仍未定义。Design Spec token 与 SVG slot 也未被推断为一对一绑定。
- 核验边界：首次 roster 解析漏掉 report_core 的 13 行（其表格比其他族多一列 Master）；按真实表结构修正后重跑，固定 commit、索引计数、roster、viewBox、slot bounds 检查全部通过。未运行产品生成、全模板渲染、Office round-trip 或 AC-001–AC-030。
- 项目边界：本项只研究上游源码；未选 YoloongPPT 语言/运行时，没有改 compose.yaml。Chart 33 项、Table 6 种及 12,027 个图标向量分别记录为页面级可视化或资源库，不误列为模板类型。
- 证据：research/P01/project_template_map.json、research/P01/tools/build_project_template_map.mjs、research/P01/validation/verify-res-p01-04.json、research/P01/README.md；Excel“需求主表”N15:P15、“可执行任务”L20:M21。

### TASK-RES-P01-05

- Requirement ID：RES-P01-05；P0；依赖 RES-P01-02（已完成）。
- 状态：已完成（含 TASK/VERIFY）。已建立 `research/P01/project_capability_map.json`，逐项整理 PowerPoint 对象矩阵 PPT-001–PPT-030 的固定源码能力状态，并单列 QA、Revision、最终 PPTX 渲染和既有 PPTX 编辑边界。Native/Partial/Fallback/Unsupported 是对上游代码路径的研究归类，不代表 YoloongPPT 产品状态。
- 写入与对象边界：Generate 以 SVG 为页面完整设计源并转为 DrawingML；flat/structured 路线显式决定 Master/Layout/placeholder 结构。已有 PPT round-trip 只编辑确认 plan 页，保留未改页，支持受限的 text/paint/image/table/chart 变更；继承 Master/Layout 对象和 source proxy 不能编辑，不能在该 route 改 slide size 或新增 Master/Layout。SmartArt、复杂效果、嵌入媒体/OLE 按 atomic proxy 保留。
- QA/Revision：区分 SVG pre-export quality gate、PPTX 离线 package/delivery checker、SVG 浏览器视觉预览、外部 Office 最终渲染、交付 read-back、SVG 重导出修订与既有 PPTX round-trip。Map 为 30 项对象、5 项 QA、3 项 Revision 均保留来源锚点和覆盖范围。
- 正常证据：复用既有 `verify-res-p01-01.json`，其中三页 Quick PPTX、ZIP/读取检查及 PowerPoint 16.0 主机只读渲染通过；每页分别有 7/16/7 个可编辑 shapes、4/9/4 个文本 shapes，未含图片、chart、notes、transition 或 timing。该 smoke 不被扩大解释为完整对象能力验证。
- 边界/失败验证：2026-10-09 禁网研究容器执行选定 26 项测试，全部通过且无跳过。继承对象、proxy ancestor 和 SmartArt 非法编辑/adopt 按预期拒绝；custom show、图表/表格一致性断言通过。QA receipt 的 not-provided/stale 仍允许导出，不能宣称强制新鲜性门禁；没有运行全量上游、真实模型、Office 对象渲染或产品 AC。旧环境阻塞已恢复，历史保留在 verify 报告。
- 项目边界：未改 `compose.yaml`，未选择产品语言/运行时/依赖；外部 PowerPoint 渲染只作为 P01-01 的 QA 证据，不是产品依赖。
- 证据：`research/P01/project_capability_map.json`、`research/P01/validation/verify-res-p01-05.json`、`research/P01/README.md`、`research/P01/validation/p01-boundary-tests.json`、`p01-boundary-tests.txt`；Excel“需求主表”`N16:P16`、“可执行任务”`L22:M23`、“开源项目研究对象”第 2 行。

### TASK-RES-P02-01

- Requirement ID：RES-P02-01；P0；无前置任务。
- 状态：进行中。按矩阵冻结 PPTAgent / DeepPresenter 三个研究快照：main `833cda553b343be0e486a93b0b57cac962cdd566`、v0.2.0 `d53296bc0ddd73e81d51c523d20dd711c7f233f3`、v1.1.38 annotated tag object `2e68c095a86bdbb91635dc4d91dad4662aba163c` / peeled commit `2419d30b134a71486523e95ded60b32489fd3c61`。远端 refs 与 GOV-010 既有版本记录一致，固定 clone 位于仓库外 `F:\YoloongPPT-Research\P02`。
- 锁与许可：main Skill 有 npm `package-lock.json`，Python `requirements.txt` 不是完整锁；v0.2.0 与 v1.1.38 均有 `uv.lock` 和子目录 npm lock。三个源码快照根 LICENSE 均为 MIT。main Skill requirements 固定 `pptagent==1.1.37`，而研究 tag 为 v1.1.38；v0.2.0 的包元数据版本为 0.2.8，与 tag 名 v0.2.0 不同。研究记录按源码事实区分，不静默对齐版本。
- 上游环境：main Skill README 要求 Linux（含 WSL）或 macOS、uv、npm、LibreOffice；macOS 转换器另需 Chrome，并示例使用 Python 3.12。论文 tags 的 `pyproject.toml` 要求 Python `>=3.11`。这些是上游各自的环境声明，不是 YoloongPPT 的技术选型。
- 环境进展：实验时及后续复核均确认 `desktop-linux` WSL Engine 使用 F 盘 WSL VHDX；研究容器将源码只读挂载、实验依赖与缓存写到 F 盘。按 main Skill requirements 安装 229 个 Python 包、npm lock、Playwright Chromium，并完成容器内 Codex Skill 注册；`uv pip check`、上游 Quick Start 的 11 项 `doctor` 检查及 Chromium headless smoke 通过。Windows 主机未安装 P02 依赖。
- 环境版本边界：本次观察到容器 Python 3.11.2、uv 0.12.23、Node 18.20.4/npm 9.2.0、LibreOffice 7.4.7.2、Playwright 1.62.0。Python 3.11.2 仅是 Debian 容器观测值，不是 YoloongPPT 产品技术选型；产品语言与运行时仍未选定。上游 npm 安装输出 6 个 high severity findings，尚未修复或替换依赖。
- 当前 Docker 状态：短暂停止后已恢复；`docker desktop status` 为 running，Engine `27.4.0`，`DockerRootDir=/var/lib/docker`。项目 workspace、P02 研究容器和 Presenton P03 研究容器均 Up，源码、artifacts 与应用数据宿主挂载均在 F 盘；P03 Web 端口只绑定 `127.0.0.1:5001`。Docker Desktop settings 仍显示 `DataFolder=C:\ProgramData\DockerDesktop\vm-data`，但当前 `wslEngineEnabled=True`，WSL VHDX 在 `F:\DockerDesktopWSL`；项目 Docker 层与容器挂载均确认位于 F。
- 验收边界：额外尝试的 `pptagent --help` 包入口约 60 秒未返回，已中断；官方 README 指定的 `scripts/pptagent.py doctor` 已通过 11 项检查。未向容器传入提供商凭据，未调用模型/API、生成 PPTX 或完成视觉评审。因此 `ProjectBaseline` 官方生成与审查尚未通过，`TASK-RES-P02-01` 与 `VERIFY-RES-P02-01` 保持进行中。
- 证据：`research/P02/README.md`、`research/P02/validation/environment-main-skill.txt`、`research/P02/validation/packages-freeze-main-skill.txt`、`research/P02/validation/official-doctor-main-skill.json`、`research/P02/validation/verify-res-p02-01.json`、`research/P02/scripts/`、`contracts/version-manifest.catalog.json`；Excel“需求主表”`N17:P17`、“可执行任务”`L24:M25`、“开源项目研究对象”第 3 行。当前 P02 官网 [README](https://github.com/icip-cas/PPTAgent/blob/833cda553b343be0e486a93b0b57cac962cdd566/README.md) 固定到 main commit。

### TASK-RES-P03-01

- Requirement ID：RES-P03-01；P0；无前置任务。
- 状态：已完成。官方 `refs/heads/main` 于 2026-10-07 指向 `35bf44290f821323e003da854f78ffcb0e918167`，与 GOV-010 的 `P03-MAIN` pinned commit 一致。仓库外研究 clone `F:\YoloongPPT-Research\P03` 使用该 detached commit 和 sparse checkout，已包含官方 Docker build 所需资源目录。
- 锁与许可：记录根、Electron、Next.js 的三个 npm v3 lock 和 FastAPI `uv.lock` version 1/revision 3；FastAPI 上游声明 `>=3.11,<3.12`，uv lock 约束为 `==3.11.*`，不推导补丁版本或产品运行时。根许可证 Apache-2.0，另有第三方归属 `NOTICE`；尚未完成依赖逐项许可审计。
- 上游流程：固定文档描述 Standard（固定 layout、outline review、模板）和 Smart（adaptive layout、流式进入编辑器）；Web UI / MCP 模式开关不等于 REST API 授权。上游 README 还描述多用户工作区，此功能属于 GOV-009 排除边界，不扩大本项目范围。
- 运行验证：从固定源码使用上游 `docker-compose.yml` 构建并启动 `production`；本地 override 仅发布 `127.0.0.1:5001`。容器数据盘位于 `F:\DockerDesktopWSL\disk\docker_data.vhdx`，`/app_data` 绑定 F 盘。Next.js/FastAPI 启动、数据库迁移和默认模板导入完成；首页与 `/api/v1/auth/status` 均返回 HTTP 200。
- 验收边界：RES-P03-01 / TASK-RES-P03-01 的基线验收是固定 checkout、锁/环境/许可证记录，以及官方 Quick Start 的 Docker 启动与本地网页访问，以上均已完成。正常启动验证证据已记录；`VERIFY-RES-P03-01` 进行中，尚缺边界/失败样例。接口状态为 `configured=false`，没有模型凭据、模型/API 请求、PPTX 生成或视觉评审；这些结果仍待后续生成任务验证。
- 证据：`research/P03/README.md`、`research/P03/validation/smoke.json`、`contracts/version-manifest.catalog.json`；Excel“需求主表”`N22:P22`、“可执行任务”`L34:M34`、“开源项目研究对象”第 4 行。官方 [README](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/README.md) 与[生成模式说明](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/docs/presentation-generation-modes.md)固定到同一 commit。

### TASK-RES-P03-02 / VERIFY-RES-P03-02

- Requirement ID：RES-P03-02；P0；TASK-RES-P03-02 依赖 TASK-RES-P03-01，已满足。
- TASK-RES-P03-02 状态：已完成。基于冻结 commit 35bf44290f821323e003da854f78ffcb0e918167 逐段追踪网页 Standard、网页 Smart、直接 REST、MCP OpenAPI adapter、编辑/聊天修订、TemplateV2、SSE 持久化与 PPTX/PDF 导出；没有只根据 README 推断。主节点均有源码路径及符号索引。
- 路径边界：export-core 实现不在 clone 内，根 package.json 的 presentationExportVersion 固定为 v1.0.34，故明确列为外部黑盒。provider 服务/密钥也在 llmai 调用边界之外。本次没有生成请求；不能把源码路径当作运行成功或产品架构决定。
- VERIFY-RES-P03-02 状态：进行中。HTTP 实际观察为 GET / = 200，GET /api/v1/auth/status = 200 且 configured=false；空生成请求与 n_slides=0 请求均由登录初始化门禁返回 428，未进入 endpoint 输入校验。没有生成大纲、页面或 PPTX。
- 验收边界：Standard 允许素材 fallback 并写 warning；未在所追踪主路径发现完整 deck 级 QA gate。Smart 有 HTML 规范化/安全检查，不等于原生 PowerPoint 对象或整套质量验收。后续继续验证正常生成、跨过登录门禁后的边界和 provider 失败路径。
- 证据：research/P03/call-graph.md、research/P03/source-index.json、research/P03/validation/verify-res-p03-02.json；Excel“需求主表”第 23 行、“可执行任务”第 36–37 行、“开源项目研究对象”第 4 行。
### TASK-RES-P03-03 / VERIFY-RES-P03-03

- Requirement ID：RES-P03-03；P0；依赖 TASK-RES-P03-02，已满足。
- TASK-RES-P03-03 状态：已完成。固定源码决策图记录 17 个代码级节点，并对 DEC-001–DEC-040 做完整交叉映射：6 个有明确机制、29 个部分映射、5 个未发现等价独立机制。
- 映射边界：明确区分字段/代码分支、LLM prompt 隐式选择、以及源码未发现的机制。ordered/unordered layout、slides_markdown 直接映射、Smart HTML 流和 fallback 分支都保留各自行为；随机 layout 修补、模型外部服务和 export-core 外部黑盒均显式标出。
- VERIFY-RES-P03-03 状态：进行中。正常 Standard/Smart 生成无法通过本地登录初始化门禁；n_slides=0 与空输入也在 HTTP 428 门禁被拦截，未执行到决策 endpoint。没有生成页面/PPTX/PDF或验证视觉结果。
- 证据：research/P03/decision-map.md、research/P03/decision-map.json、research/P03/validation/verify-res-p03-03.json；源码路径通过 research/P03/source-index.json 解析到冻结 commit。Excel“需求主表”第 24 行、“可执行任务”第 38–39 行。

### TASK-RES-P03-04 / VERIFY-RES-P03-04

- Requirement ID：RES-P03-04；TASK-RES-P03-04 依赖 TASK-RES-P03-02，已满足。
- TASK-RES-P03-04 状态：已完成。固定 commit `35bf44290f821323e003da854f78ffcb0e918167` 的 16 个默认模板已生成 `ProjectTemplateMap`，记录 383 个 layout、1,600 个组件槽位、444 个 merged-component 变体组、10,283 个嵌套元素和 1,002 个静态文件；模板 JSON 与静态文件均带 SHA-256。
- 字段范围：组件槽位与元素树保留 ID、描述、层级、位置/尺寸、内容字段、样式/主题 token、显式 min/max 容量字段、重复组件变体及静态资产清单。元素坐标单位未由模板 JSON 声明；源码中的 1280×720 常量只作为源码观察。文本字符容量不从几何推算。
- 未决语义：默认模板没有显式页面类型或逐版式适用条件；`template-map.json` 的页面类型是依据 ID/description 关键词形成的候选，未映射到产品 taxonomy。未发现模板 `parent`/`extends` 字段；merged-component variants 不等同继承。TextCapacityPlan 是单独的模板认证生成结构，不构成默认模板的已测容量。
- 静态核验：16 个模板 JSON 均可解析；模板、layout、slot、merged-component 和静态文件清单计数与源目录一致；source-index 的新增源码引用可定位到冻结 checkout。没有运行模板 API、模型生成、PPTX 导出或视觉检查。
- VERIFY-RES-P03-04 状态：进行中。正常/边界/失败生成、实际内容 Schema 输出和视觉渲染尚未验证；本机认证状态此前记录为 `configured=false`，生成请求曾在 HTTP 428 登录门禁被拦截。该任务没有重试生成或配置凭据。
- 证据：`research/P03/template-map.md`、`research/P03/template-map.json`、`research/P03/validation/verify-res-p03-04.json`、`research/P03/source-index.json`；Excel“需求主表”第 25 行、“可执行任务”第 40–41 行、“开源项目研究对象”第 4 行。

### TASK-RES-P03-05 — Presenton PPT 对象、QA、修订与已有 PPT 边界
- Requirement：RES-P03-05；依赖：RES-P03-02；固定上游 commit：35bf44290f821323e003da854f78ffcb0e918167。
- 静态交付：research/P03/capability-map.json、research/P03/capability-map.md、research/P03/source-index.json、research/P03/validation/verify-res-p03-05.json。
- 覆盖对象内部模型、浏览器渲染、导出黑盒、schema/Smart 单页检查、Standard deck QA 边界、REST/chat 修订、已有 PPT 模板转换与原包编辑边界。
- TASK-RES-P03-05：已完成（静态源码映射）；VERIFY-RES-P03-05：进行中（测试未运行，正常/边界/失败生成与导出视觉结果待认证环境验证）。
- 未调用模型或生成 API，未生成 PPTX；不得将内部对象模型描述为已验证的 PPTX 原生对象。

### TASK-RES-P04-01

- Requirement ID：RES-P04-01；P0；无前置任务。PDR 中 RES-P04-02/03 是独立后续研究任务。
- 状态：已完成。上游 main 于 2026-10-07 指向 c3605ebc487fc6c7d4f4139761e46d7021cd656c，研究 clone 在 F:/YoloongPPT-Research/P04，detached checkout 干净；package-lock SHA-256 为 f9a2b016df533d79d7c55207c699d84d754b9178be9cb421e1c43259b48f4a68；上游许可证 MIT。
- 上游 package.json 声明 Node >=18.0.0。Node 18.20.8 / npm 10.8.2 隔离容器完成 npm ci（219 个包）和 npm run build；官方 HTML CLI 样例在 Node 18.20.8 失败，报 Cannot use import statement outside a module。直接 CommonJS require PptxGenJS 成功；固定依赖 pptxgenjs@4.0.1 的 ESM export 指向 dist/pptxgen.es.js，但包未声明 type=module。相同官方样例在 Node 24.14.0 隔离容器成功。Node 24 仅为研究环境观测，不是产品运行时决定。
- VERIFY-RES-P04-01：已完成正常、边界和失败三个 CLI 案例。正常样例生成 45,012 字节 PPTX；嵌套 HTML 样例生成 47,372 字节 PPTX；无输入样例按预期退出 1 并输出参数错误。两个 PPTX 的 ZIP 必需部件和文本已检查。未运行上游测试，未做 Office/LibreOffice 视觉渲染。
- 证据：research/P04/README.md、research/P04/validation/verify-res-p04-01.json、research/P04/validation/minimal-html-poc.pptx、research/P04/validation/edge-nested-html-poc.pptx、contracts/version-manifest.catalog.json；Excel“需求主表”N27:P27、“可执行任务”L44:M45、“开源项目研究对象”K5:L5。2026-10-08 原始 OOXML 复核确认这些 P04-01 状态单元格此前已正确填写；产品语言/运行时/后端仍未选定。

### TASK-RES-P04-02

- Requirement ID：RES-P04-02；P0；依赖 RES-P04-01。固定源码为 `peterfei/ai-agent-ppt` main commit `c3605ebc487fc6c7d4f4139761e46d7021cd656c`，许可 MIT；上游研究不构成 YoloongPPT 运行时或依赖选择。
- 状态：已完成。建立 `research/P04/call-graph.md` 和 `research/P04/source-index.json`，以 bin/CLI、配置、Provider、模板、输入路由、提示词、slot、布局、适配器和写出器为节点，为每个源码节点记录文件/符号/行号；模型服务、purelayout 算法、PptxGenJS 序列化及图片 URL 请求明确标外部黑盒。未发现页面输出流水线。
- 路由边界：CLI 先要求配置并构造 Provider；CreateCommand 内路由顺序为 HTML > images > topic/input。topic/input 走 outline、逐页 content fill、layout/slot 和 PPTXBuilder；HTML 与图片走 PureLayout、PPTAdapter 和 PptxGenJS。目录输入仅读取根 README.md/package.json；无效 layout 会跳过页面；content fill 异常静默保留原大纲；图片失败继续并仍写文件。这些均为上游源码观察。
- 内容限制：`SLOT_MAP` 仅有 title/subtitle/code/notes/image/bulletPoints 映射，图表、时间线、比较数据没有相应 slot mapping。PPTXBuilder flatten 仅消费文本和图片。没有在此任务中把这些上游缺口改造成产品行为。
- Docker 验证：Node 24.14.0 容器中 `npm run build` 通过；固定源与临时依赖副本的 package-lock 及关键源码 SHA-256 一致。容器使用 `--network none`，假 Provider 覆盖主题正常、content fill 错误回退、缺输入失败；未使用真实凭据或 API。
- 结果：正常和回退路线都生成一个 slide，PPTX 含 `[Content_Types].xml`、`ppt/presentation.xml`、`ppt/slides/slide1.xml`，大小 47,127 字节，SHA-256 `EB314E726DF935D01A833E46C4F105BF24ABAD6EA81DA9144F088B26550FC61D`；缺输入在 0 次 Provider 调用时按预期报错。两个 PPTX hash 相同；当前 fixture 使用的 `bullet` layout 不含 subtitle/notes slots，因此 ContentFiller 输出字段未影响该 layout 的产物。
- 验收边界：验证记录和脚本位于 `research/P04/validation/verify-res-p04-02.json` 与 `.mjs`。未调用真实 LLM/Vision API、未运行上游 Vitest、未做 PowerPoint/LibreOffice 视觉渲染或往返编辑；页面输出路线仅标记为未发现，未推断为产品需求不需要。
- 矩阵回填：本任务更新 `需求主表 N28:P28`、`可执行任务 L46:M47`、`开源项目研究对象 K5:N5` 和“总览”开源项目研究完成数缓存。P04-01 状态保留原值；保持 308 个需求、453 个任务和其余任务范围不变。
- 证据：`research/P04/call-graph.md`、`research/P04/source-index.json`、`research/P04/validation/verify-res-p04-02.mjs`、`research/P04/validation/verify-res-p04-02.json`、两个 `topic-route-*.pptx`；Excel“需求主表”N27:P28、“可执行任务”L44:M47、“开源项目研究对象”K5:N5。

### TASK-RES-P05-01

- Requirement ID：RES-P05-01；P0；无前置任务。PDR 中的 RES-P05-02 至 RES-P05-05 是独立后续任务。
- 状态：进行中。上游 `main` 与 annotated tag `v0.8.0` 均固定到 commit `5ae0670747885c464aa8063329a902d80a251877`；tag object 为 `923300ac557b0c09ec73f4a1f681233be2940452`，研究 clone 在仓库外 `F:\YoloongPPT-Research\P05`。
- 上游运行声明：README 为 Python 3.10+、Node.js 18+；`pyproject.toml` 要求 Python `>=3.10`，npm `package.json` 要求 Node `>=18`；上游 Dockerfile 使用 `python:3.12-slim` 和 NodeSource 20.x。YoloongPPT 仍未选择语言/运行时，Python 3.11.2 不是本项目要求。
- 锁与许可证：有 npm lockfileVersion 3；Python `requirements.txt` 只有下限约束，无完整 Python 锁。根 LICENSE/package.json 声明 AGPL v3，pyproject/package-lock 元数据声明 Apache-2.0，且上游包版本 0.7.8/0.8.0 不一致；许可证标为未评估，不静默裁定。
- 环境阻塞：`scripts/project.ps1 start` 和 Docker Desktop/WSL 恢复尝试后，`desktop-linux` Engine pipe 仍不存在，项目容器未启动。没有在宿主机安装依赖；官方 Quick Start、测试、构建和 PPTX 生成均未执行。
- 验收边界：源码 refs、锁文件摘要、上游运行声明与许可差异已静态记录；`ProjectBaseline` 仍未通过，`TASK-RES-P05-01` 保持进行中，`VERIFY-RES-P05-01` 保持未开始；P05-02 至 P05-05 与 AC-001–AC-030 状态未因此改变。
- 证据：`research/P05/README.md`、`contracts/version-manifest.catalog.json`；Excel“需求主表”`N32:P32`、“可执行任务”`L54:M55`、“开源项目研究对象”第 6 行。

### TASK-IN-001

- Requirement ID：IN-001；P0；无前置任务。
- 状态：进行中。已建立 Draft 2020-12 的 `RawTaskRequest` 与 Prompt 规范化结果草案，固定原始文本、附件 Asset ID、显式请求字段、主题/要求/修改指令/上下文及错误/来源跨度；`task-route.catalog.json` 已显式引用该输入契约。
- 边界：解析结果只表示文本结构；不包含 TaskRoute、DEC、模板/样式或 provider 选择。`requested_mode` 与 `requested_outputs` 是调用方显式输入，不是解析器推断结果。
- 验收边界：自然语言正常样例及空白边界 fixture 已建立；JSON 结构和来源跨度静态核对通过。运行时 parser 未实现，原文/资产引用一致性和跨度语义尚无运行时执行证据，故 `TASK-IN-001` 保持进行中；AC-001 仍未执行。
- 证据：`contracts/prompt-input.schema.json`、`contracts/prompt-input.catalog.json`、`contracts/prompt-input.fixtures.json`；Excel“需求主表”`N40:P40`、“可执行任务”`L68:M68`、“数据对象”第 2 行。

### TASK-IN-002

- Requirement ID：IN-002；P0；无前置任务。
- 状态：进行中。已建立 `TextDocumentModel` Draft 2020-12 契约、目录和预期 fixture；模型按原顺序保留标题层级、段落/块位置、嵌套列表、围栏代码、表格、链接、图片引用、块引用与脚注标记。
- 边界：原始 Markdown 逐字保留；未知语法不得静默扁平化。Markdown 方言、解析库、运行时、依赖和许可证未选定；URL 获取与图片下载不属于本契约的解析实现。任务表有 `TextDocumentModel` 交付名，但数据对象表未单列该对象，本任务只追溯到既有 TASK-IN-002，不增加 Requirement/Task。
- 静态核验：schema/catalog/fixtures JSON 可解析且 `$ref` 可解析到本地 definitions；fixture 的 31 个来源跨度与行号自洽，块索引、表格列数和正常/边界状态满足草案约定。未运行标准 JSON Schema 验证器。
- 验收边界：正常结构样例与空白边界样例已建立；parser 尚未实现，方言兼容、真实解析、源位置语义和错误行为没有运行时验证，因此 `TASK-IN-002` 保持进行中；AC-001–AC-030 均未执行。
- 证据：`contracts/text-document.schema.json`、`contracts/text-document.catalog.json`、`contracts/text-document.fixtures.json`；Excel“需求主表”`N41:P41`、“可执行任务”`L69:M69`。

### TASK-IN-003

- Requirement ID：IN-003；P0；无前置任务。
- 状态：进行中。已建立 `DocxEvidence` Draft 2020-12 契约、目录和正常/损坏包边界 fixture；按顺序保留标题/段落、表格单元格、超链接、图片引用、题注和段落锚点。
- 边界：物理页码依赖排版引擎、字体和版式；在未固定渲染器时 fixture 明确标记 `pending` 并不给出虚构页码。DOCX 库、运行时、依赖和许可证未选定。任务表已列 `DocxEvidence` 交付名，但数据对象表无同名行；本任务不新增需求或任务。
- 静态核验：schema/catalog/fixtures JSON 可解析且 `$ref` 可解析；正常 fixture 的 5 个正文块、表格、超链接、图片/题注关联和 9 个分页状态位置均符合契约预期；输入资产引用在结果中保留。未运行标准 JSON Schema 验证器。
- 验收边界：损坏 DOCX 的结构化失败 fixture 已建立；DOCX parser 与固定分页渲染尚未实现/执行，因此 `TASK-IN-003` 保持进行中，页码和真实文件解析验收未通过；AC-001–AC-030 均未执行。
- 证据：`contracts/docx-evidence.schema.json`、`contracts/docx-evidence.catalog.json`、`contracts/docx-evidence.fixtures.json`；Excel“需求主表”`N42:P42`、“可执行任务”`L70:M70`。

### TASK-IN-004

- Requirement ID：IN-004；P0；无前置任务。
- 状态：进行中。已建立 `PdfEvidence` Draft 2020-12 契约、目录和正常/边界预期 fixture；记录逐页文本块、标题候选、表格单元格、图片对象、坐标框架和来源锚点。
- 坐标边界：项目契约定义使用旋转后 CropBox 左上角原点、point（1/72 英寸）单位；每个 bbox 都带可解释的页面 frame。该坐标转换尚未用真实 PDF/旋转页夹具执行验证。
- 输入边界：IN-004 只处理原生文本层；扫描 PDF 边界返回 `PDF_NO_TEXT_LAYER`，不在本任务中静默进入 OCR。OCR 属于独立 IN-005。
- 静态核验：schema/catalog/fixtures JSON 可解析且 `$ref` 可定位；正常 fixture 含 2 页、5 个元素、4 个表格单元格，页号/索引/锚点一致且 bbox 在页面 frame 内；Asset ID 输入/输出一致。未运行标准 JSON Schema 验证器。
- 验收边界：fixtures 仅为预期结构，无真实 PDF parser 或页框变换结果；`TASK-IN-004` 保持进行中，表格/图片提取和坐标精度未验收；AC-001–AC-030 均未执行。
- 证据：`contracts/pdf-evidence.schema.json`、`contracts/pdf-evidence.catalog.json`、`contracts/pdf-evidence.fixtures.json`；Excel“需求主表”`N43:P43`、“可执行任务”`L71:M71`。

### TASK-IN-005

- Requirement ID：IN-005；P1；矩阵未列前置任务。
- 状态：进行中。已建立 `OcrEvidence` Draft 2020-12 任务级契约草案及四个合成预期 fixture，覆盖扫描页 OCR/视觉路由、混合文本/扫描页、低置信度输出、OCR 部分失败和损坏 PDF 的结构化错误。
- 逐页与来源：沿用 IN-004 的零基 `page_index`、一基 `page_number`、coordinate_frame、PDF SourceAnchor 和 bbox 定义；无文本页必须进入 `ocr_visual` 路径，不将未运行/失败静默写成 OCR 已完成。
- 置信度与错误：保存处理器原始 score 和 scale，不设置产品阈值，也不将置信度视作事实正确概率。复用矩阵既有 ERR-004/INPUT_CORRUPT、ERR-006/PARSE_PARTIAL、ERR-007/OCR_LOW_CONFIDENCE；低置信文字继续保留并标记，不能直接作为已确认事实。
- 运行时与版本边界：记录 processor 执行状态、引擎/版本/模型/许可证字段；当前 fixtures 明确标为 fixture_only/not_executed。PDF renderer、OCR 引擎/模型、依赖版本、产品运行时和许可尚未选定。
- 数据对象对齐：任务交付名 `OcrEvidence` 未列为独立数据对象；`SourceEvidence` 已有 confidence/anchor。本任务只建任务级契约，不新增、删除或改写数据对象行。
- 静态核验：3 个 JSON 文件可解析；本地 Schema 引用、页码/锚点/置信度尺度、no-text 路由以及 ERR-004/006/007 映射静态核对。未运行标准 JSON Schema validator、真实 PDF/OCR parser、视觉处理器、Office renderer 或 AC-001–AC-030。
- 证据：`contracts/ocr-evidence.schema.json`、`contracts/ocr-evidence.catalog.json`、`contracts/ocr-evidence.fixtures.json`；Excel“需求主表”`N44:P44`、“可执行任务”`L72:M72`；`contracts/pdf-evidence.schema.json`、`contracts/input-issue.schema.json`。

### TASK-IN-006

- Requirement ID：IN-006；P0；无前置任务。
- 状态：进行中。已建立 ImportedDeckModel Draft 2020-12 契约、目录及正常/边界预期 fixture，覆盖 slide/title/body、table、chart、image、notes、master/layout/theme、几何及 OOXML package-part 锚点。
- 输入边界：source 用途仅接受 user/caller 的 content 或 reference 标记；未声明时保留 unassigned，解析层不推断业务用途。模型将导入源与模板资产区分，模板解析单列在 IN-007。
- 几何/保真边界：保留源 DrawingML x/y/cx/cy EMU 值，并明确 slide/group_local 坐标空间、旋转和翻转；不能可靠解析时标为 unsupported 并说明原因。未知对象保留源锚点并由 coverage/error 说明，不静默丢弃。
- 静态核验：schema/catalog/fixtures JSON 可解析且引用可定位；正常 fixture 有 5 个 slide 元素，覆盖 title/body/table/chart/image；含 4 个带行列来源锚点的表格单元格、3 个图表类别/值、图片与嵌入工作簿 Asset ID、演讲者备注及 master/layout/theme 关系；边界 fixture 返回 PPTX_INVALID_PACKAGE 并保留输入资产引用。
- 验收边界：fixture 是合成预期结构，未运行真实 PPTX parser、组变换/几何解析、图表读取或 Office 渲染，因此 TASK-IN-006 保持进行中；AC-001–AC-030 均未执行。产品运行时和依赖未选定。
- 基线对齐：任务表已列 ImportedDeckModel 为输出，但“数据对象”表无同名行；本任务只关联既有 IN-006/TASK-IN-006，不增删需求、任务或数据对象行。
- 证据：contracts/imported-deck.schema.json、contracts/imported-deck.catalog.json、contracts/imported-deck.fixtures.json；Excel“需求主表”N45:P45、“可执行任务”L73:M73。

### TASK-IN-007

- Requirement ID：IN-007；P0；无前置任务。
- 状态：进行中。已建立 TemplatePack Draft 2020-12 契约、目录及正常/边界预期 fixture，覆盖 master/layout/placeholders、主题 token、brand/Logo Asset、preview、license 和 version。
- 结构边界：TemplatePack 强制包含结构化 master 与 layout 及关联占位符；preview 只能作为补充，不能把模板简化成截图。只收到图片时返回 TEMPLATE_STRUCTURE_NOT_FOUND；损坏 PPTX 返回 PPTX_INVALID_PACKAGE。
- 证据边界：品牌规则必须关联来源锚点；source version 与 license 无证据时标记 unknown，不从外观、文件时间或环境信息推断。几何保留源 EMU 值，未知时显式记录 unsupported。
- 静态核验：schema/catalog/fixtures JSON 可解析且引用可定位；正常 fixture 结构化保留 master/layout/2 个 placeholder/主题色与字体/品牌规则/Logo 和 preview Asset ID；版本与许可证明确为 unknown，结果为 partial。另有损坏包与“只有截图”两个结构化失败边界 fixture。
- 验收边界：fixtures 是合成预期结构，未运行真实 PPTX 模板解析、母版/版式继承、品牌识别、资产提取或 Office 渲染；因此 TASK-IN-007 保持进行中，AC-001–AC-030 均未执行。产品运行时和依赖未选定。
- 基线对齐：已在矩阵“数据对象”既有 TemplatePack 行 I28:J28 记录进行中和契约证据；没有新增或删改需求、任务或数据对象行。
- 证据：contracts/template-pack.schema.json、contracts/template-pack.catalog.json、contracts/template-pack.fixtures.json；Excel“需求主表”N46:P46、“可执行任务”L74:M74、“数据对象”I28:J28。

### TASK-IN-008

- Requirement ID：IN-008；P0；无前置任务。
- 状态：进行中。已建立 TabularEvidence Draft 2020-12 契约、目录及 XLSX/CSV 正常与边界预期 fixture，覆盖 sheet/table/range、cell 类型、表头单位、日期系统、公式缓存显示值、图表候选及可定位来源。
- 来源边界：XLSX 以 sheet/cell/range 锚点保留来源，日期序列关联 workbook 的 1900/1904 日期系统；CSV 保留原始字符串与 record/field 锚点，不虚构 sheet 或 cell 地址。单位只在表头或可定位元数据明确声明时标记 observed。
- 公式与图表边界：保留公式文本、缓存状态和显示值；缓存缺失时不重算或伪造结果。图表对象/数据范围只作为候选及来源证据，不代表图表适用性判断。
- 静态核验：schema/catalog/fixtures JSON 可解析，schema 的本地引用可定位，4 个 fixture 的输入/结果资产引用一致；正常 XLSX 覆盖 1 个 sheet、1 个表区域、3 列/2 行、日期序列、公式缓存与 1 个图表候选，正常 CSV 保留无 sheet/cell 的 record/field 锚点；两个边界 fixture 分别声明 XLSX_INVALID_PACKAGE 与 CSV_MALFORMED。
- 验收边界：fixtures 是合成预期结构，未运行真实 XLSX/CSV parser、公式引擎或 Excel 渲染；因此 TASK-IN-008 保持进行中，AC-001–AC-030 均未执行。产品运行时、解析库和依赖版本未选定。
- 基线对齐：任务表已列 TabularEvidence 为输出，但“数据对象”表无同名行；本任务只关联既有 IN-008/TASK-IN-008，不增删需求、任务或数据对象行。
- 证据：contracts/tabular-evidence.schema.json、contracts/tabular-evidence.catalog.json、contracts/tabular-evidence.fixtures.json；Excel“需求主表”N47:P47、“可执行任务”L75:M75。

### TASK-IN-009

- Requirement ID：IN-009；P1；矩阵未列前置任务。
- 状态：进行中。已建立 `WebEvidence` Draft 2020-12 草案、目录及正常/边界合成 fixtures，覆盖 title、正文块、嵌套列表、表格、图片引用、metadata、链接引用、来源锚点和原始资产引用。
- 网络安全边界：远程获取输入必须带显式策略；仅允许 HTTP/HTTPS，私网目标默认拒绝，重定向目标重新检查，并显式提供最大重定向、响应大小和允许内容类型。图片、超链接与其他嵌入引用只抽取、不自动请求；脱敏 URL 与拒绝原因写入审计结果。
- 错误映射：复用 ERR-002/INPUT_UNSUPPORTED、ERR-006/PARSE_PARTIAL、ERR-013/ASSET_DOWNLOAD_FAIL、ERR-014/ASSET_UNSAFE_URL；解析失败需携带结构化阶段、原因和来源锚点（若可得）。
- 范围边界：`WebEvidence` 是任务输出名，未列为正式数据对象；不新增数据对象行。HTML/DOM 定位器、解析器、HTTP client、运行时、依赖版本和许可证尚未由实际 PoC 选择；max_redirects、max_response_bytes 与 media-type 集合不设产品默认值。
- 静态核验：三个 JSON 文件可解析；本地 `$ref` 可定位；6 个 fixture 的输入/输出 source ID 与原始资产引用一致，正常/部分/失败状态、策略字段、错误码映射和“外部引用不下载”约束静态核对通过。未找到标准 JSON Schema validator。Fixtures 是合成期望，不是实际网络请求、HTML 解析或 SSRF 防护测试。
- 验收边界：运行时未实现；TASK-IN-009 保持进行中，尚未满足实际解析、HTTP 策略执行或安全配置验证；AC-001–AC-030 均未执行。
- 证据：`contracts/web-evidence.schema.json`、`contracts/web-evidence.catalog.json`、`contracts/web-evidence.fixtures.json`；Excel“需求主表”`N48:P48`、“可执行任务”`L76:M76`；关联 `SEC-002/003/006/016` 与 `ERR-002/006/013/014`。

### TASK-IN-010

- Requirement ID：IN-010；P0；无前置任务。
- 状态：进行中。已建立 StructuredEvidence Draft 2020-12 契约、目录及 JSON/YAML/XML 正常和边界预期 fixture，覆盖对象/数组/mapping/sequence/scalar/XML element/text、类型、来源坐标和焦点路径结果。
- 焦点路径边界：JSON 与 YAML 输入使用 JSON Pointer，XML 使用 XPath 和显式命名空间绑定；路径只返回匹配节点 ID，不剪裁完整证据树。未匹配、语法无效和 unsupported 状态分开表达。
- 格式边界：YAML 保留可观察的 tag 与映射顺序；重复键、未知自定义 tag、别名循环不得静默覆盖或执行构造器。XML 保留 QName、属性和有序混合子节点；DTD/外部实体默认拒绝。源坐标不可得时使用 null 并记录 coverage。
- 静态核验：schema/catalog/fixtures JSON 可解析，34 个 schema 内部引用和 2 个外部文件引用可定位；6 个 fixture 的输入/结果 source/asset/format 对齐，3 种正常格式均有匹配焦点节点，3 种边界格式分别声明 JSON_DUPLICATE_KEY、YAML_UNSUPPORTED_TAG、XML_DTD_PROHIBITED。
- 验收边界：fixtures 是合成预期结构，未运行真实 JSON/YAML/XML parser、XPath 引擎或坐标验证；因此 TASK-IN-010 保持进行中，AC-001–AC-030 均未执行。解析库、运行时和依赖版本未选定。
- 基线对齐：任务表已列 StructuredEvidence 为输出，但“数据对象”表无同名行；本任务只关联既有 IN-010/TASK-IN-010，不增删需求、任务或数据对象行。
- 证据：contracts/structured-evidence.schema.json、contracts/structured-evidence.catalog.json、contracts/structured-evidence.fixtures.json；Excel“需求主表”N49:P49、“可执行任务”L77:M77。

### TASK-IN-011

- Requirement ID：IN-011；P0；无前置任务。
- 状态：进行中。已建立 ImageEvidence Draft 2020-12 契约、目录及正常/边界预期 fixture，覆盖原始/显示尺寸、格式、视觉元素候选、OCR 文本、主色比例、布局区域和 bbox 来源锚点。
- 用途与判断边界：content_source、style_reference、image_to_pptx 或 unassigned 必须由调用方声明；解析层不从图像外观推断业务用途。视觉标签、OCR 和布局都是带 confidence 的候选，不是确定事实；模型 ID/版本未选定时保持 null。
- 坐标边界：bbox 显式声明 raw/display pixel 或 normalized_0_to_1 空间；原始尺寸和方向不被静默改写。边界案例保留 IMAGE_DECODE_FAILED 和 IMAGE_UNSUPPORTED_FORMAT；后者是未选型实现的预期 partial 状态，不代表项目已验证 SVG 不支持。
- 静态核验：schema/catalog/fixtures JSON 可解析，31 个 schema 内部引用及 2 个外部文件引用可定位；3 个 fixture 的输入/结果 source、asset 与 usage 对齐；正常案例包含 2 个视觉候选、2 个 OCR 区域、3 个色值和 2 个布局区域，bbox 均位于 1280×720 合成源图范围内。
- 验收边界：正常 fixture 未绑定真实图像，所有尺寸/检测框/置信度均为合成占位；未运行解码器、OCR、视觉模型、色彩抽取或布局分析。因此 TASK-IN-011 保持进行中，AC-001–AC-030 均未执行；图像依赖、模型、版本和许可未选定。
- 基线对齐：任务表已列 ImageEvidence 为输出，但“数据对象”表无同名行；本任务只关联既有 IN-011/TASK-IN-011，不增删需求、任务或数据对象行。
- 证据：contracts/image-evidence.schema.json、contracts/image-evidence.catalog.json、contracts/image-evidence.fixtures.json；Excel“需求主表”N50:P50、“可执行任务”L78:M78。

### TASK-IN-012

- Requirement ID：IN-012；P0；无前置任务。
- 状态：进行中。已建立 AssetInventory Draft 2020-12 契约、目录和正常/边界预期 fixture，覆盖图片、SVG、视频、字体及模板的 Asset ID、相对路径、声明/检测类型、media type、体积/hash 与扫描状态。
- 目录边界：本任务只登记资产，不代替媒体内容解析。默认不跟随符号链接/Windows reparse point；本地路径必须限制在批准 root 内。绝对开发机路径不进入清单证据。
- 远程与敏感定位符：远程 URI 默认只登记，不联网抓取；未获取内容时 size/hash/MIME 保持 unknown，URL 凭据和敏感 query 必须移除或 redacted。部分扫描失败保留已成功条目并附 issue，不静默跳过。
- 静态核验：schema/catalog/fixtures JSON 可解析，21 个 schema 内部引用及 2 个外部文件引用可定位；3 个 fixture 对齐 source/target/asset，正常案例有 4 种资产类别；边界分别表达 ASSET_PATH_UNSAFE 和 remote_not_fetched/REMOTE_ASSET_NOT_FETCHED，未发起网络请求。
- 验收边界：全部路径、体积、Asset ID 和 hash 均为合成数据；未运行目录遍历、文件签名识别、哈希、链接防护或远程 adapter。因此 TASK-IN-012 保持进行中，AC-001–AC-030 均未执行；扫描实现和依赖尚未选定。
- 基线对齐：任务表已列 AssetInventory 为输出，但“数据对象”表无同名行；本任务只关联既有 IN-012/TASK-IN-012，不增删需求、任务或数据对象行。
- 证据：contracts/asset-inventory.schema.json、contracts/asset-inventory.catalog.json、contracts/asset-inventory.fixtures.json；Excel“需求主表”N51:P51、“可执行任务”L79:M79。

### TASK-IN-013

- Requirement ID：IN-013；P1；矩阵未列前置任务。
- 状态：进行中。已建立 `StyleReference` Draft 2020-12 契约、目录与 4 个合成正常/边界/失败 fixture，分别覆盖颜色、字体倾向、构图、密度、图像处理、装饰语言及逐项来源锚点。
- 观察与复用边界：字体记录为视觉倾向，不冒充具体字体识别；每个候选保留 confidence 与 image-region SourceAnchor。未观测/不支持特征显式列入 coverage，不设识别阈值。
- 权利边界：用户提供状态、复制授权证据和 license 状态分别记录。StyleReference 仅保存保护元素的类别、位置与处理决定，不复制 logo/品牌标记/受保护文字或插画；权利未知或未授权时排除，用户提供且有授权证据也只可进入独立资产/许可流程。
- 与 IN-011 的关系：复用 `SourceAnchor` 定位约定，并允许与 `ImageEvidence` 候选关联；矩阵未声明 TASK-IN-011 为前置，本任务不新增依赖。StyleReference 不在数据对象表中，本任务不新增数据对象行。
- 静态核验：三个 JSON 文件可解析，本地 `$ref` 可定位；4 个 fixture 的 source/asset 引用、六类 coverage、正常/部分/失败状态、ERR-002/006 映射、权利门控与处理器未执行标记静态核对通过。未运行标准 JSON Schema validator、真实图像解码/OCR/视觉模型或许可授权流程。
- 验收边界：fixtures 是合成预期；真实图片解析、特征抽取和版权/许可边界执行尚无运行时证据。因此 TASK-IN-013 保持进行中，AC-001–AC-030 均未执行；产品架构、运行时、模型/依赖版本与许可未选定。
- 证据：`contracts/style-reference.schema.json`、`contracts/style-reference.catalog.json`、`contracts/style-reference.fixtures.json`、`contracts/image-evidence.schema.json`；Excel“需求主表”`N52:P52`、“可执行任务”`L80:M80`；关联 `SEC-013/014`。

### TASK-IN-014

- Requirement ID：IN-014；P0；矩阵中无前置任务。
- 状态：进行中。已建立 SourceBundle Draft 2020-12 契约、目录及多源冲突/重复 ID 预期 fixture，覆盖 text/file/URL 来源、source_id、输入顺序、优先级状态、原始资产引用、冲突和去重候选。
- 优先级边界：来源优先级引用 DEC-004/TASK-DEC-004；现有 GOV-006 配置基线将其标记为 unresolved，TASK-DEC-004 仍依赖 RES-031。因此不定义全局 precedence/default；caller 未给明确规则时保留冲突，不自动选 winner。
- 冲突与去重边界：每条冲突保留 source/claim/value/anchor；仅显式 user selection/merge 可标记 resolved。SHA-256 匹配只生成 duplicate candidate；字节比对或明确确认前不选 canonical，也不删除任何来源。
- 静态核验：schema/catalog/fixtures JSON 可解析，25 个 schema 内部引用和 2 个外部文件引用可定位；正常 fixture 保留 3 个来源、3 条冲突 claims、1 个 hash duplicate candidate；重复 source_id 边界返回 SOURCE_ID_DUPLICATE。
- 验收边界：所有来源内容、哈希及冲突值均为合成预期；未运行真实文件/URL/text 解析、优先级决策、冲突检测器或去重引擎。因此 TASK-IN-014 保持进行中，AC-001–AC-030 均未执行。
- 基线对齐：任务表已列 SourceBundle 为输出，但“数据对象”表无同名行；本任务只关联既有 IN-014/TASK-IN-014，不增删需求、任务或数据对象行。
- 证据：contracts/source-bundle.schema.json、contracts/source-bundle.catalog.json、contracts/source-bundle.fixtures.json；Excel“需求主表”N53:P53、“可执行任务”L81:M81。
- IN-016 类型对齐：source_claim 与 conflict claim 的来源锚点改用结构化 SourceAnchor；旧 PDF 定位保留原始字符串并标记 partial，不推测段落索引基准。

### TASK-IN-015

- Requirement ID：IN-015；P0；矩阵中无前置任务。
- 状态：进行中。已建立 InputIssue Draft 2020-12 契约、目录及正常/边界预期 fixture，涵盖加密、损坏、格式签名不匹配、文件大小限制、归档展开限制和不支持格式。输入阈值仅来自 fixture 的显式调用方策略，不是产品默认。
- 错误码映射：仅复用矩阵已登记的 ERR-002/INPUT_UNSUPPORTED、ERR-003/INPUT_PASSWORD_PROTECTED、ERR-004/INPUT_CORRUPT、ERR-005/ZIP_BOMB_LIMIT；格式签名不匹配和普通文件大小限制没有精确代码，标记 registry review，不新增代码或错配近似代码。schema 将 ERR-001–005 与原因码及问题类型绑定。
- 输入边界：完整性状态与格式判定分开；Office/OOXML 的有效类型不能仅由 ZIP 魔数确定。所有边界资产都不能安全解析，因此批次预期为 blocked；不得静默跳过。
- 静态核对：JSON 可解析，schema 外部 ID 引用及 catalog 文件引用可定位；正常 fixture 为 ready，六项边界 fixture 均有结构化问题，错误码和 issue 引用一致。未运行 JSON Schema 实例验证器、真实解析器、加密探测、签名识别、解压预算检查或 AC-001–AC-030。
- 基线对齐：任务输出为 InputIssue[]；“数据对象”表无 InputIssue 行，本任务不增删需求、任务或数据对象。
- 证据：contracts/input-issue.schema.json、contracts/input-issue.catalog.json、contracts/input-issue.fixtures.json；Excel“需求主表”N54:P54、“可执行任务”L82:M82。

### TASK-IN-016

- Requirement ID：IN-016；P0；矩阵中无前置任务。
- 状态：进行中。已建立 SourceAnchor Draft 2020-12 契约、目录与正常/边界预期 fixture，覆盖文本、DOCX、PDF、XLSX/CSV、结构化文件、图片、URL 与 PPTX 定位。
- 统一锚点信封保留 source_id、asset_id、原生定位文本、定位联合体和 located/partial/unavailable 状态；未知页码、未抓取 URL、索引基准不明和 parser failure 各自有结构化原因。格式专属原始 anchor schema 保持原职责；SourceBundle claim/conflict claim 已引用统一对象。
- 错误边界：实际解析器部分失败复用矩阵 ERR-006/PARSE_PARTIAL；未测页码、未抓取 URL 和未规范化定位使用 SourceAnchor 局部 reason，不新增全局错误码。旧 IN-014 PDF 定位未声明索引基准，原文保留并标 partial。
- 静态核对：2 个 schema 中 51 个引用可定位；正常 fixture 含 8 种 locator，边界 fixture 含 partial/unavailable 及 ERR-006。SourceBundle 输入、结果和冲突 claim 的 anchor 均为对象且 source_id/asset_id 对齐；未运行 JSON Schema 实例验证器、真实解析器、网页抓取或 AC-001–AC-030。
- 基线对齐：任务输出为 SourceAnchor；“数据对象”表无同名行，本任务不增删需求、任务或数据对象行。
- 证据：contracts/source-anchor.schema.json、contracts/source-anchor.catalog.json、contracts/source-anchor.fixtures.json、contracts/source-bundle.schema.json/catalog.json/fixtures.json；Excel“需求主表”N55:P55、“可执行任务”L83:M83。

### TASK-TPL-001

- Requirement ID：TPL-001；P0；矩阵列明无前置任务。
- 状态：进行中。已建立语言/运行时无关的 TemplateSourceRecord 草案，登记来源项目/文件/用户上传、来源提交、项目许可证与模板许可证、模板版本、带哈希范围的 SHA-256、带单位/坐标语义的页面尺寸，以及 master/layout/theme 状态。
- 来源边界：固定对照 PPT Master 2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d、Presenton 35bf44290f821323e003da854f78ffcb0e918167、ai-agent-ppt c3605ebc487fc6c7d4f4139761e46d7021cd656c。PPT Master 多画布规格不能推断成单个模板尺寸；Presenton 的 1280x720 是来源坐标系；ai-agent-ppt 的 pitch JSON 是 13.33x7.5 英寸画布，布局定义为分开的 JSON。
- 真实 PPTX 样例：只读检查 python-pptx 固定提交 278b47b1dedd5b46ee84c286e77cdfb0bf4594be 的 default.pptx，SHA-256 e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34；ZIP/XML 可定位 1 个 master、11 个 layout、1 个 theme，master 关系均指向存在的 layout/theme 部件，sldSz 为 9144000×6858000 EMU。样例文件未复制进产品树或声明为项目依赖。
- 许可/版本边界：上游项目根许可证与模板资产许可分开；模板许可和模板自身版本无充分证据的记录保持 unknown。来源提交与模板版本是两个字段，文件时间不用于推断。
- 基线对齐：更新既有 TPL-001/TASK-TPL-001 状态和证据；数据对象表已有 TemplatePack，但未列 TemplateSourceRecord。本任务契约作为任务输出，不新增/删除需求、任务或数据对象行；与 TemplatePack.source 的正式映射及决策引擎查询、评分、实例化运行时仍待后续任务。
- 静态核验：3 份契约 JSON 可解析，schema 本地引用可定位；5 个 fixture 的必需字段、TPL-001/TASK-TPL-001 追溯 ID、证据引用及 4 个来源文件/样例 SHA-256 一致。真实 PPTX ZIP/XML 部件与关系盘点得到 1 master、11 layouts、1 theme 和页面尺寸。需求/任务总数仍为 308/453；矩阵仅改需求行 110 的 N:P、任务行 178 的 L:M 共 5 个单元格，数据对象表和验收矩阵无变化。工作簿保留 47 个 package parts、20 张表、8 个表格、115 个公式、29 个数据验证、28 个条件格式和 1 个合并单元格；styles.xml 哈希不变，另外 7 张受重新序列化的非目标工作表渲染图与原图 SHA-256 相同，需求/任务目标行也已前后渲染对照。任务状态计数为 2 已完成、41 进行中、410 未开始；AC-001–AC-030 未执行。未运行上游应用、YoloongPPT parser、PPTX 渲染、上传链路或 JSON Schema 标准实例验证。
- 证据：contracts/template-source-record.schema.json、contracts/template-source-record.catalog.json、contracts/template-source-record.fixtures.json；Excel“需求主表”N110:P110、“可执行任务”L178:M178；research/P01/README.md、research/P03/README.md、research/P04/README.md。

### TASK-TPL-002

- Requirement ID：TPL-002；P0；矩阵列明无前置任务。
- 状态：进行中。建立 MasterSpec Draft 2020-12 草案契约、来源目录与 4 个 crosswalk/specimen fixture，覆盖背景、shape、text style、clrMap、master-layout/theme relationship，以及 transition/timing 的直接声明和逐目标 slide 继承结果状态。
- 标准边界：Master 直接缺少 p:transition/p:timing 不代表目标 slide 的有效效果为空；必须保留 slide/layout/master 覆盖链。真实样例无 slide XML 部件，effective resolution 记为 no_target_slide_parts，不推断空 transition/timing。
- 来源对照：PPT Master 固定提交有 PPTX 导入、master/layout roster/inheritance graph、clrMap resolver 与部分 txStyles reader；Presenton 固定提交有 RawSlideLayouts/theme 及沿 slide→layout→master 读取字体声明的路径，但不是完整 MasterSpec；ai-agent-ppt reviewed template 配置消费语义 JSON 与分开的 layout JSON，没有 native MasterSpec 输入字段。以上仅静态源码 crosswalk，不表示上游应用已运行。
- 真实 PPTX：只读检查 python-pptx 固定提交 278b47b1dedd5b46ee84c286e77cdfb0bf4594be 的 default.pptx，SHA-256 e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34；定位 1 master、5 个 p:sp、12 项 clrMap、11 个可解析且目标存在的 layout 关系、1 个 theme 关系、title/body/other 样式层级。包内 0 个 slide XML 部件，故未解析逐页继承结果。样例不作为产品依赖或技术选型。
- 数据对象对齐：矩阵“数据对象”表已有 TemplatePack.masters，但没有 MasterSpec 独立对象行；契约只作为 TASK-TPL-002 输出，正式字段映射与消费方式待后续任务，不增删需求、任务或数据对象行。
- 静态核验：契约 JSON 可解析且本地 schema 引用存在；4 个 fixture 的任务追溯 ID、证据 ID、关系目标与状态边界一致。未运行标准 JSON Schema validator、YoloongPPT parser、Office 渲染、模板上传链路或 AC-001–AC-030。
- 证据：contracts/master-spec.schema.json、catalog.json、fixtures.json；Excel“需求主表”N111:P111、“可执行任务”L179:M179；research/P01/README.md、research/P03/README.md、research/P04/README.md。

### TASK-TPL-003

- Requirement ID：TPL-003；P0；矩阵标记无前置任务。
- 状态：进行中。建立 `LayoutTemplate` Draft 2020-12 契约草案、来源 crosswalk 与真实 PPTX fixture，记录 layout name/type、原始属性、placeholder type/index、直接 EMU 几何、layout→master 关系及 master-shape 可见性解释状态；`slots` 集合现引用 TPL-004 的强类型 `LayoutSlot` 项。
- 来源对照：PPT Master 固定提交 `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d` 有原生 master/layout roster、继承关系、placeholder 与 `showMasterSp` 解析规则；Presenton 固定提交 `35bf44290f821323e003da854f78ffcb0e918167` 的 `RawSlideLayouts` 保留来源元素/位置/尺寸等，但依赖预览和后续语义认证；ai-agent-ppt 固定提交 `c3605ebc487fc6c7d4f4139761e46d7021cd656c` 的 `LayoutLoader` 消费抽象 JSON layout，不等同于原生 PPTX layout parser。均为源码静态 review，未运行上游程序。
- 真实 PPTX：只读盘点 python-pptx 固定提交 `278b47b1dedd5b46ee84c286e77cdfb0bf4594be` 的 `default.pptx`，SHA-256 `e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34`；确认 1 master、11 layouts、1 theme、0 slide parts；fixture覆盖直接几何与省略 type/index/visibility 属性。layout 几何未声明时保留为 direct `not_present`，对应 master geometry 解析记为 unresolved；没有推断成零尺寸或最终继承结果。
- 可见性边界：OOXML 原属性保留为 `showMasterSp`。PPT Master 源码把省略属性按 true 解释只记录为该适配器源码规则，不是 YoloongPPT 产品默认；产品级规范化保持 pending。没有 slide parts，不报告具体页面的有效继承可见性。
- 数据对象对齐：在既有 LayoutTemplate 数据对象行登记 Schema 草案版本，不新增/删除需求、任务或数据对象。字段 layout_id、page_types、slots、constraints、capacity、backend_support 均保留；Slot 项结构由 layout-slot.schema.json 定义，TPL-006 LayoutApplicability 和 TPL-007 CapacityRules 已接入；容量实测、产品 parser/runtime 与后端能力仍待验证。
- 静态核验：Schema、catalog、fixtures JSON 解析；本地 Schema 引用及样例结构、11 layout roster、master 关系、直接几何和原始属性状态静态核对。未运行 JSON Schema 标准 validator、YoloongPPT parser、PPT Master/Presenton/ai-agent-ppt 程序、Office 渲染或 AC-001–AC-030。
- 证据：`contracts/layout-template.schema.json`、`contracts/layout-template.catalog.json`、`contracts/layout-template.fixtures.json`；Excel“需求主表”`N112:O112`、“可执行任务”`L180:M180`、“数据对象”`D29/J29`；`research/P01/README.md`、`research/P03/README.md`、`research/P04/README.md`。

### TASK-TPL-004

- Requirement ID：TPL-004；P0；矩阵未列前置任务。
- 状态：进行中。为既有 `LayoutSlot` 数据对象建立 Draft 2020-12 契约，覆盖 `slot_id, role, bounds, content_types, required, repeatable, capacity, style, overflow_policy`；值可按来源声明、明确映射或 unknown 表达，未知字段必须保留空值和原因，不静默推断。
- LayoutTemplate 集成：`contracts/layout-template.schema.json` 的 `slots.items` 现在引用 `contracts/layout-slot.schema.json`；现有 LayoutTemplate fixtures 保持 pending，因为尚未运行产品 parser 将整个 layout placeholder roster 转成 LayoutSlot。
- 来源对照：PPT Master 固定 commit `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d`（MIT）可静态观察 placeholder role 映射、直接几何及部分文本样式；Presenton 固定 commit `35bf44290f821323e003da854f78ffcb0e918167`（Apache-2.0）记录 raw positions/sizes/styles，并通过模型分析语义区、可重复区域与容量；ai-agent-ppt 固定 commit `c3605ebc487fc6c7d4f4139761e46d7021cd656c`（MIT）提供抽象 `LayoutNode.slot/style`，不等同原生 PPTX layout parser。三者的抽象差异和字段覆盖见 `contracts/layout-slot.catalog.json`。
- 真实 PPTX 样例：python-pptx 固定 commit `278b47b1dedd5b46ee84c286e77cdfb0bf4594be` 的 `default.pptx`，SHA-256 `e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34`；layout1 的 `ctrTitle` placeholder 有直接 EMU bounds。样例只有 1 master、11 layouts、0 slide parts，因此 required/repeatable/capacity/style inheritance/overflow 保持 unknown。
- 数据对象对齐：只更新既有“数据对象”`LayoutSlot` 行并说明 `LayoutTemplate.slots` 集成，不新增或删除矩阵行。`LayoutSlot.capacity` 现引用 TPL-007 `CapacityRules`；容量阈值和产品测量仍待验证。
- 静态验证范围：JSON 解析、本地 `$ref` 和 fixture 状态/边界检查；不表示标准 JSON Schema validator、YoloongPPT parser/runtime、源应用执行、Office 渲染或 AC-001–AC-030 已通过。
- 证据：`contracts/layout-slot.schema.json`、`contracts/layout-slot.catalog.json`、`contracts/layout-slot.fixtures.json`、`contracts/layout-template.schema.json`、`contracts/layout-template.fixtures.json`；Excel“需求主表”`N113:P113`、“可执行任务”`L181:M181`、“数据对象”`D30/J30`；`research/P01/README.md`、`research/P03/README.md`、`research/P04/README.md`。

### TASK-TPL-005

- Requirement ID：TPL-005；P0；矩阵未列前置任务。
- 状态：进行中。为既有 DesignTokens 数据对象建立语言/运行时无关的 Draft 2020-12 契约，覆盖 fonts、type scale、colors、spacing、radius、border、shadow、backgrounds、image treatment、chart style 和 table style；字段使用 declared/mapped/partial/unknown/unsupported/not_present 状态，未知值必须为 null 并说明原因。
- 来源对照：固定 PPT Master 源码读取部分 OOXML 颜色与字体字段；Presenton 从 raw layout 统计并选择语义主题角色，记录其注入合成颜色和确定性回退；ai-agent-ppt 使用抽象模板 colors/fonts/spacing 与 CSS 样式映射。三种来源模型不同，不据此选择 YoloongPPT 产品运行时或默认值。
- 真实 PPTX：只读核对既有 python-pptx default.pptx（SHA-256 e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34；theme part SHA-256 4c3412087e8fa20cf5642f42e69f1e733881c28611a2bdd4622654ee313d214e）。样例含 1 master、11 layouts、1 theme、0 slides、0 charts、0 media；保留 12 个原始颜色槽、字体方案、母版背景引用、格式样式计数及 tableStyles 默认 GUID。字号比例、通用间距、圆角、阴影语义、图片处理及图表样式仍 unknown/partial，不补入假值。
- fallback 边界：Presenton 无颜色时注入的四个合成颜色和 LLM 失败后的确定性角色选择，仅作为来源观察记录，不能成为 YoloongPPT 产品 fallback。颜色源槽与语义角色分开；空字体字符串原样保留。
- 数据对象对齐：只更新既有“数据对象”DesignTokens 行；不新增或删除需求、任务或数据对象。契约尚未定义独立 token-set ID；若后续将其确定为独立持久化实体，须先按 GOV-007 记录 ID 映射。
- 静态核验：检查 Schema/catalog/fixture JSON、Schema 本地引用及每个分类的 unknown/partial 不变量；当前工作区没有 Draft 2020-12 标准 validator，因此不宣称标准 Schema 实例验证通过。没有运行 YoloongPPT parser/runtime、三种上游程序、Office 渲染、真实图表/图片案例或 AC-001–AC-030。
- 证据：contracts/design-tokens.schema.json、contracts/design-tokens.catalog.json、contracts/design-tokens.fixtures.json；Excel“需求主表”N114:P114、“可执行任务”L182:M182、“数据对象”D31/J31；research/P01/README.md、research/P03/README.md、research/P04/README.md。

### TASK-TPL-006

- Requirement ID：TPL-006；P0；矩阵未列前置任务。
- 状态：进行中。为 PDR/矩阵中的 SlideType 与既有 LayoutTemplate 建立 LayoutApplicability Draft 2020-12 关系契约，接入 LayoutTemplate.page_types，保留 candidate/verified/incompatible/unknown、来源 layout type、限制、证据和验证状态。
- Taxonomy：以 PDR DEC-017 与矩阵“0-1全链路”S16 为基线，覆盖封面、章节、概览、图文、数据、流程、时间线、对比、表格、KPI、SWOT、总结；基线使用“等”，契约保留有证据的 extension，不声明这 12 项是封闭全集。
- 来源对照：PPT Master 提供 OOXML raw layout type/name/placeholders，但无统一 SlideType 映射；Presenton 的 RawSlideLayout/SlideLayout 提供描述、元素和语义组件，未找到 PDR 对应的固定页面类型字段；ai-agent-ppt 提供 title/comparison/timeline/chart/image-text 等抽象 JSON layout，映射只登记候选。原始类型、语义候选和产品验证状态分开存储。
- 真实 PPTX：复用既有 python-pptx default.pptx 固定样例和 LayoutTemplate fixtures。Title Slide/raw type=title 与 ctrTitle/subTitle 只形成封面 candidate；Title and Content/raw type=obj 因语义可能对应概览、数据、表格、流程等而记 unknown。样例无 slide parts，未验证页面适配。样例文件 SHA-256 为 e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34；上游 python-pptx 源码 commit 与 LayoutTemplate fixture 地址见 contracts/layout-template.fixtures.json。
- 约束：关系缺失或 unknown 不能当作不适用；只有有证据的 incompatible 才能排除。当前 slot/placeholder 观察不自动成为硬性内容要求；字符数、行数、最小字号等容量约束由 TPL-007 CapacityRules 记录。DEC-030 可查询本关系后继续容量、素材与 backend 检查；本任务不实施候选打分。
- 数据对象对齐：LayoutApplicability 嵌入既有 LayoutTemplate.page_types，以 layout_id + SlideType 组合识别，不新增需求、任务、数据对象行或独立 GOV-007 ID。更新既有 LayoutTemplate schema/catalog/fixtures 以移除 TPL-006 deferral；TPL-007 的容量实测和产品 parser/runtime 验证仍待后续。
- 静态核验：JSON 解析、本地及跨文件 Schema 引用、taxonomy 全覆盖、两条真实样例映射状态、父子 layout_id 一致性与 verified 必须有运行证据的边界检查。当前没有 Draft 2020-12 标准 validator；不宣称标准实例验证或产品 parser、上游程序、Office 渲染、AC-001–AC-030 已通过。
- 证据：contracts/layout-applicability.schema.json、layout-applicability.catalog.json、layout-applicability.fixtures.json、contracts/layout-template.schema.json/catalog.json/fixtures.json；Excel“需求主表”N115:P115、“可执行任务”L183:M183、“数据对象”D29:J29；PDR DEC-017、DEC-030 与矩阵 S16。

### TASK-TPL-007

- Requirement ID：TPL-007；P0；矩阵未列前置任务。
- 状态：进行中。建立语言/运行时无关的 Draft 2020-12 `CapacityRules` 契约，作为既有 `LayoutTemplate.capacity` 与 `LayoutSlot.capacity` 的内嵌记录；按 layout/slot 分别标识，不新增数据对象行。
- 维度：显式覆盖字符数、行数、列表项数、图片数、表格数、图表数和最小字号，并允许有证据的扩展维度。每个维度记录状态、单位、比较方向、限值、依据、证据和原因；未知或未评估时限值为空。未把 slot 数量相加为 layout 容量，也未把几何或 placeholder 数量转成安全字符数。
- 来源对照：固定 PPT Master 源码能读取占位符几何和部分文本样式，但无通用容量规则；固定 Presenton 源码将安全文本长度/增长约束与模型分析和预览认证关联，本任务未执行该流程；固定 ai-agent-ppt 抽象 LayoutNode 未发现容量字段。源版本和上游许可证记录在 catalog，源码只做静态 review。
- 真实 PPTX：复用 python-pptx 固定 commit `278b47b1dedd5b46ee84c286e77cdfb0bf4594be` 的 `default.pptx`，SHA-256 `e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34`；样例有 1 master、11 layouts、0 slide parts。Title placeholder 的 EMU 几何不足以给出字符数或最小字号；样例模板资产自身许可证继续标记 unknown。
- 容量边界：目前真实 PPTX 与上游来源都没有被 YoloongPPT parser 和目标渲染器装载真实内容并测量；fixtures 中七个基线维度均为 unknown，不定义默认上限。要记录实测值，需保留分析器/运行时、版本、渲染器、版本、字体环境和重现证据。该契约不实现自动排版、溢出策略或 DEC-030 打分。
- 静态核验：Schema/catalog/fixtures 及布局/槽位集成 JSON 可解析，本地引用、scope ID 和 unknown 限值/原因边界静态核对。未运行标准 JSON Schema validator、容量测量器、YoloongPPT parser/runtime、Office 渲染或 AC-001–AC-030。
- 证据：`contracts/capacity-rules.schema.json`、`contracts/capacity-rules.catalog.json`、`contracts/capacity-rules.fixtures.json`、`contracts/layout-template.schema.json/catalog.json/fixtures.json`、`contracts/layout-slot.schema.json/catalog.json/fixtures.json`；Excel“需求主表”`N116:P116`、“可执行任务”`L184:M184`、“数据对象”`D29:J30`；PDR 段落 139、`research/P01/README.md`、`research/P03/README.md`、`research/P04/README.md`。

### TASK-TPL-008

- Requirement ID：TPL-008；P0；矩阵未列前置任务；相关链路为 S24，DEC-032 仍有其自身依赖与执行任务。
- 状态：进行中。建立任务级 `TemplateFieldMap` 草案，使用矩阵 S24 的六类角色（标题、正文、图片、图表、表格、注释）作为唯一当前 canonical role 集合；英文 role ID 仅为这六类的契约键。每条记录保留来源版本、路径、字段位置、原字段名/原值、映射状态和证据引用。
- 命名规则：`declared` 表示源字段已声明基线角色，`mapped` 表示固定来源 alias 有证据地映射，`ambiguous` 表示证据支持多个候选但不能唯一选择，`unmapped` 表示来源字段已知但 S24 没有可证明的目标，`unknown` 表示来源语义或映射规则尚未验证。`subTitle` 不自动并入 `title` 或 `body`。
- 来源对照：PPT Master 固定版本的 `ctrTitle→title` 是 adapter-specific crosswalk；Presenton 的 `RawSlideLayouts` 语义组件需模型分析和预览认证，当前保留 unknown；ai-agent-ppt 固定 title layout 的 `slot="title"` 是来源声明；python-pptx 固定真实 `default.pptx` 样例的 `ctrTitle` 映射至 title，`subTitle` 因不在 S24 角色集中保持 unmapped。以上仅为源码/文件静态对照，未运行上游应用。
- 数据对象对齐：矩阵“数据对象”无 `TemplateFieldMap` 独立行，因此只按 TASK-TPL-008 输出交付任务级契约；不新增、删除或改动需求、任务、数据对象行，也不分配全局实体 ID。
- 当前边界：P03 语义模型流程、P01/P04 上游程序、YoloongPPT 映射运行时、DEC-032 决策执行、模板查询/评分/实例化、Office 渲染仍未验证。真实样例没有 slide parts，不能证明逐页绑定行为。
- 静态核验：三个契约 JSON 均解析成功；5 个 fixture 的 Requirement/Task ID、S24 六角色、四类必需来源覆盖、证据引用及 mapped/declared 与 unknown/unmapped 状态约束一致。此为静态一致性检查；未运行 Draft 2020-12 标准 Schema validator、上游应用、YoloongPPT parser/runtime、Office 渲染或 AC-001–AC-030。
- 证据：`contracts/template-field-map.schema.json`、`contracts/template-field-map.catalog.json`、`contracts/template-field-map.fixtures.json`；Excel“需求主表”`N117:P117`、“可执行任务”`L185:M185`、“0-1全链路”`A26:D26`；`contracts/layout-slot.catalog.json`、`contracts/layout-slot.fixtures.json`、`contracts/layout-template.fixtures.json`、`research/P01/README.md`、`research/P03/README.md`、`research/P04/README.md`。

### TASK-TPL-009

- Requirement ID：TPL-009；P0；矩阵未列前置任务。
- 状态：进行中。建立任务级 `TemplateImportReport` 契约，独立记录输入包 master/layout/theme/slide inventory、输出重建页、部件保留状态、包结构往返与页面渲染结果。报告 `complete` 必须有至少一个输出页、master/layout/theme 三类结构证据及 package roundtrip 通过；page render 单独报告，不作为 TPL-009 额外完成门槛。
- 来源对照：PPT Master 固定 `manifest.py` 盘点资源、主题和继承关系，但明确不把任意 PPTX shape 转成 SVG template；Presenton 固定 Template V2 流程依赖源 PPTX、逐页预览和模型认证，再进行 layout hydration 与导出，当前未证实输出逐部件保留源 master/layout/theme；ai-agent-ppt 使用抽象 LayoutNode JSON，不能据此证明原生 PPTX 模板导入保留；python-pptx 固定 default.pptx 真实样例有 1 master、11 layouts、1 theme、0 slide parts。
- 数据对象对齐：矩阵“数据对象”表没有 `TemplateImportReport` 独立行，仅按 TASK-TPL-009 输出任务级报告；不新增、删除或改动需求、任务、数据对象行。
- 执行环境：Docker 启动故障已定位为 stale Windows AF_UNIX socket（reparse tag `0x80000023`）导致后端清理失败；保留旧 socket 条目备份后重启 Docker Desktop。`docker desktop status` 与 `docker info` 确认 Engine running（27.4.0，环境观测）；`scripts/project.ps1 start` 成功，运行 `yoloongppt-workspace-1`，image ID `sha256:e3dda207b44bf716a50f24cd688236fe7b2f82e055bceda871859e4f204cf2c4`，将 `F:/YoloongPPT` 以读写 bind mount 到 `/workspace`。容器仅含 Debian 12、bash、git 和 ca-certificates；没有 Node/Python 产品运行时，此版本观测不构成产品技术选型。
- 当前证据：项目 Docker 开发容器已可用，但尚无模板导入/重建运行时；固定 sample 无 slide parts，故仍无法据此重建页面。契约 fixture 把 package inventory 标为局部证据，将 reconstruction、master/layout/theme output comparison、round-trip、render 全部保持 not_run；TPL-009 未通过验收。
- 静态核验：三个 JSON 文件解析、TPL-009/TASK-TPL-009 追溯 ID、四个来源 crosswalk ID、真实样例 inventory（1 master/11 layouts/1 theme/0 slides）、fixture 未夸大重建/保留/round-trip/render 状态及 8 个固定源码文件 SHA-256 均核对通过。该检查不是 Draft 2020-12 实例验证或实际模板导入验证。
- 证据：`contracts/template-import-report.schema.json`、`contracts/template-import-report.catalog.json`、`contracts/template-import-report.fixtures.json`；Excel“需求主表”`N118:P118`、“可执行任务”`L186:M186`；PDR 段落 141；`research/P01/README.md`、`research/P03/README.md`、`research/P04/README.md`；`contracts/template-source-record.catalog.json`、`contracts/layout-template.catalog.json`。

### TASK-CNT-001

- Requirement ID：CNT-001；P0；矩阵中无前置任务。
- 状态：进行中。已建立 FactConstraintSet Draft 2020-12 契约、目录和正常/边界预期 fixture；实体、金额/比例、日期、单位、指标、引文和引用分别记录原始表述、可选规范值、证据 ID 与 SourceAnchor。
- 冲突与缺失：冲突保留全部 claim；DEC-004 未决时不选 winner。缺失值保持空并引用 ERR-009/MISSING_FACT；显式假设必须关联已有 assumption_id；解析部分失败使用 ERR-006/PARSE_PARTIAL。允许的改写转换仅记录 PresentationContext 明示项。
- 静态核对：32 个 schema 引用和 6 个目录文件引用可定位；正常 fixture 含 10 项保真约束，边界 fixture 覆盖 8%/9% 冲突、缺失续约日期、显式 12% 假设和部分解析失败，evidence/source/anchor 互相匹配。未运行 JSON Schema 实例验证器、事实抽取/改写引擎或 AC-001–AC-030。
- 基线对齐：“数据对象”表已有 FactConstraintSet 行；仅更新状态和备注，不新增需求、任务或数据对象行。Schema版本仍为“待定义”，草案未获批准。
- 证据：contracts/fact-constraint-set.schema.json、catalog.json、fixtures.json；Excel“需求主表”N56:P56、“可执行任务”L84:M84、“数据对象”I9:J9。

### TASK-CNT-002

- Requirement ID：CNT-002；P0；矩阵中无前置任务。
- 状态：进行中。已建立 DataBinding Draft 2020-12 契约、目录与正常/边界预期 fixture，单个 binding 关联一个 CNT-001 fact，并由正文、表格单元格和图表序列共同引用；consumer 不保存独立数字或展示文本。
- 冲突与缺失：复用 CNT-001 的 `growth_rate` 正常值、`revenue_growth` 8%/9% 未解决冲突及缺失的 `renewal_date`。冲突保留全部 claim 和 SourceAnchor，DEC-004 未决时 blocked 且不选值；缺失值 blocked 且为空，由上游 FactConstraintSet 保留 ERR-009/MISSING_FACT。本契约不新增全局错误码。
- 静态核对：17 个 schema `$ref` 与 6 个目录文件引用可定位；3 个 fixture 的 claim/evidence/anchor 与 CNT-001 上游 fixture 一致，数字与已授权转换规则匹配，正文/表格/图表引用同一个 binding_id 且消费者不携带数值。未运行 JSON Schema 实例验证器、DataBinding 运行时、实际内容生成、PPTX 写入/渲染或 AC-001–AC-030。
- 基线对齐：矩阵“数据对象”表没有 DataBinding 行；本任务不新增需求、任务或数据对象行，Schema 版本仍为“待定义”，草案未获批准。
- 证据：contracts/data-binding.schema.json、contracts/data-binding.catalog.json、contracts/data-binding.fixtures.json、contracts/fact-constraint-set.schema.json/catalog.json/fixtures.json；Excel“需求主表”N57:P57、“可执行任务”L85:M85。

### TASK-CNT-003

- Requirement ID：CNT-003；P0；矩阵中无前置任务。
- 状态：进行中。已建立 EvidenceConflict Draft 2020-12 契约、目录与四个正常/边界预期 fixture。记录 topic、全部 evidence_refs、逐 claim 原值、解决状态、决策依据和 ERR-008/SOURCE_CONFLICT 引用。
- 冲突策略：单一受支持数值不生成冲突对象；未决冲突保留全部来源、claim、锚点和值，selected source/claim 为空。只有显式用户选择或本次调用方提供的优先级才能记录解决；优先序最高来源必须有唯一 claim，否则保持 unresolved，不自动降级到较低来源。调用方优先级不形成产品默认，DEC-004/TASK-DEC-004 保持未开始。
- 缺失边界：缺失续约日期不构造 EvidenceConflict，继续由 CNT-001 的 missing 状态及 ERR-009/MISSING_FACT 表达。ERR-008 在此只被契约引用；错误Fallback 行保持未开始，未实现 fallback 运行时。
- 静态核对：14 个 schema `$ref` 与 6 个目录文件引用可定位；4 个 fixture 中 claim/value/SourceAnchor 与 CNT-001 或 IN-014 上游样例一致，调用方优先级选择可追溯且保留其余值。未运行 JSON Schema 实例验证器、冲突检测器、DEC-004 决策器、fallback 运行时或 AC-001–AC-030。
- 基线对齐：更新既有“数据对象”EvidenceConflict 行状态与备注；不新增/删除需求、任务、数据对象或错误码。Schema 版本仍为“待定义”，草案未获批准。
- 证据：contracts/evidence-conflict.schema.json、contracts/evidence-conflict.catalog.json、contracts/evidence-conflict.fixtures.json；contracts/source-bundle.schema.json/catalog.json/fixtures.json、contracts/fact-constraint-set.schema.json/fixtures.json；Excel“需求主表”N58:P58、“可执行任务”L86:M86、“数据对象”I8:J8。

### TASK-CNT-004

- Requirement ID：CNT-004；P0；矩阵中无前置任务。
- 状态：进行中。已建立 Assumption[] Draft 2020-12 契约、目录和六个正常/边界预期 fixture，分别覆盖显式可推断规则、需记录假设、显式可见性、缺失时 ask/fail，以及数字/来源冲突边界。
- 假设边界：保留 assumption_id 与原文；reason 必须有明确来源；confidence 与 user_visible 未提供时为 null，不规定置信度量表或显示默认。可推断分支要求有证据及显式允许的确定性规则。
- 冲突与缺失：未解决来源冲突继续引用 CNT-003 EvidenceConflict/ERR-008，不生成单一事实值；缺失事实按显式上下文 ask/fail 引用 ERR-009，不构造值。DEC-004、DEC-005 和 ERR-009 仍未开始，本任务不替代全局策略决策。
- 静态核对：schema/catalog/fixtures JSON 可解析，schema 的 2 个引用和目录的 6 个 JSON 文件引用可定位；6 个 fixture 的假设身份/FactConstraintSet 引用、显式推导、未决来源冲突、缺失 ask/fail 对齐。未运行 JSON Schema 实例验证器、分类器、生成器、冲突/询问/失败运行时或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-004、TASK-CNT-004 和 Assumption 数据对象状态/证据，不新增或删除需求、任务、对象或错误码；DEC-005 保持未开始。
- 证据：contracts/assumption.schema.json、contracts/assumption.catalog.json、contracts/assumption.fixtures.json、contracts/evidence-conflict.fixtures.json、contracts/fact-constraint-set.fixtures.json、PROJECT_PLAN.md；Excel“需求主表”N59:P59、“可执行任务”L87:M87、“数据对象”I10:J10。

### TASK-CNT-005

- Requirement ID：CNT-005；P0；矩阵中无前置任务。
- 状态：进行中。已建立 AudienceProfile Draft 2020-12 契约、目录和三个正常/边界 fixture，覆盖显式受众上下文、数字/未决冲突/缺失事实并存，以及没有受众信息。
- 字段边界：knowledge_level、roles、concerns、expected_actions 保留明确输入原文及顺序；逐字段记录 evidence_id、assumption_id 或 PresentationContext JSON Pointer。未知知识水平为 null，未知列表为空；不做角色刻板推断、不设知识等级/人群默认。
- 事实保护：源数字不用于猜受众；CNT-003 未决冲突不由画像选择来源，missing fact 继续引用 CNT-001/ERR-009。AudienceProfile 只辅助内容深度和术语，不覆盖事实约束。
- 静态核对：schema/catalog/fixtures JSON 可解析，schema 引用及目录文件引用可定位；3 个 fixture 对应 3 个 acceptance case，字段值/上下文路径、数值输入隔离、未决冲突和缺失事实引用静态对齐。未运行 JSON Schema 实例验证器、受众抽取器、语义校验器、运行时或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-005 与 TASK-CNT-005 状态和证据；矩阵未列 AudienceProfile 数据对象，本任务不新增/删除任何基线行，PresentationContext 对象状态不变。
- 证据：contracts/audience-profile.schema.json、contracts/audience-profile.catalog.json、contracts/audience-profile.fixtures.json、contracts/fact-constraint-set.fixtures.json、contracts/evidence-conflict.fixtures.json；Excel“需求主表”N60:P60、“可执行任务”L88:M88。

### TASK-CNT-006

- Requirement ID：CNT-006；P0；矩阵中无前置任务。
- 状态：进行中。已建立 PresentationScenario Draft 2020-12 契约、目录和三个正常/边界 fixture，覆盖明确场景/时长、数字/未决冲突/缺失事实并存，以及输入未提供场景和时长。
- 字段边界：保留 scenario 与 duration 原文，逐字段引用 SourceEvidence、Assumption 或 PresentationContext JSON Pointer。PDR 的场景是开放示例；duration 不解析单位、不换算、不取中点、不设默认。未提供字段为 null。
- 事实保护：数值不用于推断场景；未决来源冲突继续由 CNT-003/ERR-008 表达，missing fact 继续由 CNT-001/ERR-009 表达；不覆盖事实约束。
- 静态核对：schema/catalog/fixtures JSON 可解析，5 个 schema 引用和目录 JSON 文件引用可定位；3 个 fixture 对应 acceptance case，原文/路径、数值隔离、未决冲突与缺失事实引用对齐。未运行 JSON Schema 实例验证器、场景/时长分类器、运行时或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-006/TASK-CNT-006 状态和证据；PresentationScenario 未单列数据对象，不新增/删除基线行，PresentationContext 对象行保持未开始。
- 证据：contracts/presentation-scenario.schema.json、contracts/presentation-scenario.catalog.json、contracts/presentation-scenario.fixtures.json、contracts/fact-constraint-set.fixtures.json、contracts/evidence-conflict.fixtures.json；Excel“需求主表”N61:P61、“可执行任务”L89:M89。

### TASK-CNT-007

- Requirement ID：CNT-007；P0；矩阵中无前置任务。
- 状态：进行中。已建立 LanguageStyleSpec Draft 2020-12 契约、目录和四个正常/边界 fixture，分别覆盖中文、英文、混合语言、仅部分字段指定、数值/未决冲突/缺失事实以及全字段未提供。
- 字段边界：language、tone、formal_level、terminology_rules、brand_terms 均来自显式输入并逐字段记录 evidence_id、assumption_id 或 PresentationContext JSON Pointer；未提供标量为 null、列表为空，不设默认。
- 事实保护：不从数值或冲突推导语言样式；冲突继续由 CNT-003/ERR-008 表达，missing fact 继续由 CNT-001/ERR-009 表达。契约仅记录要求，不表示翻译、多语言渲染或术语执行已交付。
- 静态核对：schema/catalog/fixtures JSON 可解析，5 个 schema 引用和目录 JSON 文件引用可定位；4 个 fixture 对应 acceptance case，三种语言模式、原文/来源路径、数字隔离、冲突和缺失事实引用对齐。未运行 JSON Schema 实例验证器、语言/风格转换器、运行时或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-007/TASK-CNT-007 状态和证据；LanguageStyleSpec 无独立数据对象行，不新增/删除基线行，PresentationContext 对象仍未开始。
- 证据：contracts/language-style-spec.schema.json、contracts/language-style-spec.catalog.json、contracts/language-style-spec.fixtures.json、contracts/fact-constraint-set.fixtures.json、contracts/evidence-conflict.fixtures.json；Excel“需求主表”N62:P62、“可执行任务”L90:M90。

### TASK-CNT-008

- Requirement ID：CNT-008；P0；矩阵中无前置任务。
- 状态：进行中。已建立 DeckThesis Draft 2020-12 契约、目录和三个正常/边界 fixture，覆盖支持数字、未决增长率冲突、显式假设与缺失续约日期。
- 输出边界：main_takeaway 为单一论点；至少一个 supporting_point，逐项引用 evidence_id 或 assumption_id；顶层 evidence_refs 是支持点证据引用的去重汇总。假设必须明确表述为假设，不得变成来源事实。
- 事实保护：正常样例保留 ARR/增长率原值和期间；未决 8%/9% 冲突不选胜者，改用独立的显式 12% 假设作为样例论点；缺失 renewal_date 不构造值并继续引用 ERR-009。
- DEC-009 边界：DEC-009 才负责选择/生成整套演示核心 takeaway，且矩阵依赖 RES-031；本任务只给输出形状与追溯约束，DEC-009/TASK-DEC-009/VERIFY-DEC-009 保持未开始。
- 静态核对：schema/catalog/fixtures JSON 可解析，schema 引用与目录 JSON 文件引用可定位；3 个 fixture 对应 acceptance case，支持证据/假设 ID、顶层汇总、冲突和缺失事实引用静态一致。未运行 JSON Schema 实例验证器、DEC-009、语义蕴含检查器、运行时或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-008/TASK-CNT-008 及 DeckThesis 数据对象状态/证据，不新增/删除需求、任务、对象或错误码；DEC-009 保持未开始。
- 证据：contracts/deck-thesis.schema.json、contracts/deck-thesis.catalog.json、contracts/deck-thesis.fixtures.json、contracts/fact-constraint-set.fixtures.json、contracts/evidence-conflict.fixtures.json；Excel“需求主表”N63:P63、“可执行任务”L91:M91、“数据对象”I12:J12。

### TASK-CNT-009

- Requirement ID：CNT-009；P0；矩阵中无前置任务。
- 状态：进行中。已建立 ContentGraph Draft 2020-12 契约、目录和三个正常/边界 fixture，覆盖同周期指标并列、未决冲突关系及缺失事实过滤。
- 图结构边界：按基线输出 nodes、edges(type)、evidence_refs；node_id 仅为图内局部引用，节点/边都必须有 evidence_id 或 assumption_id 支撑。顶层 evidence_refs 是图内证据引用的按序去重汇总。
- 关系边界：type 使用开放字符串；端点字段不自动表示方向，关系标签承担语义。并列不作因果；未决 8%/9% 值全部保留，不选胜者；missing renewal_date 不生成节点或值，继续引用 ERR-009。
- 静态核对：schema/catalog/fixtures JSON 可解析，schema 引用与目录文件引用可定位；3 个 fixture 对应 acceptance case，节点端点、引用汇总、数值证据、未决冲突和缺失事实引用静态一致。未运行 JSON Schema 实例验证器、关系抽取器、图语义校验器、运行时或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-009/TASK-CNT-009 与 ContentGraph 对象状态/证据，不新增/删除需求、任务、对象或错误码。
- 证据：contracts/content-graph.schema.json、contracts/content-graph.catalog.json、contracts/content-graph.fixtures.json、contracts/fact-constraint-set.fixtures.json、contracts/evidence-conflict.fixtures.json；Excel“需求主表”N64:P64、“可执行任务”L92:M92、“数据对象”I13:J13。

### TASK-CNT-010

- Requirement ID：CNT-010；P0；矩阵中无前置任务。
- 状态：进行中。已建立 CitationPolicy Draft 2020-12 契约、目录及 8 个 fixture：五种显式来源展示模式、未选模式、未决数值冲突与缺失事实。
- 展示边界：hidden 只隐藏视觉引用，仍保留 evidence/assumption 追溯；notes、footnote、appendix、inline 分别定义展示表面及回链规则。模式只能来自显式 PresentationContext，未提供时不设默认。
- 回链边界：复用既有 evidence_id→source_id 映射解析 SourceEvidence/SourceAnchor；不复制 locator、不编造 URL/title，partial/unavailable 原样保留。布局为语义约束；不固定字号/坐标/容量，超出能力时报告 unrenderable，不静默换模式。
- 数据边界：8%/9% 均保留并引用 ERR-008；缺失 renewal_date 不生成引用，显式 12% 假设仍用 assumption_id 回链且缺失沿用 ERR-009。DEC-021 的展示位置选择未实现，仍依赖 RES-031。
- 静态核对：schema/catalog/fixtures JSON 可解析，五个 profile 映射、8 个 fixture/验收场景、来源回链、引用汇总、冲突与缺失边界一致；未运行 JSON Schema 实例验证器、运行时或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-010/TASK-CNT-010 状态和证据；CitationPolicy 未列入数据对象表，不新增/删除任何矩阵行。
- 证据：contracts/citation-policy.schema.json、contracts/citation-policy.catalog.json、contracts/citation-policy.fixtures.json、contracts/fact-constraint-set.fixtures.json、contracts/evidence-conflict.fixtures.json；Excel“需求主表”N65:P65、“可执行任务”L93:M93。

### TASK-CNT-011

- Requirement ID：CNT-011；P0；矩阵中无前置任务。
- 状态：进行中。已建立 ContentRewriteTrace Draft 2020-12 契约、目录及 4 个 fixture，覆盖数字压缩、未决冲突、缺失事实和无法满足约束的过度压缩。
- 追溯边界：保存整体 before_text/after_text 和事实、限定词、单位、结论逐元素 trace；复用 evidence_id、assumption_id 与显式 PresentationContext 路径，局部键不替代全局 ID。
- 保留边界：保留 ARR US$2.4 million、FY2025、8% year-over-year 与上下文结论；未决 8%/9% 全部保留并引用 ERR-008；renewal_date 缺失继续引用 ERR-009，显式 12% 假设独立保留。未授权遗漏或无法同时满足保留约束时不可标记 complete。
- 转换边界：压缩不能静默改变事实、限定词、单位或结论；不授权数字换算、舍入或翻译。显式遗漏记录理由及 context pointer；压缩预算与保留约束冲突时阻止交付。
- 静态核对：schema/catalog/fixtures JSON 可解析，4 个验收 fixture 的 before/after、元素引用汇总、数值/冲突/缺失/blocked 边界静态一致；未运行 JSON Schema 实例验证器、摘要运行时、语义等价检查器或 AC-001–AC-030。
- 基线对齐：更新既有 CNT-011/TASK-CNT-011 状态和证据；ContentRewriteTrace 未列在数据对象表，不新增/删除矩阵行。
- 证据：contracts/content-rewrite-trace.schema.json、contracts/content-rewrite-trace.catalog.json、contracts/content-rewrite-trace.fixtures.json、contracts/fact-constraint-set.fixtures.json、contracts/evidence-conflict.fixtures.json；Excel“需求主表”N66:P66、“可执行任务”L94:M94。

### TASK-CNT-012

- Requirement ID：CNT-012；P0；矩阵中无前置任务。
- 状态：进行中。已建立 HallucinationGuardResult Draft 2020-12 契约、目录及 6 个静态 fixture，覆盖有来源事实、无依据数字/客户名/引用/调研结论、保留与擅选冲突、显式 placeholder 和臆造缺失值。
- 追溯边界：事实断言必须回链既有 evidence_id 或 assumption_id；PresentationContext 只能约束表示方式，不能单独证明事实。placeholder 必须显式并指向缺失事实与 ERR-009。
- 冲突边界：同时保留 8%/9% 和 ERR-008 可通过本草案 guard；只选一个值时阻断。DEC-004 仍未决，本任务不执行冲突决策。
- 基线对齐：只更新既有 CNT-012/TASK-CNT-012 状态和证据；HallucinationGuardResult 未列在数据对象表，不新增或删除矩阵行。PresentationContext 全局 Schema、模型输出语义检测器、引用真实性校验及运行时未实现。
- 静态核验：schema/catalog/fixtures JSON 可解析，7 个 schema 引用与目录文件引用可定位；6 个 fixture 对应 6 个 acceptance case，来源/假设 ID、冲突/缺失边界、占位符显式路径和阻断行为静态一致。未运行 JSON Schema 实例验证器、模型/语义运行时或 AC-001–AC-030。
- 证据：contracts/hallucination-guard.schema.json、contracts/hallucination-guard.catalog.json、contracts/hallucination-guard.fixtures.json；Excel“需求主表”N67:P67、“可执行任务”L95:M95。

### TASK-CNT-013

- Requirement ID：CNT-013；P0；矩阵中无前置任务。
- 状态：进行中。已建立 NotesSpec Draft 2020-12 契约、目录及 3 个静态 fixture，覆盖详细解释/来源/演讲稿路由、未决数字冲突及缺失事实/显式假设。
- 页面与备注：将 required_details 逐项映射到 slide 或 speaker_notes；讲稿/来源/解释保留现有 evidence_id、assumption_id 和局部内容键，页面 concise 不设未定义的固定字数阈值。
- 边界：冲突保留 8%/9% 和 ERR-008，不选择 winner；缺失 renewal_date 保留 ERR-009 和显式 placeholder，12% 假设沿用原 assumption_id。notes 引用模式来自 fixture 中显式 PresentationContext，不设产品默认。
- 基线对齐：SlideContentSpec 已列 notes、citation_refs；NotesSpec 未列为独立数据对象，不新增/删除矩阵行。PPT-023 notes master/layout/OOXML round-trip 能力仍为 Untested；AC-017 和 AC-001–AC-030 未执行。
- 静态核验：schema/catalog/fixtures JSON 可解析，12 个 schema 引用及目录文件引用可定位；3 个 fixture 对应 3 个 acceptance case，9 个 required_detail 对齐 9 条转移轨迹和 8 个 notes block；来源/假设 ID、数字、冲突/缺失边界及页面文本短于草稿静态一致。未运行 JSON Schema 实例验证器、notes runtime、PPT-023 backend PoC 或 AC-017/AC-001–AC-030。
- 证据：contracts/notes-spec.schema.json、contracts/notes-spec.catalog.json、contracts/notes-spec.fixtures.json；Excel“需求主表”N68:P68、“可执行任务”L96:M96。

### TASK-CNT-014

- Requirement ID：CNT-014；P0；矩阵中无前置任务。
- 状态：进行中。已建立 AppendixPlan Draft 2020-12 契约、目录及 4 个静态 fixture，覆盖显式附录模式、模式未决、数字来源、8%/9% 冲突与缺失日期/假设。
- 链接：正文 main_item 的 marker 指向 appendix_entry；entry 反向保留 main_item_refs，并以 evidence_id/source_id 回链现有来源锚点。局部 key 仅用于计划内关联。
- 边界：appendix 模式来自显式 PresentationContext，未选择时返回 unresolved；冲突保留双方值和 ERR-008，不选择 winner；renewal_date 保留 ERR-009，不填值，12% 保持 assumption。
- 基线对齐：SlideContentSpec 已有 citation_refs；AppendixPlan 未列为独立数据对象，本任务不新增/删除矩阵行。附录排版、PPTX 内容标记/跳转和 runtime 尚未实现。
- 静态核验：schema/catalog/fixtures JSON 可解析，16 个 schema 引用和目录文件引用可定位；4 个 fixture 对应 4 个 acceptance case，正文标记与附录反向 main_item_refs 成对一致，evidence_id/source_id 来源锚点回链一致。未决模式不默认附录；数字、冲突/缺失边界和 assumption 归属静态核对通过。未运行 JSON Schema 实例验证器、附录 runtime、DEC-004 或 AC-001–AC-030。
- 证据：contracts/appendix-plan.schema.json、contracts/appendix-plan.catalog.json、contracts/appendix-plan.fixtures.json；Excel“需求主表”N69:P69、“可执行任务”L97:M97。

### TASK-GOV-009

- Requirement ID：GOV-009；P0；无前置任务。
- 状态：已完成。建立 `SCOPE.md`，逐项记录当前排除的账号、计费、多租户、协同编辑、模板商城，并确认 CLI、API、MCP、调试入口属于核心范围；明确模板商城排除不扩大为所有模板能力排除。
- 交接：根 `AGENTS.md` 的 GOV-009 段与矩阵“Codex交接”`CH-013` 引用同一范围声明；具体能力仍回到需求基线判定，不改变 308 条需求或 453 项任务。
- 验证：对照 GOV-009 原文逐项核对 SCOPE、AGENTS 和 CH-013 的纳入/排除措辞；回读矩阵状态与证据路径一致。
- 证据：`SCOPE.md`、`AGENTS.md`；Excel“需求主表”`N10:P10`、“可执行任务”`L12:M12`、“Codex交接”第 14 行。

### TASK-RES-P04-03 / VERIFY-RES-P04-03

- Requirement ID：RES-P04-03；P0；前置 RES-P04-02。固定源码为 `peterfei/ai-agent-ppt` main commit `c3605ebc487fc6c7d4f4139761e46d7021cd656c`，MIT。
- 状态：已完成（上游源码研究）；ProjectDecisionMap 提取 17 个源码级页面结构/视觉节点。每个节点记录 input、candidates、mechanism、output、constraints、fallback、trace 和可定位源码行。
- DEC 交叉映射：覆盖 DEC-001–040 全部 40 项；3 mapped、27 partial、10 not_evidenced。项目路由、Prompt 规则、模板默认、layout 跳过、Vision raw-HTML 回退和背景色 fallback 均单独标记，不补写为产品策略。
- 验证：禁网 Node Docker 容器执行 `verify-res-p04-03.mjs`；核对 source-index 引用/源码行、40 个 DEC ID 与既有 P04-01/02 正常/边界/失败报告和 PPTX 文件 SHA-256。复用已有隔离运行证据，没有重发 Provider/API 请求。
- 边界：真实 LLM/Vision、模型内部候选/评分、截图路线、所有 layout/template、视觉渲染、QA/revision、产品 CapabilityStatus 和 AC-001–AC-030 均未因此完成或宣称通过。仅回填 P04 源码研究状态。
- 证据：`research/P04/decision-map.md`、`research/P04/decision-map.json`、`research/P04/validation/verify-res-p04-03.mjs`、`research/P04/validation/verify-res-p04-03.json`；Excel“需求主表”N29:P29、“可执行任务”L48:M49、“开源项目研究对象”K5:N5。

## 约束

- 默认开发分支为 `yoloongdevlop`，每项项目配置或实现工作按项目规则提交并推送到 `origin/yoloongdevlop`。
- 每项变更在 `ailog/` 和 `development-log/` 保存同名中文任务日志，包含相同本地时间戳。
- 不从主机或工具安装推定产品技术栈，不把 Python 3.11.2 等环境版本写成需求。
- 当前仓库处于治理和环境初始化阶段；没有产品源代码，Docker 开发容器可用也不表示应用已交付。
