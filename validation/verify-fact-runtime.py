"""Bounded DEC-004/005 contracts, adversarial evidence, CLI/API and projection."""
import copy,hashlib,json,subprocess,sys,urllib.request
from pathlib import Path
from yoloongppt.schemas import ROOT,SchemaRegistry
from yoloongppt.errors import TaskError,trace_id
from yoloongppt.sources import inspect_sources
from yoloongppt.evidence import EvidenceStore
from yoloongppt.facts import VALUE_FIELDS,resolve,boundaries,project,validate_interpretation,approved_text,planner_boundary,value_identity
from yoloongppt.artifacts import entity

s=SchemaRegistry();cases=[];saved=[]
def check(id,condition,actual):
 assert condition,id
 cases.append({'id':id,'passed':True,'actual':actual})
def fail(id,fn,code):
 try:fn()
 except TaskError as e:check(id,e.code==code,e.code)
 else:raise AssertionError(id)
task=json.loads(Path('/runtime/runs/f75a27dc-5e9d-43fd-90a9-07164f468fb5/task.json').read_text('utf-8'))
task['sources']=[{'source_id':entity('source'),'kind':'text','content':'学校节能试点2026年降低能耗8%。','metadata':{'source_role':'fact'}},{'source_id':entity('source'),'kind':'text','content':'学校节能试点2026年降低能耗9%。','metadata':{'source_role':'fact'}}]
sources=inspect_sources(task,s,EvidenceStore(),trace_id());evidence=sources['evidence']
def value(raw,n):return {**{f:None for f in VALUE_FIELDS},'raw_text':raw,'numeric_value':n,'unit':'%','period':'2026年'}
claims=[{'fact_key':'学校试点2026降低能耗','fact_kind':'percentage','value':value(n+'%',n),'provenance':'fact','quotes':[{'evidence_id':e['evidence_id'],'quote':e['raw_text']}],'reason':'对应来源的原始试点结果。'} for n,e in zip(['8','9'],evidence)]
interpretation={'coverage':[{'evidence_id':e['evidence_id'],'classification':'facts','reason':'数值断言。'} for e in evidence],'claims':claims,'missing':[]}
base={'trace_id':trace_id(),'evidence':evidence,'interpretation':interpretation,'policy':{}}
def run(id,doc):
 r=resolve(doc,s);saved.append({'id':id,'input':doc,'result':r});return r['resolution']
unresolved=run('conflict_no_default_priority',base);check('conflict_no_default_priority',unresolved['status']=='needs_clarification' and len(unresolved['conflicts'])==1,'All two values retained; no caller selection.')
priority=copy.deepcopy(base);priority['policy']={'source_precedence':[evidence[0]['source_id'],evidence[1]['source_id']]}
r=run('priority_selects_8',priority);check('priority_selects_8',r['status']=='ready' and r['groups'][0]['claims'][0]['value']['numeric_value']=='8' and r['groups'][0]['selected_claim_id']==r['groups'][0]['claims'][0]['claim_id'],'Caller priority only.')
selection=copy.deepcopy(base);selection['policy']={'conflict_selections':[{'fact_key':claims[0]['fact_key'],'source_id':evidence[1]['source_id']}]}
selected=run('explicit_selection_9',selection);check('explicit_selection_9',selected['status']=='ready' and selected['groups'][0]['basis']=='explicit_user_selection','Explicit source selection retained.')
equal=copy.deepcopy(base);equal['interpretation']['claims']=equal['interpretation']['claims'][:1];eq=run('one_uncontested_fact',equal);check('one_uncontested_fact',eq['status']=='ready' and not eq['conflicts'],'No invented priority.')
check('large_numeric_identity_exact',value_identity(value('123456789012345678901234567890','123456789012345678901234567890'))!=value_identity(value('123456789012345678901234567891','123456789012345678901234567891')),'No Decimal-context rounding merges different source numbers.')
bad=copy.deepcopy(equal);bad['policy']['conflict_selections']=[{'fact_key':claims[0]['fact_key'],'source_id':evidence[1]['source_id']}]
fail('uncontested_selection_without_claim_rejected',lambda:resolve(bad,s),'FACT_SELECTION_AMBIGUOUS')
def bound(id,doc,res):
 inp={**doc,'resolution':res};out=boundaries(inp,s);saved.append({'id':id,'input':inp,'result':out});return out['boundaries']
b=bound('supported_fact_bound',priority,r);check('supported_fact_bound',b['status']=='ready' and b['fact_constraints']['numbers'][0]['resolution_status']=='user_selected','FactConstraintSet consumes resolved selected claim.')
check('unresolved_boundary_blocks',bound('unresolved_boundary_blocks',base,unresolved)['status']=='needs_clarification','Unresolved value cannot be used.')
missing=copy.deepcopy(priority);missing['interpretation']['missing']=[{'fact_key':'预算','fact_kind':'amount','required':True,'reason':'要求预算但原文没有。','evidence_refs':[]}]
mr=run('missing_resolution',missing);mb=bound('required_missing_asks',missing,mr);check('required_missing_asks',mb['status']=='needs_clarification' and mb['actions'][0]['mode']=='ask','Required missing blocks before content model.')
assume=copy.deepcopy(missing);assume['policy']['missing_rules']=[{'fact_key':'预算','fact_kind':'amount','mode':'assume','value':{**{f:None for f in VALUE_FIELDS},'raw_text':'12万元','numeric_value':'12','unit':'万元'},'reason':'调用方明确预算假设。'}]
ab=bound('explicit_assumption_registered',assume,run('assumption_resolution',assume));check('explicit_assumption_registered',len(ab['assumptions'])==1 and ab['fact_constraints']['numbers'][-1]['status']=='assumption','Explicit assumption ID/value/user_visible preserved.')
check('assumption_identity_stable',ab['assumptions'][0]['assumption_id']==boundaries({**assume,'resolution':resolve(assume,s)['resolution']},s)['boundaries']['assumptions'][0]['assumption_id'],'Same fact/rule/value gives stable typed ID across recovery.')
placeholder=copy.deepcopy(missing);placeholder['policy']['missing_rules']=[{'fact_key':'预算','fact_kind':'amount','mode':'placeholder','label':'预算待确认','reason':'调用方要求占位。'}]
pb=bound('explicit_placeholder',placeholder,run('placeholder_resolution',placeholder));check('explicit_placeholder',pb['status']=='ready' and pb['actions'][0]['label']=='预算待确认','Missing value remains absent.')
inference=copy.deepcopy(priority);inference['interpretation']['claims'][1]['fact_key']='另一试点2026降低能耗'
inference['policy']['missing_rules']=[{'fact_key':'降低能耗差值','fact_kind':'percentage','mode':'infer','method':'difference','premises':['另一试点2026降低能耗','学校试点2026降低能耗'],'reason':'用户明确比较两个同范围数据。'}]
ib=bound('explicit_exact_inference',inference,run('inference_resolution',inference));check('explicit_exact_inference',ib['actions'][0]['formula']['result']=='1' and ib['actions'][0]['formula']['exact'],'Exact rational arithmetic, recorded assumption; no source invention.')
unused=copy.deepcopy(inference);unused['policy']['missing_rules'][0]['value']=value('12%','12')
fail('infer_unused_value_rejected',lambda:resolve(unused,s),'TASK_SCHEMA_INVALID')
unused=copy.deepcopy(placeholder);unused['policy']['missing_rules'][0]['value']=value('12%','12')
fail('placeholder_unused_value_rejected',lambda:resolve(unused,s),'TASK_SCHEMA_INVALID')
bad=copy.deepcopy(base);bad['interpretation']['claims'][0]['quotes'][0]['quote']='来源并不存在的句子'
fail('fabricated_quote_rejected',lambda:resolve(bad,s),'FACT_QUOTE_UNGROUNDED')
bad=copy.deepcopy(base);bad['interpretation']['claims'][0]['value']['numeric_value']='80'
fail('unauthorized_numeric_change',lambda:resolve(bad,s),'FACT_NUMBER_TRANSFORM_UNAUTHORIZED')
bad=copy.deepcopy(base);bad['interpretation']['claims'][0]['value']['period']='2027年'
fail('invented_period_rejected',lambda:resolve(bad,s),'FACT_SCOPE_UNGROUNDED')
bad=copy.deepcopy(base);bad['interpretation']['coverage'].pop()
fail('coverage_omission_rejected',lambda:resolve(bad,s),'FACT_COVERAGE_INCOMPLETE')
shared=copy.deepcopy(base);shared['interpretation']['claims']=[{'fact_key':'同口径','fact_kind':'quote','value':{**{f:None for f in VALUE_FIELDS},'raw_text':'学校节能试点'},'provenance':'fact','quotes':[{'evidence_id':e['evidence_id'],'quote':e['raw_text']} for e in evidence],'reason':'两来源相同的原文实体。'}]
sr=resolve(shared,s)['resolution'];check('shared_literal_split_per_source',len(sr['groups'][0]['claims'])==2 and sr['status']=='ready','Each original source independently grounds full literal assertion.')
shared['interpretation']['claims'][0]['value']=value('8%','8')
fail('shared_numeric_not_grounded_each_source',lambda:resolve(shared,s),'FACT_VALUE_UNGROUNDED')
scoped=copy.deepcopy(base);scoped['interpretation']['claims'][0]['quotes'][0]['quote']='8%'
check('same_source_scope_quote_attached',len(validate_interpretation(evidence,scoped['interpretation'],s)[0]['quotes'])>1,'Exact same-source 2026年 scope attached; model output not rewritten.')
date=copy.deepcopy(base);date['interpretation']['claims'][0]['value'].update(raw_text='2026年降低能耗8%',normalized_text=None,date_value='2026',date_precision='year')
check('date_literal_inside_full_claim',validate_interpretation(evidence,date['interpretation'],s)[0]['value']['date_value']=='2026','Exact year text normalization preserves original precision.')
date['interpretation']['claims'][0]['value'].update(raw_text='2026年',numeric_value=None,date_value='2026年',date_precision='month')
fail('date_precision_invention_rejected',lambda:resolve(date,s),'FACT_DATE_TRANSFORM_UNAUTHORIZED')
bad={**priority,'resolution':copy.deepcopy(r)};bad['resolution']['groups'][0]['selected_claim_id']=None
fail('tampered_resolution_rejected',lambda:boundaries(bad,s),'FACT_RESOLUTION_CHANGED')
rounded=copy.deepcopy(inference);rounded['policy']['missing_rules'][0].update(method='ratio',premises=['学校试点2026降低能耗','另一试点2026降低能耗'])
fail('implicit_rounding_rejected',lambda:boundaries({**rounded,'resolution':resolve(rounded,s)['resolution']},s),'INFERENCE_PRECISION_UNSUPPORTED')
projection=project(sources,r,b,interpretation)
check('loser_value_not_factual_input','9%' not in '\n'.join(projection['approved_texts'].values()) and '8%' in '\n'.join(projection['approved_texts'].values()),'Original raw 9% remains in immutable evidence, excluded only in explicit projection.')
check('full_original_evidence_retained',projection['evidence']==evidence,'No source record rewritten or deleted.')
check('copy_model_does_not_receive_rejected_values','9%' not in json.dumps(planner_boundary(projection),ensure_ascii=False),'Full conflict retained for audit/reviewer; usable-fact projection excludes competing values.')
bad=copy.deepcopy(projection);bad['approved_texts'].pop(evidence[0]['evidence_id'])
fail('missing_projection_no_raw_fallback',lambda:approved_text(bad,evidence[0]),'FACT_PROJECTION_INCOMPLETE')
redundant=copy.deepcopy(priority);redundant['interpretation']['missing']=[{'fact_key':claims[0]['fact_key'],'fact_kind':'percentage','required':True,'reason':'冲突未解决的模型提议。','evidence_refs':[]}]
rb=bound('grounded_selection_resolves_missing_proposal',redundant,resolve(redundant,s)['resolution']);check('grounded_selection_resolves_missing_proposal',rb['status']=='ready' and rb['actions'][0]['mode']=='already_supported','DEC-004 actual selected value supersedes same-key/kind missing proposal; proposal retained in trace.')
folder=Path('/runtime/fact-validation');folder.mkdir(exist_ok=True)
for command,doc,key in [('resolve-evidence',priority,'resolution'),('fact-boundaries',{**priority,'resolution':r},'boundaries')]:
 path=folder/(command+'.json');path.write_text(json.dumps(doc,ensure_ascii=False),'utf-8')
 process=subprocess.run([sys.executable,'-m','yoloongppt',command,str(path)],capture_output=True,text=True,encoding='utf-8');result=json.loads(process.stdout)
 check('CLI_'+command,process.returncode==0 and result[key]['status']=='ready',{'run_id':result.get('run_id')})
 req=urllib.request.Request('http://127.0.0.1:8000/'+command,data=json.dumps(doc).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as response:result=json.loads(response.read());check('HTTP_'+command,response.status==200 and result[key]['status']=='ready',{'run_id':result['run_id']})
(folder/'fact-cases.json').write_text(json.dumps({'scope':'Synthetic boundary fixtures loaded by actual SourceLoader; not real model outcomes.','cases':saved},ensure_ascii=False,indent=2)+'\n','utf-8')
tracked=['facts.py','generation.py','planning.py','quality.py','review.py','revision.py','api.py','__main__.py']
report={'passed':True,'cases':cases,'source_sha256':{str(Path('src/yoloongppt')/name):hashlib.sha256((ROOT/'src/yoloongppt'/name).read_bytes()).hexdigest() for name in tracked},'scope':'DEC-004/005 exact-grounding, explicit decision rules and consumed facts projection. Full semantic extraction, graph and system acceptance unproven.'}
(folder/'fact-runtime.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'passed':True,'checks':len(cases)},ensure_ascii=False))
