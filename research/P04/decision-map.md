# ai-agent-ppt 页面结构与视觉决策图

- Requirement ID：`RES-P04-03`
- Task / verification：`TASK-RES-P04-03` / `VERIFY-RES-P04-03`
- 固定上游：`peterfei/ai-agent-ppt` main commit `c3605ebc487fc6c7d4f4139761e46d7021cd656c`，MIT。
- 结构化完整映射：[decision-map.json](decision-map.json)；源码索引：[source-index.json](source-index.json)。

## 结论

从固定源码提取 17 个影响路由、内容大纲、版式、模板、几何、样式、截图反建与素材 fallback 的节点。所有节点都记录输入、候选、机制、输出、约束、fallback、trace 边界及源码行。DEC-001–040 全量映射：3 个 `mapped`、27 个 `partial`、10 个 `not_evidenced`。这些状态只评价上游源码证据，不代表 YoloongPPT 产品实现。

大纲和视觉表达主要由 Prompt 引导模型生成；源码不暴露候选集、评分或模型内部理由。主题路线和 HTML 路线采用不同几何策略：前者把 StyleNode 展平后按游标纵向排版，后者把简化 HTML 送入 PureLayout 计算 box。截图路线将 Vision JSON 或 raw HTML 转为 HTML，再复用几何与 PPT 适配器。

## 节点清单

完整字段以 JSON 为准；下表便于查看每个节点的 DEC 对应关系与固定源码位置。

| 节点 | 统一 DEC | 输入/候选与机制 | 输出及 fallback | 源码位置 |
|---|---|---|---|---|
| P04-ROUTE （项目特有规则） | DEC-001 | Create 命令选项及配置/provider 初始化结果；候选：--html、--images、--topic/--input、缺少输入；CreateCommand 先解析模板，再按 html > images > topic/input 的源码顺序分流；没有意图分类器。 | 选定的上游生成分支；或输入校验错误；fallback：缺输入抛出参数错误；不自动切换到另一模式。 | src/index.ts:15-97<br>src/commands/create.ts:47-85<br>src/commands/create.ts:157-187<br>src/commands/create.ts:190-377 |
| P04-INPUT （项目特有规则） | DEC-002, DEC-003, DEC-008 | --topic、--input、--lang、配置 defaultLang；候选：UTF-8 单文件、目录根 README.md/package.json、主题文本、显式语言；单文件按 UTF-8 读取；目录只拼接根 README.md 与 package.json，扫描异常被忽略；lang 被转换后写入 outline prompt。没有来源角色分类或冲突处理。 | 传给 outline generator 的原始字符串、模板名和可选语言提示；fallback：缺失或读取异常可能得到空/失败输入；未做 source priority/merge。 | src/commands/create.ts:71-85<br>src/commands/create.ts:395-411<br>src/commands/create.ts:87-97<br>src/core/engine/outline-generator.ts:48-65<br>src/types/config.ts:36-40 |
| P04-OUTLINE （项目特有规则） | DEC-009, DEC-011, DEC-012, DEC-013, DEC-015, DEC-016, DEC-017, DEC-019, DEC-022, DEC-023, DEC-024, DEC-026, DEC-027 | 主题或读取后的文本、模板名、语言提示；候选：标题与有序 slide 列表；8 个 layout 名称；bullet/code/chart/timeline/comparison/image 字段；SYSTEM_PROMPT 要求 5–15 页、layout 多样、单页 focused message、适当数据/代码/比较，并强制每套至少一页 image/image-text；LLM 生成 JSON。仅解析 JSON 并检查 title 与 slides 数组，不校验单页字段或语义。 | Outline.title 与 Outline.slides；每页可带 layout、标题、bulletPoints、notes、imageUrl、chartData、codeSnippet、timelineData、comparisonItems；fallback：LLM 响应解析或最小结构检查失败时重试；没有字段级修复、可解释候选或语义 fallback。 | src/core/engine/outline-generator.ts:10-80<br>src/types/config.ts:75-110 |
| P04-OUTLINE-RETRY （项目特有规则） | DEC-040 | 大纲生成调用异常；候选：首次成功、重试后成功、重试耗尽；withRetry 最多 3 次，等待 2 秒、4 秒；仅包裹大纲生成调用。 | 成功的大纲或最终抛出的最后一个错误；fallback：重试耗尽后抛出最后错误并结束该路径。 | src/commands/create.ts:379-393 |
| P04-TEMPLATE （项目特有规则） | DEC-002, DEC-028, DEC-029, DEC-033, DEC-034, DEC-035 | CLI --template、配置 defaultTemplate、内置回退值；候选：business、education、pitch、report、tech；优先级为命令行 > 配置 > 固定 tech；TemplateManager 用 Zod 校验 colors/fonts/spacing/slideSize。模板文件定义颜色、字体、字号/行距和画布尺寸。 | TemplateConfig 供 layout 变量及 PPTX 渲染使用；fallback：模板文件缺失/无效时终止生成并报错，不改用其他模板。 | src/commands/create.ts:47-57<br>src/core/template/template-manager.ts:9-90<br>src/templates/business/template.json:1-26<br>src/templates/education/template.json:1-26<br>src/templates/pitch/template.json:1-26<br>src/templates/report/template.json:1-26<br>src/templates/tech/template.json:1-26 |
| P04-CONTENT-FILL （项目特有规则） | DEC-019, DEC-020, DEC-037 | 大纲页标题、layout、bulletPoints、codeSnippet、chartData；候选：expandedText、speakerNotes；ContentFiller 按页串行请求模型扩写；成功时合并 expandedText/speakerNotes；异常或响应 JSON 解析失败时 catch 并保留原 outline slide。 | 带扩写字段或原样保留的 SlideContent 列表；fallback：逐页失败静默回退原始页，继续输出；没有结构化错误状态。 | src/core/engine/content-filler.ts:8-73<br>src/types/config.ts:75-115 |
| P04-LAYOUT-CHOICE （项目特有规则） | DEC-017, DEC-030 | LLM outline 中的 layout 字段；候选：title、bullet、code、chart、timeline、comparison、image、image-text；Prompt 给出八个名称；下游按生成的字符串尝试加载同名 JSON 文件。LayoutLoader.list 可列目录文件，但 CreateCommand 路径不据此生成候选或打分。 | 输入到 LayoutLoader.load 的一个 layout 名称；fallback：无法加载时该页被跳过，见 P04-LAYOUT-LOAD。 | src/core/engine/outline-generator.ts:10-39<br>src/core/engine/layout-loader.ts:64-83<br>src/layouts/bullet.layout.json:1-36<br>src/layouts/chart.layout.json:1-36<br>src/layouts/code.layout.json:1-50<br>src/layouts/comparison.layout.json:1-36<br>src/layouts/image-text.layout.json:1-56<br>src/layouts/image.layout.json:1-39<br>src/layouts/timeline.layout.json:1-36<br>src/layouts/title.layout.json:1-38 |
| P04-LAYOUT-LOAD （项目特有规则） | DEC-030, DEC-032, DEC-040 | 生成的 layout 名称及布局 JSON 文件；候选：有效并符合 Zod schema、缺失/JSON 错误/schema 错误；按精确文件名读取 `{name}.layout.json` 并校验根/节点结构；异常返回 null；CreateCommand 累计 skipped 后仍构建输出。 | LayoutDefinition 或 null；后者导致该页跳过；fallback：缺失/无效 layout 不自动选替代版式，也不阻止其余页面导出。 | src/core/engine/layout-loader.ts:34-83<br>src/commands/create.ts:139-153<br>src/layouts/bullet.layout.json:1-36<br>src/layouts/chart.layout.json:1-36<br>src/layouts/code.layout.json:1-50<br>src/layouts/comparison.layout.json:1-36<br>src/layouts/image-text.layout.json:1-56<br>src/layouts/image.layout.json:1-39<br>src/layouts/timeline.layout.json:1-36<br>src/layouts/title.layout.json:1-38 |
| P04-SLOT-BINDING  | DEC-018, DEC-019, DEC-032 | SlideContent 字段与 LayoutNode.slot；候选：title、subtitle、code、notes、image、bulletPoints；SLOT_MAP 将六种命名 slot 映射到字段/子节点；模板变量从 colors/fonts/spacing 解析；bulletPoints 展开为 li。 | StyleNode 树；fallback：空 code/notes/image 返回 null、无内容的 bulletPoints 生成空列表；不报告 unsupported slot。 | src/core/engine/slide-renderer.ts:5-73<br>src/types/config.ts:75-115<br>src/layouts/bullet.layout.json:1-36<br>src/layouts/chart.layout.json:1-36<br>src/layouts/code.layout.json:1-50<br>src/layouts/comparison.layout.json:1-36<br>src/layouts/image-text.layout.json:1-56<br>src/layouts/image.layout.json:1-39<br>src/layouts/timeline.layout.json:1-36<br>src/layouts/title.layout.json:1-38 |
| P04-TOPIC-RENDER （项目特有规则） | DEC-018, DEC-033, DEC-034, DEC-035, DEC-036 | StyleNode 树、模板尺寸/颜色/字体/spacing；候选：顺序文本块、图片块、固定装饰形状；PPTXBuilder 将树展平为文本/图片块，忽略原布局树的 x/y/网格关系；用游标纵向放置、估算行数并裁到剩余高度，设置字体/颜色/字号；图片按块尺寸写入。 | PptxGenJS slide 对象与 PPTX buffer；fallback：超出剩余高度时压到 bottomLimit；远程图像处理见 P04-IMAGE-ASSET。 | src/core/engine/pptx-builder.ts:25-219<br>src/core/engine/pptx-builder.ts:225-236 |
| P04-HTML-STRUCTURE （项目特有规则） | DEC-022, DEC-033, DEC-034, DEC-035, DEC-036 | 单个 HTML 字符串、模板画布尺寸；候选：解析出来的元素树与 LayoutBox；HTML 直达 PureLayout；wrapper 解析简化标签/内联样式，调用 purelayout 计算 1280×720 viewport 几何，再修补 flex 子项位置，PPTAdapter 逐 box 写入单页。 | LayoutBox[] 与一张 PPTX slide；fallback：空/无法解析 HTML 抛错；不切换到其他 route。 | src/commands/create.ts:157-187<br>src/core/engine/pure-layout.ts:70-158<br>src/core/engine/pure-layout.ts:354-584<br>src/core/engine/ppt-adapter.ts:24-188 |
| P04-HTML-CSS （项目特有规则） | DEC-033, DEC-034, DEC-035 | HTML 标签、内联 style、style block；候选：标签选择器、class、tag.class、已识别的内联属性；图片路线仅解析少量 selector；跳过 @media、伪类等嵌套规则；删除 class、脚本/head 等标签；把 body 替换为 div；多根节点包入 flex 容器。 | PureLayout 可处理的简化 HTML；fallback：不支持的规则忽略；必要时用包装容器继续解析。 | src/commands/create.ts:307-348<br>src/commands/create.ts:413-563 |
| P04-IMAGE-ANALYSIS （项目特有规则） | DEC-022, DEC-023, DEC-024 | PNG/JPG/JPEG/WEBP 图片与选择的 Vision Provider；候选：backgroundColor、title、subtitle、text/row sections、文字样式；中英文 prompt 要求 JSON 描述结构并提取全部文字；图片以 data URL 和文本 prompt 一起发送给 Provider。该路线意图是从截图提取版面信息。 | JSON 结构描述，后续转换为 HTML；fallback：JSON 解析失败后进入原始 HTML fallback；图片单页异常会继续处理后续图片。 | src/commands/create.ts:190-291<br>src/core/providers/provider-adapter.ts:1-13 |
| P04-VISION-FALLBACK （项目特有规则） | DEC-022, DEC-033, DEC-040 | Vision Provider 原始响应文本；候选：可解析 JSON、JSON 失败时原始响应按 HTML 处理；先抽取 JSON 块并转为 HTML；解析失败使用完整 raw 响应；随后清理部分标签、移除 class、body 转 div、多根元素自动包装。 | 供 PureLayout 解析的 HTML；fallback：空或不可解析 HTML 后续失败；没有 fallback 决策确认。 | src/commands/create.ts:294-349<br>src/commands/create.ts:517-563 |
| P04-BACKGROUND-FALLBACK （项目特有规则） | DEC-029, DEC-035 | LayoutBox 背景与文本颜色、模板 primary/background；候选：已有背景色、无背景且有浅色文字、无背景且无浅色文字；只在未发现背景 box 时应用规则：存在浅色文字则用 template.colors.primary，否则用 template.colors.background。 | slide.background color；fallback：识别到任意背景 box 时不应用该回退。 | src/commands/create.ts:351-363<br>src/commands/create.ts:573-584<br>src/templates/tech/template.json:1-26 |
| P04-PPT-ADAPTER （项目特有规则） | DEC-033, DEC-034, DEC-035, DEC-036, DEC-038 | LayoutBox、TemplateConfig、背景与素材信息；候选：RENDER_MAP 支持的 text/image/background 元素到 PptxGenJS API；PPTAdapter 将 box 几何、文字/图片样式和背景映射到 PptxGenJS；PPTX 后端在固定源码中是单一路径，不按能力注册表择优。 | PptxGenJS slide API 调用；fallback：素材读取失败按 adapter/调用点处理；无备用后端。 | src/core/engine/ppt-adapter.ts:24-188<br>src/commands/create.ts:168-184<br>src/core/engine/pptx-builder.ts:52-60 |
| P04-IMAGE-ASSET （项目特有规则） | DEC-024, DEC-036, DEC-040 | 背景/内容图片 URL 或本地图片路径；候选：HTTP 成功、HTTP 失败、超时、异常；fetch 最多等待 10 秒；PPTXBuilder 下载失败返回 null 后将原 URL 作为 path 交给 PptxGenJS；图片重建路线逐图 catch 后继续并最终保存。 | base64 image data、原 URL path 或失败页跳过；fallback：下载失败不阻止 topic PPTX；图片分析失败跳过该张并继续。 | src/core/engine/pptx-builder.ts:225-236<br>src/core/engine/ppt-adapter.ts:175-188<br>src/commands/create.ts:364-377 |

## DEC-001–040 交叉表

`mapped` 表示有明确上游机制；`partial` 表示有相关 prompt/字段/局部逻辑但契约不完整；`not_evidenced` 表示固定调用链中未发现对应的独立机制。详情和逐项依据见 JSON。

| 状态 | DEC IDs |
|---|---|
| mapped | DEC-001, DEC-028, DEC-032 |
| partial | DEC-002, DEC-003, DEC-008, DEC-009, DEC-011, DEC-012, DEC-013, DEC-015, DEC-016, DEC-017, DEC-018, DEC-019, DEC-020, DEC-022, DEC-023, DEC-024, DEC-026, DEC-027, DEC-029, DEC-030, DEC-033, DEC-034, DEC-035, DEC-036, DEC-037, DEC-038, DEC-040 |
| not_evidenced | DEC-004, DEC-005, DEC-006, DEC-007, DEC-010, DEC-014, DEC-021, DEC-025, DEC-031, DEC-039 |

### 项目特有机制

- **P04-PS-01 / P04-ROUTE**：固定 CLI 优先级 html > images > topic/input；不做用户意图自动分类。
- **P04-PS-02 / P04-OUTLINE**：Prompt 指定 5–15 页、至少一页 image/image-text，并建议 Unsplash URL。
- **P04-PS-03 / P04-TEMPLATE**：没有 CLI/配置模板时固定回退 tech；模板无效则失败。
- **P04-PS-04 / P04-CONTENT-FILL**：逐页填充失败 catch 后保留原 outline 内容并继续。
- **P04-PS-05 / P04-LAYOUT-LOAD**：无效/缺失 layout 页被计数跳过，仍生成剩余 PPTX。
- **P04-PS-06 / P04-HTML-CSS**：只支持有限 CSS selector；不支持的规则会忽略。
- **P04-PS-07 / P04-VISION-FALLBACK**：Vision JSON 解析失败时把原始响应当 HTML 清理后继续。
- **P04-PS-08 / P04-BACKGROUND-FALLBACK**：缺背景时依据是否含浅色文字，在模板 primary/background 间二选一。

## 可复现验证与限制

`validation/verify-res-p04-03.mjs` 在禁网 Node Docker 容器中检查全部决策节点的源码行、source-index 引用、40 个 DEC ID 覆盖、既有验证报告及 PPTX 哈希。它复核 P04-01 的 HTML 正常/嵌套边界与缺输入失败，以及 P04-02 的 topic 正常、内容填充 fallback 和缺输入失败；没有重复调用模型/API。报告：[verify-res-p04-03.json](validation/verify-res-p04-03.json)。

截图 Vision、无效 layout、模型推理与评分、视觉渲染、Office/LibreOffice round-trip、QA/revision 和产品能力均未据此宣称完成。未运行真实模型、未运行上游 Vitest，也未运行 AC-001–AC-030。

## 上游与产品边界

本图只描述固定 MIT 上游源码。PptxGenJS 序列化、PureLayout 包算法、远端 Provider 与图片 URL 服务是外部黑盒。上游 Node 观测版本、依赖与路线不构成 YoloongPPT 技术选型；产品架构保持未决。
