"""Verify mapped source references, data coverage, and actual evidence artifacts."""
import collections,hashlib,json,re,zipfile
from pathlib import Path
root=Path('F:/YoloongPPT-Research/P05');base=Path('F:/YoloongPPT/research/P05')
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
dec=load(base/'ProjectDecisionMap.json');template=load(base/'ProjectTemplateMap.json');cap=load(base/'ProjectCapabilityMap.json');probes=load(base/'validation/maps-probes.json')
baseline=load(Path('F:/YoloongPPT-Temp-P01-05/p05-baseline-rows.json'))
assert [(r['dec_id'],r['baseline_name']) for r in dec['unified_dec_crosswalk']]==[(r[0],r[1]) for r in baseline['决策链']]
assert [(r['ppt_id'],r['baseline_name']) for r in cap['objects']]==[(r[0],r[1]) for r in baseline['PowerPoint对象矩阵']]
assert len(dec['unified_dec_crosswalk'])==40 and len(cap['objects'])==30
ids={n['id'] for n in dec['nodes']};assert len(ids)==14
for n in dec['nodes']:
 assert all(n[k] for k in ['input','candidates','mechanism','output','fallback','source'])
 assert set(n['dec_ids'])<={f'DEC-{i:03}' for i in range(1,41)}
for r in dec['unified_dec_crosswalk']:assert set(r['node_ids'])<=ids
js=(root/'generate-ppt.js').read_text(encoding='utf-8');enum=re.search(r'const allowedLayouts = new Set\(\[([\s\S]*?)\]\);',js).group(1)
allowed=re.findall(r"'([^']+)'",enum)
assert set(allowed)=={l['layout'] for l in template['js_layouts']} and len(allowed)==17
assert len({l['source'][0]['symbol'] for l in template['js_layouts']})==15
assert len(template['built_in_themes'])==6
assert len(template['template_path']['observed_fixture']['layouts'])==11
assert sum(len(l['placeholders']) for l in template['template_path']['observed_fixture']['layouts'])==58
refs=[]
def walk(v):
 if isinstance(v,dict):
  if all(k in v for k in ['path','line_start','line_end','sha256']):refs.append(v)
  for item in v.values():walk(item)
 elif isinstance(v,list):
  for item in v:walk(item)
for obj in [dec,template,cap]:walk(obj)
for r in refs:
 p=root/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
 lines=p.read_text(encoding='utf-8').splitlines();assert 1<=r['line_start']<=r['line_end']<=len(lines)
 if r['symbol']:assert r['symbol'] in lines[r['line_start']-1]
assert all(o['status'] in ['Native','Partial','Fallback','Unsupported'] for o in cap['objects'])
assert not any(o['full_baseline_operations_supported'] for o in cap['objects'])
for a in probes['artifacts']:
 p=base/a['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  if a['native_chart_parts']:assert any(n.startswith('ppt/embeddings/') and n.endswith('.xlsx') for n in z.namelist())
normal=base/'outputs/normal/py-generated-deck.pptx'
assert hashlib.sha256(normal.read_bytes()).hexdigest()=='34de9862e65ba032f74d1d1c64bd813102245e8b53bcab43e8b506cb03899ceb'
assert probes['cases']['template-cli']['returncode']==1
assert probes['cases']['native-objects']['returncode']==0
assert probes['cases']['empty_template_objects']['chart_values']==[7.0,0.0,0.0]
assert not probes['cases']['empty_template_objects']['kpi_text_present']
assert probes['cases']['invalid-layout']['returncode']==1
report={'requirement_ids':['RES-P05-03','RES-P05-04','RES-P05-05'],'task_ids':[f'{p}-RES-P05-{i:02}' for i in range(3,6) for p in ['TASK','VERIFY']],'verification_state':'completed_candidate_research_with_negative_findings','source_commit':dec['source_commit'],'coverage':{'decision_groups':14,'DEC_crosswalk':40,'JS_layout_keys':17,'JS_render_functions':15,'themes':6,'parsed_fixture_layouts':11,'parsed_fixture_placeholders':58,'PPT_objects':30,'source_references_checked':len(refs),'source_files_checked':len(dec['source_files_sha256'])},'normal_cases':['既有8页官方mock/JSON修订/严格QA实际结果复用','JS显式native chart/table/notes写入；chart part+embedded workbook+table实测','empty-template Python直接写入3页chart/table/notes'],'boundary_cases':['12页请求实际9页，中文mock语言仍en-US','clarify8项101字→6项80字，未增加裁剪assumptions','template主题关系颜色/字体漏读，使用默认值','tech-modern不存在→business-clean警告fallback','empty-template KPI落title layout+bullet，KPI字段丢失','direct Python chart [7]→[7,0,0]；不与planner校验路径混淆'],'failure_cases':[{'case':'已有页面template','returncode':1,'exception_type':'KeyError','actual_message':'None','reason':'r:id缺XML namespace，drop_rel(None)','evidence':'validation/template-cli.txt; validation/template-direct.txt','error_code_scope':'上游未给稳定结构化error code；此处保留真实类型/exit/reason，不冒充产品错误码'},{'case':'missing/corrupt/wrong-extension template','exception_types':['FileNotFoundError','RuntimeError','ValueError'],'evidence':'validation/maps-probes.json'},{'case':'unsupported layout','returncode':1,'evidence':'validation/invalid-layout.txt'},{'case':'existing strict QA','returncode':1,'issues':27,'evidence':'validation/verify-res-p05-01-02.json'}],'artifact_hashes_verified':probes['artifacts'],'unchanged_normal_sha256':hashlib.sha256(normal.read_bytes()).hexdigest(),'license_boundary':'AGPL3 vs Apache metadata冲突未裁定，无产品代码复用','completion_boundary':'三个强制研究映射及正常/边界/失败证据齐备；未修补上游；不代表产品DEC/PPT/AC完成。真实LLM/Tavily、HTTP/MCP运行、完整对象编辑和PowerPoint验收未执行。'}
(base/'validation/verify-res-p05-03-05.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS:',json.dumps(report['coverage'],ensure_ascii=False),'artifacts',len(probes['artifacts']))
