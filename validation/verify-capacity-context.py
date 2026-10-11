"""Incremental real normalization/binding checks for the integrated capacity path."""
import copy
import hashlib
import json
from pathlib import Path
from yoloongppt.context import normalize
from yoloongppt.narrative import prepare
from yoloongppt.planning import compile_deck,DEFAULT_STYLE
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.artifacts import entity

out=Path('/runtime/capacity-context-validation');out.mkdir(exist_ok=True)
schemas=SchemaRegistry();checks=[]
original=json.loads(Path('/runtime/runs/32ee63b0-832f-4054-ab3e-19721f1eada7/task.json').read_text('utf-8'))
def check(name,condition,observed):
    checks.append({'name':name,'passed':bool(condition),'observed':observed})
    (out/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    assert condition,(name,observed)
for text,language,level in [
    (original['raw_request']['request']['raw_text'],'zh-CN','default'),
    ('请用中文输出演示','zh-CN','hard'),
    ('请用英文演示','en','hard'),
    ('做3页英文','en','hard'),
    ('完整标题逐字使用“中文与English混合”，保留内容','zh-CN','default')]:
    task=copy.deepcopy(original);task['raw_request']['request']['raw_text']=text
    normalized=normalize(task,schemas,entity('trace'))
    context=normalized['context'];check('language:'+text[:24],context['values']['language']==language,context['values']['language'])
    decision=normalized['decision_trace']
    candidate=next(c for c in decision['candidates'] if c['candidate_id'] in decision['selected'] and c['value']['field']=='language')
    check('language-source:'+text[:24],candidate['value']['level']==level,candidate['value']['level'])
for text,level in [('初始预算3页，允许容量需要时续页','soft'),('必须3页','hard')]:
    task=copy.deepcopy(original);task['raw_request']['request']['raw_text']=text
    decision=normalize(task,schemas,entity('trace'))['decision_trace']
    candidate=next(c for c in decision['candidates'] if c['candidate_id'] in decision['selected'] and c['value']['field']=='page_count')
    check('page-budget:'+text,candidate['value']['level']==level,candidate['value']['level'])
proposal={'title':'保持断点对象身份','main_takeaway':'原内容保留','storyline':{'pattern':'fixture','rationale':'explicit'},
    'slides':[{'kind':'text','title':'原生对象身份','body':['同一对象保持稳定ID'], 'goal':'fixture','rationale':'explicit','notes':'fixture','evidence_refs':[], 'table':None,'chart':None}]}
first,_=compile_deck(proposal,DEFAULT_STYLE,entity('trace'))
again,_=compile_deck(proposal,DEFAULT_STYLE,entity('trace'),first)
ids={e['slot_key']:e['object_id'] for e in again['slides'][0]['elements']}
check('checkpoint-object-identities',ids=={e['slot_key']:e['object_id'] for e in first['slides'][0]['elements']},ids)
bindings=again['slides'][0]['bindings']
check('checkpoint-bindings-identities',all(b['object_id']==ids[b['slot_key']] for b in bindings),bindings)
decision=next(d for d in again['slides'][0]['layout']['selection_trace']['decisions'] if d['node_id']=='DEC-032')
check('checkpoint-decision-identities',all(b['object_id']==ids[b['slot_key']] for b in decision['result']['bindings']),decision['result']['bindings'])
report={'passed':True,'checks':checks,'model_calls':0,'render_calls':0,'source_hashes':{name:hashlib.sha256((Path('/workspace')/name).read_bytes()).hexdigest() for name in ['src/yoloongppt/context.py','src/yoloongppt/planning.py','validation/verify-capacity-context.py']},'system_acceptance':'not_passed'}
(out/'capacity-context-runtime.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'passed':True},ensure_ascii=False))
