"""Run one official CLI phase; redact key if any subprocess unexpectedly echoes it."""
import json,os,subprocess,sys,time
from pathlib import Path
base=Path('/workspace/research/P02');workspace=base/'outputs/official-six'
phase=sys.argv[1]
label=sys.argv[2] if len(sys.argv)>2 else phase
host=len(sys.argv)>3 and sys.argv[3]=='host'
config=base/('config-host-review.yaml' if host else 'config-deepseek.yaml')
args=['/artifacts/main-skill/.venv/bin/python','/artifacts/main-skill/scripts/pptagent.py','--config',str(config),phase,'--workspace',str(workspace)]
if phase=='init':args+=['--slides','6','--language','zh','--aspect-ratio','16:9']
if len(sys.argv)>2 and not host:args=['/artifacts/main-skill/.venv/bin/python',str(base/'scripts/trace-official-cli.py'),phase,label]
print(json.dumps({'phase':phase,'state':'started'}),flush=True)
start=time.time()
try:
 result=subprocess.run(args,cwd='/artifacts/main-skill',capture_output=True,text=True,timeout=1200)
 key=os.environ.get('DEEPSEEK_API_KEY','')
 stdout=result.stdout.replace(key,'[REDACTED]') if key else result.stdout
 stderr=result.stderr.replace(key,'[REDACTED]') if key else result.stderr
 (base/'validation'/f'official-six-{label}.txt').write_text(stdout+'\nSTDERR:\n'+stderr,encoding='utf-8')
 report={'phase':phase,'command':args,'returncode':result.returncode,'elapsed_seconds':round(time.time()-start,2),'log':f'validation/official-six-{label}.txt'}
 try:report['result']=json.loads(stdout)
 except json.JSONDecodeError:report['result_json']=False
except Exception as e:report={'phase':phase,'error_type':type(e).__name__,'elapsed_seconds':round(time.time()-start,2)}
(base/'validation'/f'official-six-{label}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
if report.get('returncode')!=0:sys.exit(1)
