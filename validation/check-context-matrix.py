"""Verify approved status/evidence edits and preserve the complete original workbook."""
import collections
import json
import pathlib
import re
import shutil

ROOT=pathlib.Path(__file__).resolve().parents[1]
ns={}
exec((ROOT/'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0],ns)
tmp=pathlib.Path('F:/YoloongPPT-Temp-P01-05')
before,bf=ns['read'](tmp/'matrix-before-context.xlsx')
after,af=ns['read'](tmp/'matrix-after-context.xlsx')
assert list(before)==list(after) and len(after)==20 and bf==af
allowed=set()
for edit in json.loads((tmp/'context-matrix-allowed.json').read_text(encoding='utf-8')):
    match=re.fullmatch(r'([A-Z]+)(\d+):([A-Z]+)(\d+)',edit['range'])
    assert match and match[2]==match[4] and len(match[1])==len(match[3])==1
    allowed.update((edit['sheet'],chr(c)+match[2]) for c in range(ord(match[1]),ord(match[3])+1))
changes=[]
for sheet in before:
    for cell in set(before[sheet])|set(after[sheet]):
        if before[sheet].get(cell)!=after[sheet].get(cell):
            assert (sheet,cell) in allowed,(sheet,cell)
            changes.append((sheet,cell))
for c in ['N71','N72']:assert after['需求主表'][c][1]=='已完成'
for c in ['L100','L101','L102','L103']:assert after['可执行任务'][c][1]=='已完成'
req=collections.Counter(v[1] for c,v in after['需求主表'].items() if re.fullmatch('N[0-9]+',c) and int(c[1:])>1)
task=collections.Counter(v[1] for c,v in after['可执行任务'].items() if re.fullmatch('L[0-9]+',c) and int(c[1:])>1)
ac=collections.Counter(v[1] for c,v in after['验收矩阵'].items() if re.fullmatch('G[0-9]+',c) and int(c[1:])>1)
assert req=={'已完成':33,'进行中':72,'未开始':203},req
assert task=={'已完成':57,'进行中':74,'未开始':322},task
assert ac=={'部分执行/未通过':3,'未执行':27},ac
report={'changed_cells':sorted(changes),'worksheets':20,'unrelated_values_and_formulas_preserved':True,'worksheet_feature_presence_counts_preserved':True,'req_status':dict(req),'task_status':dict(task),'AC_status':dict(ac),'scope':'DEC-002/003 TASK/VERIFY complete; related SYS/GOV/OBS/TST partial; full baseline scope retained.'}
(ROOT/'validation/context-matrix-update.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(tmp/'matrix-after-context.xlsx',ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
print(json.dumps({'changed_cells':len(changes),'req_status':dict(req),'task_status':dict(task),'AC_status':dict(ac)},ensure_ascii=False))
