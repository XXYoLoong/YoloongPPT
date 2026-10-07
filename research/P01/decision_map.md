# PPT Master 页面结构与视觉决策图

- Requirement ID：RES-P01-03
- Task ID：TASK-RES-P01-03；验证：VERIFY-RES-P01-03
- 上游固定版本：`hugohe3/ppt-master` main commit `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d`
- 结构化主表：[project_decision_map.json](project_decision_map.json)

## 覆盖范围

决策图按输入路由、来源与事实边界、沟通与阅读模式、故事线/页数/页面意图、模板与 Master/Layout、图像/图标/表格/图表、颜色/字体/几何/拓扑、动画备注、质量回退与 revision 分类，提取 24 个上游决策节点。每个节点均记录输入、候选、机制、输出、fallback、源码位置和对应的统一 DEC ID。

共映射 DEC-001–DEC-040 40 个统一决策 ID。映射表示“上游有相近决策证据”，不表示节点等价、产品已实现或产品已验证。Quick/Default 路由、两阶段确认、flat/structured SVG 契约及 Agent 主导 SVG 落笔标记为 PPT Master 项目特有机制。

## 关键发现

- 多数内容、样式和版式选择由 Strategist/Executor Prompt 指导 Agent/LLM 作出；仓库没有通用模型调用循环，也未发现统一的确定性评分器。未定义的评分、候选生成或 fallback 保留为未定义，不以本项目规则补齐。
- Default 将 Stage 1/2、确认结果和部分设计决策持久化到 `design_spec.md` / `spec_lock.md`；Quick 在当前 Agent 上下文中暂存，不写这两份文件。
- Executor 决定具体载体、拓扑、形状轮廓和几何，全部可见页面内容以 SVG 为权威；PPTX 转换仅按 flat 或显式 structured 契约组包。
- 图表/表格是否值得使用与能否转为原生对象是两项独立判断。结构化 slot 缺少要求的对象能力时会拒绝编译，不应假设自动降级。
- QA 报告与 Postflight 决定能否交付；错误阻断导出、warning 为 advisory。Revision 回到各自路线拥有的源文件并重跑检查与导出。

## 证据边界

P01-01 Quick 烟测观察到三页输出、最终 SVG 检查通过和 PPTX Postflight 通过；这些证据确认所选路径和产物，不暴露 Agent 内部候选/评分/推理。Default 仅做源码研究，未声称运行。模板、图表、图像、动画等未在烟测中执行的节点仍为源码证据。

正常/边界/失败样例、实际/静态状态和错误记录见 `projects/p01_hello_world_20261007/validation/verify-res-p01-03.json`。本研究未将任何 DEC 标为 YoloongPPT 已实现或已验收。
