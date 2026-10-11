# 批量局部修订新版本的 PowerPoint 证据

2026-10-11：复用现有本机 PowerPoint 16.0.20430.20092，对主工作包四个新产品输出各执行一次只读 COM 打开。使用现有验证脚本新增 `-IncludeContent`，记录实际原生 TextRange 原文、图表 series 名称/values/categories 与对象几何；没有修改原稿、另存副本、重复父样例编辑实验、重跑模型或渲染。

[report.json](report.json) 状态为 `passed_bounded_probe`，四个文稿的 ReadOnly 实际值均为 true，原稿 SHA-256 前后不变，无 COM 异常或清理错误。脚本 SHA-256=8843d76ffb2e04e8bccb09d0d54d76516e4298ecd0191966426bbe048633a716。

| 产品 run | 页数/原生对象 | 新版本实际内容 |
| --- | --- | --- |
| 7df19731-f9ed-419d-a02a-2d40d0a81641 | 6 页 / 26 对象 | 第 1 页标题“虚构测试：周照明用电演示”；第 6 页标题“结论：核对资料并按原文流程执行”。均为原生文字框，TextRange 实际原文与最终 DeckSpec 相同。 |
| d941e05b-06bf-409a-92ff-a1eddb9569ca | 6 页 / 26 对象 | 第 5 页原生柱图系列顺序为“本期”[90,72,54]、再“基线”[100,80,60]；两系列分类均为 A楼/B楼/C楼，COM 实测与最终 DeckSpec 完全相同。 |
| d429ecdf-96b2-4877-b88f-b3b436281e69 | 4 页 / 32 对象 | 8 张图片均作为原生 Picture 存在；第 1/2 图槽的原生文字图注为“人工绘制示意图2”/“人工绘制示意图1”。独立 OOXML 媒体 SHA 对照确认两个图槽实际字节为互换后的登记资产。 |
| 295cf4c2-07c2-4c50-9dc6-07f0020a4b59 | 8 页 / 33 对象 | 31 个原生文字框、1 个表格、1 个柱图；全部对象名称/几何及原生文字内容与最终 DeckSpec 一致，原生图表系列“降低幅度”[8]可读取。 |

[content-check.py](content-check.py) 使用已保存的实际 COM 读数对照每个制品最终 DeckSpec，不再调用 Office。它比较对象存在、数量、原生文字框、原文、几何、图表系列/数值/分类；图片实际字节使用 OOXML 对象名→关系→媒体 part 的独立 SHA 对照。这些检查是有界版本内容证据，不是新的系统 AC 计数。

## 保留的初始失败与精确原因

第一次对照结果 [content-check.json](content-check.json) 为 `failed`，489 条对照中 4 条失败，均来自同两条水平连接线在两个六页制品中的几何表达：

- `object_0d1e37cf-1473-4fe0-9cd6-081b564bff23`：明确端点 [6.6384,3.6088]→[7.08,3.6088]。
- `object_55e5be6b-49fc-4da4-b404-360d6177035e`：明确端点 [9.3984,3.6088]→[9.84,3.6088]。

两对象的布局 `bounds` 为保留占位高度而给出 0.001 英寸，但明确起止端点同 y。`src/yoloongppt/writer.py` 的 `connector_shape` 实际消费起止端点；生成 `cxnSp` 的 OOXML ext cy=0，PowerPoint COM 也读取 height=0。初次比较器误用了布局 bounds；并非四个制品新增内容或线端点错误。

比较器修正为对 connector 使用其明确端点，保留原始布局 bounds、预期点单位值、实际 COM 点单位值；0.001 pt 测量阈值保持。仅重算已保存 COM 证据，另存 [content-check-endpoints.json](content-check-endpoints.json)，489 条对照通过、0 条失败，原失败 JSON 未覆盖。原文只显式归一化 CR/CRLF/softbreak 至 LF，COM raw 原文完整保留在 report.json。

## 验收边界

AC-028 仍未通过：WithWindow=false，DisplayAlerts=1（ppAlertsNone），没有观察 UI 修复提示。原生文字和图表可通过 COM 读取，不能替代这四个新版本全部对象的编辑实测、PowerPoint 渲染、视觉或事实 QA、全部属性及未知部件保真。父样例的单文字副本编辑证据保持独立；产品原有低 DPI、覆盖等警告仍保留。

新增证据只关联原 AC-028、ADP-PP-01-01、TST-018 与对象能力范围；完整 PP-01、新建/事件/选择/并发等仍按原需求保留，不能由只读打开或 DeckSpec 内容匹配冲销。

复现只读打开时传入四个 run 下的 `deck.pptx`，指定全新 F 盘输出目录并添加 `-IncludeContent`，不添加 `-VerifyTextEdit`。复算保存的读数：

```powershell
$env:TEMP = $env:TMP = 'F:\YoloongPPT\validation\powerpoint-open-artifacts\tmp'
& 'F:\Python-3.11.11\python.exe' -X utf8 `
  'F:\YoloongPPT\validation\powerpoint-open-artifacts\batch-revision-live-open\content-check.py' `
  --output 'F:\YoloongPPT\validation\powerpoint-open-artifacts\batch-revision-live-open\recheck-content.json'
```

指定新的输出名以保留已有失败和成功证据；输入 PPTX 字节改变或已比较内容/几何不一致时检查显式失败。每次登记最终 DeckSpec SHA-256，未比较的规格字段不在本轮覆盖。
