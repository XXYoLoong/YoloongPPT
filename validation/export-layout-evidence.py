"""Whitelist actual model/render/QA evidence; never copy secret/database files."""
import hashlib,json,pathlib,shutil,sys
from uuid import UUID
run=sys.argv[1];assert str(UUID(run))==run
root=pathlib.Path('/runtime/runs')/run;dest=pathlib.Path('/runtime/layout-evidence');dest.mkdir(exist_ok=False)
names=['task.json','task-effective.json','decision-route.json','runtime-snapshot.json','atomic-registry.json','decision-context.json','presentation-context.json','decision-source-roles.json','source-role-map.json','source-result.json','fact-source-result.json','deck-spec.json','execution-plan.json','execution-trace.json','object-map.json','pipeline-trace.json','quality-report.json','render-report.json','model-request.json','model-response.json','model-call.json','review-request.json','review-response.json','review-model-call.json','result.json','deck.pptx','layout-selection.json','model-response-effective.json','quality-before-reference-repair.json','reference-repair-request.json','reference-repair-response.json','reference-repair-model-call.json']
for name in names:shutil.copyfile(root/name,dest/name)
for a in json.loads((root/'render-report.json').read_text())['artifacts']:
 relative=pathlib.Path(a['path']);assert not relative.is_absolute() and relative.parts[0]=='render' and '..' not in relative.parts
 target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/relative,target)
for name in ['deck.txt','deck-bbox.xhtml']:shutil.copyfile(root/'render'/name,dest/'render'/name)
initial=pathlib.Path('/runtime/runs/038ff02e-c86e-4611-90c2-93ebdd17c214')
for name in ['result.json','quality-report.json','deck-spec.json','model-call.json']:shutil.copyfile(initial/name,dest/('initial-'+name))
files={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file()}
(dest/'manifest.json').write_text(json.dumps({'run_id':run,'primary_model_run':initial.name,'scope':'Actual 10-page native layout subset, checkpoint primary response reused, actual reference repair and full-page visual/fact review. Initial P0=9 evidence retained; current executed P0=0, full system AC not passed.','files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'run_id':run}))
