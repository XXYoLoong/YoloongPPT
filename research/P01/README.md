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

本次没有在宿主机安装 Python，也没有记录某个 Python 小版本为本项目要求。Docker 服务端不可响应，故尚未创建容器、安装上游依赖或运行生成链路；上游运行环境版本仍待隔离复现后按实际镜像摘要和容器输出记录。

## 本次环境观测与复现状态

- Windows Docker CLI：`27.4.0`；当前 Docker context：`desktop-linux`；WSL 2 中 `docker-desktop` 发行版处于运行状态。
- 本机 `docker version` 服务端查询 20 秒超时；对 `dockerDesktopLinuxEngine` 和官方 Windows 默认 `docker_engine` 命名管道发送只读 `GET /_ping`，均未收到响应。
- Docker Desktop 本地日志报告因磁盘空间不足无法写入 VM 日志；Docker WSL 中 `/mnt/host/c` 观测为约 75 MB 可用、显示 100%。C: 上本任务此前失败的临时克隆已转移到 F: 并校验 SHA，当前 API 仍无响应。此证据记录相关状态，不据此单独断言引擎无响应的唯一根因。
- 本机的 `docker --version` 成功，证明 CLI 可执行；没有证据证明容器服务可用。

| 验收项 | 状态 | 证据 |
|---|---|---|
| 固定 branch / commit | 已完成 | `main` / `2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d` |
| 查明 lock 文件、运行要求与许可证 | 已完成（上游静态证据） | 上述官方文档、`requirements.txt`、`LICENSE` |
| 官方最小流程 | 未运行 | Docker API 探测未响应；未安装依赖、未生成 PPTX |
| `VERIFY-RES-P01-01` 正常/边界/失败证据 | 未开始 | 依赖实际运行链路 |

因此 `RES-P01-01` 与 `TASK-RES-P01-01` 保持进行中；`VERIFY-RES-P01-01` 及依赖它的 `TASK-RES-P01-02` 不标为完成或开始。后续应在 Docker API 恢复后，在隔离容器里运行上游最小流程并记录实际运行环境与生成物，再开始调用链拆解。

## 来源

- [PPT Master 固定源码快照](https://github.com/hugohe3/ppt-master/tree/2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d)
- [Docker Desktop WSL 2 后端](https://docs.docker.com/desktop/features/wsl/)
- [Docker Desktop Windows FAQ：Engine 连接端点](https://docs.docker.com/desktop/troubleshoot-and-support/faqs/general/)
