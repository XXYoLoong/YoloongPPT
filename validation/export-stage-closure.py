"""Export current stage evidence and failures without secrets or runtime profiles."""
import hashlib,json,pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1];runtime=ROOT/'runtime/data'
target=ROOT/'validation/stage-closure-artifacts';target.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text('utf-8'))
secret_values=[p.read_bytes().strip() for p in (runtime/'secrets').rglob('*') if p.is_file()]
secret_values=[v for v in secret_values if len(v)>8];files=[]
def copy(src,dst):
    raw=src.read_bytes();assert not any(v in raw for v in secret_values),f'Sensitive source: {src.name}'
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
    files.append({'path':dst.relative_to(target).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
components={}
for kind in ['docx','xlsx','pdf']:
    candidates=[]
    for p in (runtime/('source-semantic-'+kind)).glob('component-*'):
        report=p/('report.json' if kind=='pdf' else 'checks.json')
        if report.is_file() and read(report).get('passed'):candidates.append((p,report))
    directory,report=max(candidates,key=lambda item:item[1].stat().st_mtime)
    components[kind]={'checks':len(read(report)['checks']),'passed':True,'model_calls':0,'report':f'components/{kind}/{report.name}'}
    for p in directory.rglob('*'):
        if p.is_file():copy(p,target/'components'/kind/p.relative_to(directory))
    for name in ['checks-failed.json','failure.json']:
        for old in (runtime/('source-semantic-'+kind)).glob('component-*/'+name):
            copy(old,target/'failures/component-checks'/kind/old.parent.name/old.name)
flow=read(runtime/'stage-closure/description-flow-evidence.json')
assert flow['passed']
run_roles={'description-generated':flow['generated_run_id'],'description-revised':flow['revised_run_id']}
xlsx=read(runtime/'source-semantic-validation/xlsx-evidence.json');run_roles['xlsx-generated']=xlsx['run_id']
for role,rid in run_roles.items():
    run=runtime/'runs'/rid
    for p in run.rglob('*'):
        if p.is_file() and (p.parent==run or p.parent.name=='render') and p.suffix in {'.json','.pptx','.pdf','.png','.txt','.xhtml','.html'}:
            copy(p,target/role/p.relative_to(run))
for folder,label in [(runtime/'stage-closure','checks/description'),(runtime/'source-semantic-validation','checks/sources')]:
    for p in folder.rglob('*.json'):copy(p,target/label/p.relative_to(folder))
failure_ids=set()
def collect(value):
    if isinstance(value,dict):
        error=value.get('error')
        if isinstance(error,dict):
            for detail in error.get('details',[]):
                if isinstance(detail,dict) and detail.get('run_id'):failure_ids.add(detail['run_id'])
        for v in value.values():collect(v)
    elif isinstance(value,list):
        for v in value:collect(v)
for p in target.glob('checks/**/*.json'):collect(read(p))
for rid in failure_ids:
    run=runtime/'runs'/rid
    for p in run.glob('*.json'):copy(p,target/'failures/runs'/rid/p.name)
for p in (ROOT/'validation/source-semantic-artifacts/integration-input').glob('*'):
    if p.is_file():copy(p,target/'inputs'/p.name)
cases={}
for case in ['xlsx','docx','pdf']:
    result=read(runtime/'source-semantic-validation'/f'{case}-result.json')
    cases[case]={'ok':result.get('ok',False),'run_id':result.get('run_id'),
                 'error_code':result.get('error',{}).get('code'),'system_acceptance':'not_passed'}
summary={'date':'2026-10-12','components':components,'source_generations':cases,
         'description_flow':{k:v for k,v in flow.items() if k not in {'description','checks'}},'description_flow_checks':len(flow['checks']),
         'xlsx_checks':len(xlsx['checks']),'run_roles':run_roles,'system_acceptance':'not_passed',
         'scope':'Stage closure: bounded input helpers, one real description/generation/revision flow and explicit source/model failures. Original full scope retained.',
         'files':sorted(files,key=lambda i:i['path'])}
(target/'evidence-manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf-8')
(ROOT/'validation/stage-closure-summary.json').write_text(json.dumps({k:v for k,v in summary.items() if k!='files'},ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in {'files','scope'}},ensure_ascii=False))
