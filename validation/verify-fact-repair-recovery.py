"""DEC-004/005 and SYS-005: saved real responses and actual recovery failures."""
import copy
import json
import shutil
from pathlib import Path
from uuid import uuid4

from yoloongppt.artifacts import RunArtifacts
from yoloongppt.errors import TaskError, trace_id
from yoloongppt.facts import validate_grounding_repair
from yoloongppt.operations import dispatch
from yoloongppt.schemas import SchemaRegistry

OUT=Path('/runtime/fact-repair-recovery')/uuid4().hex
OUT.mkdir(parents=True)
schemas=SchemaRegistry();checks=[]
fixture=Path('/runtime/runs/07e17513-f114-4120-902f-7d07a526a657')
evidence=json.loads((fixture/'fact-source-result.json').read_text('utf-8'))['evidence']
response=json.loads((fixture/'fact-interpretation.json').read_text('utf-8'))
before=response['claims'][0]
validate_grounding_repair(before,copy.deepcopy(before),evidence,response['coverage'],schemas)
checks.append({'check':'Unchanged real source-grounded claim remains valid','passed':True})
changed=copy.deepcopy(before)
other=next(e for e in evidence if e['raw_text']=='B楼本期用电量为100千瓦时。')
changed['quotes']=[{'evidence_id':other['evidence_id'],'quote':other['raw_text']}]
try:validate_grounding_repair(before,changed,evidence,response['coverage'],schemas)
except TaskError as exc:
    assert exc.code=='FACT_GROUNDING_REPAIR_SOURCE_CHANGED',exc.code
    checks.append({'check':'Same numeric literal from another actual source is rejected','passed':True,'code':exc.code})
else:raise AssertionError('Source substitution accepted')
same_document=copy.deepcopy(evidence)
original_source=next(e['source_id'] for e in evidence if e['evidence_id']==before['quotes'][0]['evidence_id'])
next(e for e in same_document if e['evidence_id']==other['evidence_id'])['source_id']=original_source
try:validate_grounding_repair(before,changed,same_document,response['coverage'],schemas)
except TaskError as exc:
    assert exc.code=='FACT_GROUNDING_REPAIR_QUOTE_DROPPED',exc.code
    checks.append({'check':'Changing subject within same document cannot discard original valid quote','passed':True,'code':exc.code,
                   'fixture':'Two saved actual literals put into one artificial document; model responses unchanged'})
else:raise AssertionError('Original subject quote discarded')
for field in ['unit','period','numeric_value']:
    altered=copy.deepcopy(before);altered['value'][field]=None
    try:validate_grounding_repair(before,altered,evidence,response['coverage'],schemas)
    except TaskError as exc:
        expected='FACT_GROUNDING_REPAIR_VALUE_CHANGED' if field=='numeric_value' else 'FACT_GROUNDING_REPAIR_SCOPE_CHANGED'
        assert exc.code==expected,(field,exc.code)
        checks.append({'check':'Already supported '+field+' cannot be cleared','passed':True,'code':exc.code})
    else:raise AssertionError(field+' was cleared')

original=Path('/runtime/runs/3f6fe040-dae7-4e17-92d7-c0184de48978')
saved_evidence=json.loads((original/'fact-source-result.json').read_text('utf-8'))['evidence']
saved_before=json.loads((original/'fact-model-response.json').read_text('utf-8'))
saved_repairs=json.loads((original/'fact-grounding-repair-response.json').read_text('utf-8'))['repairs']
for item in saved_repairs:
    validate_grounding_repair(saved_before['claims'][item['claim_index']],item['claim'],saved_evidence,saved_before['coverage'],schemas)
checks.append({'check':'Saved real XLSX grounding repairs remain valid under preservation guards','passed':True,'repairs':len(saved_repairs)})
for case,filename,code in [
    ('missing-grounding-response','fact-grounding-repair-response.json','FACT_CHECKPOINT_INCOMPLETE'),
    ('changed-grounding-response','fact-grounding-repair-response.json','FACT_CHECKPOINT_CHANGED'),
    ('changed-effective-response','fact-model-effective.json','FACT_CHECKPOINT_CHANGED'),
]:
    duplicate=RunArtifacts()
    shutil.copytree(original,duplicate.path,dirs_exist_ok=True)
    path=duplicate.path/filename
    if case.startswith('missing'):path.unlink()
    else:path.write_bytes(path.read_bytes()+b'\n')
    try:dispatch('resume',{'run_id':duplicate.run_id},trace_id(),schemas=schemas)
    except TaskError as exc:
        assert exc.code==code,(case,exc.code)
        run_id=next(d['run_id'] for d in exc.details if 'run_id' in d)
        run=Path('/runtime/runs')/run_id
        steps=json.loads((run/'pipeline-trace.json').read_text('utf-8'))['steps']
        assert not any('FactInterpreter' in step['component'] for step in steps)
        assert not (run/'model-call.json').exists() and not (run/'review-call.json').exists()
        (OUT/(case+'.json')).write_text(json.dumps(exc.result('fact-repair-recovery'),ensure_ascii=False,indent=2),'utf-8')
        checks.append({'check':case,'passed':True,'code':code,'failed_run':run_id,'fresh_model_calls':0})
    else:raise AssertionError(case+' accepted')
summary={'checks':checks,'passed':len(checks),'fresh_model_calls':0,
         'sources':[str(fixture),str(original)],'scope':'Actual saved real response guard and resume failure injection; not full system AC.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'passed':len(checks),'summary':str(OUT/'summary.json')},ensure_ascii=False))
