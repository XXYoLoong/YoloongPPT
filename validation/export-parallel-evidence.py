"""Explicit manifest allowlist; never copies runtime databases or secrets."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'runtime/data';destination=ROOT/'validation/parallel-artifacts'
destination.mkdir(exist_ok=False)
entries=[]
def copy(source,target):
 output=destination/target;output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,output)
 entries.append({'path':str(output.relative_to(destination)).replace('\\','/'),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size})
for label,run_id in [('generated','5be192ef-798f-4bb0-9c93-c24bcc279aa4'),('required-missing','78bbb274-b6c9-4805-ac6f-9564b3b26270'),('nontext-initial-failure','d0cdb8d9-2ac6-4746-a6e9-fb1ac8d1a9f0'),('stale-request-initial-failure','6442afcc-0d6f-4a8b-9bee-3680a015ca77')]:
 folder=runtime/'runs'/run_id;manifest=json.loads((folder/'manifest.json').read_text('utf-8'))
 for item in manifest['artifacts']:
  relative=Path(item['path']);source=(folder/relative).resolve()
  assert source.is_relative_to(folder.resolve()) and source.suffix in {'.json','.pptx','.pdf','.png','.xhtml','.txt'}
  assert hashlib.sha256(source.read_bytes()).hexdigest()==item['hash']
  copy(source,Path(label)/relative)
 copy(folder/'manifest.json',Path(label)/'manifest.json')
for name in ['narrative-context.json','narrative-result.json','narrative-runtime.json']:
 copy(runtime/'narrative-validation'/name,Path('narrative')/name)
for name in ['parallel-integration.json','job-lifecycle.json','live-result.json']:
 copy(runtime/'parallel-validation'/name,Path('integration')/name)
(destination/'export-manifest.json').write_text(json.dumps({'artifacts':entries,'scope':'white-listed current run evidence; no DB/key/cache/log directories'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'artifacts':len(entries),'hashes_verified':True}))
