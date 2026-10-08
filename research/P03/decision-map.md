# Presenton 结构与视觉决策图

任务：RES-P03-03 / TASK-RES-P03-03
固定源码：presenton/presenton，commit 35bf44290f821323e003da854f78ffcb0e918167

## 结论

决策图记录 17 个源码级节点，并逐项交叉映射矩阵 DEC-001–DEC-040。每个节点在 decision-map.json 中包含输入、候选、机制、输出、fallback、状态和 source-index.json 源码定位。

固定源码明确实现了 Standard/Smart 路由、请求默认值和边界、模板解析、ordered/unordered 布局分支、目录页插入、TemplateV2 schema、Smart HTML 安全处理及部分素材 fallback。其他决策有些由模型 prompt 隐式生成，有些没有独立对象或规则。

## DEC 交叉映射

| 状态 | DEC ID | 解释 |
|---|---|---|
| 已映射 | DEC-001、013、024、028、030、032 | 源码中存在可定位的直接路由、页数/素材/模板/layout/schema 决策。 |
| 部分映射 | DEC-002、003、005、008–012、014–020、022–023、025–027、029、031、033–037、039–040 | 有字段、模板约束、prompt 或局部处理，但缺少完整候选/评分/追踪契约或运行证据。 |
| 未发现等价独立机制 | DEC-004、006、007、021、038 | 固定源码中没有显式来源冲突解决、受众分类、场景分类、引用位置规划或多后端能力选择。 |

逐 ID 的节点与证据在 decision-map.json 的 decCrosswalk 中。未发现独立机制只表示没有在固定调用链中定位到对应实现，不表示这些产品需求可以省略。

## 关键结构与视觉决策

| 代码节点 | 对应全局决策 | 已观察机制 | 缺口 |
|---|---|---|---|
| P03-MODE | DEC-001 | Standard/Smart 和 REST/MCP 入口分流 | 无意图自动分类 |
| P03-OUTLINE | DEC-009–012、015–020 | Prompt + Outline schema | thesis、graph、storyline、intent 未独立建模 |
| P03-PAGE-TOC | DEC-013–015、037 | 页数预算、标题页/目录页数量与位置 | 无章节预算；未发现动画选择 |
| P03-TEMPLATE | DEC-028/029/035 | 用户模板、TemplateV2 theme/fonts | 无跨模板评分和统一 DesignTokens |
| P03-LAYOUT | DEC-017/030/031 | 选中模板内的 layout 索引；无序布局交给 LLM | 无显式评分；异常索引会随机替换 |
| P03-SLOTS | DEC-018/019/032 | 模板 schema 约束内容并绑定 UI | 无标准路径渲染后容量/溢出验证 |
| P03-VISUAL | DEC-022、025–027 | 模板对象 schema 与 Smart 视觉/图表 prompt | 实际生成选择未运行验证 |
| P03-ASSETS | DEC-023/024/036 | 用户 URL、图片生成、图标搜索和模板目标尺寸 | 部分失败以 placeholder 替代 |
| P03-SMART | DEC-017、022、029、033–035 | 1280×720 HTML prompt、安全检查及 smart-html 检查点 | prompt 约束不等于浏览器渲染 QA |
| P03-REVISION | DEC-039 | Smart 安全/恢复、素材 fallback、用户 chat 编辑 | 无 deck QA 到 RevisionPlan 闭环 |
| P03-TRACE | DEC-040 | SSE/async 完成与错误状态 | 无完整 DecisionTrace 对象 |
| P03-EXPORT | DEC-038 | PDF/PPTX 输出格式及固定 exporter | 不做多后端能力选择 |

## 项目特有分支

- REST 提供 slides_markdown 时，每项直接映射为一个 outline，绕过 outline 生成模型。
- Standard 模板为 ordered 时直接采用其布局顺序；unordered 时才调用 LLM 分配布局索引。
- Smart 独立产出分隔符包裹的 HTML section，并将接受的页面保存为 smart-html；它与 Standard JSON/template UI 数据模型不同。
- MCP 是 OpenAPI allowlist 适配层。PPTX/PDF exporter 固定为外部 @presenton/export-core v1.0.34，内部实现不在 clone 中。

## 验证边界

本交付是固定源码静态映射。没有执行模型生成、layout 决策、PPTX/PDF 导出或浏览器视觉 QA。当前登录初始化门禁先返回 HTTP 428；运行证据引用 validation/verify-res-p03-03.json，不能据此宣称任何布局或视觉决策通过。
