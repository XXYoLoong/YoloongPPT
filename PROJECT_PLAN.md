# YoloongPPT 项目目标与执行计划

## 项目目标

依据《AI_PPT_PDR_完整需求定义_V0.3.docx》和《AI_PPT_完整需求与任务矩阵_V0.3.xlsx》，交付一个可追溯的 AI PPT 生成系统。用户输入经过统一决策链后，系统至少能生成可编辑 PPTX，并完成渲染、结构、视觉、事实、可编辑性检查及局部修订闭环。

Codex 当前目标已登记为活动目标。需求矩阵是逐项执行与验收的工作台；开始或完成任何实现、研究、验证任务时，都关联稳定的 Requirement ID 或 Task ID，并在矩阵中保存状态和证据。

## 完成判定

- 308 条需求均有来源、稳定 ID、验收条件和状态；453 条任务记录均已完成，或有明确的 N/A 理由及证据。
- S00–S44 全链路均实现或有明确的不适用说明；DEC-001–040 决策节点有契约和证据。
- 5 个开源项目有可复现的研究记录；9 条 PowerPoint 后端路线完成需求对照和必要 PoC；PPT-001–030 对象能力有明确支持状态。
- AC-001–AC-030 验收通过。至少一个端到端路径从真实输入走到可编辑 PPTX、QA 与局部修订。
- Docker 仅管理本项目隔离开发环境。产品架构、语言、运行时和依赖版本须先由需求、PoC、平台限制及许可证据决定；容器环境观测不构成产品选型。

## 执行阶段

里程碑用于组织范围，不改写 Excel 中的任务依赖；实际推进顺序以“可执行任务”表的依赖列为准。

| 阶段 | 需求范围 | 主要交付 |
|---|---|---|
| 0. 基线与治理 | GOV-001–GOV-010 | 统一需求注册、模式与约束契约、能力状态、版本与追溯治理 |
| 1. 开源研究与许可 | RES-P01–RES-P05、RES-031–RES-033 | 固定研究版本、运行记录、源码证据、横向比较、复用决策和测试资产索引 |
| 2. 决策与后端验证 | DEC-001–DEC-040、ADP-PP-01–ADP-PP-09、PPT-001–PPT-030 | 决策契约、9 条后端路线 PoC、对象能力矩阵及许可/平台边界 |
| 3. 生成与修订链路 | S00–S44、IN、CNT、TPL、AST、SYS、REV | 输入解析、内容与证据、模板素材、可编辑 PPTX 生成、已有 PPT 修改和局部修订 |
| 4. 质量与交付 | QA、NFR、SEC、OBS、TST、OPS、AC-001–AC-030 | 安全与非功能控制、可观察性、回归和端到端验收证据 |

## 当前进度

### TASK-GOV-001

- Requirement ID：GOV-001；P0；无前置任务。
- 状态：已完成。将 Excel“需求主表”中的 `RES-031`、`RES-032`、`RES-033` 按原规则、输入、约束、交付、验收、依赖、优先级与任务 ID 补入 DOCX 第 3.6 节；没有增加或改写需求范围。
- 验证：DOCX 与 Excel 的 308 个 Requirement ID 全部可定位；453 个 Task ID 唯一且均引用现有需求；DOCX 原有 13 张表和原段落顺序保留。Excel 回填完成状态和证据路径。
- 证据：Excel“需求主表”`N2:P2`、“可执行任务”`L2:M2`；本文件第 3.6 节；`ailog/` 与 `development-log/` 本次同名任务日志。

### TASK-GOV-002

- Requirement ID：GOV-002；P0；DEC-001；S02。
- 状态：进行中。已建立语言/运行时无关的 TaskRoute schema 与八模式契约目录草案；每种模式都列有输入、流程、输出、独立保护策略和验收场景。另列 8 个常规路由场景与 1 个边界冲突场景。
- 当前边界：Excel 的“数据对象”表列出 `RawTaskRequest`、`TaskSpec.route` 和 `RuntimeCapabilitySnapshot`，但未单列 `TaskRoute` 的正式字段定义。因此 `contracts/task-route.schema.json` 中的路由结果/trace 字段仍是待评审草案。运行时路由、候选生成算法、冲突优先级、与 `TaskSpec.route` 的正式版本关系及 P01–P05 实现映射尚未完成；不能据此宣称系统已支持八种模式。
- 静态核验：目录含 8 个唯一模式，每个均有 input/flow/output/acceptance_case 与独立 protection_policy_id；决策场景含 8 个常规样例及 1 个边界冲突样例；schema 与目录可解析为 JSON。当前执行环境没有 `jsonschema` 包，未运行 JSON Schema 标准验证器，也未运行路由器测试。
- 证据：`contracts/task-route.schema.json`、`contracts/task-route.catalog.json`；Excel“需求主表”`N3:P3`、“可执行任务”`L3:M3`、“决策链”`M2`、“0-1全链路”`G4:I4`。

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
- 状态：进行中。建立 `CapabilityStatus` Draft 2020-12 契约草案，并逐项登记 Excel“PowerPoint对象矩阵”的 PPT-001–030 × PP-01–09 共 270 个状态。根据当前矩阵与 PoC 证据，270 项均保留为 `Untested`；30 行已关联状态证据，PP-08/PP-09 的候选源码 commit 已固定，另 7 条路线的具体源码/依赖版本仍未冻结。九条路线 PoC 均未执行；源码提交固定不代表已选为产品后端或已有能力结论。
- 当前边界：九条 PowerPoint 路线均未执行 PoC。PP-08/PP-09 仅固定了候选仓库的 main commit；其余七条路线仍未冻结具体版本，且所有路线的产品后端、package/API set/Office build 选型均未完成。`SYS-007` Capability Registry 尚未开始，基线也未枚举系统级非 PPT 原子能力或具体运行时 Adapter 实例；catalog 明确登记这两类范围缺口。`VERIFY-GOV-005` 仍未开始，尚无实际能力测试证据。
- 静态核验：Draft 2020-12 元模式、30 项能力、9 个后端版本状态、270 条状态记录和 fixture 校验通过；每项记录均匹配矩阵中的状态、版本栏和证据位置。未运行后端 PoC。
- 证据：`contracts/capability-status.schema.json`、`contracts/capability-status.catalog.json`、`contracts/capability-status.fixtures.json`；Excel“PowerPoint对象矩阵”`P2:P31`、“PowerPoint后端”`I2:J10`、“需求主表”`N6:P6`、“可执行任务”`L7:M7`。

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
- 状态：进行中。已检出 PPT Master `main` 分支快照 `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d`；上游 `v6.6.0` tag 为另一提交 `a50758ac29ec027e85966db33e2ae80031446756`。研究只记录上游要求，不据此选择 YoloongPPT 的运行时。
- 静态证据：上游 Getting Started 声明 Python 3.10+；根 `requirements.txt` 包含 skill 依赖，版本为下限约束，未发现项目级锁文件；根许可证为 MIT，PDF 转换的可选 PyMuPDF 依赖为 AGPL-3.0。运行链路是 Agent Host 对话请求生成并导出可编辑 PPTX，不是单条 CLI 示例。
- 环境阻塞：本机 Docker CLI `27.4.0` 可执行，但服务端 `docker version` 超时；对当前 `desktop-linux` 端点及官方 Windows 默认命名管道的只读 API 探测均未响应。Docker Desktop 日志记录 C: 空间不足导致 VM 日志写入失败；清理本任务自建临时克隆后仍无法连通。未启动/重置共享 Docker 引擎，也未在宿主机安装上游依赖。
- 验收边界：源码固定及静态元数据已记录；官方最小流程未运行，未生成 PPTX。`TASK-RES-P01-01` 保持进行中；`VERIFY-RES-P01-01` 与依赖它的 `TASK-RES-P01-02` 保持未开始。待 Docker API 可用后，在隔离容器复现并记录实际镜像摘要、依赖和生成物。
- 证据：`research/P01/README.md`；Excel“需求主表”`N12:O12`、“可执行任务”`L14:M15`、“开源项目研究对象”第 2 行。

### TASK-RES-P02-01

- Requirement ID：RES-P02-01；P0；无前置任务。
- 状态：进行中。按矩阵冻结 PPTAgent / DeepPresenter 三个研究快照：main `833cda553b343be0e486a93b0b57cac962cdd566`、v0.2.0 `d53296bc0ddd73e81d51c523d20dd711c7f233f3`、v1.1.38 annotated tag object `2e68c095a86bdbb91635dc4d91dad4662aba163c` / peeled commit `2419d30b134a71486523e95ded60b32489fd3c61`。远端 refs 与 GOV-010 既有版本记录一致，固定 clone 位于仓库外 `F:\YoloongPPT-Research\P02`。
- 锁与许可：main Skill 有 npm `package-lock.json`，Python `requirements.txt` 不是完整锁；v0.2.0 与 v1.1.38 均有 `uv.lock` 和子目录 npm lock。三个源码快照根 LICENSE 均为 MIT。main Skill requirements 固定 `pptagent==1.1.37`，而研究 tag 为 v1.1.38；v0.2.0 的包元数据版本为 0.2.8，与 tag 名 v0.2.0 不同。研究记录按源码事实区分，不静默对齐版本。
- 上游环境：main Skill README 要求 Linux（含 WSL）或 macOS、uv、npm、LibreOffice；macOS 转换器另需 Chrome，并示例使用 Python 3.12。论文 tags 的 `pyproject.toml` 要求 Python `>=3.11`。这些是上游各自的环境声明，不是 YoloongPPT 的技术选型。
- 环境阻塞：当前 Docker context `desktop-linux` 的 Engine pipe 不存在；项目容器未启动，P02 官方最小流程、依赖安装和 PPTX 生成均未运行。没有在 Windows 主机安装 P02 依赖。
- 验收边界：源码 refs、锁文件元数据、运行条件和上游主许可证已做静态核对；因官方最小流程未复现，`ProjectBaseline` 验收仍未完成，`TASK-RES-P02-01` 保持进行中。后续在隔离容器执行官方最小流程并记录环境/日志/生成物。
- 证据：`research/P02/README.md`、`contracts/version-manifest.catalog.json`；Excel“需求主表”`N17:P17`、“可执行任务”`L24:M24`、“开源项目研究对象”第 3 行。当前 P02 官网 [README](https://github.com/icip-cas/PPTAgent/blob/833cda553b343be0e486a93b0b57cac962cdd566/README.md) 固定到 main commit。

### TASK-RES-P03-01

- Requirement ID：RES-P03-01；P0；无前置任务。
- 状态：进行中。官方 `refs/heads/main` 于 2026-10-07 指向 `35bf44290f821323e003da854f78ffcb0e918167`，与 GOV-010 的 `P03-MAIN` pinned commit 一致。仓库外研究 clone `F:\YoloongPPT-Research\P03` 使用该 detached commit 和 sparse checkout。
- 锁与许可：记录根、Electron、Next.js 的三个 npm v3 lock 和 FastAPI `uv.lock` version 1/revision 3；FastAPI 上游声明 `>=3.11,<3.12`，uv lock 约束为 `==3.11.*`，不推导补丁版本或产品运行时。根许可证 Apache-2.0，另有第三方归属 `NOTICE`；尚未完成依赖逐项许可审计。
- 上游流程：固定文档描述 Standard（固定 layout、outline review、模板）和 Smart（adaptive layout、流式进入编辑器）；Web UI / MCP 模式开关不等于 REST API 授权。上游 README 还描述多用户工作区，此功能属于 GOV-009 排除边界，不扩大本项目范围。
- 环境阻塞：`docker version` 仍无法连接当前 `desktop-linux` Engine pipe；未启动容器、安装依赖、运行最小流程或生成 PPTX。
- 验收边界：源码快照、锁文件、运行条件、许可证与核心模式文档已静态核对；`ProjectBaseline` 官方最小流程尚未复现，`TASK-RES-P03-01` 保持进行中。待 Docker 恢复后在隔离容器复现并记录环境、日志和产物。
- 证据：`research/P03/README.md`、`contracts/version-manifest.catalog.json`；Excel“需求主表”`N22:P22`、“可执行任务”`L34:M34`、“开源项目研究对象”第 4 行。官方 [README](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/README.md) 与[生成模式说明](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/docs/presentation-generation-modes.md)固定到同一 commit。

### TASK-RES-P04-01

- Requirement ID：RES-P04-01；P0；无前置任务。PDR 同时列出后续 `RES-P04-02` 完整调用链和 `RES-P04-03` 决策节点任务，本条不替代它们。
- 状态：进行中。官方 `refs/heads/main` 于 2026-10-07 指向 `c3605ebc487fc6c7d4f4139761e46d7021cd656c`，与 GOV-010 的 `P04-MAIN` pinned commit 一致；研究 clone 位于仓库外 `F:\YoloongPPT-Research\P04` 并保持干净。
- 锁与许可：npm `package-lock.json` 为 lockfileVersion 2，根包版本 0.1.0；上游 `package.json` 声明 Node `>=18.0.0`，无补丁版本 pin 或上游容器文件。根许可证为 MIT。以上仅为候选上游元数据，不是产品运行时决策。
- 静态入口观察：CLI 入口加载配置并创建 Provider 后，才分发 HTML、图片、主题/文档路径；Provider registry 仅实际注册 DeepSeek、GLM，其他命名是预留。HTML 分支经 `PureLayout`/`PPTAdapter` 输出到 PptxGenJS，但 CLI 仍要求配置；P04-02/03 的全链路与决策分析仍未开始。
- 环境阻塞：执行 `scripts/project.ps1 start` 失败，当前 Docker Engine pipe 不存在。未在主机安装 Node、未执行 npm 安装/构建/测试、未生成 PPTX。
- 验收边界：refs、锁、许可证、上游运行声明和关键入口已静态核对；官方最小流程未运行，`ProjectBaseline` 尚未通过，`TASK-RES-P04-01` 保持进行中。待 Engine 恢复后在隔离容器复现并记录配置前置条件、日志和 PPTX。
- 证据：`research/P04/README.md`、`contracts/version-manifest.catalog.json`；Excel“需求主表”`N27:P27`、“可执行任务”`L44:M44`、“开源项目研究对象”第 5 行。官方 [README](https://github.com/peterfei/ai-agent-ppt/blob/c3605ebc487fc6c7d4f4139761e46d7021cd656c/README.md) 固定到 P04-MAIN commit。

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

### TASK-GOV-009

- Requirement ID：GOV-009；P0；无前置任务。
- 状态：已完成。建立 `SCOPE.md`，逐项记录当前排除的账号、计费、多租户、协同编辑、模板商城，并确认 CLI、API、MCP、调试入口属于核心范围；明确模板商城排除不扩大为所有模板能力排除。
- 交接：根 `AGENTS.md` 的 GOV-009 段与矩阵“Codex交接”`CH-013` 引用同一范围声明；具体能力仍回到需求基线判定，不改变 308 条需求或 453 项任务。
- 验证：对照 GOV-009 原文逐项核对 SCOPE、AGENTS 和 CH-013 的纳入/排除措辞；回读矩阵状态与证据路径一致。
- 证据：`SCOPE.md`、`AGENTS.md`；Excel“需求主表”`N10:P10`、“可执行任务”`L12:M12`、“Codex交接”第 14 行。

## 约束

- 默认开发分支为 `yoloongdevlop`，每项项目配置或实现工作按项目规则提交并推送到 `origin/yoloongdevlop`。
- 每项变更在 `ailog/` 和 `development-log/` 保存同名中文任务日志，包含相同本地时间戳。
- 不从主机或工具安装推定产品技术栈，不把 Python 3.11.2 等环境版本写成需求。
- 当前仓库处于治理和环境初始化阶段；没有产品源代码，Docker 开发容器可用也不表示应用已交付。
