"""Audit the current staged delivery, not a repeat of product test suites."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(path.read_text('utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='yoloongdevlop'
manifests=[ROOT/'validation/template-slot-artifacts/export-manifest.json',
           ROOT/'validation/gallery-artifacts/b81e5a47-0d59-4963-87a5-daa257d654ef/export-manifest.json',
           ROOT/'validation/gallery-artifacts/long-title-ae033e62/export-manifest.json',
           ROOT/'validation/adaptive-content-artifacts/export-manifest.json',
           ROOT/'validation/native-capacity-live-artifacts/export-manifest.json']
payload_count=0
for manifest_path in manifests:
    for item in read(manifest_path)['files']:
        name=item['path'].replace('\\','/')
        target=ROOT/name if name.startswith('validation/') else manifest_path.parent/name
        assert digest(target)==item['sha256'] and target.stat().st_size==item['bytes'],str(target)
        payload_count+=1
current=ROOT/'validation/native-capacity-live-artifacts/current-resumed'
version=read(current/'version-manifest.json')
for name,expected in version['source_hashes'].items():assert digest(ROOT/name)==expected,name
for name,expected in version['schemas'].items():assert digest(ROOT/'contracts'/name)==expected,name
matrix=read(ROOT/'validation/native-capacity-matrix-update.json')
assert matrix['requirements']['已完成']==35 and matrix['tasks']['已完成']==61
assert matrix['original_ids_and_completed_rows_preserved'] and matrix['worksheet_features_preserved']
assert matrix['unrelated_values_and_formulas_preserved']
report=read(ROOT/'validation/native-capacity-integration.json')
assert report['system_acceptance']=='not_passed' and report['fresh_api']['p0_issue_count']==0
assert report['fresh_api']['warning_issue_count']==5 and not report['fresh_api']['completion']['final_allowed']
assert all(item['system_acceptance']=='not_passed' for item in report['acceptance'].values())
secret=(ROOT/'runtime/data/secrets/deepseek_api_key').read_bytes().strip()
staged=[p.decode('utf-8') for p in subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0') if p]
for name in staged:
    path=ROOT/name
    assert not name.startswith('runtime/data/') and Path(name).name not in {'.env','deepseek_api_key'}
    if path.is_file():assert not secret or secret not in path.read_bytes(),('credential found',name)
logs=[name for name in staged if name.startswith('ailog/') and '接通模板多图与自适应分页_' in name]
assert len(logs)==1
other=ROOT/'development-log'/Path(logs[0]).name
assert (ROOT/logs[0]).read_bytes()==other.read_bytes()
summary={'staged_files_scanned':len(staged),'actual_credential_detected':False,
         'whitelist_payload_hashes_verified':payload_count,'current_product_source_files':len(version['source_hashes']),
         'current_schema_versions':len(version['schemas']),'original_matrix_structure_and_scope_preserved':True,
         'twin_log':Path(logs[0]).name,'current_real_run':report['fresh_api']['current_resumed_run'],
         'p0':0,'warnings':5,'system_acceptance':'not_passed',
         'scope':'Delivery byte/hash/index audit; historical product suites not rerun.'}
(ROOT/'validation/native-capacity-delivery.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(summary,ensure_ascii=False))
