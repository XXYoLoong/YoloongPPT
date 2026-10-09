"""Bounded VERIFY-RES-031: source integrity, scoped claims, existing runtime witnesses.

Negative cases alter copies of comparison data only, never upstream or prior reports.
"""
import copy,hashlib,json,re,subprocess,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class EvidenceError(ValueError):
 def __init__(self,code,detail):self.code=code;super().__init__(detail)
def require(test,code,detail):
 if not test:raise EvidenceError(code,detail)
baseline=read(HERE/'baseline-rows.json')
dimensions=baseline['需求主表']['37'][3].split('：',1)[1].rstrip('。').split('、')
ns={};exec((ROOT/'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns)
workbook,_=ns['read'](ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
matrix=read(HERE/'CrossProjectMatrix.json');catalog=read(HERE/'source-catalog.json');manifest=read(HERE/'input-manifest.json')
def pointer(obj,text):
 for k in text.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');obj=obj[int(k)] if isinstance(obj,list) else obj[k]
 return obj
def validate(m,c,im,verify_files=True):
 require(m['requirement_id']=='RES-031','E_REQUIREMENT','wrong requirement')
 require([d['dimension'] for d in m['dimensions']]==dimensions,'E_DIMENSION_SET','must preserve original 15 dimensions/order')
 projects=set(m['projects']);require(projects=={'P01','P02','P03','P04','P05'},'E_PROJECT_SET','five fixed projects required')
 for d in m['dimensions']:
  rows=d['comparisons'];ids=[r['project'] for r in rows]
  require(len(ids)>=3 and len(ids)==len(set(ids)) and set(ids)<=projects,'E_COVERAGE',d['dimension'])
  for r in rows:
   require(r.get('finding') and r.get('limit') and r['status'] in m['status_definition'],'E_CELL_STATUS',str(r))
   require(r.get('source_anchors') and all(k in c['anchors'] and c['anchors'][k]['project']==r['project'] for k in r['source_anchors']),'E_SOURCE_MISSING',str(r))
   require(all(e in im['research_files_sha256'] for e in r['runtime_evidence']),'E_EVIDENCE_MISSING',str(r))
   require(r['status']!='Observed' or bool(r['runtime_evidence']),'E_RUN_CLAIM','Observed must have actual evidence')
   require(not(r['project']=='P03' and r['status']=='Observed'),'E_P03_NOTRUN','source/startup/auth gate cannot prove P03 generation/export')
   require(r['product_status']=='not implemented/accepted by this research','E_PRODUCT_CLAIM','research is not product acceptance')
 for id,a in c['anchors'].items():
  require(a['locations'],'E_SOURCE_MISSING',id)
  for loc in a['locations']:
   if 'external_black_box' in loc:require('export-core' in str(loc),'E_BLACKBOX','unidentified external implementation');continue
   f=c['source_files'][loc['source_file']]
   require(all(1<=start<=end<=f['line_count'] for start,end in loc['spans']),'E_LINE_RANGE',id)
  if verify_files and 'research_file' in a:
   doc=read(ROOT/a['research_file']);pointed=pointer(doc,a['json_pointer'])
   require(bool(pointed),'E_POINTER',id)
   if not(id.startswith('P02:S:')):require(pointed==a['node'],'E_NODE_CHANGED',id)
 if verify_files:
  for key,f in c['source_files'].items():
   p=Path(f['local_path']);require(p.is_file() and sha(p)==f['sha256'],'E_SOURCE_HASH',key)
   require(len(p.read_text(encoding='utf-8').splitlines())==f['line_count'],'E_LINE_COUNT',key)
   if f['origin']=='fixed clone':
    v=m['projects'][f['project']]
    blob=subprocess.check_output(['git','-C',v['clone'],'show',v['fixed_commit']+':'+f['path']])
    require(blob.replace(b'\r\n',b'\n')==p.read_bytes().replace(b'\r\n',b'\n'),'E_FIXED_SOURCE_CHANGED',key)
   else:
    require(f['project']=='P02' and f['origin']=='installed pptagent1.1.37','E_DEPENDENCY_ORIGIN',key)
    depindex=read(ROOT/'research/P02/source-index.json')
    expected=next(v['sha256'] for v in depindex['files'].values() if v['origin']==f['origin'] and v['path']==f['path'])
    require(f['sha256']==expected,'E_DEPENDENCY_CHANGED',key)
  for rel,expected in im['research_files_sha256'].items():require((ROOT/rel).is_file() and sha(ROOT/rel)==expected,'E_INPUT_HASH',rel)
  for p,v in m['projects'].items():
   actual=subprocess.check_output(['git','-C',v['clone'],'rev-parse','HEAD'],text=True).strip()
   require(actual==v['fixed_commit'],'E_VERSION_DRIFT',p)
 require('AGPL' in m['projects']['P05']['license_observed'] and 'conflicting' in m['projects']['P05']['license_observed'],'E_LICENSE_CONFLICT','P05 declarations unresolved')
 return True
validate(matrix,catalog,manifest)
require(all(len(d['comparisons'])==5 for d in matrix['dimensions']),'E_FULL_COMPARISON','this artifact promises five projects per dimension')
for r in [35,37,39,41,43]:require(workbook['可执行任务'][f'L{r}'][1]=='进行中','E_P03_STATUS','do not close P03 VERIFY with this comparison')
# Check the real artifacts behind normal, boundary and failure findings without rerunning providers.
witnesses=[
 ('P01','research/P01/projects/p01_hello_world_20261007/exports/p01-hello-world.pptx','c39b6b596b6c6df0c69d8bdc2886eac5d1339cab5f148833951f1370095acd25',3),
 ('P02','research/P02/outputs/official-six/answer.pptx','eb90a46c983c15c09d02de5bccdd171b33ed39c22d12e7a9f912580ecd7b7b1b',6),
 ('P04','research/P04/validation/template-normal.pptx','e82c7d0f4ac91bdeadb9b985c91e0fcc736a09d5bc8d7abfed499fcf3fb7297d',None),
 ('P05','research/P05/outputs/maps-probes/native-objects.pptx','5965f5055e7aa27e96b8249f3f5bed5915ebe5e34c25da6206eef55d5c2cafa7',2)]
artifact_checks=[];pns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
for project,rel,expected,count in witnesses:
 path=ROOT/rel;require(sha(path)==expected,'E_ARTIFACT_HASH',rel)
 with zipfile.ZipFile(path) as z:
  require(z.testzip() is None,'E_ZIP',rel)
  names=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]
  if count is not None:require(len(names)==count,'E_SLIDE_COUNT',rel)
  texts=sum(len(E.fromstring(z.read(n)).findall('.//a:t',pns)) for n in names)
  tables=sum(len(E.fromstring(z.read(n)).findall('.//a:tbl',pns)) for n in names)
  charts=len([n for n in z.namelist() if re.fullmatch(r'ppt/charts/chart\d+\.xml',n)])
  if project=='P05':require(charts==1 and tables==1,'E_NATIVE_OBJECTS',rel)
  artifact_checks.append({'project':project,'path':rel,'sha256':expected,'slides':len(names),'text_runs':texts,'native_tables':tables,'chart_parts':charts,'scope':'ZIP/OOXML only; existing Office/visual observations remain those original reports'})
p1=read(ROOT/'research/P01/validation/verify-res-p01-05.json');require(p1['boundary_case']['tests_run']==26 and p1['boundary_case']['failures']==0,'E_P01_TEST_REPORT','selected test results')
p2=read(ROOT/'research/P02/validation/maps-probes.json');require(next(x for x in p2['cases'] if x['id']=='inline-svg-rejected')['result']['rejected'],'E_P02_FAILURE','SVG actual rejection')
p3=read(ROOT/'research/P03/validation/verify-res-p03-02.json');require([c['status'] for c in p3['cases']]==[200,200,428,428],'E_P03_HISTORY','startup/auth history')
p4=read(ROOT/'research/P04/validation/verify-res-p04-04-05.json');require(p4['cases']['boundary']['overflow']['omitted']==56,'E_P04_LOSS','silent omission witness')
p5=read(ROOT/'research/P05/validation/maps-probes.json');require(p5['cases']['page_budget']['actual']==9 and p5['cases']['clarify']['reported_assumptions_added'] is False,'E_P05_LOSS','page/crop witnesses')
tests=[{'name':'normal-comparison','kind':'normal','passed':True,'result':'15×5 records, fixed sources/provenance and current artifact hashes match'}, {'name':'explicit-missing-and-blackbox','kind':'boundary','passed':True,'result':'Not found/Unsupported with bounded source scopes accepted; P03 external exporter and host planning remain black boxes'}]
def reject(name,code,mutation):
 m,c,im=copy.deepcopy(matrix),copy.deepcopy(catalog),copy.deepcopy(manifest);mutation(m,c,im)
 try:validate(m,c,im);raise AssertionError(name+' unexpectedly accepted')
 except EvidenceError as e:
  assert e.code==code,(name,e.code,code)
  tests.append({'name':name,'kind':'failure','passed':True,'error_code':e.code,'reason':str(e),'scope':'mutated in-memory comparison copy; no upstream/report edited'})
reject('missing-dimension','E_DIMENSION_SET',lambda m,c,im:m['dimensions'].pop())
reject('below-three-projects','E_COVERAGE',lambda m,c,im:m['dimensions'][0].update(comparisons=m['dimensions'][0]['comparisons'][:2]))
reject('claim-without-source','E_SOURCE_MISSING',lambda m,c,im:m['dimensions'][0]['comparisons'][0].update(source_anchors=[]))
reject('promote-P03-source-to-runtime','E_P03_NOTRUN',lambda m,c,im:m['dimensions'][0]['comparisons'][2].update(status='Observed'))
reject('alter-source-hash','E_SOURCE_HASH',lambda m,c,im:next(iter(c['source_files'].values())).update(sha256='0'*64))
reject('alter-prior-evidence-hash','E_INPUT_HASH',lambda m,c,im:im['research_files_sha256'].update({next(iter(im['research_files_sha256'])):'0'*64}))
reject('conceal-license-conflict','E_LICENSE_CONFLICT',lambda m,c,im:m['projects']['P05'].update(license_observed='MIT'))
report={'requirement_id':'RES-031','task_id':'VERIFY-RES-031','passed':True,'dimensions':dimensions,'projects_per_dimension':{d['dimension']:len(d['comparisons']) for d in matrix['dimensions']},'source_files_verified':len(catalog['source_files']),'source_anchors_verified':len(catalog['anchors']),'research_inputs_verified':len(manifest['research_files_sha256']),'tests':tests,'existing_real_artifact_checks':artifact_checks,'P03_status':'five VERIFY still in progress; only startup/source/historical auth gate, not generation/export','runtime_reexecution':'none; reused fixed matching evidence and inspected artifacts','product_acceptance':'all 30 AC unexecuted; no architecture/runtime or code reuse approval','reproduction':'tool-bundled stdlib Python research/cross-project/build-matrix.py then verify-matrix.py; TEMP/TMP/TMPDIR on F:; fixed clones and evidence must already exist'}
(HERE/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'comparison_cells':75,'source_files':len(catalog['source_files']),'cases':len(tests),'P03_VERIFY':'remain in progress'},ensure_ascii=False))
