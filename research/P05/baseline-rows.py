import json
import collections, pathlib, posixpath, re, shutil, zipfile, xml.etree.ElementTree as E
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def read(file):
 with zipfile.ZipFile(file) as z:
  ss=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
  rel={n.attrib['Id']:n.attrib['Target'] for n in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  data={}; features={}
  for sh in E.fromstring(z.read('xl/workbook.xml')).find('s:sheets',ns):
   target=rel[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
   xml=E.fromstring(z.read(target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)))
   cells={}
   for c in xml.findall('.//s:sheetData/s:row/s:c',ns):
    f=c.find('s:f',ns); v=c.find('s:v',ns); val=v.text if v is not None else None
    if f is not None:
     assert c.attrib.get('t')!='e', (sh.attrib['name'],c.attrib['r'],val)
     cells[c.attrib['r']]=('formula',f.text)
    else:
     if c.attrib.get('t')=='s': val=ss[int(val)]
     elif c.attrib.get('t')=='inlineStr': val=''.join(c.find('s:is',ns).itertext())
     if val not in [None,'']: cells[c.attrib['r']]=(c.attrib.get('t','n') if c.attrib.get('t') not in ['s','inlineStr'] else 'text',val)
   data[sh.attrib['name']]=cells
   features[sh.attrib['name']]={name:len(xml.findall('s:'+name,ns)) for name in ['dataValidations','conditionalFormatting','mergeCells','autoFilter','tableParts','drawing']}
  return data,features
data,_=read('F:/YoloongPPT/AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
result={}
for sheet in ['决策链','PowerPoint对象矩阵']:
 cells=data[sheet]; rows=[]
 for cell,val in cells.items():
  if cell.startswith('A') and val[1].startswith(('DEC-','PPT-')):
   n=cell[1:]; row=[cells.get(c+n,('',None))[1] for c in 'ABCDEFGHIJKLM'];rows.append(row)
   print(row[0],row[1])
 result[sheet]=rows
for sheet,nums in [('需求主表',range(34,37)),('可执行任务',range(58,64))]:
 cells=data[sheet];result[sheet]=[[cells.get(c+str(n),('',None))[1] for c in 'ABCDEFGHIJKLMNOP'] for n in nums]
pathlib.Path('F:/YoloongPPT-Temp-P01-05/p05-baseline-rows.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
