# 原生对象与既有 PPT 修订

读取原 PPT-001–030、PP-05、REV-001/002/004/005/010 行后实现 `native_objects` 与 `existing_deck`，通过 operations 同时接入 CLI、HTTP 与 MCP。原生执行入口支持文字、形状、连接线、图片、表格、图表、组合；这条入口执行调用方给定对象，不声称是 AI 规划。

已有 PPT 索引使用实际 slide ID、shape ID；定位支持对象 ID、名称、文本、页号、占位符。修改需 expected_sha256，保存新副本；文字、格式、几何、表格单元格、图表及内嵌工作簿、图片、替代文字、备注实际可改。文字替换明确保留首段/首 run 格式，原 run 分段属于指定替换范围，不宣称全部富文本原样。

Docker 内 32 项检查通过，实物在 `native-object-artifacts/`。fixture 修改只涉及 slide1、chart1、内嵌 XLSX、image1、notes1 五个部件；其他 ZIP 成员 payload 字节相同，修改页非目标形状 XML 相同。主集成另实际调用 `/compose-native`、`/inspect-deck`、`/edit-deck`。

30 类能力均有 CRUD/读取/保留/渲染边界。未知对象只保证未修改部件保留；共享图表/图片、签名、锁定对象、敏感路径和未实现操作阻断。复杂对象、SmartArt/OLE 编辑、动画/切换、完整可访问性、全后端、自然语言语义定位及完整质量/系统 AC 尚未完成。结果保持 partial/unsupported，不以保留未知 XML 宣称可编辑支持。
