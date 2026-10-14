"""Revalidate the prior real DOCX response and reject invented dates."""
import copy,json
from pathlib import Path
from uuid import uuid4
from yoloongppt.facts import validate_interpretation
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.errors import TaskError

source=Path('/runtime/runs/38e8220f-25a9-4ec2-abb7-daf63b13135e')
out=Path('/runtime/fact-citation-validation')/uuid4().hex;out.mkdir(parents=True)
load=lambda name:json.loads((source/name).read_text('utf-8'))
evidence=load('fact-source-result.json')['evidence'];result=load('fact-model-response.json')
schemas=SchemaRegistry();checks=[]
grounded=validate_interpretation(evidence,result,schemas)
checks.append({'case':'original-real-response-exact-citation-year','passed':True,'grounded_claims':len(grounded)})
index=next(i for i,c in enumerate(result['claims']) if c['fact_kind']=='citation' and c['value']['date_value']=='2026')
for case,value,precision in [('invented-year','2025','year'),('invented-month-day','2026-01-01','day')]:
    changed=copy.deepcopy(result);changed['claims'][index]['value'].update(date_value=value,date_precision=precision)
    try:validate_interpretation(evidence,changed,schemas)
    except TaskError as exc:
        assert exc.code=='FACT_DATE_TRANSFORM_UNAUTHORIZED',(case,exc.code)
        checks.append({'case':case,'passed':True,'error':exc.code})
    else:raise AssertionError(case)
(out/'checks.json').write_text(json.dumps({'checks':checks,'source_run':source.name,'fresh_model_calls':0,'scope':'Exact citation year only; semantic/full-source acceptance separately required.'},ensure_ascii=False,indent=2))
print(json.dumps({'passed':len(checks),'evidence':str(out)}))
