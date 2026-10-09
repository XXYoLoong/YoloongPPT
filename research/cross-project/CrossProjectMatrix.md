# 五个项目横向对照（RES-031）

覆盖原15个维度，每个均有5项目源码/运行证据。这里只比较固定快照；不选产品语言/运行时，不复制代码、不批准许可证复用、不修改DEC或AC状态。

**进度纠正：** 25项主研究已完成；P03五个VERIFY仍在进行中。其生成/导出/编辑未运行，历史HTTP428不是当前阻塞确认。继续RES-031依据其已完成的源码研究，不提升为实测成功，也不要求全验证作为所有实现的人为前置。

## 固定来源与证据等级

- P01 ppt-master：`2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d`；MIT；Full product AC and object roundtrip remain unexecuted。
- P02 PPTAgent main Skill：`833cda553b343be0e486a93b0b57cac962cdd566`；MIT；Full product AC and object roundtrip remain unexecuted。
- P03 Presenton：`35bf44290f821323e003da854f78ffcb0e918167`；Apache-2.0；P03 five VERIFY still in progress, no generation/export evidence。
- P04 ai-agent-ppt：`c3605ebc487fc6c7d4f4139761e46d7021cd656c`；MIT；Full product AC and object roundtrip remain unexecuted。
- P05 auto-ppt-engine：`5ae0670747885c464aa8063329a902d80a251877`；AGPL-3.0 file; conflicting Apache-2.0 metadata；Full product AC and object roundtrip remain unexecuted。

Observed只证明列明实物子集；Partial是相关机制/子集；Unsupported/Not found保留范围，不能冲销目标需求。Prompt规则、主机黑盒、库潜在能力、实测及产品验收分别记录。所有定位及hash见[source-catalog](source-catalog.json)，消费文件锁见[input-manifest](input-manifest.json)。

## 输入

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | 文件/文本/URL作为来源；Generate/Beautify/Edit等路由由Skill指定 | Quick实测Markdown；其余来源转换是源码规则；无独立自然语言路由模型 |
| P02 | Partial | CLI任务仅slides/aspect_ratio/language；用户内容与HTML由主机准备 | 不是完整TaskSpec或文档输入解析器 |
| P03 | Partial | Web/REST接收prompt、files、slides_markdown、语言、页数、模板 | 启动与历史HTTP428有记录；输入生成分支未运行 |
| P04 | Partial | CLI按html>images>topic/input分流；单文件UTF-8、目录仅README/package | 没有SourceBundle角色/优先级；真实模型路径未运行 |
| P05 | Partial | CLI/JSON接收prompt、source、template、旧deck JSON；来源excerpt限5000字符 | 不是所有入口共享校验；不是任意PPTX保真输入 |

来源：

- P01：`P01:D:P01-DEC-01`, `P01:D:P01-DEC-02`, `P01:S:source_intake`；运行记录：[verify-res-p01-01.json](../../research/P01/projects/p01_hello_world_20261007/validation/verify-res-p01-01.json)。
- P02：`P02:D:D02`, `P02:D:D03`；运行记录：[verify-official-six.json](../../research/P02/validation/verify-official-six.json); [workflow-probes.json](../../research/P02/validation/workflow-probes.json)。
- P03：`P03:D:P03-REQUEST`, `P03:D:P03-SOURCES`, `P03:D:P03-MARKDOWN`；运行记录：[smoke.json](../../research/P03/validation/smoke.json); [verify-res-p03-02.json](../../research/P03/validation/verify-res-p03-02.json)。
- P04：`P04:D:P04-ROUTE`, `P04:D:P04-INPUT`；运行记录：[verify-res-p04-02.json](../../research/P04/validation/verify-res-p04-02.json)。
- P05：`P05:D:P05-D01`, `P05:D:P05-D02`；运行记录：[baseline-run.json](../../research/P05/validation/baseline-run.json); [maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：复用多来源与任务模式边界；产品必须统一TaskSpec及原文/位置，不把简化CLI字段当完整解析。

## 内容理解

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | 通信契约、reading mode、来源事实/限定词由主机按Prompt处理 | 没有独立事实冲突求解器；Quick transient plan不保存内部推理 |
| P02 | Not found | 固定CLI未实现独立内容理解/事实模型；Skill委托主机创作 | 真模型HTML输出不证明有可定位的理解算法或事实QA |
| P03 | Partial | loader/search构造context；outline结构化输出；Smart要求来源事实 | 无typed fact/assumption或来源冲突解决；模型未执行 |
| P04 | Partial | LLM大纲Prompt与逐页扩写；只检查title与slides数组 | 扩写失败保留原页；speakerNotes和chartData未被写入消费 |
| P05 | Partial | mock关键词推断；真实模型可按Schema规划；source trust/priority只是metadata | 实测中文仍en-US；没有句级证据和冲突求解 |

来源：

- P01：`P01:D:P01-DEC-02`, `P01:D:P01-DEC-04`, `P01:D:P01-DEC-05`；运行记录：仅源码。
- P02：`P02:D:D03`；运行记录：[author-prompts.json](../../research/P02/validation/author-prompts.json); [author-response.json](../../research/P02/validation/author-response.json)。
- P03：`P03:D:P03-SOURCES`, `P03:D:P03-OUTLINE`, `P03:D:P03-FACTS`；运行记录：[verify-res-p03-03.json](../../research/P03/validation/verify-res-p03-03.json)。
- P04：`P04:D:P04-OUTLINE`, `P04:D:P04-CONTENT-FILL`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D02`, `P05:D:P05-D03`, `P05:D:P05-D05`；运行记录：[maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：所有项目均缺少已验证的全事实/冲突闭环；产品以可追溯SourceEvidence和FactConstraints执行，不以Prompt句子充当保证。

## 规划

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | Default三方向→用户确认→DesignSpec/spec_lock；Quick主机瞬时规划 | Default未执行；用户确认协议不能替代确定性候选评分 |
| P02 | Not found | 内容、结构、页面用途由主机决定；CLI没有Planner编排函数 | 内部候选和评分黑盒；author-six.py是研究调用，不是上游Planner |
| P03 | Partial | Standard outline→layout→schema内容；Smart直接HTML/流式页面 | 无完整统一OutlineSpec/关系图/DecisionTrace；生成未运行 |
| P04 | Partial | 先LLM生成JSON outline，再按页扩写和固定layout加载 | 模型内部选择未知；扩写失败静默保留；仅大纲重试3次 |
| P05 | Partial | JSON deck规划、Schema校验与有限repair；mock固定roster | 真实模型未运行；mock不等于AI规划验收 |

来源：

- P01：`P01:D:P01-DEC-04`, `P01:D:P01-DEC-06`, `P01:S:strategist_and_confirmation`；运行记录：仅源码。
- P02：`P02:D:D03`；运行记录：[author-run.json](../../research/P02/validation/author-run.json)。
- P03：`P03:D:P03-OUTLINE`, `P03:D:P03-LAYOUT`, `P03:D:P03-SMART`；运行记录：[verify-res-p03-03.json](../../research/P03/validation/verify-res-p03-03.json)。
- P04：`P04:D:P04-OUTLINE`, `P04:D:P04-OUTLINE-RETRY`, `P04:D:P04-CONTENT-FILL`；运行记录：[verify-res-p04-02.json](../../research/P04/validation/verify-res-p04-02.json)。
- P05：`P05:D:P05-D04`, `P05:D:P05-D05`；运行记录：[baseline-run.json](../../research/P05/validation/baseline-run.json)。

实现影响：可参考P01确认/锁定、P03分阶段结构、P05校验repair；主机和模型内部候选不伪造为可解释trace。

## 分页

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | page budget/section roster由主机规划；锁定ID/顺序后需修订或重确认 | 没有确定性内容容量到页数求解；3页Quick实物是子集 |
| P02 | Partial | slides须正整数；HTML序号连续且数量匹配，严格构建检查 | 没有自动预算/拆页；容量不符需改源；六页footer曾转换失败 |
| P03 | Partial | 请求count、标题/TOC规则；slides_markdown逐项映射一页 | outline超数会裁剪；没章节预算；运行被历史认证门禁挡住 |
| P04 | Partial | Prompt建议5–15页；按outline页与layout遍历导出 | 缺layout跳页；60条bullet只写4条，56条无遗漏报告 |
| P05 | Partial | 请求页数钳制5–12；mock roster实测最多9页；JSON修订可改页数 | 1页请求实际5、12实际9；clarify101字裁80字无新增说明 |

来源：

- P01：`P01:D:P01-DEC-08`, `P01:D:P01-DEC-10`；运行记录：[verify-res-p01-01.json](../../research/P01/projects/p01_hello_world_20261007/validation/verify-res-p01-01.json)。
- P02：`P02:D:D02`, `P02:D:D06`, `P02:D:D15`；运行记录：[workflow-probes.json](../../research/P02/validation/workflow-probes.json); [footer-revision.json](../../research/P02/validation/footer-revision.json)。
- P03：`P03:D:P03-PAGE-TOC`, `P03:D:P03-MARKDOWN`, `P03:D:P03-OUTLINE`；运行记录：[verify-res-p03-03.json](../../research/P03/validation/verify-res-p03-03.json)。
- P04：`P04:D:P04-OUTLINE`, `P04:D:P04-LAYOUT-LOAD`, `P04:D:P04-TOPIC-RENDER`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D04`, `P05:D:P05-D07`；运行记录：[baseline-run.json](../../research/P05/validation/baseline-run.json); [maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：保留硬页数与完整内容约束；上游钳制/跳页/静默裁剪均不直接沿用，需显式失败或授权重分配。

## 页面类型

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | page brief以单页intent驱动关系、拓扑、chart/table等表达 | 目录和Prompt定义类型，不是实际跑过全部类型的分类器 |
| P02 | Not found | 只有通用claim/evidence starter；页面类型由主机写HTML | 无正式page-type枚举、分类器或页面类型到模板的选择函数 |
| P03 | Partial | Standard由template layout描述与Schema选型；Smart按Prompt生成 | 默认JSON无显式page-type/applicability字段；关键词标签只是候选 |
| P04 | Partial | 8个layout名称由Prompt给出，对应8个JSON版式 | 没有完整类型推断与适用性评分；名称无效会跳过 |
| P05 | Partial | JS17个layout key/15渲染函数；Python映射13 key另有blank | kpi/swot/image-text/funnel未映射，回layout0/bullet且字段损失 |

来源：

- P01：`P01:D:P01-DEC-09`, `P01:D:P01-DEC-11`, `P01:D:P01-DEC-17`；运行记录：仅源码。
- P02：`P02:D:D03`, `P02:D:D04`；运行记录：[verify-official-six.json](../../research/P02/validation/verify-official-six.json)。
- P03：`P03:D:P03-LAYOUT`, `P03:D:P03-SMART`, `P03:S:template-layout-model`；运行记录：[verify-res-p03-04.json](../../research/P03/validation/verify-res-p03-04.json)。
- P04：`P04:D:P04-LAYOUT-CHOICE`, `P04:D:P04-LAYOUT-LOAD`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D08`, `P05:D:P05-D10`；运行记录：[maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：用语义intent与能力匹配连接页面类型；layout名称/HTML自由创作不替代类型分类与验收。

## 素材

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | image necessity/source/job由计划规定；准备icon pool、fit/crop规则 | 允许来源与missing asset处理有Prompt，但不是已验证的所有素材获取 |
| P02 | Partial | 主机准备本地assets；review renderer仅允许跟踪file资源 | 无素材搜索/必要性算法；复杂样式PNG；converter独立goto没有同一路由保护 |
| P03 | Partial | 图片URL/生成、icon搜索、目标尺寸来自template | 图片失败可placeholder.jpg，icon无结果placeholder.svg；真实资产生成未跑 |
| P04 | Partial | images/Vision路径与图片下载；错误会warn并跳过图片 | topic image布局不保证真实资产；未实跑Vision |
| P05 | Partial | 视觉类型固定分类与定位；URL/文件图像加载；图表可PNG/native | 没有搜索/必要性算法；图像下载失败可建议文本；image-text是示意框 |

来源：

- P01：`P01:D:P01-DEC-12`, `P01:D:P01-DEC-13`, `P01:D:P01-DEC-16`；运行记录：仅源码。
- P02：`P02:D:D09`, `P02:D:D12`；运行记录：[maps-probes.json](../../research/P02/validation/maps-probes.json)。
- P03：`P03:D:P03-ASSETS`；运行记录：[verify-res-p03-05.json](../../research/P03/validation/verify-res-p03-05.json)。
- P04：`P04:D:P04-IMAGE-ANALYSIS`, `P04:D:P04-IMAGE-ASSET`；运行记录：[verify-res-p04-02.json](../../research/P04/validation/verify-res-p04-02.json)。
- P05：`P05:D:P05-D11`, `P05:D:P05-D12`；运行记录：[maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：素材获取、来源许可、几何fit与native/fallback分开；下载失败和图片替代必须可追溯。

## 模板

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | Brand/Style/Layout/Deck分层；typed slot及flat/structured输出规则 | 模板真值和完整metadata须显式；不是自动解析所有PPTX母版 |
| P02 | Partial | 唯一generic starter三槽、四种token和CSS继承；三种canvas | 非原生Master/Layout；不解析模板PPTX；只有16:9实测 |
| P03 | Partial | 16个默认模板、383布局；component/merged variants、theme、capacity模型 | 没有显式parent/extends；容量认证路径与静态模板不同；导出黑盒 |
| P04 | Partial | 5个template JSON颜色/字体/spacing/slideSize，Zod校验 | 不是PPTX母版/主题保真；缺模板拒绝 |
| P05 | Partial | 6个theme token；PPTX解析11布局/58placeholder；template路线python-pptx | 带旧slide模板KeyError(None)；独立theme关系漏读；无页模板仅子集可用 |

来源：

- P01：`P01:D:P01-DEC-07`, `P01:D:P01-DEC-19`, `P01:D:P01-DEC-20`；运行记录：[verify-res-p01-04.json](../../research/P01/validation/verify-res-p01-04.json)。
- P02：`P02:D:D04`, `P02:D:D05`；运行记录：[maps-probes.json](../../research/P02/validation/maps-probes.json)。
- P03：`P03:D:P03-TEMPLATE`, `P03:S:template-storage-and-schema`, `P03:S:template-capacity-pipeline`；运行记录：[verify-res-p03-04.json](../../research/P03/validation/verify-res-p03-04.json)。
- P04：`P04:D:P04-TEMPLATE`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D08`, `P05:D:P05-D09`；运行记录：[maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：数据化槽位/几何/token后按能力路由；单starter、内部template JSON与原生PPTX母版不同，不能等同。

## 布局

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | 先语义拓扑再SVG几何；文本fit/样式锁；typed槽位导出约束 | 主机做几何；没有确定性全局评分器；不保证所有复杂PPT对象可原生化 |
| P02 | Partial | Chromium computed DOM→inch IR；字体CDP/CSS识别；严格尺寸/底部阈值 | 单行宽+2%补偿；inlineSVG前置className错误；不是语义布局搜索 |
| P03 | Partial | 有序layout顺序；无序LLM映射；Standard schema槽位；SmartHTML | 非法索引随机替换，非评分；Smart安全启发式不是浏览器实测overflow |
| P04 | Partial | topic writer固定元素几何；HTML走PureLayout包装器/CSS子集 | topic不执行flex；父子背景等语义有差异，长文本无完整容量求解 |
| P05 | Partial | 固定英寸坐标/简单算式和shrinkText；template slot映射 | timeline最多5/process4、未记录损失；无候选检索/评分/容量测量 |

来源：

- P01：`P01:D:P01-DEC-15`, `P01:D:P01-DEC-17`, `P01:D:P01-DEC-18`, `P01:D:P01-DEC-20`；运行记录：[verify-res-p01-05.json](../../research/P01/validation/verify-res-p01-05.json)。
- P02：`P02:D:D05`, `P02:D:D06`, `P02:D:D07`, `P02:D:D08`；运行记录：[maps-probes.json](../../research/P02/validation/maps-probes.json); [footer-revision.json](../../research/P02/validation/footer-revision.json)。
- P03：`P03:D:P03-LAYOUT`, `P03:D:P03-SLOTS`, `P03:D:P03-SMART`；运行记录：[verify-res-p03-03.json](../../research/P03/validation/verify-res-p03-03.json)。
- P04：`P04:D:P04-TOPIC-RENDER`, `P04:D:P04-HTML-STRUCTURE`, `P04:D:P04-PPT-ADAPTER`；运行记录：[verify-res-p04-02.json](../../research/P04/validation/verify-res-p04-02.json); [verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D08`, `P05:D:P05-D10`；运行记录：[maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：原生对象路线需对象类型/样式/几何契约与容量实测；不得复制各项目的固定容量常量作为产品政策。

## 执行

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Observed | Quick SVG经原生builder输出3页文字/形状PPTX，并有PowerPoint只读渲染证据 | 不是全对象/Default/全编辑路径实测；主体规划是host |
| P02 | Observed | 真实DeepSeek6页HTML→固定1.1.37→PptxGenJS→LO/PDF→严格final complete | 不是产品API；非native chart；外部visual JSON失败后显式走官方host审查 |
| P03 | Partial | Web/FastAPI/SSE→DB slides→export service→@presenton/export-core1.0.34 | 仅启动200和历史428；最终导出实现黑盒，未生成PPTX |
| P04 | Observed | HTML/topic结构探针→PptxGenJS原生text/shape；实际PPTX存在 | 无真实模型/Vision/PowerPoint渲染；包装器转换子集 |
| P05 | Observed | 官方mock8页→JS PPTX；template可走Python；实际原生chart/table/notes子集 | 不是真AI生成；旧页模板失败；语言/数量/QA/低对比问题保留 |

来源：

- P01：`P01:S:preview_and_native_export`, `P01:D:P01-DEC-19`, `P01:D:P01-DEC-20`；运行记录：[verify-res-p01-05.json](../../research/P01/validation/verify-res-p01-05.json)。
- P02：`P02:D:D15`, `P02:D:D16`, `P02:D:D17`；运行记录：[verify-official-six.json](../../research/P02/validation/verify-official-six.json); [maps-probes.json](../../research/P02/validation/maps-probes.json)。
- P03：`P03:D:P03-EXPORT`, `P03:S:export-task-service`, `P03:S:export-core`；运行记录：[smoke.json](../../research/P03/validation/smoke.json); [verify-res-p03-02.json](../../research/P03/validation/verify-res-p03-02.json)。
- P04：`P04:D:P04-PPT-ADAPTER`, `P04:D:P04-TOPIC-RENDER`；运行记录：[verify-res-p04-02.json](../../research/P04/validation/verify-res-p04-02.json); [verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D01`, `P05:D:P05-D12`, `P05:D:P05-D14`；运行记录：[baseline-run.json](../../research/P05/validation/baseline-run.json); [maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：已有P01原生SVG、P02HTML原生子集、P04结构写出、P05native chart/table/notes证据；选型需RES-032许可与依赖审核，不预选环境语言。

## 可编辑性

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | 实物Quick原生文本/形状；native chart/table parity与6项edit测试共26项通过 | unsupported对象proxy；共享结构/atomic proxy修改拒绝；非全roundtrip |
| P02 | Partial | 6页各5原生文字shape；新实验原生表格，gradient为PNG | placeholder不消费；inlineSVG失败；无普通PPTX读改身份保存 |
| P03 | Partial | 内部元素树含text/shape/table/chart/group/notes等，可在DB编辑 | 全部最终OOXML由外部export-core黑盒；没有对象实物/保真编辑验证 |
| P04 | Partial | text/shape/image写入，chartData和speakerNotes未消费 | chart layout名称不等于原生chart；无普通PPTX读取/身份保真编辑 |
| P05 | Partial | 显式native charts、embedded workbook/table/notes实际写出 | 默认chart可能PNG；短series直接renderer补零；无任意PPTX原位编辑 |

来源：

- P01：`P01:D:P01-DEC-20`, `P01:D:P01-DEC-21`, `P01:S:revision`；运行记录：[verify-res-p01-05.json](../../research/P01/validation/verify-res-p01-05.json)。
- P02：`P02:D:D10`, `P02:D:D11`, `P02:D:D15`；运行记录：[verify-official-six.json](../../research/P02/validation/verify-official-six.json); [maps-probes.json](../../research/P02/validation/maps-probes.json)。
- P03：`P03:S:template-element-model`, `P03:S:chat-edit-tools`, `P03:D:P03-EXPORT`；运行记录：[verify-res-p03-05.json](../../research/P03/validation/verify-res-p03-05.json)。
- P04：`P04:D:P04-SLOT-BINDING`, `P04:D:P04-PPT-ADAPTER`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D08`, `P05:D:P05-D12`, `P05:D:P05-D13`；运行记录：[maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：OOXML对象存在、可打开、可交互编辑与保真往返分别验收；PNG回退与proxy须显式状态，不宣称全编辑。

## QA

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | SVG QualityChecker/preflight/postflight；selected parity/edit tests有证据 | 不同路线门控不同；edit receipt not-provided/stale仍exit0导出，不能当强阻断 |
| P02 | Partial | HTML逐页/导出deck真看图、hash审查和6个strict检查；资源变更失效 | 只视觉/结构count/aspect；无事实或全面可编辑性QA；外部JSON集成未通过 |
| P03 | Partial | 输入/schema与SmartHTML safety/parser局部检查 | Standard全deck事实/语义/视觉门禁Not found；没有生成QA实物 |
| P04 | Unsupported | tracked包装器只有解析/schema/output错误；没有真实生成后QA门控 | 源scope：Create/PureLayout/PPTAdapter；Pptx文件存在不表示视觉/事实通过 |
| P05 | Partial | 独立qa-visual与quality-score，LO/PDF/JPEG+bbox heuristic | 生成不自动QA；strict实际27issues exit1；暗底低对比未标高风险；非事实/像素QA |

来源：

- P01：`P01:D:P01-DEC-23`, `P01:S:svg_quality_gate`；运行记录：[verify-res-p01-05.json](../../research/P01/validation/verify-res-p01-05.json)。
- P02：`P02:D:D13`, `P02:D:D14`, `P02:D:D16`, `P02:D:D17`；运行记录：[verify-official-six.json](../../research/P02/validation/verify-official-six.json); [maps-probes.json](../../research/P02/validation/maps-probes.json)。
- P03：`P03:D:P03-SMART`, `P03:D:P03-FACTS`, `P03:D:P03-REVISION`；运行记录：[verify-res-p03-05.json](../../research/P03/validation/verify-res-p03-05.json)。
- P04：`P04:D:P04-OUTLINE`, `P04:D:P04-PPT-ADAPTER`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D14`；运行记录：[baseline-run.json](../../research/P05/validation/baseline-run.json); [visual-qa-report.json](../../research/P05/outputs/normal-qa/visual-qa-report.json)。

实现影响：采用源码/渲染/审查hash绑定的可追溯门控思路；产品还必须事实与可编辑性QA，advisory receipt不能冒充strict gate。

## 修订

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | 主机改计划/SVG重QA导出；native edit source-backed proxy有局部保留测试 | Default确认边界；复杂对象/共享master修改拒绝，非任意原件编辑 |
| P02 | Partial | 六页footer源修订、重渲染/审查/重建完成；旧源审查失效 | 全量新建，不是局部PPTX对象改写；没有自动repair agent |
| P03 | Partial | REST edit/derive与chat tools更新DB slide/component，模板导入另一路 | 无QA→RevisionPlan→保真原PPTX闭环；没有运行编辑实测 |
| P04 | Unsupported | 固定CLI/Create流程没有旧PPTX读改或QA驱动修订入口 | source scope已追踪CLI/PPTAdapter；逐页扩写不是修订闭环 |
| P05 | Partial | 旧deck JSON+指令重规划/重写；mock8→6页实物 | 不是旧PPTX原位改写；clarify裁剪无说明；theme缺失回退 |

来源：

- P01：`P01:D:P01-DEC-24`, `P01:S:revision`；运行记录：[verify-res-p01-05.json](../../research/P01/validation/verify-res-p01-05.json)。
- P02：`P02:D:D13`, `P02:D:D16`；运行记录：[footer-revision.json](../../research/P02/validation/footer-revision.json); [verify-official-six.json](../../research/P02/validation/verify-official-six.json)。
- P03：`P03:D:P03-REVISION`, `P03:S:edit-derive-api`, `P03:S:chat-edit-tools`；运行记录：[verify-res-p03-05.json](../../research/P03/validation/verify-res-p03-05.json)。
- P04：`P04:S:CLI-ROUTES`, `P04:S:CREATE-ROUTER`, `P04:D:P04-CONTENT-FILL`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:D:P05-D07`, `P05:D:P05-D09`；运行记录：[baseline-run.json](../../research/P05/validation/baseline-run.json); [maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：以局部对象范围/稳定身份/前后diff验收；JSON或HTML全量重建不自动满足普通PPTX保真编辑要求。

## 接口

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | Agent Skill与项目、source、QA、导出/原生edit脚本CLI | 固定调用链未见独立生成REST/API/MCP服务；host协议承担入口 |
| P02 | Partial | 官方CLI及两个visual MCP tools：review_slides/review_deck | MCP只源码定位、非生成服务；没有完整产品CLI/API/MCP统一入口 |
| P03 | Partial | Next.js UI、FastAPI v1/v2、SSE/jobs、OpenAPI allowlist FastMCP | 原范围排除的账号/SaaS功能不引入产品；生成接口尚未运行 |
| P04 | Partial | 命令行Create及库内engine/wrapper函数 | tracked源码没有独立HTTP/MCP/统一cancel/resume；provider前置有配置要求 |
| P05 | Partial | CLI、JSON handler、POST /skill、MCP create_deck/revise_deck | HTTP/MCP仅源码；CLI mock通过不等于所有接口真实模型验证 |

来源：

- P01：`P01:S:route`, `P01:S:project_setup`, `P01:S:preview_and_native_export`；运行记录：仅源码。
- P02：`P02:S:mcp`, `P02:D:D01`；运行记录：[verify-official-six.json](../../research/P02/validation/verify-official-six.json)。
- P03：`P03:D:P03-MODE`, `P03:D:P03-MCP`, `P03:S:direct-rest-v1`, `P03:S:smart-rest-v2`；运行记录：[smoke.json](../../research/P03/validation/smoke.json)。
- P04：`P04:S:CLI-ROUTES`, `P04:S:CREATE-ROUTER`；运行记录：[verify-res-p04-02.json](../../research/P04/validation/verify-res-p04-02.json)。
- P05：`P05:S:ENTRY-CLI`, `P05:S:ENTRY-HTTP`, `P05:S:ENTRY-MCP-CREATE`, `P05:S:ENTRY-MCP-REVISE`；运行记录：[baseline-run.json](../../research/P05/validation/baseline-run.json)。

实现影响：CLI/API/MCP共用任务与状态接口；只参考P03/P05接口分层，账号/计费等GOV-009排除项不复制。

## 安全

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | workflow限定来源、模板根、proxy编辑边界及显式no-AI/editable-only约束 | Prompt/文件规则不是主机代码执行沙箱；依赖/网络安全未全面审计 |
| P02 | Partial | review renderer拒绝非跟踪file和远程URL；配置从环境取密钥 | converter独立goto无同一路由防护；本地JS非全面沙箱；npm6 high提示未消除 |
| P03 | Partial | SmartHTML清理/限制与export输出路径校验；HTTP认证门禁 | 实际仅历史428；不是全面SSRF/沙箱/提示注入保证 |
| P04 | Partial | Zod模板/layout结构校验与HTML/CSS净化包装器 | 无统一untrusted运行沙箱证明；下载warn后跳图；仅局部源码措施 |
| P05 | Partial | request/schema与文件存在性校验；图片MIME/尺寸/URL局部规则 | 不是完整网络/执行隔离；安装7漏洞提示；来源与裁剪风险仍在 |

来源：

- P01：`P01:D:P01-DEC-07`, `P01:D:P01-DEC-12`, `P01:D:P01-DEC-24`；运行记录：[verify-res-p01-05.json](../../research/P01/validation/verify-res-p01-05.json)。
- P02：`P02:D:D12`, `P02:D:D13`, `P02:S:config`；运行记录：[maps-probes.json](../../research/P02/validation/maps-probes.json); [environment-main-skill.txt](../../research/P02/validation/environment-main-skill.txt)。
- P03：`P03:S:smart-prompt-and-validation`, `P03:S:export-task-service`；运行记录：[verify-res-p03-02.json](../../research/P03/validation/verify-res-p03-02.json)。
- P04：`P04:D:P04-TEMPLATE`, `P04:D:P04-LAYOUT-LOAD`, `P04:D:P04-HTML-CSS`, `P04:D:P04-IMAGE-ASSET`；运行记录：[verify-res-p04-04-05.json](../../research/P04/validation/verify-res-p04-04-05.json)。
- P05：`P05:S:REQUEST-JSON`, `P05:S:CLI-INPUT`, `P05:D:P05-D11`；运行记录：[environment.json](../../research/P05/validation/environment.json); [maps-probes.json](../../research/P05/validation/maps-probes.json)。

实现影响：隔离执行、资源路径/URL准入、secret注入及Prompt trust boundaries需产品级设计，局部sanitize不能当全面安全证明。

## 许可

| 项目 | 状态 | 事实 | 边界 |
|---|---|---|---|
| P01 | Partial | 固定根LICENSE为MIT | 第三方代码/模板/图标/字体许可仍须逐项审核，不推定根许可证覆盖一切 |
| P02 | Partial | 固定根及Skill LICENSE为MIT；实际converter来自pptagent1.1.37 | main许可不替代全部第三方依赖许可或资产分发审核 |
| P03 | Partial | 固定根LICENSE为Apache-2.0并有NOTICE | 外部export-core/全部依赖/素材许可未逐项确认；账号功能不因此进入范围 |
| P04 | Partial | 固定根LICENSE为MIT | 依赖PureLayout/PptxGenJS/字体/素材分别审核，尚非复用合规决定 |
| P05 | Partial | LICENSE AGPLv3、package.json AGPL-3.0-only，pyproject/lock根metadata Apache-2.0 | 声明冲突未解决；本比较不授权直接复制或裁定许可，交RES-032 |

来源：

- P01：`P01:L:LICENSE`；运行记录：仅源码。
- P02：`P02:L:LICENSE`, `P02:L:skills/pptagent/LICENSE`, `P02:D:D15`；运行记录：[converter-source.json](../../research/P02/validation/converter-source.json)。
- P03：`P03:L:LICENSE`, `P03:L:NOTICE`, `P03:D:P03-EXPORT`；运行记录：仅源码。
- P04：`P04:L:LICENSE`, `P04:D:P04-PPT-ADAPTER`；运行记录：仅源码。
- P05：`P05:L:LICENSE`, `P05:L:package.json`, `P05:L:pyproject.toml`, `P05:L:package-lock.json`；运行记录：仅源码。

实现影响：RES-032按模块和资产来源登记四种复用方式；P05冲突未解决前不得直接复制。比较文件只记录固定声明，不作法律裁定。

## 选型输入与结束条件

- 现有可编辑子集实物可支持下一步选择：P01 Quick原生SVG、P02 HTML文字/表格、P04 topic/HTML原生子集、P05显式chart/table/notes。能力不可互相推断，P05许可冲突不得越过。
- 强参考点：P01来源/类型/锁定/原生编辑边界，P02输入与审查hash门控，P03内部模板Schema和接口分层，P04数据化模板/版式，P05JSON校验及原生对象实验。模块复用方式由RES-032登记；P03账号等GOV-009排除功能不移入产品。
- 不直接沿用：无报告裁剪、分页钳制、失败跳页、随机layout替代、无说明补零、把PNG当全编辑、把缺失/过期receipt当严格通过。
- 验收：15维度每项5项目，75单元均有物理源码/Prompt范围或明确黑盒定位；正常/边界/失败用已有实物/错误和新的比较校验关联，损失/未知/历史门禁保留。达到原研究验收后进入RES-032/033，不重复安装生成。
