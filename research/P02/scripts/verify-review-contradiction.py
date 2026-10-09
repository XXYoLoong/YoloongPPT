"""Correct and rerun only the assertion with a complete issue schema."""
import json,sys
from pathlib import Path
sys.path.insert(0,'/artifacts/main-skill/scripts')
from pptagent_runtime.visual import validate_review
path=Path('/workspace/research/P02/validation/maps-probes.json')
report=json.loads(path.read_text())
item=next(c for c in report['cases'] if c['id']=='review-contradiction')
try:
 validate_review({'verdict':'pass','summary':'contradictory verdict','issues':[{'severity':'major','slide':1,'description':'test','suggested_fix':'test'}]})
 raise AssertionError('pass+major accepted')
except ValueError as error:
 assert 'cannot pass' in str(error),str(error)
 item.update(message=str(error),probe_correction='first harness omitted suggested_fix; only corrected validator assertion rerun')
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(item,ensure_ascii=False))
