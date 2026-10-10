"""Content-driven native layouts, capacity checked before selection and writing.

DEC-030/031/033/034 integration subset; no claim of the full node contracts.
"""
import copy
import hashlib
import json
from pathlib import Path

from .artifacts import entity
from .errors import TaskError
from .writer import capacity


VERSION='native-editorial-1'


def text(slot,role,items,bounds,size,refs,**formatting):
    return {'object_id':entity('object'),'type':'text','role':role,'slot_key':slot,'text':items,
            'bounds':bounds,'font_size':size,'source_refs':refs,'format':formatting}


def candidate(kind,content,order,count,style):
    refs=content['evidence_refs'];body=content['body'];dark=style['foreground'];light=style['background']
    title=text('title','title',[content['title']],[0.7,0.6,11.95,1.25],32,refs,color=dark,bold=True,margin=0)
    footer=text('footer','footer',[f'{order+1:02d} / {count:02d}'],[0.7,6.83,11.95,0.38],16,[],color=style['accent'],paragraph_spacing=0,margin=0)
    elements=[title];page_style=copy.deepcopy(style)
    if kind=='cover':
        page_style.update(background=dark,foreground=light)
        title.update(bounds=[0.7,1.35,6.4,3.65],font_size=40,format={'color':light,'bold':True,'margin':0})
        if len(content['title'])>=10 and '：' in content['title']:
            first,second=content['title'].split('：',1);title['text']=[first+'：',second]
        elements.append(text('body','body',body,[7.65,1.42,4.9,4.9],22,refs,color=light,paragraph_spacing=16,margin=0))
        footer['format']['color']=light
    elif kind=='closing':
        title.update(bounds=[0.7,1.28,5.1,4.55],font_size=36,format={'color':dark,'bold':True,'margin':0})
        elements.append(text('body','body',body,[6.4,1.24,6.2,4.95],23,refs,color=light,fill=dark,margin=0.28,paragraph_spacing=16))
    elif kind in {'cards','columns'}:
        if kind=='cards':
            slots=[[0.7+(i%2)*6.15,2.05+(i//2)*2.13,5.82,1.85] for i in range(len(body))]
            chunks=[[item] for item in body]
        else:
            split=(len(body)+1)//2;chunks=[body[:split],body[split:]]
            slots=[[0.7+i*6.15,2.05,5.82,4.25] for i in range(2)]
        for i,(chunk,bounds) in enumerate(zip(chunks,slots)):
            elements.append(text(f'body.{i}','body',chunk,bounds,22,refs,color=dark,fill='FFFFFF',border='D6DFDA',margin=0.22,paragraph_spacing=14))
    elif kind in {'table','chart'}:
        elements.append(text('body','body',body,[0.7,1.92,3.25,4.55],21,refs,color=dark,margin=0,paragraph_spacing=16))
        elements.append({'object_id':entity('object'),'type':kind,'role':'data','slot_key':'data',
                         'data':content[kind],'bounds':[4.32,1.96,8.28,4.58],'font_size':16,'source_refs':refs})
    else:
        elements.append(text('body','body',body,[0.72,2.0,11.85,4.35],24,refs,color=dark,margin=0,paragraph_spacing=15))
    elements.append(footer)
    for element in elements:
        if element['type']=='text':
            f=element.get('format',{})
            capacity(element['text'],element['bounds'],element['font_size'],padding=f.get('margin',0.12),paragraph_spacing=f.get('paragraph_spacing',10))
        elif element['type']=='table':
            data=element['data'];rows=[data['columns'],*data['rows']]
            for row in rows:
                for cell in row:capacity([cell],[0,0,element['bounds'][2]/len(data['columns']),element['bounds'][3]/len(rows)],16,padding=0.07,paragraph_spacing=0)
    return elements,page_style


def choose(content,order,count,style,previous_kind=None,registry=None):
    """Never change, summarize or drop content to make a layout fit."""
    kinds=[content['kind']] if content['kind']!='text' else ['editorial','columns','cards','cover','closing']
    from .schemas import ROOT
    catalog=json.loads((ROOT/'contracts/native-layout.catalog.json').read_text(encoding='utf-8'))
    candidates=[];eligible=[]
    for kind in kinds:
        reasons=[];score=40
        valid=not ((kind=='cards' and not 2<=len(content['body'])<=4) or (kind=='columns' and len(content['body'])<2))
        if kind=='cover':valid=order==0 and count>1;score=100;reasons.append('First text page: clear opening and side summary.')
        elif kind=='closing':valid=order==count-1 and count>1;score=95;reasons.append('Last text page: strong conclusion and preserved action points.')
        elif kind=='cards':score=75;reasons.append('Two to four original body items in individual editable panels; semantic relation is unchanged and not inferred.')
        elif kind=='columns':score=65;reasons.append('Longer point sets balanced across two columns without rewriting.')
        elif kind in {'table','chart'}:score=100;reasons.append('Native editable data object retains prominence and all original values.')
        else:reasons.append('Readable broad text slot with all original paragraphs.')
        if kind==previous_kind:score-=18;reasons.append('Variation penalty against repeating adjacent layout.')
        definition=next(x for x in catalog['layouts'] if x['name']==kind)
        if registry:
            for capability in definition['required_capabilities']:registry.select(capability)
        entry={'candidate_id':entity('candidate'),'layout_id':definition['layout_id'],'layout':kind,'score':score,'reasons':reasons,'eligible':valid,'capacity_pass':False,
               'backend_support':{'backend':'PP-05','checked':registry is not None,'required_capabilities':definition['required_capabilities']},'rejection':None}
        if valid:
            try:
                elements,page_style=candidate(kind,content,order,count,style)
                entry['capacity_pass']=True
                eligible.append((score,kind,elements,page_style,entry['candidate_id']))
            except TaskError as error:
                if error.code!='TEXT_CAPACITY_EXCEEDED':raise
                entry.update(eligible=False,rejection={'code':error.code,'details':error.details})
        else:entry['rejection']={'code':'LAYOUT_CONTENT_MISMATCH','reason':'Position or body item count does not match this layout.'}
        candidates.append(entry)
    if not eligible:
        raise TaskError('LAYOUT_CAPACITY_UNSUPPORTED','全部当前版式容量不足；没有裁剪正文、缩小字号或删除数据。','LayoutSelector',['DEC-030','DEC-031','DEC-034'],candidates)
    chosen=max(eligible,key=lambda x:x[0]);_,kind,elements,page_style,selected=chosen
    trace={'version':VERSION,'input':{'content':content,'order':order,'page_count':count,'style':style,'previous_layout':previous_kind},
           'candidates':candidates,'selected':selected,'selected_layout':kind,'mechanism':'Content compatibility + measured capacity + opening/closing/data hierarchy + adjacent variation; stable catalog order breaks equal scores.',
           'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fallback':'Capacity rejection selects another declared candidate; all rejected stops before write.',
           'limitations':['Current native text/table/chart subset; full DEC-030–035, imagery/template/RTL/brand selection not complete.']}
    return elements,page_style,trace
