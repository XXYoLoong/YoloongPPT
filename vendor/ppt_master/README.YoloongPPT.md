# PPT Master 直接模块复用

原项目：https://github.com/hugohe3/ppt-master  
固定提交：`2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d`  
关联原需求：RES-032、PPT-015、PPT-030、SYS-012、SYS-013。

`SOURCE.json` 逐文件记录原路径、原始 SHA-256 和修改状态。这些上游文件未经修改；本项目适配代码在 `src/yoloongppt/upstream_native.py`，不在原包内改写导出器。源码依据固定研究快照复用，没有重新 clone。

本包包括原生 SVG→DrawingML/PPTX 导出、PPTX→SVG 源对象恢复、OPC 交付审计及其实际 Python 依赖闭包。为保持上游原 attribution guard 可执行，保留它要求的元数据、许可、赞助通知与入口代码。SKILL.md 是上游归属元数据，不是本项目新的用户确认或产品工作流要求。

PPT Master 代码为 MIT，原版权/许可见 LICENSE。DrawingML preset 数据具有独立来源：Apache POI 的 Apache-2.0，Open XML SDK 的 MIT；原数据 NOTICE 和许可证在 `scripts/pptx_shapes/data/`。font_metrics/font_advances 是上游提取的数值数据，本包没有复制字体文件。没有复制捆绑图标、品牌模板、图片、声音、字体文件、PDF 转换器或对应 AGPL 依赖。

当前产品消费接口：

- `insert_native_svg(slide, svg_path, object_id, bounds, resource_root=None)`：直接复用上游 SVG→DrawingML，把可编辑矢量对象插入目标 slide 的原生组，返回实际组/子对象 ID 映射。bounds 使用现有 writer 的英寸，明确按 contain 等比例定位；绝对字号、线宽、文本间距和效果长度在融合层按同一比例适配并记录 before/after，解决 LibreOffice 仅缩放组几何、不缩放绝对字号的问题。纯矢量、文本、原生几何/effects 等按上游实际支持执行；图像/图表/超链接的部件关系不能直接拼接，插入前显式拒绝，改由明确调用的整页/roundtrip 路线处理。
- `export_svg_deck(svg_paths, output, title=..., notes=..., resource_root=...)`：明确无模板的 flat native 导出，不栅格化整个页面，不冒充完整模板路线；各页名称唯一，备注绑定 SVG stem。原生转换 trace、跳过对象和结构审计完整返回；跳过对象或审计错误阻断发布。
- `import_native_deck(source, workspace)` / `export_native_roundtrip(workspace, output)`：复用上游既有 PPTX 的 source-preserving workspace 和对象恢复；工作区已有源文件时拒绝覆盖。局部修改 authoring SVG 后仍保留上游原代理/关系/原生恢复保护。
- `audit_native_deck(path)`：上游只读 OPC/部件/关系/原生交付检查。它不代表视觉、事实或全部系统 AC 通过。
- `canvas_guard` / `relationship_guard` / `chart_edit_guard` / `table_merge_guard`：直接调用上游画布、关系 QName、图表可编辑性、合并拓扑规则，保留支持/拒绝原因。

模块在隔离 Python worker 运行，防止上游平铺模块名称及控制台初始化影响主服务。输入继续消费本项目现有 XML/OOXML 安全限制；SVG 外链必须先通过资产入口取得、登记为本地文件；资源越界、活动内容、DTD 被阻断。上游 API 中的图像优化和危险兼容归一化没有开启。

已有镜像的 python-pptx、XlsxWriter、Pillow 可运行本次实际子集。skia-pathops、uharfbuzz 等高级布尔/文字轮廓依赖未安装时返回明确的缺失模块，不能宣称相应能力完成。未知许可/品牌/全对象/所有后端/全部验收不由此包冲销。

实际验证：`python -B validation/verify-upstream-native.py /runtime/<独立证据目录>`。正常、边界、失败、真实输出、原生插入、局部文字 roundtrip 与结构字节保留均执行；实际 LibreOffice/PDF/PNG 渲染分别记录。完整原验收由主矩阵按真实证据判定。
