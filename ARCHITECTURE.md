# 产品架构选择与运行边界

本记录服务 SYS-001、SYS-006、SYS-007、SYS-019、SYS-020 与后续 AC-001/GOV-008。完整 308/453 范围及所有 PP/PPT/DEC/AC 仍保留；本轮仅接入任务校验和能力查询组件，E2E 未执行。

## 选择依据

- 核心编排使用 Python 3.13.16，Linux amd64 Docker，JSON Schema Draft 2020-12（jsonschema 4.26.0），HTTP 使用 FastAPI 0.143.0 / Uvicorn 0.54.0。现有契约是 JSON Schema，可直接运行；来源解析、证据处理与 python-pptx 可在同一核心执行，减少跨语言对象搬运。版本来自官方发布/包元数据和实际镜像 manifest，不是主机 Python 3.11.2 的环境观测。
- [Python 官方 3.13.16 发布说明](https://www.python.org/downloads/release/python-31316/)与[官方镜像来源](https://github.com/docker-library/python/blob/master/versions.json)已核对；固定 `python:3.13.16-slim-bookworm` 的 linux/amd64 manifest `sha256:f040863673aea2570c3ff6a5c3fb4c673a016cbc5375005ad145915922b6b78a`。选择已发布维护版本和 Debian/glibc wheel 环境；3.14 不是需求禁止项，但本轮不同时引入新 minor 与多后端。未来升级需相关兼容与产物验证。
- 包版本从各项目发布的 PyPI JSON 元数据核对；直接及传递依赖最终以 `requirements.lock` 和 `runtime/dependencies.json` 为准。只有当前组件需要的依赖进入镜像；后端/模型/渲染依赖在对应实现工作包加入，不预装整套候选。
- .NET/Open XML SDK 适合结构验证、复杂 parts 与往返保存，将作为独立 PP-04 Adapter；用它替代整个 Python 编排没有当前 E2E 收益。Node/PptxGenJS 的新建与 SVG 支持有研究实物，但 write-only 路线不能承担普通已有 PPTX 保真修改。Node 保留为 PP-06/07 或其他必要 Adapter，不成为本轮核心运行时。

## 执行、模型与质量路线

- 首条新建路径选择 PP-05 python-pptx 1.0.2（MIT）作为原生 text/shape/table/chart/notes 写入适配器。P05 研究已有这些对象实物，但其整应用 AGPL/声明冲突代码不复制；底层库按[官方发布](https://pypi.org/project/python-pptx/1.0.2/)独立接入。图像、模板、现有对象和高级对象分别验证，不把上游研究子集升格为产品 Native。
- 首条渲染使用 Docker 内 LibreOffice/PDF→PNG，保存版本/hash与渲染差异；PowerPoint 打开兼容性及 live 能力使用明确 Windows/Office 边界的 Adapter。Office 不是 Linux 镜像内依赖；可运行隔离 bridge 的部署细节在对应 PP-01/08 实验验证。不得以 Linux 运行替代 AC-028 的 PowerPoint 实测，也不在 Windows 主机安装本项目 Python/Node 依赖。
- 模型通过 provider 接口统一调用。文本首条供应商为用户授权的 DeepSeek，读取环境变量名，记录模型/参数；密钥不进入 TaskSpec、trace、Git、镜像或终端。实际模型能力和名称在调用前从配置/供应商核验；DeepSeek 文本模型不被当作视觉模型。视觉模型未配置时明确 Untested/不可运行，继续结构/事实检查，不伪造视觉通过。
- 事实/来源 QA 直接消费 evidence、constraint 和 rewrite trace，视觉与几何 QA 消费实际渲染，可编辑性 QA 检查 OOXML/ObjectMap；每类独立报告。局部修订保留实体 ID、原稿、未选对象与未知 parts，按 RevisionPlan 重跑受影响节点后再次验收。
- CLI、HTTP API、MCP 共用核心服务。当前 CLI `validate/capabilities` 与 HTTP 同义入口实际消费 TaskSpec/SchemaRegistry/CapabilityRegistry；生成、修订、渲染、持久 job、MCP、doctor 等随后按原任务实现。本轮没有返回假任务成功或空 PPTX。

## 数据、能力与失败

- TaskSpec 使用数据对象行的 `task_id, route, sources, constraints, style, template_ref, output, providers, runtime_preferences`；mode 在 route 中，复用现有 TaskRoute/ConstraintSet/实体 ID Schema，不另建冲突的 mode/约束版本。
- SchemaRegistry 从项目 contracts 载入、按文件 SHA-256 标识版本，只允许已注册本地引用，禁止自动网络获取 schema。组件校验错误返回字段 JSON Pointer、关键词和结构化错误，不回显输入/密钥。
- CapabilityRegistry 复用既有 30×9 PPT 状态草案，单列本轮核心原子实现、平台、依赖、优先级和 health。上游实验、SDK 安装和组件校验不使任何产品 PPT 能力变成 Native；健康可用与对象支持状态分开。
- 本轮 HTTP 仅发布到主机 `127.0.0.1:8000`，本项目 Compose 管理 `app` 与 `workspace`。源码挂载便于编辑，运行依赖只在镜像中。运行临时/产物目录均绑定 F 盘；Docker 磁盘由启动脚本先验证 F 盘 VHDX，容器 rootfs 只读。
- 所有 fallback、容量裁剪、平台缺口和错误显式返回并留 trace；本轮没有模型/内容转换，不产生内容裁剪或后端替换。应用日志不打印请求 body、敏感值或 traceback 内容。

## 待证明范围

SYS 各组件的完整 E2E 通过条件未满足，保持进行中。PP-01–09 的 PoC、PPT-001–030 的产品实测、DEC-001–040 的可执行决策、S00–S44 的状态/断点及 AC-001–030 全部仍按原矩阵推进。下一动作是 SourceLoader/证据与真实新建 writer 接入；不能再以编写契约本身替代输入→可编辑 PPTX→QA→局部修订。
