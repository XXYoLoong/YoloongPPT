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

因此 `TASK-RES-P01-01`、`VERIFY-RES-P01-01` 与 `RES-P01-01` 均已完成。`TASK-RES-P01-02`、`VERIFY-RES-P01-02`、`TASK-RES-P01-03`、`VERIFY-RES-P01-03` 均已按矩阵完成；当前下一项为 `TASK-RES-P01-04`。

## RES-P01-02：调用链与源码索引

- `TASK-RES-P01-02`、`VERIFY-RES-P01-02` 与 Requirement `RES-P01-02` 已完成。根据固定 commit 的工作流、Prompt、Schema、CLI 和组包代码，分别建立 Default 源码调用图与 Quick 运行轨迹索引。
- [call_graph.md](call_graph.md) 描述 Default、Quick 两条路径、条件节点、revision 和外部边界；[source_index.json](source_index.json) 为 12 个节点、13 条边记录上游文件、函数/Prompt/Schema 和固定源码行。所有本地文件及引用行经脚本检查存在。
- `validation/verify-res-p01-02.json` 记录正常 Quick 生成、Quick/Default 路由边界，以及只读默认写入路径 `OSError errno=30` 的失败证据。其正常运行轨迹复用 `workflow.log`、PPTX、Postflight、ZIP/读取检查和 PowerPoint 16.0 渲染证据。
- 运行与静态研究边界：Quick 有实际运行记录；Default 仅追踪源码，没有声称 Default 已运行。LLM/Agent Host 调度与本机/第三方 Office 渲染标为外部黑盒。环境中的 Python 版本仍只是实验观察，不代表 YoloongPPT 的语言、运行时或依赖选型；项目 Docker 配置未变。
- 后续任务严格按矩阵依赖继续：`TASK-RES-P01-03`（决策节点）已完成；当前下一项是 `TASK-RES-P01-04`（模板/版式/中间表示），`TASK-RES-P01-05` 仍未开始。

## RES-P01-03：页面结构与视觉决策节点

- `TASK-RES-P01-03`、`VERIFY-RES-P01-03` 与 Requirement `RES-P01-03` 已完成。依据固定源码整理 24 个上游决策节点，逐项记录输入、候选、机制、输出、fallback、源码位置和统一 DEC 映射。
- [decision_map.md](decision_map.md) 为人读摘要；[project_decision_map.json](project_decision_map.json) 为结构化 ProjectDecisionMap，映射 DEC-001–DEC-040 共 40 个节点，并将 PPT Master 特有的 Quick/Default、两阶段确认、flat/structured 和 SVG 主笔责任单独标记。
- 这些 crosswalk 是源码研究，不表示产品决策已实现或已验收。Agent/LLM 隐藏推理没有确定性评分器或完整 trace 时保留为外部黑盒；Quick 烟测只证明已选路径产物，不证明全部决策节点运行。
- `validation/verify-res-p01-03.json` 记录正常 Quick、路由边界、只读写入失败样例和限定范围；默认路径失败为 `OSError errno=30`，此前已有实测日志，本次未重复触发。
## 来源

- [PPT Master 固定源码快照](https://github.com/hugohe3/ppt-master/tree/2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d)
- [Docker Desktop WSL 2 后端](https://docs.docker.com/desktop/features/wsl/)
- [Docker Desktop Windows FAQ：Engine 连接端点](https://docs.docker.com/desktop/troubleshoot-and-support/faqs/general/)
