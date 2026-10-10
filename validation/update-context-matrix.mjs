import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT',tmp='F:/YoloongPPT-Temp-P01-05',base=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`;
const report=JSON.parse(await fs.readFile(`${root}/validation/context-runtime.json`,'utf8'));
if(!report.passed||report.cases.length!==40)throw Error('40 current checks required');
try{await fs.copyFile(base,`${tmp}/matrix-before-context.xlsx`,fs.constants.COPYFILE_EXCL);}catch(e){if(e.code!=='EEXIST')throw e;}
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base));
const allowed=[];
function locate(sheet,id){
 const s=w.worksheets.getItem(sheet),rows=s.getRange('A1:A500').values;
 const index=rows.findIndex(r=>r[0]===id);
 if(index<0)throw Error(`missing ${sheet} ${id}`);
 return [s,index+1];
}
function set(sheet,range,values){w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});}
const evidence='validation/context-runtime.json；validation/context-artifacts/；validation/约束归一化与来源分流.md';
const ids=[
 ['DEC-002','已完成','硬约束、偏好与默认值实际归一化；同级冲突阻断，原输出要求保留。独立入口、候选、规则、轨迹和五项目对应齐备，八页偏好真实消费。'],
 ['DEC-003','已完成','真实来源身份绑定六类角色，全量快照保留；模型与质量检查只用事实集合，风格测试数字未进入事实输入。正常及冲突样例、独立入口和五项目对应齐备。'],
 ['GOV-003','进行中','硬约束、偏好、默认值已由决策节点实际处理，冲突和输出缺口阻断，降级保留原因；原文规则有界，完整自然语言约束处理仍待实现。'],
 ['SYS-003','进行中','实际解析来源后绑定角色与资产身份，保留完整原文和独立事实快照；完整输入格式与统一加载范围待完成。'],
 ['SYS-005','进行中','前三决策节点独立及真实生成运行，候选与错误轨迹落盘；其余三十七节点、条件分支和节点恢复待完成。'],
 ['SYS-011','进行中','预执行消费归一化约束及输出要求，能力登记仍实际绑定；完整后端预执行和能力缺口范围待完成。'],
 ['SYS-015','进行中','模型事实输入和质量检查使用已判定事实集合，实际八页渲染复审；完整视觉、事实、结构规则仍待完成。'],
 ['SYS-016','进行中','修订与复查沿用事实快照，缺失或污染阻断；既有单文本修订回归通过，完整修订计划及对象范围待完成。'],
 ['SYS-019','进行中','新增约束与来源角色独立命令并保存轨迹；完整命令生命周期、基准与调试范围待完成。'],
 ['SYS-020','进行中','新增约束与来源角色独立接口，生成入口实际消费；完整作业、取消与重试范围待完成。'],
 ['SYS-022','进行中','前三节点独立入口、失败轨迹及真实链路齐备；任意节点、能力、布局、后端和质量规则调试待完成。'],
 ['OBS-003','进行中','前三节点保存输入、候选、选择、规则、输出、时长及错误；完整节点及对象到全部决策关联待完成。'],
 ['TST-003','进行中','前三节点各至少三个正常及一个边界样例已运行；其余三十七节点和完整回归范围待完成。']];
for(const [id,status,note] of ids){
 const [s,row]=locate('需求主表',id),[t,tr]=locate('可执行任务',`TASK-${id}`);
 set('需求主表',`N${row}:P${row}`,[[status,evidence,note]]);
 set('可执行任务',`L${tr}:M${tr}`,[[status,note+' '+evidence]]);
 if(id.startsWith('DEC-'))s.getRange(`A${row}:P${row}`).format.rowHeightPx=260;
 if(id.startsWith('SYS-')){const [ss,sr]=locate('系统组件接口',id);set('系统组件接口',`H${sr}:I${sr}`,[[status,note+' '+evidence]]);}
}
for(const id of ['DEC-002','DEC-003']){
 const [s,row]=locate('可执行任务',`VERIFY-${id}`);
 set('可执行任务',`L${row}:M${row}`,[['已完成','每节点至少三个正常与一个边界样例、独立入口、完整候选轨迹及真实生成通过；40项报告与五项目对应保留。 '+evidence]]);
 const [d,dr]=locate('决策链',id);set('决策链',`M${dr}:N${dr}`,[['已完成',evidence+'；validation/context-project-map.json']]);
}
for(const name of ['PresentationContext','DecisionCandidate','DecisionTrace']){
 const [s,row]=locate('数据对象',name);
 set('数据对象',`I${row}:J${row}`,[['进行中','当前三节点及来源角色/约束实际消费，完整来源格式与其余节点继续实现。 '+evidence]]);
}
const [nf,nfr]=locate('非功能与安全','OBS-003');set('非功能与安全',`H${nfr}:I${nfr}`,[['进行中','前三节点完整决策轨迹已运行，其余节点及全对象关联待完成。 '+evidence]]);
for(const [id,note] of [['AC-001','真实八页原生演示、渲染、已执行质量检查无最高优先级问题，经过前三节点；完整决策与质量验收仍未通过。'],['AC-027','三节点轨迹与来源角色保留；最终对象已关联来源、证据、规格、调用及模式节点，全部决策对象关联和随机抽检待完成。']]){
 const [s,row]=locate('验收矩阵',id);set('验收矩阵',`G${row}:J${row}`,[['部分执行/未通过',note,evidence,'完整决策、质量与全范围验收未完成']]);
}
await fs.writeFile(`${tmp}/context-matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/context-matrix-preview.png`,new Uint8Array(await (await w.render({sheetName:'需求主表',range:'N71:P72',scale:1.2,format:'png'})).arrayBuffer()));
const out=await SpreadsheetFile.exportXlsx(w);await out.save(`${tmp}/matrix-after-context.xlsx`);
console.log('context matrix exported; original scope retained');
