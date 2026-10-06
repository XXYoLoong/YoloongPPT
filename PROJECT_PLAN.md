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

## 约束

- 默认开发分支为 `yoloongdevlop`，每项项目配置或实现工作按项目规则提交并推送到 `origin/yoloongdevlop`。
- 每项变更在 `ailog/` 和 `development-log/` 保存同名中文任务日志，包含相同本地时间戳。
- 不从主机或工具安装推定产品技术栈，不把 Python 3.11.2 等环境版本写成需求。
- 当前仓库处于治理和环境初始化阶段；没有产品源代码，Docker 开发容器可用也不表示应用已交付。
