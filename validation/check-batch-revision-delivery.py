"""Check fixed evidence integrity and selected maintained files without rerunning AI."""
import ast,hashlib,json,pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
folder=ROOT/'validation/batch-revision-artifacts'
manifest=json.loads((folder/'evidence-manifest.json').read_text('utf-8'))
for entry in manifest['files']:
    raw=(folder/entry['path']).read_bytes()
    assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],entry['path']
python_files=['src/yoloongppt/batch_revision.py','src/yoloongppt/revision_scope.py','src/yoloongppt/revision.py','src/yoloongppt/existing_deck.py',
 'validation/verify-batch-revision.py','validation/verify-batch-revision-incremental.py','validation/verify-revision-scope.py',
 'validation/verify-revision-native.py','validation/export-batch-revision-evidence.py','validation/check-batch-revision-matrix.py']
for file in python_files:ast.parse((ROOT/file).read_text('utf-8'),filename=file)
json.loads((ROOT/'contracts/revision-batch-request.schema.json').read_text('utf-8'))
matrix=json.loads((ROOT/'validation/batch-revision-matrix-update.json').read_text('utf-8'))
assert sum(matrix['requirements'].values())==308 and sum(matrix['tasks'].values())==453
assert matrix['requirements']['已完成']==35 and matrix['tasks']['已完成']==61
assert matrix['original_ids_and_completed_rows_preserved'] and matrix['unrelated_values_and_formulas_preserved']
report={'evidence_files':len(manifest['files']),'file_hashes_and_sizes_verified':True,'python_files_parsed':len(python_files),
        'schema_json_parsed':True,'matrix_changed_cells':len(matrix['changed_cells']),'model_calls':0,'render_calls':0,
        'system_acceptance':'not_passed','scope':'Delivery integrity/syntax only; not a rerun of component/API/Office acceptance.'}
(ROOT/'validation/batch-revision-delivery-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(report,ensure_ascii=False))
