import ast, hashlib, json, pathlib, re, subprocess
root=pathlib.Path('F:/YoloongPPT-Research/P05')
work=pathlib.Path('F:/YoloongPPT-Research/P05-official-smoke/work')
out=pathlib.Path('F:/YoloongPPT/research/P05')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
specs=[
 ('ENTRY-CLI','auto_ppt_cli.py','main','CLI 调用与显式 QA/score 分流','normal/boundary/failure/revision/visual_qa'),
 ('CLI-REQUEST','auto_ppt_cli.py','build_request','create/revise 参数与输出路径','normal/revision'),
 ('CLI-INPUT','auto_ppt_cli.py','validate_runtime_inputs','来源、template、deck 文件存在性','failure'),
 ('ENTRY-HTTP','py-skill-server.py','SkillRequestHandler.do_POST','POST /skill 调用 handler','not_run'),
 ('ENTRY-MCP-CREATE','mcp_server.py','create_deck','MCP create_deck','not_run'),
 ('ENTRY-MCP-REVISE','mcp_server.py','revise_deck','MCP revise_deck','not_run'),
 ('ENTRY-JSON','python_backend/skill_api.py','main','JSON skill request/response','not_run'),
 ('REQUEST-JSON','python_backend/skill_api.py','load_request','JSON entry 的 action/prompt 校验；不冒充所有入口共享校验','not_run'),
 ('HANDLER','python_backend/skill_api.py','handle_skill_request','上下文、来源、JSON 旧 deck、双 renderer 路由与 response','normal/revision'),
 ('SOURCES','python_backend/source_loader.py','load_source_contexts','加载来源元数据、文本与 truncation 标记','normal'),
 ('SOURCE-CONTEXT','python_backend/source_loader.py','_build_context_text','5000 字符 excerpt 容量及 metadata','source_only'),
 ('PLANNER','python_backend/smart_layer.py','execute_planning_flow','mock/模型、schema、repair 与 chart normalization 主流程','normal/revision'),
 ('MOCK','python_backend/smart_layer.py','build_mock_deck','离线固定页型及启发式内容','normal/boundary'),
 ('COUNT','python_backend/smart_layer.py','clamp_slide_count','请求页数钳制至 5–12，固定 mock roster 另限最大 9','boundary'),
 ('SYSTEM-PROMPT','python_backend/smart_layer.py','build_system_prompt','读取根 SKILL.md 与 JSON Schema 组成模型 system prompt','source_only'),
 ('CREATE-PROMPT','python_backend/smart_layer.py','build_create_prompt','创建 prompt/context/research/数值提示','source_only'),
 ('REVISE-PROMPT','python_backend/smart_layer.py','build_revise_prompt','旧 deck JSON + 自然语言修订','source_only'),
 ('REPAIR-PROMPT','python_backend/smart_layer.py','build_repair_prompt','JSON/schema 失败后有限模型修复','source_only'),
 ('MODEL','python_backend/smart_layer.py','request_deck_json','provider.chat 外部模型边界','not_run_external_black_box'),
 ('PROVIDER','python_backend/llm_provider.py','get_default_provider','按环境/模型名选择 provider','source_only'),
 ('RESEARCH','python_backend/smart_layer.py','maybe_run_research','可选 Tavily 网络检索','not_run_external_black_box'),
 ('SCHEMA','python_backend/smart_layer.py','create_validator','deck-schema.json 的 JSON Schema validator','normal/boundary/revision'),
 ('CHART-NORMALIZE','python_backend/smart_layer.py','validate_chart_slides','数字格式修复或 chart→bullet，记录 assumptions','source_only'),
 ('MOCK-REVISION','python_backend/smart_layer.py','apply_heuristic_revision','页数/结论/执行/受众等 mock 修订，重排页码','revision'),
 ('THEME','python_backend/template_engine.py','resolve_theme','template / named theme / default','normal'),
 ('TEMPLATE','python_backend/template_engine.py','parse_template','PPTX master/layout/placeholder/theme 解析','source_only'),
 ('PY-RENDER','python_backend/pptx_renderer.py','render_deck_with_template','模板路线：移除所有旧 slides，再从 deck JSON 新建','source_only'),
 ('PY-LAYOUT','python_backend/pptx_renderer.py','_render_slide','布局 dispatch、notes、页面新建','source_only'),
 ('JS-BRIDGE','python_backend/js_renderer.py','render_deck_via_node','JSON 落盘与 Node 子进程，120 秒超时','normal/revision'),
 ('JS-ENTRY','generate-ppt.js','buildFromFile','读取命令行 JSON/PPTX 路径，处理 nativeCharts 选项，调用 buildDeck','normal/revision'),
 ('JS-BUILD','generate-ppt.js','buildDeck','wide canvas、theme、逐页 render 与 writeFile','normal/revision'),
 ('JS-VALIDATE','generate-ppt.js','validateDeck','JS 层布局、页码和数量校验','normal'),
 ('JS-LAYOUT','generate-ppt.js','renderSlide','16 种 layout key 的固定 dispatch；notes、页脚','normal'),
 ('JS-VISUALS','generate-ppt.js','renderVisualsOnSlide','图片、placeholder、视觉描述的固定处理','source_only'),
 ('JS-CHART','generate-ppt.js','renderChartSlide','默认图表图片；显式 native/无 canvas 时 OOXML','normal_image_chart_only'),
 ('JS-TABLE','generate-ppt.js','renderTableSlide','PptxGenJS addTable','source_only'),
 ('JS-CLOSING','generate-ppt.js','renderClosingSlide','closingBg + headerBg 正文造成实测低对比度','visual_review_issue'),
 ('QA','python_backend/visual_qa.py','run_visual_qa','独立 CLI QA：导出图片 + OOXML bbox heuristic','visual_qa'),
 ('QA-RENDER','python_backend/visual_qa.py','_export_images','soffice→PDF→pdftoppm JPEG，缺工具时 notes','visual_qa_external_renderer'),
 ('QA-HEURISTIC','python_backend/visual_qa.py','analyze_visual_quality','边缘/包围盒重叠/空页/文本页，非事实或像素审查','visual_qa'),
 ('QUALITY-SCORE','python_backend/quality_scorer.py','score_deck','JSON 内容 heuristic，独立 score 入口','source_only'),
]
nodes=[]; files={}
for ident,path,symbol,claim,state in specs:
 src=(root/path).read_text(encoding='utf-8')
 assert digest(root/path)==digest(work/path),(path,'source copy drift')
 files[path]=digest(root/path)
 if path.endswith('.py'):
  tree=ast.parse(src); parts=symbol.split('.')
  scope=tree
  for part in parts:
   scope=next(n for n in scope.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==part)
  start,end=scope.lineno,scope.end_lineno
 else:
  lines=src.splitlines(); start=next(i+1 for i,line in enumerate(lines) if re.match(r'(?:async )?function '+re.escape(symbol)+r'\(',line))
  end=next((i for i,line in enumerate(lines[start:],start+1) if re.match(r'(?:async )?function ',line)),len(lines)+1)-1
 nodes.append({'id':ident,'path':path,'symbol':symbol,'line_start':start,'line_end':end,'claim':claim,'evidence_state':state})
edges=[]
def edge(a,b,kind='calls',condition=None):
 e={'from':a,'to':b,'type':kind}
 if condition:e['condition']=condition
 edges.append(e)
for a in ['ENTRY-HTTP','ENTRY-MCP-CREATE','ENTRY-MCP-REVISE']:edge(a,'HANDLER')
edge('ENTRY-JSON','REQUEST-JSON');edge('ENTRY-JSON','HANDLER')
edge('ENTRY-CLI','CLI-INPUT');edge('ENTRY-CLI','CLI-REQUEST');edge('ENTRY-CLI','HANDLER')
edge('HANDLER','SOURCES');edge('SOURCES','SOURCE-CONTEXT');edge('HANDLER','PLANNER')
edge('PLANNER','SCHEMA');edge('PLANNER','RESEARCH','conditional','research_enabled')
edge('PLANNER','MOCK','conditional','mock/create');edge('MOCK','COUNT')
edge('PLANNER','MOCK-REVISION','conditional','mock/revise and existing deck JSON')
for b in ['SYSTEM-PROMPT','CREATE-PROMPT','REVISE-PROMPT','PROVIDER','MODEL']:edge('PLANNER',b,'conditional','not mock; create/revise prompt selected by mode')
edge('PLANNER','REPAIR-PROMPT','conditional','model JSON/schema failure within bounded retries')
edge('PLANNER','CHART-NORMALIZE');edge('HANDLER','TEMPLATE','conditional','template path selected')
edge('HANDLER','PY-RENDER','conditional','template path selected');edge('PY-RENDER','PY-LAYOUT')
edge('HANDLER','THEME','conditional','no template path');edge('HANDLER','JS-BRIDGE','conditional','no template path')
edge('JS-BRIDGE','JS-ENTRY');edge('JS-ENTRY','JS-BUILD');edge('JS-BUILD','JS-VALIDATE');edge('JS-BUILD','JS-LAYOUT')
for b in ['JS-VISUALS','JS-CHART','JS-TABLE','JS-CLOSING']:edge('JS-LAYOUT',b,'conditional','matching layout; visuals on eligible layout')
edge('ENTRY-CLI','QA','conditional','explicit qa-visual command; not automatic generation gate')
edge('QA','QA-RENDER');edge('QA','QA-HEURISTIC')
edge('ENTRY-CLI','QUALITY-SCORE','conditional','explicit score command')
resources=[]
for path in ['SKILL.md','deck-schema.json',*[str(p.relative_to(root)).replace('\\','/') for p in sorted((root/'assets/themes').glob('*.json'))]]:
 assert digest(root/path)==digest(work/path)
 resources.append({'path':path,'sha256':digest(root/path),'kind':'upstream prompt instructions (data, not agent authority)' if path=='SKILL.md' else 'schema' if 'schema' in path else 'theme tokens','evidence_state':'source_inspected; deck schema and dark-executive theme consumed by normal CLI'})
index={'artifact_type':'CallGraph + SourceIndex','requirement_id':'RES-P05-02','source_commit':'5ae0670747885c464aa8063329a902d80a251877','source_sha256':files,'resources':resources,'nodes':nodes,'edges':edges,'external_black_boxes':['LLM provider service (not run in these mock probes)','Tavily service (not run)','LibreOffice PDF renderer and pdftoppm rasterizer (executed, not product selection)','PptxGenJS/chartjs-node-canvas/python-pptx dependencies, resolved versions recorded; upstream internal implementation not expanded'],'runtime_evidence':'validation/baseline-run.json; per-case logs; outputs/normal-qa/visual-qa-report.json','scope':'Source call graph plus observed CLI flow, not function-level runtime instrumentation. HTTP/MCP/template/real-model branches are source-only or explicit black boxes.'}
(out/'source_index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
tracked=subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0')
changes=[p for p in tracked if p and digest(root/p)!=digest(work/p)]
assert changes==['package-lock.json'],changes
env={'source_commit':index['source_commit'],'container':'yoloongppt-p05-research','image_id':'sha256:080a15ab85a5501ded8d7ee31664b7de02b75c46712b966aa284155194dc723d','image_origin':'snapshot of previously installed P02 research system tools; independent P05 venv/npm dependencies','docker_data_vhdx':'F:/DockerDesktopWSL/disk/docker_data.vhdx','work':'F:/YoloongPPT-Research/P05-official-smoke/work -> /app','scratch':'F:/YoloongPPT-Research/P05-official-smoke/scratch -> /scratch','evidence':'F:/YoloongPPT/research/P05 -> /evidence','observed_versions_only':{'python':'3.11.2','node':'18.20.4','npm':'9.2.0','poppler':'22.12.0'},'python_dependencies':'43 installed distributions; validation/python-freeze.txt','npm_dependencies':'113 installed packages, npm-tree.json','npm_audit_notice':'7 findings: 3 moderate, 4 high; upstream dependencies not fixed or certified safe','source_copy_differences':changes,'original_npm_lock_sha256':digest(root/'package-lock.json'),'resolved_npm_lock_sha256':digest(work/'package-lock.json'),'npm_lock_change_reason':'official npm install updates copied root metadata from 0.7.8 to 0.8.0; original pinned clone unchanged','product_selection':False,'runtime_network':'bridge disconnected after installation; no model calls','setup_recovery':'snapshot inherited ENTRYPOINT sleep; first duplicate sleep argument exited 1. Task-owned empty container recreated with explicit entrypoint and infinity argument.'}
orig=json.loads((root/'package-lock.json').read_text());new=json.loads((work/'package-lock.json').read_text())
assert orig['packages'].keys()==new['packages'].keys()
env['npm_lock_changed_package_entries']=[k for k in orig['packages'] if orig['packages'][k]!=new['packages'][k]]
(out/'validation/environment.json').write_text(json.dumps(env,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'validation/package-lock.resolved.json').write_bytes((work/'package-lock.json').read_bytes())
print(f'PASS: {len(nodes)} nodes, {len(edges)} edges, {len(files)} source files match pinned clone; copied npm lock changes recorded')
