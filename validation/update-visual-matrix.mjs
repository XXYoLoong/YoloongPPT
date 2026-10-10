import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const root='F:/YoloongPPT',tmp='F:/YoloongPPT-Temp-P01-05';
const original=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`,before=`${tmp}/matrix-before-visual.xlsx`,after=`${tmp}/matrix-after-visual.xlsx`;
const digest=raw=>crypto.createHash('sha256').update(raw).digest('hex');
try{await fs.copyFile(original,before,fs.constants.COPYFILE_EXCL);}catch(error){if(error.code!=='EEXIST')throw error;}
const sourceHash=digest(await fs.readFile(before)),currentHash=digest(await fs.readFile(original));
if(currentHash!==sourceHash){let knownAfter=null;try{knownAfter=digest(await fs.readFile(after));}catch{}if(currentHash!==knownAfter)throw Error('Original workbook changed after this work package baseline; do not overwrite another edit.');}
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(before));
await fs.writeFile(`${tmp}/visual-matrix-before.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'N91:P93',scale:1,format:'png'})).arrayBuffer()));
if(process.argv.includes('--preview-only')){console.log(JSON.stringify({readOnlyPreview:true,baselineSha256:sourceHash,preview:`${tmp}/visual-matrix-before.png`}));process.exit(0);}

const recovery=JSON.parse(await fs.readFile(`${root}/runtime/data/visual-live-validation/recovery-result.json`,'utf8'));
if(recovery.result?.run_id!=='39a2dbf3-c19b-4da2-99a6-27fe7b82ef7a'||recovery.job?.state!=='succeeded'||recovery.result?.qa?.p0_issue_count!==0||recovery.result?.completion?.system_acceptance!=='not_passed')throw Error('Actual QA-only recovery evidence is missing or inconsistent.');
const evidenceReports=[
 ['validation/visual-runtime.json','historical visual node/module',50],
 ['validation/visual-path-guards.json','incremental sensitive paths/symlinks',23],
 ['validation/layout-stage-artifacts/layout-stages.json','native layout stages at recorded source version',46],
 ['validation/visual-execution-artifacts/visual-execution.json','native component execution at recorded source version',23],
 ['validation/quality-stage-artifacts/quality-stage-runtime.json','historical quality rules/policy',38],
 ['validation/revision-plan-artifacts/quality-design-variation.json','incremental declared design variation',3],
 ['validation/quality-stage-artifacts/quality-asset-note-runtime.json','incremental image metadata namespace',4],
 ['validation/revision-plan-artifacts/revision-plan-execution.json','actual bounded RevisionPlan consumer',24]
];
const reports=[];
for(const [path,scope,count] of evidenceReports){const raw=await fs.readFile(`${root}/${path}`),r=JSON.parse(raw);const observed=r.check_count??(Array.isArray(r.checks)?r.checks.length:r.passed);if(observed!==count||!(r.ok===true||r.passed===true||typeof r.passed==='number'&&r.passed>0))throw Error(`Evidence mismatch: ${path}`);reports.push({path,scope,check_count:count,report_sha256:digest(raw),source_hashes:r.source_hashes??null,schema_hashes:r.schema_hashes??null});}
const recoveryChecks=JSON.parse(await fs.readFile(`${root}/runtime/data/visual-live-validation/recovery-checks.json`,'utf8'));
const repeated=JSON.parse(await fs.readFile(`${root}/runtime/data/visual-live-validation/repeat-recovery.json`,'utf8'));
if(recoveryChecks.length!==19||!recoveryChecks.every(check=>check.passed===true)||repeated.count!==10||repeated.run_id!=='95bdc3f0-0d60-46b7-a8ce-418d3962e49c'||!repeated.checks.every(check=>check.passed===true))throw Error('Actual recovery/interface/repeat checks missing.');
for(const file of await fs.readdir(`${root}/validation/visual-live-artifacts/checks`)){
 const path=`validation/visual-live-artifacts/checks/${file}`,raw=await fs.readFile(`${root}/${path}`),record=JSON.parse(raw);
 reports.push({path,scope:Array.isArray(record)?'actual first QA-only recovery and HTTP/CLI/MCP interfaces':'repeat QA-only immutable-checkpoint boundary',check_count:Array.isArray(record)?record.length:record.count,report_sha256:digest(raw),source_hashes:record.source_hashes??null,source_sha256:record.source_sha256??null});
}
const allowed=[],notes={};
function locate(name,id){const rows=w.worksheets.getItem(name).getRange('A1:A500').values;const row=rows.findIndex(values=>values[0]===id)+1;if(!row)throw Error(`Missing original ${name} ${id}`);return row;}
function maybeLocate(name,id){const rows=w.worksheets.getItem(name).getRange('A1:A500').values;return rows.findIndex(values=>values[0]===id)+1;}
function set(sheet,range,values){w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});}
function group(ids,note,evidence){for(const id of ids)notes[id]={note,evidence};}
const live='validation/visual-live-artifacts/';
const visual='validation/visual-runtime.json；validation/visual-path-guards.json；'+live;
const layout='validation/layout-stage-artifacts/；validation/visual-execution-artifacts/；'+live;
const quality='validation/quality-stage-artifacts/；validation/revision-plan-artifacts/quality-design-variation.json；'+live;
const revision='validation/revision-plan-artifacts/；'+live;
const unpassed='完整原验收仍未通过。';
group(['DEC-022'],'真实模型消费文本/图文/表/图表/流程选择，原生执行并保留依据。完整矩阵/信息图等范围未完成。'+unpassed,visual);
group(['DEC-023'],'图片数量及信息/装饰角色进入实际规划，缺失图显式失败。信息价值/全语义相关性待验收。'+unpassed,visual);
group(['DEC-024'],'模型仅选登记asset_id，解析真实文件/hash/许可授权，保留原模型声明。在线检索/生成服务未验收。'+unpassed,visual);
group(['DEC-025'],'真实结构化表格行列检查及原生写入，未补齐/裁剪数据。强调字段/分页/必要性完整验收待补。'+unpassed,visual);
group(['DEC-026'],'bar/column/line原生数据消费并检查维度。area/pie/scatter及完整分析目的策略未完成。'+unpassed,visual);
group(['DEC-027'],'已批准原文节点和明示顺序箭头进入原生形状/连接线。拒绝词法猜测因果，完整七类关系图语义待补。'+unpassed,visual);
group(['DEC-028'],'实际登记/检索模板族，生成继承真实母版/布局/主题，尺寸不符显式拒绝。品牌锁和全部模板验收待补。'+unpassed,visual);
group(['DEC-029'],'真实模型及writer消费字体/色板/背景/形状语言，保留来源与默认值。完整效果/设计tokens未验收。'+unpassed,visual);
group(['DEC-030','DEC-031'],'原生文本/图/关系图候选、实际容量、后端支持与多样性评分已接生成，46项直接版式检查。完整语义/品牌/多后端待验收。'+unpassed,layout);
group(['DEC-032','DEC-033'],'真实内容/图片/关系节点绑定稳定槽位，原生几何与连接端点进入对象DAG。任意模板绑定/freeform等仍未完整。'+unpassed,layout);
group(['DEC-034'],'CJK字形/字号/边距/容量实测；不靠截字或不可读缩字过关。RTL与全部字体替代链待补。'+unpassed,layout);
group(['DEC-035'],'填充/描边/背景/对比及声明设计变化实际消费。渐变/阴影/透明度等完整效果待补。'+unpassed,layout+'；'+quality);
group(['DEC-036'],'原生图片contain/显式适配策略、尺寸/hash进入执行与QA。人脸/主体感知裁切/mask等全范围待验收。'+unpassed,layout);
group(['DEC-037'],'实际备注进入原生notes；动画/切换不支持时显式报告，未当作交付。完整演示增强待补。'+unpassed,layout);
group(['DEC-038'],'已消费能力登记与PP-05实际原子DAG预执行，缺口结构化失败。九路线动态选择/模板round-trip全验收待补。'+unpassed,layout);
group(['DEC-039'],'质量问题映射RevisionPlan及fail/输入需求，原生局部布局/样式修订真实执行，未修改part保持。全部节点重跑未完成。'+unpassed,quality+'；'+revision);
group(['DEC-040'],'真实六页QA-only恢复P0=0保留4警告，19项接口/恢复与10项重复恢复各自记录；轨迹齐全仍warning/not_passed，不是40节点原验收完成。',quality+'；'+live);
group(['SYS-008'],'持久登记真实模板文件、来源/license/hash、母版/布局/主题、tokens和结构预览；生成已实际消费。渲染预览/全模板规则待验收。',visual);
group(['SYS-009'],'已解析真实图片/hash/像素/MIME/许可与显式授权，真实生成消费；敏感文件/越界链接拒绝。全部来源/质量语义待补。',visual);
group(['SYS-010','SYS-011','SYS-012'],'生成将实际图片及流程节点/边转统一规格、槽位、原子DAG/ObjectMap，23项组件直接执行。全部对象/后端/能力门控待补。',layout);
group(['SYS-013'],'真实六页包含原生图片和可编辑流程，消费模板继承与跨页DAG。全部母版/布局/既有文件修改路线待验收。',layout);
group(['SYS-014'],'六页PPTX实际LibreOffice PDF/PNG/hash渲染，QA-only恢复保持文件/渲染字节。live截图/全部renderer待补。',layout+'；'+live);
group(['SYS-015'],'结构/视觉几何/图片DPI/可访问性/一致性与真实模型复审运行。50/23/46/23/38及增量3/4各有版本，未汇称全套重跑。完整QA待补。',quality+'；'+live);
group(['SYS-016','REV-006','REV-010'],'RevisionPlan几何/样式消费者24项实际检查，局部修改保留非目标part、锁与before/after/QA/history；完整任意节点/对象修订未完成。',revision);
group(['TPL-001','TPL-005'],'真实模板注册、源文件/hash/license、母版/布局/主题tokens进入生成；未知容量/字体许可保留未知，完整tokens与三上游验收待补。',visual);
group(['TPL-007','TPL-011','TPL-012','TPL-013'],'原生布局语法/容量/分配/多样性实际编译图片及关系图，不裁正文。全部槽位类型、自适应拆合及三上游模板验收待补。',layout);
group(['AST-001','AST-003','AST-004','AST-011'],'实际登记素材来源、hash/像素/MIME/授权/unknownlicense及重复候选，画像选择进入PPTX。未知许可不当作已授权版权；全类型/语义重复待补。',visual);
group(['AST-005','AST-006'],'真实图片DPI/像素和角色区分、低质量警告保留；模型图片/文案复审已执行。水印/压缩/主体和完整语义相关性待补。',visual+'；'+quality);
group(['AST-007'],'真实图片contain/显式焦点适配已接布局、裁切结果进入原生写入/渲染。人脸/对象感知裁切及全原验收待补。',layout);
group(['AST-012'],'本地实际字节/hash/MIME核验和原子缓存运行；远程HTTPS/public-IP/redirect限制已编码但公开下载/重试原验收未执行。',visual);
group(['AST-014'],'已批准节点/明示关系变为可编辑原生shape/connector，并保留evidence_quote；全图类型/布局/语义验收待补。',layout+'；'+visual);
group(['PPT-011','PPT-012','PPT-014','PPT-029','PPT-030'],'主生成DAG实际创建shape/connector/图片，stable ObjectMap/元数据/alt-text与渲染证据保存；PP-05部分能力，不代替全部CRUD/路线验收。',layout+'；'+quality);
group(['QA-001','QA-003','QA-004','QA-005','QA-006','QA-008','QA-009','QA-010','QA-015','QA-016','QA-018','QA-019','QA-020'],'部分原生结构、边界/碰撞/溢出、层级/对比/DPI、一致性/可访问性规则与DEC039/040实跑。历史38项和设计变化3/尺寸4分别保留；完整原QA验收未通过。',quality+'；'+live);
group(['QA-011','QA-012','QA-013','QA-014'],'实际表/图数据数值引用核验及真实模型视觉/事实复审，六页QA-only保留审查警告。语义真值、全部图表/表格与完整正负样例待补。',quality+'；'+live);
group(['QA-017'],'实际局部RevisionPlan保留非目标ZIP成员/对象，before/after specs、hash及QA保存；全部未知部件/模式round-trip原验收未完成。',revision);
group(['SEC-001'],'素材/模板读取前拒绝secrets/.git/.ssh/.env及实际链接越界，23项真实路径guard通过；全部用户/输出/执行路径安全原验收仍待补。','validation/visual-path-guards.json；validation/视觉决策与真实素材.md');
group(['GOV-008'],'真实六页可编辑PPTX/渲染/QA-only恢复P0=0，原生RevisionPlan局部修订实物运行。4警告及完整QA/所有P0 AC仍未通过，系统非完成。',live+'；'+revision);

for(const [id,{note,evidence}] of Object.entries(notes)){
 const row=locate('需求主表',id),tr=locate('可执行任务',`TASK-${id}`);
 if(w.worksheets.getItem('需求主表').getRange(`N${row}`).values[0][0]==='已完成')throw Error(`Refuse completed downgrade ${id}`);
 set('需求主表',`N${row}:P${row}`,[['进行中',evidence,note]]);set('可执行任务',`L${tr}:M${tr}`,[['进行中',evidence+' '+note]]);
 const vr=maybeLocate('可执行任务',`VERIFY-${id}`);if(vr){if(w.worksheets.getItem('可执行任务').getRange(`L${vr}`).values[0][0]==='已完成')throw Error(`Refuse completed VERIFY downgrade ${id}`);set('可执行任务',`L${vr}:M${vr}`,[['进行中',evidence+' 本版直接/历史证据范围分别记录，完整原验收待补。']]);}
 if(id.startsWith('DEC-')){const dr=locate('决策链',id);set('决策链',`M${dr}:N${dr}`,[['进行中',evidence+' '+note]]);}
 if(id.startsWith('SYS-')){const sr=locate('系统组件接口',id);set('系统组件接口',`H${sr}:I${sr}`,[['进行中',evidence+' '+note]]);}
 if(id.startsWith('SEC-')){const sr=locate('非功能与安全',id);set('非功能与安全',`H${sr}:I${sr}`,[['进行中',evidence+' '+note]]);}
}
for(const [prefix,name] of [['TPL','模板版式要求'],['AST','素材与可视化']]){
 const s=w.worksheets.getItem(name),header=s.getRange('A1:P1').values[0],index=header.findIndex(value=>typeof value==='string'&&value.includes('状态'));
 if(index<0)throw Error(`No original status header ${name}`);
 for(const [id,{note,evidence}] of Object.entries(notes))if(id.startsWith(prefix+'-')){const row=locate(name,id);set(name,`${String.fromCharCode(65+index)}${row}:${String.fromCharCode(66+index)}${row}`,[['进行中',evidence+' '+note]]);}
}
for(const id of ['PPT-011','PPT-012','PPT-014','PPT-029','PPT-030']){const row=locate('PowerPoint对象矩阵',id);set('PowerPoint对象矩阵',`I${row}:I${row}`,[['Partial：主生成与RevisionPlan实际消费原生图片/shape/connector/ObjectMap；全部CRUD及该能力全范围未通过。']]);set('PowerPoint对象矩阵',`P${row}:P${row}`,[[notes[id].evidence]]);}

const flowNotes={
 S03:'新增素材/模板敏感路径和真实链接越界guard。全类型/密码/宏/输出权限原验收待补。',
 S10:'只消费已批准原文明示节点与箭头，原生流程可编辑。完整内容关系抽取/因果证明及全图类型待补。',
 S18:'DEC022–029实际选择文本/图/表/图表/流程，语义价值全验收待补。',
 S19:'真实图片asset_id/文件/hash/许可与授权进入主生成；在线检索/生成服务未验收。',
 S20:'真实模板文件及母版/布局/主题/styles解析进入生成；全部tokens/品牌锁待补。',
 S21:'模板注册与候选查询已消费，尺寸冲突失败，未静默默认替换；完整容量/跨模板评分待补。',
 S22:'文本、数据、图片和流程实际候选/后端能力/容量检查；全类型/多后端待补。',
 S23:'实际容量/层级/变化评分与trace；完整语义/品牌评分待补。',
 S24:'稳定原生槽位绑定图片/节点/边；任意模板字段和全槽位待补。',
 S25:'原生几何/节点/连接端点计算，真实写入渲染；freeform及所有关系布局待补。',
 S26:'字体/填充/描边/背景与声明设计变化进入实际执行；全效果待补。',
 S27:'实际notes执行；动画/切换未支持显式报告，完整增强待补。',
 S28:'图片与流程的统一spec实际消费；全对象/模板/绑定验收待补。',
 S29:'素材hash/权限、字体、schema、容量和原子能力检查；所有路径与后端缺口待补。',
 S30:'当前PP-05原子实现已选择，九路线动态选择原验收待补。',
 S31:'图片/shape/connector进入真实DAG及ObjectMap；全部对象复杂依赖待补。',
 S32:'真实六页原生图片/流程PPTX与局部RevisionPlan已保存；全部模式和保真待补。',
 S33:'实际PDF/逐页PNG/hash版本保存，QA-only复用字节；live/全部缩略图待补。',
 S34:'部分原生结构/边界/空对象/碰撞/溢出检查运行；完整结构验收待补。',
 S35:'实际模型视觉复审与层级/对比/DPI/一致性规则，警告保留；全规则待补。',
 S36:'数值引用与真实模型事实复审，图片尺寸仅对同页实际hash/像素验证后排除元数据；完整语义真值待补。',
 S37:'原生图片/节点/边可编辑，局部非目标parts保持；全对象round-trip待补。',
 S38:'已检查原生alt-text/阅读顺序/字号/对比/表头部分字段，语言/RTL与完整可访问性待补。',
 S39:'DEC039将实际issue映射局部RevisionPlan/fail/needs_input；全部节点修订待补。',
 S40:'24项RevisionPlan消费者检查，真实布局/颜色局部修改和QA/history；任意节点/对象待补。',
 S41:'六页QA-only P0=0但保留4警告，终止warning/not_passed；没有把DEC轨迹齐全当作完整验收。',
 S42:'PPTX/PDF/PNG/manifest/trace/QA实物导出；最终系统验收门控尚未通过。',
 S43:'素材/模板来源/hash/许可/unknown状态及模型版本保存；全来源合并许可清单待补。',
 S44:'六页可编辑原生对象与真实渲染已检查，本版PowerPoint实际打开/全部交付原验收未完成。'
};
for(const [id,note] of Object.entries(flowNotes)){const row=locate('0-1全链路',id);set('0-1全链路',`G${row}:I${row}`,[['进行中',live+'；'+layout+'；'+quality+'；'+revision,note]]);}
for(const id of ['AC-001','AC-027','AC-030']){const row=locate('验收矩阵',id);set('验收矩阵',`G${row}:J${row}`,[['部分执行/未通过','真实六页主模型/PPTX/图片/流程/渲染与QA-only恢复。P0=0保留4警告，原生局部RevisionPlan执行；完整原验收未满足。',live+'；'+revision,'完整原验收未通过']]);}

w.recalculate();
const inspection=await w.inspect({kind:'table',range:'总览!A5:F21',include:'values,formulas',tableMaxRows:17,tableMaxCols:6,maxChars:2500});
await fs.writeFile(`${tmp}/visual-overview-inspection.ndjson`,inspection.ndjson);
const errors=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'changed status dependencies formula scan'});
await fs.writeFile(`${tmp}/visual-formula-errors.ndjson`,errors.ndjson);
await fs.writeFile(`${tmp}/visual-matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/visual-matrix-evidence.json`,JSON.stringify({baseline_sha256:sourceHash,reports,recovery_run_id:recovery.result.run_id,repeat_recovery_run_id:repeated.run_id,parent_generated_run_id:recovery.result.parent_run_id,actual_qa:recovery.result.qa,completion:recovery.result.completion,requirement_ids:Object.keys(notes)},null,2));
await fs.writeFile(`${tmp}/visual-matrix-after.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'N91:P93',scale:1,format:'png'})).arrayBuffer()));
await fs.writeFile(`${tmp}/visual-matrix-overview.png`,new Uint8Array(await(await w.render({sheetName:'总览',range:'A5:F21',scale:1,format:'png'})).arrayBuffer()));
await(await SpreadsheetFile.exportXlsx(w)).save(after);
console.log(JSON.stringify({requirements:Object.keys(notes).length,approvedRanges:allowed.length,recoveryRunId:recovery.result.run_id,output:after}));
