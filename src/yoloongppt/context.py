"""DEC-002: normalize explicit constraints, retaining candidates and conflict evidence."""
import copy
import hashlib
import re
import time
from pathlib import Path

from .artifacts import entity, RunArtifacts
from .errors import TaskError
from .tasks import validate_task

DEFAULTS = {'page_count': 10, 'language': 'zh-CN', 'aspect_ratio': '16:9', 'minimum_font_size': 16,
            'template': None, 'brand': None, 'output_formats': ['pptx','pdf','png'], 'audience': None,
            'scenario': None, 'duration': None, 'tone': None, 'citation_policy': 'notes'}
ALIASES = {'page_target':'page_count', 'page_budget':'page_count', 'template_ref':'template', 'formats':'output_formats'}


def canonical(field, value):
    field = ALIASES.get(field, field)
    if field == 'page_count' and isinstance(value, str) and re.fullmatch(r'\s*\d+\s*(?:页)?\s*', value):value=int(re.search(r'\d+',value)[0])
    if field == 'aspect_ratio' and isinstance(value, str):value=re.sub(r'\s+','',value).replace('：',':').replace('/' ,':')
    if field == 'language' and isinstance(value, str):value={'中文':'zh-CN','简体中文':'zh-CN','zh':'zh-CN','zh-cn':'zh-CN','英文':'en','english':'en'}.get(value.lower(),value)
    if field == 'output_formats' and isinstance(value, str):value=[x.strip().lower() for x in re.split(r'[,，、+和及 ]+',value) if x.strip()]
    if field == 'output_formats' and isinstance(value,list) and all(isinstance(x,str) for x in value):value=sorted(set(x.lower() for x in value))
    return field, value


def supported(field, value):
    if field == 'page_count':return type(value) is int and 1 <= value <= 30
    if field == 'language':return value == 'zh-CN'
    if field == 'aspect_ratio':return value == '16:9'
    if field == 'minimum_font_size':return type(value) in {int,float} and value == 16
    if field == 'output_formats':return isinstance(value,list) and bool(value) and all(isinstance(x,str) and x in {'pptx','pdf','png'} for x in value)
    if field in {'template','brand'}:return value is None
    if field == 'citation_policy':return value == 'notes'
    return value is None


def normalize(task, schemas, trace):
    begin=time.monotonic();validate_task(task,schemas,trace)
    original=task['constraints'];constraints=copy.deepcopy(original);candidates=[];issues=[];warnings=[]
    for group in ['hard','soft','defaults']:
        for item in constraints[group]:item['field'],item['value']=canonical(item['field'],item['value'])
    seen=set()
    def add(field,value,level,reference,record=None):
        field,value=canonical(field,value)
        candidate={'node_id':'DEC-002','candidate_id':entity('candidate'),'value':{'field':field,'value':value,'level':level},
                   'score':{'hard':1.0,'soft':0.7,'default':0.2}[level], 'reasons':[{'source':reference,'kind':level}],
                   'evidence_refs':[reference],'constraints':[{'known_field':field in DEFAULTS,'current_execution_supported':supported(field,value)}]}
        if record is not None:candidate['reasons'][0]['original_constraint']=copy.deepcopy(record)
        candidates.append(candidate)
        return candidate
    for level,key in [('hard','hard'),('soft','soft'),('default','defaults')]:
        for item in original[key]:
            if item['constraint_id'] in seen:issues.append({'code':'CONSTRAINT_ID_DUPLICATE','field':item['field'],'constraint_id':item['constraint_id']})
            seen.add(item['constraint_id']);add(item['field'],item['value'],level,item['constraint_id'],item)
    for field,value in task['runtime_preferences'].items():add(field,value,'soft','runtime_preferences.'+field)
    if task['template_ref'] is not None:add('template',task['template_ref'],'hard','TaskSpec.template_ref')
    if 'formats' in task['output']:add('output_formats',task['output']['formats'],'hard','TaskSpec.output.formats')
    text=task.get('raw_request',{}).get('request',{}).get('raw_text','')
    requested_outputs=task.get('raw_request',{}).get('request',{}).get('requested_outputs',[])
    requested_formats=[]
    if requested_outputs:
        _,requested_formats=canonical('output_formats',requested_outputs)
        requirement=add('requested_output_requirements',requested_formats,'hard','raw_request.request.requested_outputs')
        requirement['constraints'].append({'semantics':'required inclusion in selected output formats; additional QA intermediates may be retained'})
    # Bounded positive phrases only in caller instructions. No material text is inspected.
    patterns=[('page_count',r'(\d+)\s*页',lambda m:int(m[1])),('aspect_ratio',r'\b(\d+\s*[:：/]\s*\d+)\b',lambda m:m[1]),
              ('language',r'(简体中文|中文|英文|English)',lambda m:m[1]),('output_formats',r'(?:输出|导出)(?:为|成|格式)?\s*((?:PPTX|PDF|PNG)(?:(?:\s*[,，、+和及]\s*)(?:PPTX|PDF|PNG))*)',lambda m:m[1])]
    for field,pattern,convert in patterns:
        for m in re.finditer(pattern,text,re.I):
            prefix=text[max(0,m.start()-12):m.start()]
            if field=='page_count' and prefix.endswith('第'):continue
            if re.search(r'(?:不要|不必|无需|不得|不)\s*$',prefix):
                warnings.append({'code':'NEGATED_CONSTRAINT_NOT_SELECTED','field':field,'location':f'raw_text:{m.start()}:{m.end()}'});continue
            level='soft' if re.search(r'希望|尽量|大约|约|最好|偏好',prefix) else 'hard'
            ref=f'raw_text:{m.start()}:{m.end()}'
            if field=='output_formats' and not re.search(r'仅|只',prefix):
                _,required=canonical(field,convert(m))
                if level=='hard':requested_formats=sorted(set(requested_formats+required))
                requirement=add('requested_output_requirements',required,level,ref)
                requirement['constraints'].append({'semantics':'required inclusion, not silent exclusion of other declared outputs'});continue
            add(field,convert(m),level,ref)
    for field,value in DEFAULTS.items():add(field,value,'default','system_default.'+field)
    selected=[];values={};conflicts=copy.deepcopy(original['conflicts'])
    for field in (set(DEFAULTS)|{c['value']['field'] for c in candidates})-{'requested_output_requirements'}:
        options=[c for c in candidates if c['value']['field']==field]
        hard=[c for c in options if c['value']['level']=='hard']
        soft=[c for c in options if c['value']['level']=='soft']
        declared=[c for c in options if c['value']['level']=='default' and not c['evidence_refs'][0].startswith('system_default.')]
        pool=hard or soft or declared or [c for c in options if c['value']['level']=='default']
        distinct=[]
        for c in pool:
            if not any(type(c['value']['value']) is type(v) and c['value']['value']==v for v in distinct):distinct.append(c['value']['value'])
        if len(distinct)>1:
            issues.append({'code':'HARD_CONSTRAINT_CONFLICT' if hard else 'PREFERENCE_CONFLICT','field':field,'candidate_refs':[c['candidate_id'] for c in pool],'values':distinct});continue
        if field not in DEFAULTS:
            if hard:issues.append({'code':'HARD_CONSTRAINT_UNSUPPORTED','field':field,'value':distinct[0]})
            else:warnings.append({'code':'PREFERENCE_FIELD_UNSUPPORTED','field':field,'value':distinct[0]})
            continue
        winner=pool[0]
        if not hard and not supported(field,winner['value']['value']):
            warnings.append({'code':'PREFERENCE_DEGRADED' if soft else 'DEFAULT_UNSUPPORTED','field':field,'requested_value':winner['value']['value'],'applied_value':DEFAULTS[field], 'reason':'Current executor does not implement this value; preference/default retained in candidates.'})
            winner=next(c for c in options if c['evidence_refs']==['system_default.'+field])
        selected.append(winner['candidate_id']);values[field]=winner['value']['value']
        for c in options:c['constraints'].append({'selected':c['candidate_id']==winner['candidate_id'],'handling':'hard > soft > caller default > system default; equal-precedence disagreement blocks'})
    effective_formats=values.get('output_formats',[])
    if requested_formats and (not supported('output_formats',requested_formats) or not supported('output_formats',effective_formats) or not set(requested_formats).issubset(effective_formats)):
        issues.append({'code':'OUTPUT_REQUIREMENT_CONFLICT','field':'output_formats','required':requested_formats,'selected':values.get('output_formats'),'reason':'Requested output is missing or unavailable; cannot ignore it.'})
    for candidate in candidates:
        if candidate['value']['field']=='requested_output_requirements':
            wanted=candidate['value']['value']
            if candidate['value']['level']=='soft' and (not supported('output_formats',wanted) or not supported('output_formats',effective_formats) or not set(wanted).issubset(effective_formats)):
                warnings.append({'code':'OUTPUT_PREFERENCE_DEGRADED','requested_value':wanted,'applied_value':values.get('output_formats'),'reason':'Output preference unavailable or overridden; original candidate retained.'})
            elif not any(i['code']=='OUTPUT_REQUIREMENT_CONFLICT' for i in issues):selected.append(candidate['candidate_id'])
    for issue in issues:
        if issue['code']=='HARD_CONSTRAINT_CONFLICT':
            refs=issue['candidate_refs'];pool=[c for c in candidates if c['candidate_id'] in refs]
            conflicts.append({'conflict_id':entity('issue'),'field':issue['field'],'hard_constraint_refs':refs,'values':[{'constraint_id':c['candidate_id'],'value':c['value']['value']} for c in pool],'handling':'reported_blocking','resolution_result':'Must clarify conflicting hard values; no winner selected.'})
    constraints['conflicts']=conflicts
    for candidate in candidates:
        ref=candidate['evidence_refs'][0]
        if not (ref.startswith('raw_text:') or ref.startswith('runtime_preferences.')) or candidate['value']['field']=='requested_output_requirements':continue
        value=candidate['value'];item={'constraint_id':candidate['candidate_id'],'field':value['field'],'value':value['value'],'source':{'kind':'user_instruction','reference':ref}}
        if value['level']=='hard':constraints['hard'].append(item)
        else:constraints['soft'].append({**item,'disposition':'applied'})
    for item in constraints['soft']:
        field,wanted=canonical(item['field'],item['value']);applied=values.get(field)
        if field in values and wanted==applied:item.update(disposition='applied',applied_value=applied,handling_reason='Selected by DEC-002 and within current execution subset.')
        else:item.update(disposition='overridden' if any(c['value']['field']==field and c['value']['level']=='hard' for c in candidates) else 'degraded',applied_value=applied,handling_reason='Hard precedence, conflict or current execution support; original candidate retained.')
    constraints['defaults'] += [{'constraint_id':'system_default.'+f,'field':f,'value':v,'source':{'kind':'system_default','reference':'DEC-002 versioned runtime defaults'},'used':False} for f,v in DEFAULTS.items()]
    for item in constraints['defaults']:
        candidate=next(c for c in candidates if c['evidence_refs']==[item['constraint_id']]);item.update(used=candidate['candidate_id'] in selected,handling_reason='DEC-002 selects defaults only without higher precedence and within current execution support.')
    schemas.validate('constraint-set.schema.json',constraints)
    output={'status':'needs_clarification' if issues or conflicts else 'normalized','audience':values.get('audience'), 'scenario':values.get('scenario'),
            'duration':values.get('duration'),'language':values.get('language'),'tone':values.get('tone'),'aspect_ratio':values.get('aspect_ratio'),
            'page_target':values.get('page_count'),'citation_policy':values.get('citation_policy'), 'template':values.get('template'),'brand':values.get('brand'),
            'values':values,'constraints':constraints,'issues':issues,'warnings':warnings,'trace_id':trace}
    schemas.validate('presentation-context.schema.json',output)
    decision={'trace_id':trace,'node_id':'DEC-002','input':task,'candidates':candidates,'selected':selected,
              'rules':{'version':'DEC-002-1','mechanism':'Canonical aliases; bounded raw instruction extraction; explicit hard/soft/default precedence; no arbitrary tie breaking.',
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fallback':'Conflict blocks; unsupported soft/default explicitly falls back to known system default.'},
              'output':output,'duration':round(time.monotonic()-begin,6),'error':{'code':'CONSTRAINTS_UNRESOLVED','issues':issues,'conflicts':conflicts} if output['status']!='normalized' else None}
    schemas.validate('decision-trace.schema.json',decision)
    return {'ok':True,'trace_id':trace,'operation':'normalize_context','context':output,'decision_trace':decision}


def run_context(task,schemas,trace):
    result=normalize(task,schemas,trace);artifacts=RunArtifacts()
    artifacts.json('decision-context.json',result['decision_trace']);artifacts.json('presentation-context.json',result['context'])
    result.update(run_id=artifacts.run_id,artifact_root=str(artifacts.path));artifacts.json('result.json',result)
    artifacts.json('manifest.json',{'run_id':artifacts.run_id,'artifacts':artifacts.manifest()});return result
