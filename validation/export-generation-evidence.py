"""Export the verified public fixture runs, never runtime credentials/databases."""
import json
import shutil
from pathlib import Path

from yoloongppt.artifacts import sha256

ROOT=Path('/workspace'); OUT=Path('/runtime/generation-evidence')
if OUT.exists():raise RuntimeError('Evidence export already exists; choose a new explicit directory.')
OUT.mkdir()
run_ids={'original':'f40df117-e1fb-4bbf-b813-55b1ddf78603','revised':'5e5532c1-966d-4785-bd61-5031b80707a8','http-generated':'f04a6024-7c66-4920-b5ee-45c4390c6365'}
shared=['task.json','model-request.json','model-response.json','model-response-effective.json','model-call.json','deck-spec.json','execution-plan.json','execution-trace.json','object-map.json','source-result.json','pipeline-trace.json','quality-report.json','render-report.json','review-request.json','review-response.json','review-model-call.json','revision-history.json','revision-request.json','quality-before-recheck.json','checkpoint-reference-repair.json','result.json']
for kind,id in run_ids.items():
    base=Path('/runtime/runs')/id; folder=OUT/kind;folder.mkdir()
    shutil.copyfile(base/'deck.pptx',folder/'deck.pptx')
    for name in shared:
        if (base/name).is_file():shutil.copyfile(base/name,folder/name)
    shutil.copytree(base/'render',folder/'render')
# Preserve the actual detected failures and restricted reference correction.
correction=OUT/'reference-correction';correction.mkdir()
for name in ['quality-before-reference-repair.json','reference-repair-request.json','reference-repair-response.json','reference-repair-model-call.json','review-response.json','review-model-call.json','failure.json']:
    path=Path('/runtime/runs/7d5c5b35-2b00-4322-b054-0690dd265c2d')/name
    if path.is_file():shutil.copyfile(path,correction/name)
old_review=OUT/'revision-review-scope-failure';old_review.mkdir()
for name in ['quality-report.json','review-request.json','review-response.json','review-model-call.json']:
    shutil.copyfile(Path('/runtime/runs/fde2d479-966d-4ebe-9ae1-80069c2a2740')/name,old_review/name)
inventory=Path('/opt/yoloongppt-system-packages.txt').read_text(encoding='utf-8')
(OUT/'system-packages.txt').write_text(inventory,encoding='utf-8')
licenses=[]
for name in ['libreoffice-impress','libreoffice-core','poppler-utils','fonts-noto-cjk']:
    file=Path('/usr/share/doc')/name/'copyright'
    if file.is_file():
        destination=OUT/('copyright-'+name+'.txt');shutil.copyfile(file,destination)
        licenses.append({'package':name,'license_file':destination.name,'sha256':sha256(destination)})
manifest={'run_ids':run_ids,'scope':'Actual public fixture generation/revision. Full system acceptance still pending.',
          'licenses':licenses,'files':{str(p.relative_to(OUT)):sha256(p) for p in sorted(OUT.rglob('*')) if p.is_file()}}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'exported_files':len(manifest['files']),'root':str(OUT)}))
