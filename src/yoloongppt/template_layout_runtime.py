"""TPL-004/006/008/015/016: measured bindings to real native placeholders."""
import copy
import hashlib
import io
import json
import math
import subprocess
import zipfile
from xml.etree import ElementTree as ET

from .errors import TaskError
from .artifacts import entity

VERSION = 'template-layout-runtime-1'
EMU = 914400
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
POLICY_KEYS = {'version', 'layout_part', 'layout_by_kind', 'field_map', 'fallback_layouts', 'typography', 'brand', 'preserve_master_style'}


def fail(code, message, details=None):
    raise TaskError(code, message, 'TemplateLayoutRuntime', ['TPL-004', 'TPL-006', 'TPL-008', 'TPL-015', 'TPL-016', 'AC-006'], details or [])


def policy_value(policy):
    value = copy.deepcopy(policy or {})
    from .schemas import ROOT
    from jsonschema import Draft202012Validator
    schema = json.loads((ROOT / 'contracts/template-brand-policy.schema.json').read_text('utf-8'))
    if list(Draft202012Validator(schema).iter_errors(value)):
        fail('TEMPLATE_POLICY_INVALID', '模板策略不符合字段/类型契约。')
    if not isinstance(value, dict) or set(value) - POLICY_KEYS:
        fail('TEMPLATE_POLICY_INVALID', '模板策略有未知字段或不是对象。')
    if value.get('version', 'template-policy-1') != 'template-policy-1' or value.get('preserve_master_style', True) is not True:
        fail('TEMPLATE_POLICY_INVALID', '当前模板路径要求保持原生母版样式。')
    for key in ('layout_by_kind', 'field_map', 'typography', 'brand'):
        if not isinstance(value.get(key, {}), dict): fail('TEMPLATE_POLICY_INVALID', '模板策略映射必须为对象。')
    if not isinstance(value.get('fallback_layouts', []), list) or any(not isinstance(x, str) for x in value.get('fallback_layouts', [])):
        fail('TEMPLATE_POLICY_INVALID', 'fallback 必须是明确布局 part 的列表。')
    value.setdefault('version', 'template-policy-1'); value.setdefault('preserve_master_style', True)
    return value


def geometry(slot):
    b = slot.get('bounds')
    if not b: fail('TEMPLATE_SLOT_BOUNDS_UNRESOLVED', '槽位没有可解析几何。')
    return [b[k] / EMU for k in ('x_emu', 'y_emu', 'width_emu', 'height_emu')]


def _rect(rect):
    if not isinstance(rect, list) or len(rect) != 4 or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in rect) or min(rect[2:]) <= 0:
        fail('TEMPLATE_BRAND_POLICY_INVALID', '品牌区域必须是四个有限英寸数值，宽高须为正。')
    return rect


def _overlap(a, b):
    return min(a[0]+a[2], b[0]+b[2]) > max(a[0], b[0])+1e-6 and min(a[1]+a[3], b[1]+b[3]) > max(a[1], b[1])+1e-6


def locks_for(record, policy):
    brand = policy.get('brand', {})
    if set(brand) - {'locked_objects', 'safe_areas', 'content_area', 'locked_tokens'}:
        fail('TEMPLATE_BRAND_POLICY_INVALID', '未知品牌锁字段不能忽略。')
    pack = record['template_pack']; objects = []
    for item in brand.get('locked_objects', []):
        if not isinstance(item, dict) or not item.get('part') or set(item)-{'part', 'shape_id', 'name'} or not (item.get('shape_id') or item.get('name')):
            fail('TEMPLATE_BRAND_POLICY_INVALID', '品牌锁需明确 part 及 shape_id/name。')
        parents = [x for x in pack['masters']+pack['layouts'] if x['part'] == item['part']]
        matches = [s for x in parents for s in x['shapes'] if ('shape_id' not in item or s['shape_id'] == str(item['shape_id'])) and ('name' not in item or s['name'] == item['name'])]
        if len(matches) != 1: fail('TEMPLATE_BRAND_OBJECT_UNKNOWN', '品牌对象选择器没有唯一真实对象。', [item])
        s = matches[0]
        objects.append({'part': item['part'], 'shape_id': s['shape_id'], 'name': s['name'], 'placeholder_index': s['placeholder_index'],
                        'bounds': s['bounds'], 'xml_sha256': hashlib.sha256(s['raw_xml'].encode()).hexdigest()})
    areas = [_rect(x) for x in brand.get('safe_areas', [])]
    area = _rect(brand['content_area']) if 'content_area' in brand else None
    tokens = brand.get('locked_tokens', {})
    if not isinstance(tokens, dict) or set(tokens)-{'font', 'foreground', 'background', 'accent'} or any(not isinstance(v, str) for v in tokens.values()):
        fail('TEMPLATE_BRAND_POLICY_INVALID', '品牌 token 锁需明确字体/颜色值。')
    return {'preserve_master_style': True, 'objects': objects, 'safe_areas': areas, 'content_area': area, 'tokens': tokens,
            'protected_parts': record['template_pack'].get('preservation', {}).get('parts', [])}


def _font_available(font):
    matched = subprocess.run(['fc-match', '-f', '%{family}\n%{file}', font], capture_output=True, text=True, check=True).stdout
    family, font_file = matched.split('\n', 1)
    if font.casefold() not in [x.strip().casefold() for x in family.split(',')]:
        fail('TEMPLATE_FONT_UNAVAILABLE', '模板字体未安装，须调用者显式指定可用字体；未静默替换。', [{'requested_font': font, 'matched_family': family}])
    return font_file


def _capacity(texts, bounds, size, font_name, padding=0, paragraph_spacing=0):
    from PIL import ImageFont
    font = ImageFont.truetype(_font_available(font_name), int(size*4/3)); width = (bounds[2]-padding*2)*96
    height = (bounds[3]-padding*2)*96; lines = 0
    if min(width, height) <= 0: fail('TEMPLATE_CAPACITY_EXCEEDED', '槽位没有可用文本空间。')
    for text in texts:
        current = 0; lines += 1
        for char in str(text):
            if char == '\n': current=0; lines+=1; continue
            advance = font.getlength(char)
            if current+advance > width: lines+=1; current=advance
            else: current+=advance
    line_height=max(size*4/3*1.25,sum(font.getmetrics()))
    used = lines*line_height+max(0,len(texts)-1)*paragraph_spacing*4/3
    if used > height: fail('TEMPLATE_CAPACITY_EXCEEDED', '内容超过实际字体测量容量；未裁剪、缩小或覆盖。', [{'estimated_height_px': round(used), 'available_height_px': round(height)}])
    return {'status':'measured', 'font':font_name, 'estimated_lines':lines, 'line_height_px':line_height, 'font_metrics_px':list(font.getmetrics()), 'estimated_height_px':round(used), 'available_height_px':round(height), 'measurement':'actual installed font glyph advances and max(legacy height, ascent+descent); conservative; render QA pending'}


def _typography(record, layout, slot, role, policy, style):
    override = policy.get('typography', {})
    if set(override)-{'font', 'sizes'}: fail('TEMPLATE_POLICY_INVALID', '未知 typography 字段。')
    local = ET.fromstring(slot['style_xml']); props = local.find('.//a:defRPr', NS)
    if props is None: props = local.find('.//a:rPr', NS)
    master = next((x for x in record['template_pack']['masters'] if x['part'] == layout['master_part']), None)
    inherited_props = None
    if master and master.get('text_styles_xml'):
        tx = ET.fromstring(master['text_styles_xml']); tag = 'titleStyle' if role == 'title' else 'bodyStyle'
        inherited_props = tx.find('p:'+tag+'/a:lvl1pPr/a:defRPr', NS)
    chain=[x for x in (props,inherited_props) if x is not None]
    size=next((float(x.get('sz'))/100 for x in chain if x.get('sz')),None)
    size = override.get('sizes', {}).get(role, size)
    if isinstance(size, bool) or not isinstance(size, (int, float)) or not math.isfinite(size) or size < 16:
        fail('TEMPLATE_FONT_SIZE_INVALID', '原生模板文本字号须为至少16pt，不能自动缩小。')
    font = override.get('font')
    for source_props in chain:
        if font: break
        ea = source_props.find('a:ea', NS); latin = source_props.find('a:latin', NS)
        font = ea.get('typeface') if ea is not None and ea.get('typeface') else latin.get('typeface') if latin is not None else None
    if not font or font.startswith('+'):
        theme_role = 'majorFont' if role == 'title' else 'minorFont'
        fonts = [x for t in record['template_pack']['themes'] for x in t['fonts'].get(theme_role, [])]
        font = next((x.get('typeface') for x in fonts if x['kind'] == 'ea' and x.get('typeface')), None) or next((x.get('typeface') for x in fonts if x['kind'] == 'latin'), None)
    if not font: fail('TEMPLATE_FONT_UNRESOLVED', '模板字体无法解析，不能假定与主机默认字体相同。')
    font_file = _font_available(font)
    color = None
    for source_props in chain:
        if color: break
        rgb = source_props.find('a:solidFill/a:srgbClr', NS); scheme = source_props.find('a:solidFill/a:schemeClr', NS)
        if rgb is not None: color = rgb.get('val')
        elif scheme is not None:
            token = scheme.get('val'); cmap = master.get('color_map', {}) if master else {}
            color = record['design_tokens']['theme_colors'].get(cmap.get(token, token))
    return {'font': font, 'font_file': font_file, 'font_size': size, 'color': color or style['foreground'],
            'provenance': 'explicit caller typography' if override else 'native layout/master/theme inheritance'}


def choose(record, content, style, policy=None, order=0, count=1):
    if content.get('images') or content.get('kind') == 'gallery':
        fail('TEMPLATE_GALLERY_SLOTS_UNSUPPORTED', '指定模板尚不支持多原生图片槽位绑定；未取第一张图、改为单图或通用版式。')
    if content.get('kind') == 'image' and not isinstance(content.get('image'), dict):
        fail('TEMPLATE_IMAGE_REQUIRED', '单图模板页面缺少已解析 image 对象，未从其他字段猜测图片。')
    policy = policy_value(record.get('policy') if policy is None else policy)
    if record.get('policy') and policy != record['policy']:
        fail('TEMPLATE_REGISTERED_POLICY_CHANGED', '已登记模板策略不可被调用时覆盖；请重新登记新的策略版本。')
    locks = locks_for(record, policy)
    for key, value in locks['tokens'].items():
        effective = policy.get('typography', {}).get('font', style.get(key)) if key == 'font' else style.get(key)
        if effective != value: fail('TEMPLATE_BRAND_TOKEN_CONFLICT', '请求样式与明确品牌 token 锁冲突。', [{'token': key, 'locked': value, 'requested': effective}])
    kind = content['kind']
    if kind in {'diagram', 'gallery'}: fail('TEMPLATE_CONTENT_UNSUPPORTED', '当前模板没有可执行的原生图示/图库槽位绑定，未改为图片或通用布局。')
    needs = [('title', 'text', [content['title']])]
    if content.get('body'): needs.append(('body', 'text', list(content['body'])))
    if kind in {'image', 'table', 'chart'}: needs.append(('asset' if kind == 'image' else 'data', kind, content[kind]))
    layouts = record['template_pack']['layouts']; primary = policy.get('layout_by_kind', {}).get(kind, policy.get('layout_part'))
    if primary and not any(x['part'] == primary for x in layouts): fail('TEMPLATE_LAYOUT_UNKNOWN', '指定原生 layout part 不存在。')
    fallbacks = policy.get('fallback_layouts', [])
    if any(not any(x['part'] == part for x in layouts) for part in fallbacks): fail('TEMPLATE_FALLBACK_UNKNOWN', '指定 fallback layout 不存在。')
    pool = [x for x in layouts if x['part'] == primary] if primary else sorted(layouts, key=lambda x: (len(x['slots']), x['part']))
    if primary: pool += [x for part in fallbacks for x in layouts if x['part'] == part and part != primary]
    decisions = []; selected = None
    for layout in pool:
        elements = []; used = set(); bindings = []; page_style = copy.deepcopy(style)
        try:
            for role, typ, value in needs:
                mapping = policy.get('field_map', {}).get(role)
                slots = [s for s in layout['slots'] if s['bounds'] and s['placeholder_index'] not in used]
                if mapping is not None:
                    slots = [s for s in slots if (isinstance(mapping, int) and not isinstance(mapping, bool) and s['placeholder_index'] == mapping) or (isinstance(mapping, str) and s['name'] == mapping)]
                    if len(slots) != 1: fail('TEMPLATE_FIELD_MISMATCH', '显式字段映射未匹配唯一原生槽位。', [{'role': role, 'mapping': mapping, 'layout': layout['part']}])
                else:
                    roles = {'title': {'title', 'ctrTitle'}, 'body': {'body', 'subTitle', 'obj'}, 'asset': {'pic'}, 'data': {'tbl'} if typ == 'table' else {'chart'}}[role]
                    slots = [s for s in slots if s['role'] in roles]
                    if len(slots) != 1: fail('TEMPLATE_FIELD_MISMATCH', '统一角色没有唯一模板字段，须明确 field_map。', [{'role': role, 'candidate_indices': [s['placeholder_index'] for s in slots]}])
                slot = slots[0]
                allowed = {'image': {'pic'}, 'table': {'tbl'}, 'chart': {'chart'}}
                if typ not in slot['content_types'] or typ in allowed and slot['role'] not in allowed[typ]:
                    fail('TEMPLATE_SLOT_TYPE_UNSUPPORTED', '原生槽位不支持请求对象的插入接口，未覆盖为浮动对象。')
                if any(x['part'] == layout['part'] and x['placeholder_index'] == slot['placeholder_index'] or x['part'] == layout['master_part'] and slot.get('inherited_shape_ref') == f"{x['part']}#shape={x['shape_id']}" for x in locks['objects']):
                    fail('TEMPLATE_BRAND_OBJECT_LOCKED', '内容映射命中已锁定品牌对象。')
                bounds = geometry(slot)
                if any(_overlap(bounds, area) for area in locks['safe_areas']): fail('TEMPLATE_BRAND_SAFE_AREA_CONFLICT', '槽位与明确品牌安全区相交，不能移动或重绘。')
                area = locks['content_area']
                if area and not (bounds[0] >= area[0]-1e-6 and bounds[1] >= area[1]-1e-6 and bounds[0]+bounds[2] <= area[0]+area[2]+1e-6 and bounds[1]+bounds[3] <= area[1]+area[3]+1e-6): fail('TEMPLATE_BRAND_SAFE_AREA_CONFLICT', '槽位超出品牌内容区。')
                typography = _typography(record, layout, slot, role, policy, style)
                if typ != 'text': typography['font_size']=16
                if 'font' in locks['tokens'] and typography['font'] != locks['tokens']['font']: fail('TEMPLATE_BRAND_TOKEN_CONFLICT', '继承字体违反品牌字体锁。')
                if 'foreground' in locks['tokens'] and typography['color'].upper() != locks['tokens']['foreground'].upper(): fail('TEMPLATE_BRAND_TOKEN_CONFLICT', '继承文字颜色违反品牌颜色锁。')
                if elements and page_style['font'] != typography['font']: fail('TEMPLATE_MULTIPLE_FONTS_UNSUPPORTED', '页面各槽位字体不同，当前单页样式不能隐式统一。')
                page_style['font'] = typography['font']
                measurement = {'status': 'native_geometry_checked', 'render_qa': 'pending'}
                if typ == 'text':
                    measurement = _capacity(value, bounds, typography['font_size'], typography['font'])
                elif typ == 'table':
                    rows = [value['columns'], *value['rows']]; cols = len(value['columns'])
                    if not cols or any(len(row) != cols for row in rows): fail('TEMPLATE_TABLE_FIELDS_MISMATCH', '表格列数不一致。')
                    for row in rows:
                        for cell in row: _capacity([cell], [0, 0, bounds[2]/cols, bounds[3]/len(rows)], 16, typography['font'], padding=.07)
                    measurement.update(rows=len(rows), columns=cols)
                elif typ == 'image':
                    original_bounds = list(bounds)
                    if value.get('fit', 'contain') == 'contain':
                        scale = min(bounds[2]/value['width_px'], bounds[3]/value['height_px']); width=value['width_px']*scale; height=value['height_px']*scale
                        bounds = [bounds[0]+(bounds[2]-width)/2, bounds[1]+(bounds[3]-height)/2, width, height]
                        value = {**value, 'crop':[0,0,0,0]}
                    elif value.get('fit') not in {'cover','crop'} or 'crop' not in value:
                        fail('TEMPLATE_IMAGE_FIT_UNSUPPORTED', 'cover/crop 必须有明确已解析裁剪，不能接受默认裁剪。')
                binding = {'native_layout_part': layout['part'], 'placeholder_index': slot['placeholder_index'], 'placeholder_name': slot['name'], 'preserve_master_style': True,
                           'native_role': slot['role'], 'typography': typography, 'capacity': measurement}
                if typ == 'image': binding['original_slot_bounds'] = original_bounds
                element = {'object_id': entity('object'), 'type': typ, 'role': role,
                           'slot_key': role, 'bounds': bounds, 'font_size': typography['font_size'], 'source_refs': content.get('evidence_refs', []),
                           'template_binding': binding, 'locked': False}
                if typ == 'text': element.update(text=value, format={'color': typography['color'], 'margin': 0, 'paragraph_spacing': 0})
                else: element['data'] = copy.deepcopy(value)
                if typ == 'image': element['source_refs'] = value.get('source_refs', element['source_refs'])
                elements.append(element); used.add(slot['placeholder_index']); bindings.append({'role': role, **binding})
            selected = (layout, elements, bindings, page_style)
            decisions.append({'layout_part': layout['part'], 'eligible': True, 'selected': True, 'reason': 'all required content mapped and measured in real native slots'})
            break
        except TaskError as error:
            decisions.append({'layout_part': layout['part'], 'eligible': False, 'selected': False, 'reason': error.code, 'details': error.details})
            if error.code in {'TEMPLATE_BRAND_TOKEN_CONFLICT', 'TEMPLATE_BRAND_POLICY_INVALID'}: raise
            if error.code == 'TEMPLATE_FONT_UNAVAILABLE' and not (primary and fallbacks): raise
    if selected is None: fail('TEMPLATE_NO_COMPATIBLE_LAYOUT', '没有符合内容、容量与品牌锁的原生布局；未改用通用模板。', decisions)
    layout, elements, bindings, page_style = selected
    from .upstream_templates import analyze_upstream_template, validate_native_slot_content
    upstream_analysis=analyze_upstream_template(record['template_pack'],source=record['source'])
    upstream_checks=validate_native_slot_content(upstream_analysis,layout['part'],{
        element['template_binding']['placeholder_index']:element['text'] if isinstance(element['text'],str) else '\n'.join(element['text'])
        for element in elements if element['type']=='text'})
    fallback = bool(primary and layout['part'] != primary)
    selection = {'version': VERSION, 'template_id': record['template_id'], 'selected_layout': layout['part'], 'bindings': bindings, 'decisions': decisions,
                 'fallback': {'used': fallback, 'requested_layout': primary, 'selected_layout': layout['part'], 'reason': decisions[:-1] if fallback else [], 'authorization': 'explicit caller fallback_layouts' if fallback else None},
                 'capacity_status': 'measured_conservative_render_pending', 'upstream_validation':upstream_checks, 'system_acceptance': 'not_claimed'}
    return {'elements': elements, 'page_style': page_style, 'selection': selection, 'native_layout_part': layout['part'], 'locks': locks}


def create_slide(presentation, spec):
    binding = spec.get('layout', {}).get('template_binding')
    if not binding: return None
    part = binding.get('native_layout_part')
    matches = [l for m in presentation.slide_masters for l in m.slide_layouts if str(l.part.partname).lstrip('/') == str(part).lstrip('/')]
    if len(matches) != 1 or binding.get('preserve_master_style', True) is not True: fail('TEMPLATE_LAYOUT_UNAVAILABLE', '执行时没有唯一绑定布局或要求破坏母版。')
    slide = presentation.slides.add_slide(matches[0])
    slide._yoloong_template_locks = copy.deepcopy(binding.get('locks', {}))
    # Original native placeholders (including intentional unfilled fields) remain.
    return slide


def bind_placeholder(slide, element):
    binding = element.get('template_binding')
    if not binding: return None
    if str(slide.slide_layout.part.partname).lstrip('/') != str(binding.get('native_layout_part')).lstrip('/'):
        fail('TEMPLATE_BINDING_LAYOUT_CHANGED', '执行页面与选定原生布局不一致。')
    try: placeholder = slide.placeholders[binding['placeholder_index']]
    except (KeyError, TypeError): fail('TEMPLATE_PLACEHOLDER_UNAVAILABLE', '目标占位符没有实例化，未新建浮动对象。')
    if element.get('locked') or any(x.get('part') == str(slide.slide_layout.part.partname).lstrip('/') and x.get('placeholder_index') == binding['placeholder_index'] for x in getattr(slide, '_yoloong_template_locks', {}).get('objects', [])):
        fail('TEMPLATE_BRAND_OBJECT_LOCKED', '执行试图填充品牌锁定对象。')
    actual = [placeholder.left/EMU, placeholder.top/EMU, placeholder.width/EMU, placeholder.height/EMU]
    expected = binding.get('original_slot_bounds', element['bounds'])
    if any(abs(a-b) > .002 for a, b in zip(actual, expected)): fail('TEMPLATE_BINDING_GEOMETRY_CHANGED', '执行几何与真实占位符不同，拒绝自动移动。')
    fit = element['bounds']
    if fit[0]<actual[0]-.002 or fit[1]<actual[1]-.002 or fit[0]+fit[2]>actual[0]+actual[2]+.002 or fit[1]+fit[3]>actual[1]+actual[3]+.002:
        fail('TEMPLATE_BINDING_GEOMETRY_CHANGED', '图片实际 fit box 超出原生槽位。')
    typ = element['type']
    supported = placeholder.has_text_frame if typ == 'text' else callable(getattr(placeholder, {'image': 'insert_picture', 'table': 'insert_table', 'chart': 'insert_chart'}.get(typ, ''), None))
    if not supported: fail('TEMPLATE_SLOT_TYPE_UNSUPPORTED', '目标 placeholder 没有所需原生填写接口。')
    return placeholder


def preserved_part_names(names):
    protected={x for x in names if x.startswith(('ppt/slideMasters/','ppt/slideLayouts/','ppt/theme/','ppt/media/'))}
    known=('ppt/slides/','ppt/notesSlides/','ppt/notesMasters/','ppt/charts/','ppt/embeddings/','docProps/')
    editable={'[Content_Types].xml','_rels/.rels','ppt/presentation.xml','ppt/_rels/presentation.xml.rels','ppt/presProps.xml','ppt/viewProps.xml','ppt/tableStyles.xml'}
    return protected | {x for x in names if x not in editable and not x.startswith(known) and x not in protected}


def serialize_package_xml(node):
    """OPC packaging XML uses default namespace for LibreOffice compatibility.

    Do not mutate ElementTree's process-global namespace registry: requests can
    execute concurrently. Namespace-local lxml serialization keeps native design
    parts untouched and avoids ns0-prefixed ContentTypes rejected by LO 7.4.
    """
    from lxml import etree
    namespace=node.tag.split('}',1)[0].lstrip('{')
    root=etree.Element(node.tag,dict(node.attrib),nsmap={None:namespace})
    for child in node:
        if len(child): fail('TEMPLATE_PACKAGE_XML_UNSUPPORTED','OPC关系/类型有未知嵌套结构，拒绝静默重写。')
        element=etree.SubElement(root,child.tag,dict(child.attrib));element.text=child.text
    return etree.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)


def preserve_package(original, generated):
    """Keep immutable native design and unknown parts byte-for-byte after OOXML save."""
    from .input_formats import package, xml
    rel_ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
    ct_ns = 'http://schemas.openxmlformats.org/package/2006/content-types'
    with package(original, 'ppt/presentation.xml') as before, package(generated, 'ppt/presentation.xml') as after:
        old = {x: before.read(x) for x in before.namelist()}; new = {x: after.read(x) for x in after.namelist()}
    protected = preserved_part_names(old); unknown=set()
    for x in protected | unknown: new[x] = old[x]
    # Restore unknown relationships on surviving generated parts. Identity collisions
    # are rejected rather than rewriting unknown XML reference semantics.
    for name in old:
        if not name.endswith('.rels') or name in protected | unknown or name not in new: continue
        left = xml(old[name]); right = xml(new[name]); changed = False
        for rel in left:
            if rel.get('Type', '').rsplit('/', 1)[-1] in {'slide', 'slideLayout', 'slideMaster', 'notesSlide', 'notesMaster', 'theme', 'image', 'chart', 'package', 'core-properties', 'extended-properties'}: continue
            equal = next((r for r in right if r.attrib == rel.attrib), None)
            if equal is not None: continue
            if any(r.get('Id') == rel.get('Id') for r in right): fail('TEMPLATE_UNKNOWN_RELATIONSHIP_COLLISION', '未知 OOXML 关系ID冲突，不能静默丢弃。')
            right.append(copy.deepcopy(rel)); changed = True
        if changed: new[name] = serialize_package_xml(right)
    left = xml(old['[Content_Types].xml']); right = xml(new['[Content_Types].xml']); existing = {(x.tag, x.get('PartName') or x.get('Extension')) for x in right}
    for entry in left:
        key = (entry.tag, entry.get('PartName') or entry.get('Extension'))
        part = entry.get('PartName', '').lstrip('/')
        if key not in existing and (not part or part in new): right.append(copy.deepcopy(entry)); existing.add(key)
    new['[Content_Types].xml'] = serialize_package_xml(right)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, raw in new.items(): archive.writestr(name, raw)
    return output.getvalue()
