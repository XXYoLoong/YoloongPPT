# P02：PPTAgent / DeepPresenter 研究基线

## 任务与范围

- Requirement ID：`RES-P02-01`
- Task ID：`TASK-RES-P02-01`
- 研究目的：固定上游源码 refs，记录依赖锁、环境条件和许可证，并复现官方最小流程。
- 本文只记录 PPTAgent / DeepPresenter 上游；不把其运行时、语言或后端选为 YoloongPPT 产品架构。

## 源码 refs

在 2026-10-07 对官方 Git remote 执行 `git ls-remote`，并在隔离于产品代码的研究目录检出固定对象：

| 快照 | 上游 ref | 固定对象 | 备注 |
|---|---|---|---|
| 当前 main / Skill | `refs/heads/main` | `833cda553b343be0e486a93b0b57cac962cdd566` | 当前分支的主线是 agent Skill；远端 main 与该 commit 一致 |
| PPTAgent 论文快照 | `refs/tags/v0.2.0` | `d53296bc0ddd73e81d51c523d20dd711c7f233f3` | 轻量 tag；该提交的 `pyproject.toml` 包版本写为 `0.2.8`，与 tag 文本不同 |
| DeepPresenter 论文快照 | `refs/tags/v1.1.38` | peeled commit `2419d30b134a71486523e95ded60b32489fd3c61` | annotated tag object `2e68c095a86bdbb91635dc4d91dad4662aba163c` |

研究 clone 位于仓库外：`F:\YoloongPPT-Research\P02`。当前 checkout 为 main 的固定 commit，`HEAD` detached；工作树干净。clone 使用浅层/按需 blob 下载并额外抓取两个 tag，不包含完整历史；需要历史考古时再按任务加深 fetch。

可复现固定 checkout 的命令：

```powershell
git clone --filter=blob:none --depth=1 --no-checkout https://github.com/icip-cas/PPTAgent.git F:\YoloongPPT-Research\P02
git -C F:\YoloongPPT-Research\P02 fetch --depth=1 origin refs/tags/v0.2.0:refs/tags/v0.2.0
git -C F:\YoloongPPT-Research\P02 fetch --depth=1 origin refs/tags/v1.1.38:refs/tags/v1.1.38
git -C F:\YoloongPPT-Research\P02 checkout --detach 833cda553b343be0e486a93b0b57cac962cdd566
git -C F:\YoloongPPT-Research\P02 rev-parse HEAD
```

末条命令应输出 `833cda553b343be0e486a93b0b57cac962cdd566`。tag 可分别用 `git rev-parse 'refs/tags/v0.2.0^{commit}'` 与 `git rev-parse 'refs/tags/v1.1.38^{commit}'` 核对。既有 [VersionManifest](../../contracts/version-manifest.catalog.json) 记录的 P02 refs 与本次 remote/clone 核对结果一致。

## 锁文件、依赖清单与许可证

| 快照 | 文件 | 观察结果 |
|---|---|---|
| main / Skill | `skills/pptagent/package-lock.json` | npm `lockfileVersion: 2`；SHA-256 `d4dfa60730c53b9d6ad9106ad70bc88072c534730c7144afe81e5f845250ca42` |
| main / Skill | `skills/pptagent/requirements.txt` | 不是 Python 完整锁文件；含 `pptagent==1.1.37`、`playwright==1.62.0`，以及 `PyYAML>=6`、`Pillow>=10`、`PyMuPDF>=1.24.3`、`fastmcp>=2.10.0,<2.14.0`；SHA-256 `5a85fdebda19e08cafc695281fe68367af018c620c7e77396a23459ee2cc4437` |
| v0.2.0 | `uv.lock`、`pyproject.toml`、`pptagent_ui/package-lock.json` | Python lock `version=1/revision=2`，要求 `>=3.11`；npm lock `version=3`；uv.lock SHA-256 `c9fb4b5c844a1e1d028890cd00eb2cfdc1b87c7739861cbbe9fed38d645c4bfc` |
| v1.1.38 | `uv.lock`、`pyproject.toml`、`deeppresenter/html2pptx/package-lock.json` | Python lock `version=1/revision=3`，要求 `>=3.11`；npm lock `version=3`；uv.lock SHA-256 `637f598907293b89dbf501b678df90252a76499513fa157870a0cbab2e3e63b5` |

三个快照根目录 `LICENSE` 均为 MIT，SHA-256 相同：`e1faa9265adfb5feb24c4be691b5c39b559dec4f0414d9ec3a1157cf94faaf8b`。main Skill 还带有独立 MIT `skills/pptagent/LICENSE`。这只确认上游主许可证；第三方依赖的逐项许可证与 YoloongPPT 是否复用尚未评估。

## 官方运行环境与最小流程

- 固定 main README 的 Skill 安装说明要求 Claude Code、Codex CLI 或 OpenCode，Linux（含 WSL）或 macOS、`uv`、npm 与可从 PATH 调用的 LibreOffice；macOS 转换器还要求 Chrome。README 示例使用 `uv venv --python 3.12`，这是该上游快照的安装示例，不是 YoloongPPT 的技术选型。
- main Skill 运行路径还要安装 `skills/pptagent/requirements.txt`、Playwright Chromium，并通过官方 installer 注册所选 agent；生成与视觉评审流程可能需要配置外部模型/API 凭据。没有读取或记录任何凭据。
- v0.2.0 与 v1.1.38 的 `pyproject.toml` 声明 Python `>=3.11`，`uv.lock` 锁依赖解算，不固定 YoloongPPT 产品运行时。v1.1.38 README 明确不支持原生 Windows，建议 WSL，并提供 `uvx pptagent generate`、Docker host/sandbox 与源码开发路径。
- main Skill 的 `requirements.txt` 固定 `pptagent==1.1.37`，而独立 DeepPresenter tag 是 v1.1.38；这是上游 Skill 与论文 tag 的版本差异，后续最小流程必须按被研究 ref 分别记录，不能静默互换。

本项目 Docker CLI 当前无法连接 `desktop-linux` 服务端：`docker version` 返回 `//./pipe/dockerDesktopLinuxEngine` 不存在。项目 `compose.yaml` 的 Debian workspace 目前只声明 bash、ca-certificates、git，并未包含 P02 环境。没有启动容器、安装 P02 依赖、执行官方最小流程或生成 PPTX；没有使用 Windows 主机安装项目依赖。

因此源码 refs、lock/依赖文件和主许可证已核对，但 `ProjectBaseline` 验收尚未完成；`TASK-RES-P02-01` 保持进行中。Docker 服务端恢复后，应在容器内按固定快照复现官方最小流程，记录实际镜像摘要、环境输出、日志和生成产物，再关闭本任务。

## 固定来源

- [PPTAgent 官方仓库 main 固定快照](https://github.com/icip-cas/PPTAgent/tree/833cda553b343be0e486a93b0b57cac962cdd566)
- [PPTAgent v0.2.0 固定快照](https://github.com/icip-cas/PPTAgent/tree/d53296bc0ddd73e81d51c523d20dd711c7f233f3)
- [DeepPresenter v1.1.38 固定快照](https://github.com/icip-cas/PPTAgent/tree/2419d30b134a71486523e95ded60b32489fd3c61)
- [官方 main README 安装说明](https://github.com/icip-cas/PPTAgent/blob/833cda553b343be0e486a93b0b57cac962cdd566/README.md)
