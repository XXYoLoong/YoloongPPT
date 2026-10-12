import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT',tmp=`${root}/.tmp/execution-revision`;
const policy=JSON.parse(await fs.readFile(`${root}/validation/authorized-execution-policy-20261012.json`,'utf8'));
const verified=process.argv.includes('--verify-final');
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(`${tmp}/${verified?'verified':'before'}-AI_PPT_完整需求与任务矩阵_V0.3.xlsx`));
const previews=async(prefix)=>{
 for(const [name,range,label] of [['总览','A1:J3','overview'],['Codex交接',prefix==='before'?'A1:C6':'A16:C24','policy'],['可执行任务',prefix==='before'?'A66:F72':'O66:R72','tasks']]){
  const b=await w.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(`${tmp}/${prefix}-${label}.png`,new Uint8Array(await b.arrayBuffer()));
 }
};
if(process.argv.includes('--preview-only')){await previews('before');console.log('Original workbook previews saved');process.exit(0);}
if(verified){
 await previews('final');
 for(const [sheetName,range,label] of [['Codex交接','A25:C32','policy-second'],['来源索引','A15:G17','source'],['需求主表','L37:M44','requirement-notes']]){
  const b=await w.render({sheetName,range,scale:1,format:'png'});await fs.writeFile(`${tmp}/final-${label}.png`,new Uint8Array(await b.arrayBuffer()));
 }
 console.log('Final preserved workbook visual checks rendered');process.exit(0);
}
const allowed=[];
const set=(sheet,range,values)=>{w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});};
const locate=(sheet,id)=>w.worksheets.getItem(sheet).getRange('A1:A500').values.findIndex(r=>r[0]===id)+1;
const append=(sheet,col,id,note)=>{const r=locate(sheet,id);if(!r)throw Error(`Missing baseline ID ${id}`);const prev=w.worksheets.getItem(sheet).getRange(`${col}${r}`).values[0][0]??'';set(sheet,`${col}${r}`,[[`${prev}${prev?'\n':''}${policy.revision_id}：${note}`]]);};
set('总览','B2',[['V0.3']]);set('总览','D2',[['2026-10-12']]);
const overview=w.worksheets.getItem('总览');overview.mergeCells('A3:J3');set('总览','A3',[['EXEC-20261012-01：GPT-6.1 sol 自主开发；Docling 与已选开源模块优先复用；禁止开发工期预算；全部原验收一次整体交付。']]);overview.getRange('A3:J3').format.wrapText=true;overview.getRange('A3:J3').format.rowHeight=35;
const notes={
 'GOV-001':'用户授权执行修订同步三份文件；原ID、需求、依赖、验收及状态保持。',
 'GOV-008':'全部原验收一次整体交付；中间产物、P0=0和阶段收尾不代替最终完成。',
 'GOV-010':'复用固定上游快照与证据；Docling和新接模块在实际集成时登记版本/hash。',
 'RES-032':'优先直接调用/模块复用；核对来源、依赖、许可和接口后调整旧仅参考/抽象复用决定，不以工程偏好重写现成功能。',
 'IN-003':'优先接Docling DOCX结构输出到现有SourceBundle/Evidence及原锚点；保留原解析证据，缺口才补适配。',
 'IN-004':'优先接Docling PDF布局、表格和结构输出，保留page/坐标/source anchor与完整证据。',
 'IN-005':'优先复用Docling OCR与成熟OCR引擎；模型/语言/置信度/页面定位按原验收记录。',
 'IN-008':'评估Docling适用输出，保留现有公式缓存、显示值、单位与cell/range能力；不丢原字段。',
 'IN-016':'融合层保留原文件/hash、page/paragraph/cell锚点、资产与事实ID，不把候选冒作事实真值。',
 'SYS-003':'SourceLoader实际调用成熟解析器，统一SourceBundle、结构化错误及trace。',
 'SYS-012':'优先调用成熟原生对象库与开源执行模块，按现有AtomicCapability/对象映射消费；只补必需适配。',
 'SYS-013':'优先接PPT Master导出/编辑与Presenton适用对象模型，结合已验证原生库；保留模板/主题/未知部件。',
 'SYS-014':'复用现有LibreOffice/Poppler与PPTAgent适用渲染模块；统一PNG/PDF/thumbnail、hash及renderer版本。',
 'SYS-015':'接PPTAgent视觉审查/freshness及PPT Master检查器，统一原QA问题契约，补上游事实/语义缺口。',
 'SYS-016':'连接上游与现有局部修改能力，统一范围/锁/版本/RevisionPlan及修订后的真实复查。',
 'QA-020':'复用检查与审查模块，按原slide/object/severity/measurement/threshold/action消费；有代码不等于原验收通过。',
 'REV-010':'保留真实修订前后实物、对象差异与独立复查；已存在的修订模块优先复用。',
 'OPS-012':'GPT-6.1 sol独立完成实现/测试/排障/交付，不要求人工开发，不估算工期，不以阶段结果结束整体目标。'
};
for(const [id,note]of Object.entries(notes))append('需求主表','M',id,note);
const domainSource={
 '输入与来源解析':'Docling；既有SourceLoader/解析库；仅补原能力缺口',
 '内容与证据':'已选项目内容处理模块；既有事实/来源/冲突模块',
 '决策体系':'PPT Master/PPTAgent/Presenton决策模块；既有DEC消费者',
 '模板/版式/风格':'PPT Master模板/导出；Presenton模板/布局/schema',
 '素材与视觉资产':'已选项目资产处理；成熟图像库；既有资产登记',
 'PowerPoint 原生对象能力':'PPT Master原生导出/编辑；既有原生库；原PP路线',
 'PowerPoint 后端与接口':'原PP-01–09库/CLI/API/MCP；复用已有PoC证据',
 '系统组件与编排':'现有CLI/API/MCP/任务核心；已选项目服务模块',
 '已有 PPT 与修订':'PPT Master编辑模块；已有原生局部修订模块',
 '质量与验收':'PPTAgent渲染/视觉/freshness；PPT Master检查器',
 '开源项目源码研究':'复用P01–P05固定快照、已完成研究与证据',
 '治理与边界':'原schema/ID/能力/来源/变更记录',
 '测试与验收':'既有有效用例/实物；RES-033登记的可复用测试',
 '工程化与交付':'现有Docker/启动/任务/版本/日志；成熟工具',
 '非功能需求':'现有运行组件；成熟并发/性能/故障测试工具',
 '安全/隐私/许可':'现有安全控制；成熟校验库；来源/许可记录',
 '可观察性与可复现':'现有trace/manifest/版本/恢复；成熟日志组件'
};
const tasks=w.worksheets.getItem('可执行任务'),base=tasks.getRange('A2:N454').values;
if(base.length!==453||new Set(base.map(r=>r[0])).size!==453)throw Error('Task baseline count changed');
set('可执行任务','O1:R1',[['执行主体','实现原则','优先复用来源','执行修订']]);
set('可执行任务','O2:R454',base.map(r=>['GPT-6.1 sol','先调用/复用，再薄适配；有证据缺口才补实现',domainSource[r[2]]??'既有模块与成熟开源组件；按原ID核对缺口',policy.revision_id]));
tasks.getRange('O1:R454').format.font={name:'Noto Sans CJK SC',size:11};tasks.getRange('O1:R454').format.wrapText=true;tasks.getRange('O1:R1').format.fill='#1F4E78';tasks.getRange('O1:R1').format.font.color='#FFFFFF';tasks.getRange('O1:R1').format.font.bold=true;
tasks.getRange('O1:O454').format.columnWidth=18;tasks.getRange('P1:P454').format.columnWidth=39;tasks.getRange('Q1:Q454').format.columnWidth=45;tasks.getRange('R1:R454').format.columnWidth=24;
// Prevent import/export autofit from expanding untouched historical evidence rows.
tasks.getRange('O1:R1').format.rowHeight=30;
for(let i=0;i<base.length;i++)tasks.getRange(`O${i+2}:R${i+2}`).format.rowHeight=48;
tasks.getRange('O1:R454').format.verticalAlignment='center';
const flow={'S04':'优先调用Docling及成熟SourceLoader，映射现有SourceBundle与文件/hash。','S05':'复用结构/OCR/表格能力，融合page/paragraph/cell锚点、资产和事实ID。','S33':'优先接已有渲染器；统一产物与版本/hash，不另造渲染引擎。','S34':'复用PPT Master结构/导出检查并统一原Issue契约。','S35':'复用PPTAgent视觉审查模块，保留真实图像、阈值和问题定位。','S36':'沿用既有事实证据核对，补上游未覆盖的语义条件，不能以视觉审查代替事实验收。','S37':'复用原生对象库/上游编辑测试，按原对象与backend条件验证可编辑性。','S38':'统一上游问题到原slide/object/action，保留严重度、测量值与阈值。','S39':'统一RevisionPlan与范围/锁/版本，不重写完整修订引擎。','S40':'调用既有局部修改及上游适用能力，实际渲染和独立复查。','S43':'固定模块/依赖版本和许可，未知边界明确记录；开发由GPT完成。','S44':'全部原验收后整体交付；不以阶段稿替代，不安排人工开发或工期预算。'};
for(const[id,note]of Object.entries(flow))append('0-1全链路','I',id,note);
const handoff=w.worksheets.getItem('Codex交接');
for(let r=2;r<=13;r++){const old=handoff.getRange(`F${r}`).values[0][0]??'';set('Codex交接',`F${r}`,[[`${old}${old?'\n':''}${policy.revision_id}：由GPT-6.1 sol完成接入/实现/验证；复用有效证据，保持原交接要求。`]]);}
handoff.mergeCells('A16:C16');set('Codex交接','A16',[['用户授权执行要求 EXEC-20261012-01']]);handoff.getRange('A16:C16').format.font={name:'Noto Sans CJK SC',size:13,bold:true};handoff.getRange('A16:C16').format.rowHeight=30;
for(let i=0;i<policy.sections.length;i++){
 const r=17+i,s=policy.sections[i];handoff.mergeCells(`B${r}:C${r}`);set('Codex交接',`A${r}`,[[s.title]]);set('Codex交接',`B${r}`,[[s.text]]);
 handoff.getRange(`A${r}:C${r}`).format.font={name:'Noto Sans CJK SC',size:11};handoff.getRange(`A${r}:C${r}`).format.wrapText=true;handoff.getRange(`A${r}:C${r}`).format.verticalAlignment='center';handoff.getRange(`A${r}:C${r}`).format.rowHeight=Math.max(55,Math.ceil(s.text.length/52)*17+12);
}
handoff.mergeCells('A32:C32');set('Codex交接','A32',[['变更记录：2026-10-12 用户授权；原需求/任务/依赖/验收/状态不变；三份文件同步。']]);handoff.getRange('A32:C32').format.wrapText=true;handoff.getRange('A32:C32').format.rowHeight=35;
const sources=w.worksheets.getItem('来源索引');set('来源索引','A17:G17',[[policy.docling_source.id,'开源组件',policy.docling_source.name,policy.docling_source.repository,'IN-003/004/005/008/016；SYS-003；RES-032；GOV-010','2026-10-12',`${policy.docling_source.observed_license}；${policy.docling_source.version_state}`]]);sources.getRange('A17:G17').format.font={name:'Noto Sans CJK SC',size:11};sources.getRange('A17:G17').format.wrapText=true;sources.getRange('A17:G17').format.rowHeight=66;
w.recalculate();
const checks=await w.inspect({kind:'region',sheetId:'可执行任务',range:'O66:R72',maxChars:2000});await fs.writeFile(`${tmp}/matrix-policy-inspect.ndjson`,checks.ndjson);
const errors=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},summary:'Execution policy formula check'});await fs.writeFile(`${tmp}/matrix-error-scan.ndjson`,errors.ndjson);
await previews('after');
await(await SpreadsheetFile.exportXlsx(w)).save(`${tmp}/after-AI_PPT_完整需求与任务矩阵_V0.3.xlsx`);
await fs.writeFile(`${tmp}/allowed-matrix-edits.json`,JSON.stringify(allowed));
console.log(JSON.stringify({revision_id:policy.revision_id,tasks:453,policy_sections:14,edited_ranges:allowed.length,output:'after-AI_PPT_完整需求与任务矩阵_V0.3.xlsx'}));
