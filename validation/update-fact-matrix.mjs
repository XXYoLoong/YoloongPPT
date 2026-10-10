import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT',tmp='F:/YoloongPPT-Temp-P01-05',base=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`;
const node=JSON.parse(await fs.readFile(`${root}/validation/fact-runtime.json`,'utf8')),live=JSON.parse(await fs.readFile(`${root}/validation/fact-integration.json`,'utf8'));
if(!node.passed||node.cases.length!==35||!live.passed||live.cases.length!==16)throw Error('actual node and pipeline evidence required');
try{await fs.copyFile(base,`${tmp}/matrix-before-fact.xlsx`,fs.constants.COPYFILE_EXCL);}catch(e){if(e.code!=='EEXIST')throw e;}
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(`${tmp}/matrix-before-fact.xlsx`)),allowed=[];
function locate(sheet,id){const s=w.worksheets.getItem(sheet),rows=s.getRange('A1:A500').values,index=rows.findIndex(r=>r[0]===id);if(index<0)throw Error(`missing ${sheet} ${id}`);return index+1;}
function set(sheet,range,values){w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});}
const evidence='validation/fact-runtime.json；validation/fact-integration.json；validation/fact-project-map.json；validation/fact-artifacts/；validation/来源冲突与事实边界.md';
for(const [id,status,note] of [
 ['DEC-004','已完成','实际SourceEvidence逐来源校验后生成候选；用户选定或来源优先级决定冲突，无唯一选择时unresolved并阻断。独立CLI/API、规则/轨迹、三正常及边界、五项目固定源码对应齐备；真实生成和修订消费已选值。'],
 ['DEC-005','已完成','事实直接使用、显式假设、精确推算、placeholder及询问/失败已运行；假设稳定ID及可见标记，未决阻断。独立入口、原FactConstraintSet/Assumption校验、候选/轨迹、正常边界和五项目对应齐备。'],
 ['CNT-001','进行中','真实模型解释逐字锚定数值/范围，原事实约束实际消费；保留主体/动词上下文，拒绝臆造范围。全部格式、语义抽取完整性及全部事实改写验收待完成。'],
 ['CNT-003','进行中','8%/9%真实冲突全部保留；明确优先级选8%，无策略阻断，生成与修订不采用9%。全格式语义冲突/合并与系统验收待完成。'],
 ['CNT-004','进行中','假设/精确推算/占位/询问/失败实际执行并注册；生成及QA消费假设引用和可见标记。完整自动缺失识别及全链路验收待完成。'],
 ['IN-014','进行中','真实多源ID/哈希去重候选及来源优先级/冲突规则实际执行，完整原文保留。全输入格式及完整语义冲突范围待完成。'],
 ['SYS-005','进行中','前五决策节点及事实解释阶段恢复实际运行；真实失败断点复用解释，源身份/hash变化阻断，主模型和复审新调用。其余35节点/条件分支及完整恢复待完成。'],
 ['SYS-015','进行中','生成/QA用已选事实投影；UUID元数据与明确否决值备注分开检查，事实/假设/占位边界参与检查。真实四页P0=0，完整质量及AC待完成。'],
 ['SYS-016','进行中','单文本修订沿用已选事实及冲突轨迹，快照缺失/hash变化或被否决数值在写入前阻断；实际单part修订和复审已运行。完整修订计划/对象/原验收待完成。'],
 ['SYS-019','进行中','增加resolve-evidence与fact-boundaries独立命令，输入/候选/规则/输出落盘；完整CLI生命周期/基准待完成。'],
 ['SYS-020','进行中','增加两事实决策API并由生成/修订消费；原HTTP错误/trace一致，完整作业/取消/重试待完成。'],
 ['SYS-022','进行中','前五节点独立入口和实际失败/恢复轨迹齐备；全部节点、能力、布局、后端与规则调试待完成。'],
 ['OBS-003','进行中','前五节点保存候选/选择/原来源/约束/hash/输出/时长/错误；完整节点与全部对象关联待完成。'],
 ['TST-003','进行中','前五节点正常/边界及真实链路已执行，事实工作包35节点检查+16实物检查；其余35节点及完整回归范围待完成。']]){
 const row=locate('需求主表',id),tr=locate('可执行任务',`TASK-${id}`);
 set('需求主表',`N${row}:P${row}`,[[status,evidence,note]]);set('可执行任务',`L${tr}:M${tr}`,[[status,note+' '+evidence]]);
 if(id.startsWith('DEC-')){const vr=locate('可执行任务',`VERIFY-${id}`),dr=locate('决策链',id);set('可执行任务',`L${vr}:M${vr}`,[['已完成','三正常以上、边界/冲突、独立入口及完整候选轨迹通过；实际生成/修订及初次失败保留，五项目partial/not_found明确。 '+evidence]]);set('决策链',`M${dr}:N${dr}`,[[status,note+' '+evidence]]);w.worksheets.getItem('需求主表').getRange(`A${row}:P${row}`).format.rowHeightPx=260;}
 if(id.startsWith('SYS-')){const sr=locate('系统组件接口',id);set('系统组件接口',`H${sr}:I${sr}`,[[status,note+' '+evidence]]);}
}
for(const name of ['SourceEvidence','EvidenceConflict','FactConstraintSet','Assumption','DecisionCandidate','DecisionTrace']){const row=locate('数据对象',name);set('数据对象',`I${row}:J${row}`,[['进行中','前五节点实际消费原对象及来源锚点；冲突、已选值、稳定假设与边界保留，完整格式/节点/语义范围待完成。 '+evidence]]);}
for(const [id,note] of [['S06','来源ID/哈希、用户优先级及冲突候选真实执行，未决阻断；全格式及完整语义冲突待完成。'],['S08','真实FactConstraintSet、显式假设/精确推算/占位/询问及可引用边界运行；自动事实抽取完整性及全格式待完成。'],['S36','实际已选值/假设可见性/否决值/数值与备注检查，独立真实视觉事实复审；完整语义真值及全图像对应待完成。'],['S39','真实失败断点恢复事实解释及内容规划，新主模型/复审；单文本修改保持已选事实和单part范围，完整修订计划待完成。']]){const row=locate('0-1全链路',id);set('0-1全链路',`G${row}:H${row}`,[['进行中',note+' '+evidence]]);}
const obs=locate('非功能与安全','OBS-003');set('非功能与安全',`H${obs}:I${obs}`,[['进行中','前五节点完整轨迹已消费，全节点和全部对象关联待完成。 '+evidence]]);
for(const id of ['AC-001','AC-027']){const row=locate('验收矩阵',id);set('验收矩阵',`G${row}:J${row}`,[['部分执行/未通过','前五节点真实生成/已选事实单对象修订，已执行P0=0；完整DEC/对象/QA/系统验收未满足。',evidence,'系统原验收全部条件未完成']]);}
await fs.writeFile(`${tmp}/fact-matrix-allowed.json`,JSON.stringify(allowed));
w.worksheets.getItem('需求主表').getRange('P1:P309').format.columnWidthPx=420;
w.worksheets.getItem('需求主表').getRange('A73:P74').format.rowHeightPx=330;
await fs.writeFile(`${tmp}/fact-matrix-preview.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'N73:P74',scale:1.1,format:'png'})).arrayBuffer()));
await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/matrix-after-fact.xlsx`);console.log('fact matrix exported; original scope and dependencies retained');
