"""Audit the current package's staged files and independently exported evidence."""
import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
assert ROOT.drive.upper()=='F:' and Path(os.environ['TEMP']).drive.upper()=='F:'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
assert git('branch','--show-current').decode().strip()=='yoloongdevlop'
assert git('rev-parse','--abbrev-ref','--symbolic-full-name','@{upstream}').decode().strip()=='origin/yoloongdevlop'
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
source_count=0
for file in (ROOT/'src/yoloongppt').glob('*.py'):
    ast.parse(file.read_text('utf-8'),filename=str(file));source_count+=1
schema_count=0
for file in (ROOT/'contracts').glob('*.json'):
    json.loads(file.read_text('utf-8'));schema_count+=1

manifests=[]
for name in ['visual-live-artifacts','visual-execution-artifacts','revision-plan-artifacts']:
    path=ROOT/'validation'/name/('manifest.json' if name=='visual-execution-artifacts' else 'export-manifest.json')
    manifest=json.loads(path.read_text('utf-8'))
    entries=manifest.get('artifacts',manifest.get('files',[]))
    assert entries, name
    for item in entries:
        file=path.parent/item['path']
        assert file.resolve().is_relative_to(path.parent.resolve())
        expected=item.get('sha256',item.get('hash'))
        assert expected and hashlib.sha256(file.read_bytes()).hexdigest()==expected,(name,item['path'])
    if 'current_source_contract_hashes' in manifest:
        for relative,expected in manifest['current_source_contract_hashes'].items():
            assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected,relative
    manifests.append({'name':name,'verified_files':len(entries)})

files=git('diff','--cached','--name-only','-z','--diff-filter=ACM').decode('utf-8').split('\0')
files=[name for name in files if name]
keyfile=ROOT/'runtime/data/secrets/deepseek_api_key'
key=keyfile.read_bytes().strip() if keyfile.is_file() else b''
scanned=0
for name in files:
    assert not any(part.lower() in {'secrets','.ssh','.git'} for part in Path(name).parts)
    assert not Path(name).name.lower().startswith('.env')
    raw=git('show',':'+name)
    assert not key or key not in raw,'Configured credential found in staged file'
    assert not re.search(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9_-]{20,}',raw),'Credential pattern found in staged file'
    scanned+=1
logs=[n for n in files if n.startswith('ailog/')]
assert len(logs)==1
log=Path(logs[0]);twin=ROOT/'development-log'/log.name
assert re.fullmatch(r'[\u4e00-\u9fffA-Za-z0-9与及]+_\d{8}-\d{6}\.md',log.name)
assert (ROOT/log).read_bytes()==twin.read_bytes()
matrix=json.loads((ROOT/'validation/visual-matrix-update.json').read_text('utf-8'))
assert matrix['requirements']['已完成']==35 and matrix['tasks']['已完成']==61
assert matrix['worksheets']==20 and matrix['AC'].get('已通过',0)==0
report={'passed':True,'branch':'yoloongdevlop','upstream':'origin/yoloongdevlop',
        'syntax_checked_sources':source_count,'parsed_contract_documents':schema_count,
        'export_manifests':manifests,'staged_files_scanned':scanned,'twin_logs_equal':True,
        'matrix_scope_preserved':True,'requirements':matrix['requirements'],'tasks':matrix['tasks'],
        'scope':'Syntax, manifest hashes, immutable baseline cells, staged credential boundaries and paired logs only; no full system acceptance',
        'system_acceptance':'not_passed'}
out=ROOT/'validation/visual-delivery-audit.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(report,ensure_ascii=False))
