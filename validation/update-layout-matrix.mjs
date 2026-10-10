import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from 'file:///C:/Users/Ni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='F:/YoloongPPT',tmp='F:/YoloongPPT-Temp-P01-05',base=`${root}/AI_PPT_完整需求与任务矩阵_V0.3.xlsx`;
const report=JSON.parse(await fs.readFile(`${root}/validation/layout-runtime.json`,'utf8'));
if(!report.passed||report.cases.length!==23)throw Error('23 current layout checks required');
try{await fs.copyFile(base,`${tmp}/matrix-before-layout.xlsx`,fs.constants.COPYFILE_EXCL);}catch(e){if(e.code!=='EEXIST')throw e;}
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base)),allowed=[];
function locate(sheet,id){const s=w.worksheets.getItem(sheet),rows=s.getRange('A1:A500').values,index=rows.findIndex(r=>r[0]===id);if(index<0)throw Error(`missing ${sheet} ${id}`);return [s,index+1];}
function set(sheet,range,values){w.worksheets.getItem(sheet).getRange(range).values=values;allowed.push({sheet,range});}
const evidence='validation/layout-runtime.json；validation/layout-artifacts/；validation/版式编译与链路进度修复.md';
for(const [id,note] of [
 ['DEC-030','七类原生文本、表格、图表版式按内容槽位及实际容量生成候选；素材比例、完整类型及独立正式节点契约待完成。'],
 ['DEC-031','实际容量、开场结尾层级与相邻变化参与评分，失败候选保留理由；完整语义、品牌、素材、多后端与正式节点验收待完成。'],
 ['DEC-033','已实际执行文本、表格、图表几何槽位与非重叠检查；连接线、裁切、旋转及完整类型待完成。'],
 ['DEC-034','已实测中文字形、字号、段距、边距与容量，超出全部候选时失败；RTL、字体替代和完整文本适配待完成。'],
 ['SYS-010','统一规格实际消费内容驱动候选、槽位、每页样式并写入真实十页；完整素材、模板和绑定待完成。'],
 ['SYS-012','原生文本面板、字号、边距、描边与逐页样式经登记输入校验和实际写入；全部对象及失败恢复待完成。'],
 ['SYS-013','十页实际顺序构建并保存布局评分，恢复时维持槽位对象身份；完整模板、母版与导入修改待完成。'],
 ['SYS-014','实际渲染PDF、PNG及坐标文字；主产物哈希与版本保留，live与完整缩略图范围待完成。'],
 ['SYS-015','多栏文字按真实PDF对象坐标检查，删除PDF词反例仍检出；实际模型复审通过当前检查，完整质量规则待完成。']]){
 const [s,row]=locate('需求主表',id),[t,tr]=locate('可执行任务',`TASK-${id}`);
 set('需求主表',`N${row}:P${row}`,[['进行中',evidence,note]]);
 set('可执行任务',`L${tr}:M${tr}`,[['进行中',note+' '+evidence]]);
 if(id.startsWith('DEC-')){
  const [v,vr]=locate('可执行任务',`VERIFY-${id}`);set('可执行任务',`L${vr}:M${vr}`,[['进行中','当前子集23项核验及真实产物；完整节点输入输出、五项目对应和全部原验收继续。 '+evidence]]);
  const [d,dr]=locate('决策链',id);set('决策链',`M${dr}:N${dr}`,[['进行中',note+' '+evidence]]);
 }else{const [i,ir]=locate('系统组件接口',id);set('系统组件接口',`H${ir}:I${ir}`,[['进行中',note+' '+evidence]]);}
}
for(const name of ['LayoutCandidates','SlideSpec']){const [s,row]=locate('数据对象',name);set('数据对象',`I${row}:J${row}`,[['进行中','七类原生候选、容量和槽位实际消费，完整对象契约范围待完成。 '+evidence]]);}
const flow={
 S00:'CLI/HTTP接收真实任务、原文与来源身份；全输入格式及统一生命周期待完成。',
 S01:'本地平台、锁定依赖、字体、渲染与实际模型列表已探测；Office、MCP及全部后端探测待完成。',
 S02:'八模式判定及冲突保护已运行，完整后续模式执行仍待完成。',
 S03:'实际校验JSON、UTF-8、容量、身份与约束；全部格式、密码、宏及外链风险校验待完成。',
 S04:'文本、Markdown真实来源及角色加载；其他原始格式待实现。',
 S05:'实际保存文本块、表格、证据和原文锚点；其他格式图片/图形解析待实现。',
 S06:'来源哈希、版本、引用与重复候选保留；语义冲突及优先级决策待实现。',
 S07:'约束归一化实际运行；完整受众、场景、语气、品牌推断与执行待完成。',
 S08:'事实集合及数值成员检查已运行；完整事实、禁止臆造及假设决策待完成。',
 S09:'真实模型输出整套核心信息及逐页证据引用；独立论点决策及完整证据图待完成。',
 S11:'真实模型输出故事线和页面顺序；独立叙事候选与完整章节结构待完成。',
 S12:'真实模型输出页面标题序列；章节/子章节及正式大纲对象待完成。',
 S13:'十页硬预算、八页偏好实际消费；时长与章节分配预算待完成。',
 S14:'真实模型按页组织内容并检查总页数；完整语义拆合及跨页衔接待完成。',
 S15:'每页实际保存目标及核心信息；独立页面目标决策与完整受众推导待完成。',
 S16:'当前文本、表格、图表及开场/结尾版式实际运行；完整类型决策待完成。',
 S17:'实际测量文本/表格槽位，容量不足明确失败；语义改写、拆合及图片预算待完成。',
 S18:'原生文本面板、表格、分类图表实际写入；完整图文、流程、时间线与关系表达待完成。',
 S20:'显式颜色与已安装字体配置已消费；模板、母版、主题和参考图解析待完成。',
 S22:'七类原生候选按槽位与实测容量检索；完整素材及模板条件待完成。',
 S23:'当前容量、页面层级与相邻变化实际评分；完整语义、品牌、素材比例及多后端待完成。',
 S24:'当前标题、正文、数据及备注映射稳定槽位；图片和完整模板占位符待完成。',
 S25:'实际几何槽位、边距和非重叠检查；连接线、旋转、裁切等待完成。',
 S26:'实际中文字体、字号、颜色、填充和描边；阴影、圆角、图片处理等待完成。',
 S27:'原生备注与证据已写入；动画、过渡、媒体和动作待完成。',
 S28:'统一页面规格经真实编译/写入消费；完整素材、模板及绑定待完成。',
 S29:'实际schema、能力绑定、字体、数据和容量检查；完整路径/权限/模板与后端缺口待完成。',
 S30:'当前PP-05登记实现实际选择；全九路线按保真/任务能力动态选择待完成。',
 S31:'实际能力调用DAG与稳定对象/实现ID；完整对象及复杂依赖待完成。',
 S32:'真实原生PPTX与单文本修订已运行；已有文件保真编辑和全部对象待完成。',
 S33:'真实PDF与逐页PNG，版本/hash已保存；live截图和完整缩略图范围待完成。',
 S34:'实际ZIP/XML、边界、对象映射与PDF字词检查；完整关系与结构规则待完成。',
 S35:'真实渲染页经模型视觉审查；全部确定性视觉规则和验收阈值待完成。',
 S36:'实际数值/引用检查与模型事实审查；完整语义真值及图像对应待完成。',
 S37:'原生文本/表格/图表和嵌入数据已检查；导入往返、母版/主题保真待完成。',
 S39:'数值引用问题可触发受限修正；完整质量问题到任意节点修订计划待完成。',
 S40:'既有单文本修订保留其他parts及实体ID，恢复复用模型；任意节点/对象范围待完成。',
 S41:'实际报告草稿及未通过验收状态；完整终止/重试策略待完成。',
 S42:'实际导出PPTX/PDF/PNG与trace/QA；完整导出配置和最终验收门控待完成。',
 S43:'来源、模型、依赖版本和既有版权记录已保留；全部资产/模板许可及转换合并清单待完成。',
 S44:'既有原稿曾经PowerPoint实际打开；本版、修复提示和全部可编辑交付验收待完成。'
};
for(const [id,note] of Object.entries(flow)){const [s,row]=locate('0-1全链路',id);set('0-1全链路',`G${row}:I${row}`,[['进行中',evidence+'；validation/context-runtime.json；validation/generation-runtime.json',note]]);s.getRange(`A${row}:I${row}`).format.rowHeightPx=260;}
const [a,ar]=locate('验收矩阵','AC-001');set('验收矩阵',`G${ar}:J${ar}`,[['部分执行/未通过','真实十页原生PPTX、版式编译及模型复审，当前执行检查P0为零；完整决策链与全质量验收未通过。',evidence,'其余节点、全对象/输入/质量与完整验收继续。']]);
await fs.writeFile(`${tmp}/layout-matrix-allowed.json`,JSON.stringify(allowed));
await fs.writeFile(`${tmp}/layout-matrix-preview.png`,new Uint8Array(await (await w.render({sheetName:'0-1全链路',range:'G24:I25',scale:1.3,format:'png'})).arrayBuffer()));
const out=await SpreadsheetFile.exportXlsx(w);await out.save(`${tmp}/matrix-after-layout.xlsx`);
console.log('layout and original flow status exported');
