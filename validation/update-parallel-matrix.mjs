import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT',tmp='F:/YoloongPPT-Temp-P01-05';
const reports=['validation/narrative-runtime.json','validation/input-format-artifacts/input-formats-runtime.json','validation/native-object-artifacts/native-object-runtime.json','validation/parallel-integration.json','validation/job-lifecycle.json'];
for(const path of reports){const r=JSON.parse(await fs.readFile(`${root}/${path}`,'utf8'));if(!(r.passed||r.ok||r.status==='passed'))throw Error(`missing evidence ${path}`);}
try{await fs.copyFile(`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`,`${tmp}/matrix-before-parallel.xlsx`,fs.constants.COPYFILE_EXCL);}catch(e){if(e.code!=='EEXIST')throw e;}
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(`${tmp}/matrix-before-parallel.xlsx`)),allowed=[],notes={};
function locate(name,id){const rows=w.worksheets.getItem(name).getRange('A1:A500').values;const row=rows.findIndex(x=>x[0]===id)+1;if(row===0)throw Error(`${name} ${id}`);return row;}
function set(sheet,range,values){w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});}
function group(ids,note,evidence){for(const id of ids)notes[id]={note,evidence};}
group(Array.from({length:16},(_,i)=>`DEC-${String(i+6).padStart(3,'0')}`),'prepare/real model/finalize实际消费16节点：受众、场景、叙事候选、页/章预算、页意图、容量、正文/备注和引用位置；75项模块检查与真实8页生成通过。自动推断、语义关系、多级章节、时长换算、语义拆合及全部引用模式仍未完成，节点原完整验收保持进行中。','validation/narrative-runtime.json；validation/parallel-integration.json；validation/叙事决策并行实现.md');
group(['CNT-005','CNT-006','CNT-007','CNT-008','CNT-009','CNT-011','CNT-013'],'调用方受众/场景/风格进入真实模型，按候选故事线和页预算生成，整段容量移动保留原文及可见假设/来源/占位标记。自动语义推断、全部故事线/多级章节/改写原验收待完成。','validation/narrative-runtime.json；validation/parallel-integration.json');
group(['IN-003','IN-004','IN-006','IN-007','IN-008','IN-010','IN-011','IN-012','IN-015','IN-016'],'原生结构适配器已接SourceLoader/证据事务：DOCX/XLSX/CSV/PPTX/PDF/图像/JSON/XML，原字节、格式锚点、结构/警告保存，31项正常/边界通过；DOCX与文本实际生成。空结构/图片保留在nontext_evidence，不伪造OCR事实。DOCX物理页、PDF表格/扫描OCR、完整显示语义、YAML/路径选择/全资产类型待完成。','validation/input-format-artifacts/；validation/输入格式与原生模板实装.md；validation/parallel-integration.json；validation/job-lifecycle.json');
group(['TPL-001','TPL-002','TPL-003','TPL-004','TPL-005','TPL-009','TPL-014'],'真实解析母版/布局/主题/占位符/继承/尺寸，CLI/API/MCP入口可调用；真实原生文本槽位实例化且母版/布局/主题保持。容量/全部tokens/品牌锁/全部比例转换和三上游模板验收待完成，普通generate尚不替换自定义模板。','validation/input-format-artifacts/；validation/parallel-integration.json');
group(['AST-001','AST-004','AST-011'],'资产目录/图片像素、DPI、aspect、格式、alpha、ICC、主色与dHash已运行；完全哈希与感知重复仅候选，许可unknown显式保留。全部来源/类型、生成下载、语义相关性、重复授权/裁切及原验收待完成。','validation/input-format-artifacts/；validation/输入格式与原生模板实装.md');
group(['PPT-001','PPT-002','PPT-007','PPT-008','PPT-009','PPT-011','PPT-012','PPT-013','PPT-014','PPT-016','PPT-017','PPT-022','PPT-023','PPT-029','PPT-030'],'PP-05原生文字/形状/线/组/图片/表/图表实际创建，已有PPT可定向修改并保留未知部件/非目标形状；32项实物检查及CLI/API/MCP入口。能力清单逐CRUD/保真/渲染标partial/unsupported，不表示全部对象子能力或Office专属功能完成。','validation/native-object-artifacts/；validation/原生对象与既有PPT修订.md；validation/parallel-integration.json');
group(['REV-001','REV-002','REV-004','REV-005','REV-010'],'stable slide-id+shape-id索引、精确选择器、expected_sha256及save-as，修改文字/格式/位置/单元格/图表+内嵌工作簿/图片/替代文字/备注；未涉及ZIP成员byte相同、非目标形状XML相同。真实API修改已执行；完整自然语言范围、语义定位、所有部件语义、质量/历史原验收待完成。','validation/native-object-artifacts/；validation/parallel-integration.json');
group(['SYS-003','SYS-004','SYS-005','SYS-017','SYS-019','SYS-020','SYS-021','SYS-022'],'四模块已接统一CLI/API/MCP或生成主链路；持久化作业、create/status/artifacts/cancel/retry、独立节点调试与精确已有PPT编辑已执行。真实八页AI生成/渲染/QA P0=0；全部生命周期、任意节点/能力/布局调试、全部MCP链路和系统AC待完成。','validation/parallel-integration.json；validation/job-lifecycle.json；validation/并行核心功能集成.md');
group(['NFR-004'],'实际长解析作业独立进程组，运行中取消终止PID；队列取消、显式新ID重试、服务重启标interrupted而不重复模型请求已运行。模型/下载/渲染全部故障与性能/跨平台矩阵待完成。','validation/job-lifecycle.json');
group(['OBS-002','OBS-004','OBS-005','OBS-006','OBS-007','OBS-009'],'真实任务结构化事件、原子执行轨迹、供应商token/latency/request ID、产物hash清单及version manifest、保存运行结构差异入口已接入；已生成/修订实物保留。全类型/全链路关联、兼容重放、全部版本和比较原验收待完成。','validation/parallel-integration.json；validation/job-lifecycle.json；validation/parallel-artifacts/');
const special={'IN':'输入源矩阵','TPL':'模板版式要求','AST':'素材与可视化','SYS':'系统组件接口'};
for(const [id,{note,evidence}] of Object.entries(notes)){
 const row=locate('需求主表',id),tr=locate('可执行任务',`TASK-${id}`);
 if(w.worksheets.getItem('需求主表').getRange(`N${row}`).values[0][0]==='已完成')throw Error(`do not downgrade completed ${id}`);
 set('需求主表',`N${row}:P${row}`,[['进行中',evidence,note]]);set('可执行任务',`L${tr}:M${tr}`,[['进行中',note+' '+evidence]]);
 if(id.startsWith('DEC-')){const dr=locate('决策链',id),vr=locate('可执行任务',`VERIFY-${id}`);set('决策链',`M${dr}:N${dr}`,[['进行中',note+' '+evidence]]);set('可执行任务',`L${vr}:M${vr}`,[['进行中','模块正常/边界与真实模型消费已有证据；节点全部原验收尚未完成。 '+evidence]]);}
 if(id.startsWith('SYS-')){const sr=locate('系统组件接口',id);set('系统组件接口',`H${sr}:I${sr}`,[['进行中',note+' '+evidence]]);}
 if(id.startsWith('OBS-')||id.startsWith('NFR-')){const sr=locate('非功能与安全',id);set('非功能与安全',`H${sr}:I${sr}`,[['进行中',note+' '+evidence]]);}
}
// Source tables vary; retain their native status columns by locating header text.
for(const [prefix,name] of Object.entries(special)){
 if(prefix==='SYS')continue;
 const s=w.worksheets.getItem(name),header=s.getRange('A1:P1').values[0];
 const statusIndex=header.findIndex(x=>typeof x==='string'&&/状态/.test(x));
 if(statusIndex<0)continue;
 for(const [id,{note,evidence}] of Object.entries(notes))if(id.startsWith(prefix+'-')){
  const row=locate(name,id),col=String.fromCharCode(65+statusIndex),next=String.fromCharCode(66+statusIndex);
  set(name,`${col}${row}:${next}${row}`,[['进行中',note+' '+evidence]]);
 }
}
for(const id of ['S02','S03','S04','S05','S06','S08','S09','S10','S11','S12','S13','S14','S15','S16','S17','S18','S19','S20','S21','S26','S27','S28','S29','S39','S40','S41','S42','S43','S44']){
 const row=locate('0-1全链路',id);set('0-1全链路',`G${row}:H${row}`,[['进行中','并行核心模块已增加输入、叙事、模板、原生对象、精确编辑、任务及MCP入口；仅已执行子能力。剩余完整条件以原需求行和原验收为准，未通过不可标完成。 validation/并行核心功能集成.md']]);
}
for(const id of ['AC-001','AC-027','AC-030']){const row=locate('验收矩阵',id);set('验收矩阵',`G${row}:J${row}`,[['部分执行/未通过','真实八页多源生成+DEC1–21有界消费+作业/取消/MCP入口/已有PPT精确修改，P0=0；全决策/QA/模式/系统原条件未满足。','validation/parallel-integration.json；validation/job-lifecycle.json；validation/parallel-artifacts/','完整原验收未通过']]);}
const native=JSON.parse(await fs.readFile(`${root}/validation/native-object-artifacts/native-object-runtime.json`,'utf8'));
for(const item of native.capabilities.requirements){const row=locate('PowerPoint对象矩阵',item.requirement_id);set('PowerPoint对象矩阵',`I${row}:I${row}`,[[item.status+': '+item.reason]]);set('PowerPoint对象矩阵',`P${row}:P${row}`,[['validation/native-object-artifacts/native-object-runtime.json；validation/native-object-artifacts/preservation-report.json；仅PP-05组件范围，全对象原验收未通过']]);}
await fs.writeFile(`${tmp}/parallel-matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/parallel-matrix-preview.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'N75:P77',scale:1,format:'png'})).arrayBuffer()));
await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/matrix-after-parallel.xlsx`);
console.log(JSON.stringify({requirements:Object.keys(notes).length,approvedRanges:allowed.length}));
