"""Read original matrix states for the user-requested closure report; never alter it."""
import collections,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1];n={}
exec((ROOT/'research/P05/baseline-rows.py').read_text('utf-8').split('data,_=')[0],n)
data,_=n['read'](ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
def rows(sheet):
    cells=data[sheet]
    return [{c:cells.get(c+cell[1:],('',None))[1] for c in 'ABCDEFGHIJKLMNOP'} for cell in cells if re.fullmatch(r'A\d+',cell) and int(cell[1:])>1]
requirements=rows('需求主表');tasks=rows('可执行任务');acceptance=rows('验收矩阵')
domains={}
for row in requirements:
    domains.setdefault(row['B'],collections.Counter())[row['N']]+=1
def counts(values,key):return dict(collections.Counter(r[key] for r in values))
report={'date':'2026-10-12','source':'AI_PPT_完整需求与任务矩阵_V0.3.xlsx','requirements':counts(requirements,'N'),
        'tasks':counts(tasks,'L'),'AC':counts(acceptance,'G'),'domains':{k:dict(v) for k,v in domains.items()},
        'requirements_not_complete':sum(r['N']!='已完成' for r in requirements),'tasks_not_complete':sum(r['L']!='已完成' for r in tasks),
        'acceptance_not_passed':sum(r['G'] not in {'已通过','通过'} for r in acceptance),
        'completed_requirement_ids':[r['A'] for r in requirements if r['N']=='已完成'],
        'completed_task_ids':[r['A'] for r in tasks if r['L']=='已完成'],
        'remaining_requirement_ids':[r['A'] for r in requirements if r['N']!='已完成'],
        'remaining_task_ids':[r['A'] for r in tasks if r['L']!='已完成'],
        'boundary':'Original acceptance states. In-progress includes runnable subsets, research and missing coverage; not a percentage of usable functions.'}
assert sum(report['requirements'].values())==308 and sum(report['tasks'].values())==453
(ROOT/'validation/stage-closure-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in {'domains','completed_requirement_ids','completed_task_ids','remaining_requirement_ids','remaining_task_ids'}},ensure_ascii=False))
