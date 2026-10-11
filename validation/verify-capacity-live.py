"""Fresh real API/model run for gallery and adaptive title/table consumption.

All materials are explicitly artificial validation fixtures. This script checks
the new path, not completion of the original system acceptance matrix.
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

parser=argparse.ArgumentParser();parser.add_argument('--fixture');parser.add_argument('--resume-run');args=parser.parse_args()
OUT=Path('/runtime/capacity-live-validation')/str(uuid4())
OUT.mkdir(parents=True)

def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def http(path,body=None):
    request=urllib.request.Request('http://127.0.0.1:8000'+path,
        data=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None,
        headers={'Content-Type':'application/json'})
    try: response=urllib.request.urlopen(request,timeout=30)
    except urllib.error.HTTPError as error: response=error
    return response.status,json.loads(response.read())

deadline=time.monotonic()+40
while True:
    try:
        if http('/health')[0]==200:break
    except (urllib.error.URLError,TimeoutError):pass
    if time.monotonic()>deadline:raise RuntimeError('App readiness deadline; no job submitted')
    time.sleep(.3)

if args.fixture:
    fixture=Path(args.fixture)
    task=json.loads((fixture/'task.json').read_text('utf-8'));task['task_id']='task_'+str(uuid4())
    expected=json.loads((fixture/'expected.json').read_text('utf-8'))
    title,columns,rows,asset_ids,captions=(expected[k] for k in ['title','columns','rows','asset_ids','captions'])
    save('task.json',task);save('expected.json',expected);save('fixture-reference.json',{'reused_artificial_inputs':str(fixture),'fresh_model_required':True})
else:
    task=json.loads(Path('/runtime/runs/5be192ef-798f-4bb0-9c93-c24bcc279aa4/task.json').read_text('utf-8'))
    task['task_id']='task_'+str(uuid4())
    task.pop('raw_request',None);task.pop('evidence_policy',None)
    title='人工验证资料完整展示：中文与English混合长标题必须逐字保留并采用可读字号自动调整页面布局，所有内容仅用于软件验证而不代表真实业务结论'
    columns=['标识','甲项','乙项','丙项']
    rows=[[f'样本{n:02d}',str(n),str(n+20),str(n+40)] for n in range(1,15)]
    captions=[f'人工绘制示意图{n}' for n in range(1,9)]
    material=('这些均为人工构造的软件验证资料，不代表现实业务。\n指定完整标题：'+title+
        '\n图注明示：'+'；'.join(captions)+'。\n表格单位：测试分。全部原始列名及14行如下：\n'+
        '\t'.join(columns)+'\n'+'\n'.join('\t'.join(r) for r in rows)+
        '\n正文：先保存原始数据与来源，再检查页面容量。图片仅作软件验证装饰，不证明统计、关系或因果。')
    task['sources']=[{'source_id':'source_'+str(uuid4()),'kind':'text','content':material,'metadata':{'source_role':'fact'}}]
    asset_ids=[]
    for n,(w,h) in enumerate([(1000,1000),(1200,600),(600,1200),(1600,400),(800,1000),(1000,800),(1400,700),(700,1400)],1):
        path=OUT/f'fixture-image-{n}.png'
        image=Image.new('RGB',(w,h),(30+n*18,70+n*12,110+n*9))
        draw=ImageDraw.Draw(image);draw.rectangle((w*.1,h*.1,w*.9,h*.9),outline='white',width=8)
        draw.text((w*.15,h*.2),f'ARTIFICIAL FIXTURE {n}',fill='white');image.save(path)
        asset='asset_'+str(uuid4());asset_ids.append(asset)
        task['sources'].append({'source_id':'source_'+str(uuid4()),'kind':'image','locator':str(path),
            'metadata':{'source_role':'asset','asset_id':asset,'usage_status':'authorized',
                'license':'test-fixture-authorized','authorization_basis':'Artificial fixture authored for product integration verification'}})
    instruction=('按初始预算3页新建演示，允许容量需要时续页，所有数值明确为人工软件验证。'
        '第1页是多图页，必须用images数组保留8个提供的asset_id，fit=contain，逐字图注按图序使用原文明示文字，正文只写“图片仅作软件验证装饰”。'
        '第2页是纯文字页，完整标题逐字使用“'+title+'”，正文保留原文两句。'
        '第3页是原生表格页，必须逐字保留原文4个列名和全部14行，不汇总、不省略、不替换为图片，单位为测试分。'
        '不新增封面/目录，不发明事实，不把测试图像说成真实证据。')
    task.update(runtime_preferences={'page_count':3},constraints={'hard':[],'soft':[],'defaults':[],'conflicts':[]},template_ref=None,style=None,
        output={'formats':['pptx','pdf','png']},raw_request={'request':{'raw_text':instruction,'attachments':[],
            'requested_mode':'create_from_materials','requested_outputs':['pptx','pdf','png']},'attachment_roles':[]})
    save('task.json',task);save('expected.json',{'title':title,'columns':columns,'rows':rows,'asset_ids':asset_ids,'captions':captions})
status,submitted=http('/jobs',{'operation':'resume','request':{'run_id':args.resume_run}} if args.resume_run else {'operation':'generate','request':task})
save('submitted.json',submitted);assert status==202,submitted
print('fresh job submitted '+submitted['job']['job_id'],flush=True)
deadline=time.monotonic()+900
while time.monotonic()<deadline:
    _,current=http('/jobs/'+submitted['job']['job_id'])
    if current['job']['state'] in {'succeeded','failed','interrupted','cancelled'}:break
    time.sleep(1)
else:raise RuntimeError('Fresh generation deadline; actual job remains inspectable')
save('live-result.json',current)
assert current['job']['state']=='succeeded',current.get('result')
result=current['result'];folder=Path(result['artifact_root'])
deck=json.loads((folder/'deck-spec.json').read_text('utf-8'))
adapt=json.loads((folder/'adaptive-content-result.json').read_text('utf-8'))
checks=[]
def check(name,condition,observed):
    checks.append({'name':name,'passed':bool(condition),'observed':observed});save('checks.json',checks)
    assert condition,(name,observed)
gallery=[s for s in deck['slides'] if s['content'].get('images')]
check('all-eight-native-images',len(gallery)==1 and Counter(e['data']['asset_id'] for e in gallery[0]['elements'] if e['type']=='image')==Counter(asset_ids),[s['slide_id'] for s in gallery])
check('literal-long-title',any(s['content']['title']==title for s in deck['slides']),[s['content']['title'] for s in deck['slides']])
actual_rows=[row for s in deck['slides'] if s['content']['kind']=='table' for row in s['content']['table']['rows']]
check('all-fourteen-table-rows',Counter(tuple(row) for row in actual_rows)==Counter(tuple(row) for row in rows),len(actual_rows))
check('capacity-continuation',adapt['output_pages']>adapt['input_pages'],{'input':adapt['input_pages'],'output':adapt['output_pages']})
call=json.loads((folder/'model-call.json').read_text('utf-8'))
check('actual-model-provenance',call.get('real_model_call') is True and call.get('fresh_model_call_this_run',True)==(not bool(args.resume_run)),call)
if args.resume_run:
    prior=Path('/runtime/runs')/args.resume_run
    check('exact-model-seed-reused',(folder/'model-response.json').read_bytes()==(prior/'model-response.json').read_bytes(),args.resume_run)
    check('new-review-executed',json.loads((folder/'review-model-call.json').read_text('utf-8')).get('real_model_call') is True and not (folder/'review-reuse.json').exists(),result['run_id'])
check('actual-render',len(list((folder/'render').glob('*.png')))==len(deck['slides']),len(deck['slides']))
check('qa-no-p0',result['qa']['p0_issue_count']==0,result['qa'])
save('summary.json',{'run_id':result['run_id'],'output_pages':len(deck['slides']),'checks':checks,'model_seed_reused_from':args.resume_run,'new_review':True,'system_acceptance':'not_claimed'})
print(json.dumps({'run_id':result['run_id'],'output_pages':len(deck['slides']),'checks':len(checks),'completion':result['completion']['state']},ensure_ascii=False),flush=True)
