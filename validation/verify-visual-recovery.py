"""Actual QA-only recovery of the saved six-page AI run; no new model call."""
import copy
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

from yoloongppt.errors import TaskError,trace_id
from yoloongppt.review import validate_review

OUT=Path('/runtime/visual-live-validation');OUT.mkdir(exist_ok=True)
PARENT=Path('/runtime/runs/74a0567c-2bfb-47e1-a6b0-eae2dcf252e6');checks=[]
def record(name,passed,observed=None):
    assert passed,(name,observed)
    checks.append({'name':name,'passed':True,'observed':observed})
    (OUT/'recovery-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),'utf-8')
def http(path,body=None):
    req=urllib.request.Request('http://127.0.0.1:8000'+path,data=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None,headers={'Content-Type':'application/json'})
    try:response=urllib.request.urlopen(req,timeout=30)
    except urllib.error.HTTPError as e:response=e
    return response.status,json.loads(response.read())
deadline=time.monotonic()+40
while True:
    try:
        if http('/health')[0]==200:break
    except urllib.error.URLError:pass
    if time.monotonic()>deadline:raise RuntimeError('app not ready')
    time.sleep(.3)
if '--resume-checks' in sys.argv:
    current=json.loads((OUT/'recovery-result.json').read_text('utf-8'))
    record('saved_review_recovery_job',current['job']['operation']=='recheck',current['job']['job_id'])
else:
    code,submitted=http('/jobs',{'operation':'recheck','request':{'run_id':PARENT.name,'reuse_saved_review':True}})
    record('saved_review_recovery_job',code==202,submitted['job']['job_id'])
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        _,current=http('/jobs/'+submitted['job']['job_id'])
        if current['job']['state'] in {'succeeded','failed','interrupted','cancelled'}:break
        time.sleep(.5)
(OUT/'recovery-result.json').write_text(json.dumps(current,ensure_ascii=False,indent=2),'utf-8')
record('real_recovery_succeeded',current['job']['state']=='succeeded',current)
result=current['result'];root=Path(result['artifact_root']);load=lambda n:json.loads((root/n).read_text('utf-8'))
deck=load('deck-spec.json');kinds=[s['content']['kind'] for s in deck['slides']]
record('six_page_actual_AI_visual_kinds',len(kinds)==6 and {'image','diagram','chart','table'}<=set(kinds),kinds)
record('PPTX_bytes_reused',(root/'deck.pptx').read_bytes()==(PARENT/'deck.pptx').read_bytes())
renders=load('render-report.json');record('all_PNG_PDF_bytes_reused',all((root/i['path']).read_bytes()==(PARENT/i['path']).read_bytes() for i in renders['artifacts']))
record('no_new_model_call',result['fresh_model_call'] is False and load('review-reuse.json')['fresh_model_call'] is False)
record('review_response_structured_content_retained',load('review-response.json')==json.loads((PARENT/'review-response.json').read_text('utf-8')))
quality=load('quality-report.json');record('actual_P0_zero',quality['p0_issue_count']==0,quality['p0_issue_count'])
record('actual_model_issues_preserved',len(quality['model_review']['issues'])==3 and {i['severity'] for i in quality['model_review']['issues']}=={'P1','P2'})
record('all_38_prior_nodes_reached',load('completion-decision.json')['missing_nodes']==[],load('completion-decision.json')['missing_nodes'])
record('no_false_system_acceptance',result['completion']['state']=='warning' and result['system_acceptance']=='not_passed')
# Saved optional note is metadata; wrong types/coverage/unknown fields still fail.
sources=load('approved-source-result.json');raw=load('review-response.json')
for name,changed in [('wrong_note_type',{'issues_note':{'pretend':'pass'}}),('extra_field',{'pretend_final':True}),('missing_page',{'checked_slide_orders':[0]})]:
    candidate={**copy.deepcopy(raw),**changed}
    try:validate_review(candidate,deck,sources,list(range(6)))
    except TaskError as e:record(name+'_rejected',e.code=='QA_REVIEW_INCOMPLETE')
    else:raise AssertionError(name)
# HTTP/CLI/MCP registry consumers share the actual implementation.
template='/runtime/visual-validation/wide-template.pptx'
code,registered=http('/register-template',{'path':template})
record('HTTP_template_register',code==200 and Path(registered['template']['path']).is_file(),registered)
code,conflict=http('/register-template',{'path':template,'license':'fixture-authorized'})
record('changed_template_provenance_rejected',code==422 and conflict['error']['code']=='ASSET_CACHE_CHANGED')
tid=registered['template']['template_id'];code,fetched=http('/get-template',{'template_id':tid})
record('HTTP_template_hash_query',code==200 and fetched['template']['sha256']==registered['template']['sha256'])
proc=subprocess.run([sys.executable,'-m','yoloongppt','get-template','-'],input=json.dumps({'template_id':tid}),text=True,capture_output=True,timeout=20)
record('CLI_template_query',proc.returncode==0 and json.loads(proc.stdout)['template']['template_id']==tid)
messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'visual-verification','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},
 {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'get_template','arguments':{'template_id':tid}}}]
proc=subprocess.run([sys.executable,'-m','yoloongppt','mcp-serve'],input=''.join(json.dumps(m)+'\n' for m in messages),text=True,capture_output=True,timeout=20)
response=json.loads(proc.stdout.splitlines()[-1]);record('MCP_template_query',proc.returncode==0 and response['result']['structuredContent']['template']['template_id']==tid)
print(json.dumps({'checks':len(checks),'run_id':result['run_id'],'kinds':kinds,'qa':result['qa'],'completion':result['completion']['state']},ensure_ascii=False),flush=True)
