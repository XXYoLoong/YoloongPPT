import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const root='F:/YoloongPPT',tmp=`${root}/.tmp/batch-revision`;
const original=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`,before=`${tmp}/matrix-before.xlsx`,after=`${tmp}/matrix-after.xlsx`;
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const baseline=hash(await fs.readFile(before));
if(hash(await fs.readFile(original))!==baseline)throw Error('Original matrix changed since package baseline');
const evidence=JSON.parse(await fs.readFile(`${root}/validation/batch-revision-artifacts/evidence-manifest.json`,'utf8'));
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(before)),allowed=[];
const locate=(sheet,id)=>w.worksheets.getItem(sheet).getRange('A1:A500').values.findIndex(r=>r[0]===id)+1;
const set=(sheet,range,values)=>{w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});};
const path='validation/批量局部修订与原生保真.md；validation/batch-revision-artifacts/';
const notes={
 'REV-001':'现有原生导入与批次写入相接；含母版/布局/图表/图片/备注/未知扩展的组件夹具52项检查。任意已有PPT内容与语义导入仍未完整。',
 'REV-002':'批次前置验证及原子另存保留未选ZIP负载/实体ID；共享媒体/工作簿/备注拒绝跨范围修改，未支持对象不重新保存。所有未知对象客户端语义保真仍待覆盖。',
 'REV-003':'真实DeepSeek解析限定两页自然语言指令，范围/原文证据/候选唯一性校验；明确scope越界拒绝。完整deck/section语义范围和任意既有deck仍待实现。',
 'REV-004':'ID/shape/name/text/placeholder/页号选择器在授权范围内唯一定位；真实模型选择保留原文匹配与目标证据。范围组件39项是合成响应测试，非真实AI验收。',
 'REV-005':'批次文字/图表系列/登记图片/单元格/几何/有界格式/替代文字/备注接入；实际API两页改标题、原图表系列重排、换图及重复换图，未选对象与页字节不变。完整图表新数值、裁切及复杂对象原验收未完成。',
 'REV-006':'指令或原RevisionPlan才修改几何；锁/品牌范围前置核对；真实故障注入父稿局部恢复正文布局和标题颜色，真实重渲染/复审。任意layout/节点重排仍待补。',
 'REV-009':'实际beautify锁定其余对象，正文几何与标题对比修复，事实/数据不变；8页P0=0但7警告且旧父缺DEC022–038，不伪造继承节点。完整视觉与品牌验收未通过。',
 'REV-010':'每次成功保存instruction/scope/locks、逐操作中间与最终spec、原生part差异、QA前后、父子run与版本hash；结构化失败另留manifest。完整所有修订路径仍待覆盖。',
 'SYS-016':'共享revise入口连接批次识别→前置规格/锁校验→原生修改→真实render→独立选页模型复审→QA/history；CLI/MCP锁拒绝实跑。全部节点局部重跑仍未完成。',
 'QA-019':'五次实际API修订均P0=0，警告6/4/5/7/6，final_allowed=false；原失败与旧父覆盖缺口保留。全问题类型/自动修订与原AC未通过。',
 'QA-020':'复审只更新所选页并保留其他页issue；DEC040消费真实祖先节点，未把P0=0当final。所有issue完整字段/阈值/action原验收仍待补。',
 'TST-007':'原生52项组件含共享引用、组锁、双图表/内嵌工作簿、图像/表格/备注以及未知扩展保留；真实修订比较未改页/对象/包成员。全部对象/客户端round-trip仍待覆盖。',
 'TST-018':'两页文案、图表、换图及再次换图、故障注入美化五次实际修订74项检查；不混同不同版本39/52/10组件检查。修订后PowerPoint实际改存复开尚未执行。',
 'ADP-PP-01-01':'本机PowerPoint16.0.20430.20092实际COM打开父稿/副本改文案另存复开与四份新修订只读检查489项；原稿hash不变。另存重写非目标XML/关系及部分printerSettings，非字节保真；新建/高级对象/并发/弹窗/UI修复提示未完整验证。'
};
for(const [id,note] of Object.entries(notes)){
 const row=locate('需求主表',id);if(!row)throw Error(`Missing ${id}`);
 const prev=w.worksheets.getItem('需求主表').getRange(`N${row}:P${row}`).values[0];
 if(prev[0]==='已完成')throw Error(`Refusing completed row ${id}`);
 set('需求主表',`N${row}:P${row}`,[['进行中',`${prev[1]??''}${prev[1]?'；':''}${path}`,`${prev[2]??''}${prev[2]?'\n':''}2026-10-11增量：${note} 完整原验收未通过。`]]);
 for(const prefix of ['TASK-','VERIFY-']){
  const tr=locate('可执行任务',prefix+id);if(!tr)continue;
  const old=w.worksheets.getItem('可执行任务').getRange(`L${tr}:M${tr}`).values[0];if(old[0]==='已完成')continue;
  set('可执行任务',`L${tr}:M${tr}`,[['进行中',`${old[1]??''}${old[1]?'\n':''}2026-10-11：${note} ${path}；完整原验收未通过。`]]);
 }
 if(id==='SYS-016'){
  const sr=locate('系统组件接口',id);
  const prev=w.worksheets.getItem('系统组件接口').getRange(`H${sr}:I${sr}`).values[0];
  set('系统组件接口',`H${sr}:I${sr}`,[['进行中',`${prev[1]}\n2026-10-11：${note} ${path}`]]);
 }
}
const ac={
 'AC-008':['真实自然语言只修改第1/6页标题；16项API检查，未修改页/对象字节保留，PowerPoint原生文字框读取匹配。P0=0/6警告；修订稿目标对象实际选中改存复开及完整质量原验收未完成。',path],
 'AC-009':['真实API系列重排15项、换图14项及再次换图14项，内嵌工作簿/图表缓存与系列一致；COM图片hash/图表值匹配。未验证有来源的新数值改写、所有图表/图片/裁切及完整事实语义。',path],
 'AC-010':['复用明确人工故障注入父稿，真实恢复标题色与正文几何、锁定其余对象，15项检查；事实/数据不变，重渲染及新模型审查P0=0/7警告。旧父缺DEC022–038，完整视觉改善/品牌/事实原验收仍待满足。',path],
 'AC-028':['PowerPoint16.0实际打开四个新修订稿，489项文字/图片/图表/几何对照；原稿hash不变。初次4条水平连接线比较失败保留，按显式端点纠正比较器后通过；COM无异常不证明UI无修复提示。','validation/powerpoint-open-artifacts/']
};
for(const [id,[note,evidencePath]] of Object.entries(ac)){
 const r=locate('验收矩阵',id);set('验收矩阵',`G${r}:J${r}`,[['部分执行/未通过',note,evidencePath,'完整原验收未通过']]);
}
const flow={
 S35:'五次真实render/独立选页模型复审；美化局部几何/颜色恢复，全部视觉规则仍待覆盖。',
 S37:'五次原生修订和52项夹具检查保留未选parts/XML；COM读取证明有界原生对象，所有对象编辑性/客户端语义待验收。',
 S38:'换图的alt_text与图注证据同步，连接线descr承载关系时明确拒绝alt修改；完整可访问性待验收。',
 S39:'继承已有RevisionPlan路径；新增用户批次指令与真实模型目标解释保留trace，不等同全QA自动动作已支持。',
 S40:'多页多对象批次修改→实际render→独立选页复审→QA/history；未选页/对象字节保留，重复换图可继续修订。任意节点/对象/已有deck语义仍待补。',
 S41:'五次P0=0但警告及覆盖缺口保留，均warning/final_allowed=false；不替旧父补缺失DEC。',
 S44:'四份新修订稿实际PowerPoint只读打开及489项对照；更早父稿副本编辑另存复开成立。UI无修复提示及修订稿目标对象实际改存复开仍未验证。'
};
for(const [id,note] of Object.entries(flow)){
 const r=locate('0-1全链路',id),prev=w.worksheets.getItem('0-1全链路').getRange(`G${r}:I${r}`).values[0];
 set('0-1全链路',`G${r}:I${r}`,[['进行中',`${prev[1]}；${path}`,`${prev[2]}\n2026-10-11：${note} 完整步骤与原验收未通过。`]]);
}
const pp=locate('PowerPoint后端','PP-01');
set('PowerPoint后端',`H${pp}:N${pp}`,[['本机已安装，COM部分实际执行','部分执行/未通过','PowerPoint16.0.20430.20092','新建未执行；现有稿打开/只读检查已执行','validation/powerpoint-open-artifacts/；父稿副本文字修改另存复开，Office重写非目标parts，未证明字节保真','高级能力/事件/并发/UI弹窗未完整执行','COM为独立平台PoC；不是Docker运行依赖或已选产品后端，AC028仍缺UI修复提示观察。']]);
w.recalculate();
await fs.writeFile(`${tmp}/matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/matrix-evidence.json`,JSON.stringify({baseline_sha256:baseline,requirement_ids:Object.keys(notes),cases:evidence.cases,system_acceptance:'not_passed'},null,2));
await fs.writeFile(`${tmp}/matrix-after.png`,new Uint8Array(await(await w.render({sheetName:'需求主表',range:'A208:D215',scale:1,format:'png'})).arrayBuffer()));
await(await SpreadsheetFile.exportXlsx(w)).save(after);
console.log(JSON.stringify({output:after,requirements:Object.keys(notes).length,allowedRanges:allowed.length}));
