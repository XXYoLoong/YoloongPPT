"""SEC-001/PPT-015: real native guard, private-directory fixture and safe links."""
import base64,json
from pathlib import Path
from uuid import uuid4
from PIL import Image
from yoloongppt.upstream_native import canvas_guard
from yoloongppt.errors import TaskError

root=Path('/runtime/svg-source-security')/uuid4().hex;root.mkdir(parents=True)
(root/'secrets').mkdir();Image.new('RGB',(4,4),'white').save(root/'secrets/artificial-test-only.png')
checks=[]
def verify(name,body,expected=None):
    path=root/(name+'.svg');path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'+body+'</svg>')
    try:canvas_guard(path)
    except TaskError as exc:
        assert exc.code==expected,(name,exc.code)
        checks.append({'case':name,'passed':True,'error':exc.code})
    else:
        assert expected is None,name
        checks.append({'case':name,'passed':True})
verify('private-nested-image','<image href="secrets/artificial-test-only.png"/>','NATIVE_ASSET_PATH_FORBIDDEN')
verify('script-link','<a href="javascript:alert(1)"><text>x</text></a>','SVG_LINK_UNSAFE')
verify('credential-link','<a href="https://u:p@example.com/"><text>x</text></a>','SVG_LINK_UNSAFE')
verify('file-link','<a href="file:///runtime/private"><text>x</text></a>','SVG_LINK_UNSAFE')
encoded=base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>').decode()
verify('inline-active-document','<image href="data:image/svg+xml;base64,'+encoded+'"/>','SVG_INLINE_ASSET_UNSUPPORTED')
verify('safe-public-link','<a href="https://example.com/"><text>x</text></a>')
(root/'checks.json').write_text(json.dumps({'checks':checks,'passed':True,'fixture':'Artificial test PNG in private-named folder; no real secrets accessed.','scope':'Native SVG source boundary; full security/objects acceptance not claimed.'},indent=2))
print(json.dumps({'passed':len(checks),'evidence':str(root)}))
