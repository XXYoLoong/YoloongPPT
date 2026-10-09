"""RES-032/033: bounded module decisions and fixture provenance, no upstream copying."""
import ast,collections,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];CLONES=Path('F:/YoloongPPT-Research')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,v):(HERE/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cross=read(ROOT/'research/cross-project/CrossProjectMatrix.json')
methods={'直接复用':'只复制已逐文件审核的明确来源；保留许可/版权和变化记录，确认目标接口兼容。登记不等于代码已接入。','抽象复用':'采用分层、约束或门控思路；按本项目基线独立实现，不复制源代码、Prompt、原样schema/版式或素材。','仅参考':'用于能力/风险/失败行为比较；不复制实现或资产，也不机械翻译成目标代码。','不采用':'不引入当前产品路线；不取消基线必须支持的能力，另行实现或选用已明确许可的替代。'}
MIT=['LICENSE'];LICENSES={'P01':['LICENSE','skills/ppt-master/LICENSE'],'P02':['LICENSE','skills/pptagent/LICENSE'],'P03':['LICENSE','NOTICE'],'P04':['LICENSE'],'P05':['LICENSE','package.json','pyproject.toml','package-lock.json']}
LICENSE_NAMES={'P01':'MIT (code); third-party assets separate','P02':'MIT (main/Skill); dependency separate','P03':'Apache-2.0 + NOTICE; dependencies/assets separate','P04':'MIT (code); dependencies separate','P05':'Unresolved: LICENSE AGPLv3/package AGPL-3.0-only vs pyproject/lock Apache-2.0'}
POLICIES={'P01':'复制已审核代码时保留MIT许可与Hugo He版权。icons/sounds/geometry data的独立声明不由MIT替代。','P02':'Skill复制须保留其MIT许可/版权；installed converter与所有第三方依赖单独审核，不从main MIT推导。','P03':'若复制Apache内容须附许可证、保留适用通知/NOTICE，并对修改作明显说明；本次只抽象/参考，不搬整应用及第三方分发物。','P04':'若复制MIT代码/JSON应保留许可与peterfei版权；PureLayout等依赖、字体/图片独立审核。','P05':'冲突未解决且没有确定copyleft合规方案，禁止直接复制、移植或改写翻译源代码/Prompt/schema/assets；本次仅参考研究发现，不调用其代码作为产品后端。'}
LEGAL=[{'id':'MIT','title':'OSI MIT license','url':'https://opensource.org/license/mit','sections':['copyright/permission notice condition'],'summary':'复制软件或实质部分时保留版权和许可通知。'}, {'id':'Apache-2.0','title':'ASF Apache License 2.0','url':'https://www.apache.org/licenses/LICENSE-2.0','sections':['4(a)-(d)','6'],'summary':'分发条件包括许可副本、修改说明、保留适用通知/NOTICE；没有商标授权。'}, {'id':'AGPL-3.0-only','title':'SPDX AGPL v3 license text','url':'https://spdx.org/licenses/AGPL-3.0-only.html','sections':['2','5','6','13'],'summary':'修改/分发covered work与网络交互有对应源代码义务；输出仅在内容构成covered work时受该许可覆盖，不能只据生成工具判断输出许可。','fetch_boundary':'GNU官方网站本次超时；改用SPDX维护文本，并与固定P05 LICENSE的第2/13条核对。'}]
files={}
def upstream(p,path):
 key=p+':'+path
 if key in files:return key
 actual=CLONES/p/path;assert actual.is_file(),actual
 blob=subprocess.check_output(['git','-C',str(CLONES/p),'show',cross['projects'][p]['fixed_commit']+':'+path])
 assert blob.replace(b'\r\n',b'\n')==actual.read_bytes().replace(b'\r\n',b'\n'),actual
 files[key]={'project':p,'origin':'fixed upstream','path':path,'local_path':str(actual),'commit':cross['projects'][p]['fixed_commit'],'sha256':sha(actual),'bytes':actual.stat().st_size,'source_url':'https://github.com/'+{'P01':'hugohe3/ppt-master','P02':'icip-cas/PPTAgent','P03':'presenton/presenton','P04':'peterfei/ai-agent-ppt','P05':'lijunliu-gh/auto-ppt-engine'}[p]+'/blob/'+cross['projects'][p]['fixed_commit']+'/'+path};return key
def local(p,path,producer):
 key='local:'+path
 if key in files:return key
 actual=ROOT/path;assert actual.is_file(),actual
 files[key]={'project':p,'origin':'project research artifact','path':path,'local_path':str(actual),'sha256':sha(actual),'bytes':actual.stat().st_size,'producer':producer,'source_url':None,'rights_boundary':'生成软件许可不自动决定输出权利；本次只索引已存在研究产物，不批准产品分发'};return key
# ID, project, module, reuse method, source files, intended consumer, reason and scope.
MODULES=[
 ('R01','P01','opaque XML relationship-attribute guard','直接复用',['skills/ppt-master/scripts/pptx_shapes/xml_safety.py'],'未来OOXML Adapter的片段关系复制安全检查（PPT-030）','单文件仅stdlib ElementTree；定位关系QName，避免把part-local关系当普通属性','只判断关系属性存在，不是XML parser沙箱、关系重绑定或全PPTX安全保证'),
 ('R02','P01','root SVG canvas contract','直接复用',['skills/ppt-master/scripts/svg_to_pptx/canvas_contract.py'],'未来SVG原生Adapter的页面尺寸/视口检查','单文件stdlib；已独立定义canvas错误；可与TaskSpec几何接口连接','源规则zero-origin与EMU范围必须能力化；不可替代用户全部比例/约束；目标语言/接口未选前不复制'),
 ('R03','P01','source roles, communication/spec lock and roster','抽象复用',['skills/ppt-master/references/plan-core.md','skills/ppt-master/workflows/routing.md'],'统一来源/TaskSpec/DEC规划、页面冻结与trace','保持事实、模式、页序与确认边界，独立实现契约消费接口','不能引入上游固定确认流程来覆盖本项目默认与硬约束，也不复制Prompt'),
 ('R04','P01','native SVG export / edit proxy / chart parity','仅参考',['skills/ppt-master/scripts/tests/test_native_chart_table_parity.py','skills/ppt-master/scripts/pptx_ooxml/edit_safety.py'],'原生对象、roundtrip及局部修订的验收设计','已有Quick与26项selected tests说明可实现子集；完整依赖链尚未选定','不整包vendoring exporter；共享master/proxy拒绝与advisory receipt保留为测试边界'),
 ('R05','P01','bundled icons, sounds and branded decks','不采用',['skills/ppt-master/templates/icons/THIRD_PARTY_NOTICES.md','skills/ppt-master/templates/sounds/THIRD_PARTY_NOTICES.md'],'后续素材库必须独立许可/来源登记','包含CC BY/CC0/MIT与品牌商标等独立条件，不由根MIT统一覆盖','不复制整个库或品牌模板；媒体/图标功能仍在产品范围，另选来源'),
 ('R06','P02','source/render/review/build freshness gate','抽象复用',['skills/pptagent/scripts/pptagent_runtime/core.py'],'QA、执行trace和RevisionPlan freshness','将输入/资源/输出hash绑定审查，独立实现任务状态与失效门控','需要产品事实/可编辑性QA，不复制源码或把六项检查当全QA'),
 ('R07','P02','visual review payload/config boundary','抽象复用',['skills/pptagent/scripts/pptagent_runtime/visual.py','skills/pptagent/scripts/pptagent_runtime/config.py'],'结构化视觉审查与模型secret注入接口','严格issue字段、pass不可含major、env name边界可独立实现','不复制Prompt；外部string slide失败需要产品明确错误，不自动吞掉'),
 ('R08','P02','installed HTML converter 1.1.37','不采用',['skills/pptagent/requirements.txt'],'当前首条写入路线不依赖此converter','native chart缺口、inlineSVG bug、PNG降级与单独依赖许可/安全未解决','其依赖与main不是同一版本/许可证明；HTML输入/生成能力不从基线移除'),
 ('R09','P02','single starter and visual MCP packaging','仅参考',['skills/pptagent/assets/slide-template.html','skills/pptagent/scripts/visual_mcp.py'],'最小页面fixture与MCP审查分层','可参考小型工具封装；不是完整生成服务或模板族','不把其MCP两个工具当产品CLI/API/MCP交付'),
 ('R10','P03','template element/layout/schema separation','抽象复用',['servers/fastapi/templates/v2/models/elements.py','servers/fastapi/templates/v2/models/layouts.py','servers/fastapi/templates/v2/schema.py'],'模板IR、语义槽位与几何/容量接口','区分元素、layout与结构化内容，按本项目现有契约独立实现','不复制383布局/1002资产或依赖它的外部导出能力'),
 ('R11','P03','REST/SSE/MCP/editor service layering','抽象复用',['servers/fastapi/mcp_server.py','servers/fastapi/services/chat/tools.py'],'共用任务状态的CLI/API/MCP与局部修订入口','分层与allowlist思想可用；源调用依赖DB而非PPTX原件','不复制账号/产品业务、Prompt/工具实现；保真PPTX编辑另验收'),
 ('R12','P03','external @presenton/export-core backend','不采用',['scripts/run-presentation-export.mjs','servers/fastapi/services/export_task_service.py'],'首条执行后端需已知实现/依赖与真实对象证据','固定包装器可定位，但实际外部制品是黑盒；许可/实现/对象实物不足','不能把Apache根许可或内部元素树当外部exporter许可/完整可编辑性保证'),
 ('R13','P03','account/auth application subsystem','不采用',['servers/fastapi/api/v1/auth/router.py'],'GOV-009排除项','当前范围不包含账号/计费/多租户等，不复制该应用业务','产品CLI/API/MCP仍必须实现；不能把核心接口一并排除'),
 ('R14','P04','JSON template tokens/layout slots','抽象复用',['src/core/template/template-manager.ts','src/core/engine/layout-loader.ts','src/core/engine/slide-renderer.ts'],'TPL/AST页面类型与布局registry','独立设计typed slots、token、适用性和几何','不沿用缺layout跳页、固定容量、未消费chart/notes的行为'),
 ('R15','P04','topic writer and PureLayout adapter','仅参考',['src/core/engine/pptx-builder.ts','src/core/engine/ppt-adapter.ts'],'原生对象写入边界/回归样例','有native text/shape子集实物；可用于抽象test oracle','不整包采用：静默bullet丢失、无QA/保真编辑；依赖许可另查'),
 ('R16','P05','planner/repair/schema/assets','仅参考',['python_backend/smart_layer.py','deck-schema.json'],'来源/分页/Schema错误与裁剪的独立测试设计','保留正反例需求和观测，不采用源表达；许可冲突未解决','不得直接复制、移植或机械翻译源代码/Prompt/Schema；按本项目基线独立实现'),
 ('R17','P05','dual renderer/native chart/table/notes','不采用',['python_backend/pptx_renderer.py','generate-ppt.js'],'选择其他明确许可的底层原生对象库实现同一能力','AGPL conflict、旧slide删除bug、短series补零/内容损失；不作为产品依赖','原生chart/table/notes仍必须支持，不得以不采用取消范围'),
 ('R18','P05','independent QA/revision mock behavior','仅参考',['python_backend/visual_qa.py','tests/test_visual_qa.py','tests/test_smart_layer.py'],'产品QA/局部修订的失效/损失测试','只参考问题类别与既有实验事实，独立编写测试','bbox不是事实/像素QA；不复制AGPL测试或mock数据为产品golden')]
# Fixture references are exact files or declared groups. No upstream content is copied.
# project, category, origin/path, relation to current modules, reuse choice, rights, executed evidence.
FIXTURES=[
 ('P01','QA cases','upstream','skills/ppt-master/scripts/tests/test_native_chart_table_parity.py',['R04'],'仅参考','MIT code; imports/fixtures separately; recreate product assertions','research/P01/validation/verify-res-p01-05.json'),
 ('P01','QA cases','upstream','skills/ppt-master/scripts/tests/test_edit_native_batch_b.py',['R04'],'仅参考','MIT code; selected six tests only, not complete suite','research/P01/validation/verify-res-p01-05.json'),
 ('P01','schemas','upstream','skills/ppt-master/templates/schemas/design_spec.schema.json',['R03'],'仅参考','MIT declaration; project schema differs; do not overwrite own contracts',''),
 ('P01','schemas','upstream','skills/ppt-master/templates/schemas/spec_lock.schema.json',['R03'],'仅参考','MIT declaration; no automatic product protocol equivalence',''),
 ('P01','templates','upstream','skills/ppt-master/templates/tables/comparison_matrix.svg',['R04'],'仅参考','root/Skill MIT declaration only; embedded font/brand/media must be checked before copying',''),
 ('P01','PPTX','local','research/P01/projects/p01_hello_world_20261007/exports/p01-hello-world.pptx',['R04'],'仅参考','project research output; not covered automatically by generator MIT; inspect content before distribution','research/P01/validation/verify-res-p01-05.json'),
 ('P01','screenshots','local','research/P01/projects/p01_hello_world_20261007/validation/native-render/slide-01.png',['R04'],'仅参考','PowerPoint research render of prior source/output; no third-party asset blanket clearance','research/P01/validation/verify-res-p01-05.json'),
 ('P01','golden cases','local','research/P01/validation/p01-boundary-tests.json',['R04'],'仅参考','project-owned observation metadata; compare outcomes, do not copy upstream tests','research/P01/validation/verify-res-p01-05.json'),
 ('P02','templates','upstream','skills/pptagent/assets/slide-template.html',['R09'],'仅参考','Skill MIT; generic HTML starter, no PPTX master/layout capability',''),
 ('P02','QA cases','upstream','skills/pptagent/tests/test_workflow.py',['R06'],'仅参考','Skill MIT test code; full suite not executed here; rebuild hash gate tests independently','research/P02/validation/maps-probes.json'),
 ('P02','QA cases','upstream','skills/pptagent/tests/test_visual_mcp.py',['R09'],'仅参考','Skill MIT; MCP session not executed; reference only',''),
 ('P02','schemas','upstream','skills/pptagent/references/task-contract.md',['R09'],'仅参考','Skill MIT documentation contract, not a formal JSON Schema',''),
 ('P02','PPTX','local','research/P02/outputs/official-six/answer.pptx',['R06','R08'],'仅参考','real model research output with saved public prompt/response; generation license does not itself license output','research/P02/validation/verify-official-six.json'),
 ('P02','screenshots','local','research/P02/outputs/official-six/qa/deck/page-01.jpg',['R06'],'仅参考','research LO/PDF render; trace source deck, no product asset import','research/P02/validation/verify-official-six.json'),
 ('P02','golden cases','local','research/P02/validation/maps-probes.json',['R06','R08'],'仅参考','project-owned result metadata; negative SVG/resource/staleness cases retained','research/P02/validation/maps-probes.json'),
 ('P03','QA cases','upstream','servers/fastapi/tests/unit/test_template_api.py',['R10'],'仅参考','Apache-2.0 root + NOTICE; dependencies/embedded fixtures separately assessed; not executed','research/P03/validation/verify-res-p03-05.json'),
 ('P03','QA cases','upstream','servers/fastapi/tests/integration/test_presentation_generation_flow.py',['R11'],'仅参考','Apache-2.0 code; integration tests not executed, export core external','research/P03/validation/verify-res-p03-05.json'),
 ('P03','golden cases','upstream','servers/fastapi/tests/regression/snapshots/outline_generation.json',['R10'],'仅参考','Apache root declaration; snapshot content/provider output rights need separate clearance; no copy approval',''),
 ('P03','templates','upstream','templates/modern/template.json',['R10'],'仅参考','Apache root declaration; template/images/fonts provenance not universally cleared; no copy approval','research/P03/validation/verify-res-p03-04.json'),
 ('P03','schemas','upstream','servers/fastapi/templates/v2/models/layouts.py',['R10'],'仅参考','Apache-2.0 code model, not JSONSchema asset; independent product schema implementation',''),
 ('P03','screenshots','upstream','servers/nextjs/public/create_presentation_card_1.png',['R13'],'不采用','root license does not establish artwork/brand/font rights; exclude branded UI asset',''),
 ('P04','QA cases','upstream','tests/unit/pptx-builder.test.ts',['R15'],'仅参考','MIT code; source-located test suite, not executed here; product test independently rebuilt',''),
 ('P04','QA cases','upstream','tests/unit/layout-loader.test.ts',['R14'],'仅参考','MIT code; do not infer test execution from source existence',''),
 ('P04','templates','upstream','src/templates/tech/template.json',['R14'],'仅参考','MIT-declared JSON token fixture; no external media copied','research/P04/validation/verify-res-p04-04-05.json'),
 ('P04','templates','upstream','src/layouts/chart.layout.json',['R14'],'仅参考','MIT-declared slot layout; chart name does not mean native chart capability','research/P04/validation/verify-res-p04-04-05.json'),
 ('P04','PPTX','local','research/P04/validation/template-normal.pptx',['R15'],'仅参考','project research structural fixture output; no full visual/PowerPoint/product acceptance','research/P04/validation/verify-res-p04-04-05.json'),
 ('P04','golden cases','local','research/P04/validation/verify-res-p04-04-05.json',['R14','R15'],'仅参考','project-owned outcomes; 56 omitted bullet lines remain negative oracle','research/P04/validation/verify-res-p04-04-05.json'),
 ('P05','QA cases','upstream','tests/test_template_engine.py',['R17'],'仅参考','AGPL/metadata conflict unresolved; reference behaviors only, no code/fixture copy',''),
 ('P05','QA cases','upstream','tests/test_visual_qa.py',['R18'],'仅参考','AGPL/metadata conflict unresolved; no direct copying',''),
 ('P05','schemas','upstream','deck-schema.json',['R16'],'仅参考','AGPL/metadata conflict; do not copy Schema expression into product contracts',''),
 ('P05','templates','upstream','assets/themes/business-clean.json',['R17'],'仅参考','AGPL/metadata conflict; no theme-token copy; choose independent brand/style',''),
 ('P05','golden cases','upstream','examples/inputs/sample-source-brief.md',['R16'],'仅参考','AGPL root declaration/content rights not separately clear; create original source text',''),
 ('P05','PPTX','local','research/P05/outputs/maps-probes/native-objects.pptx',['R17'],'仅参考','generated mock research output; cannot infer free distribution or AGPL solely from generator; reference native object structure only','research/P05/validation/maps-probes.json'),
 ('P05','screenshots','local','research/P05/outputs/normal-qa/contact-1.png',['R18'],'仅参考','research render/underlying mock output; no product-media clearance','research/P05/validation/verify-res-p05-01-02.json'),
 ('P05','golden cases','local','research/P05/validation/maps-probes.json',['R16','R17','R18'],'仅参考','project-owned observed outcomes; do not copy original code/prompt/mock text','research/P05/validation/maps-probes.json')]
def build():
 modules=[]
 for id,p,name,method,paths,consumer,reason,limit in MODULES:
  refs=[upstream(p,s) for s in paths];lic=[upstream(p,s) for s in LICENSES[p]]
  dependency_scope='not copied; only conceptual/test observations retained'
  imports=[]
  if method=='直接复用':
   tree=ast.parse((CLONES/p/paths[0]).read_text(encoding='utf-8'))
   imports=sorted({a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}|{n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module})
   assert all(i in sys.stdlib_module_names or i=='__future__' for i in imports),imports
   dependency_scope='AST inspected: stdlib imports only; no third-party package or data payload imported by this file'
  modules.append({'id':id,'project':p,'module':name,'method':method,'source_files':refs,'license_files':lic,'license_observed':LICENSE_NAMES[p],'obligations':POLICIES[p],'consumer':consumer,'reason':reason,'limits':limit,'copy_permission':'eligible only for these exact MIT files with notices and confirmed compatible target interface' if method=='直接复用' else 'no source/asset copying under this decision','dependencies':dependency_scope,'imports':imports,'implementation_state':'registry decision only; no source imported into product','unknown_rights':'No implicit clearance for adjacent third-party assets/dependencies','cross_project_evidence':'research/cross-project/CrossProjectMatrix.json'})
 assets=[]
 for i,(p,kind,origin,path,related,choice,rights,evidence) in enumerate(FIXTURES,1):
  key=upstream(p,path) if origin=='upstream' else local(p,path,evidence)
  if evidence:assert (ROOT/evidence).is_file(),evidence
  status='source located; not executed'
  if evidence and p!='P03':status='existing selected research observation; not whole-suite/product acceptance'
  assets.append({'id':f'FIX-{i:03d}','project':p,'kind':kind,'source_file':key,'related_reuse_ids':related,'reuse_method':choice,'license_files':[upstream(p,s) for s in LICENSES[p]],'license_and_rights':rights,'copy_state':'not copied by this task; reference/recreate only','execution_evidence':evidence or None,'execution_status':status,'execution_boundary':'evidence describes its original selected scope, not complete asset/test execution; P03 reports are static source research, not generation/test execution','test_consumer':'future product regression/QA corpus; no fixture is product golden until independent scope and rights review'})
 # Separate third-party declarations explicitly located, never inherited from repository license.
 third=[{'project':'P01','kind':'icons','source_file':upstream('P01','skills/ppt-master/templates/icons/THIRD_PARTY_NOTICES.md'),'declaration':'CHUNK CC BY4.0, Tabler/Phosphor MIT, Simple Icons CC0 + individual brand/trademark conditions','decision':'not adopted; per-asset review required'}, {'project':'P01','kind':'sounds','source_file':upstream('P01','skills/ppt-master/templates/sounds/THIRD_PARTY_NOTICES.md'),'declaration':'Kenney CC0 sources and local transcodes','decision':'not adopted; retain per-file provenance if selected later'}, {'project':'P01','kind':'preset geometry data','source_file':upstream('P01','skills/ppt-master/scripts/pptx_shapes/data/NOTICE.md'),'declaration':'Apache POI data Apache2 + OpenXML SDK list MIT; separate notices/files','decision':'not copied by the approved small helper decisions'}, {'project':'P03','kind':'bundled dependencies','source_file':upstream('P03','NOTICE'),'declaration':'large package-specific notice collection, not one universal Apache grant','decision':'no dependency bundle copied; choose product dependencies separately'}]
 inventory=collections.Counter(a['project'] for a in assets)
 facts={'P03':'No generated PPTX/screenshots or successful generation golden in research; five VERIFY remain in progress. Upstream UI screenshot is source artwork, not a research export screenshot.','P04':'No research render screenshot identified in current evidence; structural PPTX and QA metadata only.','P02':'Task contract is Markdown + function checks, not full formal planner JSONSchema.'}
 registry={'artifact_type':'ReuseDecisionRegistry','requirement_id':'RES-032','task_id':'TASK-RES-032','methods':methods,'projects':cross['projects'],'modules':modules,'third_party_boundaries':third,'legal_sources':LEGAL,'license_interpretation':'module-scoped engineering reuse decision based on fixed declarations and license text, not blanket distribution approval or a resolution of upstream conflicting rights','product_license':'not selected; this task does not assign a product license','consumer':'architecture record, adapter/module implementation and future attribution inventory; direct-source adoption only after target interface selected'}
 fixture={'artifact_type':'ResearchFixtureIndex','requirement_id':'RES-033','task_id':'TASK-RES-033','assets':assets,'coverage_by_project':dict(inventory),'coverage_by_kind':dict(collections.Counter(a['kind'] for a in assets)),'explicit_gaps':facts,'scope':'bounded proposed fixtures across all five projects, not blanket inventory/rights clearance for every repository asset','consumer':'product test design/QA/future regression fixture selection; original cases independently authored before use, no source-less copy'}
 write('ReuseDecisionRegistry.json',registry);write('ResearchFixtureIndex.json',fixture);write('source-manifest.json',{'source_files':files,'cross_matrix_sha256':sha(ROOT/'research/cross-project/CrossProjectMatrix.json'),'cross_validation_sha256':sha(ROOT/'research/cross-project/validation.json')})
 ns={};exec((ROOT/'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns);data,_=ns['read'](ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
 assert data['需求主表']['N37'][1]=='已完成'
 baseline={s:{str(r):[data[s].get(c+str(r),('',None))[1] for c in 'ABCDEFGHIJKLMNOP'] for r in nums} for s,nums in [('需求主表',[38,39]),('可执行任务',[66,67])]};write('baseline-rows.json',baseline)
 text='# 模块复用与测试资产来源（RES-032 / RES-033）\n\n只登记拟复用模块与有来源资产，不引入产品实现或选择产品语言/运行时。消费已完成RES-031；范围仍以V0.3基线为准。\n\n## 许可依据\n\n复制MIT实质内容需保留版权及许可通知。[OSI MIT](https://opensource.org/license/mit)\n\nApache分发须附许可、保留适用通知/NOTICE并说明修改；不因此获得商标权。[ASF Apache2第4/6条](https://www.apache.org/licenses/LICENSE-2.0)\n\nAGPL covered work的修改/分发与网络交互需考虑对应源代码条件；输出只在其内容构成covered work时覆盖，不能直接按生成工具判断输出许可。[AGPL文本第2/5/6/13条](https://spdx.org/licenses/AGPL-3.0-only.html)\n\nP05许可声明冲突未被本研究裁定。当前工程决定是仅参考/不采用，禁止直接复制或机械翻译源表达。是否将来采用需明确实际许可与合规方式；当前首条产品链路可以使用其他明确许可组件，不被此阻塞。\n\n## 模块决定\n\n| ID | 项目/模块 | 方式 | 消费位置与理由 | 边界 |\n|---|---|---|---|---|\n'
 for m in modules:text+=f'| {m["id"]} | {m["project"]} / {m["module"]} | {m["method"]} | {m["consumer"]}；{m["reason"]} | {m["limits"]} |\n'
 text+='\n仅R01/R02两份明确MIT、stdlib文件具备限定直接复制资格；还须选定兼容接口并附完整许可/版权，尚未接入产品。其余抽象/参考不复制源、Prompt、schema或资源。原exporter整包依赖/字体/第三方data不是这两份文件的审核范围。\n\n## 测试资产登记\n\n| ID | 项目 | 类型 | 来源文件 | 方式/权利边界 |\n|---|---|---|---|---|\n'
 for a in assets:text+=f'| {a["id"]} | {a["project"]} | {a["kind"]} | `{files[a["source_file"]]["path"]}` | {a["reuse_method"]}；{a["license_and_rights"]} |\n'
 text+='\n## 来源与未执行边界\n\n- 每文件路径、固定commit、Git内容/本地实物hash、许可文件及模块绑定见[source-manifest](source-manifest.json)、[模块JSON](ReuseDecisionRegistry.json)及[资产JSON](ResearchFixtureIndex.json)。没有复制新上游代码、资源或既有生成物。\n- P01已运行的26项selected测试仅按原报告认定；源测试文件存在不代表全文件测试完成。P02实际六页与对象探针可复用；P03测试仅定位/未执行，历史认证门禁不冒充当前阻塞。P04结构产物不等于渲染验收；P05 mock不等于真AI生成。\n- 图标/声音/品牌资产和几何data的独立声明已定位，不从根MIT/Apache推断。P03生成PPTX缺失、P04研究渲染截图缺失及P02非formal JSONSchema明确登记。\n- 后续产品回归用本项目事实/对象契约独立编写；参考一项失败行为不能成为复制上游测试/Prompt/裁剪规则的理由。所有强制对象/QA/修订仍保留，不能用“不采用”删除功能需求。\n'
 (HERE/'README.md').write_text(text,encoding='utf-8')
 print(json.dumps({'modules':len(modules),'assets':len(assets),'source_files':len(files),'reuse_methods':dict(collections.Counter(m['method'] for m in modules)),'fixture_projects':dict(inventory)},ensure_ascii=False))
if __name__=='__main__':build()
