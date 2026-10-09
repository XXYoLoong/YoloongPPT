"""Minimal source revision for observed converter margin rejection."""
import hashlib,json,shutil
from pathlib import Path
root=Path('/workspace/research/P02');workspace=root/'outputs/official-six';history=root/'outputs/source-v1'
history.mkdir(exist_ok=True)
shutil.copytree(workspace/'qa/slides',history/'qa-slides')
shutil.copyfile(workspace/'workspace-state.json',history/'workspace-state.json')
changes=[]
for p in sorted((workspace/'slides').glob('*.html')):
 before=p.read_bytes();text=before.decode('utf-8');assert text.count('top:660px')==1
 text=text.replace('top:660px','top:620px');p.write_text(text,encoding='utf-8')
 changes.append({'path':str(p.relative_to(root)),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'change':'footer top 660px ->620px; content unchanged'})
report={'reason':'official converter rejects footer at0.40in bottom margin; requires0.5in','evidence':'validation/official-six-build-host.json','change_type':'research example HTML revision, no upstream library/validator edit','changes':changes,'next_required':'fresh render and host review before rebuild; old review state not forged'}
(root/'validation/footer-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Moved six footers; original renders/state preserved',flush=True)
