"""Repeat a real saved-review recovery and reject a changed checkpoint."""
import hashlib
import json
import shutil
from pathlib import Path

from yoloongppt.artifacts import RunArtifacts
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.errors import TaskError, trace_id
from yoloongppt.revision import recheck

parent=Path('/runtime/runs/39a2dbf3-c19b-4da2-99a6-27fe7b82ef7a')
checks=[]
def record(name,passed,observed=None):
    assert passed,(name,observed)
    checks.append({'name':name,'passed':True,'observed':observed})
def load(root,name):return json.loads((root/name).read_text('utf-8'))
schemas=SchemaRegistry()
result=recheck(parent.name,schemas,trace_id(),reuse_saved_review=True)
root=Path(result['artifact_root'])
record('repeat_saved_review_recovery',result['fresh_model_call'] is False,result['run_id'])
record('repeat_P0_zero',result['qa']['p0_issue_count']==0)
record('repeat_still_warning_not_final',result['completion']['state']=='warning' and not result['completion']['final_allowed'])
record('saved_request_actual_six_pages',load(root,'review-request.json')['context']['reviewed_image_orders']==list(range(6)))
old=load(parent,'quality-report.json');new=load(root,'quality-report.json')
key=lambda i:tuple(str(i[k]) for k in ('slide_order','severity','kind','detail','evidence_refs'))
record('issues_not_duplicated_or_dropped',sorted(map(key,old['model_review']['issues']))==sorted(map(key,new['model_review']['issues'])))
record('raw_response_unchanged',(root/'review-response.json').read_bytes()==(parent/'review-response.json').read_bytes())
record('same_PPTX_and_render_bytes',all((root/n).read_bytes()==(parent/n).read_bytes() for n in ['deck.pptx',*[a['path'] for a in load(root,'render-report.json')['artifacts']]]))
record('all_38_nodes_preserved',result['completion']['missing_nodes']==[])

# A separate fixture retains the manifest then corrupts only its own bytes.
fixture=RunArtifacts()
for name in ['task.json','deck-spec.json','source-result.json','object-map.json','render-report.json','deck.pptx']:
    shutil.copyfile(parent/name,fixture.path/name)
fixture.json('manifest.json',{'run_id':fixture.run_id,'artifacts':fixture.manifest()})
with (fixture.path/'deck.pptx').open('ab') as stream:stream.write(b'changed-checkpoint-fixture')
for reuse in (False,True):
    try:recheck(fixture.run_id,schemas,trace_id(),reuse_saved_review=reuse)
    except TaskError as error:
        record('changed_checkpoint_rejected_'+str(reuse),error.code=='ARTIFACT_CHANGED',error.code)
    else:raise AssertionError('corrupted checkpoint accepted')

source=Path('/workspace/src/yoloongppt/revision.py')
report={'passed':True,'checks':checks,'count':len(checks),'run_id':result['run_id'],
        'parent_run_id':parent.name,'corrupt_fixture_run_id':fixture.run_id,
        'fresh_model_calls':0,'fresh_render_calls':0,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'scope':'Saved-review repeat recovery and immutable checkpoint boundary only; full AC remains not_passed'}
out=Path('/runtime/visual-live-validation/repeat-recovery.json')
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'count':len(checks),'run_id':result['run_id'],'fresh_model_calls':0},ensure_ascii=False),flush=True)
