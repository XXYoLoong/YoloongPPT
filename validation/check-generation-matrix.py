"""Verify only this package's status/evidence cells; preserve all baseline scope."""
import collections,json,pathlib,re,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];ns={}
exec((ROOT/'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns)
folder=pathlib.Path('F:/YoloongPPT-Temp-P01-05')
before,bf=ns['read'](folder/'matrix-before-generation.xlsx');after,af=ns['read'](folder/'matrix-after-generation.xlsx')
assert list(before)==list(after) and len(after)==20 and bf==af
rows=[(188,297,6),(193,302,11),(194,303,12),(195,304,13),(196,305,14),(197,306,15),(198,307,16),(199,308,17),(200,309,18)]
allowed={('需求主表',f'{c}{r}') for r,_,_ in rows for c in 'NOP'}|{('可执行任务',f'{c}{t}') for _,t,_ in rows for c in 'LM'}|{('系统组件接口',f'{c}{i}') for _,_,i in rows for c in 'HI'}
allowed|={('需求主表',f'{c}{r}') for r in [9,202,203] for c in 'OP'}|{('可执行任务',f'M{r}') for r in [11,311,312]}
allowed|={('验收矩阵',f'{c}{r}') for r in [2,28,29] for c in 'GHIJ'}|{('PowerPoint后端',f'{c}6') for c in 'HIJ'}|{('数据对象',f'J{r}') for r in [37,41,42,43]}
changes=[]
for sheet in before:
 for cell in set(before[sheet])|set(after[sheet]):
  if before[sheet].get(cell)!=after[sheet].get(cell):
   assert (sheet,cell) in allowed,(sheet,cell)
   changes.append((sheet,cell))
assert len(changes)==91,len(changes)
for r,t,i in rows:assert after['需求主表'][f'N{r}'][1]=='进行中' and after['可执行任务'][f'L{t}'][1]=='进行中'
for r in [35,37,39,41,43]:assert after['可执行任务'][f'L{r}'][1]=='进行中'
ac=collections.Counter(v[1] for c,v in after['验收矩阵'].items() if re.fullmatch('G(?:[2-9]|[12][0-9]|3[01])',c))
assert ac=={'未执行':27,'部分执行/未通过':3},ac
report={'changed_cells':sorted(changes),'worksheets':20,'unrelated_values_and_formulas_preserved':True,'worksheet_feature_presence_counts_preserved':True,'P03_VERIFY':'5进行中，未变更','AC_status':dict(ac),'req_status':dict(collections.Counter(v[1] for c,v in after['需求主表'].items() if re.fullmatch('N[0-9]+',c) and int(c[1:])>1)),'task_status':dict(collections.Counter(v[1] for c,v in after['可执行任务'].items() if re.fullmatch('L[0-9]+',c) and int(c[1:])>1))}
assert report['req_status']=={'已完成':30,'进行中':68,'未开始':210}
assert report['task_status']=={'已完成':51,'进行中':70,'未开始':332}
(ROOT/'validation/generation-matrix-update.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(folder/'matrix-after-generation.xlsx',ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
print(json.dumps({'changed_cells':len(changes),'req_status':report['req_status'],'task_status':report['task_status'],'AC_status':report['AC_status']},ensure_ascii=False))
