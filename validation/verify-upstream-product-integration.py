"""Actual product consumers, fixed artifacts and explicit failure injections."""
import copy
import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZipFile
from uuid import uuid4

from pptx import Presentation
from yoloongppt.artifacts import RunArtifacts, sha256
from yoloongppt.evidence import EvidenceStore
from yoloongppt.errors import TaskError, trace_id
from yoloongppt.operations import dispatch
from yoloongppt.quality import check as quality_check
from yoloongppt.review import validate_review
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.source_roles import assign, fact_input
from yoloongppt.sources import inspect_sources
from yoloongppt.template_layout_runtime import choose
from yoloongppt.template_registry import register, get
from yoloongppt.existing_deck import inspect_deck

OUT=Path('/runtime/upstream-product-integration')/uuid4().hex;OUT.mkdir(parents=True,exist_ok=False)
schemas=SchemaRegistry();checks=[]


def save(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')


def verify(name,condition,detail=None):
    if not condition:
        save('failure.json',{'check':name,'detail':detail});raise AssertionError(name)
    checks.append({'check':name,'passed':True,'detail':detail})


def reject(name,call,code):
    try:call()
    except TaskError as exc:
        save('failures/'+name+'.json',exc.result('upstream-product-integration'))
        verify(name,exc.code==code,{'expected':code,'actual':exc.code})
        return exc
    raise AssertionError(name+' did not fail')


prior=Path('/workspace/validation/stage-closure-artifacts/description-generated')
# quality.check writes current adapter evidence. Work on a byte-identical copy,
# preserving the original committed actual rendering/model outputs.
run=OUT/'old-six-page'
if not run.exists():shutil.copytree(prior,run)
deck=json.loads((run/'deck-spec.json').read_text('utf-8'))
sources=json.loads((run/'approved-source-result.json').read_text('utf-8'))
mapping=json.loads((run/'object-map.json').read_text('utf-8'))
renders=json.loads((run/'render-report.json').read_text('utf-8'))
quality=quality_check(deck,run/'deck.pptx',mapping,sources,renders,run)
save('quality-report.json',quality)
verify('Main quality.check executes original PPTAgent freshness',any('PPTAgent render_current' in c.get('check','') for c in quality['checks']))
verify('Main quality.check executes PPT Master native OPC audit',(run/'upstream-native-audit.json').is_file() and any(c.get('kind')=='PPT Master OPC delivery audit' for c in quality['checks']))
verify('Main quality.check automatically locates original cover instruction leakage',any(i['code']=='TASK_INSTRUCTION_LEAK' and i['object_id'] for i in quality['issues']))
response=json.loads((run/'review-response.json').read_text('utf-8'))
review=validate_review(copy.deepcopy(response),deck,sources,list(range(6)))
verify('Product review validates saved real six-page response through upstream contract',review['checked_slide_orders']==list(range(6)))
malformed=copy.deepcopy(response);malformed['summary']=''
reject('review-empty-summary',lambda:validate_review(malformed,deck,sources,list(range(6))),'UPSTREAM_VISUAL_REVIEW_INVALID')

template=Path('/workspace/validation/template-slot-artifacts/enterprise.pptx')
policy={'version':'template-policy-1','typography':{'font':'Noto Sans CJK SC','sizes':{'title':28,'body':20}},
        'layout_part':'ppt/slideLayouts/slideLayout2.xml',
        'brand':{'locked_objects':[{'part':'ppt/slideMasters/slideMaster1.xml','name':'LockedLogo'},{'part':'ppt/slideMasters/slideMaster1.xml','name':'LockedFooter'}],
                 'safe_areas':[[0,6.8,13.333333,.7]],'locked_tokens':{'font':'Noto Sans CJK SC','foreground':'000000','background':'FFFFFF','accent':'176548'}}}
record=register(template,source='Previously verified artificial enterprise fixture',license='user-provided artificial fixture',root=str(OUT/'template-registry'),allowed_roots=['/workspace'],schemas=schemas,policy=policy)
save('template-record.json',record)
verify('Template registry actually publishes Presenton-derived layout schemas',record['preview']['upstream_layout_schemas']['native_source'] and bool(record['preview']['upstream_layout_schemas']['layouts']))
verify('Registered persisted upstream template remains schema-valid',get(record['template_id'],root=str(OUT/'template-registry'),schemas=schemas)==record)
style={'font':'Noto Sans CJK SC','foreground':'000000','background':'FFFFFF','accent':'176548'}
content={'title':'模板融合接入验证','body':['第一段完整保留。','第二段完整保留。'],'evidence_refs':[sources['evidence'][0]['evidence_id']],
         'kind':'text','goal':'保留原生槽位','notes':'人工输入用于软件验证。','rationale':'真实模板槽位集成','table':None,'chart':None}
selected=choose(record,content,style)
schemas.validate('template-layout-runtime.schema.json',selected)
save('template-selection.json',selected)
verify('Native template choose executes upstream selected-slot validation',selected['selection']['upstream_validation']['valid'])
verify('Selected template body preserves both original paragraphs',next(e for e in selected['elements'] if e['role']=='body')['text']==content['body'])
verify('Template fusion keeps actual logo/footer locks',len(selected['locks']['objects'])==2)

# Dispatch original edit-deck consumers, keeping all untouched ZIP members.
before=inspect_deck(run/'deck.pptx');objects=[o for s in before['slides'] for o in s['objects']]
table=next(o for o in objects if 'table' in o)
chart=next(o for o in objects if 'chart' in o)
values={'categories':chart['chart']['series'][0]['categories'],
        'series':[{'name':s['name'][0],'values':[float(x) for x in s['values']]} for s in reversed(chart['chart']['series'])]}
requests=[('table-edit',table,{'operation':'table_cell','value':{'row':1,'column':0,'text':'A楼（软件验证修订）'}}),
          ('chart-edit',chart,{'operation':'chart_data','value':values})]
for name,target,patch in requests:
    request={'expected_sha256':before['source_sha256'],'patches':[{'object_id':target['object_id'],**patch}]}
    result=dispatch('edit_deck',{'path':str(run/'deck.pptx'),'request':request},trace_id(),schemas=schemas)
    save(name+'.json',result)
    edited=result['result'];output=Path(edited['pptx'])
    with ZipFile(run/'deck.pptx') as original,ZipFile(output) as after:
        verify(name+' preserves every non-target package payload',all(original.read(n)==after.read(n) for n in original.namelist() if n not in edited['changed_parts']),{'changed_parts':edited['changed_parts']})
    after=inspect_deck(output)
    actual=next(o for s in after['slides'] for o in s['objects'] if o['object_id']==target['object_id'])
    old_other={o['object_id']:o for o in objects if o['object_id']!=target['object_id']}
    new_other={o['object_id']:o for s in after['slides'] for o in s['objects'] if o['object_id']!=target['object_id']}
    verify(name+' preserves non-target native object records',old_other==new_other)
    if name=='table-edit':verify('Upstream table guard permits actual single-cell editable change',actual['table'][1][0]=='A楼（软件验证修订）')
    else:verify('Upstream chart guard permits real data rewrite with native labels/series',actual['chart']['series']==[
        {'name':[s['name']],'categories':values['categories'],'values':[str(v) for v in s['values']]} for s in values['series']])

# Import known real-model artificial source IDs into an isolated actual SQLite
# store. This preserves the original call/response bytes and actual source text;
# no provider, product function or output is replaced with a mock.
real=Path('/runtime/fact-batches-artifacts/real-model')
payloads=[json.loads(json.loads((real/'fact-batches'/('batch-'+str(i).zfill(4)+'-request.json')).read_text('utf-8'))['messages'][1]['content'])['evidence'][0] for i in range(4)]
task=json.loads((prior/'task.json').read_text('utf-8'))
task['sources']=[{'source_id':p['source_id'],'kind':'text','content':p['text'],'metadata':{'source_role':'fact'}} for p in payloads]
task['runtime_preferences']['fact_batch_policy']={'max_batch_evidence':1}
task['raw_request']['request']['raw_text']='人工软件验证：保留A楼本期100与110的来源冲突，不选其中任何一个；B楼本期和A楼目标分别保留。'
store=EvidenceStore(OUT/'fixture-evidence.sqlite3')
inspected=inspect_sources(task,schemas,store,trace_id())
with store.connect() as db:
    for item in inspected['evidence']:
        original=next(p for p in payloads if p['source_id']==item['source_id'])
        verify('Imported fixture source literal matches actual model input '+item['source_id'],item['raw_text']==original['text'])
        updated={**item,'evidence_id':original['evidence_id'],'metadata':{**item['metadata'],'source_context':original['source_context']}}
        db.execute('UPDATE evidence SET evidence_id=?,body=? WHERE source_id=? AND source_hash=? AND parser_version=? AND segment_index=?',
                   (original['evidence_id'],json.dumps(updated,ensure_ascii=False),item['source_id'],item['source_hash'],item['parser_version'],item['segment_index']))
inspected=inspect_sources(task,schemas,store,trace_id())
roles=assign({'task':task,'source_bundle':inspected['source_bundle']},schemas,trace_id())
facts=fact_input(inspected,roles['source_role_map'])
verify('Actual product source/role consumers replay original real-model IDs',{e['evidence_id'] for e in facts['evidence']}=={p['evidence_id'] for p in payloads})
checkpoint=RunArtifacts()
for file in real.rglob('*'):
    if not file.is_file():continue
    destination=checkpoint.path/file.relative_to(real);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(file.read_bytes())
checkpoint.json('task.json',task);checkpoint.json('source-result.json',inspected);checkpoint.json('fact-source-result.json',facts)
checkpoint.json('fact-interpretation.json',json.loads((real/'fact-model-response.json').read_text('utf-8')))
checkpoint.json('fixture-provenance.json',{'type':'artificial literal source fixture with existing authorized real model responses',
                                        'original_calls':str(real),'id_import':'same source_id and exact original text; no altered response or model substitution'})
checkpoint.json('manifest.json',{'run_id':checkpoint.run_id,'artifacts':checkpoint.manifest()})
save('checkpoint-fixture.json',{'run_id':checkpoint.run_id,'path':str(checkpoint.path),'task':task})


def resumed_failure(case,expected):
    error=reject(case,lambda:dispatch('resume',{'run_id':case_artifact.run_id},trace_id(),schemas=schemas,store=store),expected)
    run_id=next(d['run_id'] for d in error.details if 'run_id' in d)
    output=Path('/runtime/runs')/run_id
    timeline=json.loads((output/'pipeline-trace.json').read_text('utf-8'))['steps']
    verify(case+' makes no new fact-model execution',all('FactInterpreter' not in s['component'] for s in timeline))
    return output


case_artifact=checkpoint
replayed=resumed_failure('checkpoint-valid-unresolved-conflict','FACT_DECISION_UNRESOLVED')
verify('Valid checkpoint preserves every original batch artifact byte',all((replayed/file.relative_to(checkpoint.path)).read_bytes()==file.read_bytes() for file in checkpoint.path.rglob('*') if file.is_file() and (str(file.relative_to(checkpoint.path)).startswith('fact-batches/') or file.name in {'fact-batch-plan.json','fact-model-request.json','fact-model-response.json','fact-model-call.json'})))
verify('Valid checkpoint explicitly records no fresh model call',json.loads((replayed/'fact-checkpoint.json').read_text('utf-8'))['fresh_fact_model_call'] is False)


def clone_checkpoint():
    duplicate=RunArtifacts()
    for file in checkpoint.path.rglob('*'):
        if file.is_file():
            target=duplicate.path/file.relative_to(checkpoint.path);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(file.read_bytes())
    return duplicate


case_artifact=clone_checkpoint()
(case_artifact.path/'fact-batches/batch-0001-response.json').unlink()
resumed_failure('checkpoint-missing-batch-response','FACT_CHECKPOINT_CHANGED')
case_artifact=clone_checkpoint()
changed=case_artifact.path/'fact-batches/alignment-response.json';changed.write_bytes(changed.read_bytes()+b'\n')
resumed_failure('checkpoint-changed-alignment-bytes','FACT_CHECKPOINT_CHANGED')
case_artifact=clone_checkpoint()
(case_artifact.path/'fact-batch-plan.json').unlink()
resumed_failure('checkpoint-missing-plan','FACT_CHECKPOINT_INCOMPLETE')

summary={'checks':checks,'passed':len(checks),'fresh_model_calls':0,'new_renders':0,
         'source_evidence':'Previously committed real six-page deck/render/review and authorized 4-source model response; imported artificial fixture IDs explicitly recorded.',
         'scope':'Actual product integration and failure injections, not full AC or new PDF acceptance.'}
save('summary.json',summary)
print(json.dumps({'passed':len(checks),'fresh_model_calls':0,'summary':str(OUT/'summary.json')},ensure_ascii=False))
