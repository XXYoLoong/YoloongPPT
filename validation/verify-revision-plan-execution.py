"""SYS-016/REV-006/010 actual geometry+color consumer, single real-page review."""
import argparse,copy,json,hashlib,shutil,time
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from yoloongppt.artifacts import RunArtifacts,sha256
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.errors import TaskError,trace_id
from yoloongppt.revision import revise_plan,revision_sources,DECISION_FILES
from yoloongppt.revision_plans import build_plan,validate_plan
from yoloongppt.quality import check
from yoloongppt.existing_deck import apply_patch,inspect_deck

args=argparse.ArgumentParser();args.add_argument('--execute',action='store_true');args.add_argument('--reuse-result');opts=args.parse_args()
parent_id='5be192ef-798f-4bb0-9c93-c24bcc279aa4';parent=Path('/runtime/runs')/parent_id;output=Path('/runtime/revision-plan-validation');output.mkdir(exist_ok=True);schemas=SchemaRegistry();checks=[];source_before=sha256(parent/'deck.pptx');trace=trace_id()
load=lambda p,n:json.loads((p/n).read_text('utf-8'))
def test(name,condition,observation=None):checks.append({'name':name,'passed':bool(condition),'observation':observation});assert condition,name

def rejected(name,fn,code):
 try:fn()
 except TaskError as e:test(name,e.code==code,{'code':e.code});return
 raise AssertionError(name+' was not rejected')

def write_report(state,fixture_id=None,result=None):
 paths=[Path('/workspace/src/yoloongppt')/n for n in ['revision.py','revision_plans.py','existing_deck.py','quality.py','quality_rules.py','quality_decisions.py']]+[Path('/workspace/validation/verify-revision-plan-execution.py')]
 report={'passed':all(c['passed'] for c in checks),'state':state,'checks':checks,'parent_run_id':parent_id,'fixture_run_id':fixture_id,'fixture_identity':'artificial geometry/color fault injection over unchanged real generated parent; not AI newly generated','result':result,'model_calls':1 if result else 0,'source_hashes':{str(p.relative_to('/workspace')):sha256(p) for p in paths},'parent_pptx_sha256':source_before,'system_acceptance':'not_passed'}
 (output/'revision-plan-execution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'passed':report['passed'],'state':state,'checks':len(checks),'fixture_run_id':fixture_id,'run_id':result['run_id'] if result else None},ensure_ascii=False));return report

deck=load(parent,'deck-spec.json');mapping=load(parent,'object-map.json');slide=deck['slides'][0];title=next(e for e in slide['elements'] if e['role']=='title');body=next(e for e in slide['elements'] if e['role']=='body');native=inspect_deck(parent/'deck.pptx');actual={o['name']:o for o in native['slides'][0]['objects']}
# Prepare a directly-consumable color plan for safety-only calls: failures precede any writer/model.
from yoloongppt.quality_rules import issue
selected_issue=issue('TEXT_CONTRAST_LOW',slide['slide_id'],'Injected test candidate','QA-009',object_id=title['object_id'],action={'node':'style','mode':'local_revision'})
plan=build_plan(deck,mapping,[selected_issue],trace=trace,parent_run_id=parent_id)
rejected('invalid_request_no_writer',lambda:revise_plan(parent_id,{'plan':plan,'ignore_locks':True},schemas,trace),'REVISION_PLAN_REQUEST_INVALID')
bad=copy.deepcopy(plan);bad['parent_run_id']='00000000-0000-0000-0000-000000000000';rejected('wrong_parent_no_writer',lambda:revise_plan(parent_id,{'plan':bad},schemas,trace),'REVISION_PLAN_PARENT_CHANGED')
bad=copy.deepcopy(plan);bad['actions'][0]['before_spec']['text']=['tampered'];rejected('stale_before_spec_no_writer',lambda:revise_plan(parent_id,{'plan':bad},schemas,trace),'REVISION_PLAN_STALE')
bad=copy.deepcopy(plan);bad['locked_object_ids']=[title['object_id']];rejected('locked_target_no_writer',lambda:revise_plan(parent_id,{'plan':bad},schemas,trace),'REVISION_PLAN_TARGET_INVALID')
bad=copy.deepcopy(plan);bad['scope']['object_ids'].append(body['object_id']);rejected('scope_expansion_no_writer',lambda:revise_plan(parent_id,{'plan':bad},schemas,trace),'REVISION_PLAN_SCOPE_INVALID')
bad=copy.deepcopy(plan);bad['actions'][0]['changes']['format']['font_size']=1;rejected('format_extra_field_no_writer',lambda:revise_plan(parent_id,{'plan':bad},schemas,trace),'REVISION_PLAN_FORMAT_INVALID')
bad=copy.deepcopy(plan);bad['actions'][0]['changes']['replacement_text']=['undisclosed text'];rejected('format_extra_operation_no_writer',lambda:revise_plan(parent_id,{'plan':bad},schemas,trace),'REVISION_PLAN_CHANGES_INVALID')
locked_deck=copy.deepcopy(deck);locked_deck['slides'][0]['elements'][0]['locked']=True;rejected('persistent_element_lock_revalidated',lambda:validate_plan(plan,locked_deck,mapping),'REVISION_PLAN_TARGET_LOCKED')
test('negative_cases_parent_byte_unchanged',sha256(parent/'deck.pptx')==source_before)
if not opts.execute and not opts.reuse_result:write_report('safety_verified_no_model');raise SystemExit()
if opts.reuse_result:
 result=load(Path('/runtime/runs')/opts.reuse_result,'result.json');fixture=Path('/runtime/runs')/result['parent_run_id'];fixture_id=fixture.name
else:
 artifact=RunArtifacts();fixture=artifact.path;fixture_id=artifact.run_id
 # Whitelist only known immutable inputs/decision evidence/outputs required by consumer.
 required=['task.json','task-effective.json','deck-spec.json','source-result.json','object-map.json','quality-report.json','render-report.json',*DECISION_FILES]
 for name in dict.fromkeys(required):
  if (parent/name).is_file():shutil.copyfile(parent/name,fixture/name)
 renders=load(parent,'render-report.json')
 render_paths=[a['path'] for a in renders['artifacts']]+[renders['render_text_path']]+([renders['render_bbox_path']] if renders.get('render_bbox_path') else [])
 for name in dict.fromkeys(render_paths):
  destination=fixture/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(parent/name,destination)
 patches=[{'object_id':actual[title['object_id']]['object_id'],'operation':'format','value':{'color':slide['style']['background']}},{'object_id':actual[body['object_id']]['object_id'],'operation':'geometry','value':[14,body['bounds'][1],body['bounds'][2],body['bounds'][3]]}]
 injected=apply_patch(parent/'deck.pptx',fixture/'deck.pptx',{'expected_sha256':source_before,'patches':patches})
 fixture_deck=copy.deepcopy(deck);fixture_title=next(e for e in fixture_deck['slides'][0]['elements'] if e['object_id']==title['object_id']);fixture_title.setdefault('format',{})['color']=slide['style']['background'];artifact.json('deck-spec.json',fixture_deck)
 source=revision_sources(parent);qa=check(fixture_deck,fixture/'deck.pptx',mapping,source,renders,fixture)
 qa['model_review']=load(parent,'quality-report.json').get('model_review',{})
 qa['p0_issue_count']+=sum(i['severity']=='P0' for i in qa['model_review'].get('issues',[]));qa['fixture_note']='Model review/render snapshots belong to original unmodified parent; artificial faults have deterministic native checks only until consumer creates new renders/first-page real review.'
 artifact.json('quality-report.json',qa)
 identity={'fixture':True,'kind':'artificial_fault_injection','not_ai_generated':True,'source_run_id':parent_id,'source_sha256':source_before,'injected_objects':[title['object_id'],body['object_id']],'injection_report':injected,'stale_render_snapshot_for_original_parent':True};artifact.json('fixture-identity.json',identity)
 selected_codes={'TEXT_CONTRAST_LOW','ACTUAL_TEXT_CONTRAST_LOW','OBJECT_GEOMETRY_MISMATCH','OBJECT_OUT_OF_BOUNDS'}
 selected_issues=[i for i in qa['issues'] if i['code'] in selected_codes and i.get('object_id') in {title['object_id'],body['object_id']}]
 identity['explicit_requested_scope']='only two-object geometry/color consumer verification; not repair all original QA issues'
 identity['selected_issue_ids']=[i['issue_id'] for i in selected_issues];identity['unselected_issues_preserved']=[i for i in qa['issues'] if i not in selected_issues];artifact.json('fixture-identity.json',identity)
 fixplan=build_plan(fixture_deck,mapping,selected_issues,trace=trace,parent_run_id=fixture_id);artifact.json('revision-plan.json',fixplan);artifact.json('manifest.json',{'run_id':fixture_id,'artifacts':artifact.manifest()})
 test('injected_fixture_two_safe_actions',fixplan['status']=='ready' and len(fixplan['actions'])==2 and {a['operation'] for a in fixplan['actions']}=={'geometry','format'},{'status':fixplan['status'],'actions':len(fixplan['actions']),'issues':[i['code'] for i in qa['issues']]})
 # Exactly one fresh model review for changed page 0, performed by the real consumer.
 result=revise_plan(fixture_id,{'plan':fixplan},schemas,trace)
 output_run=Path('/runtime/runs')/result['run_id'];(output/'last-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
output_run=Path('/runtime/runs')/result['run_id'];history=load(output_run,'revision-history.json');quality=load(output_run,'quality-report.json');after_deck=load(output_run,'deck-spec.json');after_map=load(output_run,'object-map.json')
test('consumer_actual_success',result['ok'] and result['operation']=='revise' and result['system_acceptance']=='not_passed')
test('exactly_two_objects_selected',set(history['scope']['object_ids'])=={title['object_id'],body['object_id']})
test('fresh_real_review_one_page',quality['model_review']['fresh_checked_slide_orders']==[0] and (output_run/'review-model-call.json').is_file())
call=load(output_run,'review-model-call.json');test('real_model_identity_recorded','model' in call or 'usage' in call,call)
with ZipFile(fixture/'deck.pptx') as before,ZipFile(output_run/'deck.pptx') as after:
 changed=[n for n in before.namelist() if before.read(n)!=after.read(n)];test('only_selected_page_part_changed',changed==['ppt/slides/slide1.xml'],changed);test('unselected_parts_byte_preserved',all(before.read(n)==after.read(n) for n in before.namelist() if n not in changed))
 ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
 def shapes(blob):
  tree=etree.fromstring(blob);return {n.xpath('.//p:cNvPr',namespaces=ns)[0].get('name'):etree.tostring(n) for n in tree.xpath('./p:cSld/p:spTree/*',namespaces=ns) if n.xpath('.//p:cNvPr',namespaces=ns)}
 b=shapes(before.read('ppt/slides/slide1.xml'));a=shapes(after.read('ppt/slides/slide1.xml'));test('unselected_page_object_byte_preserved',all(a[n]==b[n] for n in b if n not in {title['object_id'],body['object_id']}))
test('native_mapping_entity_ids_preserved',after_map==load(fixture,'object-map.json'))
test('fact_snapshot_byte_preserved',all((fixture/n).read_bytes()==(output_run/n).read_bytes() for n in ['approved-source-result.json','fact-boundary.json','evidence-resolution.json','fact-interpretation.json']))
test('history_actual_hashes_and_qa',history['before_pptx_hash']==sha256(fixture/'deck.pptx') and history['after_pptx_hash']==sha256(output_run/'deck.pptx') and history['unchanged_parts_byte_preserved'] and history['quality_before'] and history['quality_after'])
test('fresh_renders_written',len([a for a in load(output_run,'render-report.json')['artifacts'] if a['type']=='png'])==len(deck['slides']))
test('quality_pipeline_decision_saved',all((output_run/n).is_file() for n in ['decision-DEC-039.json','decision-DEC-040.json','revision-plan.json','completion-decision.json']))
test('p0_faults_actually_removed',not any(i['code'] in {'OBJECT_OUT_OF_BOUNDS','OBJECT_GEOMETRY_MISMATCH','TEXT_CONTRAST_LOW','ACTUAL_TEXT_CONTRAST_LOW'} for i in quality['issues']))
test('original_parent_preserved_through_positive',sha256(parent/'deck.pptx')==source_before)
write_report('actual_consumer_verified',fixture_id,result)
