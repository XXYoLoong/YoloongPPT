import json,subprocess
from pathlib import Path
base=Path('/workspace/research/P02');data=json.loads((base/'validation/host-slide-review.json').read_text(encoding='utf-8'))
results=[]
for r in data['reviews']:
 args=['/artifacts/main-skill/.venv/bin/python','/artifacts/main-skill/scripts/pptagent.py','--config',str(base/'config-host-review.yaml'),'record-slide-review','--workspace',str(base/'outputs/official-six'),'--slide',f"slides/slide{r['slide']:02}.html",'--verdict',r['verdict'],'--summary',r['summary'],'--issues-json',json.dumps(r['issues'])]
 result=subprocess.run(args,capture_output=True,text=True,timeout=120)
 results.append({'slide':r['slide'],'command':args,'returncode':result.returncode,'result':json.loads(result.stdout)})
 assert result.returncode==0
(base/'validation/record-host-slides.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded six actual host slide reviews through official CLI',flush=True)
