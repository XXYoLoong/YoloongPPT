"""Executable DEC-030–038 stages for the declared native PP-05 subset.

Scores are deterministic layout heuristics, not probabilities or semantic truth.
Every stage preserves caller content and records its narrower capability boundary.
"""
import copy
import hashlib
import json
import math
import re
from pathlib import Path

from .artifacts import entity
from .errors import TaskError
from .writer import capacity

VERSION = 'native-layout-stages-2'
NODE_IDS = tuple(f'DEC-{n:03d}' for n in range(30, 39))
RESEARCH_MAP = {'P01': 'PPT Master', 'P02': 'PPTAgent / DeepPresenter', 'P03': 'Presenton',
                'P04': 'ai-agent-ppt', 'P05': 'Auto PPT Engine'}
RESEARCH_FILES = {'P01':'research/P01/project_decision_map.json','P02':'research/P02/decision-map.json',
                  'P03':'research/P03/decision-map.json','P04':'research/P04/decision-map.json','P05':'research/P05/ProjectDecisionMap.json'}


def research_mapping(node_id):
    from .schemas import ROOT
    result={}
    for project,name in RESEARCH_MAP.items():
        path=ROOT/RESEARCH_FILES[project]
        raw=path.read_bytes() if path.is_file() else None
        result[project]={'project':name,'evidence_path':RESEARCH_FILES[project],
            'evidence_sha256':hashlib.sha256(raw).hexdigest() if raw is not None else None,
            'stable_node_reference':'recorded' if raw is not None and node_id in raw.decode('utf-8') else 'unknown',
            'product_status':'research_reference_not_runtime'}
    return result


def fail(code, message, node, details=None):
    raise TaskError(code, message, 'LayoutDecisions', [node, 'SYS-010'], details or [])


def geometry(elements, width=13.333333, height=7.5):
    slots = set()
    for element in elements:
        slot = element.get('slot_key')
        if not slot or slot in slots:
            fail('LAYOUT_SLOT_DUPLICATE', '槽位标识缺失或重复。', 'DEC-033')
        slots.add(slot)
        b = element.get('bounds', [])
        if len(b) != 4 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in b) or min(b[:2]) < 0 or min(b[2:]) <= 0 or b[0]+b[2] > width+1e-5 or b[1]+b[3] > height+1e-5:
            fail('LAYOUT_GEOMETRY_INVALID', '对象必须具有页内有限正尺寸。', 'DEC-033', [{'slot_key': slot, 'bounds': b}])
    # Connector bounding rectangles may cross endpoints; other native slots may not overlap.
    boxes = [e for e in elements if e['type'] != 'connector']
    for i, a in enumerate(boxes):
        ax, ay, aw, ah = a['bounds']
        for b in boxes[i+1:]:
            bx, by, bw, bh = b['bounds']
            if min(ax+aw,bx+bw)-max(ax,bx)>0.015 and min(ay+ah,by+bh)-max(ay,by)>0.015:
                fail('LAYOUT_SLOT_OVERLAP', '内容槽位重叠，未隐式调整或覆盖。', 'DEC-033', [{'slots':[a['slot_key'],b['slot_key']]}])
    return {'elements': copy.deepcopy(elements), 'unit': 'inches', 'grid': 'declared deterministic native slots',
            'z_order': [e['slot_key'] for e in elements], 'alignment': 'explicit geometry',
            'connector_routing': 'explicit endpoints; advanced rerouting unsupported', 'overlap_check': 'passed'}


def typography(elements, style):
    if style.get('font') != 'Noto Sans CJK SC':
        fail('LAYOUT_FONT_UNSUPPORTED', '当前仅允许已安装并测量的 Noto Sans CJK SC；未替换字体。', 'DEC-034')
    measurements = []
    for element in elements:
        if element['type'] not in {'text', 'shape', 'table'}:
            continue
        if element.get('font_size', 0) < style.get('minimum_size', 16):
            fail('LAYOUT_FONT_TOO_SMALL', '字号低于用户最小字号。', 'DEC-034')
        texts = element.get('text', [])
        if element['type'] == 'shape': texts = [element['data']['text']]
        if any(re.search('[\u0590-\u08ff]', value) for value in texts):
            fail('LAYOUT_RTL_UNSUPPORTED', 'RTL 排版尚未执行验收；未按 LTR 静默写入。', 'DEC-034')
        f = element.get('format', {})
        if element['type'] == 'table':
            rows = [element['data']['columns'], *element['data']['rows']]
            if not rows[0] or any(len(row) != len(rows[0]) for row in rows):
                fail('LAYOUT_TABLE_INVALID', '表格必须保留完整等宽列。', 'DEC-034')
            m = [capacity([value], [0,0,element['bounds'][2]/len(rows[0]),element['bounds'][3]/len(rows)], element['font_size'], padding=.07, paragraph_spacing=0) for row in rows for value in row]
        else:
            m = capacity(texts, element['bounds'], element['font_size'], padding=f.get('margin',.12), paragraph_spacing=f.get('paragraph_spacing',10))
        measurements.append({'slot_key':element['slot_key'], 'font_size':element['font_size'], 'measurement':m})
    return {'font':style['font'], 'font_fallback':'none; unsupported font fails', 'autosize':False,
            'content_truncated':False, 'measurements':measurements, 'limitations':['RTL unavailable; glyph measurement does not replace rendered QA.']}


def luminance(color):
    if not isinstance(color,str) or not re.fullmatch('[0-9a-fA-F]{6}',color):
        fail('LAYOUT_COLOR_INVALID', '颜色必须是六位 RGB。', 'DEC-035')
    c = [int(color[i:i+2],16)/255 for i in (0,2,4)]
    c = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in c]
    return .2126*c[0]+.7152*c[1]+.0722*c[2]


def contrast(foreground, background):
    a,b = sorted([luminance(foreground),luminance(background)])
    return (b+.05)/(a+.05)


def visual_style(elements, style):
    unsupported = set(style) & {'gradient','shadow','transparency','effects'}
    if unsupported: fail('LAYOUT_EFFECT_UNSUPPORTED', '渐变/阴影/透明效果尚未接入当前写入路径。', 'DEC-035', [{'fields':sorted(unsupported)}])
    checks=[]
    for element in elements:
        f=element.get('format',{})
        if set(f)-{'fill','border','color','bold','margin','paragraph_spacing'}:
            fail('LAYOUT_EFFECT_UNSUPPORTED', '当前元素样式含未实现效果，未忽略。', 'DEC-035', [{'slot_key':element['slot_key'],'fields':sorted(set(f)-{'fill','border','color','bold','margin','paragraph_spacing'})}])
        for key in ('fill','border','color'):
            if key in f:luminance(f[key])
        if element['type'] in {'text','shape'}:
            foreground=f.get('color',style['foreground']); background=f.get('fill',style['background'])
            ratio=contrast(foreground,background); minimum=3 if element['font_size']>=24 or (element['font_size']>=18 and f.get('bold')) else 4.5
            if ratio+1e-8<minimum:
                fail('LAYOUT_CONTRAST_INSUFFICIENT', '文字对比度不足；未擅自修改品牌颜色。', 'DEC-035', [{'slot_key':element['slot_key'],'ratio':round(ratio,4),'minimum':minimum}])
            checks.append({'slot_key':element['slot_key'],'foreground':foreground,'background':background,'ratio':round(ratio,4),'minimum':minimum})
    return {'background':style['background'],'elements':copy.deepcopy(elements),'contrast':checks,
            'effects':'solid fill and stroke only; unsupported requested effects fail'}


def image_fit(image, bounds):
    width=image.get('width_px');height=image.get('height_px')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (width,height)):
        fail('IMAGE_DIMENSIONS_INVALID', '图片须提供实际探测的正像素尺寸。', 'DEC-036')
    mode=image.get('fit','contain')
    if mode not in {'contain','cover','crop'}:fail('IMAGE_FIT_UNSUPPORTED','不支持请求的图片适配方式。','DEC-036')
    if image.get('mask') not in (None,'rectangle'):fail('IMAGE_MASK_UNSUPPORTED','图片蒙版未实现，未替换。','DEC-036')
    focus=image.get('focal_point',[.5,.5])
    if not isinstance(focus,list) or len(focus)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in focus):
        fail('IMAGE_FOCAL_POINT_INVALID','焦点必须为两个 0–1 有限数。','DEC-036')
    crop=list(image.get('crop',[0,0,0,0]))
    if len(crop)!=4 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<1 for v in crop) or crop[0]+crop[2]>=1 or crop[1]+crop[3]>=1:
        fail('IMAGE_CROP_INVALID','裁切比例必须保留正尺寸图片。','DEC-036')
    if mode!='crop' and any(crop):fail('IMAGE_CROP_POLICY_CONFLICT','显式裁切必须使用 crop 模式。','DEC-036')
    if mode=='crop' and 'crop' not in image:fail('IMAGE_CROP_REQUIRED','crop 必须有用户明确的裁切比例。','DEC-036')
    x,y,w,h=bounds;cw=width*(1-crop[0]-crop[2]);ch=height*(1-crop[1]-crop[3])
    if mode=='contain':
        scale=min(w/cw,h/ch);dw,dh=cw*scale,ch*scale;placed=[x+(w-dw)/2,y+(h-dh)/2,dw,dh]
    else:
        placed=list(bounds);image_ratio=cw/ch;slot_ratio=w/h
        if image_ratio>slot_ratio:
            removed=1-slot_ratio/image_ratio;remaining=1-crop[0]-crop[2];crop[0]+=remaining*removed*focus[0];crop[2]+=remaining*removed*(1-focus[0])
        else:
            removed=1-image_ratio/slot_ratio;remaining=1-crop[1]-crop[3];crop[1]+=remaining*removed*focus[1];crop[3]+=remaining*removed*(1-focus[1])
    dpi=min(width*(1-crop[0]-crop[2])/placed[2],height*(1-crop[1]-crop[3])/placed[3])
    return {'mode':mode,'bounds':placed,'crop':crop,'focal_point':focus,'effective_dpi':round(dpi,2),
            'quality':'low_resolution' if dpi<96 else 'nominal_96dpi_or_above',
            'warning':'Below 96 DPI at display size; no fabricated upscaling.' if dpi<96 else None,
            'pixel_removal_explicit':mode!='contain'}


def preflight(elements, registry=None, backend='PP-05', requirements=None):
    names={'text':'add_text','table':'add_table','chart':'add_chart','image':'add_image','shape':'add_shape','connector':'add_connector'}
    if backend!='PP-05':fail('LAYOUT_BACKEND_UNAVAILABLE','当前布局执行只接入 PP-05，未替换指定后端。','DEC-038')
    if requirements and set(requirements)-{'live_edit','office_round_trip','pixel_exact_template'}:
        fail('LAYOUT_BACKEND_REQUIREMENT_UNKNOWN','后端约束未登记，未忽略。','DEC-038')
    if requirements and any(requirements.get(k) for k in ('live_edit','office_round_trip','pixel_exact_template')):
        fail('LAYOUT_BACKEND_REQUIREMENT_UNSUPPORTED','PP-05 尚未验证指定 Live/Office round-trip/像素模板保真要求。','DEC-038')
    calls=['create_slide','add_notes']
    for element in elements:
        if element['type'] not in names:fail('LAYOUT_OBJECT_UNSUPPORTED','元素类型未接入当前执行后端。','DEC-038')
        if names[element['type']] not in calls:calls.append(names[element['type']])
    checks=[];gaps=[]
    for name in calls:
        if registry is None:checks.append({'capability':name,'checked':False,'status':'untested'})
        else:
            try:
                item,implementation=registry.select(name)
                checks.append({'capability':name,'checked':True,'status':'available','capability_id':item['capability_id'],'implementation_id':implementation['implementation_id']})
            except TaskError as error:gaps.append({'capability':name,'code':error.code})
    if gaps:fail('LAYOUT_BACKEND_CAPABILITY_GAP','后端缺少必要能力，写入前停止。','DEC-038',gaps)
    return {'backend':backend,'required_capabilities':calls,'checks':checks,'preflight':'passed' if registry else 'untested',
            'limitations':['Availability is not complete object or Office round-trip acceptance; PP-01–04/06–09 not selected.']}


def run_stage(node_id, payload, registry=None, schemas=None):
    """Single-stage debug/API function; no model/network or artifact writes."""
    if node_id not in NODE_IDS:fail('LAYOUT_NODE_UNKNOWN','未登记版式节点。','DEC-030')
    if not isinstance(payload,dict):fail('LAYOUT_INPUT_INVALID','节点输入必须是对象。',node_id)
    required={'DEC-030':{'content','style'},'DEC-031':{'candidates'},'DEC-032':{'elements'},'DEC-033':{'elements'},
              'DEC-034':{'elements','style'},'DEC-035':{'elements','style'},'DEC-036':{'elements'},'DEC-037':set(),'DEC-038':{'elements'}}[node_id]
    if required-set(payload):fail('LAYOUT_INPUT_MISSING','节点缺少必需输入。',node_id,[{'fields':sorted(required-set(payload))}])
    if node_id=='DEC-030' and (type(payload.get('order',0)) is not int or type(payload.get('page_count',1)) is not int or not 0<=payload.get('order',0)<payload.get('page_count',1)):
        fail('LAYOUT_PAGE_ORDER_INVALID','页序必须位于总页数内。',node_id)
    if 'elements' in payload and (not isinstance(payload['elements'],list) or not payload['elements']):fail('LAYOUT_ELEMENTS_REQUIRED','几何阶段必须有实际元素。',node_id)
    if schemas:schemas.validate('layout-stage-node.schema.json',{'node_id':node_id,'input':payload})
    p=copy.deepcopy(payload);elements=p.get('elements',[]);style=p.get('style',{})
    if node_id=='DEC-030':
        from .layouts import generate_candidates
        result={'candidates':generate_candidates(p['content'],p.get('order',0),p.get('page_count',1),style,p.get('previous_layout'),registry)}
    elif node_id=='DEC-031':
        candidates=p.get('candidates',[]);eligible=[c for c in candidates if c['eligible'] and c['capacity_pass']]
        if not eligible:fail('LAYOUT_CAPACITY_UNSUPPORTED','所有候选不满足容量/内容/后端，未裁剪或缩小。',node_id,candidates)
        selected=max(eligible,key=lambda c:c['score']);result={'selected':selected['candidate_id'],'selected_layout':selected['layout'],'selected_candidate':selected,'tie_break':'stable declared catalog order'}
    elif node_id=='DEC-032':
        result={'bindings':[{'slot_key':e['slot_key'],'object_id':e['object_id'],'role':e['role'],'content_type':e['type'],'source_refs':e['source_refs'],'required':True,'overflow':'reject'} for e in elements],
                'notes':p.get('content',{}).get('notes',''),'evidence_refs':p.get('content',{}).get('evidence_refs',[]),'unmapped_fields':[]}
    elif node_id=='DEC-033':result=geometry(elements,p.get('width_inches',13.333333),p.get('height_inches',7.5))
    elif node_id=='DEC-034':result=typography(elements,style)
    elif node_id=='DEC-035':result=visual_style(elements,style)
    elif node_id=='DEC-036':result={'images':[{'slot_key':e['slot_key'],**image_fit(e['data'],e['bounds'])} for e in elements if e['type']=='image']}
    elif node_id=='DEC-037':
        requested=p.get('enhancements',{})
        if set(requested)-{'notes','animation','transition','progressive_reveal'}:fail('LAYOUT_ENHANCEMENT_UNKNOWN','增强字段未登记，未忽略。',node_id)
        if any(requested.get(k) not in (None,False,'none') for k in ('animation','transition','progressive_reveal')):fail('LAYOUT_ENHANCEMENT_UNSUPPORTED','动画/切换/渐进揭示尚未接入，未忽略请求。',node_id)
        result={'notes':requested.get('notes',p.get('content',{}).get('notes','')),'animation':'none','transition':'none','progressive_reveal':False,'reason':'Default static deck; no unsupported enhancement is silently discarded.'}
    else:result=preflight(elements,registry,p.get('backend','PP-05'),p.get('backend_requirements'))
    output={'node_id':node_id,'result':result,'trace':{'trace_id':p.get('trace_id',entity('trace')),'version':VERSION,'input':p,
        'mechanism':{'DEC-030':'Declared content types and geometric capacity; image ratio included in explicit fit.', 'DEC-031':'Heuristic hierarchy, capacity, contrast, and adjacent variation; no semantic score claim.', 'DEC-032':'Exact content-to-native slots, original notes and citations retained.', 'DEC-033':'Finite page geometry, non-overlap, explicit connector endpoints and z-order.', 'DEC-034':'Installed Noto glyph measurement and fixed minimum font; no truncation.', 'DEC-035':'Solid native RGB and computed text contrast; unsupported effects reject.', 'DEC-036':'Caller-approved contain/cover/crop and actual dimensions; no subject inference.', 'DEC-037':'Explicit static default, original notes, requested unsupported animation fails.', 'DEC-038':'Exact registered PP-05 capabilities/platform versions; required gap rejects.'}[node_id],
        'constraint':'Preserve source text, source refs, dimensions, explicit policy and stable slot keys.',
        'fallback':'Declared next layout candidate only; no semantic rewrite, data removal, font substitution or backend substitution.',
        'research_mapping':research_mapping(node_id),
        'product_implementation':'Independent declared PP-05 python-pptx runtime, not copied upstream application code.',
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'status':'partial','limitations':['Native 16:9 text/table/category chart/image/basic shape/connector subset; full node, brand/template/RTL and system acceptance remain incomplete.']}}
    if schemas:schemas.validate('layout-stage-node.schema.json',output)
    return output
