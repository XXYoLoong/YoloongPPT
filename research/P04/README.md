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

## 最小流程复现与运行边界

本节 Node 版本仅记录一次性研究容器中的环境观测，不代表 YoloongPPT 产品运行时选型。

### 隔离环境

- 上游源码副本固定在 c3605ebc487fc6c7d4f4139761e46d7021cd656c，使用锁文件副本，SHA-256 为 f9a2b016df533d79d7c55207c699d84d754b9178be9cb421e1c43259b48f4a68；官方 clone 位于 F:/YoloongPPT-Research/P04，本次 npm 安装与构建在 F:/YoloongPPT-Temp-P01-05 的临时副本完成。
- Docker Desktop 实际数据文件为 F:/DockerDesktopWSL/disk/docker_data.vhdx。Node 容器仅挂载 F 盘研究副本和输出目录，运行使用 --network none；HTML 路径只使用隔离配置中的 dummy 值，不发起模型/API 请求。
- 上游 package.json 声明 Node.js >=18.0.0。Node 18.20.8 / npm 10.8.2 下 npm ci --no-audit --no-fund 安装 219 个包，npm run build 成功。未运行上游测试。
- Node 18.20.8 镜像 digest：node@sha256:f9ab18e354e6855ae56ef2b290dd225c1e51a564f87584b9bd21dd651838830e；Node 24.14.0 镜像 digest：node@sha256:d8e448a56fc63242f70026718378bd4b00f8c82e78d20eefb199224a4d8e33d8。

### 正常、边界和失败样例

| 类别 | 输入与环境 | 实际结果 | 产物 / 证据 |
|---|---|---|---|
| 正常 | README 的 HTML 最小示例（--html），Node 24.14.0，隔离 dummy config | 解析 1 个元素、完成单页渲染、退出码 0 | validation/minimal-html-poc.pptx；SHA-256 D6BD31369C7F07073886A689D4F45BE7163E9FD396B5692128B5700D78045383；45,012 字节 |
| 边界 | 嵌套 div / p / strong / span、内联字号与颜色，Node 24.14.0 | 解析 4 个元素、保存 PPTX、退出码 0；slide XML 含 Nested | validation/edge-nested-html-poc.pptx；SHA-256 0B142B904F7D041BEF066813AF9A10C6D778CA74C593950493EE2E866B75D3FA；47,372 字节 |
| 失败 | 已配置隔离 dummy config，但 create 未提供 --topic、--input、--html 或 --images，Node 24.14.0 | 退出码 1；输出 Create failed: Provide --topic, --input, --html, or --images；未访问网络 | validation/verify-res-p04-01.json |

两个 PPTX 均可作为 ZIP 打开，含 <code>[Content_Types].xml</code>、<code>ppt/presentation.xml</code> 与 <code>ppt/slides/slide1.xml</code>，各有 39 个 ZIP 条目；完成的是包结构与文本检查，没有做 Office/LibreOffice 渲染或视觉质量审阅。

### Node 18 声明兼容范围偏差

Node 18.20.8 下的官方 CLI HTML 样例失败，报错为 SyntaxError: Cannot use import statement outside a module，位置在 node_modules/pptxgenjs/dist/pptxgen.es.js 第 2 行（import JSZip from 'jszip';）。单独执行 require('pptxgenjs') 则成功并返回构造函数。锁文件固定 pptxgenjs@4.0.1；该包 package.json 没有 type 字段，exports.import 指向 ./dist/pptxgen.es.js，exports.require 指向 ./dist/pptxgen.cjs.js。同一官方 HTML 样例在 Node 24.14.0 离线容器成功。

结合 Node 18 的包类型规则和上述包元数据，当前证据指向 ESM .js 入口在 Node 18 下被按 CommonJS 解析；这是对运行错误来源的判断。上游声明的 >=18.0.0 与本次 Node 18.20.8 样例结果存在兼容偏差。未修改上游文件，也未把 Node 24 记为 YoloongPPT 的产品运行时。

### 许可与结论边界

固定上游仓库根许可证为 MIT。锁文件中的 pptxgenjs@4.0.1 包元数据也声明 MIT；其余传递依赖的逐包许可证清单和法律兼容性审查不属于本次完成范围。固定版本、官方流程复现和正常/边界/失败运行证据已完成。P04-02/03 的完整调用链与决策节点研究仍是独立后续任务。

未运行上游测试套件；没有验证截图识别、LLM 生成、广泛 HTML/CSS 支持、视觉质量、PowerPoint 编辑行为或 YoloongPPT 产品能力。候选项目结果不能外推为产品功能承诺。

## 固定来源

- [ai-agent-ppt 官方固定快照](https://github.com/peterfei/ai-agent-ppt/tree/c3605ebc487fc6c7d4f4139761e46d7021cd656c)
- [固定快照 README](https://github.com/peterfei/ai-agent-ppt/blob/c3605ebc487fc6c7d4f4139761e46d7021cd656c/README.md)
- [CLI 入口](https://github.com/peterfei/ai-agent-ppt/blob/c3605ebc487fc6c7d4f4139761e46d7021cd656c/src/index.ts)
- [生成命令](https://github.com/peterfei/ai-agent-ppt/blob/c3605ebc487fc6c7d4f4139761e46d7021cd656c/src/commands/create.ts)
- [Node.js 18 包规则](https://nodejs.org/download/release/v18.20.7/docs/api/packages.html)
- [Node.js 22.12 语法检测规则](https://nodejs.org/download/release/v22.12.0/docs/api/packages.html)
- [PptxGenJS 4.0.1 包元数据](https://www.npmjs.com/package/pptxgenjs/v/4.0.1)
