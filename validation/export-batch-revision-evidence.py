"""Export fixed live runs and component evidence, excluding secrets/LO profiles."""
import hashlib,json,pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
runtime=ROOT/'runtime/data';target=ROOT/'validation/batch-revision-artifacts'
target.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text('utf-8'))
secret_values=[p.read_bytes().strip() for p in (runtime/'secrets').rglob('*') if p.is_file()]
secret_values=[v for v in secret_values if len(v)>8]
copied=[]
def copy(src,dst):
    raw=src.read_bytes()
    if src.suffix in {'.json','.txt','.xml','.log','.md'}:
        assert not any(v in raw for v in secret_values),f'Sensitive data detected in {src.name}'
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
    copied.append({'path':dst.relative_to(target).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})

cases={};parents=set()
for case in ['text','chart','image','beautify','image-repeat']:
    report=read(runtime/'batch-revision-validation'/f'{case}-evidence.json')
    cases[case]={'run_id':report['run_id'],'parent_run_id':report['parent_run_id'],'checks':len(report['checks']),
                 'p0':report['qa']['p0_issue_count'],'warnings':report['completion']['warning_issue_count'],
                 'final_allowed':report['completion']['final_allowed'],'missing_nodes':report['completion']['missing_nodes']}
    parents.add(report['parent_run_id'])
    run=runtime/'runs'/report['run_id']
    for path in run.rglob('*'):
        if path.is_file() and (path.parent==run or path.parent.name=='render') and path.suffix in {'.json','.pptx','.pdf','.png','.txt','.html'}:
            copy(path,target/'runs'/report['run_id']/path.relative_to(run))
for run_id in parents:
    run=runtime/'runs'/run_id
    for name in ['deck.pptx','deck-spec.json','object-map.json','quality-report.json','result.json','manifest.json','version-manifest.json','fixture-identity.json']:
        if (run/name).is_file():copy(run/name,target/'parents'/run_id/name)
for path in (runtime/'batch-revision-validation').iterdir():
    if path.is_file() and path.suffix in {'.json','.pptx'}:copy(path,target/'checks'/path.name)
for kind,folder in [('native','revision-native-validation/1791741166720458028'),('scope','revision-scope-validation/e1d50e44-2305-4b1b-9c4d-b6c583d78bb5')]:
    source=runtime/folder
    for p in source.rglob('*'):
        if p.is_file() and p.suffix in {'.json','.pptx','.png'}:copy(p,target/'components'/kind/p.relative_to(source))
failure_ids={'a5f855fd-fba8-4563-892e-03c17b94191d','ab762c14-bb2e-4f7e-9f3a-54a10a0ab23e'}
def collect_failures(content):
    if isinstance(content,dict):
        error=content.get('error')
        for detail in error.get('details',[]) if isinstance(error,dict) else []:
            if isinstance(detail,dict) and detail.get('run_id'):failure_ids.add(detail['run_id'])
        for value in content.values():collect_failures(value)
    elif isinstance(content,list):
        for value in content:collect_failures(value)
for path in (runtime/'batch-revision-validation').glob('*.json'):collect_failures(read(path))
for run_id in failure_ids:
    run=runtime/'runs'/run_id
    for name in ['failure.json','manifest.json','revision-request.json','revision-intent.json','version-manifest.json']:
        if (run/name).is_file():copy(run/name,target/'failures'/run_id/name)
components={'scope':read(target/'components/scope/component-validation.json'),
            'native':read(target/'components/native/native-revision-checks.json'),
            'incremental':read(target/'checks/incremental-checks.json')}
manifest={'cases':cases,'files':sorted(copied,key=lambda x:x['path']),'system_acceptance':'not_passed',
          'scope':'Fixed live API revisions and separate synthetic/component regressions; full baseline remains incomplete.',
          'excluded':'Secrets, local LO profiles and unrelated runtime runs; parent manifests retain full original hashes.'}
(target/'evidence-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'files':len(copied),'bytes':sum(x['bytes'] for x in copied),'cases':cases,
                  'component_check_counts':{k:len(v['checks']) for k,v in components.items()}},ensure_ascii=False))
