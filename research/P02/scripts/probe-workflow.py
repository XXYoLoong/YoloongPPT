"""Bounded real CLI failure probes; no synthetic acceptance evidence."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path('/workspace/research/P02');out=root/'outputs/workflow-probes';out.mkdir(parents=True,exist_ok=True)
python='/artifacts/main-skill/.venv/bin/python';cli='/artifacts/main-skill/scripts/pptagent.py';config=root/'config-deepseek.yaml'
cases=[]
def run(name,command,expected):
 r=subprocess.run([python,cli,'--config',str(config),*command],text=True,capture_output=True,timeout=120)
 key=os.environ.get('DEEPSEEK_API_KEY','');text=r.stdout+'\nSTDERR:\n'+r.stderr
 if key:text=text.replace(key,'[REDACTED]')
 (root/'validation'/('workflow-'+name+'.txt')).write_text(text,encoding='utf-8')
 assert r.returncode==expected,(name,r.returncode)
 try:response=json.loads(r.stdout)
 except json.JSONDecodeError:response=None
 cases.append({'case':name,'arguments':command,'returncode':r.returncode,'result':response,'log':'validation/workflow-'+name+'.txt'})
run('reject-zero',['init','--workspace',str(out/'zero'),'--slides','0'],2)
run('init-one',['init','--workspace',str(out/'one'),'--slides','1','--language','zh','--aspect-ratio','16:9'],0)
(out/'one/slides').mkdir(exist_ok=True)
(out/'one/slides/slide01.html').write_bytes((root/'outputs/official-six/slides/slide01.html').read_bytes())
run('build-unreviewed',['build','--workspace',str(out/'one')],2)
run('finalize-incomplete',['finalize','--workspace',str(out/'one')],1)
run('init-existing',['init','--workspace',str(out/'one'),'--slides','1'],2)
report={'requirement_id':'RES-P02-01','scope':'expected real CLI failures; no model calls or forged workspace-state/review records','cases':cases,'credential_values_persisted':False}
(root/'validation/workflow-probes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
from importlib.metadata import version
from deeppresenter.utils.webview import SCRIPT_PATH
import deeppresenter.utils.webview as module
paths=[Path(SCRIPT_PATH),Path(module.__file__)]
info={'installed_pptagent_version':version('pptagent'),'python':sys.version.split()[0],'node_converter':str(SCRIPT_PATH),'source_files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],'scope':'resolved requirement dependency, not a change to fixed main/source tag or product runtime choice'}
(root/'validation/converter-source.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True);print(json.dumps(info,ensure_ascii=False),flush=True)
