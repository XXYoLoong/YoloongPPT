import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT',tmp='F:/YoloongPPT-Temp-P01-05',base=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`;
const report=JSON.parse(await fs.readFile(`${root}/validation/route-runtime.json`,'utf8'));
if(!report.passed||report.cases.length!==39)throw Error('39 current checks required');
try{await fs.copyFile(base,`${tmp}/matrix-before-route.xlsx`,fs.constants.COPYFILE_EXCL);}catch(e){if(e.code!=='EEXIST')throw e;}
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base));
const allowed=[];
function locate(sheet,id){
 const s=w.worksheets.getItem(sheet),rows=s.getRange('A1:A500').values;
 const index=rows.findIndex(r=>r[0]===id);
 if(index<0)throw Error(`missing ${sheet} ${id}`);
 return [s,index+1];
}
function set(sheet,range,values){const s=w.worksheets.getItem(sheet);s.getRange(range).values=values;allowed.push({sheet,range});}
const ids=[['DEC-001','已完成','八种模式与十个边界实际运行；输入、候选、规则、输出、约束、回退、轨迹及五项目对应齐备。39项核验和真实生成通过。'],
 ['SYS-002','进行中','实际本地平台/精确写入依赖/字体/渲染探测由路由消费；Office/API set/MCP/远端模型完整探测待完成。'],
 ['SYS-005','进行中','DEC-001已实际执行并保存候选/错误/轨迹；DEC-002–040、条件分支及节点级恢复仍待完成。'],
 ['SYS-007','进行中','五项原生能力/实现稳定实体登记，输入输出/平台/依赖/优先级/health；planner/writer真实消费，全部对象×后端待扩展。'],
 ['SYS-011','进行中','DAG绑定登记capability_id/implementation_id，实际检查输入与错配ID；完整后端预执行/缺口判定仍待完成。'],
 ['SYS-012','进行中','五项登记能力实际写入并核对输入/输出，真实ObjectMap/调用；完整对象及失败恢复范围待完成。'],
 ['SYS-019','进行中','CLI新增route独立节点并保存trace；完整CLI生命周期/bench/debug等范围仍待完成。'],
 ['SYS-020','进行中','HTTP /route独立节点与/generate实际消费；完整jobs/取消/重试范围仍待完成。'],
 ['SYS-022','进行中','DEC-001独立CLI/API已运行、trace落盘并经真实生成；任意节点/能力/layout/adapter/QARule调试范围待完成。'],
 ['OBS-003','进行中','DEC-001保存input/candidates/score/reason/selected/rules/output/duration/error；最终对象关联该节点，其余39节点待完成。'],
 ['TST-003','进行中','DEC-001八常规+十边界自动结果和真实链路已保留；DEC-002–040各3+1仍待完成。'],
 ['GOV-002','进行中','八模式运行时判定/保护策略均有测试；除新建子集外的完整后续流程尚未交付。'],
 ['GOV-007','进行中','实际DAG原子能力及实现ID已稳定登记；shape到source/spec/call/DEC-001可追溯，全部对象/决策尚未完成。']];
for(const [id,status,note] of ids){
 const [r,rr]=locate('需求主表',id),[t,tr]=locate('可执行任务',`TASK-${id}`);
 set('需求主表',`N${rr}:P${rr}`,[[status,'validation/route-runtime.json；validation/route-artifacts/；validation/模式路由与能力登记.md',note]]);
 set('可执行任务',`L${tr}:M${tr}`,[[status,note+' 证据：validation/route-runtime.json']]);
 r.getRange(`A${rr}:P${rr}`).format.rowHeightPx=230;
 if(id.startsWith('SYS-')){const [s,sr]=locate('系统组件接口',id);set('系统组件接口',`H${sr}:I${sr}`,[[status,note+' validation/route-artifacts/']]);}
}
const [verify,vr]=locate('可执行任务','VERIFY-DEC-001');set('可执行任务',`L${vr}:M${vr}`,[['已完成','39项实际检查含八模式/十边界及真实HTTP对象关联，validation/route-runtime.json；失败/澄清轨迹保留。']]);
set('决策链','M2:N2',[['已完成','src/yoloongppt/routing.py；validation/route-runtime.json；validation/route-project-map.json；validation/route-artifacts/decision-route.json']]);
for(const name of ['RawTaskRequest','RuntimeCapabilitySnapshot','AtomicCapability','CapabilityImplementation','DecisionCandidate','DecisionTrace']){
 const [s,row]=locate('数据对象',name);
 set('数据对象',`I${row}:J${row}`,[['进行中','当前DEC-001/五项能力契约已实际消费、落盘；其他节点/能力/完整探测继续，见validation/模式路由与能力登记.md']]);
}
const [nf,nfr]=locate('非功能与安全','OBS-003');set('非功能与安全',`H${nfr}:I${nfr}`,[['进行中','DEC-001实际DecisionTrace与最终对象关联；其他39节点仍待完成，validation/route-runtime.json']]);
for(const [id,note] of [['AC-001','真实新请求10页PPTX/渲染/QA P0=0并经过DEC-001；其余39节点及全部原QA/AC条件待完成。'],['AC-027','本次所有原生对象关联source/evidence/spec/call/DEC-001；完整决策链及全对象随机抽检未完成。']]){
 const [s,row]=locate('验收矩阵',id);set('验收矩阵',`G${row}:J${row}`,[['部分执行/未通过',note,'validation/route-artifacts/；validation/route-runtime.json','完整DEC/QA/全范围未完成']]);
}
await fs.writeFile(`${tmp}/route-matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/route-matrix-preview.png`,new Uint8Array(await (await w.render({sheetName:'需求主表',range:'N70:P70',scale:1.4,format:'png'})).arrayBuffer()));
const out=await SpreadsheetFile.exportXlsx(w);await out.save(`${tmp}/matrix-after-route.xlsx`);
console.log('route matrix exported; baseline scope unchanged');
