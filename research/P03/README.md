# P03：Presenton 研究基线

## 任务与范围

- Requirement ID：`RES-P03-01`
- Task ID：`TASK-RES-P03-01`
- 研究目的：固定 Presenton 上游源码，记录依赖锁、运行条件、许可证与架构，并复现官方最小流程。
- 本文只记录上游证据；不据此选择 YoloongPPT 产品运行时，也不把 Presenton 超出 GOV-009 范围的功能带入项目需求。

## 固定源码快照

2026-10-07 查询官方 Git remote：`refs/heads/main` 为 `35bf44290f821323e003da854f78ffcb0e918167`，与 `contracts/version-manifest.catalog.json` 中 `P03-MAIN` 的 pinned commit 一致。研究 clone 位于仓库外 `F:\YoloongPPT-Research\P03`，当前 detached HEAD 即该 commit；使用 blob-filter 和 sparse checkout 展开源码研究目录及官方 Docker build 所需模板、文档提取资源，工作树干净。

复现固定 checkout：

```powershell
git clone --filter=blob:none --depth=1 --no-checkout https://github.com/presenton/presenton.git F:\YoloongPPT-Research\P03
git -C F:\YoloongPPT-Research\P03 sparse-checkout init --cone
git -C F:\YoloongPPT-Research\P03 sparse-checkout set docs servers/fastapi servers/nextjs scripts templates electron/resources/document-extraction
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
- 研究对象表还要求继续核对 custom template 解析、API/MCP job、`slides_markdown` 映射和编辑器对象模型；这些属于后续调用链与能力研究任务，不据当前基线宣称已通过验证。
- 固定 README 同时描述多用户工作区及账号管理。该上游范围与 GOV-009 明确排除的账号/多租户方向重叠；这里只作为边界观察，不纳入 YoloongPPT 当前产品范围。

## 复现状态与边界

2026-10-08 从冻结源码通过上游 `docker-compose.yml` 构建并启动 `production` 服务；本地 override 将唯一 Web 端口限制为 `127.0.0.1:5001`，官方 OAuth 回调端口未发布。Compose 项目名为 `yoloongppt-p03`，容器可写层位于 Docker Desktop WSL 数据盘 `F:\DockerDesktopWSL\disk\docker_data.vhdx`，应用数据绑定到 `F:\YoloongPPT-Research\P03\app_data`，模板以只读方式绑定。镜像 ID 为 `sha256:822dc9c5c34bbb3cc126f38cec2dc9c646330eb1ee53c2fd37b6e0fee1bc87dd`。

启动日志显示 Next.js、FastAPI、数据库迁移及默认模板导入完成；首页返回 HTTP 200，`/api/v1/auth/status` 返回 HTTP 200。接口报告 `configured=false`、`authenticated=false`。官方 Quick Start 的 Docker 最小流程是启动并打开本地网页；固定源码的容器已启动且首页可访问，因此 `TASK-RES-P03-01` 的基线验收完成。正常启动样例已记录，`VERIFY-RES-P03-01` 保持进行中，仍需准备边界/失败样例。没有配置或转发模型凭据，没有发起模型/API 请求，也没有生成 PPTX 或做视觉评审；这些生成能力不包含在本任务已验证结果内。对应可复现记录见 `research/P03/validation/smoke.json`。

## 固定来源

- [Presenton 官方仓库固定快照](https://github.com/presenton/presenton/tree/35bf44290f821323e003da854f78ffcb0e918167)
- [固定快照 README](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/README.md)
- [Standard / Smart 模式说明](https://github.com/presenton/presenton/blob/35bf44290f821323e003da854f78ffcb0e918167/docs/presentation-generation-modes.md)

## 调用链研究（RES-P03-02）

已从固定源码建立 Standard、Smart、直接 REST/MCP、编辑/修订和 PPTX/PDF 导出调用链；节点和符号位置见 call-graph.md 与 source-index.json。@presenton/export-core 固定 v1.0.34，但其实现以外部发布制品形式提供，按黑盒标注。源码静态追踪完成；本地登录状态尚未初始化，生成请求被 HTTP 428 门禁挡住，因此 VERIFY-RES-P03-02 仍进行中。运行观测见 validation/verify-res-p03-02.json。

## 结构与视觉决策映射（RES-P03-03）

已从固定源码提取 17 个节点，并逐项映射 DEC-001–DEC-040。6 项有明确机制，29 项部分映射，5 项未发现独立等价机制。节点输入、候选、机制、输出、fallback 和源码索引见 decision-map.json；摘要见 decision-map.md。静态映射已完成；动态决策样例受本地登录初始化 HTTP 428 阻塞，VERIFY-RES-P03-03 保持进行中。

## 模板、版式与中间表示（RES-P03-04）

固定 Presenton commit 的 16 个默认模板已结构化为 `template-map.json`（机器可读清单）和 `template-map.md`（摘要）。清单覆盖 383 个 layouts、1,600 个组件槽位、444 个 merged-component 变体组、10,283 个嵌套元素和 1,002 个静态文件；对模板 JSON 和静态文件记录 SHA-256。二进制图片、字体和缩略图不复制进本项目。

组件 ID/描述/位置表示槽位；元素树记录类型、命名内容字段、几何、样式属性及显式容量约束。主题颜色/字体作为 token 保留；`Position`/`Size` 是源数值坐标，模板 JSON 没有声明坐标单位。上游认证代码出现 1280×720 画布常量，但它不是模板 JSON 的单位声明。字符容量不会由几何推算；独立 `TextCapacityPlan` 属于认证生成路径，不是这 16 个静态模板预先测得的上限。

默认模板没有显式页面类型或逐版式适用条件；清单中的页面类型只按 layout ID/description 做关键词候选标记，不映射为 YoloongPPT 产品页面类型。16 份模板 JSON 未声明 parent/extends；merged-component variants 记录为替代组件，不视作继承。运行时会从 outline 与 layout 描述/Schema 建立版式索引映射，不能据此声称视觉生成或适用性已通过验证。

`TASK-RES-P03-04` 静态提取完成。`VERIFY-RES-P03-04` 仍进行中：静态结构清单和来源定位已核对；正常生成、边界/失败生成、PPTX 导出与视觉检查尚无运行证据。Presenton 本地认证仍未配置，先前 HTTP 428 门禁记录见 P03-02/03 验证报告；本任务没有发送模型请求或生成文件。详见 `validation/verify-res-p03-04.json`。
