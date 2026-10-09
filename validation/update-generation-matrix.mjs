import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const base='F:/YoloongPPT/AI_PPT_完整需求与任务矩阵_V0.3.xlsx',tmp='F:/YoloongPPT-Temp-P01-05';
const report=JSON.parse(await fs.readFile('F:/YoloongPPT/validation/generation-runtime.json','utf8'));
if(!report.passed)throw Error('generation component evidence required');
await fs.copyFile(base,`${tmp}/matrix-before-generation.xlsx`,fs.constants.COPYFILE_EXCL);
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base));
const req=w.worksheets.getItem('需求主表'),tasks=w.worksheets.getItem('可执行任务'),interfaces=w.worksheets.getItem('系统组件接口');
for(const [r,t,i,id,note] of [
 [188,297,6,'SYS-005','真实模型规划及模型阶段恢复已接入；完整DEC节点/条件分支/节点重跑未完成。'],
 [193,302,11,'SYS-010','新建子集SlideSpec含内容/几何/样式/来源/备注，实际writer消费；其他对象/绑定/模板待完成。'],
 [194,303,12,'SYS-011','实际DAG与明确PP-05方法实现已执行；正式能力实体登记及完整预执行边界待完成。'],
 [195,304,13,'SYS-012','原生文本/表格/图表/备注调用与实际ObjectMap已运行；其他原子能力待扩展。'],
 [196,305,14,'SYS-013','真实10页原生新建/顺序执行；导入模板/master/layout/theme及已有deck修改待完成。'],
 [197,306,15,'SYS-014','实际LibreOffice PDF/10 PNG含hash/version，F盘IPC挂载；live截图/缩略图待完成。'],
 [198,307,16,'SYS-015','结构/数值/几何/可编辑性与真实PNG模型审查已运行；可访问性及完整QA未完成，模型可能误判。'],
 [199,308,17,'SYS-016','单正文原生对象修订仅改变一个slide XML，ID/其他parts保持，复审/QA恢复；完整RevisionPlan/节点重跑待完成。'],
 [200,309,18,'SYS-017','JSON/PPTX/render/trace/QA/manifest实际保存与hash，失败证据保留；完整生命周期清理待完成。']]){
 if(req.getRange(`A${r}`).values[0][0]!==id||tasks.getRange(`A${t}`).values[0][0]!==`TASK-${id}`||interfaces.getRange(`A${i}`).values[0][0]!==id)throw Error('row mismatch');
 req.getRange(`N${r}:P${r}`).values=[['进行中','src/yoloongppt/；validation/generation-runtime.json；validation/generation-artifacts/',note]];
 tasks.getRange(`L${t}:M${t}`).values=[['进行中','真实草稿链路及31项组件检查见validation/generation-runtime.json；完整原验收仍未通过。']];
 interfaces.getRange(`H${i}:I${i}`).values=[['进行中',note+' 实物：validation/generation-artifacts/']];
 req.getRange(`A${r}:P${r}`).format.rowHeightPx=230;
}
for(const [r,t,id,note] of [[9,11,'GOV-008','已有真实10页可编辑PPTX→render→部分QA→单对象修订；完整DEC/全部QA/所有P0 AC未通过。'],[202,311,'SYS-019','CLI接入generate/resume/revise/recheck；完整命令/任务生命周期仍待原验收。'],[203,312,'SYS-020','HTTP接入/generate、/resume、/revise、/recheck，真实生成已运行；完整jobs/取消/重试等仍待原验收。']]){
 if(req.getRange(`A${r}`).values[0][0]!==id||tasks.getRange(`A${t}`).values[0][0]!==`TASK-${id}`)throw Error('entry row mismatch');
 req.getRange(`O${r}:P${r}`).values=[['validation/generation-artifacts/；validation/generation-runtime.json',note]];
 tasks.getRange(`M${t}`).values=[[note+' 证据：validation/generation-artifacts/']];
}
const ac=w.worksheets.getItem('验收矩阵');
for(const [r,id,note] of [[2,'AC-001','10页实物与执行过的QA P0=0；完整DEC轨迹、全部QA及原通过条件未证明。'],[28,'AC-027','原生ObjectMap可回到source/evidence/spec/call/QA；完整decision链及随机最终对象全范围未证明。'],[29,'AC-028','PowerPoint 16.0 COM实际打开10页32对象无异常；未经UI观察修复提示，不能判通过。']]){
 if(ac.getRange(`A${r}`).values[0][0]!==id)throw Error('AC row mismatch');
 ac.getRange(`G${r}:J${r}`).values=[['部分执行/未通过','validation/generation-artifacts/；validation/powerpoint-generation-open.json','已执行部分：真实生成/修订/报告与平台观测',note]];
 ac.getRange(`A${r}:J${r}`).format.rowHeightPx=220;
}
const pp=w.worksheets.getItem('PowerPoint后端');
if(pp.getRange('A6').values[0][0]!=='PP-05')throw Error('backend row mismatch');
pp.getRange('H6:J6').values=[['已运行（新建子集）','部分执行/未通过','python-pptx 1.0.2；实际原生对象/单文本修订，完整后端边界待验证；validation/generation-artifacts/']];
const objects=w.worksheets.getItem('数据对象');
for(const [r,id,note] of [[37,'SlideSpec','内容/几何/样式/来源/备注实际消费，其他对象/模板绑定待完成'],[41,'ExecutionPlan','实际调用DAG/方法别名执行，正式AtomicCapability/implementation实体登记待完成'],[42,'ObjectMap','32个实际原生对象，逻辑/后端ID、shape/name、来源和call引用，单对象修订ID保持'],[43,'RenderArtifact','实际PDF/PNG含hash/version/DPI；其他渲染边界未完成']]){
 if(objects.getRange(`A${r}`).values[0][0]!==id)throw Error('object row mismatch');
 objects.getRange(`J${r}`).values=[[note+'；contracts/deck-execution.schema.json；validation/generation-artifacts/']];
}
w.recalculate();await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/matrix-after-generation.xlsx`);
const preview=await w.render({sheetName:'需求主表',range:'N195:P195',scale:1});
await fs.writeFile(`${tmp}/generation-matrix-preview.png`,new Uint8Array(await preview.arrayBuffer()));
console.log('Generation SYS subset in progress; AC partial execution not passed.');
