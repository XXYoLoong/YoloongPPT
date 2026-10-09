# 产品架构选择与运行边界

本记录服务核心SYS与AC-001/GOV-008。完整308/453范围及所有PP/PPT/DEC/AC保留；真实模型/PPTX/render/部分QA和单文本对象修订已运行，完整DEC和系统验收尚未通过。

## 选择依据

- 核心编排使用 Python 3.13.16，Linux amd64 Docker，JSON Schema Draft 2020-12（jsonschema 4.26.0），HTTP 使用 FastAPI 0.143.0 / Uvicorn 0.54.0。现有契约是 JSON Schema，可直接运行；来源解析、证据处理与 python-pptx 可在同一核心执行，减少跨语言对象搬运。版本来自官方发布/包元数据和实际镜像 manifest，不是主机 Python 3.11.2 的环境观测。
- [Python 官方 3.13.16 发布说明](https://www.python.org/downloads/release/python-31316/)与[官方镜像来源](https://github.com/docker-library/python/blob/master/versions.json)已核对；固定 `python:3.13.16-slim-bookworm` 的 linux/amd64 manifest `sha256:f040863673aea2570c3ff6a5c3fb4c673a016cbc5375005ad145915922b6b78a`。选择已发布维护版本和 Debian/glibc wheel 环境；3.14 不是需求禁止项，但本轮不同时引入新 minor 与多后端。未来升级需相关兼容与产物验证。
- 包版本从各项目发布的 PyPI JSON 元数据核对；直接及传递依赖最终以 `requirements.lock` 和 `runtime/dependencies.json` 为准。只有当前组件需要的依赖进入镜像；后端/模型/渲染依赖在对应实现工作包加入，不预装整套候选。
- .NET/Open XML SDK 适合结构验证、复杂 parts 与往返保存，将作为独立 PP-04 Adapter；用它替代整个 Python 编排没有当前 E2E 收益。Node/PptxGenJS 的新建与 SVG 支持有研究实物，但 write-only 路线不能承担普通已有 PPTX 保真修改。Node 保留为 PP-06/07 或其他必要 Adapter，不成为本轮核心运行时。

## 执行、模型与质量路线

- 首条新建路径选择 PP-05 python-pptx 1.0.2（MIT）作为原生 text/shape/table/chart/notes 写入适配器。P05 研究已有这些对象实物，但其整应用 AGPL/声明冲突代码不复制；底层库按[官方发布](https://pypi.org/project/python-pptx/1.0.2/)独立接入。图像、模板、现有对象和高级对象分别验证，不把上游研究子集升格为产品 Native。
- 首条渲染使用 Docker 内 LibreOffice/PDF→PNG，保存版本/hash与渲染差异；PowerPoint 打开兼容性及 live 能力使用明确 Windows/Office 边界的 Adapter。Office 不是 Linux 镜像内依赖；可运行隔离 bridge 的部署细节在对应 PP-01/08 实验验证。不得以 Linux 运行替代 AC-028 的 PowerPoint 实测，也不在 Windows 主机安装本项目 Python/Node 依赖。
- 模型通过provider接口调用；首条为用户授权DeepSeek，系统环境变量安全同步到F盘忽略目录，读取值不进入TaskSpec/trace/Git/镜像/终端。每次实际调用核对供应商/models；本轮列表为deepseek-flash和deepseek-v4-pro，明确选用flash，未将旧deepseek-chat静默替换。按[官方视觉文档](https://api-docs.deepseek.com/guides/vision/)和实际PNG请求，flash已执行视觉/事实审查；不由“文本模型”标签推定其视觉能力。模型结果、用量、参数和hash保留，审查仍可能误判，不替代所有QA及兼容性验收。
- 事实/来源 QA 直接消费 evidence、constraint 和 rewrite trace，视觉与几何 QA 消费实际渲染，可编辑性 QA 检查 OOXML/ObjectMap；每类独立报告。局部修订保留实体 ID、原稿、未选对象与未知 parts，按 RevisionPlan 重跑受影响节点后再次验收。
- CLI/HTTP共用核心服务：validate/inspect/evidence/capabilities/schemas/generate/resume/revise/recheck。草稿路径确实消费来源、模型、spec、DAG、对象写入、渲染和QA；单文本对象修订逐字节保留未改OOXML parts。MCP、完整jobs/取消、完整RevisionPlan与节点恢复仍按原任务实现。返回draft_generated/draft_revised，不能当成系统验收成功。

## 数据、能力与失败

- TaskSpec 使用数据对象行的 `task_id, route, sources, constraints, style, template_ref, output, providers, runtime_preferences`；mode 在 route 中，复用现有 TaskRoute/ConstraintSet/实体 ID Schema，不另建冲突的 mode/约束版本。
- SchemaRegistry 从项目 contracts 载入、按文件 SHA-256 标识版本，只允许已注册本地引用，禁止自动网络获取 schema。组件校验错误返回字段 JSON Pointer、关键词和结构化错误，不回显输入/密钥。
- CapabilityRegistry 复用既有 30×9 PPT 状态草案，单列本轮核心原子实现、平台、依赖、优先级和 health。上游实验、SDK 安装和组件校验不使任何产品 PPT 能力变成 Native；健康可用与对象支持状态分开。
- 本轮 HTTP 仅发布到主机 `127.0.0.1:8000`，本项目 Compose 管理 `app` 与 `workspace`。源码挂载便于编辑，运行依赖只在镜像中。运行临时/产物目录均绑定 F 盘；Docker 磁盘由启动脚本先验证 F 盘 VHDX，容器 rootfs 只读。
- 所有 fallback、容量裁剪、平台缺口和错误显式返回并留 trace；本轮没有模型/内容转换，不产生内容裁剪或后端替换。应用日志不打印请求 body、敏感值或 traceback 内容。

## 待证明范围

来源运行时使用markdown-it-py 4.2.0 / mdit-py-plugins 0.6.1及mdurl 0.1.2。新增python-pptx 1.0.2/lxml 6.1.3/Pillow 12.3.0/XlsxWriter 3.2.9，此前22项版本未变，现26项以lock为准。SQLite不可变快照/证据维持原有hash/version/ID与unknown confidence。消费Schema共52份，新增模型提案、Deck/Execution/ObjectMap及单对象修订接口；未推定语义事实真值或多源冲突解决。

Docker固定安装libreoffice-impress 4:7.4.7-1+deb12u14、poppler-utils 22.12.0-2+deb12u3、fonts-noto-cjk 1:20220127+repack1-1；完整系统包版本和核心版权文件随实物证据保留。/tmp实际挂载F盘runtime/data/tmp以满足LibreOffice IPC硬编码，XDG配置/缓存亦在/runtime；镜像rootfs继续只读。真实生成及修订证据见validation/generation-artifacts，组件核验31项、核心26项、来源36项通过。

相关SYS保持进行中：当前子集真实经过草稿链路，完整对象/模式、决策、QA与恢复范围未满足。PP-01–09、PPT-001–030、DEC-001–040、S00–S44和AC-001–030继续按原矩阵推进。下一动作是DEC关键节点和正式能力登记接入本实物链路，补齐AC-001完整轨迹；implementation_id当前仍为方法别名，不虚称已符合全部实体登记。
