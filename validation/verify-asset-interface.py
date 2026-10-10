"""Direct changed asset/MCP interface checks; no model call."""
import hashlib,json,subprocess,sys,urllib.request
from pathlib import Path
from yoloongppt.errors import TaskError
from yoloongppt.assets import inventory
checks=[]
request={'directory':'/runtime/input-format-validation'}
req=urllib.request.Request('http://127.0.0.1:8000/inventory-assets',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
r=json.loads(urllib.request.urlopen(req,timeout=10).read());assert r['ok'] and len(r['inventory']['entries'])>0
checks.append({'name':'HTTP actual inventory','passed':True})
try:inventory('/runtime/secrets');raise AssertionError('sensitive directory accepted')
except TaskError as error:assert error.code=='ASSET_DIRECTORY_INVALID'
checks.append({'name':'sensitive directory rejected','passed':True})
messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'inventory_assets','arguments':request}}]
p=subprocess.run([sys.executable,'-m','yoloongppt','mcp-serve'],input=''.join(json.dumps(x)+'\n' for x in messages),text=True,capture_output=True,timeout=15)
response=json.loads(p.stdout.splitlines()[-1]);assert response['result']['structuredContent']['ok']
checks.append({'name':'MCP actual inventory','passed':True})
cap=json.loads(urllib.request.urlopen('http://127.0.0.1:8000/capabilities').read());assert len(cap['native_objects']['requirements'])==30
checks.append({'name':'HTTP capability partial boundaries','passed':True})
report={'passed':True,'checks':checks,'fresh_model_calls':0,'source_hashes':{str(x.relative_to('/workspace')):hashlib.sha256(x.read_bytes()).hexdigest() for x in Path('/workspace/src/yoloongppt').glob('*.py')}}
Path('/runtime/parallel-validation/post-integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'passed':True,'checks':len(checks),'fresh_model_calls':0}))
