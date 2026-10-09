# P01：PPT Master 研究基线

## 任务与边界

- Requirement ID：`RES-P01-01`
- Task ID：`TASK-RES-P01-01`
- 研究目的：固定可核对的上游源码快照，记录官方运行要求、依赖与许可，并复现官方首个可编辑 PPTX 流程。
- 当前结论只描述 PPT Master 上游及本次研究环境，不构成 YoloongPPT 的架构、语言或运行时选型。

## 源码快照

| 项目 | 已核实值 |
|---|---|
| 上游仓库 | [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) |
| 分支 | `main` |
| 固定 commit | `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d` |
| 当前检出 | `main`，HEAD 与上述 commit 一致；克隆完成后工作树干净 |
| 对照 tag | `v6.6.0` 指向 `a50758ac29ec027e85966db33e2ae80031446756`，不是本次固定的 main 快照 |
| 研究克隆 | `F:\YoloongPPT-Research\P01`（项目仓库之外，不向本项目 vendor 上游源码） |

在可访问该 commit 的 GitHub 镜像时，可用以下命令固定到同一对象：

```powershell
git init ppt-master
git -C ppt-master remote add origin https://github.com/hugohe3/ppt-master.git
git -C ppt-master fetch --filter=blob:none --depth=1 origin 2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d
git -C ppt-master checkout --detach FETCH_HEAD
git -C ppt-master rev-parse HEAD
```

最后一条命令应输出上表中的完整 SHA。该 commit 是研究快照；上游 `main` 后续移动时，不应以新的 `main` HEAD 替代它。

## 运行时、依赖和许可证据

- 上游 [Getting Started](https://github.com/hugohe3/ppt-master/blob/2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d/docs/getting-started.md) 声明安装路径需要 Python 3.10 或更高版本，以及可读写工作区、执行命令并已认证的 Agent Host。这是 PPT Master 上游的支持条件，不是本项目选型。
- 根目录 `requirements.txt` 递归包含 `skills/ppt-master/requirements.txt`。上游清单使用 `>=` 下限约束；该快照中未找到 `pyproject.toml`、Poetry、uv、PDM 或 Pipenv 锁文件。因此目前只能固定源码 commit，不能称依赖集合已锁定。
- 仓库根 `LICENSE` 为 MIT。上游 README 和依赖清单指出 PDF 转换可选依赖 PyMuPDF 使用 AGPL-3.0；若本项目考虑复用该路径，需单独核对依赖引入及分发边界。
- 上游支持的最小运行链路见 [Generate your first deck](https://github.com/hugohe3/ppt-master/blob/2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d/docs/getting-started.md#generate-your-first-deck)：准备可读取的来源材料，通过 Agent 对话请求生成，最后得到可编辑 `.pptx`。它不是一个独立的一行 CLI 示例。

本次 P01 试验在 Docker 容器中执行，没有在 Windows Python 环境安装上游依赖，也没有把容器版本当作 YoloongPPT 的技术选型。试验使用本机已有镜像 ID `sha256:9cc4943354564a8d71825420752552f989afc8c85a66c7d396df0d0f6a5dab56`；容器内观察到 Debian 12 与 Python `3.11.2`，满足上游 Python `3.10+` 前置条件。这只是本次实验环境观测，不是项目产品要求。上游 `requirements.txt` 已在容器内安装到 F 盘临时研究目录；锁文件不存在，实际解析的 88 个发行包记录在 `artifacts/quick-smoke/pip-list.json`。根许可证为 MIT；全量依赖试验装入了可选 PDF 依赖 PyMuPDF `1.28.2`（AGPL-3.0），但不构成本项目依赖选择。清单 SHA-256、环境镜像 ID 和许可边界见 `artifacts/quick-smoke/environment.json`。

## 本次环境观测与复现状态

- 2026-10-07 检查时 Docker CLI、Engine 与 Compose 均可用；项目 `compose.yaml` 的通用 workspace 容器保持原样。
- PPT Master 安装目录以只读方式挂载；项目工作目录和实验依赖目标通过独立挂载提供给临时容器。容器内先运行 `attribution_guard.py`，再按上游要求安装并检查依赖；`import pptx; import fitz` 通过。
- 复现使用上游 FAQ 推荐的三页 Quick “Hello World”烟测。`project_manager.py init` 在只读源码目录默认路径下按预期以 `OSError errno=30` 失败；指定可写的 `--dir /workspace/research/P01/projects` 后初始化成功。
- 三页 PPTX 的最终检查器和 Postflight 均通过；包可由 `python-pptx` 读取，ZIP 完整，17 个文本对象及 DrawingML 形状均保留，未发现图片、图表、备注、转场或 timing。最终文件 SHA-256 为 `c39b6b596b6c6df0c69d8bdc2886eac5d1339cab5f148833951f1370095acd25`。
- 当前 Docker 实验镜像没有 PowerPoint 或 LibreOffice。另用本机已有 Microsoft PowerPoint 16.0 以只读方式打开生成文件，并通过 [Slide.Export](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.export) 导出三张 1920×1080 PNG；三页视觉复核均通过，未见裁切、遮挡或缺字。图片及 SHA-256 见 `projects/p01_hello_world_20261007/validation/native-render/` 与 `verify-res-p01-01.json`。本机 Office 仅用于验证，不是 Docker 项目运行环境或 YoloongPPT 产品依赖。

| 验收项 | 状态 | 证据 |
|---|---|---|
| 固定 branch / commit | 已完成 | `main` / `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d` |
| 查明锁文件、运行要求与许可证 | 已完成 | 固定源码、`requirements.txt`、`LICENSE`、环境及发行包清单 |
| 官方 Quick 最小流程 | 已完成 | `projects/p01_hello_world_20261007/`、最终 PPTX 与 Postflight 报告 |
| `VERIFY-RES-P01-01` 正常/边界/失败证据 | 已完成 | `projects/p01_hello_world_20261007/validation/verify-res-p01-01.json`、`validation/native-render/slide-01.png` 至 `slide-03.png`；PowerPoint 16.0 只读打开及视觉复核通过 |

因此 `TASK-RES-P01-01`、`VERIFY-RES-P01-01` 与 `RES-P01-01` 均已完成。`TASK-RES-P01-02`、`VERIFY-RES-P01-02`、`TASK-RES-P01-03`、`VERIFY-RES-P01-03` 均已按矩阵完成。

## RES-P01-02：调用链与源码索引

- `TASK-RES-P01-02`、`VERIFY-RES-P01-02` 与 Requirement `RES-P01-02` 已完成。根据固定 commit 的工作流、Prompt、Schema、CLI 和组包代码，分别建立 Default 源码调用图与 Quick 运行轨迹索引。
- [call_graph.md](call_graph.md) 描述 Default、Quick 两条路径、条件节点、revision 和外部边界；[source_index.json](source_index.json) 为 12 个节点、13 条边记录上游文件、函数/Prompt/Schema 和固定源码行。所有本地文件及引用行经脚本检查存在。
- `validation/verify-res-p01-02.json` 记录正常 Quick 生成、Quick/Default 路由边界，以及只读默认写入路径 `OSError errno=30` 的失败证据。其正常运行轨迹复用 `workflow.log`、PPTX、Postflight、ZIP/读取检查和 PowerPoint 16.0 渲染证据。
- 运行与静态研究边界：Quick 有实际运行记录；Default 仅追踪源码，没有声称 Default 已运行。LLM/Agent Host 调度与本机/第三方 Office 渲染标为外部黑盒。环境中的 Python 版本仍只是实验观察，不代表 YoloongPPT 的语言、运行时或依赖选型；项目 Docker 配置未变。
- 后续任务严格按矩阵依赖继续：`TASK-RES-P01-03`（决策节点）和 `TASK-RES-P01-04`（模板/版式/中间表示）已完成；`TASK-RES-P01-05` 也已完成，见下节收尾证据。

## RES-P01-03：页面结构与视觉决策节点

- `TASK-RES-P01-03`、`VERIFY-RES-P01-03` 与 Requirement `RES-P01-03` 已完成。依据固定源码整理 24 个上游决策节点，逐项记录输入、候选、机制、输出、fallback、源码位置和统一 DEC 映射。
- [decision_map.md](decision_map.md) 为人读摘要；[project_decision_map.json](project_decision_map.json) 为结构化 ProjectDecisionMap，映射 DEC-001–DEC-040 共 40 个节点，并将 PPT Master 特有的 Quick/Default、两阶段确认、flat/structured 和 SVG 主笔责任单独标记。
- 这些 crosswalk 是源码研究，不表示产品决策已实现或已验收。Agent/LLM 隐藏推理没有确定性评分器或完整 trace 时保留为外部黑盒；Quick 烟测只证明已选路径产物，不证明全部决策节点运行。
- `validation/verify-res-p01-03.json` 记录正常 Quick、路由边界、只读写入失败样例和限定范围；默认路径失败为 `OSError errno=30`，此前已有实测日志，本次未重复触发。

## RES-P01-04：模板、版式与中间表示

- `TASK-RES-P01-04`、`VERIFY-RES-P01-04` 与 Requirement `RES-P01-04` 均已完成。依据固定 PPT Master commit 建立 [ProjectTemplateMap](project_template_map.json)，逐页记录主要 Layout 原型、画布、PowerPoint Layout key、slot、geometry、Design Spec tokens、用途和源码定位。
- 资产盘点：21 个 Brand、14 个 Style、7 个 Layout、2 个 Deck；7 组 Layout 共 86 个 SVG 原型、53 种页面类型、320 个显式 slot 和 287 个 Design Spec token。每个 slot 的正数 bounds 均通过检查；两个 Blank 原型是合法零-slot 页面。
- 模板类型边界：Brand、Style、Layout、Deck 是正交类型，不构成继承层级。Chart 33 项、Table 6 种是页面级可视化族；图标库 12,027 个向量，均不作为模板类型。索引内容与源 SHA-256 保存在 map。
- 表示结构：保留 Markdown Design Spec、spec_lock Schema、逐页 SVG 元数据和可选原生 Chart/Table payload 的边界；没有把它们虚构成统一规范化 IR。Layout SVG 的 token 列表与 slot 角色分别记录，源码没有声明一对一绑定。
- 容量边界：每个 slot 记录 SVG user units 下的 x/y/width/height、面积与画布比例。源码将 bounds 定义为几何容量区域，但没有统一字符数或行数上限；map 明确保留为未定义，不猜测文本容量。
- 适用条件：记录 library/explicit 选择来源、standard/fidelity/mirror 创建方式、style/layout/mirror 复用范围、strict/adaptive 遵循方式及 flat/structured 结构模式；结构只能依据显式声明，不自动推断或升级旧契约。
- 核验：固定源码 commit 校验、7/86/53/320 计数、索引声明数量、86/86 roster 映射、86/86 viewBox、320/320 有效 bounds 均通过。首次解析因 report_core 多出 Master 列未映射 13 行；按源码实际两种表结构修正后重跑通过。详见 [verify-res-p01-04.json](validation/verify-res-p01-04.json)。
- 这是上游源码研究结果，不表示 YoloongPPT 已实现 PPT Master 资产或选择其架构；项目语言/运行时仍未选定，compose.yaml 未改动。后续 `TASK-RES-P01-05` 已完成，见下节。

## RES-P01-05：PPT 写入、渲染、QA、修订与既有 PPT 编辑边界

- `RES-P01-05`、`TASK-RES-P01-05`、`VERIFY-RES-P01-05` 依赖的 `RES-P01-02` 已满足。本项建立 [ProjectCapabilityMap](project_capability_map.json)，按需求矩阵的 `PPT-001`–`PPT-030` 逐项记录 Native/Partial/Fallback/Unsupported 状态、固定源码证据、Quick smoke 观察范围和明确限制。
- 分类是对固定 PPT Master commit `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d` 的源码研究归一化，不是上游自带状态，也不是 YoloongPPT 已实现状态。各能力均带有源码锚点；仅验证报告列出的 26 项测试已执行，其余仍是源码证据。
- QA/Revision 分别记录 SVG 导出前质量门、PPTX 离线 package 检查、浏览器 SVG 视觉预览、外部 PowerPoint 最终渲染、read-back，以及 SVG 页面修订、既有 PPTX round-trip 和 opaque proxy 边界。
- 既有 PPT 编辑边界：只编辑已确认 plan 中页面；未改页可 passthrough；Master/Layout 继承对象与 source proxy 不可编辑；不支持 round-trip 中改 slide size 或新增 Master/Layout；SmartArt、复杂效果、media/OLE 按 atomic proxy 保留；notes、motion 是按输出页挂接的 overlay。
- 正常证据复用 P01-01 三页 Quick smoke：PPTX/ZIP/读取检查通过，每页分别有 7/16/7 个可编辑 shapes、4/9/4 个文本 shapes；图片、图表、notes、transition、timing 均为 0。Microsoft PowerPoint 16.0 主机只读渲染三页并视觉复核通过。该证据不覆盖 P01-05 的 charts/tables/media/motion 或 round-trip。
- 2026-10-09 收尾：WSL/Docker 恢复后，在 F 盘数据的禁网研究容器中复用原依赖，执行 6 项编辑边界/失败用例及 20 项原生图表/表格一致性用例，26/26 通过，无失败、错误或跳过；上游源码只读。继承对象删除/编辑、proxy ancestor 修改、SmartArt adopt/修改均按预期抛出明确异常。见 [测试结果](validation/p01-boundary-tests.json) 和 [原始输出](validation/p01-boundary-tests.txt)。
- QA 实测限制：page_plan/SVG 改动让 receipt 变为 stale，重跑 QA 后 passed；not-provided/stale 仍允许导出，不能据此宣称强制阻断。图表/表格测试是选定上游断言，不是最终 Office 保真或产品 AC 验收。hyperlink、semantic text contract 和其他未选边界仍未运行。
- `RES-P01-05`、`TASK-RES-P01-05`、`VERIFY-RES-P01-05` 已完成候选研究。以前的环境阻塞仅保留为历史，见 [verify-res-p01-05.json](validation/verify-res-p01-05.json)。下一工作包按原依赖收尾 P02/P05 剩余研究，随后形成 RES-031 横向对照。
- 本项不修改 `compose.yaml`，不选择 YoloongPPT 产品语言、运行时或依赖版本。

## 来源

- [PPT Master 固定源码快照](https://github.com/hugohe3/ppt-master/tree/2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d)
- [Docker Desktop WSL 2 后端](https://docs.docker.com/desktop/features/wsl/)
- [Docker Desktop Windows FAQ：Engine 连接端点](https://docs.docker.com/desktop/troubleshoot-and-support/faqs/general/)
