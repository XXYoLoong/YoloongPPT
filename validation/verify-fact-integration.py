"""Actual saved provider/PPTX/render evidence, consumed projection and revision guards."""
import copy,hashlib,json,subprocess,sys,urllib.request,urllib.error
from pathlib import Path
from pptx import Presentation
from yoloongppt.schemas import ROOT,SchemaRegistry
from yoloongppt.quality import check,numbers
from yoloongppt.revision import revision_sources
from yoloongppt.errors import TaskError

s=SchemaRegistry();cases=[]
def record(id,condition,actual):
 assert condition,id
 cases.append({'id':id,'passed':True,'actual':actual})
def load(folder,name):return json.loads((folder/name).read_text('utf-8'))
def post(path,body):
 req=urllib.request.Request('http://127.0.0.1:8000'+path,data=json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
 try:r=urllib.request.urlopen(req,timeout=300)
 except urllib.error.HTTPError as e:r=e
 return r.status,json.loads(r.read())
root=Path('/runtime/runs/6ed1b3c5-a6c0-47cb-888c-fc841ab610c5');blocked=Path('/runtime/runs/a3924701-c060-489b-bc32-1f7b0f3f54f7')
record('real_conflict_stopped_before_content_model',load(blocked,'failure.json')['error']['code']=='FACT_DECISION_UNRESOLVED' and (blocked/'decision-evidence.json').exists() and not (blocked/'model-call.json').exists(),'Actual source extraction model called; main content model and PPT writer not called.')
boundary=load(root,'fact-boundary.json');sources=revision_sources(root);deck=load(root,'deck-spec.json');renders=load(root,'render-report.json');object_map=load(root,'object-map.json')
quality=check(deck,root/'deck.pptx',object_map,sources,renders,root)
record('current_qa_on_actual_four_pages',quality['p0_issue_count']==0 and load(root,'quality-report.json')['p0_issue_count']==0,'Current deterministic checks and saved real image review have zero P0; system acceptance still not_passed.')
record('real_native_pptx',len(Presentation(root/'deck.pptx').slides)==4 and len(object_map['objects'])>0,{'pages':4,'native_objects':len(object_map['objects'])})
record('real_render_bytes',all(hashlib.sha256((root/a['path']).read_bytes()).hexdigest()==a['hash'] for a in renders['artifacts']),{'render_artifacts':len(renders['artifacts'])})
model=load(root,'model-call.json');factcall=load(root,'fact-model-call.json');review=load(root,'review-model-call.json')
record('actual_model_provenance',all(m['real_model_call'] and m['response_id'] for m in [model,factcall,review]),{'fact_response':factcall['response_id'],'content_response':model['response_id'],'image_review_response':review['response_id']})
record('fact_checkpoint_reuse_disclosed',load(root,'fact-checkpoint.json')['reused_from_run']=='61fda8d9-6794-4658-886d-f8caecb2cca0','Source/hash identity checked; real original extraction reused; fresh content and visual models called.')
for name in ['decision-evidence.json','decision-fact-boundary.json']:s.validate('decision-trace.schema.json',load(root,name))
record('actual_DEC004_005_traces_valid',True,'Inputs, candidates, chosen IDs, rules/hash, output, time/error retained.')
packet=json.loads(load(root,'model-request.json')['messages'][1]['content'])
record('actual_copy_input_excludes_9','9%' not in json.dumps(packet,ensure_ascii=False) and '8%' in json.dumps(packet,ensure_ascii=False),'Rejected value remains in full source/decision/independent reviewer; absent from copy generation packet.')
text='\n'.join(t for slide in deck['slides'] for t in [slide['content']['title'],*slide['content']['body']])
record('actual_copy_8_with_disclosure','9%' not in text and '8%' in text and '【已选来源】' in text,text)
negative=copy.deepcopy(deck);negative['slides'][0]['content']['body']=['2026年降低能耗9%。']
issues=check(negative,root/'deck.pptx',object_map,sources,renders,root)['issues']
record('negative_spec_rejected_value_detected',any(i['code']=='FACT_NUMBER_UNSUPPORTED' and '9%' in i['detail']['numbers_not_found_in_cited_evidence'] for i in issues),'Modified spec fixture, actual original PPTX; numeric guard specifically catches rejected 9%.')
before=hashlib.sha256((root/'deck.pptx').read_bytes()).hexdigest();body=next(e for e in deck['slides'][0]['elements'] if e['role']=='body')
status,error=post('/revise/'+root.name,{'object_id':body['object_id'],'replacement_text':['2026年降低能耗9%。'],'reason':'验证被否决数值不能经修订重新进入。'})
record('HTTP_revision_rejected_value_before_write',status==422 and error['error']['code']=='REVISION_FACT_UNSUPPORTED' and hashlib.sha256((root/'deck.pptx').read_bytes()).hexdigest()==before,error['error']['code'])
title=next(e for e in deck['slides'][0]['elements'] if e['role']=='title')
if '--reuse-revision' in sys.argv:
 previous=load(Path('/runtime/fact-validation'),'fact-integration.json');revised=Path('/runtime/runs')/previous['revision_run_id'];result=load(revised,'result.json');status=200
 result={**result,'verification_evidence_reused':True,'fresh_revision_or_review_call_this_check':False}
else:status,result=post('/revise/'+root.name,{'object_id':title['object_id'],'replacement_text':['【已选来源】2026年试点节能8%'],'reason':'验证单对象修订继续保留已选事实与来源。'})
record('HTTP_revision_selected_fact_preserved',status==200 and result['ok'] and result['qa']['p0_issue_count']==0,result)
revised=Path(result['artifact_root']);history=load(revised,'revision-history.json')
record('revision_part_boundary_preserved',len(history['changed_parts'])==1 and history['unchanged_parts_byte_preserved'],'Only selected slide XML part changes; other parts bytes preserved.')
record('revision_fact_snapshot_preserved',revision_sources(revised)['approved_texts']==sources['approved_texts'] and all((revised/name).is_file() for name in ['decision-evidence.json','decision-fact-boundary.json','fact-boundary.json']),'Same selected value map, evidence, conflict trace and boundary copied into revised version.')
mapping=load(ROOT/'validation','fact-project-map.json')
for node in ['DEC-004','DEC-005']:
 record('five_project_mapping_'+node,{p['project'] for p in mapping['mapping'][node]}=={'P01','P02','P03','P04','P05'},'Fixed-source partial and not_found are explicit; no claimed upstream conflict algorithm.')
paths=[*sorted((ROOT/'src/yoloongppt').glob('*.py')),*sorted((ROOT/'contracts').glob('*.schema.json'))]
report={'passed':True,'cases':cases,'base_run_id':root.name,'revision_run_id':revised.name,'blocked_run_id':blocked.name,'checkpoint_run_id':'61fda8d9-6794-4658-886d-f8caecb2cca0','initial_p0_run_ids':['cb886c7a-49d8-4568-8c31-45edcc49aa86','c747e330-82f1-4d5a-be80-37b59ca4e89c'],
        'scope':'Actual DEC-004/005 source priority + four-page native generation + single-object revision; full semantic extraction, all formats/decisions/QA and AC remain incomplete.','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
Path('/runtime/fact-validation/fact-integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'passed':True,'checks':len(cases),'run_id':root.name,'revision_run_id':revised.name},ensure_ascii=False))
