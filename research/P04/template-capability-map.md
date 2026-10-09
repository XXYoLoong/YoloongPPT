# P04 模板版式与 PPT 能力边界

- 需求：RES-P04-04、RES-P04-05；任务：TASK/VERIFY-RES-P04-04、TASK/VERIFY-RES-P04-05。
- 固定快照：`c3605ebc487fc6c7d4f4139761e46d7021cd656c`，MIT © peterfei。JSON 中保留资产原值、来源路径、行范围、哈希及固定链接；这是候选上游研究，不是产品实现。
- 数据交付：[template-map.json](template-map.json)、[capability-map.json](capability-map.json)。消费者是 RES-031 横向对照、RES-032 复用决策及后端/模板选型；不另建产品 schema。

## 模板、slot、geometry、capacity、token 与 inheritance

5 个模板为 business、education、pitch、report、tech。每个保存完整 colors、fonts、spacing、slideSize；它们是 CLI 可选 JSON 样式配置，不是可导入的 PowerPoint 母版。无 extends/父模板。`fonts.fallback` 与部分 spacing 字段存在于定义中，但不能据此宣称执行端消费了它们。

| 页面类型/资产 | 实际 slot | 条件与边界 |
|---|---|---|
| title | title、subtitle | subtitle 消费 expandedText 或 notes，居中仅为样式声明 |
| bullet | title、bulletPoints | 列表文字，不是完整 PowerPoint 原生编号/缩进语义 |
| code | title、code、bulletPoints | codeSnippet 文本框，代码背景/圆角声明不等于原生对象效果完整实现 |
| chart | title、bulletPoints | chartData 未消费；不创建原生 chart |
| timeline | title、bulletPoints | timelineData 未消费；不创建时间线对象 |
| comparison | title、bulletPoints | comparisonItems 未消费；没有实际两列几何执行 |
| image-text | image、title、bulletPoints | 声明 row/45% 图；topic writer 扁平化为顺序块，不按 flex 行排布 |
| image | title、subtitle + backgroundImage | imageUrl 替换背景变量；下载和显示仍受输入/后端限制 |

每个布局完整保留递归树、slot 节点路径与样式。token 为 `{{colors.*}}` 及 `{{imageUrl}}` 等变量；LayoutLoader 只替换解析到的字符串，未解析变量保持原样。SlideRenderer 用 SLOT_MAP 填内容，未知 slot 无内容；节点本身的 src 不直接复制到返回对象，image slot 通过新 img 子节点传递。

**两条 geometry 路线必须区分：** topic/input 经 LayoutNode → StyleNode → PPTXBuilder，writer 扁平化，边距 0.8 inch、顶部 0.9 inch、下界 height−0.5 inch，以游标估算文本高度；忽略 flex 列/行和多数 CSS 空间属性。HTML 路线经 RawStyleNode → PureLayout → LayoutBox，默认 1280×720 px，再由 PPTAdapter 用 slideHeight/720 转 inch。topic 样式树没有送入 PureLayout，因此不能将 HTML 路线的几何能力外推到 JSON 模板路线。

**容量：** 资产没有字符/项目上限或 ContentBudget。writer 的 CJK 字宽启发式、shrinkText 和剩余高度裁剪不是 QA；游标到下界就 break，不生成内容丢失报告或自动拆页。上层继承是 StyleNode 的祖先 style 合并，非 PPTX placeholder/master 继承。

**中间表示：** TemplateConfig；Outline/OutlineSlide/SlideContent；LayoutDefinition/LayoutNode/StyleNode；RawStyleNode 与 LayoutBox。原字段和限制见 JSON。没有 source/evidence/decision/object/QA 的稳定 ID 贯通，不可直接用作产品 SlideSpec。

## PPT 对象、写入、QA 和修订边界

`capability-map.json` 逐项对应原 PPT-001–030，保留原描述。Partial 仅表示包装器有子能力，不表示整个 Requirement 已满足。Unsupported 表示固定包装器未发现执行入口，不评价 PptxGenJS 库独立能力。

- Partial：新建/保存、增加 slide、样式颜色/字体应用、文本框、有限字符格式、CJK 高度估计、rect 装饰、图片/背景写入。没有已有 deck 的生命周期或完整对象读改保存。
- 未提供：sections/custom show、导入/编辑母版与 layout、placeholder idx/继承、connector/freeform、group、原生 table/chart/equation/SmartArt、OLE、媒体、hyperlink/action、真实 speaker notes/comment、footer/date/page number 继承、transition/animation、完整 effects/accessibility、对象身份往返。
- `speakerNotes` 和 notes slot 只是内容字段/页面 slot；没有 `addNotes` 调用。类型字段存在不表示演讲稿已进入 notes。
- 所谓 render 是把元素写进 PPTX，不是 Office/LibreOffice 图像渲染。上游无结构/视觉/事实/可编辑性 QA 和 QA 驱动的局部修订链。
- content filler 失败回退原内容、未知 layout 回退 bullet，但没有产品式 FallbackRecord、统一 trace 和最终报告。下载有 timeout，没有内网/SSRF/大小预算防护；writeFile 保存没有原文件保护事务。

## 验证与可复现边界

验证脚本为 [validation/verify-res-p04-04-05.mjs](validation/verify-res-p04-04-05.mjs)，在现有固定、已构建的研究副本中运行，Docker 禁网，仅挂载 F 盘。检查 5 模板/8 版式与源文件哈希、正常 PPTX 文本、未解析变量/未知 slot、chartData 与 speakerNotes 不消费、超容量截断、缺失/损坏布局和输出父路径为文件的失败。

实际执行结果以 `validation/verify-res-p04-04-05.json` 为准；未运行时不得视为通过。已有 P04-01/02 HTML/topic 输出与失败证据复用；不重新执行模型生成或全量测试。新探针也不调用真实模型/Vision、不做 Office/LibreOffice 渲染或 PowerPoint 编辑行为验证，不更新产品 CapabilityStatus 或 AC 状态。

## 对选型的影响

可参考模板变量/slot 加载、CLI 分流和基本文本/图片写入；不能直接承担母版保真、原生 chart/table、既有 PPT 局部修改或系统 QA。产品必须补齐内容预算、对象/证据追溯、显式降级、安全下载、真正的渲染/QA 和修改保护。是否直接/抽象复用仍由 RES-032 在横向研究完成后决定，不在此预设产品语言或库。
