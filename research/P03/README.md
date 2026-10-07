# P03：Presenton 研究基线

## 任务与范围

- Requirement ID：`RES-P03-01`
- Task ID：`TASK-RES-P03-01`
- 研究目的：固定 Presenton 上游源码，记录依赖锁、运行条件、许可证与架构，并复现官方最小流程。
- 本文只记录上游证据；不据此选择 YoloongPPT 产品运行时，也不把 Presenton 超出 GOV-009 范围的功能带入项目需求。

## 固定源码快照

2026-10-07 查询官方 Git remote：`refs/heads/main` 为 `35bf44290f821323e003da854f78ffcb0e918167`，与 `contracts/version-manifest.catalog.json` 中 `P03-MAIN` 的 pinned commit 一致。研究 clone 位于仓库外 `F:\YoloongPPT-Research\P03`，当前 detached HEAD 即该 commit；使用 blob-filter 和 sparse checkout 只展开 README、文档、脚本与 Web/API 服务目录，避免复制大量模板素材。工作树干净。

复现固定 checkout：

```powershell
git clone --filter=blob:none --depth=1 --no-checkout https://github.com/presenton/presenton.git F:\YoloongPPT-Research\P03
git -C F:\YoloongPPT-Research\P03 sparse-checkout init --cone
git -C F:\YoloongPPT-Research\P03 sparse-checkout set docs servers/fastapi servers/nextjs scripts
git -C F:\YoloongPPT-Research\P03 checkout --detach 35bf44290f821323e003da854f78ffcb0e918167
git -C F:\YoloongPPT-Research\P03 rev-parse HEAD
```

最后一条命令应输出 `35bf44290f821323e003da854f78ffcb0e918167`。Electron 子目录的锁文件虽不在 sparse working tree 中，但已从该 Git commit 对象读取并计算 SHA-256。

## 依赖锁、上游运行条件与许可证

| 文件 / 范围 | 固定信息 | SHA-256 |
|---|---|---|
| 根 `package-lock.json` | npm `lockfileVersion: 3`；包 `presenton@0.9.11-beta` | `e13e4b2b90e9d556d8d72e39c527dd5ee3cc8cc0bf70b1610abad4ef648f1db8` |
| `servers/fastapi/uv.lock` | uv lock `version = 1`、`revision = 3`；`requires-python = "==3.11.*"` | `0f9ecf38a9fca34b62f839bc3be7eb049415525f2765b886bd074e80b08c2bd3` |
| `servers/fastapi/pyproject.toml` | `presenton-backend@0.1.0`；`requires-python = ">=3.11,<3.12"` | `7e69db82d4525bfeb6d3ca3b2517b71b5ea1e6e66cf2c4579afeff807164522e` |
| `servers/nextjs/package-lock.json` | npm `lockfileVersion: 3`；包 `presenton@0.1.0` | `f845d84c1e9de13d4d53bce6d097b7f1ff6be393228c115a7584c177264a9362` |
| `electron/package-lock.json` | npm `lockfileVersion: 3`；包 `presenton@0.9.11-beta` | `8ce48108de9178bf4a9190e9664ec2ca8d0576fe9bc543902775a25f7cbc4c26` |

上游 README 的 Electron 本地开发说明列出 Node.js LTS、npm、Python 3.11 和 uv；这是该固定源码快照的上游开发条件，不是 YoloongPPT 选型。`uv.lock` 将 Python 限定为 3.11 系列，没有固定补丁版本，因此不能据此推定为 3.11.2。

根 `LICENSE` 为 Apache-2.0，SHA-256 `23d6fd64bfcbd46b331098ed89454717fd1719faccbf632f8234b962aa43ed1a`；根目录含第三方归属信息 `NOTICE`，SHA-256 `b896b6803a6dd38c9307e3fc6768c0da387e9ce8596d1c2e7c73c26b769ce2d7`。这里只确认上游根许可证和 NOTICE 存在，尚未逐项审计全部依赖许可证或评估 YoloongPPT 复用边界。

## 架构观察与范围边界

- 固定 README 描述 Docker 自托管应用和 Electron 桌面应用；Electron 开发模式使用 Next.js Web UI 与 FastAPI 后端。官方 Docker 快速启动使用 `ghcr.io/presenton/presenton:latest`，该标签不等于本任务冻结的源码 commit；后续复现应使用冻结源码对应的 Compose/build 路径并记录实际镜像摘要。
- `docs/presentation-generation-modes.md` 记录 Standard 固定 layouts、outline review 和模板工作流；Smart 使用 adaptive layouts 并将生成内容流式送入编辑器，不走模板工作流。`PRESENTATION_GENERATION_MODE` 控制 Web UI 选项和 MCP 工具暴露；文档明确它不作为 REST API 授权控制。
- 研究对象表还要求继续核对 custom template 解析、API/MCP job、`slides_markdown` 映射和编辑器对象模型；当前只完成 ProjectBaseline 的静态基线，不宣称这些能力已经迁移或通过验证。
- 固定 README 同时描述多用户工作区及账号管理。该上游范围与 GOV-009 明确排除的账号/多租户方向重叠；这里只作为边界观察，不纳入 YoloongPPT 当前产品范围。

## 复现状态与阻塞

项目要求的隔离 Docker 当前不可用：`docker version` 无法连接 `desktop-linux` 的 `//./pipe/dockerDesktopLinuxEngine`。没有启动容器、安装上游依赖、运行官方最小流程或生成 PPTX；也没有在 Windows 主机安装依赖。静态 refs、locks、环境声明、上游主许可证和核心工作流已记录，但 `ProjectBaseline` 验收仍未完成，`TASK-RES-P03-01` 保持进行中。Docker Engine 恢复后，应从冻结 commit 在项目隔离容器中执行官方源码 Compose 流程，记录真实镜像摘要、环境、日志和输出，再更新任务状态。

## 固定来源

- [Presenton 官方仓库固定快照](https://github.com/presenton/presenton/tree/35bf44290f821323e003da854f78ffcb0e918167)
- [固定快照 README](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/README.md)
- [Standard / Smart 模式说明](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/docs/presentation-generation-modes.md)
