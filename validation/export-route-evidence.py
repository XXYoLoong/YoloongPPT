"""Whitelist public fictional-sample node/generation artifacts; never copy runtime secrets."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
from uuid import UUID

run_id = sys.argv[1]
assert str(UUID(run_id)) == run_id
root = Path('/runtime/runs')/run_id
destination = Path('/runtime/route-evidence')
destination.mkdir(exist_ok=False)
names = ['task.json','task-effective.json','decision-route.json','runtime-snapshot.json','atomic-registry.json',
         'source-result.json','deck-spec.json','execution-plan.json','execution-trace.json','object-map.json',
         'pipeline-trace.json','quality-report.json','render-report.json','model-request.json','model-response.json',
         'model-call.json','review-request.json','review-response.json','review-model-call.json','result.json','deck.pptx']
for name in names:shutil.copyfile(root/name, destination/name)
shutil.copytree(root/'render',destination/'render')
files={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destination.rglob('*')) if p.is_file()}
(destination/'manifest.json').write_text(json.dumps({'run_id':run_id,'scope':'Actual route + registered native draft path; full DEC/AC unfinished.','files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'run_id':run_id,'bytes':sum(p.stat().st_size for p in destination.rglob('*') if p.is_file())}))
