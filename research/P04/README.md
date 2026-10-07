# P04：ai-agent-ppt 研究基线

## 任务与范围

- Requirement ID：`RES-P04-01`
- Task ID：`TASK-RES-P04-01`
- 研究目的：固定 ai-agent-ppt 上游源码，记录 branch/commit、锁文件、运行条件和许可证，并尝试官方最小流程。
- 本文只保留上游研究证据，不据此选择 YoloongPPT 产品语言、运行时或 PPTX 后端。完整调用链与决策节点由 PDR 中的 `RES-P04-02`、`RES-P04-03` 任务继续研究。

## 固定源码快照

2026-10-07 查询官方 Git remote，`refs/heads/main` 指向 `c3605ebc487fc6c7d4f4139761e46d7021cd656c`，与 GOV-010 的 `P04-MAIN` pinned commit 一致。研究 clone 位于仓库外 `F:\YoloongPPT-Research\P04`，当前 detached HEAD 为该 commit，工作树干净。

复现固定 checkout：

```powershell
git clone --filter=blob:none --depth=1 --no-checkout https://github.com/peterfei/ai-agent-ppt.git F:\YoloongPPT-Research\P04
git -C F:\YoloongPPT-Research\P04 checkout --detach c3605ebc487fc6c7d4f4139761e46d7021cd656c
git -C F:\YoloongPPT-Research\P04 rev-parse HEAD
```

最后一条命令应输出 `c3605ebc487fc6c7d4f4139761e46d7021cd656c`。

## 锁文件、上游运行条件与许可证

| 文件 / 范围 | 固定信息 | SHA-256 |
|---|---|---|
| `package.json` | `ai-agent-ppt@0.1.0`；声明 Node.js `>=18.0.0`；依赖包括 `pptxgenjs`、`purelayout`、TypeScript、Vitest | — |
| `package-lock.json` | npm `lockfileVersion: 2`；根包 `0.1.0` | `f9a2b016df533d79d7c55207c699d84d754b9178be9cb421e1c43259b48f4a68` |
| `LICENSE` | MIT © peterfei | `7e5fa1c85294d445491eeb8cc1f72d8fb53d619d0613604831d499c60d63afb2` |

README 和中文手册要求 Node.js `>=18.0.0`；没有发现 `.nvmrc`、`.node-version`、`.tool-versions`、Dockerfile 或 Compose 文件，因此没有固定 Node 补丁版本或上游容器环境。这些都是候选项目的上游信息，不代表 YoloongPPT 已选择 Node。

## 架构与运行入口观察

- 上游定位为 CLI。README 声明 8 种布局、5 种主题与 topic/document、HTML、截图三种输入路线；这些能力只在本次静态源码中核对了入口和关键组件，尚未通过生成产物验证。
- `src/index.ts` 先加载配置并创建 Provider，之后才把命令交给 `CreateCommand`。`src/commands/create.ts` 将 `--html` 路由到 `PureLayout` → `PPTAdapter`，主题/文档路由使用大纲与内容生成器、layout/slot 和 `PPTXBuilder`；图片路由调用视觉 Provider 并把解析结果交给布局适配器。
- `PureLayout` 使用 `purelayout` 解析 HTML 与内联样式、计算元素几何；`PPTAdapter` 将文字和图像映射到 PptxGenJS 元素 API。Provider registry 实际只注册 `deepseek` 和 `glm`；`claude`、`openai`、`kimi` 在配置类型/README 中列为预留，不能按已支持能力处理。
- 官方文档将 HTML 路径说明为绕过 LLM，但 CLI 入口仍无条件要求已有配置并先创建 Provider；因此它可能不调用模型，却不是无配置的启动路径。最小复现需要在隔离环境中确认这一配置前置条件，不能仅以 README 的 HTML 示例推断。
- 仓库包含 unit 与 integration 测试文件；README 宣称测试数量和覆盖率门槛，但本任务未运行这些测试，也不把上游声明当作验证结果。

## 最小流程尝试与阻塞

PDR 要求先运行官方最小示例。项目隔离容器启动命令 `scripts/project.ps1 start` 已实际尝试，但 Docker CLI 不能连接 `desktop-linux` Engine：`//./pipe/dockerDesktopLinuxEngine` 不存在。当前项目基础镜像只安装 bash、ca-certificates 和 git；在没有确认产品技术栈前，本任务没有把 Node 装入项目镜像，也没有在 Windows 主机安装依赖。未执行 `npm ci`、构建、上游测试或 HTML/PPTX 样例，未生成 PPTX。

因此，源码 refs、锁文件、许可证、上游运行条件和关键入口已静态记录，但 `ProjectBaseline` 验收尚未完成，`TASK-RES-P04-01` 保持进行中。Docker Engine 恢复后，应在隔离容器中按固定 commit 安装锁文件依赖，先验证 README 的 HTML 最小样例及其配置前置，再记录日志、PPTX 和结构回读结果。

## 固定来源

- [ai-agent-ppt 官方固定快照](https://github.com/peterfei/ai-agent-ppt/tree/c3605ebc487fc6c7d4f4139761e46d7021cd656c)
- [固定快照 README](https://github.com/peterfei/ai-agent-ppt/blob/c3605ebc487fc6c7d4f4139761e46d7021cd656c/README.md)
- [CLI 入口](https://github.com/peterfei/ai-agent-ppt/blob/c3605ebc487fc6c7d4f4139761e46d7021cd656c/src/index.ts)
- [生成命令](https://github.com/peterfei/ai-agent-ppt/blob/c3605ebc487fc6c7d4f4139761e46d7021cd656c/src/commands/create.ts)
