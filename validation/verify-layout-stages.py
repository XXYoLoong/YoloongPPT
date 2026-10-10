"""Direct native layout-stage checks; synthetic geometric fixtures, no model calls."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image
from yoloongppt.artifacts import entity
from yoloongppt.atomic import AtomicRegistry
from yoloongppt.errors import TaskError
from yoloongppt.layout_decisions import run_stage, image_fit
from yoloongppt.layouts import choose, candidate
from yoloongppt.planning import DEFAULT_STYLE
from yoloongppt.schemas import SchemaRegistry, ROOT

out=Path('/runtime/layout-stage-validation');out.mkdir(parents=True,exist_ok=True)
schemas=SchemaRegistry();registry=AtomicRegistry(schemas);checks=[];traces=[]
refs=[entity('evidence')]
base={'title':'明确来源的页面','body':['保留原始文字','检查完整对象'], 'notes':'原始备注必须保持。','evidence_refs':refs,'kind':'text'}
samples=[copy.deepcopy(base) for _ in range(3)]
samples[1].update(kind='table',table={'columns':['项目','说明'],'rows':[['来源','原文'],['状态','保留']]})
samples[2].update(kind='chart',chart={'type':'column','categories':['甲','乙'],'series':[{'name':'样例值','values':[2,3]}],'units':'个'})
for i,content in enumerate(samples):
    elements,style,trace=choose(content,1,3,DEFAULT_STYLE,registry=registry)
    assert len(trace['decisions'])==9 and trace['enhancements']['notes']==content['notes']
    assert trace['decisions'][-1]['result']['preflight']=='passed'
    assert [e['slot_key'] for e in elements][0]=='title' and elements[-1]['slot_key']=='footer'
    traces.append(trace)
    for decision in trace['decisions']:
        schemas.validate('layout-stage-node.schema.json',decision)
        checks.append({'name':f"{decision['node_id']}_normal_{i+1}",'passed':True})
Image.new('RGB',(1200,800),'#243B53').save(out/'image.png')
image={**copy.deepcopy(base),'kind':'image','image':{'asset_id':entity('asset'),'role':'reference','alt_text':'本地验证色块，不包含事实含义','required':True,'path':str(out/'image.png'),'width_px':1200,'height_px':800,'fit':'contain','source_refs':refs,'sha256':hashlib.sha256((out/'image.png').read_bytes()).hexdigest()}}
elements,style,trace=choose(image,0,1,DEFAULT_STYLE,registry=registry)
pic=next(e for e in elements if e['type']=='image')
assert pic['data']['crop']==[0,0,0,0] and abs(pic['bounds'][2]/pic['bounds'][3]-1.5)<1e-9
assert trace['decisions'][-1]['result']['preflight']=='passed'
assert 'crop' not in image['image'] and 'fit_result' not in image['image']
checks.append({'name':'actual_png_probe_contain_no_pixel_removal','passed':True});traces.append(trace)
diagram={**copy.deepcopy(base),'kind':'diagram','diagram':{'type':'process','direction':'horizontal',
    'nodes':[{'node_id':'a','label':'原始输入','evidence_refs':refs},{'node_id':'b','label':'解析来源','evidence_refs':refs},{'node_id':'c','label':'原生输出','evidence_refs':refs}],
    'edges':[{'from':'a','to':'b','relation':'sequence','evidence_refs':refs},{'from':'b','to':'c','relation':'sequence','evidence_refs':refs}]}}
elements,style,trace=choose(diagram,0,1,DEFAULT_STYLE,registry=registry)
assert len([e for e in elements if e['type']=='shape'])==3 and len([e for e in elements if e['type']=='connector'])==2
assert [e['data']['text'] for e in elements if e['type']=='shape']==['原始输入','解析来源','原生输出']
checks.append({'name':'explicit_diagram_nodes_edges_native_slots','passed':True});traces.append(trace)
for mode in ('contain','cover','crop'):
    fixture={'width_px':1200,'height_px':800,'fit':mode,'focal_point':[.25,.75]}
    if mode=='crop':fixture['crop']=[.1,.1,.1,.1]
    direct=copy.deepcopy(pic);direct['data']=fixture;direct['bounds']=[1,1,4,4]
    result=run_stage('DEC-036',{'elements':[direct]},schemas=schemas)['result']['images'][0]
    assert all(0<=v<1 for v in result['crop'])
    if mode=='contain':assert result['crop']==[0,0,0,0]
    else:assert result['crop'][0]+result['crop'][2]>0
    checks.append({'name':f'explicit_{mode}_geometry','passed':True})
plain,style=candidate('editorial',base,1,3,DEFAULT_STYLE)
def rejected(name,node,payload,code,reg=None):
    try:run_stage(node,payload,reg,schemas)
    except TaskError as error:
        assert error.code==code,(name,error.code,code)
        checks.append({'name':name,'passed':True,'expected_code':code});return
    raise AssertionError(name)
rejected('DEC030_invalid_order','DEC-030',{'content':base,'style':DEFAULT_STYLE,'order':3,'page_count':3},'LAYOUT_PAGE_ORDER_INVALID')
rejected('DEC031_all_rejected','DEC-031',{'candidates':[]},'LAYOUT_CAPACITY_UNSUPPORTED')
rejected('DEC032_missing_elements','DEC-032',{},'LAYOUT_INPUT_MISSING')
bad=copy.deepcopy(plain);bad[1]['bounds']=bad[0]['bounds']
rejected('DEC033_overlap','DEC-033',{'elements':bad},'LAYOUT_SLOT_OVERLAP')
badstyle={**DEFAULT_STYLE,'font':'Unavailable Font'}
rejected('DEC034_unknown_font','DEC-034',{'elements':plain,'style':badstyle},'LAYOUT_FONT_UNSUPPORTED')
bad=copy.deepcopy(plain);bad[0]['format']['color']=DEFAULT_STYLE['background']
rejected('DEC035_contrast','DEC-035',{'elements':bad,'style':DEFAULT_STYLE},'LAYOUT_CONTRAST_INSUFFICIENT')
bad=[copy.deepcopy(pic)];bad[0]['data']['width_px']=0
rejected('DEC036_bad_dimensions','DEC-036',{'elements':bad},'IMAGE_DIMENSIONS_INVALID')
rejected('DEC037_requested_animation','DEC-037',{'enhancements':{'animation':'fade'}},'LAYOUT_ENHANCEMENT_UNSUPPORTED')
rejected('DEC038_office_round_trip','DEC-038',{'elements':plain,'backend_requirements':{'office_round_trip':True}},'LAYOUT_BACKEND_REQUIREMENT_UNSUPPORTED',registry)
bad=copy.deepcopy(plain);bad[1]['text']=['עברית']
rejected('rtl_not_silently_ltr','DEC-034',{'elements':bad,'style':DEFAULT_STYLE},'LAYOUT_RTL_UNSUPPORTED')
bad=copy.deepcopy(plain);bad[1]['text']=['文字'*1500]
rejected('long_text_not_truncated','DEC-034',{'elements':bad,'style':DEFAULT_STYLE},'TEXT_CAPACITY_EXCEEDED')
bad=[copy.deepcopy(pic)];bad[0]['data'].update(fit='crop');bad[0]['data'].pop('crop',None)
rejected('crop_requires_explicit_ratios','DEC-036',{'elements':bad},'IMAGE_CROP_REQUIRED')
bad=copy.deepcopy(plain);bad[1]['type']='smartart'
rejected('backend_unknown_native_type','DEC-038',{'elements':bad},'LAYOUT_OBJECT_UNSUPPORTED',registry)
assert base['body']==['保留原始文字','检查完整对象']
checks.append({'name':'caller_content_unchanged','passed':True})
report={'ok':True,'checks':checks,'check_count':len(checks),'requirement_ids':[f'DEC-{n:03d}' for n in range(30,39)]+['SYS-010','SYS-011','TPL-007','TPL-011','TPL-012','TPL-013'],
    'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/yoloongppt/layouts.py',ROOT/'src/yoloongppt/layout_decisions.py',ROOT/'contracts/layout-stage-node.schema.json']},
    'evidence_scope':'Direct native stage validation with synthetic layout fixtures and actual locally created PNG; not model grounding, E2E or full node/AC acceptance.',
    'limitations':['Complete brand locks, template selection, RTL, all native objects, advanced masks/effects/animation and multi-backend/Office acceptance remain incomplete.']}
(out/'layout-stages.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'layout-traces.json').write_text(json.dumps(traces,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ok':True,'checks':len(checks),'report':str(out/'layout-stages.json')}))
