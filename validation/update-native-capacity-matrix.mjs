import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const root='F:/YoloongPPT',tmp='F:/YoloongPPT-Temp-P01-05';
const original=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`;
const before=`${tmp}/matrix-before-native-capacity.xlsx`,after=`${tmp}/matrix-after-native-capacity.xlsx`;
const digest=raw=>crypto.createHash('sha256').update(raw).digest('hex');
try{await fs.copyFile(original,before,fs.constants.COPYFILE_EXCL);}catch(e){if(e.code!=='EEXIST')throw e;}
const baseline=digest(await fs.readFile(before));
if(digest(await fs.readFile(original))!==baseline)throw Error('Original matrix changed after package baseline; refusing overwrite');
const evidence=JSON.parse(await fs.readFile(`${root}/validation/native-capacity-integration.json`,'utf8'));
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(before)),allowed=[];
const locate=(sheet,id)=>{const values=w.worksheets.getItem(sheet).getRange('A1:A500').values;return values.findIndex(row=>row[0]===id)+1;};
const set=(sheet,range,values)=>{w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});};
const notes={};
const group=(ids,text,path)=>{for(const id of ids)notes[id]={text,path};};
group(['TPL-002','TPL-003','TPL-004','TPL-006','TPL-008','TPL-015','TPL-016','DEC-028','DEC-032','SYS-008'],
  evidence.template.note,'validation/模板原生槽位与品牌锁.md；validation/template-slot-artifacts/');
group(['AST-002','AST-007','DEC-030','DEC-031','DEC-036'],
  evidence.gallery.note,'validation/实现八图原生布局与焦点裁切.md；validation/gallery-artifacts/');
group(['DEC-014','DEC-015','DEC-016','DEC-017','DEC-018','DEC-019','QA-006'],
  evidence.adaptive.note,'validation/完整正文和大表格自适应分页.md；validation/adaptive-content-artifacts/');
group(['DEC-033','DEC-034','SYS-010','SYS-012'],
  evidence.integration_note,'validation/native-capacity-integration.json；validation/native-capacity-live-artifacts/');
for(const [id,{text,path}] of Object.entries(notes)){
 const row=locate('需求主表',id);if(!row)throw Error(`Missing requirement ${id}`);
 const previous=w.worksheets.getItem('需求主表').getRange(`N${row}:P${row}`).values[0];
 if(previous[0]==='已完成')throw Error(`Cannot rewrite completed ${id}`);
 set('需求主表',`N${row}:P${row}`,[['进行中',`${previous[1]??''}；${path}`,`${previous[2]??''}\n2026-10-11增量：${text} 完整原验收仍未通过。`]]);
 for(const prefix of ['TASK-','VERIFY-']){
  const tr=locate('可执行任务',prefix+id);if(!tr)continue;
  const old=w.worksheets.getItem('可执行任务').getRange(`L${tr}:M${tr}`).values[0];
  if(old[0]==='已完成')continue;
  set('可执行任务',`L${tr}:M${tr}`,[['进行中',`${old[1]??''}\n2026-10-11增量：${text} ${path}；完整原验收未通过。`]]);
 }
 for(const [sheet,state,last] of [['决策链','M','N'],['模板版式要求','H','I'],['素材与可视化','H','I'],['系统组件接口','H','I']]){
  const dr=locate(sheet,id);if(!dr)continue;
  const old=w.worksheets.getItem(sheet).getRange(`${state}${dr}:${last}${dr}`).values[0];
  if(old[0]==='已完成')continue;
  set(sheet,`${state}${dr}:${last}${dr}`,[['进行中',`${old[1]??''}\n2026-10-11增量：${text} ${path}；完整原验收未通过。`]]);
 }
}
for(const id of ['AC-006','AC-012','AC-014','AC-015']){
 const row=locate('验收矩阵',id);
 const detail=evidence.acceptance[id];if(!detail)throw Error(`Missing actual status ${id}`);
 set('验收矩阵',`G${row}:J${row}`,[[detail.state,detail.note,detail.evidence,'完整原验收未通过']]);
}
for(const id of ['S17','S18','S19','S20','S25','S26','S27','S28','S29','S30','S31','S32','S33','S34','S35','S36']){
 const row=locate('0-1全链路',id);const old=w.worksheets.getItem('0-1全链路').getRange(`G${row}:I${row}`).values[0];
 set('0-1全链路',`G${row}:I${row}`,[['进行中',`${old[1]??''}；validation/native-capacity-integration.json`,`${old[2]??''}\n2026-10-11：${evidence.integration_note} 完整S步骤与原验收未通过。`]]);
}
w.recalculate();
await fs.writeFile(`${tmp}/native-capacity-matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/native-capacity-matrix-evidence.json`,JSON.stringify({baseline_sha256:baseline,requirement_ids:Object.keys(notes),...evidence},null,2));
await fs.writeFile(`${tmp}/native-capacity-matrix-preview.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'N151:P154',scale:1,format:'png'})).arrayBuffer()));
await(await SpreadsheetFile.exportXlsx(w)).save(after);
console.log(JSON.stringify({output:after,requirements:Object.keys(notes).length,allowedRanges:allowed.length}));
