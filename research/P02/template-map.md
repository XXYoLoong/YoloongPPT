# P02 模板、槽位与容量映射

固定 main `833cda553b343be0e486a93b0b57cac962cdd566` + 实际 requirements 依赖 `pptagent==1.1.37`。v0.2.0/v1.1.38 是独立历史版本，未静默混用。所有文件 hash/函数范围见 [SourceIndex](source-index.json)。这是上游研究交付，产品架构/运行时未选定，AC-001–030 未执行。

仅一个 generic-starter：kicker→claim→evidence，48px主容器padding。四个不同占位token中 WIDTH/HEIGHT 多处替换；不是模板族、原生母版或Slide Layout。完整属性、测量坐标、IR与适用性见 [JSON](template-map.json)。

| 槽 | DOM | 字号/样式 | 几何/容量 |
|---|---|---|---|
| kicker | p.kicker | 14px/700/#8b6a35 | 流式；bottom margin16px |
| claim | h1 | 44px/line1.12 | 流式；bottom margin24px |
| evidence | p.message | 22px/line1.45 | max-width900px；无行数预算 |

body继承Arial/sans-serif、#182231；背景#f4f1ea；全局border-box。画布16:9=1280×720，4:3=960×720，A1=2244×3178；只有16:9实际转换验证。

## 转换边界

- geometry是computed DOM px/96 inch；字体px×0.75 point。原生text/table/images/rect/line由IR映射，复杂样式需PNG。
- body scroll超尺寸1px报错；locked layout允许0.1in误差；字体>12pt时bottom要求>=0.5in。原footer0.40in失败，top660→620px后六页真实重建通过。这是候选策略，不能当作普遍PowerPoint要求。
- 单行文字宽度+2%补偿；不等于自动缩字/拆页。暂无template容量预算或候选评分。
- class placeholder只返回inch坐标。此次slot chart-slot为x6.6667/y4.7917/w5.4167/h1.3542；CLI不消费，PPTX没有p:ph/chart。
- gradient实测PNG；inlineSVG因className.includes前置错误拒绝，未验证外链SVG。

## 正常、边界与失败

- 六页真模型HTML与strict complete：validation/verify-official-six.json。
- 表格、渐变、slot实际DOM-IR和对象PPTX：outputs/maps-probes；maps-probes.json。两张HTML预览实际查看无重叠/裁切；仅结构转换实验，未伪造官方host review或宣称完整delivery。
- 原footer失败：validation/official-six-build-host.json及footer-revision.json。
- 非本地资源拒绝与共享asset失效：validation/maps-probes.json。

源码：`starter:resource` (main Skill `assets/slide-template.html:1`); `core:scaffold` (main Skill `scripts/pptagent_runtime/core.py:110`); `converter:extractSlideData` (installed pptagent1.1.37 `html2pptx/html2pptx.js:708`); `converter:addElements` (installed pptagent1.1.37 `html2pptx/html2pptx.js:544`); `converter:validateTextBoxPosition` (installed pptagent1.1.37 `html2pptx/html2pptx.js:120`); `converter:placeholder-extract` (installed pptagent1.1.37 `html2pptx/html2pptx.js:1546`)
