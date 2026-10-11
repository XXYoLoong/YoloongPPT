# PowerPoint 实际打开与单文字副本编辑证据

2026-10-11：复用现有正式产品生成物，不调用模型、不重新生成、不重新渲染；本目录是外部 Windows/Office 验证，不是产品 PowerPoint 后端实现。

原始需求依据：Excel `验收矩阵!29` 的 AC-028 要求“PowerPoint 无修复提示”；`需求主表!172` 的 ADP-PP-01-01 与 `PowerPoint后端!2` 要求完整 PP-01 PoC 和能力矩阵；`需求主表!295` / `可执行任务!440` 的 TST-018 要求局部修改无关页面/对象不变且可继续编辑。关联 TASK-ADP-PP-01-01、VERIFY-ADP-PP-01-01、TASK-TST-018；对象范围关联 PPT-001/002/008/011/012/014/016/017。全部原能力范围和验收条件保留。

## 实际执行

已安装 Microsoft PowerPoint，COM `PowerPoint.Application` 有注册；应用 Version=16.0，实际二进制及 Click-to-Run 版本=16.0.20430.20092。本轮未安装软件、修改注册表或更改 PowerPoint 全局配置。全部项目文件、应用 TEMP/TMP 及验证副本在 F 盘。

首个运行记录于 [20261011-current-live-open/report.json](20261011-current-live-open/report.json)，验证每个源 PPTX 的只读状态、页数、原生 shape 类型/ID/name/几何/层级/文本哈希/表格单元格哈希/图表类型和 series 数量，并在独立副本修改第一页第一个非空文字框、SaveAs 后只读重开。

| 产品 run | 页数/原生对象 | 实际 COM 类型 | 原稿 SHA-256（前后相同） |
| --- | --- | --- | --- |
| 468ac35a-eef5-424f-9585-2fa45ad6722a | 4 页 / 32 对象 | 22 TextBox、8 Picture、2 Table | 2113ef0e7053c646d4dc13a3afa835309af0a1a04091f8aca95f2c30de44a3c0 |
| 39a2dbf3-c19b-4da2-99a6-27fe7b82ef7a | 6 页 / 26 对象 | 18 TextBox、1 Picture、3 AutoShape、2 Line、1 Table、1 Chart | 25ee366566ddafc9f1ad5bff08df09b5aa803adef2117bcd3bc6b711c3dca733 |

两个源文件实际只读打开成功；两个副本均成功持久化文字修改并重开，目标文字 SHA-256 匹配预期，非目标已测 COM 属性差异为 0，页数/尺寸保持。原稿未保存，SHA-256 未变。副本位于对应 `input-1/` 与 `input-2/`，不是正式产品修订输出。

脚本随后增加最终清理时核对当前打开文稿数、清空已释放 COM 引用、登记源 run ID 与删除已分配 Office TEMP 的保护。对这项生命周期变化仅进行只读定向复验，未重复副本文字实验；[20261011-cleanup-check/report.json](20261011-cleanup-check/report.json) 记录当时脚本 SHA-256=13e32bbf6ca2f95386f3f8cbef697e992fcad78a9d02a1e3a196a2253f553018、两份源文稿打开成功与 cleanup_errors=[]。PowerPoint 退出后，仅清除本目录分配的临时诊断文件；保留有意生成的 JSON/PPTX 证据。

批量修订产生新版本后，脚本增加显式 `-IncludeContent` 只读选项，登记原生 TextRange 原文及图表实际系列名称/数值/分类。四个新产品制品的实际打开、内容对照和保留的初始比较失败见 [batch-revision-live-open/README.md](batch-revision-live-open/README.md)。没有重复父样例的副本编辑实验；旧证据保留各自脚本版本。

## 不可扩大解释的边界

- **AC-028 仍部分执行/未通过。** WithWindow=false，没有 UI 观察修复提示；DisplayAlerts=1（ppAlertsNone），脚本未更改。COM 无异常不证明没有修复提示。报告将 `ac028_no_repair_prompt_verified` 留空、`ac028_passed=false`。
- **PP-01 仍仅部分真实 PoC 证据。** 本轮证明打开/读取/单文字更新/另存/重开/关闭；没有证明新建、添加或删除页面、全部对象 CRUD、母版/主题/备注/评论/动画/事件/选择/并发/权限/全部渲染能力，也未接入产品运行时。
- **TST-018 仅已测属性范围。** COM 比较没有覆盖所有格式、字体 runs、图表数据编辑、母版、未知对象和未知部件；不能判完整验收通过。
- **Office SaveAs 不保持包字节。** 四页副本有 52 个 part 改写、1 个删除（printerSettings）；六页副本有 62 个 part 改写、2 个删除、1 个新增（嵌入 Excel 文件重写并改名，另删 printerSettings）。所有 slide XML 和其关系都有改写，明细已保存在报告。媒体图片保持字节相同；不能以非目标已测 COM 属性不变宣称全包保真。
- 本轮没有用 PowerPoint 实际渲染/视觉复核，没有执行表格或图表的 UI 编辑，没有绕过现存产品 QA 警告或 DEC-040 final_allowed=false。

## 复现

在 Windows PowerShell 7、已有本机 PowerPoint 条件下，用全新输出目录执行；`-VerifyTextEdit` 显式启用 F 盘副本实验，不改变源文件。脚本拒绝 C 盘输入/输出与已存在的证据输出目录。

```powershell
$env:TEMP = $env:TMP = 'F:\YoloongPPT\validation\powerpoint-open-artifacts\tmp'
$output = 'F:\YoloongPPT\validation\powerpoint-open-artifacts\recheck-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
& 'F:\YoloongPPT\validation\verify-powerpoint-open.ps1' `
  -InputPptx @(
    'F:\YoloongPPT\validation\native-capacity-live-artifacts\current-resumed\deck.pptx',
    'F:\YoloongPPT\validation\visual-live-artifacts\qa-recovered-success-39a2dbf3\deck.pptx'
  ) -OutputDirectory $output -VerifyTextEdit
```

API 参数与提示边界使用 Microsoft 官方文档：[Presentations.Open](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open)、[Presentation.SaveAs](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.saveas)、[Application.DisplayAlerts](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.displayalerts)。
