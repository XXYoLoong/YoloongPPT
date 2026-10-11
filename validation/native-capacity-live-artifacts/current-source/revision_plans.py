"""DEC-039/SYS-016/REV-006/010: local, lock-aware, non-factual repair plans."""
import copy
import math
from .artifacts import entity
from .errors import TaskError,trace_id
from .quality_rules import contrast

NODE_MAP={'structure':'adapter','geometry':'geometry','layout':'layout','style':'style','asset':'asset','accessibility':'accessibility','content':'content','fact':'fact_boundary','semantic':'content','diagram':'diagram','adapter':'adapter','QA':'QA'}
FACT_CODES={'FACT_NUMBER_UNSUPPORTED','FACT_NOTE_NUMBER_UNSUPPORTED','CHART_VALUE_UNSUPPORTED','ASSUMPTION_REFERENCE_UNKNOWN','ASSUMPTION_NOT_VISIBLE','PLACEHOLDER_NOT_VISIBLE','VISUAL_FACT_NUMBER_UNSUPPORTED'}

def _error(code,message,details=None):raise TaskError(code,message,'RevisionPlanner',['DEC-039','SYS-016','QA-019'],details or [])

def _index(deck,object_map):
 by={};slides={s['slide_id']:s for s in deck['slides']};mapped={o['logical_object_id']:o for o in object_map['objects']}
 for slide in deck['slides']:
  for element in slide['elements']:
   if element['object_id'] in by:_error('REVISION_DUPLICATE_OBJECT','对象ID重复，不能制定局部计划。')
   by[element['object_id']]=(slide,element)
 return by,slides,mapped

def build_plan(deck,object_map,issues,policy=None,trace=None,parent_run_id=None):
 policy=policy or {};trace=trace or trace_id()
 if set(policy)-{'locked_object_ids','locked_slide_ids','max_actions','allow_geometry','allow_style','parent_run_id'}:_error('REVISION_POLICY_UNSUPPORTED','修订策略含未登记字段，未忽略。')
 by,slides,mapped=_index(deck,object_map);locked=set(policy.get('locked_object_ids',[]));locked_slides=set(policy.get('locked_slide_ids',[]))
 if locked-set(by) or locked_slides-set(slides):_error('REVISION_LOCK_TARGET_UNKNOWN','锁定对象/页面不存在。')
 actions=[];blocked=[];candidates=[];seen=set()
 for item in issues:
  if item.get('severity') not in {'P0','P1','P2'}:_error('REVISION_ISSUE_INVALID','Issue severity必须为P0/P1/P2。')
  iid=item.get('issue_id') or entity('issue');oid=item.get('object_id');sid=item.get('slide_id');code=item['code'];node=item.get('action',{}).get('node','QA')
  if not oid and isinstance(item.get('detail'),str) and item['detail'] in by:oid=item['detail']
  state='fail';reason='No safe executable repair registered';changes={};op=None
  element=by.get(oid,(None,None))[1];slide=by.get(oid,(None,None))[0]
  if oid and not element:reason='Issue object does not exist in authoritative spec'
  elif sid and sid not in slides:reason='Issue slide does not exist in authoritative spec'
  elif oid in locked or (slide and slide['slide_id'] in locked_slides) or (element and element.get('locked')):reason='Locked object/slide preserved; issue cannot be silently bypassed'
  elif code in FACT_CODES or node in {'fact','semantic','content','fact_boundary'}:
   state='requires_user_input';reason='Requires grounded replacement/registered assumption or source correction; no automatic fact changes';node='fact_boundary' if code in FACT_CODES else 'content'
  elif element and oid in mapped:
   if code in {'OBJECT_OUT_OF_BOUNDS','OBJECT_GEOMETRY_MISMATCH'} and policy.get('allow_geometry',True):
    x,y,w,h=element['bounds'];width=deck['width_inches'];height=deck['height_inches']
    if 0<w<=width and 0<h<=height:
     changes={'bounds':[min(max(0,x),width-w),min(max(0,y),height-h),w,h]};state='ready';op='geometry';node='geometry';reason='Move only selected object within canvas; preserve size/content/IDs'
   elif code in {'TEXT_CONTRAST_LOW','ACTUAL_TEXT_CONTRAST_LOW'} and element['type']=='text' and policy.get('allow_style',True):
    bg=element.get('format',{}).get('fill',slide.get('style',{}).get('background','FFFFFF'));choices=['000000','FFFFFF'];best=max(choices,key=lambda c:contrast(c,bg))
    changes={'format':{'color':best}};state='ready';op='format';node='style';reason='Choose black/white foreground with maximum measured contrast; preserve content'
   elif code in {'FONT_TOO_SMALL','ACTUAL_FONT_TOO_SMALL'} and element['type']=='text' and policy.get('allow_style',True):
    changes={'font_size':max(element['font_size'],item.get('threshold',{}).get('minimum_pt',16))};state='requires_user_input';node='style';reason='Larger font requires capacity re-evaluation before execution; not silently shrunk or clipped'
   elif code in {'ALT_TEXT_MISSING'}:
    state='requires_user_input';node='accessibility';reason='Descriptive alt text requires grounded user/visual input; not invented'
   elif code in {'OBJECT_OVERLAP','IMAGE_STRETCHED','IMAGE_RESOLUTION_LOW','READING_ORDER_TITLE_AFTER_BODY'}:
    state='requires_user_input';reason='Needs explicit geometry/asset/order choice; related objects must remain unchanged'
  candidate={'candidate_id':entity('candidate'),'issue_id':iid,'object_id':oid,'slide_id':sid,'node':NODE_MAP.get(node,node),'state':state,'operation':op,'changes':changes,'reason':reason,'score':1 if state=='ready' else 0,'evidence':{'issue':copy.deepcopy(item)}};candidates.append(candidate)
  if state=='ready':
   key=(oid,op)
   if key in seen:
    prior=next(a for a in actions if a['object_id']==oid and a['operation']==op)
    if prior['changes']!=changes:blocked.append({'issue_id':iid,'severity':item['severity'],'state':'fail','reason':'Conflicting patches for same object/operation','candidate_id':candidate['candidate_id']});continue
    prior['issue_ids'].append(iid);continue
   seen.add(key);actions.append({'action_id':entity('revision_action'),'issue_ids':[iid],'slide_id':slide['slide_id'],'object_id':oid,'operation':op,'changes':changes,'before_spec':copy.deepcopy(element),'expected_native_mapping':copy.deepcopy(mapped[oid]),'rerun_nodes':[node,'selected_object','render','QA'],'preserve_fact_boundary':True,'preserve_unselected_objects':True})
  else:blocked.append({'issue_id':iid,'severity':item['severity'],'state':state,'reason':reason,'candidate_id':candidate['candidate_id']})
 maximum=policy.get('max_actions',100)
 if not isinstance(maximum,int) or isinstance(maximum,bool) or maximum<0:_error('REVISION_ACTION_LIMIT_INVALID','max_actions必须为非负整数。')
 if len(actions)>maximum:_error('REVISION_ACTION_LIMIT_EXCEEDED','计划超过用户明确的修订动作数量。',[{'actual':len(actions),'maximum':maximum}])
 status='fail' if any(b['state']=='fail' and b['severity']=='P0' for b in blocked) else 'needs_input' if blocked else 'ready'
 return {'plan_id':entity('revision_plan'),'trace_id':trace,'parent_run_id':parent_run_id or policy.get('parent_run_id'),'status':status,'scope':{'slide_ids':list(dict.fromkeys(a['slide_id'] for a in actions)),'object_ids':list(dict.fromkeys(a['object_id'] for a in actions))},'locked_object_ids':sorted(locked),'locked_slide_ids':sorted(locked_slides),'actions':actions,'blocked':blocked,'candidates':candidates,'all_issue_ids':[c['issue_id'] for c in candidates],'rerun_nodes':list(dict.fromkeys(n for a in actions for n in a['rerun_nodes'])),'preserve_unselected_objects':True,'full_acceptance':'not_passed'}

def validate_plan(plan,deck,object_map):
 by,slides,mapped=_index(deck,object_map)
 if plan['status']!='ready' or plan.get('blocked'):_error('REVISION_PLAN_BLOCKED','修订计划未就绪；不能跳过阻断。',plan.get('blocked',[]))
 expected_objects={a['object_id'] for a in plan['actions']};expected_slides={a['slide_id'] for a in plan['actions']}
 scope=plan.get('scope',{})
 if set(scope)!={'object_ids','slide_ids'} or set(scope['object_ids'])!=expected_objects or set(scope['slide_ids'])!=expected_slides or len(scope['object_ids'])!=len(expected_objects) or len(scope['slide_ids'])!=len(expected_slides):_error('REVISION_PLAN_SCOPE_INVALID','计划scope必须精确等于实际动作目标集合。')
 seen=set()
 for action in plan['actions']:
  oid=action['object_id']
  if oid not in by or oid not in mapped or oid in plan['locked_object_ids'] or action['slide_id'] in plan['locked_slide_ids']:_error('REVISION_PLAN_TARGET_INVALID','计划目标不存在或已锁定。')
  slide,element=by[oid]
  if element.get('locked') or slide.get('locked'):_error('REVISION_PLAN_TARGET_LOCKED','原对象或页面已锁定。')
  expected_keys={'geometry':{'bounds'},'format':{'format'},'text':{'replacement_text'}}
  if action['operation'] not in expected_keys or not isinstance(action['changes'],dict) or set(action['changes'])!=expected_keys[action['operation']]:_error('REVISION_PLAN_CHANGES_INVALID','动作changes字段须严格对应操作，未忽略额外值。')
  if action['slide_id']!=slide['slide_id'] or action['before_spec']!=element or action['expected_native_mapping']!=mapped[oid]:_error('REVISION_PLAN_STALE','对象规格或原生映射已改变；需重新制定计划。')
  key=(oid,action['operation'])
  if key in seen:_error('REVISION_PLAN_DUPLICATE_ACTION','重复目标操作。')
  seen.add(key)
  if action['operation']=='geometry':
   v=action['changes'].get('bounds')
   if not isinstance(v,list) or len(v)!=4 or not all(isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x) for x in v):_error('REVISION_PLAN_GEOMETRY_INVALID','非法边界。')
   x,y,w,h=v
   if x<0 or y<0 or w<=0 or h<=0 or x+w>deck['width_inches']+1e-6 or y+h>deck['height_inches']+1e-6:_error('REVISION_PLAN_GEOMETRY_INVALID','局部几何计划越界。')
  elif action['operation']=='format':
   formatting=action['changes'].get('format')
   if not isinstance(formatting,dict) or set(formatting)!={'color'}:_error('REVISION_PLAN_FORMAT_INVALID','当前format计划仅允许color，不执行其他格式字段。')
   color=formatting.get('color')
   if not isinstance(color,str) or len(color)!=6 or any(c not in '0123456789ABCDEFabcdef' for c in color):_error('REVISION_PLAN_FORMAT_INVALID','非法颜色。')
  elif action['operation']=='text':
   if not isinstance(action['changes'].get('replacement_text'),list):_error('REVISION_PLAN_TEXT_INVALID','文本修订需显式替换内容。')
  else:_error('REVISION_PLAN_OPERATION_UNSUPPORTED','计划操作没有实际消费。')
 return {'valid':True,'action_count':len(plan['actions']),'preserves_fact_boundary':True}

def history_input(plan,before_hash,after_hash,changed_parts,quality_before,quality_after):
 return {'plan_id':plan['plan_id'],'trace_id':plan['trace_id'],'instruction':{'source':'quality_issues','issue_ids':plan['all_issue_ids']},'scope':copy.deepcopy(plan['scope']),'before_specs':[copy.deepcopy(a['before_spec']) for a in plan['actions']],'object_changes':copy.deepcopy(plan['actions']),'before_pptx_hash':before_hash,'after_pptx_hash':after_hash,'changed_parts':list(changed_parts),'quality_before':copy.deepcopy(quality_before),'quality_after':copy.deepcopy(quality_after),'rerun_nodes':plan['rerun_nodes'],'locked_object_ids':plan['locked_object_ids'],'locked_slide_ids':plan['locked_slide_ids'],'unchanged_parts_byte_preserved':None,'note':'Executor must provide actual preservation evidence; planner does not claim bytes were preserved'}
