"""RES-031: compare existing fixed research, with physical source and evidence anchors.

No provider calls, dependency installs, implementation copying or product runtime choice.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
CLONES=Path('F:/YoloongPPT-Research')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(name,data):(HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
PROJECTS={
 'P01':('ppt-master','2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d','project_decision_map.json','decision_nodes','source_index.json','MIT'),
 'P02':('PPTAgent main Skill','833cda553b343be0e486a93b0b57cac962cdd566','decision-map.json','nodes','source-index.json','MIT'),
 'P03':('Presenton','35bf44290f821323e003da854f78ffcb0e918167','decision-map.json','nodes','source-index.json','Apache-2.0'),
 'P04':('ai-agent-ppt','c3605ebc487fc6c7d4f4139761e46d7021cd656c','decision-map.json','decisionNodes','source-index.json','MIT'),
 'P05':('auto-ppt-engine','5ae0670747885c464aa8063329a902d80a251877','ProjectDecisionMap.json','nodes','source_index.json','AGPL-3.0 file; conflicting Apache-2.0 metadata')}
# Each row: status, observed/source-backed conclusion, limitation, locator IDs, runtime evidence.
# D: existing decision node; S: existing source index node; L: fixed license declarations.
ROWS={
'输入':[
 ('Partial','文件/文本/URL作为来源；Generate/Beautify/Edit等路由由Skill指定','Quick实测Markdown；其余来源转换是源码规则；无独立自然语言路由模型','D:P01-DEC-01,D:P01-DEC-02,S:source_intake','projects/p01_hello_world_20261007/validation/verify-res-p01-01.json'),
 ('Partial','CLI任务仅slides/aspect_ratio/language；用户内容与HTML由主机准备','不是完整TaskSpec或文档输入解析器','D:D02,D:D03','validation/verify-official-six.json;validation/workflow-probes.json'),
 ('Partial','Web/REST接收prompt、files、slides_markdown、语言、页数、模板','启动与历史HTTP428有记录；输入生成分支未运行','D:P03-REQUEST,D:P03-SOURCES,D:P03-MARKDOWN','validation/smoke.json;validation/verify-res-p03-02.json'),
 ('Partial','CLI按html>images>topic/input分流；单文件UTF-8、目录仅README/package','没有SourceBundle角色/优先级；真实模型路径未运行','D:P04-ROUTE,D:P04-INPUT','validation/verify-res-p04-02.json'),
 ('Partial','CLI/JSON接收prompt、source、template、旧deck JSON；来源excerpt限5000字符','不是所有入口共享校验；不是任意PPTX保真输入','D:P05-D01,D:P05-D02','validation/baseline-run.json;validation/maps-probes.json')],
'内容理解':[
 ('Partial','通信契约、reading mode、来源事实/限定词由主机按Prompt处理','没有独立事实冲突求解器；Quick transient plan不保存内部推理','D:P01-DEC-02,D:P01-DEC-04,D:P01-DEC-05',''),
 ('Not found','固定CLI未实现独立内容理解/事实模型；Skill委托主机创作','真模型HTML输出不证明有可定位的理解算法或事实QA','D:D03','validation/author-prompts.json;validation/author-response.json'),
 ('Partial','loader/search构造context；outline结构化输出；Smart要求来源事实','无typed fact/assumption或来源冲突解决；模型未执行','D:P03-SOURCES,D:P03-OUTLINE,D:P03-FACTS','validation/verify-res-p03-03.json'),
 ('Partial','LLM大纲Prompt与逐页扩写；只检查title与slides数组','扩写失败保留原页；speakerNotes和chartData未被写入消费','D:P04-OUTLINE,D:P04-CONTENT-FILL','validation/verify-res-p04-04-05.json'),
 ('Partial','mock关键词推断；真实模型可按Schema规划；source trust/priority只是metadata','实测中文仍en-US；没有句级证据和冲突求解','D:P05-D02,D:P05-D03,D:P05-D05','validation/maps-probes.json')],
'规划':[
 ('Partial','Default三方向→用户确认→DesignSpec/spec_lock；Quick主机瞬时规划','Default未执行；用户确认协议不能替代确定性候选评分','D:P01-DEC-04,D:P01-DEC-06,S:strategist_and_confirmation',''),
 ('Not found','内容、结构、页面用途由主机决定；CLI没有Planner编排函数','内部候选和评分黑盒；author-six.py是研究调用，不是上游Planner','D:D03','validation/author-run.json'),
 ('Partial','Standard outline→layout→schema内容；Smart直接HTML/流式页面','无完整统一OutlineSpec/关系图/DecisionTrace；生成未运行','D:P03-OUTLINE,D:P03-LAYOUT,D:P03-SMART','validation/verify-res-p03-03.json'),
 ('Partial','先LLM生成JSON outline，再按页扩写和固定layout加载','模型内部选择未知；扩写失败静默保留；仅大纲重试3次','D:P04-OUTLINE,D:P04-OUTLINE-RETRY,D:P04-CONTENT-FILL','validation/verify-res-p04-02.json'),
 ('Partial','JSON deck规划、Schema校验与有限repair；mock固定roster','真实模型未运行；mock不等于AI规划验收','D:P05-D04,D:P05-D05','validation/baseline-run.json')],
'分页':[
 ('Partial','page budget/section roster由主机规划；锁定ID/顺序后需修订或重确认','没有确定性内容容量到页数求解；3页Quick实物是子集','D:P01-DEC-08,D:P01-DEC-10','projects/p01_hello_world_20261007/validation/verify-res-p01-01.json'),
 ('Partial','slides须正整数；HTML序号连续且数量匹配，严格构建检查','没有自动预算/拆页；容量不符需改源；六页footer曾转换失败','D:D02,D:D06,D:D15','validation/workflow-probes.json;validation/footer-revision.json'),
 ('Partial','请求count、标题/TOC规则；slides_markdown逐项映射一页','outline超数会裁剪；没章节预算；运行被历史认证门禁挡住','D:P03-PAGE-TOC,D:P03-MARKDOWN,D:P03-OUTLINE','validation/verify-res-p03-03.json'),
 ('Partial','Prompt建议5–15页；按outline页与layout遍历导出','缺layout跳页；60条bullet只写4条，56条无遗漏报告','D:P04-OUTLINE,D:P04-LAYOUT-LOAD,D:P04-TOPIC-RENDER','validation/verify-res-p04-04-05.json'),
 ('Partial','请求页数钳制5–12；mock roster实测最多9页；JSON修订可改页数','1页请求实际5、12实际9；clarify101字裁80字无新增说明','D:P05-D04,D:P05-D07','validation/baseline-run.json;validation/maps-probes.json')],
'页面类型':[
 ('Partial','page brief以单页intent驱动关系、拓扑、chart/table等表达','目录和Prompt定义类型，不是实际跑过全部类型的分类器','D:P01-DEC-09,D:P01-DEC-11,D:P01-DEC-17',''),
 ('Not found','只有通用claim/evidence starter；页面类型由主机写HTML','无正式page-type枚举、分类器或页面类型到模板的选择函数','D:D03,D:D04','validation/verify-official-six.json'),
 ('Partial','Standard由template layout描述与Schema选型；Smart按Prompt生成','默认JSON无显式page-type/applicability字段；关键词标签只是候选','D:P03-LAYOUT,D:P03-SMART,S:template-layout-model','validation/verify-res-p03-04.json'),
 ('Partial','8个layout名称由Prompt给出，对应8个JSON版式','没有完整类型推断与适用性评分；名称无效会跳过','D:P04-LAYOUT-CHOICE,D:P04-LAYOUT-LOAD','validation/verify-res-p04-04-05.json'),
 ('Partial','JS17个layout key/15渲染函数；Python映射13 key另有blank','kpi/swot/image-text/funnel未映射，回layout0/bullet且字段损失','D:P05-D08,D:P05-D10','validation/maps-probes.json')],
'素材':[
 ('Partial','image necessity/source/job由计划规定；准备icon pool、fit/crop规则','允许来源与missing asset处理有Prompt，但不是已验证的所有素材获取','D:P01-DEC-12,D:P01-DEC-13,D:P01-DEC-16',''),
 ('Partial','主机准备本地assets；review renderer仅允许跟踪file资源','无素材搜索/必要性算法；复杂样式PNG；converter独立goto没有同一路由保护','D:D09,D:D12','validation/maps-probes.json'),
 ('Partial','图片URL/生成、icon搜索、目标尺寸来自template','图片失败可placeholder.jpg，icon无结果placeholder.svg；真实资产生成未跑','D:P03-ASSETS','validation/verify-res-p03-05.json'),
 ('Partial','images/Vision路径与图片下载；错误会warn并跳过图片','topic image布局不保证真实资产；未实跑Vision','D:P04-IMAGE-ANALYSIS,D:P04-IMAGE-ASSET','validation/verify-res-p04-02.json'),
 ('Partial','视觉类型固定分类与定位；URL/文件图像加载；图表可PNG/native','没有搜索/必要性算法；图像下载失败可建议文本；image-text是示意框','D:P05-D11,D:P05-D12','validation/maps-probes.json')],
'模板':[
 ('Partial','Brand/Style/Layout/Deck分层；typed slot及flat/structured输出规则','模板真值和完整metadata须显式；不是自动解析所有PPTX母版','D:P01-DEC-07,D:P01-DEC-19,D:P01-DEC-20','validation/verify-res-p01-04.json'),
 ('Partial','唯一generic starter三槽、四种token和CSS继承；三种canvas','非原生Master/Layout；不解析模板PPTX；只有16:9实测','D:D04,D:D05','validation/maps-probes.json'),
 ('Partial','16个默认模板、383布局；component/merged variants、theme、capacity模型','没有显式parent/extends；容量认证路径与静态模板不同；导出黑盒','D:P03-TEMPLATE,S:template-storage-and-schema,S:template-capacity-pipeline','validation/verify-res-p03-04.json'),
 ('Partial','5个template JSON颜色/字体/spacing/slideSize，Zod校验','不是PPTX母版/主题保真；缺模板拒绝','D:P04-TEMPLATE','validation/verify-res-p04-04-05.json'),
 ('Partial','6个theme token；PPTX解析11布局/58placeholder；template路线python-pptx','带旧slide模板KeyError(None)；独立theme关系漏读；无页模板仅子集可用','D:P05-D08,D:P05-D09','validation/maps-probes.json')],
'布局':[
 ('Partial','先语义拓扑再SVG几何；文本fit/样式锁；typed槽位导出约束','主机做几何；没有确定性全局评分器；不保证所有复杂PPT对象可原生化','D:P01-DEC-15,D:P01-DEC-17,D:P01-DEC-18,D:P01-DEC-20','validation/verify-res-p01-05.json'),
 ('Partial','Chromium computed DOM→inch IR；字体CDP/CSS识别；严格尺寸/底部阈值','单行宽+2%补偿；inlineSVG前置className错误；不是语义布局搜索','D:D05,D:D06,D:D07,D:D08','validation/maps-probes.json;validation/footer-revision.json'),
 ('Partial','有序layout顺序；无序LLM映射；Standard schema槽位；SmartHTML','非法索引随机替换，非评分；Smart安全启发式不是浏览器实测overflow','D:P03-LAYOUT,D:P03-SLOTS,D:P03-SMART','validation/verify-res-p03-03.json'),
 ('Partial','topic writer固定元素几何；HTML走PureLayout包装器/CSS子集','topic不执行flex；父子背景等语义有差异，长文本无完整容量求解','D:P04-TOPIC-RENDER,D:P04-HTML-STRUCTURE,D:P04-PPT-ADAPTER','validation/verify-res-p04-02.json;validation/verify-res-p04-04-05.json'),
 ('Partial','固定英寸坐标/简单算式和shrinkText；template slot映射','timeline最多5/process4、未记录损失；无候选检索/评分/容量测量','D:P05-D08,D:P05-D10','validation/maps-probes.json')],
'执行':[
 ('Observed','Quick SVG经原生builder输出3页文字/形状PPTX，并有PowerPoint只读渲染证据','不是全对象/Default/全编辑路径实测；主体规划是host','S:preview_and_native_export,D:P01-DEC-19,D:P01-DEC-20','validation/verify-res-p01-05.json'),
 ('Observed','真实DeepSeek6页HTML→固定1.1.37→PptxGenJS→LO/PDF→严格final complete','不是产品API；非native chart；外部visual JSON失败后显式走官方host审查','D:D15,D:D16,D:D17','validation/verify-official-six.json;validation/maps-probes.json'),
 ('Partial','Web/FastAPI/SSE→DB slides→export service→@presenton/export-core1.0.34','仅启动200和历史428；最终导出实现黑盒，未生成PPTX','D:P03-EXPORT,S:export-task-service,S:export-core','validation/smoke.json;validation/verify-res-p03-02.json'),
 ('Observed','HTML/topic结构探针→PptxGenJS原生text/shape；实际PPTX存在','无真实模型/Vision/PowerPoint渲染；包装器转换子集','D:P04-PPT-ADAPTER,D:P04-TOPIC-RENDER','validation/verify-res-p04-02.json;validation/verify-res-p04-04-05.json'),
 ('Observed','官方mock8页→JS PPTX；template可走Python；实际原生chart/table/notes子集','不是真AI生成；旧页模板失败；语言/数量/QA/低对比问题保留','D:P05-D01,D:P05-D12,D:P05-D14','validation/baseline-run.json;validation/maps-probes.json')],
'可编辑性':[
 ('Partial','实物Quick原生文本/形状；native chart/table parity与6项edit测试共26项通过','unsupported对象proxy；共享结构/atomic proxy修改拒绝；非全roundtrip','D:P01-DEC-20,D:P01-DEC-21,S:revision','validation/verify-res-p01-05.json'),
 ('Partial','6页各5原生文字shape；新实验原生表格，gradient为PNG','placeholder不消费；inlineSVG失败；无普通PPTX读改身份保存','D:D10,D:D11,D:D15','validation/verify-official-six.json;validation/maps-probes.json'),
 ('Partial','内部元素树含text/shape/table/chart/group/notes等，可在DB编辑','全部最终OOXML由外部export-core黑盒；没有对象实物/保真编辑验证','S:template-element-model,S:chat-edit-tools,D:P03-EXPORT','validation/verify-res-p03-05.json'),
 ('Partial','text/shape/image写入，chartData和speakerNotes未消费','chart layout名称不等于原生chart；无普通PPTX读取/身份保真编辑','D:P04-SLOT-BINDING,D:P04-PPT-ADAPTER','validation/verify-res-p04-04-05.json'),
 ('Partial','显式native charts、embedded workbook/table/notes实际写出','默认chart可能PNG；短series直接renderer补零；无任意PPTX原位编辑','D:P05-D08,D:P05-D12,D:P05-D13','validation/maps-probes.json')],
'QA':[
 ('Partial','SVG QualityChecker/preflight/postflight；selected parity/edit tests有证据','不同路线门控不同；edit receipt not-provided/stale仍exit0导出，不能当强阻断','D:P01-DEC-23,S:svg_quality_gate','validation/verify-res-p01-05.json'),
 ('Partial','HTML逐页/导出deck真看图、hash审查和6个strict检查；资源变更失效','只视觉/结构count/aspect；无事实或全面可编辑性QA；外部JSON集成未通过','D:D13,D:D14,D:D16,D:D17','validation/verify-official-six.json;validation/maps-probes.json'),
 ('Partial','输入/schema与SmartHTML safety/parser局部检查','Standard全deck事实/语义/视觉门禁Not found；没有生成QA实物','D:P03-SMART,D:P03-FACTS,D:P03-REVISION','validation/verify-res-p03-05.json'),
 ('Unsupported','tracked包装器只有解析/schema/output错误；没有真实生成后QA门控','源scope：Create/PureLayout/PPTAdapter；Pptx文件存在不表示视觉/事实通过','D:P04-OUTLINE,D:P04-PPT-ADAPTER','validation/verify-res-p04-04-05.json'),
 ('Partial','独立qa-visual与quality-score，LO/PDF/JPEG+bbox heuristic','生成不自动QA；strict实际27issues exit1；暗底低对比未标高风险；非事实/像素QA','D:P05-D14','validation/baseline-run.json;outputs/normal-qa/visual-qa-report.json')],
'修订':[
 ('Partial','主机改计划/SVG重QA导出；native edit source-backed proxy有局部保留测试','Default确认边界；复杂对象/共享master修改拒绝，非任意原件编辑','D:P01-DEC-24,S:revision','validation/verify-res-p01-05.json'),
 ('Partial','六页footer源修订、重渲染/审查/重建完成；旧源审查失效','全量新建，不是局部PPTX对象改写；没有自动repair agent','D:D13,D:D16','validation/footer-revision.json;validation/verify-official-six.json'),
 ('Partial','REST edit/derive与chat tools更新DB slide/component，模板导入另一路','无QA→RevisionPlan→保真原PPTX闭环；没有运行编辑实测','D:P03-REVISION,S:edit-derive-api,S:chat-edit-tools','validation/verify-res-p03-05.json'),
 ('Unsupported','固定CLI/Create流程没有旧PPTX读改或QA驱动修订入口','source scope已追踪CLI/PPTAdapter；逐页扩写不是修订闭环','S:CLI-ROUTES,S:CREATE-ROUTER,D:P04-CONTENT-FILL','validation/verify-res-p04-04-05.json'),
 ('Partial','旧deck JSON+指令重规划/重写；mock8→6页实物','不是旧PPTX原位改写；clarify裁剪无说明；theme缺失回退','D:P05-D07,D:P05-D09','validation/baseline-run.json;validation/maps-probes.json')],
'接口':[
 ('Partial','Agent Skill与项目、source、QA、导出/原生edit脚本CLI','固定调用链未见独立生成REST/API/MCP服务；host协议承担入口','S:route,S:project_setup,S:preview_and_native_export',''),
 ('Partial','官方CLI及两个visual MCP tools：review_slides/review_deck','MCP只源码定位、非生成服务；没有完整产品CLI/API/MCP统一入口','S:mcp,D:D01','validation/verify-official-six.json'),
 ('Partial','Next.js UI、FastAPI v1/v2、SSE/jobs、OpenAPI allowlist FastMCP','原范围排除的账号/SaaS功能不引入产品；生成接口尚未运行','D:P03-MODE,D:P03-MCP,S:direct-rest-v1,S:smart-rest-v2','validation/smoke.json'),
 ('Partial','命令行Create及库内engine/wrapper函数','tracked源码没有独立HTTP/MCP/统一cancel/resume；provider前置有配置要求','S:CLI-ROUTES,S:CREATE-ROUTER','validation/verify-res-p04-02.json'),
 ('Partial','CLI、JSON handler、POST /skill、MCP create_deck/revise_deck','HTTP/MCP仅源码；CLI mock通过不等于所有接口真实模型验证','S:ENTRY-CLI,S:ENTRY-HTTP,S:ENTRY-MCP-CREATE,S:ENTRY-MCP-REVISE','validation/baseline-run.json')],
'安全':[
 ('Partial','workflow限定来源、模板根、proxy编辑边界及显式no-AI/editable-only约束','Prompt/文件规则不是主机代码执行沙箱；依赖/网络安全未全面审计','D:P01-DEC-07,D:P01-DEC-12,D:P01-DEC-24','validation/verify-res-p01-05.json'),
 ('Partial','review renderer拒绝非跟踪file和远程URL；配置从环境取密钥','converter独立goto无同一路由防护；本地JS非全面沙箱；npm6 high提示未消除','D:D12,D:D13,S:config','validation/maps-probes.json;validation/environment-main-skill.txt'),
 ('Partial','SmartHTML清理/限制与export输出路径校验；HTTP认证门禁','实际仅历史428；不是全面SSRF/沙箱/提示注入保证','S:smart-prompt-and-validation,S:export-task-service','validation/verify-res-p03-02.json'),
 ('Partial','Zod模板/layout结构校验与HTML/CSS净化包装器','无统一untrusted运行沙箱证明；下载warn后跳图；仅局部源码措施','D:P04-TEMPLATE,D:P04-LAYOUT-LOAD,D:P04-HTML-CSS,D:P04-IMAGE-ASSET','validation/verify-res-p04-04-05.json'),
 ('Partial','request/schema与文件存在性校验；图片MIME/尺寸/URL局部规则','不是完整网络/执行隔离；安装7漏洞提示；来源与裁剪风险仍在','S:REQUEST-JSON,S:CLI-INPUT,D:P05-D11','validation/environment.json;validation/maps-probes.json')],
'许可':[
 ('Partial','固定根LICENSE为MIT','第三方代码/模板/图标/字体许可仍须逐项审核，不推定根许可证覆盖一切','L:LICENSE',''),
 ('Partial','固定根及Skill LICENSE为MIT；实际converter来自pptagent1.1.37','main许可不替代全部第三方依赖许可或资产分发审核','L:LICENSE,L:skills/pptagent/LICENSE,D:D15','validation/converter-source.json'),
 ('Partial','固定根LICENSE为Apache-2.0并有NOTICE','外部export-core/全部依赖/素材许可未逐项确认；账号功能不因此进入范围','L:LICENSE,L:NOTICE,D:P03-EXPORT',''),
 ('Partial','固定根LICENSE为MIT','依赖PureLayout/PptxGenJS/字体/素材分别审核，尚非复用合规决定','L:LICENSE,D:P04-PPT-ADAPTER',''),
 ('Partial','LICENSE AGPLv3、package.json AGPL-3.0-only，pyproject/lock根metadata Apache-2.0','声明冲突未解决；本比较不授权直接复制或裁定许可，交RES-032','L:LICENSE,L:package.json,L:pyproject.toml,L:package-lock.json','')]}
IMPACTS={
'输入':'复用多来源与任务模式边界；产品必须统一TaskSpec及原文/位置，不把简化CLI字段当完整解析。',
'内容理解':'所有项目均缺少已验证的全事实/冲突闭环；产品以可追溯SourceEvidence和FactConstraints执行，不以Prompt句子充当保证。',
'规划':'可参考P01确认/锁定、P03分阶段结构、P05校验repair；主机和模型内部候选不伪造为可解释trace。',
'分页':'保留硬页数与完整内容约束；上游钳制/跳页/静默裁剪均不直接沿用，需显式失败或授权重分配。',
'页面类型':'用语义intent与能力匹配连接页面类型；layout名称/HTML自由创作不替代类型分类与验收。',
'素材':'素材获取、来源许可、几何fit与native/fallback分开；下载失败和图片替代必须可追溯。',
'模板':'数据化槽位/几何/token后按能力路由；单starter、内部template JSON与原生PPTX母版不同，不能等同。',
'布局':'原生对象路线需对象类型/样式/几何契约与容量实测；不得复制各项目的固定容量常量作为产品政策。',
'执行':'已有P01原生SVG、P02HTML原生子集、P04结构写出、P05native chart/table/notes证据；选型需RES-032许可与依赖审核，不预选环境语言。',
'可编辑性':'OOXML对象存在、可打开、可交互编辑与保真往返分别验收；PNG回退与proxy须显式状态，不宣称全编辑。',
'QA':'采用源码/渲染/审查hash绑定的可追溯门控思路；产品还必须事实与可编辑性QA，advisory receipt不能冒充strict gate。',
'修订':'以局部对象范围/稳定身份/前后diff验收；JSON或HTML全量重建不自动满足普通PPTX保真编辑要求。',
'接口':'CLI/API/MCP共用任务与状态接口；只参考P03/P05接口分层，账号/计费等GOV-009排除项不复制。',
'安全':'隔离执行、资源路径/URL准入、secret注入及Prompt trust boundaries需产品级设计，局部sanitize不能当全面安全证明。',
'许可':'RES-032按模块和资产来源登记四种复用方式；P05冲突未解决前不得直接复制。比较文件只记录固定声明，不作法律裁定。'}
DEC={ 'P01':('project_decision_map.json','decision_nodes'),'P02':('decision-map.json','nodes'),'P03':('decision-map.json','nodes'),'P04':('decision-map.json','decisionNodes'),'P05':('ProjectDecisionMap.json','nodes')}
SI={p:(ROOT/'research'/p/PROJECTS[p][4]) for p in PROJECTS}
docs={};input_files={};catalog={};source_files={}
def doc(path):
 key=path.relative_to(ROOT).as_posix()
 if key not in docs:docs[key]=read(path);input_files[key]=sha(path)
 return docs[key]
def physical(project,path,lines=None,origin='fixed clone'):
 if project=='P02' and origin=='installed pptagent1.1.37':
  actual=CLONES/'P02-official-smoke/main-skill/.venv/lib/python3.11/site-packages/deeppresenter'/path
 else:actual=CLONES/project/path
 assert actual.is_file(),actual
 raw=actual.read_bytes();count=len(raw.decode('utf-8').splitlines());spans=[]
 if isinstance(lines,list) and len(lines)==2 and all(isinstance(x,int) for x in lines):spans=[lines]
 elif isinstance(lines,str):
  for match in re.finditer(r'(\d+)(?:\s*-\s*(\d+))?',lines):spans.append([int(match[1]),int(match[2] or match[1])])
 elif lines is None:spans=[[1,count]]
 else:raise ValueError(('unsupported line format',lines))
 assert spans and all(1<=a<=b<=count for a,b in spans),(actual,spans,count)
 key=f'{project}:{origin}:{path}';source_files[key]={'project':project,'origin':origin,'path':path,'local_path':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),'line_count':count}
 return {'source_file':key,'spans':spans}
def source_locations(project,obj):
 result=[]
 if project=='P01':
  for s in obj.get('source',[]):result.append(physical(project,s['file'],s['lines']))
 elif project=='P02':
  idx=doc(SI[project]);keys=obj.get('source_refs',[])
  for k in keys:
   r=idx['references'][k];f=idx['files'][r['file']]
   path='skills/pptagent/'+f['path'] if f['origin']=='main Skill' else f['path']
   result.append(physical(project,path,[r['start'],r['end']],f['origin'] if f['origin']!='main Skill' else 'fixed clone'))
 elif project=='P03':
  idx=doc(SI[project]);nodes={n['id']:n for n in idx['nodes']}
  for id in obj.get('sourceIndex',[]):result.extend(source_locations(project,nodes[id]))
  if 'path' in obj:
   paths=obj['path'].split('; ')
   for path in paths:result.append(physical(project,path,obj.get('lines')))
  if obj.get('kind')=='external_black_box' or obj.get('id')=='export-core':result.append({'external_black_box':obj})
 elif project=='P04':
  sources=obj.get('sources',[obj] if 'file' in obj else [])
  for s in sources:result.append(physical(project,s['file'],s.get('lines')))
 elif project=='P05':
  sources=obj.get('source',[obj] if 'path' in obj else [])
  for s in sources:result.append(physical(project,s['path'],[s['line_start'],s['line_end']]))
 return result
def anchor(project,selector):
 key=f'{project}:{selector}'
 if key in catalog:return key
 mode,id=selector.split(':',1)
 if mode=='L':
  catalog[key]={'project':project,'kind':'license declaration','locations':[physical(project,id)],'scope':'固定文件声明；未授权复用，未审计全部第三方'};return key
 path=ROOT/'research'/project/(DEC[project][0] if mode=='D' else PROJECTS[project][4]);d=doc(path)
 field=DEC[project][1] if mode=='D' else 'nodes'
 if project=='P02' and mode=='S':
  # Read all references of one tracked module or call graph node for source-only boundaries.
  if id=='mcp':obj={'source_refs':['mcp:module']}
  elif id=='config':obj={'source_refs':['config:module']}
  else:raise ValueError(id)
  pointer='/references/'+obj['source_refs'][0]
 else:
  i,obj=next((i,n) for i,n in enumerate(d[field]) if n['id']==id);pointer=f'/{field}/{i}'
 loc=source_locations(project,obj);assert loc,(project,selector,obj)
 catalog[key]={'project':project,'kind':'source or prompt rule','research_file':path.relative_to(ROOT).as_posix(),'json_pointer':pointer,'node_id':id,'node':obj,'locations':loc}
 return key
def build():
 manifests={}
 for p,(name,commit,_,_,_,license) in PROJECTS.items():
  actual=subprocess.check_output(['git','-C',str(CLONES/p),'rev-parse','HEAD'],text=True).strip();assert actual==commit,(p,actual)
  manifests[p]={'name':name,'fixed_commit':commit,'clone':str(CLONES/p),'license_observed':license,'runtime_scope':'source + prior runtime subset; no new provider calls','remaining_verification':'P03 five VERIFY still in progress, no generation/export evidence' if p=='P03' else 'Full product AC and object roundtrip remain unexecuted'}
 dimensions=[]
 for dimension,items in ROWS.items():
  assert len(items)==5
  cells=[]
  for p,(status,finding,limit,ids,evidence) in zip(PROJECTS,items):
   evidence_paths=[]
   for value in evidence.split(';'):
    if not value:continue
    path=ROOT/'research'/p/value;assert path.is_file(),path
    rel=path.relative_to(ROOT).as_posix();input_files[rel]=sha(path);evidence_paths.append(rel)
   proof='source + startup/auth-gate history; no generation/export' if p=='P03' and evidence_paths else ('source + recorded runtime subset' if evidence_paths else 'source-only; no runtime support claim')
   cells.append({'project':p,'status':status,'finding':finding,'limit':limit,'source_anchors':[anchor(p,id) for id in ids.split(',')],'runtime_evidence':evidence_paths,'proof_level':proof,'product_status':'not implemented/accepted by this research'})
  dimensions.append({'dimension':dimension,'comparisons':cells,'implementation_consequence':IMPACTS[dimension]})
 ns={};exec((ROOT/'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns)
 matrix,_=ns['read'](ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
 for r in range(12,37):assert matrix['需求主表'][f'N{r}'][1]=='已完成',(r,matrix['需求主表'][f'N{r}'])
 baseline={s:{str(r):[matrix[s].get(c+str(r),('',None))[1] for c in 'ABCDEFGHIJKLMNOP'] for r in nums} for s,nums in [('需求主表',[37]),('可执行任务',[64,65])]}
 original=baseline['需求主表']['37'];assert original[0]=='RES-031' and original[8]=='RES-P01-05~RES-P05-05'
 write('baseline-rows.json',baseline)
 result={'artifact_type':'CrossProjectMatrix','requirement_id':'RES-031','task_ids':['TASK-RES-031','VERIFY-RES-031'],'scope':'原15维度×5固定项目；证据结论不是产品架构/技术栈/全能力或复用许可批准','status_definition':{'Observed':'实际制品/运行仅证明所述子集','Partial':'源码/部分运行存在，但没有完整维度能力证据','Unsupported':'追踪路线缺失能力或明确拒绝','Not found':'固定追踪源码未发现独立实现；主机/模型黑盒不算该算法已实现'},'projects':manifests,'dimensions':dimensions,'source_catalog':'source-catalog.json','input_manifest':'input-manifest.json','consumers':['RES-032模块复用/许可决定','RES-033测试资产来源索引','后续架构与DEC实现；不得将比较标记冒充产品验收'],'missing_evidence':['P03五个VERIFY进行中；仅startup/source/历史428，不是generation成功','所有项目全对象/全系统AC未验证','P05许可证冲突未解决','P02 external visual JSON与inline SVG失败未消除'],'overall':'没有单一候选有全部需求证据；以明确来源和损失边界组合选择，拒绝静默裁剪/补零/随机替代与把黑盒输出当可编辑保证'}
 write('CrossProjectMatrix.json',result);write('source-catalog.json',{'anchors':catalog,'source_files':source_files})
 write('input-manifest.json',{'research_files_sha256':input_files,'scope':'only consumed maps and prior evidence; frozen after comparison; workbook states updated separately'})
 header='# 五个项目横向对照（RES-031）\n\n覆盖原15个维度，每个均有5项目源码/运行证据。这里只比较固定快照；不选产品语言/运行时，不复制代码、不批准许可证复用、不修改DEC或AC状态。\n\n**进度纠正：** 25项主研究已完成；P03五个VERIFY仍在进行中。其生成/导出/编辑未运行，历史HTTP428不是当前阻塞确认。继续RES-031依据其已完成的源码研究，不提升为实测成功，也不要求全验证作为所有实现的人为前置。\n\n## 固定来源与证据等级\n\n'
 text=header+'\n'.join(f'- {p} {v["name"]}：`{v["fixed_commit"]}`；{v["license_observed"]}；{v["remaining_verification"]}。' for p,v in manifests.items())+'\n\nObserved只证明列明实物子集；Partial是相关机制/子集；Unsupported/Not found保留范围，不能冲销目标需求。Prompt规则、主机黑盒、库潜在能力、实测及产品验收分别记录。所有定位及hash见[source-catalog](source-catalog.json)，消费文件锁见[input-manifest](input-manifest.json)。\n\n'
 for d in dimensions:
  text+=f'## {d["dimension"]}\n\n| 项目 | 状态 | 事实 | 边界 |\n|---|---|---|---|\n'
  for c in d['comparisons']:text+=f'| {c["project"]} | {c["status"]} | {c["finding"]} | {c["limit"]} |\n'
  text+='\n来源：\n\n'
  for c in d['comparisons']:
   text+=f'- {c["project"]}：`'+ '`, `'.join(c['source_anchors'])+'`；运行记录：'+('; '.join(f'[{Path(e).name}](../../{e})' for e in c['runtime_evidence']) or '仅源码')+'。\n'
  text+='\n实现影响：'+d['implementation_consequence']+'\n\n'
 text+='## 选型输入与结束条件\n\n- 现有可编辑子集实物可支持下一步选择：P01 Quick原生SVG、P02 HTML文字/表格、P04 topic/HTML原生子集、P05显式chart/table/notes。能力不可互相推断，P05许可冲突不得越过。\n- 强参考点：P01来源/类型/锁定/原生编辑边界，P02输入与审查hash门控，P03内部模板Schema和接口分层，P04数据化模板/版式，P05JSON校验及原生对象实验。模块复用方式由RES-032登记；P03账号等GOV-009排除功能不移入产品。\n- 不直接沿用：无报告裁剪、分页钳制、失败跳页、随机layout替代、无说明补零、把PNG当全编辑、把缺失/过期receipt当严格通过。\n- 验收：15维度每项5项目，75单元均有物理源码/Prompt范围或明确黑盒定位；正常/边界/失败用已有实物/错误和新的比较校验关联，损失/未知/历史门禁保留。达到原研究验收后进入RES-032/033，不重复安装生成。\n'
 (HERE/'CrossProjectMatrix.md').write_text(text,encoding='utf-8')
 print(json.dumps({'dimensions':len(dimensions),'cells':sum(len(d['comparisons']) for d in dimensions),'source_anchors':len(catalog),'physical_source_files':len(source_files),'inputs':len(input_files)},ensure_ascii=False))
if __name__=='__main__':build()
