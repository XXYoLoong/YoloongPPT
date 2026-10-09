# P02 PowerPoint 对象与QA能力映射

固定 main `833cda553b343be0e486a93b0b57cac962cdd566` + 实际 requirements 依赖 `pptagent==1.1.37`。v0.2.0/v1.1.38 是独立历史版本，未静默混用。所有文件 hash/函数范围见 [SourceIndex](source-index.json)。这是上游研究交付，产品架构/运行时未选定，AC-001–030 未执行。

标记作用于基线完整对象范围。Partial中有原生写入子集；不将底层库潜在能力提升为官方路线支持。SVG实测失败保留；Unsupported不取消产品需求。

| ID | 对象 | 状态 | 证据/限制 |
|---|---|---|---|
| PPT-001 | 演示文稿生命周期 | Partial | 新建/写出PPTX与count/ratio/zip检查；无普通PPTX打开后保真save/metadata编辑 |
| PPT-002 | Slide 管理 | Partial | 按连续HTML新建slide；没有导入、删除/复制/任意重排既有PPTX对象的完整接口 |
| PPT-003 | Sections/Custom Show | Unsupported | 官方路线无section/custom-show调用 |
| PPT-004 | Slide Master | Unsupported | generic HTML不解析/保留/编辑Slide Master |
| PPT-005 | Slide Layout | Unsupported | canvas layout指页面尺寸，不是原生Slide Layout管理 |
| PPT-006 | Theme | Partial | CSS字体/色彩写成局部style；未映射原生Theme/theme inheritance |
| PPT-007 | Placeholder | Unsupported | placeholder仅coords，官方CLI不消费；没有原生p:ph |
| PPT-008 | 文本框 | Partial | addText实测原生可编辑文字；CSS支持子集与2%补偿，无完整编辑/roundtrip |
| PPT-009 | 字符/段落 | Partial | rich runs/bullets/paragraph样式源码映射；列表实测；未全字符/段落属性或roundtrip |
| PPT-010 | 语言与文字方向 | Partial | 中文正文已写出；旋转/writing-mode有代码；language只是HTML属性，未验证bidi/语言OOXML |
| PPT-011 | AutoShape | Partial | rectangle/roundRect shape与样式；非全AutoShape形状集合 |
| PPT-012 | Line/Connector/Freeform | Partial | line addShape；未见native connector attachment/freeform路径 |
| PPT-013 | Group/Z-order | Partial | DOM顺序写入对应堆叠；没有原生Group结构/稳定组关系 |
| PPT-014 | 图片 | Partial | addImage与复杂CSS PNG路径；渐变PNG图对象实测，不等于所有图片裁切/替换保真 |
| PPT-015 | SVG/Icon | Unsupported | 内联SVG实测className.includes失败；代码拟做PNG而非原生SVG；外链SVG回退未测 |
| PPT-016 | Table | Partial | 实测原生3x2表格和正文；代码映射span/runs/borders，未全表操作或roundtrip |
| PPT-017 | Chart | Unsupported | addChart只有顶部文档示例，官方CLI不消费coords，没有native chart路径 |
| PPT-018 | Equation | Unsupported | 没有native Equation/OMML写入路径；普通文本不能算公式对象 |
| PPT-019 | SmartArt | Unsupported | 没有native SmartArt数据/关系路径 |
| PPT-020 | Audio/Video/GIF | Unsupported | 没有音频/视频/动画GIF嵌入路径；不推断底层库潜在能力 |
| PPT-021 | OLE/Embedded Object | Unsupported | 没有OLE/embedded object写入路径 |
| PPT-022 | Hyperlink/Action | Unsupported | 写入器未把DOM href映射到hyperlink/action；文本呈现不算链接动作 |
| PPT-023 | Speaker Notes | Unsupported | 没有addNotes或notes master处理；HTML讲稿不算Speaker Notes |
| PPT-024 | Comments | Unsupported | 没有comment/author/thread写入路径 |
| PPT-025 | Headers/Footers/日期/页码 | Partial | 可用普通HTML正文放页码/footer；无原生动态日期/header/footer字段 |
| PPT-026 | Transitions | Unsupported | 无transition接口 |
| PPT-027 | Animations | Unsupported | 无animation timing接口 |
| PPT-028 | Effects | Fallback | solid/shadow有局部native映射；gradient实测PNG，复杂filter/rounded image源码栅格化，不保留原生效果 |
| PPT-029 | Accessibility | Unsupported | 未映射altText/reading order/accessibility元数据 |
| PPT-030 | Object identity/metadata | Unsupported | 没有稳定源对象ID/原位编辑身份追踪；新建PPTX生成器ID不等于产品identity |

## QA、修订与未验证范围

- 主机实际看图、官方record和strict finalize通过；外部模型JSON字符串slide失败仍为Partial。
- 内容事实、来源真实性、对象编辑行为与Microsoft PowerPoint打开未验证；目前只做ZIP结构/count/aspect、真实OOXML文字/table/image检查。
- 主机HTML修订并全量重建已验证；无自动局部修订或保真普通PPTX编辑。
- 临时研究instrumentation没有改写上游；对象fixture不是AI生成验收。

逐对象源引用/基线范围/运行或source-only区分与roundtrip边界见 [JSON](capability-map.json)。
