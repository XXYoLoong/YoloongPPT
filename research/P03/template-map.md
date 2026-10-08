# Presenton 模板与版式结构摘要

## 来源和统计

来源固定为 Presenton commit `35bf44290f821323e003da854f78ffcb0e918167`。完整的机器可读 `ProjectTemplateMap` 见 [`template-map.json`](template-map.json)，包含模板源文件摘要、布局槽位、元素结构、主题令牌、容量字段和静态资产清单。图片、字体和缩略图只列路径、大小及 SHA-256，不复制二进制文件。

| ID | 模板 | Layouts | 合并组件组 | 静态资产文件 |
|---|---|---:|---:|---:|
| civic | Civic | 29 | 38 | 87 |
| dynamic | Dynamic | 32 | 40 | 23 |
| editorial | Editorial | 24 | 9 | 116 |
| executive | Executive | 32 | 47 | 20 |
| general | General | 12 | 15 | 17 |
| horizon | Horizon | 28 | 29 | 84 |
| landmark | Landmark | 27 | 17 | 123 |
| modern | Modern | 10 | 19 | 1 |
| momentum | Momentum | 28 | 27 | 33 |
| mosaic | Mosaic | 34 | 67 | 108 |
| nova | Nova | 28 | 26 | 102 |
| pulse | Pulse | 28 | 20 | 114 |
| signal | Signal | 24 | 20 | 98 |
| standard | Standard | 11 | 19 | 3 |
| swift | Swift | 9 | 20 | 3 |
| verdant | Verdant | 27 | 31 | 70 |
| **总计** | **16** | **383** | **444** | **1,002** |

此外有 1,600 个组件槽位、10,283 个嵌套元素和 6,080 个命名且可编辑的元素。元素类型计数：text 3,623、image 2,251、group 2,038、flex 1,132、vector 733、container 255、chart 113、grid 45、text-list 35、infographic 51、table 7。

## 字段与边界

- **槽位 / 中间表示：** 每个 layout 下按组件 ID、描述和组件位置表示槽位；保留元素树层级、元素类型、命名内容字段、元素位置/尺寸、布局容器参数和内联样式。
- **几何：** `Position{x,y}`、`Size{width,height}` 为源 JSON 数值；模板数据没有声明单位。认证生成代码中出现 1280×720 画布常量，但不把它解释为 JSON 单位。嵌套元素位置不做未经验证的全局坐标变换。
- **容量：** 记录文本字符长度、列表/表格行列、Flex/Grid 子项等明示的 min/max 字段。未从几何推算字符容量，也没有对模板实际渲染溢出做测量。上游另有 `TextCapacityPlan` 与文本增长步骤，属于认证生成流程，不是默认模板静态容量值。
- **Token / 样式：** 保留每模板的语义颜色、字体和元素级 style 字段/令牌原文。模板 JSON 与 SQL `TemplateV2` 的存储字段不完全相同；源码模型还列出 `raw_layouts`、`components` 和 `assets`。
- **继承：** 16 个默认模板 JSON 未声明 `parent` 或 `extends`。`merged_components[].variants` 是替代组件变体关系，未标为继承。
- **页面类型：** 源模板没有显式页面类型字段。JSON 中只给出由 layout ID 与描述关键词生成的候选标签，状态为推导候选或未分类，未映射到 YoloongPPT 产品页面类型。
- **适用条件：** 源模板未声明逐版式条件。Presenton 将版式 Schema 与 outline 交给结构生成路径形成 layout 索引映射；这不是预先声明的适用谓词，且本次未运行生成器。

## 核验状态

16 份 `template.json` 均解析成功；模板、版式、槽位、合并组件和静态文件计数与冻结源码目录一致。数据文件记录每个 `template.json` 与静态文件的 SHA-256，代码位置见 `template-map.json` 和 `source-index.json`。未运行模板生成 API、模型、PPTX 导出或视觉检查；对应 `VERIFY-RES-P03-04` 仍进行中，见 [`validation/verify-res-p03-04.json`](validation/verify-res-p03-04.json)。
