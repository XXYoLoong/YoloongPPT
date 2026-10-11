"""Export explicit delivery evidence from the F-backed runtime, preserving bytes."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'runtime/data'
OUT=ROOT/'validation/native-capacity-live-artifacts'
parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
files=[]
def copy(source,target):
    raw=source.read_bytes()
    # Never publish actual configured credentials, including inside model records.
    secret=(RUNTIME/'secrets/deepseek_api_key').read_bytes().strip()
    assert not secret or secret not in raw,('credential detected',str(source))
    destination=OUT/target
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():assert destination.read_bytes()==raw,('evidence would be overwritten',str(destination))
    else:shutil.copyfile(source,destination)
    files.append({'source':str(source.relative_to(ROOT)).replace('\\','/'),
                  'path':str(destination.relative_to(ROOT)).replace('\\','/'),
                  'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})

for label,run in [('language-conflict','32ee63b0-832f-4054-ab3e-19721f1eada7'),
                  ('resource-identity-missing','5bd522b9-c1af-4008-be10-98957da53cdc'),
                  ('pagination-title-p0','ad03ceec-a393-48a3-840e-4e2f52c50613'),
                  ('current-resumed',args.run_id)]:
    folder=RUNTIME/'runs'/run
    assert folder.is_dir(),run
    for path in sorted(folder.glob('*.json')):copy(path,Path(label)/path.name)
    if (folder/'deck.pptx').exists():copy(folder/'deck.pptx',Path(label)/'deck.pptx')
    for path in sorted((folder/'render').glob('*')):
        if path.is_file() and path.suffix in {'.png','.pdf','.txt','.xhtml'}:copy(path,Path(label)/'render'/path.name)
fixture=RUNTIME/'capacity-live-validation/61500308-5afc-4f3d-ad4f-54c70c4e7fe9'
for path in sorted(fixture.glob('*')):
    if path.name in {'task.json','expected.json','submitted.json','live-result.json'} or path.name.startswith('fixture-image-'):
        copy(path,Path('artificial-inputs')/path.name)
for folder in sorted((RUNTIME/'capacity-live-validation').iterdir()):
    if (folder/'live-result.json').is_file():
        result=json.loads((folder/'live-result.json').read_text('utf-8')).get('result',{})
        if result.get('run_id')==args.run_id:
            for name in ['checks.json','summary.json','submitted.json','live-result.json','fixture-reference.json']:
                if (folder/name).is_file():copy(folder/name,Path('current-driver')/name)
for path in sorted((RUNTIME/'capacity-context-validation').glob('*.json')):copy(path,Path('context-increment')/path.name)
for path in sorted((RUNTIME/'adaptive-content-validation/20261011-105104').glob('*.json')):
    name=path.name.replace(':','-').replace('\uf03a','-')
    copy(path,Path('pagination-increment')/name)
for path in sorted((ROOT/'src/yoloongppt').glob('*.py')):copy(path,Path('current-source')/path.name)
for path in sorted((ROOT/'contracts').glob('*.json')):copy(path,Path('current-contracts')/path.name)
report={'current_run_id':args.run_id,'system_acceptance':'not_passed',
        'scope':'Versioned component evidence stays separate; current resumed artifacts include new execution and review, reused real fact/content seed. Prior failures retained.',
        'files':files}
(OUT/'export-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'files':len(files),'current_run':args.run_id,'bytes':sum(f['bytes'] for f in files)}))
