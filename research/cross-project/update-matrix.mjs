// One-time authoritative status update after VERIFY-RES-031 passes; all temporary files on F:.
import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const base='F:/YoloongPPT/AI_PPT_完整需求与任务矩阵_V0.3.xlsx',tmp='F:/YoloongPPT-Temp-P01-05';
const report=JSON.parse(await fs.readFile('F:/YoloongPPT/research/cross-project/validation.json','utf8'));
if(report.passed!==true)throw Error('verification required');
await fs.copyFile(base,`${tmp}/matrix-before-res-031.xlsx`,fs.constants.COPYFILE_EXCL);
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base));
const req=w.worksheets.getItem('需求主表'),tasks=w.worksheets.getItem('可执行任务');
if(req.getRange('A37').values[0][0]!=='RES-031'||tasks.getRange('A64').values[0][0]!=='TASK-RES-031'||tasks.getRange('A65').values[0][0]!=='VERIFY-RES-031')throw Error('row mismatch');
req.getRange('N37:P37').values=[['已完成','research/cross-project/CrossProjectMatrix.json；research/cross-project/validation.json','15维度×5项目，来源/运行/黑盒分列；P03 VERIFY仍进行中。']];
tasks.getRange('L64:M65').values=[['已完成','research/cross-project/CrossProjectMatrix.json；research/cross-project/source-catalog.json'],['已完成','research/cross-project/validation.json']];
req.getRange('A37:P37').format.rowHeightPx=160;
w.recalculate();
console.log((await w.inspect({kind:'table',range:'需求主表!N37:P37',include:'values',tableMaxRows:1,tableMaxCols:3})).ndjson);
await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/matrix-after-res-031.xlsx`);
const preview=await w.render({sheetName:'需求主表',range:'N37:P37',scale:1});
await fs.writeFile(`${tmp}/res-031-matrix-preview.png`,new Uint8Array(await preview.arrayBuffer()));
