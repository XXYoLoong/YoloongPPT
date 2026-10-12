"""Retain original package features; apply only Artifact Tool authored policy cells."""
from __future__ import annotations
import argparse,copy,hashlib,json,re,math
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1];TMP=ROOT/'.tmp/execution-revision'
N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};S=N['s'];Q=lambda x:f'{{{S}}}{x}'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def column(text):
    result=0
    for c in text:result=result*26+ord(c)-64
    return result
def read(p):
    with ZipFile(p) as z:
        ss=[''.join(n.itertext()) for n in E.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
        rel={r.attrib['Id']:r.attrib['Target'] for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        out={};paths={};trees={}
        for sh in E.fromstring(z.read('xl/workbook.xml')).find('s:sheets',N):
            t=rel[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']];path=t.lstrip('/') if t.startswith('/') else 'xl/'+t
            tree=E.fromstring(z.read(path));name=sh.attrib['name'];cells={}
            for c in tree.findall('.//s:sheetData/s:row/s:c',N):
                f=c.find('s:f',N);v=c.find('s:v',N);t=c.attrib.get('t','n');value=v.text if v is not None else ''
                if t=='s':value=ss[int(value)]
                if t=='inlineStr':value=''.join(c.find('s:is',N).itertext())
                if f is not None:cells[c.attrib['r']]=('formula',f.text)
                elif value not in (None,''):cells[c.attrib['r']]=('text' if t in ('str','s','inlineStr') else t,value)
            out[name]=cells;paths[name]=path;trees[name]=tree
        return out,paths,trees
def main():
    before=TMP/'before-AI_PPT_完整需求与任务矩阵_V0.3.xlsx';authored=TMP/'after-AI_PPT_完整需求与任务矩阵_V0.3.xlsx';final=TMP/'verified-AI_PPT_完整需求与任务矩阵_V0.3.xlsx'
    b,paths,trees=read(before);a,ap,at=read(authored);assert list(a)==list(b) and len(a)==20
    allowed=set()
    for item in json.loads((TMP/'allowed-matrix-edits.json').read_text('utf-8')):
        match=re.fullmatch(r'([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?',item['range']);assert match
        c0=column(match[1]);r0=int(match[2]);c1=column(match[3] or match[1]);r1=int(match[4] or match[2])
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):allowed.add((item['sheet'],c,r))
    changed=[];replacements={}
    for name in b:
        tree=trees[name];data=tree.find('s:sheetData',N)
        for addr in set(a[name])|set(b[name]):
            if a[name].get(addr)==b[name].get(addr):continue
            m=re.fullmatch(r'([A-Z]+)(\d+)',addr);col=column(m[1]);r=int(m[2]);assert(name,col,r)in allowed,(name,addr,'Unapproved change')
            typ,value=a[name].get(addr,('text',''));assert typ!='formula','Execution edit may not change a formula'
            row=data.find(f's:row[@r="{r}"]',N)
            if row is None:row=E.Element(Q('row'),r=str(r));data.append(row)
            c=row.find(f's:c[@r="{addr}"]',N)
            if c is None:
                c=E.Element(Q('c'),r=addr)
                reference='N' if name=='可执行任务' else 'C' if name=='Codex交接' else m[1]
                source=tree.find(f'.//s:c[@r="{reference}{1 if r==1 else 2}"]',N)
                if source is not None and 's'in source.attrib:c.set('s',source.attrib['s'])
                row.append(c)
            for child in list(c):c.remove(child)
            c.set('t','str' if typ=='text' else typ);E.SubElement(c,Q('v')).text=value
            changed.append([name,addr])
        if any(n==name for n,_ in changed):
            # Preserve all existing styles, row attributes, caches, links, names and opaque parts.
            if name in ('总览','Codex交接'):
                merge=tree.find('s:mergeCells',N)
                if merge is None:
                    merge=E.Element(Q('mergeCells'))
                    filter_node=tree.find('s:autoFilter',N)
                    if filter_node is not None:tree.insert(list(tree).index(filter_node)+1,merge)
                    else:tree.insert(list(tree).index(data)+1,merge)
                existing={n.attrib['ref'] for n in merge}
                for new in at[name].findall('s:mergeCells/s:mergeCell',N):
                    if new.attrib['ref'] not in existing:merge.append(copy.deepcopy(new))
                if 'count'in merge.attrib:merge.set('count',str(len(merge)))
            if name=='可执行任务':
                cols=tree.find('s:cols',N)
                for start,width in [(15,18),(16,39),(17,45),(18,24)]:E.SubElement(cols,Q('col'),min=str(start),max=str(start),width=str(width),customWidth='1')
                f=tree.find('s:autoFilter',N)
                if f is not None:f.set('ref','A1:R454')
            if name=='来源索引':
                f=tree.find('s:autoFilter',N)
                if f is not None:f.set('ref','A1:G17')
            # Fit changed notes without touching historical task row attributes.
            changed_rows={int(re.search(r'\d+',addr)[0])for n,addr in changed if n==name}
            if name in ('需求主表','0-1全链路'):
                widths={}
                for cc in tree.findall('s:cols/s:col',N):
                    for c in range(int(cc.attrib['min']),int(cc.attrib['max'])+1):widths[c]=float(cc.attrib.get('width','8.43'))
                for rn in changed_rows:
                    rr=data.find(f's:row[@r="{rn}"]',N);height=30.0
                    for cc in rr:
                        addr=cc.attrib['r'];value=a[name].get(addr,('text',''))[1]or''
                        width=widths.get(column(re.match('[A-Z]+',addr)[0]),8.43)
                        lines=sum(max(1,math.ceil(sum(1.85 if ord(ch)>255 else 1 for ch in line)/max(3,width-1)))for line in str(value).split('\n'))
                        height=max(height,lines*13+8)
                    rr.set('ht',str(height));rr.set('customHeight','1')
            # Heights for added policy and source rows; historical task rows unchanged.
            for r in data:
                rn=int(r.attrib['r'])
                if name=='Codex交接' and rn>=16 or name=='来源索引' and rn==17 or name=='总览' and rn==3:
                    original=at[name].find(f's:sheetData/s:row[@r="{rn}"]',N)
                    if original is not None:
                        for k in ('ht','customHeight'):
                            if k in original.attrib:r.set(k,original.attrib[k])
                cells=list(r)
                for c in cells:r.remove(c)
                for c in sorted(cells,key=lambda x:column(re.match('[A-Z]+',x.attrib['r'])[0])):r.append(c)
            rows=list(data)
            for r in rows:data.remove(r)
            for r in sorted(rows,key=lambda x:int(x.attrib['r'])):data.append(r)
            replacements[paths[name]]=E.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
    with ZipFile(before) as z,ZipFile(final,'w') as dest:
        for info in z.infolist():dest.writestr(copy.copy(info),replacements.get(info.filename,z.read(info.filename)))
    f,_,ft=read(final);assert f==a,'Final workbook differs from Artifact Tool authored values'
    # All original mandatory fields, dependency, priority, statuses, evidence and AC stay identical.
    for sheet,cols in [('需求主表','ABCDEFGHIJKLNOP'),('可执行任务','ABCDEFGHIJKLMN'),('0-1全链路','ABCDEFGH'),('验收矩阵','ABCDEFGHIJ')]:
        for addr,value in b[sheet].items():
            if re.match('[A-Z]+',addr)[0]in cols:assert f[sheet].get(addr)==value,(sheet,addr)
    for sheet in b:
        for addr,value in b[sheet].items():
            if value[0]=='formula':assert f[sheet][addr]==value
    for sheet,col,total in [('需求主表','A',308),('可执行任务','A',453),('0-1全链路','A',45),('决策链','A',40),('PowerPoint对象矩阵','A',30),('PowerPoint后端','A',9),('验收矩阵','A',30)]:
        ids=[v for c,v in f[sheet].items() if re.fullmatch(col+r'\d+',c) and int(c[1:])>1]
        assert len(ids)==total and len(set(ids))==total,(sheet,total,len(ids))
    statuses={sheet:dict(Counter(v[1]for c,v in f[sheet].items()if re.fullmatch(col+r'\d+',c)and int(c[len(col):])>1))for sheet,col in [('需求主表','N'),('可执行任务','L'),('验收矩阵','G')]}
    assert statuses['需求主表']=={'已完成':35,'进行中':174,'未开始':99}
    assert statuses['可执行任务']=={'已完成':61,'进行中':240,'未开始':152}
    with ZipFile(before) as z,ZipFile(final) as zz:
        assert z.namelist()==zz.namelist()
        assert all(z.read(n)==zz.read(n)for n in z.namelist()if n not in replacements)
    for addr,value in b['总览'].items():
        if value[0]=='formula':
            old=trees['总览'].find(f'.//s:c[@r="{addr}"]/s:v',N);new=ft['总览'].find(f'.//s:c[@r="{addr}"]/s:v',N)
            assert E.tostring(old)==E.tostring(new),(addr,'Formula cache changed')
    assert all(f['可执行任务'][f'O{r}'][1]=='GPT-6.1 sol'for r in range(2,455))
    goal=(TMP/'after-GOAL.md').read_text('utf-8');assert'EXEC-20261012-01'in goal and'禁止工期预算'in goal and'Docling'in goal
    report={'revision_id':'EXEC-20261012-01','before_sha256':sha(before),'after_sha256':sha(final),'worksheets':20,'changed_cells':changed,'changed_parts':list(replacements),'all_original_required_fields_dependencies_and_acceptance_preserved':True,'original_statuses_and_evidence_preserved':True,'original_formulas_and_overview_caches_preserved':True,'original_task_row_attributes_and_package_features_preserved':True,'task_execution_owners':453,'statuses':statuses,'new_source':'SRC-016 / Docling','no_system_acceptance_claimed':True}
    (ROOT/'validation/execution-matrix-preservation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({**{k:v for k,v in report.items()if k not in('changed_cells',)},'changed_cells':len(changed)},ensure_ascii=False))
if __name__=='__main__':main()
