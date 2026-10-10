"""White-list visual pipeline evidence from F-backed runs; never copy runtime wholesale."""
import argparse,datetime,hashlib,json,os,re
from pathlib import Path
from uuid import UUID

ROOT=Path(__file__).resolve().parents[1]
RUN_ROOT=ROOT/'runtime/data/runs'
DEST=ROOT/'validation/visual-live-artifacts'
KNOWN_RUNS={'generated':'74a0567c-2bfb-47e1-a6b0-eae2dcf252e6','failed-source-role':'f1504d37-f2d0-4b22-88a9-3727b93b34a4','failed-fact-scope':'467692a5-a625-443e-94f1-276617c01e55','failed-diagram-edge':'146f90e3-8305-43dc-ae41-383afa87c235','historical-qa-pixel-false-positive':'dbb3a53c-1c15-4fdd-aa73-e66560ce7b77'}
JSON_NAMES=['task.json','task-effective.json','source-result.json','fact-source-result.json','source-role-map.json','decision-route.json','decision-context.json','decision-source-roles.json','presentation-context.json','decision-evidence.json','evidence-resolution.json','decision-fact-boundary.json','fact-boundary.json','approved-source-result.json','fact-interpretation.json','fact-grounding.json','fact-model-request.json','fact-model-response.json','fact-model-call.json','fact-checkpoint.json','narrative-context.json','narrative-result.json','visual-packet.json','visual-result.json','resolved-assets.json','template-selection.json','layout-selection.json','deck-spec.json','execution-plan.json','execution-trace.json','object-map.json','atomic-registry.json','pipeline-trace.json','runtime-snapshot.json','version-manifest.json','model-request.json','model-response.json','model-response-effective.json','model-call.json','quality-report.json','quality-before-recheck.json','render-report.json','review-request.json','review-response.json','review-model-call.json','review-reuse.json','revision-plan.json','completion-decision.json','result.json','failure.json','manifest.json']+[f'decision-DEC-{i:03d}.json' for i in range(1,41)]
FIXTURES={'visual-independent-50':['runtime/data/visual-validation/visual-runtime.json','runtime/data/visual-validation/node-samples.json','runtime/data/visual-validation/visual-result.json','runtime/data/visual-validation/declared-image.png','runtime/data/visual-validation/wide-template.pptx','runtime/data/visual-validation/narrow-template.pptx'],
 'visual-native-fixture':['runtime/data/visual-execution-validation/visual-execution.json','runtime/data/visual-execution-validation/proposal.json','runtime/data/visual-execution-validation/final-proposal.json','runtime/data/visual-execution-validation/visual-packet.json','runtime/data/visual-execution-validation/visual-result.json','runtime/data/visual-execution-validation/source-fixture.json','runtime/data/visual-execution-validation/deck-spec.json','runtime/data/visual-execution-validation/execution-plan.json','runtime/data/visual-execution-validation/object-map.json','runtime/data/visual-execution-validation/execution-result.json','runtime/data/visual-execution-validation/quality-report.json','runtime/data/visual-execution-validation/quality-decisions.json','runtime/data/visual-execution-validation/render-report.json','runtime/data/visual-execution-validation/deck.pptx','runtime/data/visual-execution-validation/selected-template.pptx','runtime/data/visual-execution-validation/unsupported-template.pptx','runtime/data/visual-execution-validation/render/deck.pdf'],
 'incremental-verification':['validation/visual-path-guards.json','validation/quality-stage-artifacts/quality-asset-note-runtime.json','validation/quality-stage-artifacts/quality-after-metadata-check.json']}


def digest(raw):return hashlib.sha256(raw).hexdigest()
def safe_json(raw,name):
 value=json.loads(raw)
 def scan(v):
  if isinstance(v,dict):
   for k,item in v.items():
    if k.lower() in {'api_key','apikey','password','access_token','private_key','secret'} and isinstance(item,str) and item:raise RuntimeError('Sensitive credential field blocked: '+name)
    scan(item)
  elif isinstance(v,list):
   for item in v:scan(item)
 scan(value)
 if re.search(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9_-]{20,}|"Authorization"\s*:\s*"(?:Bearer|Basic) ',raw,re.I):raise RuntimeError('Sensitive credential pattern blocked: '+name)
 return value


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--success-run',action='append',default=[]);parser.add_argument('--checks',action='append',default=[]);args=parser.parse_args()
 if os.name=='nt' and (ROOT.drive.upper()!='F:' or Path(os.environ.get('TEMP','')).drive.upper()!='F:'):raise RuntimeError('Workspace and TEMP must remain on F:')
 runs=dict(KNOWN_RUNS)
 for success in args.success_run:
  if str(UUID(success))!=success:raise RuntimeError('Success run must be a UUID')
  runs['qa-recovered-success-'+success[:8]]=success
 DEST.mkdir(exist_ok=True);entries=[];states=[]
 old_path=DEST/'export-manifest.json';old=json.loads(old_path.read_text('utf-8')) if old_path.is_file() else {'artifacts':[],'runs':[]}
 def copy(source,relative,expected=None):
  source=source.resolve();target=(DEST/relative).resolve()
  if not source.is_relative_to(ROOT) or not target.is_relative_to(DEST) or source.is_symlink() or any(p.lower() in {'secrets','.ssh','.git'} for p in source.parts):raise RuntimeError('Evidence path outside allowed roots')
  if source.suffix.lower() not in {'.json','.png','.pdf','.pptx','.txt','.xhtml'}:raise RuntimeError('File type not explicitly white-listed')
  raw=source.read_bytes();actual=digest(raw)
  if expected and actual!=expected:raise RuntimeError('Run manifest hash differs: '+str(source.relative_to(ROOT)))
  if source.suffix.lower()=='.json':safe_json(raw,str(source.relative_to(ROOT)))
  if len(raw)>64*1024*1024:raise RuntimeError('Evidence exceeds explicit 64 MiB per-file bound')
  target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists() and target.read_bytes()!=raw:raise RuntimeError('Historical export changed; refusing overwrite: '+relative)
  if not target.exists():target.write_bytes(raw)
  entries.append({'path':str(target.relative_to(DEST)).replace('\\','/'),'source_path':str(source),'bytes':len(raw),'sha256':actual,'source_manifest_sha256':expected})
 for label,rid in runs.items():
  folder=RUN_ROOT/rid
  if not folder.is_dir():raise RuntimeError('Known run absent: '+rid)
  manifest=safe_json((folder/'manifest.json').read_bytes(),label+'/manifest.json');hashes={a['path']:a['hash'] for a in manifest['artifacts']}
  names=[n for n in JSON_NAMES+['deck.pptx'] if (folder/n).is_file()]
  if (folder/'render-report.json').is_file():
   render=safe_json((folder/'render-report.json').read_bytes(),label+'/render-report.json')
   for a in render['artifacts']:
    if a['type'] not in {'png','pdf'}:continue
    if not re.fullmatch(r'render/(?:deck\.pdf|slide-\d+\.png)',a['path']):raise RuntimeError('Unexpected render evidence name')
    names.append(a['path'])
   names.extend(n for n in [render.get('render_text_path'),render.get('render_bbox_path')] if n)
  for n in dict.fromkeys(names):
   if n!='manifest.json' and n not in hashes:raise RuntimeError('Known evidence missing from source manifest: '+rid+'/'+n)
   copy(folder/n,label+'/'+n,hashes.get(n))
  failure=safe_json((folder/'failure.json').read_bytes(),label+'/failure.json')['error'] if (folder/'failure.json').is_file() else None
  states.append({'label':label,'run_id':rid,'failure_code':failure['code'] if failure else None,'failure_component':failure['component'] if failure else None,'historical_qa_issue_state':label=='historical-qa-pixel-false-positive','status':'success' if label.startswith('qa-recovered-success-') else 'historical_evidence'})
 for label,names in FIXTURES.items():
  for n in names:
   p=ROOT/n
   if p.is_file():copy(p,'fixtures/'+label+'/'+p.name)
 for n in args.checks:
  p=Path(n);p=p if p.is_absolute() else ROOT/p
  if not p.is_file() or p.suffix!='.json':raise RuntimeError('Explicit checks must be existing JSON evidence')
  copy(p,'checks/'+p.stem+'-'+digest(p.read_bytes())[:12]+p.suffix)
 current={str(p.relative_to(ROOT)).replace('\\','/'):digest(p.read_bytes()) for p in sorted([*(ROOT/'src/yoloongppt').rglob('*.py'),*(ROOT/'contracts').glob('*.json')]) if p.is_file()}
 merged_entries={a['path']:a for a in old['artifacts']}
 merged_entries.update({a['path']:a for a in entries});entries=[merged_entries[n] for n in sorted(merged_entries)]
 for a in entries:
  exported=DEST/a['path']
  if not exported.is_file() or digest(exported.read_bytes())!=a['sha256']:raise RuntimeError('Historical export missing/changed: '+a['path'])
 merged_runs={r['run_id']:r for r in old['runs']};merged_runs.update({r['run_id']:r for r in states});states=list(merged_runs.values())
 report={'scope':'White-listed real six-page visual generation, all native rendered pages, historical failures and QA-only recovery; independent fixture node evidence separate; not full AC acceptance','runs':states,'artifacts':entries,'current_source_contract_hashes':current,'source_snapshot_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_snapshot_meaning':'current repository snapshot for review; each run retains its own actual execution/version metadata, not rewritten to this snapshot','not_exported':['secrets','credentials','SQLite','runtime directories wholesale','LibreOffice profiles'],'system_acceptance':'not_passed'}
 path=DEST/'export-manifest.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'files':len(entries),'runs':len(states),'source_contract_hashes':len(current),'manifest':str(path),'success_run':args.success_run},ensure_ascii=False))

if __name__=='__main__':main()
