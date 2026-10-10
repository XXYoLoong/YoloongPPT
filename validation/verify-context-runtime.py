"""Bounded DEC-002/003 contract, trace, CLI/API and live generation evidence."""
import copy
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from pptx import Presentation
from yoloongppt.context import normalize
from yoloongppt.errors import TaskError,trace_id
from yoloongppt.planning import preflight
from yoloongppt.schemas import ROOT,SchemaRegistry
from yoloongppt.source_roles import assign,fact_input
from yoloongppt.revision import revision_sources

s=SchemaRegistry();cases=[];traces=[]
def record(id,condition,actual):
    assert condition,id
    cases.append({'id':id,'passed':True,'actual':actual})
def fail(id,fn,code):
    try:fn()
    except TaskError as e:record(id,e.code==code,e.code)
    else:raise AssertionError(id)
fixtures=json.loads((ROOT/'validation/context-cases.json').read_text(encoding='utf-8'))['cases']
for fixture in fixtures:
    result=normalize(fixture['input'],s,trace_id()) if fixture['node']=='DEC-002' else assign(fixture['input'],s,trace_id())
    output=result.get('context',result.get('source_role_map'))
    for key,val in fixture['expected'].items():
        assert len(output['fact_source_ids'])==val if key=='fact_count' else output[key]==val,(fixture['id'],key)
    record(fixture['id'],True,output)
    traces.append({'fixture_id':fixture['id'],'trace':result['decision_trace']})
soft=normalize(fixtures[1]['input'],s,trace_id())['context']
record('soft_applied_not_ignored',soft['constraints']['soft'][0]['disposition']=='applied' and preflight(fixtures[1]['input'],soft,s)[0]==8,'Eight-page preference reaches execution preflight.')
default=normalize(fixtures[2]['input'],s,trace_id())['context']
record('caller_default_consumed',default['constraints']['defaults'][0]['used'] and default['page_target']==6,'Caller default wins before built-in ten.')
over=normalize(fixtures[6]['input'],s,trace_id())['context']
record('hard_overrides_soft_with_reason',over['constraints']['soft'][0]['disposition']=='overridden' and bool(over['constraints']['soft'][0]['handling_reason']),'Hard ten overrides soft seven explicitly.')
fail('unknown_hard_blocks',lambda:preflight(fixtures[7]['input']),'HARD_CONSTRAINT_UNSUPPORTED')
fail('hard_conflict_blocks',lambda:preflight(fixtures[4]['input']),'HARD_CONSTRAINT_CONFLICT')
outputtest=copy.deepcopy(fixtures[0]['input']);outputtest['raw_request']={'request':{'raw_text':'','attachments':[],'requested_mode':'create_from_materials','requested_outputs':['pptx']},'attachment_roles':[]}
record('raw_output_requirement_consumed',normalize(outputtest,s,trace_id())['context']['status']=='normalized','Raw requested format must be included in effective formats.')
outputtest['raw_request']['request']['requested_outputs']=['docx']
fail('raw_output_requirement_not_ignored',lambda:preflight(outputtest),'OUTPUT_FORMAT_UNSUPPORTED')
outputtest['output']['formats']=42;outputtest['raw_request']['request']['requested_outputs']=['pptx']
fail('malformed_effective_format_blocks',lambda:preflight(outputtest),'OUTPUT_FORMAT_UNSUPPORTED')
rolefixture=fixtures[12]['input'];roles=assign(rolefixture,s,trace_id())['source_role_map']
mock_sources={'evidence':[{'source_id':x['source_id'],'evidence_id':'unit-'+str(i)} for i,x in enumerate(rolefixture['task']['sources'])],'documents':[{'source_id':x['source_id']} for x in rolefixture['task']['sources']]}
filtered=fact_input(mock_sources,roles)
record('style_not_fact_all_inputs_preserved',len(filtered['evidence'])==1 and len(roles['preserved_source_ids'])==2,'Fixture verifies selection only; not a model generation claim.')
def http(path,body):
    req=urllib.request.Request('http://127.0.0.1:8000'+path,data=json.dumps(body).encode('utf-8'),headers={'Content-Type':'application/json'})
    try:r=urllib.request.urlopen(req,timeout=30)
    except urllib.error.HTTPError as e:r=e
    return r.status,json.loads(r.read())
status,api=http('/context',fixtures[1]['input'])
record('HTTP_context_trace_saved',status==200 and api['context']['page_target']==8 and Path(api['artifact_root'],'decision-context.json').is_file(),{'run_id':api['run_id']})
folder=Path('/runtime/context-validation');folder.mkdir(exist_ok=True)
guard=folder/'revision-guard';guard.mkdir(exist_ok=True)
(guard/'source-role-map.json').write_text(json.dumps(roles),encoding='utf-8')
if (guard/'fact-source-result.json').exists():(guard/'fact-source-result.json').unlink()
fail('revision_missing_fact_snapshot_blocks',lambda:revision_sources(guard),'FACT_SOURCE_SNAPSHOT_MISSING')
(guard/'fact-source-result.json').write_text(json.dumps(mock_sources),encoding='utf-8')
fail('revision_contaminated_fact_snapshot_blocks',lambda:revision_sources(guard),'FACT_SOURCE_ROLE_MISMATCH')
inputfile=folder/'source-roles-input.json';inputfile.write_text(json.dumps(rolefixture,ensure_ascii=False),encoding='utf-8')
cli=subprocess.run([sys.executable,'-m','yoloongppt','source-roles',str(inputfile)],capture_output=True,text=True,encoding='utf-8')
result=json.loads(cli.stdout)
record('CLI_roles_trace_saved',cli.returncode==0 and result['source_role_map']['status']=='assigned' and Path(result['artifact_root'],'decision-source-roles.json').is_file(),{'run_id':result['run_id']})
status,error=http('/generate',fixtures[4]['input'])
record('HTTP_conflict_before_model',status==422 and error['error']['code']=='HARD_CONSTRAINT_CONFLICT',error['error']['code'])
info=next(d for d in error['error']['details'] if 'artifact_root' in d);blocked=Path(info['artifact_root'])
record('conflict_evidence_preserved_no_model',(blocked/'decision-context.json').is_file() and not (blocked/'model-call.json').exists(),'Actual product entry stopped before provider invocation.')
mapping=json.loads((ROOT/'validation/context-project-map.json').read_text(encoding='utf-8'))
record('five_project_counterparts',{x['project'] for x in mapping['mapping']['DEC-002']}=={x['project'] for x in mapping['mapping']['DEC-003']}=={'P01','P02','P03','P04','P05'},'Indexed source counterparts and Not found boundaries; no copied source.')
if len(sys.argv)>1:
    run=Path('/runtime/runs')/sys.argv[1];load=lambda name:json.loads((run/name).read_text(encoding='utf-8'))
    ctx=load('presentation-context.json');rolemap=load('source-role-map.json');full=load('source-result.json');facts=load('fact-source-result.json')
    record('real_E2E_eight_page_constraints',ctx['page_target']==8 and len(Presentation(run/'deck.pptx').slides)==8 and load('task-effective.json')['constraints']['soft'][0]['disposition']=='applied',{'run_id':sys.argv[1],'pages':8})
    record('real_E2E_style_excluded_preserved',len(rolemap['preserved_source_ids'])==2 and len(rolemap['fact_source_ids'])==1 and len(full['documents'])==2 and len(facts['documents'])==1,rolemap['source_roles'])
    request=load('model-request.json');parsed=json.loads(request['messages'][1]['content']);known={e['evidence_id'] for e in facts['evidence']}
    record('real_model_only_fact_evidence',{e['evidence_id'] for e in parsed['sources']}==known and all('999999' not in e['text'] for e in parsed['sources']),{'sent_evidence':len(known),'nonfact_sources_retained':1})
    record('revision_QA_preserves_fact_boundary',revision_sources(run)['evidence']==facts['evidence'] and all('999999' not in e['raw_text'] for e in revision_sources(run)['evidence']),'Revision/recheck share guarded factual snapshot selector; no model rerun for this check.')
    record('three_decision_nodes_live',[x['component'] for x in load('pipeline-trace.json')['steps'] if x['component'].startswith('DEC-')]==['DEC-001','DEC-002','DEC-003'],['DEC-001','DEC-002','DEC-003'])
    record('actual_provider_render_QA',load('model-call.json')['real_model_call'] and load('review-model-call.json')['real_model_call'] and len([a for a in load('render-report.json')['artifacts'] if a['type']=='png'])==8 and load('quality-report.json')['p0_issue_count']==0,load('result.json')['qa'])
    record('full_goal_not_shrunk',load('quality-report.json')['acceptance']['AC-001']=='not_passed','Three node contributions do not prove complete DEC/QA/AC scope.')
paths=[*sorted((ROOT/'src/yoloongppt').glob('*.py')), *[ROOT/'contracts'/n for n in ['decision-trace.schema.json','presentation-context.schema.json','source-role-map.schema.json','constraint-set.schema.json']],ROOT/'validation/context-cases.json',ROOT/'validation/context-project-map.json',ROOT/'validation/context-generation-task.json']
report={'passed':True,'requirement_ids':['DEC-002','DEC-003','GOV-003'],'cases':cases,'traces':traces,'scope':'Constraint normalization and source-role node integration; remaining nodes and full system AC not passed.','consumed_file_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
Path('/runtime/context-runtime.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'checks':len(cases),'live_run':sys.argv[1] if len(sys.argv)>1 else None}))
