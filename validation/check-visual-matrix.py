"""Check all original scope/cells/formulas/features and only then replace matrix."""
import collections
import argparse
import hashlib
import json
import pathlib
import re
import shutil
import xml.etree.ElementTree as E
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
ns={};exec((ROOT/'research/P05/baseline-rows.py').read_text('utf-8').split('data,_=')[0],ns)
tmp=pathlib.Path('F:/YoloongPPT-Temp-P01-05')
before,bf=ns['read'](tmp/'matrix-before-visual.xlsx');after,af=ns['read'](tmp/'matrix-after-visual.xlsx')
assert list(before)==list(after) and len(after)==20 and bf==af
allowed=set()
for item in json.loads((tmp/'visual-matrix-allowed.json').read_text('utf-8')):
    match=re.fullmatch(r'([A-Z])(\d+):([A-Z])(\d+)',item['range']);assert match and match[2]==match[4]
    allowed.update((item['sheet'],chr(column)+match[2]) for column in range(ord(match[1]),ord(match[3])+1))
changed=[]
for sheet in before:
    for cell in set(before[sheet])|set(after[sheet]):
        if before[sheet].get(cell)!=after[sheet].get(cell):
            assert (sheet,cell) in allowed,(sheet,cell)
            changed.append((sheet,cell))
        if before[sheet].get(cell,('',None))[0]=='formula':assert after[sheet].get(cell)==before[sheet][cell]

def count(document,sheet,col):
    return collections.Counter(value[1] for cell,value in document[sheet].items() if re.fullmatch(col+'[0-9]+',cell) and int(cell[1:])>1)
req=count(after,'需求主表','N');tasks=count(after,'可执行任务','L');ac=count(after,'验收矩阵','G');flow=count(after,'0-1全链路','G')
assert sum(req.values())==308 and sum(tasks.values())==453 and sum(ac.values())==30 and sum(flow.values())==45
assert req['已完成']==35 and tasks['已完成']==61
assert ac==count(before,'验收矩阵','G') and ac.get('已通过',0)==0 and ac.get('通过',0)==0
for sheet,column in [('需求主表','N'),('可执行任务','L')]:
    for cell,value in before[sheet].items():
        if re.fullmatch(column+r'\d+',cell) and value[1]=='已完成':assert after[sheet][cell]==value
for sheet in before:
    for cell,value in before[sheet].items():
        if cell.startswith('A') and re.fullmatch(r'A\d+',cell):assert after[sheet].get(cell)==value

overview={};n={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(tmp/'matrix-after-visual.xlsx') as archive:
    tree=E.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    for cell in tree.findall('.//s:c',n):
        assert cell.get('t')!='e',('formula_error',cell.get('r'))
    for row in range(5,22):
        domain=after['总览'].get('A'+str(row),('',None))[1]
        if not domain:continue
        ids=[cell[1:] for cell,value in after['需求主表'].items() if re.fullmatch('B[0-9]+',cell) and value[1]==domain]
        expected=len(ids);completed=sum(after['需求主表'].get('N'+id,('',None))[1]=='已完成' for id in ids)
        values={}
        for column,target in [('B',expected),('E',completed)]:
            value=tree.find(f'.//s:c[@r="{column}{row}"]/s:v',n)
            assert value is not None and value.text is not None,(domain,column,'cache_missing')
            assert float(value.text)==target,(domain,column,target,value.text)
            values[column]=float(value.text)
        percent=tree.find(f'.//s:c[@r="F{row}"]/s:v',n)
        assert percent is not None and percent.text is not None
        assert abs(float(percent.text)-completed/expected)<1e-10,(domain,'completion_percent',percent.text)
        overview[domain]={'requirements':expected,'completed':completed,'cached_values':values,'cached_fraction':float(percent.text)}

metadata=json.loads((tmp/'visual-matrix-evidence.json').read_text('utf-8'))
assert metadata['baseline_sha256']==hashlib.sha256((tmp/'matrix-before-visual.xlsx').read_bytes()).hexdigest()
assert metadata['actual_qa']['p0_issue_count']==0 and metadata['completion']['system_acceptance']=='not_passed'
report={'changed_cells':sorted(changed),'worksheets':20,'requirements':dict(req),'tasks':dict(tasks),'AC':dict(ac),'flow':dict(flow),
        'unrelated_values_and_formulas_preserved':True,'worksheet_features_preserved':True,'original_ids_and_completed_rows_preserved':True,
        'overview':overview,**metadata,'scope':'Partial runtime/QA/revision expansion; historical and incremental checks remain versioned separately; full original acceptance unpassed.'}
(ROOT/'validation/visual-matrix-update.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
if args.apply:
    current=hashlib.sha256((ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx').read_bytes()).hexdigest()
    assert current in {metadata['baseline_sha256'],hashlib.sha256((tmp/'matrix-after-visual.xlsx').read_bytes()).hexdigest()},'Original changed since baseline; refusing overwrite.'
    shutil.copyfile(tmp/'matrix-after-visual.xlsx',ROOT/'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
print(json.dumps({'changed_cells':len(changed),'requirements':dict(req),'tasks':dict(tasks),'AC':dict(ac),'flow':dict(flow),'applied':args.apply},ensure_ascii=False))
