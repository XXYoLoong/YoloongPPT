// Source/EvidenceStore components are runnable; original SYS E2E remains pending.
import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const base='F:/YoloongPPT/AI_PPT_完整需求与任务矩阵_V0.3.xlsx',tmp='F:/YoloongPPT-Temp-P01-05';
const report=JSON.parse(await fs.readFile('F:/YoloongPPT/validation/source-runtime.json','utf8'));
if(report.passed!==true)throw Error('source verification required');
await fs.copyFile(base,`${tmp}/matrix-before-source-runtime.xlsx`,fs.constants.COPYFILE_EXCL);
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base));
const req=w.worksheets.getItem('需求主表'),tasks=w.worksheets.getItem('可执行任务');
for(const [r,t,id,note] of [
 [40,68,'IN-001','原文/上下文已载入并保留；主题、要求、修改意图语义提取尚未实现。'],
 [41,69,'IN-002','真实结构解析/原文锚点已运行；行内定位为所属块范围，部分Markdown扩展明确拒绝。'],
 [53,81,'IN-014','多源ID/哈希重复候选保留；优先级DEC-004及语义冲突检测未执行。'],
 [54,82,'IN-015','文本路径、编码、NUL、超限/不支持及解析失败明确返回；其他格式检测待接入。'],
 [55,83,'IN-016','文本/Markdown块锚点与原文回读一致；其他格式及最终PPT对象追溯待验收。'],
 [186,295,'SYS-003','SourceBundle与文本/Markdown解析已实际运行；IN其他格式及原SYS E2E待完成。'],
 [187,296,'SYS-004','SQLite原文/结构/锚点/hash/版本与ID查询已运行；原SYS生成QA修订E2E待完成。']]){
 if(req.getRange(`A${r}`).values[0][0]!==id||tasks.getRange(`A${t}`).values[0][0]!==`TASK-${id}`)throw Error('row mismatch');
 req.getRange(`N${r}:P${r}`).values=[['进行中','src/yoloongppt/sources.py；evidence.py；markdown.py；validation/source-runtime.json',note]];
 tasks.getRange(`L${t}:M${t}`).values=[['进行中','validation/source-runtime.json；src/yoloongppt/；原完整范围/E2E仍待执行']];
 req.getRange(`A${r}:P${r}`).format.rowHeightPx=240;
}
const interfaces=w.worksheets.getItem('系统组件接口');
for(const [r,id] of [[4,'SYS-003'],[5,'SYS-004']]){
 if(interfaces.getRange(`A${r}`).values[0][0]!==id)throw Error('interface row mismatch');
 interfaces.getRange(`H${r}:I${r}`).values=[['进行中','src/yoloongppt/；validation/source-runtime.json；文本组件可运行，原E2E待验证']];
}
const objects=w.worksheets.getItem('数据对象');
if(objects.getRange('A2').values[0][0]!=='RawTaskRequest'||objects.getRange('A7').values[0][0]!=='SourceEvidence')throw Error('object rows mismatch');
objects.getRange('J2').values=[['src/yoloongppt/sources.py；validation/source-runtime.json；原文与上下文已载入，完整原始请求和语义规范化仍待完成。']];
objects.getRange('J7').values=[['contracts/source-evidence.schema.json；src/yoloongppt/evidence.py；validation/source-runtime.json；文本快照及原生块已存储，confidence为null，其他格式与完整E2E待接入。']];
w.recalculate();
await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/matrix-after-source-runtime.xlsx`);
const preview=await w.render({sheetName:'需求主表',range:'N41:P41',scale:1});
await fs.writeFile(`${tmp}/source-runtime-matrix-preview.png`,new Uint8Array(await preview.arrayBuffer()));
console.log('Seven source-related requirement/task notes updated, all in progress.');
