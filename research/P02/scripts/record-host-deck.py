import json,subprocess
from pathlib import Path
base=Path('/workspace/research/P02');r=json.loads((base/'validation/host-deck-review.json').read_text(encoding='utf-8'))
args=['/artifacts/main-skill/.venv/bin/python','/artifacts/main-skill/scripts/pptagent.py','--config',str(base/'config-host-review.yaml'),'record-deck-review','--workspace',str(base/'outputs/official-six'),'--verdict',r['verdict'],'--summary',r['summary'],'--issues-json',json.dumps(r['issues'])]
result=subprocess.run(args,capture_output=True,text=True,timeout=120)
report={'command':args,'returncode':result.returncode,'result':json.loads(result.stdout)}
(base/'validation/record-host-deck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert result.returncode==0
print('Recorded actual exported-deck host review through official CLI',flush=True)
