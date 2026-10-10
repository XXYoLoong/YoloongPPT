"""Export only public fictional sample artifacts, preserving actual run bytes."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
from uuid import UUID

run_id=sys.argv[1]
assert str(UUID(run_id))==run_id
root=Path('/runtime/runs')/run_id
destination=Path('/runtime/context-evidence')
destination.mkdir(exist_ok=False)
names=['task.json','task-effective.json','decision-route.json','runtime-snapshot.json','atomic-registry.json',
       'decision-context.json','presentation-context.json','decision-source-roles.json','source-role-map.json',
       'source-result.json','fact-source-result.json','deck-spec.json','execution-plan.json','execution-trace.json',
       'object-map.json','pipeline-trace.json','quality-report.json','render-report.json','model-request.json',
       'model-response.json','model-call.json','review-request.json','review-response.json','review-model-call.json',
       'result.json','deck.pptx']
for name in names:shutil.copyfile(root/name,destination/name)
renders=json.loads((root/'render-report.json').read_text(encoding='utf-8'))
for artifact in renders['artifacts']:
    relative=Path(artifact['path'])
    assert not relative.is_absolute() and relative.parts[0]=='render' and '..' not in relative.parts
    assert artifact['type'] in {'pdf','png'}
    path=root/relative
    target=destination/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,target)
shutil.copyfile(root/'render/deck.txt',destination/'render/deck.txt')
files={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destination.rglob('*')) if p.is_file()}
(destination/'manifest.json').write_text(json.dumps({'run_id':run_id,'scope':'Actual DEC-001/002/003 native draft; full DEC/QA/AC incomplete. Run predates additional output/revision rejection guards; original snapshots are unchanged.','files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'run_id':run_id}))
