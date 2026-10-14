"""Actual DOCX/PDF/XLSX product inputs; preserved source context, render and QA."""
import argparse,copy,hashlib,json,urllib.request,uuid
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--case',choices=['docx','pdf','xlsx'],required=True)
parser.add_argument('--result',help='Only check a saved result; no model or render call')
parser.add_argument('--prepare-only',action='store_true')
parser.add_argument('--output-root',default='/runtime/source-semantic-validation')
parser.add_argument('--input',help='Actual input file, never a surrogate source')
parser.add_argument('--pdf-pages',type=int,default=6)
args=parser.parse_args();ROOT=Path(args.output_root);ROOT.mkdir(parents=True,exist_ok=True)
if not ROOT.resolve().is_relative_to(Path('/runtime')):raise ValueError('Validation output must be F-backed /runtime')
load=lambda p:json.loads(p.read_text('utf-8'))
save=lambda name,value:(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')
checks=[]
def test(name,value,detail=None):
    checks.append({'name':name,'passed':bool(value),'detail':detail})
    if not value:raise AssertionError(name)

request=load(Path('/workspace/validation/generation-task.json'))
request['task_id']='task_'+str(uuid.uuid4());request['constraints']={'hard':[],'soft':[],'defaults':[],'conflicts':[]}
request['runtime_preferences']={'page_count':6};request['style']=None;request['template_ref']=None
docx_fixtures=sorted(Path('/runtime/source-semantic-docx').glob('component-*/report.docx'),key=lambda p:p.stat().st_mtime)
inputs={'docx':str(docx_fixtures[-1]) if docx_fixtures else '/workspace/validation/input-format-artifacts/school-source.docx',
        'pdf':'/runtime/runs/39a2dbf3-c19b-4da2-99a6-27fe7b82ef7a/render/deck.pdf',
        'xlsx':'/workspace/validation/source-semantic-artifacts/integration-input/artificial-data.xlsx'}
source_id='source_'+str(uuid.uuid4());path=Path(args.input or inputs[args.case]);source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
request['sources']=[{'source_id':source_id,'kind':args.case,'locator':str(path),'metadata':{'source_role':'fact'}}]
instruction={'docx':'根据所给人工验证DOCX报告新建中文演示，保留标题、表格数据、原有引用和来源；不要把外部链接下载或原生图片当作业务事实。表格与图表依原内容合理选择。',
 'pdf':'根据已提供的六页虚构软件验证PDF新建中文摘要演示，保留所有原数字、单位、限定与明确流程关系；每个事实保留来源页码。表格行列如不确定须显式报告，不猜测图片内事实或新因果。',
 'xlsx':'根据两sheet人工验证数据新建中文演示，完整展示三个月日期、用电量、降低比例、三个月合计和三楼分类数据，全部注明人工验证非真实业务；选择原生表格和图表，不同单位不得混在同一数值轴。读取已保存公式缓存并标明未证明新鲜；不重新计算，不增加新统计或因果。'}[args.case]
request['raw_request']={'request':{'raw_text':instruction,'attachments':[],
                       'requested_mode':'create_from_materials','requested_outputs':['pptx','pdf','png']},
                       'attachment_roles':[]}
# Use the actual input source as material; no Markdown surrogate is added.
save(args.case+'-task.json',request)
if args.prepare_only:print(json.dumps({'prepared':args.case,'source_sha256':source_hash}));raise SystemExit()
if args.result:
    result=load(Path(args.result));saved=load(ROOT/(args.case+'-task-original.json'));source_id=saved['sources'][0]['source_id'];request=saved
else:
    save(args.case+'-task-original.json',request)
    req=urllib.request.Request('http://127.0.0.1:8000/generate',data=json.dumps(request,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=900) as response:result=json.load(response)
    except urllib.error.HTTPError as error:result=json.load(error)
    save(args.case+'-result.json',result)
try:
    test('api_success',result.get('ok'),result)
    run=Path('/runtime/runs')/result['run_id'];sources=load(run/'source-result.json');deck=load(run/'deck-spec.json');quality=load(run/'quality-report.json')
    original=[e for e in sources['evidence'] if e['source_id']==source_id]
    test('input_original_hash_preserved',bool(original) and all(e['source_hash']==source_hash for e in original))
    test('native_format_evidence_consumed',any(e.get('metadata',{}).get('source_context',{}).get('source_kind')==args.case for e in original))
    model=load(run/'fact-model-request.json')
    payload=(json.loads(model['messages'][1]['content'])['evidence'] if 'messages' in model else
             [e for name in model['batch_requests'] for e in json.loads(load(run/name)['messages'][1]['content'])['evidence']])
    test('real_fact_model_consumes_context',load(run/'fact-model-call.json')['real_model_call'] and any(e.get('source_context') for e in payload))
    test('real_content_and_review_models',load(run/'model-call.json')['real_model_call'] and load(run/'review-model-call.json')['real_model_call'])
    test('editable_pptx_and_actual_render',(run/'deck.pptx').is_file() and len([a for a in load(run/'render-report.json')['artifacts'] if a['type']=='png'])==len(deck['slides']))
    test('selected_fact_boundary_saved',all((run/name).is_file() for name in ['approved-source-result.json','fact-boundary.json','fact-interpretation.json','evidence-resolution.json']))
    test('system_acceptance_not_promoted',result['completion']['final_allowed'] is False)
    test('no_p0_in_executed_checks',quality['p0_issue_count']==0,quality['p0_issue_count'])
    if args.case=='xlsx':
        texts=[e['raw_text'] for e in original]
        test('display_dates_percent_and_literal_units',all(t in texts for t in ['2026-01-01','2026-02-01','2026-03-01','8%','9%','10%','1200 千瓦时','1300 千瓦时','1250 千瓦时','3750 千瓦时']))
        test('cell_and_sheet_anchors_preserved',all(e['anchor']['locator']['kind']=='tabular_cell' for e in original))
        test('table_or_chart_native_decision',any(e['type'] in {'chart','table'} for s in deck['slides'] for e in s['elements']))
    elif args.case=='pdf':
        test('source_page_numbers_preserved',all(e['anchor']['locator']['page_number']>=1 for e in original))
        test('multiple_source_pages',{e['anchor']['locator']['page_number'] for e in original}==set(range(1,args.pdf_pages+1)))
    else:
        test('docx_native_anchors_preserved',all(e['anchor']['locator']['kind']=='docx_block' or
             e['anchor']['locator']['kind']=='structured_node' and e.get('metadata',{}).get('source_context',{}).get('source_field')=='bibliography' for e in original))
    save(args.case+'-evidence.json',{'case':args.case,'run_id':result['run_id'],'source_sha256':source_hash,'checks':checks,
         'p0':quality['p0_issue_count'],'warnings':result['completion']['warning_issue_count'],'completion':result['completion'],
         'scope':'Actual product input/model/render/QA; bounded parser semantics and full original acceptance still separately assessed.'})
    print(json.dumps({'case':args.case,'run_id':result['run_id'],'checks':len(checks),'p0':quality['p0_issue_count'],'warnings':result['completion']['warning_issue_count']},ensure_ascii=False))
finally:save(args.case+'-checks.json',{'case':args.case,'result':result,'checks':checks})
