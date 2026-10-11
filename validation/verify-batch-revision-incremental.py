"""Targeted regression for caption provenance, repeat bindings, body swaps and entrances."""
import copy
import json
import subprocess
import sys
from pathlib import Path

from yoloongppt.batch_revision import _apply_spec,_body_binding,_update_bodies,_image_content_index,_finalize_geometry
from yoloongppt.errors import TaskError
from yoloongppt.mcp_server import handle

root=Path('/runtime/batch-revision-validation');root.mkdir(exist_ok=True);checks=[]
def test(name,value):
    checks.append({'name':name,'passed':bool(value)})
    if not value:raise AssertionError(name)

# Synthetic component input is explicit; it is not a model call or AC acceptance.
sources={'evidence':[{'evidence_id':'e1','raw_text':'甲图'},{'evidence_id':'e2','raw_text':'乙图'}]}
image={'object_id':'imageA','type':'image','slot_key':'asset.A','data':{'asset_id':'B','caption':'甲图','caption_source_refs':['e1'],'sha256':'hashB'}}
caption={'object_id':'captionA','type':'text','role':'body','slot_key':'caption.A','text':['甲图'],'source_refs':['e1']}
slide={'slide_id':'s1','source_refs':['e1','e2'],'content':{'body':[],'images':[{'asset_id':'B','caption':'甲图','caption_source_refs':['e1'],'sha256':'hashB'}]},'elements':[image,caption]}
index=_image_content_index(slide,caption)
test('repeat_caption_binding_uses_stable_slot',index==0)
_apply_spec({'operation':'text','value':['乙图'],'content_image_index':index},slide,caption,{},sources,[])
test('caption_refs_changed_to_exact_selected_evidence',caption['source_refs']==['e2'] and slide['content']['images'][0]['caption_source_refs']==['e2'] and image['data']['caption_source_refs']==['e2'])
test('caption_and_image_projection_agree',caption['text']==[image['data']['caption']]==[slide['content']['images'][0]['caption']])
ambiguous=copy.deepcopy(sources);ambiguous['evidence'][0]['raw_text']='甲图 乙图'
try:_apply_spec({'operation':'text','value':['乙图'],'content_image_index':0},slide,caption,{},ambiguous,[])
except TaskError as error:test('ambiguous_caption_provenance_rejected',error.code=='REVISION_CAPTION_EVIDENCE_AMBIGUOUS')
else:test('ambiguous_caption_provenance_rejected',False)
before={'slides':[{'slide_id':'body','content':{'body':['甲段','乙段','丙段']}}]};after=copy.deepcopy(before)
span_a=_body_binding(before['slides'][0],{'text':['甲段']});span_b=_body_binding(before['slides'][0],{'text':['乙段']})
_update_bodies(after,before,{'body':[(span_a,['乙段']), (span_b,['甲段','甲补段'])]})
test('body_swap_and_length_change_use_immutable_spans',after['slides'][0]['content']['body']==['乙段','甲段','甲补段','丙段'] and before['slides'][0]['content']['body']==['甲段','乙段','丙段'])
try:_update_bodies(after,before,{'body':[(span_a,['新甲']), (span_a,['另甲'])]})
except TaskError as error:test('overlapping_body_edits_rejected',error.code=='REVISION_CONTENT_BINDING_CONFLICT')
else:test('overlapping_body_edits_rejected',False)
try:_apply_spec({'operation':'alt_text','value':'说明'},slide,{'type':'connector'}, {},sources,[])
except TaskError as error:test('connector_relation_not_overwritten',error.code=='REVISION_ALT_TARGET_UNSUPPORTED')
else:test('connector_relation_not_overwritten',False)

parent_id='39a2dbf3-c19b-4da2-99a6-27fe7b82ef7a';parent=Path('/runtime/runs')/parent_id
deck=json.loads((parent/'deck-spec.json').read_text('utf-8'));oid=deck['slides'][0]['elements'][0]['object_id']
from yoloongppt.existing_deck import inspect_deck,apply_patch
from yoloongppt.artifacts import sha256
from yoloongppt.revision import revision_sources
image_slide=copy.deepcopy(deck['slides'][1]);picture=next(e for e in image_slide['elements'] if e['type']=='image')
native=inspect_deck(parent/'deck.pptx');nid=next(o['object_id'] for s in native['slides'] for o in s['objects'] if o['name']==picture['object_id'])
registered=json.loads((parent/'resolved-assets.json').read_text('utf-8'))['entries'];facts=revision_sources(parent)
patches=[]
for edit in [{'operation':'geometry','value':[1,1,4,4]},{'operation':'image','value':{'asset_id':picture['data']['asset_id']},'content_image_index':0}]:
    op,value=_apply_spec(edit,image_slide,picture,deck,facts,registered);patches.append({'object_id':nid,'operation':op,'value':value})
_finalize_geometry(patches,{picture['object_id']:(image_slide,picture)},{picture['object_id']:nid},{picture['object_id']},{picture['object_id']})
out=root/('geometry-image-'+__import__('uuid').uuid4().hex+'.pptx')
report=apply_patch(parent/'deck.pptx',out,{'expected_sha256':sha256(parent/'deck.pptx'),'patches':patches})
actual=next(o for s in report['after']['slides'] for o in s['objects'] if o['object_id']==nid)
test('geometry_then_image_native_matches_final_contain',picture['bounds']==[1,2,4,2] and actual['bounds_emu']==[914400,1828800,3657600,1828800])
request={'instruction':'接口同范围锁校验','locked_object_ids':[oid],'edits':[{'object_id':oid,'operation':'text','value':['虚构测试标题']}]}
path=root/'entrance-locked-request.json';path.write_text(json.dumps(request,ensure_ascii=False),'utf-8')
cli=subprocess.run([sys.executable,'-B','-m','yoloongppt','revise',parent_id,str(path)],capture_output=True,text=True)
cli_result=json.loads(cli.stdout);test('cli_consumes_batch_and_rejects_lock',cli.returncode!=0 and cli_result.get('error',{}).get('code')=='REVISION_OBJECT_LOCKED')
mcp=handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'revise_deck','arguments':{'run_id':parent_id,'request':request}}})
test('mcp_consumes_same_batch_and_rejects_lock',mcp['result']['isError'] and mcp['result']['structuredContent'].get('error',{}).get('code')=='REVISION_OBJECT_LOCKED')
report={'checks':checks,'passed':all(c['passed'] for c in checks),'scope':'Synthetic regressions for proven binding defects plus real CLI/MCP negative entrances; no real model or system acceptance claimed.',
        'real_model_calls':0,'cli_result':cli_result,'mcp_result':mcp['result']['structuredContent']}
(root/'incremental-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'checks':len(checks),'passed':report['passed'],'real_model_calls':0}))
