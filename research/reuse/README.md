# 模块复用与测试资产来源（RES-032 / RES-033）

只登记拟复用模块与有来源资产，不引入产品实现或选择产品语言/运行时。消费已完成RES-031；范围仍以V0.3基线为准。

## 许可依据

复制MIT实质内容需保留版权及许可通知。[OSI MIT](https://opensource.org/license/mit)

Apache分发须附许可、保留适用通知/NOTICE并说明修改；不因此获得商标权。[ASF Apache2第4/6条](https://www.apache.org/licenses/LICENSE-2.0)

AGPL covered work的修改/分发与网络交互需考虑对应源代码条件；输出只在其内容构成covered work时覆盖，不能直接按生成工具判断输出许可。[AGPL文本第2/5/6/13条](https://spdx.org/licenses/AGPL-3.0-only.html)

P05许可声明冲突未被本研究裁定。当前工程决定是仅参考/不采用，禁止直接复制或机械翻译源表达。是否将来采用需明确实际许可与合规方式；当前首条产品链路可以使用其他明确许可组件，不被此阻塞。

## 模块决定

| ID | 项目/模块 | 方式 | 消费位置与理由 | 边界 |
|---|---|---|---|---|
| R01 | P01 / opaque XML relationship-attribute guard | 直接复用 | 未来OOXML Adapter的片段关系复制安全检查（PPT-030）；单文件仅stdlib ElementTree；定位关系QName，避免把part-local关系当普通属性 | 只判断关系属性存在，不是XML parser沙箱、关系重绑定或全PPTX安全保证 |
| R02 | P01 / root SVG canvas contract | 直接复用 | 未来SVG原生Adapter的页面尺寸/视口检查；单文件stdlib；已独立定义canvas错误；可与TaskSpec几何接口连接 | 源规则zero-origin与EMU范围必须能力化；不可替代用户全部比例/约束；目标语言/接口未选前不复制 |
| R03 | P01 / source roles, communication/spec lock and roster | 抽象复用 | 统一来源/TaskSpec/DEC规划、页面冻结与trace；保持事实、模式、页序与确认边界，独立实现契约消费接口 | 不能引入上游固定确认流程来覆盖本项目默认与硬约束，也不复制Prompt |
| R04 | P01 / native SVG export / edit proxy / chart parity | 仅参考 | 原生对象、roundtrip及局部修订的验收设计；已有Quick与26项selected tests说明可实现子集；完整依赖链尚未选定 | 不整包vendoring exporter；共享master/proxy拒绝与advisory receipt保留为测试边界 |
| R05 | P01 / bundled icons, sounds and branded decks | 不采用 | 后续素材库必须独立许可/来源登记；包含CC BY/CC0/MIT与品牌商标等独立条件，不由根MIT统一覆盖 | 不复制整个库或品牌模板；媒体/图标功能仍在产品范围，另选来源 |
| R06 | P02 / source/render/review/build freshness gate | 抽象复用 | QA、执行trace和RevisionPlan freshness；将输入/资源/输出hash绑定审查，独立实现任务状态与失效门控 | 需要产品事实/可编辑性QA，不复制源码或把六项检查当全QA |
| R07 | P02 / visual review payload/config boundary | 抽象复用 | 结构化视觉审查与模型secret注入接口；严格issue字段、pass不可含major、env name边界可独立实现 | 不复制Prompt；外部string slide失败需要产品明确错误，不自动吞掉 |
| R08 | P02 / installed HTML converter 1.1.37 | 不采用 | 当前首条写入路线不依赖此converter；native chart缺口、inlineSVG bug、PNG降级与单独依赖许可/安全未解决 | 其依赖与main不是同一版本/许可证明；HTML输入/生成能力不从基线移除 |
| R09 | P02 / single starter and visual MCP packaging | 仅参考 | 最小页面fixture与MCP审查分层；可参考小型工具封装；不是完整生成服务或模板族 | 不把其MCP两个工具当产品CLI/API/MCP交付 |
| R10 | P03 / template element/layout/schema separation | 抽象复用 | 模板IR、语义槽位与几何/容量接口；区分元素、layout与结构化内容，按本项目现有契约独立实现 | 不复制383布局/1002资产或依赖它的外部导出能力 |
| R11 | P03 / REST/SSE/MCP/editor service layering | 抽象复用 | 共用任务状态的CLI/API/MCP与局部修订入口；分层与allowlist思想可用；源调用依赖DB而非PPTX原件 | 不复制账号/产品业务、Prompt/工具实现；保真PPTX编辑另验收 |
| R12 | P03 / external @presenton/export-core backend | 不采用 | 首条执行后端需已知实现/依赖与真实对象证据；固定包装器可定位，但实际外部制品是黑盒；许可/实现/对象实物不足 | 不能把Apache根许可或内部元素树当外部exporter许可/完整可编辑性保证 |
| R13 | P03 / account/auth application subsystem | 不采用 | GOV-009排除项；当前范围不包含账号/计费/多租户等，不复制该应用业务 | 产品CLI/API/MCP仍必须实现；不能把核心接口一并排除 |
| R14 | P04 / JSON template tokens/layout slots | 抽象复用 | TPL/AST页面类型与布局registry；独立设计typed slots、token、适用性和几何 | 不沿用缺layout跳页、固定容量、未消费chart/notes的行为 |
| R15 | P04 / topic writer and PureLayout adapter | 仅参考 | 原生对象写入边界/回归样例；有native text/shape子集实物；可用于抽象test oracle | 不整包采用：静默bullet丢失、无QA/保真编辑；依赖许可另查 |
| R16 | P05 / planner/repair/schema/assets | 仅参考 | 来源/分页/Schema错误与裁剪的独立测试设计；保留正反例需求和观测，不采用源表达；许可冲突未解决 | 不得直接复制、移植或机械翻译源代码/Prompt/Schema；按本项目基线独立实现 |
| R17 | P05 / dual renderer/native chart/table/notes | 不采用 | 选择其他明确许可的底层原生对象库实现同一能力；AGPL conflict、旧slide删除bug、短series补零/内容损失；不作为产品依赖 | 原生chart/table/notes仍必须支持，不得以不采用取消范围 |
| R18 | P05 / independent QA/revision mock behavior | 仅参考 | 产品QA/局部修订的失效/损失测试；只参考问题类别与既有实验事实，独立编写测试 | bbox不是事实/像素QA；不复制AGPL测试或mock数据为产品golden |

仅R01/R02两份明确MIT、stdlib文件具备限定直接复制资格；还须选定兼容接口并附完整许可/版权，尚未接入产品。其余抽象/参考不复制源、Prompt、schema或资源。原exporter整包依赖/字体/第三方data不是这两份文件的审核范围。

## 测试资产登记

| ID | 项目 | 类型 | 来源文件 | 方式/权利边界 |
|---|---|---|---|---|
| FIX-001 | P01 | QA cases | `skills/ppt-master/scripts/tests/test_native_chart_table_parity.py` | 仅参考；MIT code; imports/fixtures separately; recreate product assertions |
| FIX-002 | P01 | QA cases | `skills/ppt-master/scripts/tests/test_edit_native_batch_b.py` | 仅参考；MIT code; selected six tests only, not complete suite |
| FIX-003 | P01 | schemas | `skills/ppt-master/templates/schemas/design_spec.schema.json` | 仅参考；MIT declaration; project schema differs; do not overwrite own contracts |
| FIX-004 | P01 | schemas | `skills/ppt-master/templates/schemas/spec_lock.schema.json` | 仅参考；MIT declaration; no automatic product protocol equivalence |
| FIX-005 | P01 | templates | `skills/ppt-master/templates/tables/comparison_matrix.svg` | 仅参考；root/Skill MIT declaration only; embedded font/brand/media must be checked before copying |
| FIX-006 | P01 | PPTX | `research/P01/projects/p01_hello_world_20261007/exports/p01-hello-world.pptx` | 仅参考；project research output; not covered automatically by generator MIT; inspect content before distribution |
| FIX-007 | P01 | screenshots | `research/P01/projects/p01_hello_world_20261007/validation/native-render/slide-01.png` | 仅参考；PowerPoint research render of prior source/output; no third-party asset blanket clearance |
| FIX-008 | P01 | golden cases | `research/P01/validation/p01-boundary-tests.json` | 仅参考；project-owned observation metadata; compare outcomes, do not copy upstream tests |
| FIX-009 | P02 | templates | `skills/pptagent/assets/slide-template.html` | 仅参考；Skill MIT; generic HTML starter, no PPTX master/layout capability |
| FIX-010 | P02 | QA cases | `skills/pptagent/tests/test_workflow.py` | 仅参考；Skill MIT test code; full suite not executed here; rebuild hash gate tests independently |
| FIX-011 | P02 | QA cases | `skills/pptagent/tests/test_visual_mcp.py` | 仅参考；Skill MIT; MCP session not executed; reference only |
| FIX-012 | P02 | schemas | `skills/pptagent/references/task-contract.md` | 仅参考；Skill MIT documentation contract, not a formal JSON Schema |
| FIX-013 | P02 | PPTX | `research/P02/outputs/official-six/answer.pptx` | 仅参考；real model research output with saved public prompt/response; generation license does not itself license output |
| FIX-014 | P02 | screenshots | `research/P02/outputs/official-six/qa/deck/page-01.jpg` | 仅参考；research LO/PDF render; trace source deck, no product asset import |
| FIX-015 | P02 | golden cases | `research/P02/validation/maps-probes.json` | 仅参考；project-owned result metadata; negative SVG/resource/staleness cases retained |
| FIX-016 | P03 | QA cases | `servers/fastapi/tests/unit/test_template_api.py` | 仅参考；Apache-2.0 root + NOTICE; dependencies/embedded fixtures separately assessed; not executed |
| FIX-017 | P03 | QA cases | `servers/fastapi/tests/integration/test_presentation_generation_flow.py` | 仅参考；Apache-2.0 code; integration tests not executed, export core external |
| FIX-018 | P03 | golden cases | `servers/fastapi/tests/regression/snapshots/outline_generation.json` | 仅参考；Apache root declaration; snapshot content/provider output rights need separate clearance; no copy approval |
| FIX-019 | P03 | templates | `templates/modern/template.json` | 仅参考；Apache root declaration; template/images/fonts provenance not universally cleared; no copy approval |
| FIX-020 | P03 | schemas | `servers/fastapi/templates/v2/models/layouts.py` | 仅参考；Apache-2.0 code model, not JSONSchema asset; independent product schema implementation |
| FIX-021 | P03 | screenshots | `servers/nextjs/public/create_presentation_card_1.png` | 不采用；root license does not establish artwork/brand/font rights; exclude branded UI asset |
| FIX-022 | P04 | QA cases | `tests/unit/pptx-builder.test.ts` | 仅参考；MIT code; source-located test suite, not executed here; product test independently rebuilt |
| FIX-023 | P04 | QA cases | `tests/unit/layout-loader.test.ts` | 仅参考；MIT code; do not infer test execution from source existence |
| FIX-024 | P04 | templates | `src/templates/tech/template.json` | 仅参考；MIT-declared JSON token fixture; no external media copied |
| FIX-025 | P04 | templates | `src/layouts/chart.layout.json` | 仅参考；MIT-declared slot layout; chart name does not mean native chart capability |
| FIX-026 | P04 | PPTX | `research/P04/validation/template-normal.pptx` | 仅参考；project research structural fixture output; no full visual/PowerPoint/product acceptance |
| FIX-027 | P04 | golden cases | `research/P04/validation/verify-res-p04-04-05.json` | 仅参考；project-owned outcomes; 56 omitted bullet lines remain negative oracle |
| FIX-028 | P05 | QA cases | `tests/test_template_engine.py` | 仅参考；AGPL/metadata conflict unresolved; reference behaviors only, no code/fixture copy |
| FIX-029 | P05 | QA cases | `tests/test_visual_qa.py` | 仅参考；AGPL/metadata conflict unresolved; no direct copying |
| FIX-030 | P05 | schemas | `deck-schema.json` | 仅参考；AGPL/metadata conflict; do not copy Schema expression into product contracts |
| FIX-031 | P05 | templates | `assets/themes/business-clean.json` | 仅参考；AGPL/metadata conflict; no theme-token copy; choose independent brand/style |
| FIX-032 | P05 | golden cases | `examples/inputs/sample-source-brief.md` | 仅参考；AGPL root declaration/content rights not separately clear; create original source text |
| FIX-033 | P05 | PPTX | `research/P05/outputs/maps-probes/native-objects.pptx` | 仅参考；generated mock research output; cannot infer free distribution or AGPL solely from generator; reference native object structure only |
| FIX-034 | P05 | screenshots | `research/P05/outputs/normal-qa/contact-1.png` | 仅参考；research render/underlying mock output; no product-media clearance |
| FIX-035 | P05 | golden cases | `research/P05/validation/maps-probes.json` | 仅参考；project-owned observed outcomes; do not copy original code/prompt/mock text |

## 来源与未执行边界

- 每文件路径、固定commit、Git内容/本地实物hash、许可文件及模块绑定见[source-manifest](source-manifest.json)、[模块JSON](ReuseDecisionRegistry.json)及[资产JSON](ResearchFixtureIndex.json)。没有复制新上游代码、资源或既有生成物。
- P01已运行的26项selected测试仅按原报告认定；源测试文件存在不代表全文件测试完成。P02实际六页与对象探针可复用；P03测试仅定位/未执行，历史认证门禁不冒充当前阻塞。P04结构产物不等于渲染验收；P05 mock不等于真AI生成。
- 图标/声音/品牌资产和几何data的独立声明已定位，不从根MIT/Apache推断。P03生成PPTX缺失、P04研究渲染截图缺失及P02非formal JSONSchema明确登记。
- 后续产品回归用本项目事实/对象契约独立编写；参考一项失败行为不能成为复制上游测试/Prompt/裁剪规则的理由。所有强制对象/QA/修订仍保留，不能用“不采用”删除功能需求。
