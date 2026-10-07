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

### TASK-IN-004

- Requirement ID：IN-004；P0；无前置任务。
- 状态：进行中。已建立 `PdfEvidence` Draft 2020-12 契约、目录和正常/边界预期 fixture；记录逐页文本块、标题候选、表格单元格、图片对象、坐标框架和来源锚点。
- 坐标边界：项目契约定义使用旋转后 CropBox 左上角原点、point（1/72 英寸）单位；每个 bbox 都带可解释的页面 frame。该坐标转换尚未用真实 PDF/旋转页夹具执行验证。
- 输入边界：IN-004 只处理原生文本层；扫描 PDF 边界返回 `PDF_NO_TEXT_LAYER`，不在本任务中静默进入 OCR。OCR 属于独立 IN-005。
- 静态核验：schema/catalog/fixtures JSON 可解析且 `$ref` 可定位；正常 fixture 含 2 页、5 个元素、4 个表格单元格，页号/索引/锚点一致且 bbox 在页面 frame 内；Asset ID 输入/输出一致。未运行标准 JSON Schema 验证器。
- 验收边界：fixtures 仅为预期结构，无真实 PDF parser 或页框变换结果；`TASK-IN-004` 保持进行中，表格/图片提取和坐标精度未验收；AC-001–AC-030 均未执行。
- 证据：`contracts/pdf-evidence.schema.json`、`contracts/pdf-evidence.catalog.json`、`contracts/pdf-evidence.fixtures.json`；Excel“需求主表”`N43:P43`、“可执行任务”`L71:M71`。

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
