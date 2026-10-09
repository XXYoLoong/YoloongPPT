// Five SYS entries are in progress: component checks do not meet original E2E acceptance.
import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const base='F:/YoloongPPT/AI_PPT_完整需求与任务矩阵_V0.3.xlsx',tmp='F:/YoloongPPT-Temp-P01-05';
const report=JSON.parse(await fs.readFile('F:/YoloongPPT/validation/runtime-core.json','utf8'));
if(report.passed!==true)throw Error('component verification required');
await fs.copyFile(base,`${tmp}/matrix-before-system-core.xlsx`,fs.constants.COPYFILE_EXCL);
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base));
const req=w.worksheets.getItem('需求主表'),tasks=w.worksheets.getItem('可执行任务'),interfaces=w.worksheets.getItem('系统组件接口');
for(const [r,t,i,id] of [[184,293,2,'SYS-001'],[189,298,7,'SYS-006'],[190,299,8,'SYS-007'],[202,311,20,'SYS-019'],[203,312,21,'SYS-020']]){
 if(req.getRange(`A${r}`).values[0][0]!==id||tasks.getRange(`A${t}`).values[0][0]!==`TASK-${id}`||interfaces.getRange(`A${i}`).values[0][0]!==id)throw Error('row mismatch');
 req.getRange(`N${r}:P${r}`).values=[['进行中','ARCHITECTURE.md；src/yoloongppt/；validation/runtime-core.json','Docker组件校验/CLI/API已运行；完整生成、QA、修订E2E未执行，不能标完成。']];
 tasks.getRange(`L${t}:M${t}`).values=[['进行中','src/yoloongppt/；validation/runtime-core.json；原E2E验收待执行']];
 interfaces.getRange(`H${i}:I${i}`).values=[['进行中','src/yoloongppt/；validation/runtime-core.json；组件可运行，E2E待验证']];
 req.getRange(`A${r}:P${r}`).format.rowHeightPx=240;
}
const objects=w.worksheets.getItem('数据对象');
if(objects.getRange('A3').values[0][0]!=='TaskSpec')throw Error('TaskSpec row mismatch');
objects.getRange('J3').values=[['contracts/task-spec.schema.json；src/yoloongppt/tasks.py；validation/runtime-core.json；运行时形状/ID校验已接入，E2E仍待执行。']];
w.recalculate();
await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/matrix-after-system-core.xlsx`);
const preview=await w.render({sheetName:'需求主表',range:'N184:P184',scale:1});
await fs.writeFile(`${tmp}/system-core-matrix-preview.png`,new Uint8Array(await preview.arrayBuffer()));
console.log('Five SYS requirements/tasks/interfaces marked in progress; original E2E acceptance preserved.');
