"""Execute vendored upstream modules and existing real six-page evidence."""
import copy
import json
from pathlib import Path

from yoloongppt.errors import TaskError
from yoloongppt.templates import parse_template
from yoloongppt.upstream_quality import audit_upstream_quality, instruction_leaks, validate_upstream_review
from yoloongppt.upstream_templates import analyze_upstream_template, validate_template_content, validate_native_slot_content, VENDOR

OUT=Path('/runtime/upstream-quality-templates-artifacts')
OUT.mkdir(parents=True,exist_ok=True)
checks=[]


def verify(name,condition):
    assert condition,name
    checks.append({'check':name,'passed':True})


def rejects(name,call,code):
    try:call()
    except TaskError as exc:verify(name,exc.code==code)
    else:raise AssertionError(name+' did not reject')


good={'verdict':'pass','summary':'No visible issue in supplied images.','issues':[]}
verify('Original PPTAgent validate_review pass',validate_upstream_review(good)['ok'])
bad={'verdict':'pass','summary':'Invalid pass.','issues':[{'severity':'major','slide':1,'description':'Clipping','suggested_fix':'Resize explicit object'}]}
rejects('Upstream refuses pass with major issue',lambda:validate_upstream_review(bad),'UPSTREAM_VISUAL_REVIEW_INVALID')
bad['verdict']='fail';verify('Upstream preserves fail',not validate_upstream_review(bad)['ok'])
bad['issues'][0]['slide']=99
rejects('Mapped actual deck rejects out-of-scope slide',lambda:validate_upstream_review(bad,slide_count=6),'UPSTREAM_VISUAL_REVIEW_INVALID')
rejects('Upstream rejects empty summary',lambda:validate_upstream_review({'verdict':'pass','summary':'','issues':[]}),'UPSTREAM_VISUAL_REVIEW_INVALID')

prior=Path('/workspace/validation/stage-closure-artifacts/description-generated')
deck=json.loads((prior/'deck-spec.json').read_text('utf-8'))
renders=json.loads((prior/'render-report.json').read_text('utf-8'))
mapping=json.loads((prior/'object-map.json').read_text('utf-8'))
task=json.loads((prior/'task.json').read_text('utf-8'))
result=audit_upstream_quality(deck,prior/'deck.pptx',mapping,renders,prior)
verify('Actual 6-page declared PNG hashes execute original freshness check',result['checks'][0]['passed'])
leaks=[i for i in result['issues'] if i['code']=='TASK_INSTRUCTION_LEAK']
verify('Actual prior cover page-control leakage automatically detected',len(leaks)>=1)
verify('Leak locates original native object and evidence',all(i['object_id'] and i['measurement']['prompt_span'] for i in leaks))
verify('Leak retains measured threshold and explicit fail action',all(i['threshold'] and i['action']['mode']=='fail' for i in leaks))
clean=copy.deepcopy(deck);clean['slides'][0]['content']['body']=['预算管理采用6页培训材料。','来源：偏好6页；允许按软预算分页。','本页介绍PPT的制作方法。']
verify('No generic keyword false positive for budget/PPT/provenance',not instruction_leaks(clean,task))
missing=copy.deepcopy(task);missing['runtime_preferences']={}
verify('No preference association means no invented instruction claim',not instruction_leaks(deck,missing))
damaged=copy.deepcopy(renders);damaged['artifacts'][1]['hash']='0'*64
bad_result=audit_upstream_quality(deck,prior/'deck.pptx',mapping,damaged,prior)
verify('Tampered PNG hash is explicit P0 freshness issue',any(i['code']=='UPSTREAM_RENDER_STALE' and i['severity']=='P0' for i in bad_result['issues']))
partial=copy.deepcopy(renders);partial['artifacts']=[x for x in partial['artifacts'] if x.get('slide_id')!=deck['slides'][0]['slide_id']]
verify('Missing page is explicit scope issue',any(i['code']=='UPSTREAM_RENDER_SCOPE_INCOMPLETE' for i in audit_upstream_quality(deck,prior/'deck.pptx',mapping,partial,prior)['issues']))

standard=json.loads((VENDOR/'standard-template.json').read_text('utf-8'))
analysis=analyze_upstream_template(standard,source='P03/templates/standard/template.json')
verify('Actual full Presenton Standard element/layout models validate',len(analysis['layouts'])==len(standard['layouts']))
verify('Actual upstream schemas have editable capacity fields',any(s['capacity']['characters'] for l in analysis['layouts'] for s in l['slots']))
verify('Real template declared bounds are not falsely render verified',all(s['capacity']['status']=='upstream_declared_not_render_verified' for l in analysis['layouts'] for s in l['slots']))
simple={'layouts':[{'id':'example','description':'Explicit caption','components':[{'id':'caption','description':'Caption','position':{'x':0,'y':0},'elements':[{'type':'text','name':'caption','decorative':False,'runs':[{'text':'示例'}],'min_length':1,'max_length':5,'position':{'x':0,'y':0},'size':{'width':200,'height':40}}]}]}]}
small=analyze_upstream_template(simple)
verify('Generated upstream schema accepts exact capacity',validate_template_content(small,'example',{'caption':{'caption':'12345'}})['valid'])
rejects('Over-capacity text fails without trimming',lambda:validate_template_content(small,'example',{'caption':{'caption':'123456'}}),'UPSTREAM_TEMPLATE_CAPACITY_FAILED')
rejects('Unexpected field cannot silently enter content',lambda:validate_template_content(small,'example',{'caption':{'caption':'ok','unknown':'bad'}}),'UPSTREAM_TEMPLATE_CAPACITY_FAILED')
duplicate=copy.deepcopy(simple);duplicate['layouts'].append(copy.deepcopy(duplicate['layouts'][0]))
rejects('Duplicate layout ID rejected',lambda:analyze_upstream_template(duplicate),'UPSTREAM_TEMPLATE_INVALID')
invalid=copy.deepcopy(simple);invalid['layouts'][0]['components'][0]['elements'][0]['runs'][0]={'type':'chart','text':'bad'}
rejects('Native upstream text-run type validation retained',lambda:analyze_upstream_template(invalid),'UPSTREAM_TEMPLATE_INVALID')
native=analyze_upstream_template(parse_template((prior/'deck.pptx').read_bytes()),source='actual native deck')
verify('Actual OOXML template feeds upstream content schema',native['native_source'] and len(native['layouts'])>0)
verify('Native unknown character capacities stay unknown',all(s['capacity']['characters'] is None and s['capacity']['status']=='unmeasured' for l in native['layouts'] for s in l['slots']))
native_layout=next(l for l in native['layouts'] if l['slots'])
native_slot=native_layout['slots'][0]
verify('Native original slot/index/geometry identity retained',native_slot['native_slot_id'] and native_slot['bounds'] and native_slot['placeholder_index'] is not None)
verify('Selected native slot content uses original schema without requiring all placeholders',validate_native_slot_content(native,native_layout['layout_id'],{native_slot['placeholder_index']:'原生中文内容'})['valid'])
rejects('Native unknown placeholder rejects',lambda:validate_native_slot_content(native,native_layout['layout_id'],{999:'bad'}),'UPSTREAM_TEMPLATE_SLOT_UNKNOWN')
rejects('Native non-text content rejects at upstream schema',lambda:validate_native_slot_content(native,native_layout['layout_id'],{native_slot['placeholder_index']:42}),'UPSTREAM_TEMPLATE_CAPACITY_FAILED')
bad_native=parse_template((prior/'deck.pptx').read_bytes())
next(s for l in bad_native['layouts'] for s in l['slots'] if 'text' in s['content_types'])['capacity']['characters']=-1
rejects('Invalid declared native capacity is structured failure',lambda:analyze_upstream_template(bad_native),'UPSTREAM_TEMPLATE_INVALID')

out={'task_ids':['TASK-RES-032','TASK-TPL-004','TASK-TPL-007','TASK-TPL-008','TASK-QA-013','TASK-QA-020','TASK-SYS-014','TASK-SYS-015'],
     'checks':checks,'passed':len(checks),'quality':result,'presenton_template':{'version':analysis['version'],'layout_count':len(analysis['layouts']),'slot_count':sum(len(l['slots']) for l in analysis['layouts'])},'scope':'Component plus fixed existing real six-page evidence; not full AC/system acceptance'}
(OUT/'summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'presenton-schema.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'summary':str(OUT/'summary.json')},ensure_ascii=False))
