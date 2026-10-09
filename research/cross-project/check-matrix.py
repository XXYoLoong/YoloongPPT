"""Allow only seven RES-031 cell-value edits; preserve unrelated values/formulas/features."""
import collections,json,pathlib,re,shutil
ROOT=pathlib.Path(__file__).resolve().parents[2]; ns={}
exec((ROOT/'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns)
folder=pathlib.Path('F:/YoloongPPT-Temp-P01-05')
before,bf=ns['read'](folder/'matrix-before-res-031.xlsx');after,af=ns['read'](folder/'matrix-after-res-031.xlsx')
assert list(before)==list(after) and len(after)==20 and bf==af
allowed={('需求主表',c+'37') for c in 'NOP'}|{('可执行任务',f'{c}{r}') for r in [64,65] for c in 'LM'}
changes=[]
for sheet in before:
 for cell in set(before[sheet])|set(after[sheet]):
  if before[sheet].get(cell)!=after[sheet].get(cell):
   assert (sheet,cell) in allowed,(sheet,cell)
   changes.append((sheet,cell))
assert len(changes)==7 and after['需求主表']['N37'][1]=='已完成'
for r in [64,65]:assert after['可执行任务'][f'L{r}'][1]=='已完成'
for r in [35,37,39,41,43]:assert after['可执行任务'][f'L{r}'][1]=='进行中'
assert collections.Counter(v[1] for c,v in after['验收矩阵'].items() if re.fullmatch('G(?:[2-9]|[12][0-9]|3[01])',c))=={'未执行':30}
report={'changed_cells':sorted(changes),'worksheets':20,'unrelated_values_and_formulas_preserved':True,'worksheet_feature_presence_counts_preserved':True,'P03_VERIFY':'5进行中，未变更','AC_status':'30未执行','req_status':dict(collections.Counter(v[1] for c,v in after['需求主表'].items() if re.fullmatch('N[0-9]+',c) and int(c[1:])>1)),'task_status':dict(collections.Counter(v[1] for c,v in after['可执行任务'].items() if re.fullmatch('L[0-9]+',c) and int(c[1:])>1))}
(ROOT/'research/cross-project/matrix-update.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(folder/'matrix-after-res-031.xlsx',ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
print(json.dumps(report,ensure_ascii=False))
