"""Bounded research probes; no model, fake reviews, or upstream patch."""
import asyncio, hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as E
sys.path.insert(0,'/artifacts/main-skill/scripts')
from pptagent_runtime import core
from pptagent_runtime.config import node_environment
from pptagent_runtime.visual import validate_review
base=Path('/workspace/research/P02'); out=base/'outputs/maps-probes'
out.mkdir(exist_ok=True)
assert not (base/'validation/maps-probes.json').exists(), 'completed report cannot be overwritten'
def dump(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
css='html,body{width:1280px;height:720px;margin:0;overflow:hidden}*{box-sizing:border-box}body{font-family:Arial,sans-serif;background:#f4f1ea;color:#182231}h1{position:absolute;left:64px;top:35px;font-size:40px;margin:0}p{font-size:22px;margin:0}'
(out/'native-table.html').write_text('<html><head><style>'+css+'table{position:absolute;left:64px;top:145px;width:680px;height:220px;border-collapse:collapse;font-size:24px}td,th{border:2px solid #182231;padding:12px}th{background:#ded5c3}.box{position:absolute;left:810px;top:145px;width:380px;height:280px;background:#e2e8ed;padding:24px}li{font-size:24px}</style></head><body><h1>原生表格与文字</h1><table><tr><th>对象</th><th>检查</th></tr><tr><td>文字</td><td>可编辑</td></tr><tr><td>表格</td><td>原生单元格</td></tr></table><div class="box"><p>结构边界</p><ul><li>表格</li><li>矩形与列表</li></ul></div></body></html>',encoding='utf-8')
(out/'svg-failure.html').write_text('<html><head><style>'+css+'</style></head><body><h1>内联 SVG 失败探测</h1><svg xmlns="http://www.w3.org/2000/svg" width="300" height="240"><circle cx="120" cy="120" r="90" fill="#236a8a"/></svg></body></html>',encoding='utf-8')
(out/'raster-slot.html').write_text('<html><head><style>'+css+'.gradient{position:absolute;left:64px;top:160px;width:480px;height:240px;background:linear-gradient(120deg,#236a8a,#e9be65)}.placeholder{position:absolute;left:640px;top:460px;width:520px;height:130px}</style></head><body><h1>渐变与坐标占位</h1><div class="gradient"></div><div class="placeholder" id="chart-slot"></div></body></html>',encoding='utf-8')
report={'scope':'main Skill + installed pptagent1.1.37; research only','cases':[]}
if not (out/'objects.pptx').exists():
 run=subprocess.run(['node',str(base/'scripts/probe-maps.js')],env=node_environment(),capture_output=True,text=True,timeout=300)
 (base/'validation/maps-converter.txt').write_text(run.stdout+'\nSTDERR:\n'+run.stderr,encoding='utf-8')
 assert run.returncode==0,run.stderr
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
objects=[]
with zipfile.ZipFile(out/'objects.pptx') as z:
 for i in (1,2):
  slide=E.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
  item={'slide':i,'text_shapes':len(slide.findall('.//p:sp',ns)),'pictures':len(slide.findall('.//p:pic',ns)),'native_tables':len(slide.findall('.//a:tbl',ns)),'charts':len(slide.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/chart}chart')),'native_placeholders':len(slide.findall('.//p:ph',ns)),'text': [x.text for x in slide.findall('.//a:t',ns)]}
  objects.append(item)
 assert objects[0]['native_tables']==1 and '原生单元格' in objects[0]['text'],objects
 assert objects[1]['pictures']==1 and objects[1]['charts']==0 and objects[1]['native_placeholders']==0,objects
 media={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('ppt/media/') and not n.endswith('/')}
 assert len(media)==1 and all(n.endswith('.png') for n in media),media
ir=json.loads((out/'dom-ir.json').read_text())
assert len(ir['captures'][1]['returned_placeholders'])==1
report['cases'].append({'id':'native-and-raster','kind':'normal/boundary','passed':True,'objects':objects,'media':media,'placeholder':ir['captures'][1]['returned_placeholders'],'evidence':['outputs/maps-probes/objects.pptx','outputs/maps-probes/dom-ir.json','validation/maps-converter.txt'],'limit':'library probe; not host-reviewed complete delivery or PowerPoint round-trip'})
svg=json.loads((out/'svg-failure.json').read_text())
assert svg['rejected'] and 'className.includes' in svg['error'],svg
report['cases'].append({'id':'inline-svg-rejected','kind':'failure','passed':True,'result':svg,'evidence':['outputs/maps-probes/svg-failure.html','outputs/maps-probes/svg-failure.json','validation/maps-converter-attempt1.txt'],'limit':'source has rasterization branch but this inline SVG fails first; no upstream patch'})
normal=base/'outputs/official-six'; before=core.sha256(normal/'answer.pptx')
stale=out/'shared-resource'; shutil.copytree(normal,stale)
(stale/'assets').mkdir(exist_ok=True); (stale/'assets/shared.css').write_text('/* research shared-resource freshness probe */\n',encoding='utf-8')
gaps=core.review_gaps(stale,core.slide_files(stale)); final=core.finalize(stale,{'delivery':{'mode':'strict'}})
assert len(gaps)==6 and not final['complete'] and not final['checks']['build_current'] and not final['checks']['slide_reviews_current']
report['cases'].append({'id':'shared-resource-invalidation','kind':'failure','passed':True,'gaps':gaps,'final':final,'reason':'whole assets snapshot invalidates all slide reviews even unused new asset','evidence':['outputs/maps-probes/shared-resource/final-report.json']})
blocked=out/'remote-resource';(blocked/'slides').mkdir(parents=True)
dump(blocked/'task.json',{'slides':1,'aspect_ratio':'16:9','language':'zh'})
(blocked/'slides/slide01.html').write_text('<html><body style="width:1280px;height:720px;margin:0"><img src="https://example.invalid/p02-probe.png"></body></html>',encoding='utf-8')
try: asyncio.run(core.render_slides(blocked)); raise AssertionError('remote resource unexpectedly accepted')
except ValueError as e:
 assert 'untracked' in str(e),str(e)
 report['cases'].append({'id':'remote-resource-block','kind':'failure','passed':True,'exception':'ValueError','message':str(e),'evidence':['outputs/maps-probes/remote-resource/slides/slide01.html'],'limit':'core review renderer route; library converter independently lacks this route guard'})
try: validate_review({'verdict':'pass','summary':'contradictory verdict','issues':[{'severity':'major','slide':1,'description':'test','suggested_fix':'test'}]});raise AssertionError('pass+major accepted')
except ValueError as e:
 assert 'cannot pass' in str(e)
 report['cases'].append({'id':'review-contradiction','kind':'boundary','passed':True,'exception':'ValueError','message':str(e)})
assert before==core.sha256(normal/'answer.pptx')=='eb90a46c983c15c09d02de5bccdd171b33ed39c22d12e7a9f912580ecd7b7b1b'
report['normal_unchanged_sha256']=before
report['artifacts']={str(p.relative_to(base)):core.sha256(p) for p in out.rglob('*') if p.is_file()}
dump(base/'validation/maps-probes.json',report)
print(json.dumps({'ok':True,'cases':len(report['cases']),'objects':objects},ensure_ascii=False))
