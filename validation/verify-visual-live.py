"""One real HTTP job for the newly integrated visual pipeline; no mocked model."""
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from uuid import uuid4

OUT=Path('/runtime/visual-live-validation');OUT.mkdir(exist_ok=True)
def http(path,body=None):
    request=urllib.request.Request('http://127.0.0.1:8000'+path,data=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None,headers={'Content-Type':'application/json'})
    try:response=urllib.request.urlopen(request,timeout=30)
    except urllib.error.HTTPError as error:response=error
    return response.status,json.loads(response.read())

task=json.loads(Path('/runtime/runs/5be192ef-798f-4bb0-9c93-c24bcc279aa4/task.json').read_text('utf-8'))
task['task_id']='task_'+str(uuid4());task.pop('raw_request',None);task.pop('evidence_policy',None)
material=('明确虚构的学校照明演示测试资料；所有数据仅用于软件验证，不是现实节能效果。'
 '管理流程原文明示：检查照明→设置定时→记录变化。检查照明指核对灯具与使用时段。设置定时指设置关灯规则。记录变化指记录照明用电。'
 '测试数据单位为千瓦时，观察窗口为虚构测试周，统计对象为照明用电：A楼基线100，本期90；B楼基线80，本期72；C楼基线60，本期54。'
 '基线与本期都是明确虚构的记录值，只做并列展示，不推断控制实验或因果效果。'
 '素材是程序人工绘制的测试示意图，仅用于装饰，不证明任何事实。结论是先核对资料、保留来源，再按原文明示流程执行。')
task['sources']=[{'source_id':'source_'+str(uuid4()),'kind':'text','content':material,'metadata':{'source_role':'fact'}},
 {'source_id':'source_'+str(uuid4()),'kind':'prompt','content':'用明确虚构测试材料新建恰好6页中文演示：封面、真实素材图片页、原生流程图页、原生表格页、原生柱图页、结论页。流程必须采用资料原文明示的三个节点和箭头；图像仅作装饰。全部数值注明虚构测试。不要新增统计或因果。','metadata':{'source_role':'instruction'}},
 {'source_id':'source_'+str(uuid4()),'kind':'image','locator':'/runtime/visual-validation/declared-image.png',
  'metadata':{'source_role':'asset','asset_id':'asset_'+str(uuid4()),'usage_status':'authorized','license':'test-fixture-authorized','authorization_basis':'Artificial fixture authored for product integration verification'}}]
task['runtime_preferences']={'page_count':6};task['constraints']={'hard':[],'soft':[],'defaults':[],'conflicts':[]};task['template_ref']=None;task['style']=None
task['output']={'formats':['pptx','pdf','png']}
instruction=task['sources'].pop(1)['content']
task['sources'][0]['content']=task['sources'][0]['content'].replace('管理流程原文明示：检查照明→设置定时→记录变化。','')
task['sources'].insert(1,{'source_id':'source_'+str(uuid4()),'kind':'text','content':'原文唯一流程关系：检查照明→设置定时→记录变化。不得添加其他关系或因果；这是软件测试示例。','metadata':{'source_role':'fact'}})
task['raw_request']={'request':{'raw_text':instruction,'attachments':[],'requested_mode':'create_from_materials','requested_outputs':['pptx','pdf','png']},'attachment_roles':[]}
(OUT/'task.json').write_text(json.dumps(task,ensure_ascii=False,indent=2),'utf-8')
deadline=time.monotonic()+40
while True:
    try:
        if http('/health')[0]==200:break
    except urllib.error.URLError:pass
    if time.monotonic()>deadline:raise RuntimeError('app not ready')
    time.sleep(.3)
status,submitted=http('/jobs',{'operation':'generate','request':task});assert status==202,submitted
(OUT/'submitted.json').write_text(json.dumps(submitted,ensure_ascii=False,indent=2),'utf-8')
print('job submitted',submitted['job']['job_id'],flush=True)
deadline=time.monotonic()+600
while time.monotonic()<deadline:
    _,current=http('/jobs/'+submitted['job']['job_id'])
    if current['job']['state'] in {'succeeded','failed','interrupted','cancelled'}:break
    time.sleep(1)
else:raise RuntimeError('live generation deadline; worker remains inspectable')
(OUT/'live-result.json').write_text(json.dumps(current,ensure_ascii=False,indent=2),'utf-8')
print('terminal job state',current['job']['state'],flush=True)
if current['job']['state']!='succeeded':
    print(json.dumps(current.get('result'),ensure_ascii=False),flush=True);raise RuntimeError('actual visual generation failed; retained evidence')
result=current['result'];folder=Path(result['artifact_root']);deck=json.loads((folder/'deck-spec.json').read_text('utf-8'))
kinds=[s['content']['kind'] for s in deck['slides']];assert {'image','diagram','table','chart'}<=set(kinds),kinds
calls=json.loads((folder/'execution-trace.json').read_text('utf-8'))['calls']
assert {'add_image','add_shape','add_connector','add_table','add_chart'}<={c['capability'] for c in json.loads((folder/'execution-plan.json').read_text('utf-8'))['calls']}
print(json.dumps({'run_id':result['run_id'],'kinds':kinds,'qa':result['qa'],'completion':result['completion']['state']},ensure_ascii=False),flush=True)
