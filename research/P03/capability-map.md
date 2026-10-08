# Presenton 写入、渲染、QA、修订与已有 PPT 边界（RES-P03-05）

- 固定上游：`presenton/presenton`，commit `35bf44290f821323e003da854f78ffcb0e918167`。本文件是源码静态能力图，不是 YoloongPPT 的语言/架构选择。
- `Native` 仅指该层在固定源码中有直接实现；它不等于已验证 PowerPoint OOXML 原生对象。端到端状态需同时看内部表示、运行依赖和导出边界。
- `Partial` 表示只覆盖部分路径或依赖未审计的外部实现；`Fallback` 表示明确的占位/降级路径；`Unsupported` 只限表中声明的已追踪调用路径，不能外推为产品绝对不支持。

| 范围 | 能力/对象 | 状态 | 源码观察 | 边界 |
|---|---|---|---|---|
| 写入 | Standard 结构化页内容写入 | **Partial** | Standard 路径依据模板 layout/schema 生成结构化 content，持久化为 SlideModel.content 与 ui。 | PPTX 编码由外部导出包承担；本次仅静态追踪，未生成文件。 |
| PPT 对象 | 文本与富文本 | **Partial** | Text/TextRun 模型含文本、字体、段落与样式字段；UI 有对应编辑动作。 | 未验证其映射为 PPTX 原生文本对象，也未验证字体与格式保真。 |
| PPT 对象 | 图片 | **Partial** | 图片 URL/提示词进入内部元素模型；资源处理可取用已有 URL 或生成图片。 | 失败回退和最终 PPTX 嵌入行为须分别看待；导出实现是外部黑盒。 |
| PPT 对象 | 矢量形状 | **Partial** | Vector 模型声明形状、点、曲线、填充和描边等内部字段。 | 内部矢量模型不证明导出为对应 PowerPoint 原生形状。 |
| PPT 对象 | 表格 | **Partial** | Table/TableCell 模型和 chat 编辑输入结构存在。 | 未验证导出为可编辑原生表格或保留单元格格式。 |
| PPT 对象 | 图表 | **Partial** | Chart/ChartSeries 模型和 chat 编辑能力存在。 | 未验证导出为 PowerPoint 原生图表、数据表或可编辑属性。 |
| PPT 对象 | 信息图 | **Partial** | Infographic 类型和数据结构存在，编辑工具可增添信息图。 | 最终对象分解与 PPTX 可编辑性取决于外部导出包，尚未运行验证。 |
| PPT 对象 | 文本列表 | **Partial** | TextList 是内部 SlideElement 联合类型成员。 | 未验证 PPTX 输出结构。 |
| PPT 对象 | 容器、Flex、Grid、Group | **Partial** | Container/Flex/Grid/Group 支持嵌套 children 与位置、尺寸或布局字段。 | 这些是内部排版/分组表示，不证明 PowerPoint 分组对象的序列化结果。 |
| 主题与模板 | 模板、版式、主题 token | **Partial** | TemplateV2/layout 和主题字段供结构生成及编辑器渲染使用；P03-04 已建立固定模板清单。 | 静态结构图不证明实际生成适配性或导出后主题保真。 |
| PPT 对象 | 演讲者备注 | **Partial** | SlideModel 保存 speaker_note，复制页时保留；聊天上下文读取备注。 | PdfMaker HTML 带备注渲染辅助属性不等于 PPTX Notes Slide 导出已证实。 |
| 写入与渲染 | Smart HTML 页 | **Partial** | Smart 页保存 html_content 并由浏览器编辑器渲染，安全/溢出检查后可流式持久化。 | HTML 到 PPTX 的转换实现在外部导出包；本次未生成或检查 PPTX。 |
| 渲染 | 浏览器编辑器渲染 | **Native** | 浏览器组件渲染标准 TemplateV2 UI 与 Smart HTML。 | 源码级实现已定位；本次未运行浏览器视觉检查，不能据此宣称视觉验收通过。 |
| PPTX 写入 | PPTX/PDF 导出任务链 | **Partial** | 服务端封装 export task 并调用 runner；@presenton/export-core 固定为 v1.0.34，但实现是独立发布制品，不在研究源码 clone 中。 | 文件字节、OOXML 对象、可编辑性、注释/备注保真和错误路径均未直接检查。 |
| QA | 请求与结构化内容校验 | **Native** | 源码具有请求 schema、模板 schema 和 Smart HTML 基础结构检查。 | 只说明存在校验实现，不表示本次运行通过或覆盖所有内容错误。 |
| QA | Smart 单页安全与布局启发式检查 | **Native** | 源码拒绝滚动/裁切样式、按页型限制可见文字密度，并检查布局溢出/重叠风险。 | 属于生成前单页启发式检查，不等同于整套 PPT 的事实、语义、可读性或最终渲染 QA；未运行。 |
| QA | Standard 全套演示文稿的事实/语义/视觉 QA 门禁 | **Unsupported** | 在本次追踪的 Standard 主生成路径中未发现完成后整套 deck 的事实/语义/视觉 QA 阶段。 | 结论仅限 Presenton 固定 commit 的已追踪路径；不外推到所有模式或产品范围。 |
| QA | 导出后 PPTX 与预期的对象/像素级对比检查 | **Unsupported** | 导出实现为外部黑盒，本次没有导出文件或导出后复核链路证据。 | 表示本次审计链路未证实此门禁，不推断黑盒内部绝对不存在相关功能。 |
| 修订 | REST /edit 与 /derive | **Partial** | 接口修改已有数据库演示文稿页内容，或基于 PresentationModel/SlideModel 建立派生演示文稿，再触发导出。 | 不是直接改写上传的原始 PPTX 包；本次未调用接口。 |
| 修订 | 编辑器聊天修订 | **Partial** | ChatService 可调度新增/更新/删除 slide、element、component 等工具；代码中有标准与 Smart 模式路由。 | 依赖登录和模型提供方；本次未执行模型或编辑 API 调用。 |
| 已有 PPT | 已有 PPT 转为模板参考 | **Partial** | 模板入口调用外部 PPTX-to-JSON 转换，校验 RawSlideLayouts，并按预览图片数截取 layout；随后进入模板生成/存储流程。 | 这是模板解析/参考路径，不代表原始 deck 可往返保真或直接编辑。 |
| 已有 PPT | 直接对任意已有 PPTX 原包进行原位编辑并保留未知对象 | **Unsupported** | 本次追踪的 /edit、/derive 操作数据库 PresentationModel/SlideModel；PPTX 上传路径用于模板提取，没有发现任意原包对象级编辑/往返保真流程。 | 仅为已追踪 Presenton 路径的边界，不外推为产品全局断言。 |
| Fallback | 图片生成失败后的占位图回退 | **Fallback** | 允许回退的调用路径可将失败图片替换为 placeholder.jpg，并在 warning 集合记录失败。 | 结果是占位素材，不应视作成功生成图片或无损降级。 |
| Fallback | 图标查询无结果时的占位图标 | **Fallback** | P03-02 调用链静态跟踪记录空图标查询结果使用 placeholder.svg。 | 只记录固定源码 fallback，未运行确认。 |

## 主要对象汇总

固定源码的 `SlideElement` 联合类型包含 Text、Container、Image、TextList、Table、Vector、Chart、Infographic、Flex、Grid、Group。它们在 Presenton 内部模型中属于 Native；对象的端到端 PPTX 序列化均标为 Partial，因为导出核心 `@presenton/export-core@1.0.34` 是 clone 外单独下载的制品，无法从当前源码检查其对象写入实现。Speaker note 在 SlideModel 中持久化；Smart 模式页以 `html_content` 保存并在浏览器渲染。

## QA 与修订边界

- 已有请求/schema 校验；Smart 单页检查会拒绝滚动/裁切样式，按页面类型检查可见文字密度，并调用布局检查识别溢出/重叠风险。这些是源码可见的机制，不是本次运行通过的证据。
- 本次追踪的 Standard 主生成路径没有整套 deck 的事实、语义、视觉 QA 门禁。导出核心为黑盒，也没有导出后对象/像素对比证据。状态只约束上述调用路径。
- REST `/edit`、`/derive` 和聊天工具提供已存演示文稿的内容修订；调用受身份/模型依赖影响，本次未执行。
- 已有 PPTX 可经 PPTX-to-JSON 转换进入模板参考/生成流程，并按预览图数量限制解析 layout。没有发现任意原 PPTX 包原位编辑及往返保真路径。

## 运行验证

- `TASK-RES-P03-05`：静态能力映射完成。来源节点及固定 commit 可在 `source-index.json` 核对。
- `VERIFY-RES-P03-05`：进行中。上游测试仅静态定位，没有运行；正常生成、边界/失败用例、导出文件及视觉检查均未执行。此前固定环境的认证状态为 `configured=false`，生成请求曾被 HTTP 428 登录门禁拦截；本任务未重试请求、未设置凭据、未生成 PPTX。详见 `validation/verify-res-p03-05.json`。

## 证据文件

- 结构化能力图：`research/P03/capability-map.json`
- 来源索引：`research/P03/source-index.json`
- 验证状态：`research/P03/validation/verify-res-p03-05.json`
