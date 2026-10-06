# YoloongPPT 产品范围声明

**Requirement ID：`GOV-009`**

**Task ID：`TASK-GOV-009`**

## 当前核心范围

- CLI、API、MCP 和调试入口属于系统核心要求。
- 其它产品能力仍以根目录《AI_PPT_PDR_完整需求定义_V0.3.docx》和《AI_PPT_完整需求与任务矩阵_V0.3.xlsx》的 Requirement ID、约束和验收为准；本文件不替代需求基线。

## 当前明确排除

当前需求不包含以下 SaaS 产品功能：

- 账号
- 计费
- 多租户
- 协同编辑
- 模板商城

这些事项是当前范围的明确排除项，不作为本轮交付遗漏。模板生成、解析或使用能力是否属于范围，应依据需求基线中的具体 Requirement ID 判断，不能将“模板商城”扩展解释为排除所有模板能力。

## Agent 交接

项目 Agent 入口 [AGENTS.md](AGENTS.md) 和需求矩阵“Codex交接”表 `CH-013` 均引用本声明。执行任务时同时遵守 `GOV-009` 与具体需求行，不能以 SaaS 边界排除 CLI/API/MCP/调试入口，也不能把明确排除项悄然加入交付范围。
