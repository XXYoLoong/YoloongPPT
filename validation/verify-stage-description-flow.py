"""Stage closure: one literal description through real API generation and local revision."""
import argparse,json,urllib.request,uuid
from pathlib import Path

ROOT=Path('/runtime/stage-closure');ROOT.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text('utf-8'))
save=lambda n,v:(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
parser=argparse.ArgumentParser();parser.add_argument('--reuse',action='store_true');parser.add_argument('--revise-only',action='store_true');args=parser.parse_args()
description=('制作中文PPT介绍一个虚构校园节能试点，偏好6页，允许在可读容量不足时按默认软预算分页，全部内容注明软件验证、非真实业务。'
 '介绍虚构试点，用原生表格列出数据，用原生柱状图展示同一组数据，再总结并保留来源。'
 '虚构数据：A楼基线100千瓦时、本期90千瓦时；B楼基线80千瓦时、本期72千瓦时；C楼基线60千瓦时、本期54千瓦时。'
 '不要推算比例、合计或新统计，不加入图片和原文没有的因果。')
task=load(Path('/workspace/validation/generation-task.json'));task['task_id']='task_'+str(uuid.uuid4())
task['sources']=[{'source_id':'source_'+str(uuid.uuid4()),'kind':'prompt','content':description,'metadata':{'source_role':'fact'}}]
task['constraints']={'hard':[],'soft':[],'defaults':[],'conflicts':[]};task['runtime_preferences']={'page_count':6}
task['raw_request']={'request':{'raw_text':description,'attachments':[],'requested_mode':'create_from_materials','requested_outputs':['pptx','pdf','png']},'attachment_roles':[]}
checks=[]
def test(name,condition,detail=None):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition:raise AssertionError(name)
def call(url,body):
    req=urllib.request.Request('http://127.0.0.1:8000'+url,data=json.dumps(body,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=900) as response:return json.load(response)
    except urllib.error.HTTPError as error:return json.load(error)
if args.reuse or args.revise_only:task=load(ROOT/'description-task.json');generated=load(ROOT/'description-result.json')
else:
    save('description-task.json',task);generated=call('/generate',task);save('description-result.json',generated)
try:
    test('description_only_input',len(task['sources'])==1 and task['sources'][0]['kind']=='prompt' and 'locator' not in task['sources'][0])
    test('real_api_generation',generated.get('ok'),generated)
    parent=Path('/runtime/runs')/generated['run_id'];deck=load(parent/'deck-spec.json');qa=load(parent/'quality-report.json')
    test('readable_pages_with_explicit_soft_budget',len(deck['slides'])>=1 and generated['slide_count']==len(deck['slides']))
    test('native_table_and_chart',{'table','chart'}<={e['type'] for s in deck['slides'] for e in s['elements']})
    test('fact_content_review_calls_real',all(load(parent/n)['real_model_call'] for n in ['fact-model-call.json','model-call.json','review-model-call.json']))
    test('render_and_original_trace',(parent/'deck.pptx').is_file() and len([a for a in load(parent/'render-report.json')['artifacts'] if a['type']=='png'])==len(deck['slides']) and (parent/'fact-boundary.json').is_file())
    test('generation_no_p0',qa['p0_issue_count']==0,qa['p0_issue_count'])
    title=next(e for e in deck['slides'][0]['elements'] if e['role']=='title')
    body=next(e for e in deck['slides'][0]['elements'] if e['role']=='body')
    request={'instruction':'仅修订首页标题为“虚构测试：校园节能试点”，首页正文只保留主题及软件验证、非真实业务标记，清除制作PPT与偏好页数等操作指令。其余页面、数据和对象保持。',
             'scope':{'object_ids':[title['object_id'],body['object_id']]},'edits':[
                 {'object_id':title['object_id'],'operation':'text','value':['虚构测试：校园节能试点']},
                 {'object_id':body['object_id'],'operation':'text','value':['虚构校园节能试点的数据展示。','软件验证，非真实业务。']}]}
    if args.reuse:revised=load(ROOT/'description-revision-result.json')
    else:
        save('description-revision-request.json',request);revised=call('/revise/'+generated['run_id'],request);save('description-revision-result.json',revised)
    test('real_api_local_revision',revised.get('ok'),revised)
    output=Path('/runtime/runs')/revised['run_id'];history=load(output/'revision-history.json');after=load(output/'deck-spec.json');q2=load(output/'quality-report.json')
    test('exact_selected_cover_objects',set(history['scope']['object_ids'])=={title['object_id'],body['object_id']})
    test('unmodified_pages_specs_preserved',deck['slides'][1:]==after['slides'][1:])
    test('selected_fact_snapshot_preserved',(parent/'approved-source-result.json').read_bytes()==(output/'approved-source-result.json').read_bytes())
    test('independent_new_review',load(output/'review-model-call.json')['real_model_call'] and q2['model_review']['fresh_checked_slide_orders']==[0])
    test('revision_no_p0',q2['p0_issue_count']==0,q2['p0_issue_count'])
    visible='\n'.join(t for e in after['slides'][0]['elements'] for t in e.get('text',[]))
    test('cover_task_instructions_removed_after_visual_inspection',not any(t in visible for t in ['制作中文PPT','制作中文 PPT','偏好','软预算']))
    test('full_acceptance_gate_preserved',generated['completion']['final_allowed'] is False and revised['completion']['final_allowed'] is False)
    report={'passed':True,'checks':checks,'description':description,'generated_run_id':generated['run_id'],'revised_run_id':revised['run_id'],
            'generation_quality':{'p0':qa['p0_issue_count'],'warnings':generated['completion']['warning_issue_count']},
            'revision_quality':{'p0':q2['p0_issue_count'],'warnings':revised['completion']['warning_issue_count']},
            'scope':'One bounded real description-to-PPTX/render/QA/revision flow. Full original baseline remains incomplete.'}
    save('description-flow-evidence.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['checks','description']},ensure_ascii=False))
finally:save('description-flow-checks.json',{'checks':checks,'generated':generated})
