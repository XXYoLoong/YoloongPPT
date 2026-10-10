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


VERSION='native-layout-stages-2'


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
    elif kind=='image':
        image=copy.deepcopy(content['image'])
        elements.append(text('body','body',body,[0.7,1.92,3.25,4.55],21,refs,color=dark,margin=0,paragraph_spacing=16))
        elements.append({'object_id':entity('object'),'type':'image','role':'asset','slot_key':'asset',
                         'data':image,'bounds':[4.32,1.96,8.28,4.58],'font_size':16,'source_refs':image.get('source_refs',refs)})
    elif kind=='diagram':
        diagram=content['diagram'];nodes=diagram['nodes'];edges=diagram.get('edges',[])
        if diagram.get('type') not in {'process','timeline','tree','network','matrix','funnel','swimlane'}:
            raise TaskError('DIAGRAM_TYPE_UNSUPPORTED','图示类型未登记。','LayoutSelector',['DEC-030'])
        ids=[node['node_id'] for node in nodes]
        if not 2<=len(nodes)<=12 or len(ids)!=len(set(ids)) or any(edge['from'] not in ids or edge['to'] not in ids or edge['from']==edge['to'] for edge in edges):
            raise TaskError('DIAGRAM_STRUCTURE_INVALID','图示必须为2–12个唯一节点及有效非自环边。','LayoutSelector',['DEC-030'])
        if diagram['type']=='swimlane' and not all('lane' in node for node in nodes):
            raise TaskError('DIAGRAM_LANES_REQUIRED','泳道图必须有明确来源泳道分组，未猜测。','LayoutSelector',['DEC-030'])
        if diagram['type']=='tree':
            incoming={node:0 for node in ids};children={node:[] for node in ids}
            for edge in edges:incoming[edge['to']]+=1;children[edge['from']].append(edge['to'])
            roots=[node for node in ids if incoming[node]==0];seen=[];queue=list(roots)
            while queue:
                node=queue.pop(0);seen.append(node)
                for child in children[node]:
                    incoming[child]-=1
                    if incoming[child]==0:queue.append(child)
            if len(roots)!=1 or len(seen)!=len(nodes) or len(edges)!=len(nodes)-1:
                raise TaskError('DIAGRAM_TREE_INVALID','树图必须保留唯一根和无环单亲结构。','LayoutSelector',['DEC-030'])
        elements.append(text('body','body',body,[0.7,1.92,3.25,4.55],21,refs,color=dark,margin=0,paragraph_spacing=16))
        vertical=diagram.get('direction','horizontal')=='vertical';positions={}
        for index,node in enumerate(nodes):
            if vertical:
                step=4.58/len(nodes);bounds=[4.55,1.96+index*step,7.8,step*.68]
            else:
                cols=min(4,len(nodes));rows=(len(nodes)+cols-1)//cols;row=index//cols;col=index%cols;stepx=8.28/cols;stepy=4.58/rows;bounds=[4.32+col*stepx,1.96+row*stepy,stepx*.84,stepy*.72]
            if diagram['type']=='funnel':
                bounds[2]*=1-index/(len(nodes)*2);bounds[0]=8.46-bounds[2]/2
            positions[node['node_id']]=bounds
            elements.append({'object_id':entity('object'),'type':'shape','role':'diagram','slot_key':f"diagram.node.{node['node_id']}",
                'data':{'node_id':node['node_id'],'shape_type':'rounded_rectangle','text':node['label']},'bounds':bounds,'font_size':18,
                'source_refs':node.get('evidence_refs',refs),'format':{'fill':'FFFFFF','border':dark,'color':dark,'margin':0.12,'paragraph_spacing':0}})
        # Connector endpoints are explicit and preserve edge direction; writers may use signed deltas.
        for index,edge in enumerate(edges):
            a=positions[edge['from']];b=positions[edge['to']]
            if abs((b[0]+b[2]/2)-(a[0]+a[2]/2)) > abs((b[1]+b[3]/2)-(a[1]+a[3]/2)):
                forward=b[0]>a[0]
                start=[a[0]+(a[2] if forward else 0),a[1]+a[3]/2]
                end=[b[0]+(0 if forward else b[2]),b[1]+b[3]/2]
            else:
                forward=b[1]>a[1]
                start=[a[0]+a[2]/2,a[1]+(a[3] if forward else 0)]
                end=[b[0]+b[2]/2,b[1]+(0 if forward else b[3])]
            x=min(start[0],end[0]);y=min(start[1],end[1]);w=max(abs(end[0]-start[0]),0.001);h=max(abs(end[1]-start[1]),0.001)
            elements.append({'object_id':entity('object'),'type':'connector','role':'diagram','slot_key':f'diagram.edge.{index}',
                'data':{'from_slot':f"diagram.node.{edge['from']}",'to_slot':f"diagram.node.{edge['to']}",'start':start,'end':end,
                        'label':edge.get('label',''),'relation':edge.get('relation'),'connector_type':'straight'},
                'bounds':[x,y,w,h],'font_size':16,'source_refs':edge.get('evidence_refs',refs),'format':{'color':dark}})
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


def generate_candidates(content,order,count,style,previous_kind=None,registry=None):
    """Build declared alternatives without replacing caller data or manufacturing semantics."""
    from uuid import UUID,uuid5
    from .schemas import ROOT
    kinds=[content['kind']] if content['kind']!='text' else ['editorial','columns','cards','cover','closing']
    catalog=json.loads((ROOT/'contracts/native-layout.catalog.json').read_text(encoding='utf-8'))
    candidates=[]
    for kind in kinds:
        reasons=[];score=40
        valid=not ((kind=='cards' and not 2<=len(content['body'])<=4) or (kind=='columns' and len(content['body'])<2))
        if kind=='cover':valid=order==0 and count>1;score=100;reasons.append('First text page: clear opening and side summary.')
        elif kind=='closing':valid=order==count-1 and count>1;score=95;reasons.append('Last text page: strong conclusion and preserved action points.')
        elif kind=='cards':score=75;reasons.append('Original items in individual editable panels; semantic relation is unchanged and not inferred.')
        elif kind=='columns':score=65;reasons.append('Original point sets balanced without rewriting.')
        elif kind in {'table','chart','image','diagram'}:score=100;reasons.append('Explicit source-grounded visual object; original data and topology retained.')
        else:reasons.append('Broad native text slot with every original paragraph.')
        if kind==previous_kind:score-=18;reasons.append('Adjacent repetition variation penalty.')
        definition=next((x for x in catalog['layouts'] if x['name']==kind),None)
        if definition is None:
            if kind not in {'image','diagram'}:
                raise TaskError('LAYOUT_TYPE_UNSUPPORTED','版式类型未登记，未替换。','LayoutSelector',['DEC-030'])
            required=['create_slide','add_text','add_notes',*(['add_image'] if kind=='image' else ['add_shape','add_connector'])]
            definition={'layout_id':'layout_'+str(uuid5(UUID('b229f8e4-2219-4ab9-ab60-1560c0a593b6'),kind)),'required_capabilities':required}
        entry={'candidate_id':entity('candidate'),'layout_id':definition['layout_id'],'layout':kind,'score':score,'reasons':reasons,'eligible':valid,'capacity_pass':False,
               'backend_support':{'backend':'PP-05','checked':registry is not None,'required_capabilities':definition['required_capabilities']},'rejection':None}
        if valid:
            try:
                from .layout_decisions import geometry,typography,visual_style,preflight
                elements,page_style=candidate(kind,content,order,count,style)
                geometry(elements);typography(elements,page_style);visual_style(elements,page_style)
                preflight(elements,registry)
                entry['capacity_pass']=True
            except TaskError as error:
                entry.update(eligible=False,rejection={'code':error.code,'details':error.details})
        else:entry['rejection']={'code':'LAYOUT_CONTENT_MISMATCH','reason':'Position/body cardinality mismatches declared layout.'}
        candidates.append(entry)
    return candidates


def choose(content,order,count,style,previous_kind=None,registry=None):
    """Execute DEC-030–038 subset; return compatible tuple and stable legacy slot keys."""
    from .layout_decisions import run_stage
    base={'content':content,'order':order,'page_count':count,'style':style,'previous_layout':previous_kind}
    decisions=[run_stage('DEC-030',base,registry)]
    candidates=decisions[0]['result']['candidates']
    selection=run_stage('DEC-031',{**base,'candidates':candidates},registry);decisions.append(selection)
    selected=selection['result'];kind=selected['selected_layout']
    elements,page_style=candidate(kind,content,order,count,style)
    for node in ('DEC-032','DEC-033','DEC-034','DEC-035','DEC-036','DEC-037','DEC-038'):
        decision=run_stage(node,{**base,'style':page_style,'elements':elements},registry);decisions.append(decision)
        if node=='DEC-036':
            images={item['slot_key']:item for item in decision['result']['images']}
            for element in elements:
                if element['type']=='image':
                    fit=images[element['slot_key']];element['bounds']=fit['bounds'];element['data']['crop']=fit['crop']
                    element['data']['fit_result']=fit
    trace={'version':VERSION,'input':base,'candidates':candidates,'selected':selected['selected'],
           'selected_layout':kind,'mechanism':selection['trace']['mechanism'],'decisions':decisions,
           'bindings':decisions[2]['result']['bindings'],'enhancements':decisions[7]['result'],
           'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'fallback':'Declared candidates only; reject all unsupported/capacity failures before native write.',
           'limitations':['Native subset, complete DEC-030–038 node and multi-backend/brand/template/RTL acceptance incomplete.']}
    return elements,page_style,trace
