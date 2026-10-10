"""Only approved evidence/status changes; preserve original scope and formulas."""
import collections,json,pathlib,re,shutil,xml.etree.ElementTree as E,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];ns={}
exec((ROOT/'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns)
tmp=pathlib.Path('F:/YoloongPPT-Temp-P01-05')
before,bf=ns['read'](tmp/'matrix-before-layout.xlsx');after,af=ns['read'](tmp/'matrix-after-layout.xlsx')
assert list(before)==list(after) and len(after)==20 and bf==af
allowed=set()
for edit in json.loads((tmp/'layout-matrix-allowed.json').read_text(encoding='utf-8')):
 m=re.fullmatch(r'([A-Z])(\d+):([A-Z])(\d+)',edit['range']);assert m and m[2]==m[4]
 allowed.update((edit['sheet'],chr(c)+m[2]) for c in range(ord(m[1]),ord(m[3])+1))
changes=[]
for sheet in before:
 for cell in set(before[sheet])|set(after[sheet]):
  if before[sheet].get(cell)!=after[sheet].get(cell):assert (sheet,cell) in allowed,(sheet,cell);changes.append((sheet,cell))
def count(sheet,col):return collections.Counter(v[1] for c,v in after[sheet].items() if re.fullmatch(col+'[0-9]+',c) and int(c[1:])>1)
req=count('需求主表','N');task=count('可执行任务','L');ac=count('验收矩阵','G');flow=count('0-1全链路','G')
assert req=={'已完成':33,'进行中':76,'未开始':199},req
assert task=={'已完成':57,'进行中':82,'未开始':314},task
assert ac=={'部分执行/未通过':3,'未执行':27},ac
assert flow=={'进行中':41,'未开始':4},flow
overview={}
with zipfile.ZipFile(tmp/'matrix-after-layout.xlsx') as z:
 tree=E.fromstring(z.read('xl/worksheets/sheet1.xml'));n={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 for row in range(5,19):
  domain=after['总览'].get('A'+str(row),('',None))[1]
  if not domain:continue
  actual=sum(v[1]=='已完成' and after['需求主表'].get('B'+c[1:],('',None))[1]==domain for c,v in after['需求主表'].items() if re.fullmatch('N[0-9]+',c))
  cell=tree.find(f'.//s:c[@r="E{row}"]/s:v',n)
  if cell is not None and cell.text is not None:assert float(cell.text)==actual,(domain,actual,cell.text)
  overview[domain]={'actual_completed':actual,'cache':cell.text if cell is not None else None}
report={'changed_cells':sorted(changes),'worksheets':20,'unrelated_values_and_formulas_preserved':True,'worksheet_feature_presence_counts_preserved':True,'req_status':dict(req),'task_status':dict(task),'AC_status':dict(ac),'flow_status':dict(flow),'overview_cache':overview,'scope':'Native layout subset and stale flow statuses corrected; all original requirements and acceptance remain.'}
(ROOT/'validation/layout-matrix-update.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(tmp/'matrix-after-layout.xlsx',ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
print(json.dumps({'changed_cells':len(changes),'req_status':dict(req),'task_status':dict(task),'flow_status':dict(flow)},ensure_ascii=False))
