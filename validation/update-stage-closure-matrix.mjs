import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT',tmp=`${root}/.tmp/source-semantic`;
const original=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`,before=`${tmp}/matrix-before.xlsx`,after=`${tmp}/matrix-after.xlsx`;
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const baseline=hash(await fs.readFile(before));
if(hash(await fs.readFile(original))!==baseline)throw Error('Original matrix changed since this package baseline');
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(before));
if(process.argv.includes('--preview-only')){
 await fs.writeFile(`${tmp}/matrix-before.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'A35:D44',scale:1,format:'png'})).arrayBuffer()));
 console.log(JSON.stringify({preview:`${tmp}/matrix-before.png`}));process.exit(0);
}
const ev=JSON.parse(await fs.readFile(`${root}/validation/stage-closure-summary.json`,'utf8')),allowed=[];
if(!ev.description_flow.passed||ev.description_flow_checks!==15)throw Error('Final bounded description flow not proven');
const locate=(sheet,id)=>w.worksheets.getItem(sheet).getRange('A1:A500').values.findIndex(r=>r[0]===id)+1;
const set=(sheet,range,values)=>{w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});};
const path='当前实现与阶段收尾报告_20261012.md；validation/stage-closure-artifacts/；validation/stage-closure-summary.json';
const notes={
 'IN-003':'原DOCX解析已接native evidence增强：heading/table逻辑grid/合并/图片部件hash尺寸alt、hyperlink/脚注/引用、物理页pending；34项组件通过。有效外链URI另登记原生关系字面证据，未下载。旧夹具引用关系异常与当前实际模型日期变换均拒绝；本轮完整DOCX生成未通过。',
 'IN-004':'固定Poppler真实4页夹具38项通过，页/块/逐字坐标、网格/标题候选与真实图片清单进入source_context；跨页表/并列正文/OCR/图片几何不猜，超限明确失败。六页PDF实际模型输出截断阻断生成，完整AC003未通过。',
 'IN-008':'XLSX显示投影接入：日期1900/1904、固定格式/百分比/引用单位、已有公式缓存、原cell/range与候选，57项组件通过。未知/地域/条件格式/缺缓存原数据保留但不冒作数值事实。两sheet实际API六页PPTX/render/真实审查12项通过，P0=0/4警告；全Excel显示/语义AC005仍未通过。',
 'IN-016':'三格式原生定位与source_context进入真正SourceLoader/初始事实解释，原始字节/hash保留；DOCX新增URI有独立关系锚点，PDF重复数字保留不同字锚点。物理Word页、OCR与全格式来源绑定仍待完成。',
 'SYS-003':'三格式助手已由parse_input实际调用并纳入parser_version；真实XLSX生成和单段prompt链路经过SourceLoader。原始快照/角色/选定事实保留，HTML/YAML/OCR等原范围未完成。',
 'DEC-005':'本轮新增source_context实际消费，候选不宣称事实真值；XLSX显示值区分底层存储/缓存。DOCX无依据引用/日期与PDF模型截断在写PPT前失败，原独立节点已完成状态保留，不等于来源语义与AC全通过。',
 'SYS-015':'单段描述六页24对象→原生PPTX/真实render/独立review，P0=0/3警告；局部修订后P0=0/2警告。人工视觉发现封面操作指令泄漏，自动QA未拦截；完整事实/内容适用性/可编辑性等原QA仍未通过。',
 'SYS-016':'复用前一批次消费者，明确局部改封面标题/正文清除操作指令；真实复审15项流程检查，另8项Native数据/字节检查，只有slide1.xml改变，其他页/数据/选定事实保留。未称全节点自动修订完成。',
 'QA-020':'人工发现的task_instruction_leak另记slide/object/type/P1/measurement/threshold/action/render hash及改后状态，原自动QA不覆盖；自动规则尚未支持该问题，完整issue/修订原验收仍未通过。'
};
for(const [id,note] of Object.entries(notes)){
 const r=locate('需求主表',id);if(!r)throw Error(`Missing ${id}`);
 const prev=w.worksheets.getItem('需求主表').getRange(`N${r}:P${r}`).values[0];
 if(prev[0]==='已完成')set('需求主表',`O${r}:P${r}`,[[`${prev[1]}；${path}`,`${prev[2]}\n2026-10-12阶段收尾：${note}`]]);
 else set('需求主表',`N${r}:P${r}`,[['进行中',`${prev[1]??''}${prev[1]?'；':''}${path}`,`${prev[2]??''}${prev[2]?'\n':''}2026-10-12阶段收尾：${note} 完整原验收未通过。`]]);
 for(const prefix of ['TASK-','VERIFY-']){
  const tr=locate('可执行任务',prefix+id);if(!tr)continue;
  const old=w.worksheets.getItem('可执行任务').getRange(`L${tr}:M${tr}`).values[0];
  if(old[0]==='已完成')set('可执行任务',`M${tr}:M${tr}`,[[`${old[1]}\n2026-10-12：${note} ${path}`]]);
  else set('可执行任务',`L${tr}:M${tr}`,[['进行中',`${old[1]??''}${old[1]?'\n':''}2026-10-12：${note} ${path}；完整原验收未通过。`]]);
 }
 if(id.startsWith('SYS-')){
  const sr=locate('系统组件接口',id);if(sr){const old=w.worksheets.getItem('系统组件接口').getRange(`H${sr}:I${sr}`).values[0];set('系统组件接口',`H${sr}:I${sr}`,[['进行中',`${old[1]}\n2026-10-12：${note} ${path}`]]);}
 }
}
const ac={
 'AC-001':'单段prompt实际6页/24原生对象（22文字+1表+1图表），真实事实/内容/复审；生成3警告、局部修订2警告，均P0=0/final=false。15流程+8原生实物检查，不替代原约10页及完整原验收。',
 'AC-002':'DOCX增强34项组件；旧夹具引用未逐字落证据时拒绝，当前有效夹具实际模型日期无依据变换再拒绝。没有PPTX成功制品，完整原AC未通过。',
 'AC-003':'PDF四页含文本/网格/图片夹具38项；实际六页输入事实解释模型输出截断，MODEL_OUTPUT_INCOMPLETE保留，未降级生成，完整AC未通过。',
 'AC-005':'真实两sheet/日期/时序/分类/缓存和百分比显示→六页原生表格与分单位图表，12项链路/P0=0/4警告；缓存新鲜/所有格式/完整语义仍未验收，图表合计与月份混排需独立语义评估。',
 'AC-027':'本轮保留原始来源/hash、选定事实、DEC001–040有界trace、DeckSpec/ObjectMap/native执行/QA/revision/版本；人工指令泄漏另存问题与修订记录，完整随机对象抽检未完成。',
 'AC-030':'当前从单段描述到生成/实际render/QA/局部修订/再QA可运行；硬4页不足、DOCX事实/日期、PDF输出截断保留显式fail。S00–44有界消费不等于全部模式/覆盖及final原验收，当前final仍false。'
};
for(const [id,note] of Object.entries(ac)){
 const r=locate('验收矩阵',id);set('验收矩阵',`G${r}:J${r}`,[['部分执行/未通过',note,path,'完整原验收未通过']]);
}
const flow={
 S00:'单段prompt的真实TaskSpec进入HTTP/CLI/MCP共享核心，输出六页并可局部再修订；完整所有输入与任务模式待验收。',
 S04:'当前SourceLoader实际读取prompt/text/Markdown、DOCX/XLSX/CSV/PPTX/POTX/PDF/image/JSON/XML的有界原文件；本轮三格式增强接入。HTML/URL/YAML/OCR及全部资产类型仍待完成。',
 S05:'三格式原文/结构/原生段格页与图片部件证据已保存，候选结构进入模型但不视为语义真值；物理Word页/OCR/复杂PDF表格/全部格式语义待补。',
 S07:'硬四页不足明确失败；显式软六页描述生成六页，约束沿用。完整受众/场景/品牌与任意自然语言约束仍待验收。',
 S34:'新描述与XLSX实物真实结构/渲染检查P0=0，原生数值与字节另验；全结构规则仍未完成。',
 S35:'实际render经人工查看，发现封面操作指令外泄并仅修封面。自动QA未发现该内容问题，不能以P0=0判全部视觉/内容通过。',
 S36:'事实/数值与实际模型审查执行，DOCX日期错误/PDF截断拒绝，XLSX数字单位实际保留。完整事实语义/内容适用性仍未通过。',
 S37:'当前六页24原生对象含可编辑表/图；8项实物核对源数值和未改parts，所有对象与PowerPointUI兼容待验收。',
 S40:'当前明确局部改首页两个对象，其他五页/数据/选定事实保留，仅slide1.xml改变，实际选页重审；全部节点自动修订未完成。',
 S41:'当前生成/修订均warning/final_allowed=false；自动0P0不能覆盖人工发现内容问题或完整覆盖缺口。',
 S44:'当前可下载六页原生PPTX/PDF/PNG，报告及剩余范围已交付；本版未重跑PowerPointUI，AC028与全部原AC仍未通过。'
};
for(const [id,note] of Object.entries(flow)){
 const r=locate('0-1全链路',id),old=w.worksheets.getItem('0-1全链路').getRange(`G${r}:I${r}`).values[0];
 const detail=['S04','S05'].includes(id)?`2026-10-12当前：${note}`:`${old[2]}\n2026-10-12：${note} 完整步骤原验收未通过。`;
 set('0-1全链路',`G${r}:I${r}`,[['进行中',`${old[1]}；${path}`,detail]]);
}
w.recalculate();
const inspection=await w.inspect({kind:'region',sheetId:'需求主表',range:'N35:P44',maxChars:1800,tableMaxRows:10,tableMaxCols:3});
await fs.writeFile(`${tmp}/matrix-inspect.ndjson`,inspection.ndjson);
await fs.writeFile(`${tmp}/matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/matrix-evidence.json`,JSON.stringify({baseline_sha256:baseline,requirement_ids:Object.keys(notes),system_acceptance:'not_passed',components:ev.components,description_flow:ev.description_flow,source_generations:ev.source_generations},null,2));
await fs.writeFile(`${tmp}/matrix-after.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'A35:D44',scale:1,format:'png'})).arrayBuffer()));
await(await SpreadsheetFile.exportXlsx(w)).save(after);
console.log(JSON.stringify({output:after,requirements:Object.keys(notes).length,allowedRanges:allowed.length}));
