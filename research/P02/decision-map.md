# P02 决策映射

固定 main `833cda553b343be0e486a93b0b57cac962cdd566` + 实际 requirements 依赖 `pptagent==1.1.37`。v0.2.0/v1.1.38 是独立历史版本，未静默混用。所有文件 hash/函数范围见 [SourceIndex](source-index.json)。这是上游研究交付，产品架构/运行时未选定，AC-001–030 未执行。

候选没有实现产品 DEC 全部标准。40 项 crosswalk 全保留；partial/not_evidenced 是研究发现，不能将 DEC 判定为已实现。

## D01 · 命令及视觉模式路由

- 输入：command + mode
- 候选：固定命令集、text/multimodal
- 机制：显式配置分支
- 输出：JSON结果/host instructions
- 约束：合法枚举；默认multimodal
- 回退：无自动模式切换；研究显式选host
- trace：validation/verify-official-six.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`cli:main` (main Skill `scripts/pptagent.py:236`); `config:load_config` (main Skill `scripts/pptagent_runtime/config.py:27`)

## D02 · 任务规范与画布

- 输入：slides:int,aspect_ratio:str,language:str
- 候选：用户指定、3种ASPECTS
- 机制：字段类型/枚举检查
- 输出：3字段task
- 约束：slides>=1
- 回退：非法输入抛错，不推断预算
- trace：validation/workflow-probes.json, validation/verify-official-six.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`core:load_task` (main Skill `scripts/pptagent_runtime/core.py:40`); `cli:init_workspace` (main Skill `scripts/pptagent.py:107`)

## D03 · 内容/结构/页面类型规划

- 输入：用户任务与材料；无CLI schema
- 候选：主机生成，候选不可观察
- 机制：Skill文字要求，host负责
- 输出：slide HTML
- 约束：静态HTML和任务页数
- 回退：无上游Planner fallback实现
- trace：validation/verify-official-six.json, validation/author-prompts.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`skill:resource` (main Skill `SKILL.md:1`); `contract:resource` (main Skill `references/task-contract.md:1`)

## D04 · 模板初始化

- 输入：task + starter tokens
- 候选：一个generic starter；既有HTML
- 机制：只补缺页，替换tokens
- 输出：HTML文件
- 约束：禁止覆盖既有slide
- 回退：不存在模板库检索/评分
- trace：validation/verify-official-six.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`core:scaffold` (main Skill `scripts/pptagent_runtime/core.py:110`); `starter:resource` (main Skill `assets/slide-template.html:1`)

## D05 · 布局与几何

- 输入：CSS computed DOM / body
- 候选：浏览器布局结果，不生成候选
- 机制：getBoundingClientRect；inch换算；锁layout
- 输出：IR positions + layout
- 约束：locked size误差<=0.1in
- 回退：strict报错；库auto布局分支非官方main自动选型
- trace：validation/maps-probes.json, validation/verify-official-six.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`converter:extractSlideData` (installed pptagent1.1.37 `html2pptx/html2pptx.js:708`); `converter:adaptLayout` (installed pptagent1.1.37 `html2pptx/html2pptx.js:87`)

## D06 · 容量与安全边距

- 输入：scroll/body/text bounds
- 候选：接受或拒绝；无自动拆页
- 机制：1px overflow；>12pt正文需0.5in bottom
- 输出：errors[]
- 约束：不是字数容量/fit搜索
- 回退：strict拒绝；研究修HTMLfooter后全链重跑
- trace：validation/footer-revision.json, validation/verify-official-six.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`converter:getBodyDimensions` (installed pptagent1.1.37 `html2pptx/html2pptx.js:50`); `converter:validateTextBoxPosition` (installed pptagent1.1.37 `html2pptx/html2pptx.js:120`)

## D07 · 文本格式与字体

- 输入：CSS/font/CDP/text geometry
- 候选：actual font/CSS/non-generic/MicrosoftYaHei
- 机制：CDP glyph主字体；rich runs；单行宽+2%补偿
- 输出：native text options
- 约束：px*.75pt、inch geometry
- 回退：CDP错误忽略；fallback字体无统一trace
- trace：validation/verify-official-six.json, validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`converter:font-family` (installed pptagent1.1.37 `html2pptx/html2pptx.js:726`); `converter:html2pptx` (installed pptagent1.1.37 `html2pptx/html2pptx.js:2835`); `converter:addElements` (installed pptagent1.1.37 `html2pptx/html2pptx.js:544`)

## D08 · 颜色/背景/效果

- 输入：computed color/gradient/shadow
- 候选：native solid/shadow或PNG
- 机制：按CSS类型选择写入分支
- 输出：fill/text/image
- 约束：复杂样式栅格化失去对象可编辑性
- 回退：gradient实测fallback；inlineSVG前置失败
- trace：validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`converter:addBackground` (installed pptagent1.1.37 `html2pptx/html2pptx.js:155`); `converter:rasterizeGradients` (installed pptagent1.1.37 `html2pptx/html2pptx.js:171`); `converter:addElements` (installed pptagent1.1.37 `html2pptx/html2pptx.js:544`)

## D09 · 图片适配

- 输入：IMG src/object-fit/filter/bounds
- 候选：native image或PNG flatten
- 机制：按复杂样式检查
- 输出：image IR
- 约束：必须有本地asset；main review禁未跟踪资源
- 回退：strict missing报错；soft依赖分支可跳图但main不启用
- trace：validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`converter:rasterizeGradients` (installed pptagent1.1.37 `html2pptx/html2pptx.js:171`); `converter:extractSlideData` (installed pptagent1.1.37 `html2pptx/html2pptx.js:708`)

## D10 · 表格对象映射

- 输入：TABLE/tr/td/th computed CSS
- 候选：native table，非必要性推断
- 机制：cells/runs/span/border/fill/colW/rowH
- 输出：addTable rows/options
- 约束：支持CSS子集；未全对象roundtrip
- 回退：空表/转换错误严格拒绝
- trace：validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`converter:table-extract` (installed pptagent1.1.37 `html2pptx/html2pptx.js:1700`); `converter:addElements` (installed pptagent1.1.37 `html2pptx/html2pptx.js:544`)

## D11 · 占位符/图表坐标

- 输入：class placeholder + bbox
- 候选：仅坐标slot
- 机制：返回id/x/y/w/h但CLI忽略
- 输出：placeholders[]
- 约束：不是native ph/chart
- 回退：没有官方chart消费路径
- trace：validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`converter:placeholder-extract` (installed pptagent1.1.37 `html2pptx/html2pptx.js:1546`); `converter-cli:module` (installed pptagent1.1.37 `html2pptx/html2pptx_cli.js:1`)

## D12 · 资源准入与字体就绪

- 输入：URL + snapshot resources
- 候选：跟踪的file或拒绝
- 机制：route检查；fonts.ready
- 输出：rendered images或ValueError
- 约束：仅review renderer route保证
- 回退：不尝试联网下载
- trace：validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`core:open_slide` (main Skill `scripts/pptagent_runtime/core.py:148`); `core:render_slides` (main Skill `scripts/pptagent_runtime/core.py:176`)

## D13 · 源与审查有效性

- 输入：task/slides/resources/image hashes
- 候选：current/missing/stale/not-passing
- 机制：hash和完整快照相等
- 输出：review gaps
- 约束：共享asset整体失效
- 回退：重新render/review；不能改state假通过
- trace：validation/verify-official-six.json, validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`core:input_snapshot` (main Skill `scripts/pptagent_runtime/core.py:93`); `core:render_current` (main Skill `scripts/pptagent_runtime/core.py:134`); `core:review_gaps` (main Skill `scripts/pptagent_runtime/core.py:243`)

## D14 · 视觉质量判定

- 输入：images/context/review payload
- 候选：pass/fail/unjudgeable；severity
- 机制：host看图或外部model；严格字段检查
- 输出：review {verdict,summary,issues,ok}
- 约束：major/blocker不能pass；slide正整数
- 回退：外部JSON失败抛错，无自动修JSON；主机路线需明确选择
- trace：validation/verify-official-six.json, validation/visual-slides-traced-01.json, validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`visual:module` (main Skill `scripts/pptagent_runtime/visual.py:1`); `cli:review_slides` (main Skill `scripts/pptagent.py:126`); `core:record_slide_review` (main Skill `scripts/pptagent_runtime/core.py:211`)

## D15 · 导出与后端路径

- 输入：fresh HTML/reviews/aspect
- 候选：固定Chromium→PptxGenJS，不比较PP01–09
- 机制：strict构建门控与writeFile
- 输出：PPTX与source/artifact hashes
- 约束：数量/比例须一致
- 回退：strict converter error，无自动换后端
- trace：validation/verify-official-six.json, validation/workflow-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`core:build` (main Skill `scripts/pptagent_runtime/core.py:283`); `converter-cli:module` (installed pptagent1.1.37 `html2pptx/html2pptx_cli.js:1`); `config:node_environment` (main Skill `scripts/pptagent_runtime/config.py:54`)

## D16 · 整稿QA与修订

- 输入：PPTX/contact + visual issues
- 候选：pass/fail/主机改源重建
- 机制：LO渲染、review、source invalidation
- 输出：deck review + new build
- 约束：无事实校验、自动局部编辑
- 回退：人工/主机修HTML；非原位PPTX修改
- trace：validation/verify-official-six.json, validation/footer-revision.json, validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`core:render_deck` (main Skill `scripts/pptagent_runtime/core.py:366`); `core:record_deck_review` (main Skill `scripts/pptagent_runtime/core.py:433`); `skill:resource` (main Skill `SKILL.md:1`)

## D17 · 交付终止

- 输入：6 bool checks + delivery mode
- 候选：strict完成或best-effort draft
- 机制：all checks /显式mode
- 输出：final-report
- 约束：当前研究仅strict；draft未授权
- 回退：reject incomplete，保留原因
- trace：validation/verify-official-six.json, validation/workflow-probes.json, validation/maps-probes.json；没有结构化候选评分/所有主机内部决策trace
- 源码：`core:finalize` (main Skill `scripts/pptagent_runtime/core.py:459`)

## DEC 全量对应

| ID | 决策 | 状态 | 节点 |
|---|---|---|---|
| DEC-001 | 任务模式路由 | partial | D01, D03 |
| DEC-002 | 输入约束归一化 | partial | D02 |
| DEC-003 | 来源加载策略 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-004 | 来源优先级/冲突 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-005 | 事实/假设边界 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-006 | 受众判定 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-007 | 用途与场景 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-008 | 语言/语气 | partial | D02, D03 |
| DEC-009 | 核心论点 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-010 | 内容关系图 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-011 | 故事线 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-012 | 章节/大纲 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-013 | 总页数预算 | partial | D02 |
| DEC-014 | 章节页数分配 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-015 | 分页 | partial | D03 |
| DEC-016 | 单页目标 | partial | D03 |
| DEC-017 | 页面类型 | partial | D03, D04 |
| DEC-018 | 内容容量 | partial | D06 |
| DEC-019 | 标题与层级文案 | partial | D03, D07 |
| DEC-020 | 压缩/扩写/拆分 | partial | D03, D06 |
| DEC-021 | 来源展示位置 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-022 | 主视觉表达 | partial | D03 |
| DEC-023 | 图片必要性 | partial | D03 |
| DEC-024 | 素材来源策略 | partial | D03, D12 |
| DEC-025 | 表格必要性 | partial | D03, D10 |
| DEC-026 | 图表必要性与类型 | partial | D03, D11 |
| DEC-027 | 流程/关系图类型 | partial | D03 |
| DEC-028 | 模板族选择 | partial | D04 |
| DEC-029 | 全局风格 | partial | D03, D04, D08 |
| DEC-030 | 版式候选检索 | partial | D03, D04 |
| DEC-031 | 版式评分与选择 | partial | D03, D05 |
| DEC-032 | 槽位映射 | partial | D11 |
| DEC-033 | 几何布局 | partial | D05 |
| DEC-034 | 字体与文本适配 | partial | D07 |
| DEC-035 | 颜色/背景/效果 | partial | D08 |
| DEC-036 | 图片裁切与适配 | partial | D09 |
| DEC-037 | 动画/切换/备注 | not_evidenced | 主机黑盒/未见显式实现 |
| DEC-038 | 预执行与后端选择 | partial | D15 |
| DEC-039 | 质量问题与回退 | partial | D14, D16 |
| DEC-040 | 终止与轨迹 | partial | D13, D17 |
