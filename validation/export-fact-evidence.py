"""Whitelist only fictional public PoC artifacts; never export secrets/DB/runtime."""
import hashlib,json,shutil
from pathlib import Path
root=Path('F:/YoloongPPT');destination=root/'validation/fact-artifacts'
destination.mkdir(exist_ok=False)
report=json.loads((root/'validation/fact-integration.json').read_text('utf-8'))
names=['task.json','task-effective.json','source-result.json','fact-source-result.json','fact-interpretation.json','fact-grounding.json','fact-checkpoint.json','fact-model-request.json','fact-model-response.json','fact-model-call.json',
       'decision-route.json','runtime-snapshot.json','atomic-registry.json','decision-context.json','presentation-context.json','decision-source-roles.json','source-role-map.json','decision-evidence.json','evidence-resolution.json','decision-fact-boundary.json','fact-boundary.json','approved-source-result.json',
       'model-request.json','model-response.json','model-response-effective.json','model-call.json','deck-spec.json','execution-plan.json','execution-trace.json','object-map.json','pipeline-trace.json','quality-report.json','render-report.json',
       'review-request.json','review-response.json','review-model-call.json','revision-request.json','revision-history.json','result.json','failure.json','deck.pptx']
runs={'generated':report['base_run_id'],'revised':report['revision_run_id'],'unresolved':report['blocked_run_id'],'fact-checkpoint':report['checkpoint_run_id'],
      'initial-qa-1':report['initial_p0_run_ids'][0],'initial-qa-2':report['initial_p0_run_ids'][1],
      'initial-shared-claim-error':'8393689f-7dd0-450b-8532-602a18f05556','initial-scope-quote-error':'e11a40c9-33bf-4d36-8238-fb7cccd34b4a','initial-date-error':'841413f8-77cf-42d3-bf0a-f21521622d32'}
for label,rid in runs.items():
 source=root/'runtime/data/runs'/rid;manifest=json.loads((source/'manifest.json').read_text('utf-8'));hashes={a['path']:a['hash'] for a in manifest['artifacts']}
 target=destination/label;target.mkdir()
 selected=[name for name in names if (source/name).is_file()]
 if (source/'render-report.json').is_file():
  render=json.loads((source/'render-report.json').read_text('utf-8'));selected.extend(a['path'] for a in render['artifacts']);selected.extend([render['render_text_path'],render['render_bbox_path']])
 for name in dict.fromkeys(selected):
  relative=Path(name);assert not relative.is_absolute() and '..' not in relative.parts
  data=(source/relative).read_bytes();assert hashlib.sha256(data).hexdigest()==hashes[name],(rid,name)
  output=target/relative;output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
files={str(p.relative_to(destination)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destination.rglob('*')) if p.is_file()}
(destination/'manifest.json').write_text(json.dumps({'runs':runs,'files':files,'scope':'Actual source conflict blocking, checkpoint extraction reuse, new four-page native PPTX/render/review and single-title revision. Initial errors/P0 evidence preserved. Full AC remains not_passed.'},ensure_ascii=False,indent=2)+'\n','utf-8',newline='\n')
print(json.dumps({'files':len(files),'runs':runs},ensure_ascii=False))
