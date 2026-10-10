"""Changed surface verification; one real generation via durable HTTP job."""
import copy
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from uuid import uuid4

from yoloongppt.jobs import JobManager
from yoloongppt.errors import trace_id

ROOT=Path('/workspace');OUT=Path('/runtime/parallel-validation');OUT.mkdir(exist_ok=True)
checks=[]


def record(name,condition,value=None):
    assert condition,name
    checks.append({'name':name,'passed':True,'observation':value})
    (OUT/'checks-partial.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),'utf-8')


def http(path,body=None):
    req=urllib.request.Request('http://127.0.0.1:8000'+path,data=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None,headers={'Content-Type':'application/json'})
    try: response=urllib.request.urlopen(req,timeout=30)
    except urllib.error.HTTPError as error: response=error
    return response.status,json.loads(response.read())


def wait_job(job_id,timeout=360):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        _,result=http('/jobs/'+job_id)
        if result['job']['state'] in {'succeeded','failed','interrupted','cancelled'}:return result
        time.sleep(.4)
    raise AssertionError('job deadline')


task=json.loads((Path('/runtime/runs/6ed1b3c5-a6c0-47cb-888c-fc841ab610c5')/'task.json').read_text('utf-8'))
task['task_id']='task_'+str(uuid4());task.pop('evidence_policy',None)
task.pop('raw_request',None)
task['sources']=[{'source_id':'source_'+str(uuid4()),'kind':'text','content':
 '以下为明确虚构的学校节能演示测试材料。试点先检查教室照明，再设置定时关灯，随后记录变化。目标是让管理层理解执行方法。团队先培训值班人员，再每周回看记录。发现异常时先核实记录，再调整设备。试点只讨论照明管理，不对全校节能作出承诺。'},
 {'source_id':'source_'+str(uuid4()),'kind':'docx','locator':'/runtime/input-format-validation/school-source.docx'}]
task['constraints']={'hard':[],'soft':[],'defaults':[],'conflicts':[]}
for key,value in [('page_count',8),('audience','学校管理层'),('scenario','项目汇报'),('tone','清晰克制')]:
    task['constraints']['soft'].append({'constraint_id':'parallel-'+key,'field':key,'value':value,'source':{'kind':'user_instruction','reference':'parallel integration fixture'},'disposition':'applied'})
task['runtime_preferences']={}
deadline=time.monotonic()+40
while True:
    try:
        ready=http('/health')[0]==200
        break
    except urllib.error.URLError:
        if time.monotonic()>deadline:raise
        time.sleep(.3)
if '--reuse-prefix' in sys.argv:
    checks=json.loads((OUT/'checks-partial.json').read_text('utf-8'))[:15]
else:
    record('http_ready',ready)
    code,result=http('/jobs',{'operation':'validate','request':task})
    record('job_submit_202',code==202)
    validated=wait_job(result['job']['job_id'],30)
    record('isolated_worker_actual_validate',validated['job']['state']=='succeeded',validated['job'])
    queue=JobManager('/runtime/parallel-validation/queue-boundary')
    cancel=queue.submit('validate',task,trace_id());cancelled=queue.cancel(cancel['job']['job_id'],trace_id())
    record('queued_cancel',cancelled['job']['state']=='cancelled')
    retry=queue.retry(cancel['job']['job_id'],trace_id())
    record('explicit_retry_new_identity',retry['retry_of']==cancel['job']['job_id'] and retry['job']['job_id']!=cancel['job']['job_id'])
    messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'verification','version':'1'}}},
              {'jsonrpc':'2.0','method':'notifications/initialized'},
              {'jsonrpc':'2.0','id':2,'method':'tools/list'},
              {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'inspect','arguments':task}},
              {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'validate','arguments':{}}}]
    proc=subprocess.run([sys.executable,'-m','yoloongppt','mcp-serve'],input=''.join(json.dumps(m,ensure_ascii=False)+'\n' for m in messages),capture_output=True,text=True,timeout=30)
    responses=[json.loads(x) for x in proc.stdout.splitlines()]
    record('mcp_stdio_initialized',proc.returncode==0 and len(responses)==4 and responses[0]['result']['protocolVersion']=='2025-06-18')
    record('mcp_required_tools',{'create_deck','revise_deck','inspect','validate','capabilities','debug'} <= {t['name'] for t in responses[1]['result']['tools']})
    record('mcp_actual_evidence_not_mock',responses[2]['result']['structuredContent']['evidence'][0]['raw_text']==task['sources'][0]['content'])
    record('mcp_structured_failure',responses[3]['result']['isError'] and not responses[3]['result']['structuredContent']['ok'])
    native={'slides':[{'objects':[{'kind':'text','bounds':[1,1,10,1],'text':'可编辑原生对象','name':'标题'},
                                {'kind':'shape','bounds':[1,3,2,1],'shape_type':'rounded_rectangle','text':'原生形状'},
                                {'kind':'connector','bounds':[3,3.5,2,.1],'connector_type':'straight'}]}]}
    code,native_result=http('/compose-native',native)
    record('native_api_real_pptx',code==200 and Path(native_result['pptx']).is_file(),native_result.get('run_id'))
    code,model=http('/inspect-deck',{'path':native_result['pptx']})
    record('existing_deck_api_index',code==200 and len(model['result']['slides'][0]['objects'])==3)
    original=Path(native_result['pptx']);digest=hashlib.sha256(original.read_bytes()).hexdigest()
    patch={'expected_sha256':model['result']['source_sha256'],'patches':[{'selector':{'name':'标题'},'operation':'text','value':'指定对象已修订'}]}
    code,modified=http('/edit-deck',{'path':str(original),'request':patch})
    record('existing_deck_api_preserve',code==200 and hashlib.sha256(original.read_bytes()).hexdigest()==digest and len(modified['result']['changed_parts'])==1)
    code,template=http('/parse-template',{'path':str(original)})
    record('template_api_master_layout_theme',code==200 and bool(template['result']['masters']) and bool(template['result']['themes']))
    chosen=next(l for l in template['result']['layouts'] if any(s['role']=='title' for s in l['slots']))
    slot=next(s for s in chosen['slots'] if s['role']=='title')
    code,inst=http('/instantiate-template',{'path':str(original),'layout_part':chosen['part'],'slot_content':{str(slot['placeholder_index']):'真实模板填充'}})
    record('template_api_actual_instantiation',code==200 and Path(inst['result']['pptx']).is_file())
if '--resume-facts' in sys.argv:
    old=json.loads((OUT/'live-result.json').read_text('utf-8'))
    run_id=next(x['run_id'] for x in old['result']['error']['details'] if 'run_id' in x)
    missing=[x for x in old['result']['error']['details'] if x.get('code')=='MISSING_FACT']
    interpretation=json.loads((Path('/runtime/runs')/run_id/'fact-interpretation.json').read_text('utf-8'))
    rules=[{'fact_key':x['fact_key'],'fact_kind':next(m['fact_kind'] for m in interpretation['missing'] if m['fact_key']==x['fact_key']),
            'mode':'placeholder','reason':'Integration fixture explicitly retains missing baseline/metric as visible placeholders, no invented value.',
            'label':'【待补充：'+x['fact_key']+'】'} for x in missing]
    code,result=http('/jobs',{'operation':'resume','request':{'run_id':run_id,'task_patch':{'evidence_policy':{'missing_rules':rules}}}})
    record('explicit_missing_policy_resume',code==202)
else:
    code,result=http('/create',task)
    record('create_async_202',code==202)
(OUT/'live-job.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'stage':'real_generation_submitted','job_id':result['job']['job_id'],'bounded_checks':len(checks)}),flush=True)
finished=wait_job(result['job']['job_id'],540)
(OUT/'live-result.json').write_text(json.dumps(finished,ensure_ascii=False,indent=2),'utf-8')
record('actual_ai_job_succeeded',finished['job']['state']=='succeeded',finished)
run=finished['result'];folder=Path(run['artifact_root'])
packet=json.loads((folder/'model-request.json').read_text('utf-8'))
user=json.loads(packet['messages'][1]['content'])
record('narrative_consumed_by_real_model',user['narrative']['audience'] is not None and user['narrative']['scenario']['scenario']=='项目汇报')
narrative=json.loads((folder/'narrative-result.json').read_text('utf-8'))
record('sixteen_nodes_consumed',len(narrative['decision_traces'])==16 and len(narrative['content_budgets'])==8)
record('actual_eight_native_slides',run['slide_count']==8 and Path(run['pptx']).is_file())
render=json.loads((folder/'render-report.json').read_text('utf-8'))
record('actual_lo_render',len(list((folder/'render').glob('*.png')))==8,render)
code,manifest=http('/artifacts/'+run['run_id'])
record('api_manifest_verified',code==200 and any(x['path']=='version-manifest.json' for x in manifest['artifacts']))
report={'passed':True,'checks':checks,'run_id':run['run_id'],'job_id':finished['job']['job_id'],
        'qa':run['qa'],'scope':'bounded parallel integration; full original requirements and AC not accepted',
        'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/yoloongppt').glob('*.py'))}}
(OUT/'parallel-integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'passed':True,'checks':len(checks),'run_id':run['run_id'],'qa':run['qa']}),flush=True)
