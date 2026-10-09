# P02：PPTAgent / DeepPresenter 研究基线

## 任务与范围

- Requirement ID：`RES-P02-01`
- Task ID：`TASK-RES-P02-01`、`VERIFY-RES-P02-01`
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
- main Skill 运行路径还要安装 `skills/pptagent/requirements.txt`、Playwright Chromium，并通过官方 installer 注册所选 agent；生成与视觉评审流程可能需要配置外部模型/API 凭据。初次安装未配置凭据；2026-10-09 经用户授权读取系统变量名称 DEEPSEEK_API_KEY 并仅传入执行进程，未输出或落盘其值。
- v0.2.0 与 v1.1.38 的 `pyproject.toml` 声明 Python `>=3.11`，`uv.lock` 锁依赖解算，不固定 YoloongPPT 产品运行时。v1.1.38 README 明确不支持原生 Windows，建议 WSL，并提供 `uvx pptagent generate`、Docker host/sandbox 与源码开发路径。
- main Skill 的 `requirements.txt` 固定 `pptagent==1.1.37`，而独立 DeepPresenter tag 是 v1.1.38；这是上游 Skill 与论文 tag 的版本差异，后续最小流程必须按被研究 ref 分别记录，不能静默互换。

### 隔离容器中的环境复现记录（2026-10-07 至 2026-10-08）

- 实验执行时本机 `desktop-linux` Docker context 可用；观察到 Docker Desktop WSL 磁盘文件 `F:\DockerDesktopWSL\disk\docker_data.vhdx`。研究容器 `yoloongppt-p02-research` 使用项目 workspace 镜像，P02 固定源码以只读方式挂载到 `/research`，实验依赖、缓存和输出写到 F 盘挂载 `/artifacts`。Windows 主机未安装 P02 依赖。
- 按固定 main commit `833cda553b343be0e486a93b0b57cac962cdd566` 安装 Skill requirements、npm lock、Playwright Chromium，并运行官方 installer 注册 Codex Skill。注册结果仅存在容器内 `/artifacts/home/.agents/skills/pptagent`，不代表当前 Windows Codex 主机已启用该 Skill。
- 本次容器的环境观察值：Python 3.11.2、uv 0.12.23、Node.js 18.20.4、npm 9.2.0、LibreOffice 7.4.7.2、Playwright 1.62.0；已安装 Python 包 229 个。`uv pip check` 通过，Chromium headless 页面 smoke 通过。**Python 3.11.2 是本次 Debian 镜像内的观测版本，不是 YoloongPPT 的产品运行时选型或项目要求。**产品语言/运行时仍未确定。
- 按上游 Quick Start 执行 `scripts/pptagent.py doctor`，11 项本地检查全部通过（Python 模块/版本、LibreOffice、Node、Playwright 版本、html2pptx 脚本与运行时）。此 doctor 不会生成 PPTX，也不验证模型服务。
- 上游 `npm ci` 输出 6 个 high severity findings；未自动修改上游 lock 或升级依赖，需后续按上游依赖和许可/安全任务核查。
- 另一次 `pptagent --help` 包入口探测约 60 秒未返回，已中断；这不是上游 Quick Start 的 doctor 命令，也没有据此判定 Skill 功能失败。未观察到 API 请求。
- 本次未向容器传入或配置提供商凭据，未调用模型/API，也未生成 PPTX 或完成视觉评审。因此这次只验证安装、依赖一致性、浏览器与容器内 Skill 注册，不能视为官方端到端生成流程通过。
- 2026-10-08 复核时发现 Docker service/WSL 发行版一度停止。核实 `wslEngineEnabled=True`、`CustomWslDistroDir=F:\DockerDesktopWSL` 和 F 盘 VHDX 后，恢复 Docker Desktop；Engine 版本 `27.4.0`、`DockerRootDir=/var/lib/docker`。随后用 `scripts/project.ps1 -Action start` 启动 `yoloongppt-workspace-1`，并恢复 `yoloongppt-p02-research`；两个容器与研究数据的宿主挂载均位于 F 盘。设置中 `DataFolder=C:\ProgramData\DockerDesktop\vm-data` 仍保留；当前启用的 WSL 后端使用 F 盘 WSL 磁盘，这一点由设置与实际 VHDX/挂载路径共同确认。未在 C 盘写入项目文件、研究数据或 Docker 容器数据。
- 可追溯证据：`research/P02/validation/environment-main-skill.txt`、`research/P02/validation/packages-freeze-main-skill.txt`、`research/P02/validation/verify-res-p02-01.json`、`research/P02/scripts/`。原始实验目录位于仓库外 `F:\YoloongPPT-Research\P02-official-smoke`，Docker 可写层和 Docker 数据盘也在 F 盘。

上述安装记录是当时的历史范围。2026-10-09 已完成下述真实模型创作与官方主机审查流程，`TASK-RES-P02-01` 与 `VERIFY-RES-P02-01` 按候选研究验收收尾；P02-02/03/04/05 仍待交付源码映射。DeepSeek /models 查询只作为发现证据，实际推理结果单独保留。

## 六页官方生成与审查（2026-10-09 收尾）

固定 main Skill 的角色是主机创作 HTML，CLI 负责渲染、原生转换、状态/审查门控。此次用用户授权的 `DEEPSEEK_API_KEY` 调用 `deepseek-flash` 生成六页中文 HTML（非 mock），保留公开内容、提示、请求 ID、usage 与 hash；不保存私有 reasoning 或密钥值。模型创作 8.32 秒、3,056 completion tokens；内容来自已有矩阵/目标与 P05 研究事实，不含联网推测。API 请求格式按官方 [Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/) 和 [JSON Output](https://api-docs.deepseek.com/guides/json_mode/)；图像输入按 [Vision](https://api-docs.deepseek.com/guides/vision/)。

| 环节 | 实际结果与范围 |
|---|---|
| init + 模型创作 | 6页/16:9/中文；author-run.json、author-response.json、author-prompts.json |
| 外部 text-mode review-slides | 两次退出2；真实图像请求有响应，但 issue.slide 返回字符串 `"01"`，违反原正整数校验；响应记录保留。没有强转、删除issue或放宽validator |
| 官方默认 multimodal 路线 | 显式切换 config-host-review.yaml；主机逐页查看六张HTML JPG，再经官方 record-slide-review记录。外部JSON接口仍未通过 |
| 首次 build | 退出2：footer距底0.40英寸，小于写入器0.5英寸；HTML可见不等于转换有效 |
| 源码修订与重新审查 | 六页footer top660→620px；旧渲染/状态保存source-v1，所有六页重新渲染和逐页查看，再记录当前review；固定上游未修改 |
| 第二次 build + review-deck | 6页PPTX写出；LibreOffice→PDF→PyMuPDF6张JPG；查看两张contact覆盖六页，并复核第2/6页原图，无可见裁切/重叠 |
| finalize | 严格模式complete=true，六个check均真；仅是上游Skill候选研究，不代表产品验收 |
| 结构/失效边界 | 每页5个原生文字shape；每页5项HTML正文全部在OOXML a:t中；在真实完整任务副本修改一页HTML后finalize退出1，build_current与slide_reviews_current为false，原正常任务不变 |
| 输入/失败门控 | zero slides/init overwrite/missing render→退出2；无PPTX的finalize→退出1。真实错误及日志见workflow-probes.json |

产物：[answer.pptx](outputs/official-six/answer.pptx)，SHA-256 `eb90a46c983c15c09d02de5bccdd171b33ed39c22d12e7a9f912580ecd7b7b1b`；[final-report.json](outputs/official-six/final-report.json)、[完整核验](validation/verify-official-six.json)。版式单一/空白多的minor限制保留；没验证图片、原生chart/table/全部对象、PowerPoint打开、历史tag运行或产品AC。HTML源修订是全量重建，不是保真原位PPTX编辑。

实际转换依赖是requirements固定的pptagent1.1.37，未替换为论文tag1.1.38。installed converter及webview源码hash见converter-source.json。系统Node观测18.20.4，但官方node_environment将Playwright driver置于PATH前端，**实际build使用Node24.18.1**；这是候选环境记录，仍不构成产品技术选型。

复现使用既有F盘容器与固定Skill。新建独立workspace后按官方init，复制已保存的六份真实模型HTML（或用相同公开prompt重新调用授权模型），执行review-slides；必须实际看每页再record-slide-review，build后review-deck并看contact，再record-deck-review与finalize。脚本official-six-step.py保存本次命令/日志；verify-six.py核对当前实物并在独立副本测试过期源门控，脚本中的副本目录应首次不存在。不能重用本次pass标记去认可不同输入。

本任务执行脚本使用HOME=/artifacts/home、TMPDIR=/artifacts/tmp、PLAYWRIGHT_BROWSERS_PATH=/artifacts/cache/ms-playwright，所有挂载和Docker可写数据都在F盘；产品代码/compose未改变。下一工作包复用这些实物与当前已读源码，建立P02调用链、决策、模板和能力边界，明确main Skill与1.1.37依赖的职责；不再重复安装或整个生成流程。

## 固定来源

- [PPTAgent 官方仓库 main 固定快照](https://github.com/icip-cas/PPTAgent/tree/833cda553b343be0e486a93b0b57cac962cdd566)
- [PPTAgent v0.2.0 固定快照](https://github.com/icip-cas/PPTAgent/tree/d53296bc0ddd73e81d51c523d20dd711c7f233f3)
- [DeepPresenter v1.1.38 固定快照](https://github.com/icip-cas/PPTAgent/tree/2419d30b134a71486523e95ded60b32489fd3c61)
- [官方 main README 安装说明](https://github.com/icip-cas/PPTAgent/blob/833cda553b343be0e486a93b0b57cac962cdd566/README.md)
