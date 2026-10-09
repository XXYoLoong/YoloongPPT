// Status update only after original RES-032/033 registration acceptance passes.
import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const base='F:/YoloongPPT/AI_PPT_完整需求与任务矩阵_V0.3.xlsx',tmp='F:/YoloongPPT-Temp-P01-05';
const report=JSON.parse(await fs.readFile('F:/YoloongPPT/research/reuse/validation.json','utf8'));
if(report.passed!==true)throw Error('verification required');
await fs.copyFile(base,`${tmp}/matrix-before-res-032-033.xlsx`,fs.constants.COPYFILE_EXCL);
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base));
const req=w.worksheets.getItem('需求主表'),tasks=w.worksheets.getItem('可执行任务');
for(const [r,t,id] of [[38,66,'RES-032'],[39,67,'RES-033']]){
 if(req.getRange(`A${r}`).values[0][0]!==id||tasks.getRange(`A${t}`).values[0][0]!==`TASK-${id}`)throw Error('row mismatch');
}
req.getRange('N38:P39').values=[
 ['已完成','research/reuse/ReuseDecisionRegistry.json；research/reuse/source-manifest.json；research/reuse/validation.json','18项模块分四类；2份MIT文件限定资格，未接入产品；P05许可冲突保留。'],
 ['已完成','research/reuse/ResearchFixtureIndex.json；research/reuse/source-manifest.json；research/reuse/validation.json','35项资产覆盖五项目；P03无生成PPTX、P04无研究渲染截图，未执行项显式记录。']];
tasks.getRange('L66:M67').values=[
 ['已完成','research/reuse/ReuseDecisionRegistry.json；research/reuse/validation.json'],
 ['已完成','research/reuse/ResearchFixtureIndex.json；research/reuse/validation.json']];
req.getRange('A38:P39').format.rowHeightPx=240;
w.recalculate();
console.log((await w.inspect({kind:'table',range:'需求主表!N38:P39',include:'values',tableMaxRows:2,tableMaxCols:3})).ndjson);
await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/matrix-after-res-032-033.xlsx`);
const preview=await w.render({sheetName:'需求主表',range:'N38:P39',scale:1});
await fs.writeFile(`${tmp}/res-032-033-matrix-preview.png`,new Uint8Array(await preview.arrayBuffer()));
