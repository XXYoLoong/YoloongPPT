"""Preserve baseline scope/formulas and only update approved status/evidence cells."""
import collections,json,pathlib,re,shutil,xml.etree.ElementTree as E,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];ns={}
exec((ROOT/'research/P05/baseline-rows.py').read_text('utf-8').split('data,_=')[0],ns)
tmp=pathlib.Path('F:/YoloongPPT-Temp-P01-05')
before,bf=ns['read'](tmp/'matrix-before-parallel.xlsx');after,af=ns['read'](tmp/'matrix-after-parallel.xlsx')
assert list(before)==list(after) and len(after)==20 and bf==af
allowed=set()
for item in json.loads((tmp/'parallel-matrix-allowed.json').read_text('utf-8')):
 m=re.fullmatch(r'([A-Z])(\d+):([A-Z])(\d+)',item['range']);assert m and m[2]==m[4]
 allowed.update((item['sheet'],chr(c)+m[2]) for c in range(ord(m[1]),ord(m[3])+1))
changed=[]
for sheet in before:
 for cell in set(before[sheet])|set(after[sheet]):
  if before[sheet].get(cell)!=after[sheet].get(cell):
   assert (sheet,cell) in allowed,(sheet,cell)
   changed.append((sheet,cell))
def count(sheet,col):return collections.Counter(v[1] for c,v in after[sheet].items() if re.fullmatch(col+'[0-9]+',c) and int(c[1:])>1)
req=count('需求主表','N');tasks=count('可执行任务','L');ac=count('验收矩阵','G');flow=count('0-1全链路','G')
assert sum(req.values())==308 and sum(tasks.values())==453 and sum(ac.values())==30 and sum(flow.values())==45
assert req['已完成']==35 and tasks['已完成']==61 and ac.get('已通过',0)==0
overview={}
with zipfile.ZipFile(tmp/'matrix-after-parallel.xlsx') as z:
 tree=E.fromstring(z.read('xl/worksheets/sheet1.xml'));n={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 for row in range(5,22):
  domain=after['总览'].get('A'+str(row),('',None))[1]
  if not domain:continue
  actual=sum(v[1]=='已完成' and after['需求主表'].get('B'+c[1:],('',None))[1]==domain for c,v in after['需求主表'].items() if re.fullmatch('N[0-9]+',c))
  value=tree.find(f'.//s:c[@r="E{row}"]/s:v',n)
  if value is not None and value.text is not None:assert float(value.text)==actual,(domain,actual,value.text)
  overview[domain]={'actual_completed':actual,'cache':value.text if value is not None else None}
report={'changed_cells':sorted(changed),'worksheets':20,'unrelated_values_and_formulas_preserved':True,'worksheet_features_preserved':True,
        'requirements':dict(req),'tasks':dict(tasks),'AC':dict(ac),'flow':dict(flow),'overview':overview,
        'scope':'parallel runtime components; full original acceptance retained; no unearned completed status'}
(ROOT/'validation/parallel-matrix-update.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
shutil.copyfile(tmp/'matrix-after-parallel.xlsx',ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
print(json.dumps({'changed_cells':len(changed),'requirements':dict(req),'tasks':dict(tasks)},ensure_ascii=False))
