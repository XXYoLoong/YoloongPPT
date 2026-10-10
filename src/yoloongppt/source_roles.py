"""DEC-003: retain all sources, select roles and isolate factual model input."""
import hashlib
import time
from pathlib import Path

from .artifacts import entity, RunArtifacts
from .tasks import validate_task

ROLES={'fact','template','style','asset','existing_deck','reconstruction'}
CANONICAL={'content':'fact','style_reference':'style','material':'fact','image_asset':'asset',**{r:r for r in ROLES}}


def assign(document,schemas,trace):
    begin=time.monotonic();schemas.validate('source-role-map.schema.json',document)
    task=document['task'];bundle=document['source_bundle'];validate_task(task,schemas,trace)
    sources=bundle['bundle']['sources'];known={s['source_id']:s for s in sources};original={s['source_id']:s for s in task['sources']}
    issues=[];candidates=[];entries=[];selected=[]
    if set(known)!=set(original):issues.append({'code':'SOURCE_BUNDLE_ID_MISMATCH','reason':'TaskSpec and loaded source identities must match; no source dropped.'})
    if len(known)!=len(sources):issues.append({'code':'SOURCE_ID_DUPLICATE'})
    raw=task.get('raw_request',{});bindings=raw.get('attachment_roles',[])
    assets={a for s in sources for a in s['raw_asset_refs']}
    for binding in bindings:
        if binding['asset_id'] not in assets:issues.append({'code':'ATTACHMENT_SOURCE_UNRESOLVED','asset_id':binding['asset_id'],'reason':'Declared attachment must map to actual loaded source asset identity.'})
    for source in sources:
        id=source['source_id'];spec=original.get(id,{})
        signals=[]
        if 'source_role' in spec.get('metadata',{}):
            value=spec['metadata']['source_role'];signals.extend([(r,'TaskSpec.sources.metadata.source_role') for r in (value if isinstance(value,list) else [value])])
        signals.extend((b['role'],'raw_request.attachment_roles:'+b['asset_id']) for b in bindings if b['asset_id'] in source['raw_asset_refs'])
        if not signals:
            if task['route']['mode'] in {'create_from_materials','create_from_scratch'} and spec.get('kind') in {'prompt','text','markdown','docx','pdf','xlsx','csv','url','web'}:signals=[('fact','explicit content-source input for current route')]
            else:signals=[(None,'No explicit source role; source format alone does not authorize facts/style/template.')]
        normalized=[];refs=[]
        for role,ref in signals:
            canonical=CANONICAL.get(role) if isinstance(role,str) else None
            if canonical not in normalized:normalized.append(canonical)
            candidate={'node_id':'DEC-003','candidate_id':entity('candidate'),'value':{'source_id':id,'role':canonical,'original_role':role},'score':1.0 if 'metadata' in ref or 'attachment_roles' in ref else 0.7,
                       'reasons':[{'basis':ref}],'evidence_refs':[id,*source['raw_asset_refs']], 'constraints':[{'preserve_source':True,'exclude_nonfact_from_content_model':True}]}
            candidates.append(candidate);refs.append(candidate['candidate_id'])
        conflict=len(normalized)!=1 or normalized[0] is None
        if conflict:issues.append({'code':'SOURCE_ROLE_UNRESOLVED','source_id':id,'candidate_roles':normalized})
        else:selected.extend(refs)
        entries.append({'source_id':id,'asset_refs':source['raw_asset_refs'],'role':None if conflict else normalized[0],
                        'candidate_refs':refs,'loading_strategy':{'kind':spec.get('kind'),'locator':source['locator'],'fact_input':not conflict and normalized[0]=='fact'},
                        'reason':'Conflicting or unknown roles require clarification.' if conflict else 'Explicit role or bounded content-source default; original input retained.'})
    output={'status':'needs_clarification' if issues else 'assigned','source_roles':entries,'fact_source_ids':[e['source_id'] for e in entries if e['role']=='fact'],
            'preserved_source_ids':[s['source_id'] for s in sources], 'issues':issues,'trace_id':trace,
            'fallback':'No guessing unknown roles or treating style/template/assets as factual evidence; preserve sources and clarify.'}
    schemas.validate('source-role-map.schema.json',output)
    decision={'trace_id':trace,'node_id':'DEC-003','input':document,'candidates':candidates,'selected':selected,
              'rules':{'version':'DEC-003-1','mechanism':'Explicit source metadata and loaded asset bindings; unique role required; bounded textual-source default for material/scratch route.', 'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              'output':output,'duration':round(time.monotonic()-begin,6),'error':{'code':'SOURCE_ROLES_UNRESOLVED','issues':issues} if issues else None}
    schemas.validate('decision-trace.schema.json',decision)
    return {'ok':True,'trace_id':trace,'operation':'assign_source_roles','source_role_map':output,'decision_trace':decision}


def fact_input(sources,role_map):
    ids=set(role_map['fact_source_ids'])
    # Empty OOXML paragraphs and image-only records are physical structure, not
    # ambiguous text. Keep their original evidence/bytes explicitly as assets;
    # do not ask the text fact model to invent OCR or interpret blank content.
    structural=[e for e in sources['evidence'] if e['source_id'] in ids and e['raw_text']=='']
    return {**sources,'evidence':[e for e in sources['evidence'] if e['source_id'] in ids and e['raw_text']!=''],
            'nontext_evidence':structural,
            'documents':[d for d in sources['documents'] if d['source_id'] in ids],
            'selection':{'producer':'DEC-003','fact_source_ids':role_map['fact_source_ids'],'all_sources_preserved_in':'source-result.json',
                         'nontext_evidence_ids':[e['evidence_id'] for e in structural],
                         'nontext_handling':'Original evidence retained in nontext_evidence; empty structure carries no textual fact; OCR/visual fact inference not executed.'}}


def run_roles(document,schemas,trace):
    result=assign(document,schemas,trace);artifacts=RunArtifacts()
    artifacts.json('decision-source-roles.json',result['decision_trace']);artifacts.json('source-role-map.json',result['source_role_map'])
    result.update(run_id=artifacts.run_id,artifact_root=str(artifacts.path));artifacts.json('result.json',result)
    artifacts.json('manifest.json',{'run_id':artifacts.run_id,'artifacts':artifacts.manifest()});return result
