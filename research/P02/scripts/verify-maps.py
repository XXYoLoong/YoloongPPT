"""Verify research map references, baseline coverage and unchanged real artifacts."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
BASE=Path(__file__).resolve().parents[1]
def load(name):return json.loads((BASE/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
src=load('source-index.json');refs=src['references'];files=src['files']
skill=Path('F:/YoloongPPT-Research/P02/skills/pptagent') if sys.platform=='win32' else Path('/research/skills/pptagent')
copy=Path('F:/YoloongPPT-Research/P02-official-smoke/main-skill') if sys.platform=='win32' else Path('/artifacts/main-skill')
dep=copy/'.venv/lib/python3.11/site-packages/deeppresenter'
for fid,f in files.items():
 path=(skill if f['origin']=='main Skill' else dep)/f['path']
 assert sha(path)==f['sha256'],fid
 if f['origin']=='main Skill': assert sha(copy/f['path'])==f['sha256'],fid
for key,r in refs.items():
 f=files[r['file']];path=(skill if f['origin']=='main Skill' else dep)/f['path'];lines=path.read_text(encoding='utf-8').splitlines()
 assert 1<=r['start']<=r['end']<=len(lines),key
 assert hashlib.sha256('\n'.join(lines[r['start']-1:r['end']]).encode()).hexdigest()==r['snippet_sha256'],key
assert 'className.includes' in (dep/files['converter']['path']).read_text().splitlines()[refs['converter:className-bug']['start']-1]
maps={name:load(name+'.json') for name in ['call-graph','decision-map','template-map','capability-map']}
def walk(item):
 if isinstance(item,dict):
  for key,value in item.items():
   if key=='source_refs':assert value and all(r in refs for r in value),value
   if key=='evidence' and isinstance(value,list):assert all((BASE/p).is_file() for p in value),value
   walk(value)
 elif isinstance(item,list):
  for value in item:walk(value)
for m in maps.values():walk(m)
g=maps['call-graph'];ids={n['id'] for n in g['nodes']}
assert len(ids)==len(g['nodes']) and all(e['from'] in ids and e['to'] in ids for e in g['edges'])
assert set(g['phase_coverage'])=={'entry','Agent/Planner','Prompt','Schema','template','layout','render','export','QA','revision'}
assert all(set(ns)<=ids for ns in g['phase_coverage'].values())
assert next(n for n in g['nodes'] if n['id']=='host')['owner']=='external host'
d=maps['decision-map'];assert [r['id'] for r in d['dec_crosswalk']]==[f'DEC-{i:03d}' for i in range(1,41)]
did={n['id'] for n in d['nodes']}
for n in d['nodes']:assert all(n.get(k) for k in ['input_schema','candidate_generation','mechanism','output_schema','constraints','fallback','trace','source_refs'])
assert all(set(r['nodes'])<=did for r in d['dec_crosswalk'])
c=maps['capability-map'];assert [o['id'] for o in c['objects']]==[f'PPT-{i:03d}' for i in range(1,31)]
assert all(o['status'] in c['status_definition'] and o['reason'] and o['round_trip'] for o in c['objects'])
assert next(o for o in c['objects'] if o['id']=='PPT-015')['status']=='Unsupported'
assert next(o for o in c['objects'] if o['id']=='PPT-017')['status']=='Unsupported'
t=maps['template-map'];assert len(t['templates'])==1 and len(t['templates'][0]['slots'])==3 and len(t['canvases'])==3
assert set(t['templates'][0]['tokens'])==set(re.findall(r'\{\{(\w+)\}\}',(skill/'assets/slide-template.html').read_text()))
p=load('validation/maps-probes.json');assert len(p['cases'])==5 and all(x['passed'] for x in p['cases'])
for path,value in p['artifacts'].items():assert sha(BASE/path)==value,path
normal=load('validation/verify-official-six.json');actual=sha(BASE/'outputs/official-six/answer.pptx')
assert actual==p['normal_unchanged_sha256']=='eb90a46c983c15c09d02de5bccdd171b33ed39c22d12e7a9f912580ecd7b7b1b'
final=load('outputs/official-six/final-report.json');assert final['complete'] and all(final['checks'].values())
assert load('outputs/maps-probes/shared-resource/final-report.json')['complete'] is False
assert load('outputs/maps-probes/svg-failure.json')['rejected']
ns={};exec((BASE.parent/'P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns)
baseline,_=ns['read'](BASE.parents[1]/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
for sheet,key,prefix in [('决策链','dec_crosswalk','DEC-'),('PowerPoint对象矩阵','objects','PPT-')]:
 rows=[(cell[1:],v[1]) for cell,v in baseline[sheet].items() if re.fullmatch('A[0-9]+',cell) and v[1].startswith(prefix)]
 expected=[(id,baseline[sheet]['B'+n][1]) for n,id in rows]
 assert [(r['id'],r['name']) for r in maps['decision-map' if prefix=='DEC-' else 'capability-map'][key]]==expected
report={'requirements':['RES-P02-02','RES-P02-03','RES-P02-04','RES-P02-05'],'passed':True,'source_files_verified':len(files),'source_refs_verified':len(refs),'call_graph_nodes':len(ids),'phase_coverage':g['phase_coverage'],'decision_nodes':len(did),'DEC_crosswalk':40,'PPT_objects':30,'normal_evidence':'validation/verify-official-six.json','boundary_failure_evidence':['validation/maps-probes.json','validation/footer-revision.json','validation/workflow-probes.json','validation/visual-slides-traced-01.json'],'new_probe_cases':5,'actual_normal_pptx_sha256':actual,'normal_final_complete':True,'source_and_artifact_hashes_verified':True,'visual_probe_previews':'two HTML PNGs actually viewed; no obvious clipping/overlap; no fake host review','limitations':['source graph is not full dynamic tracing','main Skill host planning is external','inline SVG converter bug unpatched','external visual JSON integration unpassed','MCP session not executed','all Microsoft PowerPoint/roundtrip and product AC unexecuted']}
(BASE/'validation/verify-maps.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
