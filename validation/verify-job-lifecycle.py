"""Bounded checks for changed job/MCP code; never invokes an AI provider."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4
from yoloongppt.jobs import JobManager
from yoloongppt.errors import TaskError,trace_id
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.sources import inspect_sources
from yoloongppt.source_roles import assign,fact_input
from yoloongppt.evidence import EvidenceStore

out=Path('/runtime/parallel-validation');checks=[]
def check(name,value,observed=None):
    assert value,name
    checks.append({'name':name,'passed':True,'observation':observed})
def wait(manager,job_id,endstate,timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=manager.status(job_id,trace_id())
        if value['job']['state'] in endstate:return value
        time.sleep(.05)
    raise AssertionError('job deadline')
task=json.loads(Path('/runtime/runs/5be192ef-798f-4bb0-9c93-c24bcc279aa4/task.json').read_text('utf-8'))
manager=JobManager('/runtime/jobs/verification-'+str(uuid4()))
first=manager.submit('validate',task,trace_id());ident=first['job']['job_id']
with manager.connect() as conn:conn.execute("UPDATE jobs SET state='running',pid=12345 WHERE job_id=?",(ident,))
manager.start()
check('restart_marks_interrupted_not_replayed',manager.status(ident,trace_id())['job']['state']=='interrupted')
retry=manager.retry(ident,trace_id());result=wait(manager,retry['job']['job_id'],{'succeeded','failed'})
check('explicit_retry_executes_new_worker',result['job']['state']=='succeeded')
broken=manager.submit('resume',{'run_id':'00000000-0000-4000-8000-000000000000'},trace_id())
result=wait(manager,broken['job']['job_id'],{'failed','succeeded'})
check('worker_failure_structured',result['job']['state']=='failed' and result['result']['error']['code']=='CHECKPOINT_INCOMPLETE')
long=copy.deepcopy(task)
long['sources']=[{'source_id':'source_'+str(uuid4()),'kind':'docx','locator':'AI_PPT_PDR_完整需求定义_V0.3.docx'} for _ in range(50)]
queued=manager.submit('inspect',long,trace_id());job_id=queued['job']['job_id']
deadline=time.monotonic()+15;pid=None
while time.monotonic()<deadline:
    with manager.lock:
        if job_id in manager.active:pid=manager.active[job_id].pid;break
    time.sleep(.01)
check('actual_worker_has_own_process_group',pid is not None and os.getpgid(pid)==pid)
manager.cancel(job_id,trace_id());cancelled=wait(manager,job_id,{'cancelled','succeeded','failed'})
check('running_cancel_stops_actual_process',cancelled['job']['state']=='cancelled')
try:os.kill(pid,0);alive=True
except ProcessLookupError:alive=False
check('cancelled_worker_pid_absent',not alive)
manager.close()
events=[json.loads(line) for line in (manager.root/'events.jsonl').read_text('utf-8').splitlines()]
check('structured_job_events',all({'time','level','component','job_id','event','duration','result'}<=set(e) for e in events))
schema=SchemaRegistry()
try:schema.validate('job-request.schema.json',{'operation':'resume','request':{'run_id':'x','secret':'forbidden'}});invalid=False
except TaskError:invalid=True
check('job_envelope_rejects_unknown_fields',invalid)
source=inspect_sources(task,schema,EvidenceStore(),trace_id())
roles=assign({'task':task,'source_bundle':source['source_bundle']},schema,trace_id())
selected=fact_input(source,roles['source_role_map'])
check('binary_source_real_evidence',any(e['metadata'].get('semantic_claim_status')=='not_inferred' for e in source['evidence']))
check('empty_structure_preserved_outside_text_facts',bool(selected['nontext_evidence']) and all(e['raw_text'] for e in selected['evidence']))
messages=[{'jsonrpc':'2.0','id':1,'method':'tools/list'},
          {'jsonrpc':'2.0','id':2,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},
          {'jsonrpc':'2.0','method':'notifications/initialized'},
          {'jsonrpc':'2.0','id':3,'method':'tools/list'},
          {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'inspect','arguments':task}}]
proc=subprocess.run([sys.executable,'-m','yoloongppt','mcp-serve'],input=''.join(json.dumps(m,ensure_ascii=False)+'\n' for m in messages),capture_output=True,text=True,timeout=30)
responses=[json.loads(line) for line in proc.stdout.splitlines()]
check('mcp_enforces_initialization',responses[0]['error']['code']==-32002)
check('mcp_after_initialize_lists_tools',len(responses[2]['result']['tools'])>=12)
check('mcp_binary_inspect_actual_contract',responses[3]['result']['structuredContent']['ok'] and bool(responses[3]['result']['structuredContent']['documents']))
report={'passed':True,'checks':checks,'fresh_model_calls':0,'scope':'changed lifecycle/MCP/SourceLoader surfaces only; not full AC acceptance',
        'source_hashes':{str(p.relative_to('/workspace')):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('/workspace/src/yoloongppt/jobs.py'),Path('/workspace/src/yoloongppt/mcp_server.py'),Path('/workspace/src/yoloongppt/sources.py'),Path('/workspace/src/yoloongppt/source_roles.py')]}}
(out/'job-lifecycle.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'passed':True,'checks':len(checks),'fresh_model_calls':0}),flush=True)
