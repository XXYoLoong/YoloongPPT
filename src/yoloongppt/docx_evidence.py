"""IN-003/016: native DOCX evidence; no rendering, network or semantic inference.

The caller owns package validation and the original source-byte snapshot. This
module enriches its existing blocks without changing any extracted text. Images
become nontext segments tied to actual package bytes, never invented text facts.
"""
import copy
import hashlib
import re
from collections import defaultdict
from xml.etree import ElementTree as ET

from .assets import inspect_image
from .errors import TaskError

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
V = 'urn:schemas-microsoft-com:vml'
O = 'urn:schemas-microsoft-com:office:office'
B = 'http://schemas.openxmlformats.org/officeDocument/2006/bibliography'
N = {'w': W, 'r': R, 'a': A, 'wp': WP, 'v': V, 'o': O, 'b': B}
UNIT = re.compile(r'(?<![A-Za-z])(?:kWh|MWh|kW|MW|kg|km|cm|mm|m²|m³|万元|亿元|千瓦时|千瓦|平方米|立方米|美元|元|吨|小时|分钟|人|台|件|%|％)(?![A-Za-z])')


def _id(kind, part, path):
    return 'docx_' + kind + '_' + hashlib.sha256((part + '#' + path).encode()).hexdigest()[:24]


def _warn(warnings, code, part, path, message):
    warnings.append({'code': code, 'part': part, 'xml_path': path, 'message': message,
                     'requirement_ids': ['IN-003', 'IN-016']})


def _paths(root):
    paths = {}; parents = {}
    def label(tag):
        namespace, local = tag[1:].split('}', 1) if tag.startswith('{') else ('', tag)
        prefix = next((k for k, v in N.items() if v == namespace), None)
        return (prefix + ':' + local) if prefix else ('{' + namespace + '}' + local if namespace else local)
    def walk(node, path):
        paths[node] = path
        count = defaultdict(int)
        for child in node:
            count[child.tag] += 1; parents[child] = node
            walk(child, path + '/' + label(child.tag) + '[' + str(count[child.tag]) + ']')
    walk(root, '/' + label(root.tag) + '[1]')
    return paths, parents


def _paragraph_text(node):
    return ''.join((child.text or '') if child.tag == '{' + W + '}t' else '\t' if child.tag == '{' + W + '}tab' else '\n'
                   for child in node.iter() if child.tag in {'{' + W + '}t', '{' + W + '}tab', '{' + W + '}br'})


def _units(text):
    return [{'raw_text': match.group(), 'start_char': match.start(), 'end_char': match.end(),
             'status': 'candidate', 'meaning': 'unknown', 'offset_unit': 'unicode_code_points'} for match in UNIT.finditer(text)]


def _int(node, attr, default, warnings, part, path, minimum=0):
    value = node.get('{' + W + '}' + attr) if node is not None else None
    if node is None:return default
    if value is None:
        _warn(warnings, 'DOCX_GRID_VALUE_INVALID', part, path, '网格/大纲属性缺少数值；未补入默认值。')
        return None
    try:
        result = int(value)
        if result < minimum or result > 4096:raise ValueError
        return result
    except ValueError:
        _warn(warnings, 'DOCX_GRID_VALUE_INVALID', part, path, '表格网格数值无效；未猜测其逻辑位置。')
        return None


def _bibliography(archive, xml):
    result = defaultdict(list)
    for part in archive.namelist():
        if not re.fullmatch(r'customXml/item\d+\.xml', part):continue
        root = xml(archive.read(part))
        for source in root.iter('{' + B + '}Source'):
            tag = source.find('b:Tag', N)
            if tag is not None and tag.text:
                result[tag.text].append({'part': part, 'tag': tag.text,
                                        'fields': [{'name': child.tag.rsplit('}', 1)[-1], 'text': ''.join(child.itertext())} for child in source]})
    return result


def _fields(node, paths):
    """Keep separate complex fields; concatenating all instrText would mix citations."""
    result = []; stack = []
    for child in node.iter():
        if child.tag == '{' + W + '}fldSimple':
            result.append({'instruction': child.get('{' + W + '}instr', ''), 'xml_path': paths[child],
                           'display_text': _paragraph_text(child), 'field_kind': 'simple'})
        elif child.tag == '{' + W + '}fldChar':
            kind = child.get('{' + W + '}fldCharType')
            if kind == 'begin':stack.append({'instruction': '', 'xml_path': paths[child], 'display_text': '', 'field_kind': 'complex', 'display': False})
            elif kind == 'separate' and stack:stack[-1]['display'] = True
            elif kind == 'end' and stack:
                field = stack.pop(); field.pop('display'); result.append(field)
        elif child.tag == '{' + W + '}instrText' and stack:stack[-1]['instruction'] += child.text or ''
        elif child.tag == '{' + W + '}t' and stack and stack[-1]['display']:stack[-1]['display_text'] += child.text or ''
    for field in stack:
        field.pop('display'); field['status'] = 'unclosed'; result.append(field)
    return result


def enhance_docx(raw, document, segments):
    """Return enriched (document, segments, extra_warnings); preserve input text.

    source_context is a bounded projection: native story/block/cell location,
    heading references, explicit hyperlink/note/field references, logical grid,
    exact unit candidates and caption adjacency candidates. It contains no raw
    XML, image interpretation or invented physical page numbers.
    """
    # Lazy import keeps parse_docx free to call this helper without an import cycle.
    from .input_formats import package, relationships, xml, segment, paragraph
    document = copy.deepcopy(document); segments = copy.deepcopy(segments); warnings = []
    baseline_text = [item['raw_text'] for item in segments]
    if not segments:
        raise TaskError('DOCX_EVIDENCE_CONTEXT_MISSING', 'DOCX增强缺少源身份锚点。', 'DocxEvidence', ['IN-003', 'IN-016'])
    source_id = segments[0]['anchor']['source_id']; asset_id = segments[0]['anchor']['asset_id']
    evidence = {'version': 'docx-native-evidence-1', 'tables': [], 'images': [], 'hyperlinks': [],
                'note_references': [], 'notes': [], 'citation_fields': [], 'caption_candidates': [],
                'sections': [], 'story_relationships': [], 'semantic_status': 'not_inferred',
                'physical_pages': {'status': 'pending', 'renderer_ref': None, 'reason': '未执行Word布局分页渲染。'}}
    segment_by_native = {s['anchor']['native_locator']: s for s in segments}
    if len(segment_by_native) != len(segments):
        raise TaskError('DOCX_ANCHOR_DUPLICATE', '原解析DOCX存在重复原生定位。', 'DocxEvidence', ['IN-003', 'IN-016'])
    with package(raw, 'word/document.xml') as archive:
        names = set(archive.namelist()); bib = _bibliography(archive, xml); story_roots = {}; relmaps = {}
        style_nodes = {}
        if 'word/styles.xml' in names:
            style_nodes = {s.get('{' + W + '}styleId'): s for s in xml(archive.read('word/styles.xml')).findall('w:style', N)}
        def heading_level(node, block, part, path):
            outline = node.find('w:pPr/w:outlineLvl', N)
            if outline is not None:return _int(outline, 'val', None, warnings, part, path), 'paragraph_pPr'
            style_id = block.get('style_id'); seen = set()
            while style_id and style_id in style_nodes:
                if style_id in seen:
                    _warn(warnings, 'DOCX_STYLE_INHERITANCE_CYCLE', part, path, '样式继承出现循环；大纲级别保持未知。')
                    return None, None
                seen.add(style_id); style = style_nodes[style_id]; outline = style.find('w:pPr/w:outlineLvl', N)
                if outline is not None:return _int(outline, 'val', None, warnings, part, path), 'style:' + style_id
                base = style.find('w:basedOn', N); style_id = base.get('{' + W + '}val') if base is not None else None
            return None, None
        for story in document.get('stories', []):
            part = story['part']; root = xml(archive.read(part)); story_roots[part] = root
            rels = relationships(archive, part); relmap = {}
            for rel in rels:
                if not rel['id'] or rel['id'] in relmap:
                    raise TaskError('DOCX_RELATIONSHIP_AMBIGUOUS', 'DOCX关系ID为空或重复。', 'DocxEvidence', ['IN-003', 'IN-016', 'SEC-006'])
                relmap[rel['id']] = rel
            relmaps[part] = relmap
            for rel in rels:
                if any((rel['type'] or '').endswith('/' + kind) for kind in ('header', 'footer', 'footnotes', 'endnotes')):
                    evidence['story_relationships'].append({'from_part': part, **rel})
        note_by_part = {}
        for story in document.get('stories', []):
            if story['story'] not in {'footnote', 'endnote'}:continue
            part = story['part']; root = story_roots[part]; paths, _ = _paths(root); index = {}
            for node in root:
                note_id = node.get('{' + W + '}id')
                if note_id is None or note_id in index:
                    raise TaskError('DOCX_NOTE_ID_AMBIGUOUS', 'DOCX脚注/尾注ID缺失或重复。', 'DocxEvidence', ['IN-003', 'IN-016'])
                item = {'evidence_id': _id('note', part, paths[node]), 'part': part, 'story': story['story'],
                        'note_id': note_id, 'note_type': node.get('{' + W + '}type', 'normal'),
                        'xml_path': paths[node], 'native_locator': part + '#path=' + paths[node],
                        'text': '\n'.join(_paragraph_text(p) for p in node.findall('w:p', N)),
                        'semantic_status': 'not_inferred'}
                index[note_id] = item; evidence['notes'].append(item)
            note_by_part[part] = index

        def native(part, node, paths):return part + '#path=' + paths[node]

        def annotate_paragraph(node, data, context, part, paths, parents, location):
            data['xml_path'] = paths[node]; data['package_part'] = part
            context.update({'source_kind': 'docx', 'story': location['story'], 'package_part': part,
                            'xml_path': paths[node], 'paragraph_index': location['paragraph_index'],
                            'table_index': location['table_index'], 'row_index': location['row_index'],
                            'cell_index': location['cell_index'], 'block_kind': data.get('kind', 'paragraph'),
                            'units': _units(data.get('text', '')), 'semantic_status': 'not_inferred',
                            'physical_page_status': 'pending'})
            hyperlinks = []
            for link in node.findall('.//w:hyperlink', N):
                rid = link.get('{' + R + '}id'); bookmark = link.get('{' + W + '}anchor'); rel = relmaps[part].get(rid)
                item = {'evidence_id': _id('link', part, paths[link]), 'native_locator': native(part, link, paths),
                        'relationship_id': rid, 'text': _paragraph_text(link), 'anchor': bookmark,
                        'target': rel['target'] if rel else None, 'target_part': rel['target_part'] if rel else None,
                        'target_kind': 'external' if rel and rel['external'] else 'package_part' if rel else 'internal_anchor' if bookmark else 'unresolved',
                        'relationship_type': rel['type'] if rel else None, 'retrieval': 'not_fetched' if rel and rel['external'] else 'package_part' if rel else 'not_applicable',
                        'semantic_status': 'not_inferred'}
                if rid and (not rel or not (rel['type'] or '').endswith('/hyperlink')):
                    item['target_kind'] = 'unresolved'
                    _warn(warnings, 'DOCX_HYPERLINK_RELATIONSHIP_UNRESOLVED', part, paths[link], '超链接关系缺失或类型不符；保留原文与关系ID。')
                if bookmark:
                    matches = [b for b in story_roots[part].iter('{' + W + '}bookmarkStart') if b.get('{' + W + '}name') == bookmark]
                    item['bookmark_status'] = 'resolved' if len(matches) == 1 else 'missing' if not matches else 'ambiguous'
                    item['bookmark_native_locator'] = native(part, matches[0], paths) if len(matches) == 1 else None
                hyperlinks.append(item); evidence['hyperlinks'].append(item)
            data['hyperlink_evidence'] = hyperlinks; context['hyperlinks'] = hyperlinks
            refs = []
            for kind in ('footnote', 'endnote'):
                for ref in node.iter('{' + W + '}' + kind + 'Reference'):
                    note_id = ref.get('{' + W + '}id')
                    relations = [r for r in relmaps[part].values() if (r['type'] or '').endswith('/' + kind + 's')]
                    relation = relations[0] if len(relations) == 1 and not relations[0]['external'] else None
                    note = note_by_part.get(relation['target_part'], {}).get(note_id) if relation else None
                    item = {'evidence_id': _id('reference', part, paths[ref]), 'native_locator': native(part, ref, paths),
                            'kind': kind, 'note_id': note_id, 'relationship_id': relation['id'] if relation else None,
                            'target_part': relation['target_part'] if relation else None, 'status': 'resolved' if note else 'unresolved',
                            'note_evidence_id': note['evidence_id'] if note else None,
                            'note_native_locator': note['native_locator'] if note else None,
                            'note_text': note['text'] if note else None, 'semantic_status': 'not_inferred'}
                    if note is None:_warn(warnings, 'DOCX_NOTE_REFERENCE_UNRESOLVED', part, paths[ref], '脚注/尾注明确引用未找到唯一关系及目标；未猜测引用。')
                    refs.append(item); evidence['note_references'].append(item)
            data['note_references'] = refs; context['note_references'] = refs
            fields = _fields(node, paths); citations = []
            for field in fields:
                if field.get('status') == 'unclosed':_warn(warnings, 'DOCX_FIELD_UNCLOSED', part, field['xml_path'], '域缺少结束标记；原始域指令保留，未解析为引用。')
                match = re.match(r'\s*CITATION\s+("[^"]+"|\S+)', field['instruction'], re.I)
                if not match or field.get('status') == 'unclosed':continue
                tag = match[1].strip('"'); tags = [tag] + [m[1].strip('"') for m in re.finditer(r'\\m\s+("[^"]+"|\S+)', field['instruction'], re.I)]
                records = bib.get(tag, [])
                sources = [{'tag': t, 'status': 'resolved' if len(bib.get(t, [])) == 1 else 'missing' if not bib.get(t) else 'ambiguous',
                            'source': bib[t][0] if len(bib.get(t, [])) == 1 else None} for t in tags]
                item = {**field, 'evidence_id': _id('citation', part, field['xml_path']), 'native_locator': part + '#path=' + field['xml_path'],
                        'citation_tag': tag, 'citation_tags': tags, 'bibliography_sources': sources,
                        'bibliography_status': 'resolved' if all(s['status'] == 'resolved' for s in sources) else 'unresolved',
                        'bibliography': records[0] if len(records) == 1 else None, 'semantic_status': 'not_inferred'}
                if item['bibliography_status'] != 'resolved':_warn(warnings, 'DOCX_CITATION_SOURCE_UNRESOLVED', part, field['xml_path'], '引用域保留；书目标签缺少唯一登记项。')
                citations.append(item); evidence['citation_fields'].append(item)
            data['fields'] = fields; data['citation_fields'] = citations; context['citation_fields'] = citations
            images = []
            refs = list(node.iter('{' + A + '}blip')) + list(node.iter('{' + V + '}imagedata'))
            for image in refs:
                rid = image.get('{' + R + '}embed') if image.tag == '{' + A + '}blip' else image.get('{' + R + '}id')
                linkrid = image.get('{' + R + '}link'); relation = relmaps[part].get(rid or linkrid)
                item = {'evidence_id': _id('image', part, paths[image]), 'part': part, 'xml_path': paths[image],
                        'native_locator': native(part, image, paths), 'relationship_id': rid or linkrid,
                        'embedded_relationship_id': rid, 'linked_relationship_id': linkrid,
                        'target_part': relation['target_part'] if relation else None, 'external_target': relation['target'] if relation and relation['external'] else None,
                        'status': 'unresolved', 'retrieval': 'not_fetched' if relation and relation['external'] else 'package_part' if relation else 'unresolved',
                        'sha256': None, 'bytes': None, 'pixel_width': None, 'pixel_height': None, 'inspection_status': 'not_executed',
                        'alt_text': None, 'description': None, 'display_extent_emu': None, 'crop': [],
                        'source_anchor': {'package_part': part, 'xml_path': paths[node], **location},
                        'license': 'unknown', 'authorization': 'not_provided', 'semantic_status': 'not_inferred', 'ocr_status': 'not_executed'}
                parent = image
                while parent in parents and parent is not node:
                    if parent.tag in {'{' + W + '}drawing', '{' + W + '}pict'}:break
                    parent = parents[parent]
                props = parent.find('.//wp:docPr', N)
                if props is not None:
                    item['alt_text'] = props.get('title'); item['description'] = props.get('descr'); item['drawing_id'] = props.get('id')
                elif image.tag == '{' + V + '}imagedata':item['alt_text'] = image.get('{' + O + '}title')
                extent = parent.find('.//wp:extent', N)
                if extent is not None:
                    try:item['display_extent_emu'] = {'cx': int(extent.get('cx')), 'cy': int(extent.get('cy'))}
                    except (ValueError, TypeError):_warn(warnings, 'DOCX_IMAGE_EXTENT_INVALID', part, paths[image], '绘图显示尺寸无效；未猜测物理尺寸。')
                item['crop'] = [c.attrib for c in parent.findall('.//a:srcRect', N)]
                if rid and linkrid:
                    item['status'] = 'ambiguous'
                    _warn(warnings, 'DOCX_IMAGE_RELATIONSHIP_AMBIGUOUS', part, paths[image], '图片同时带嵌入/链接引用，两个引用完整保留，未选择替代来源。')
                elif not relation or not (relation['type'] or '').endswith('/image'):
                    _warn(warnings, 'DOCX_IMAGE_RELATIONSHIP_UNRESOLVED', part, paths[image], '图片关系缺失或类型不符，未登记虚构媒体。')
                elif relation['external']:
                    item['status'] = 'external_not_fetched'
                    _warn(warnings, 'DOCX_EXTERNAL_IMAGE_NOT_FETCHED', part, paths[image], '外部图片仅登记关系，未下载或将其作为像素证据。')
                elif relation['target_part'] not in names:
                    _warn(warnings, 'DOCX_IMAGE_PART_MISSING', part, paths[image], '内嵌图片关系目标部件不存在。')
                else:
                    payload = archive.read(relation['target_part']); item['sha256'] = hashlib.sha256(payload).hexdigest(); item['bytes'] = len(payload); item['status'] = 'registered'
                    try:
                        inspection = inspect_image(payload, relation['target_part'])
                        item.update({'pixel_width': inspection['width'], 'pixel_height': inspection['height'],
                                     'mime_type': inspection['mime_type'], 'format': inspection['format'], 'dpi': inspection['dpi'],
                                     'inspection_status': 'verified_raster_metadata'})
                    except TaskError as error:
                        item['inspection_status'] = 'unsupported_or_invalid'; item['inspection_error'] = error.code
                        _warn(warnings, 'DOCX_IMAGE_INSPECTION_UNAVAILABLE', part, paths[image], '媒体原字节/hash已登记，像素格式或校验未支持；未编造尺寸或图内文本。')
                images.append(item); evidence['images'].append(item)
                # Even unresolved images get a nontext locator, never text provenance.
                imgseg = segment('', copy.deepcopy(location), {'kind': 'docx_image', **copy.deepcopy(item)}, source_id, asset_id, item['native_locator'])
                imgseg['metadata']['source_context'] = {'source_kind': 'docx', 'block_kind': 'image', 'package_part': part,
                    'story': location['story'], 'xml_path': paths[image], 'image_evidence_id': item['evidence_id'],
                    'semantic_status': 'not_inferred', 'pixel_evidence_status': item['inspection_status'], 'physical_page_status': 'pending'}
                segments.append(imgseg)
            data['image_evidence'] = images
            context['images'] = [{'evidence_id': item['evidence_id'], 'native_locator': item['native_locator'], 'target_part': item['target_part'],
                                  'status': item['status'], 'semantic_status': 'not_inferred'} for item in images]

        for story in document.get('stories', []):
            part = story['part']; kind = story['story']; root = story_roots[part]; paths, parents = _paths(root)
            body = root.find('w:body', N) if kind == 'body' else root
            if body is None:raise TaskError('DOCX_BODY_MISSING', 'DOCX缺少正文body结构。', 'DocxEvidence', ['IN-003'])
            nodes = [(n, None) for n in body] if kind not in {'footnote', 'endnote'} else [(n, note.get('{' + W + '}id')) for note in body for n in note]
            blocknodes = [(n, noteid) for n, noteid in nodes if n.tag != '{' + W + '}sectPr']
            if len(blocknodes) != len(story['blocks']):raise TaskError('DOCX_BLOCK_MAPPING_MISMATCH', '已有DOCX块与原生XML不能一一对应。', 'DocxEvidence', ['IN-003', 'IN-016'])
            top_tables = [n for n, _ in nodes if n.tag == '{' + W + '}tbl']; nested_index = [len(top_tables)]
            headings = []; block_records = []; previous_note_id = None
            def table(node, data, table_index, noteid, parent_path=None):
                rownodes = node.findall('w:tr', N); gridnode = node.find('w:tblGrid', N)
                tabledata = {'evidence_id': _id('table', part, paths[node]), 'package_part': part, 'story': kind,
                             'native_locator': native(part, node, paths), 'xml_path': paths[node], 'table_index': table_index,
                             'note_id': noteid, 'parent_table_cell_path': parent_path,
                             'declared_grid_columns': len(gridnode) if gridnode is not None else None,
                             'grid_column_widths_twips': [g.get('{' + W + '}w') for g in gridnode] if gridnode is not None else [],
                             'rows': [], 'semantic_status': 'not_inferred'}
                active = {}; inferred_width = 0
                for ri, row in enumerate(rownodes):
                    before = _int(row.find('w:trPr/w:gridBefore', N), 'val', 0, warnings, part, paths[row]); after = _int(row.find('w:trPr/w:gridAfter', N), 'val', 0, warnings, part, paths[row]); cursor = before
                    rowdata = {'row_index': ri, 'grid_before': before, 'grid_after': after,
                               'repeat_header': row.find('w:trPr/w:tblHeader', N) is not None, 'cells': []}; nextactive = {}
                    horizontal = None
                    for ci, cell in enumerate(row.findall('w:tc', N)):
                        celldata = data['rows'][ri][ci]
                        span = _int(cell.find('w:tcPr/w:gridSpan', N), 'val', 1, warnings, part, paths[cell], minimum=1)
                        merge = cell.find('w:tcPr/w:vMerge', N); vmerge = (merge.get('{' + W + '}val', 'continue') if merge is not None else None)
                        hnode = cell.find('w:tcPr/w:hMerge', N); hmerge = (hnode.get('{' + W + '}val', 'continue') if hnode is not None else None)
                        cellid = _id('cell', part, paths[cell]); end = cursor + span if cursor is not None and span is not None else None
                        if end is not None and end > 4096:
                            end = None
                            _warn(warnings, 'DOCX_GRID_VALUE_INVALID', part, paths[cell], '逻辑列超出有界解析4096列限制；单元格原文保留，未展开巨型网格。')
                        status = 'located' if end is not None else 'unresolved'; owner = None
                        if vmerge == 'restart' and end is not None:owner = cellid
                        elif vmerge == 'continue' and end is not None:
                            owners = {active.get(col) for col in range(cursor, end)}
                            if len(owners) == 1 and None not in owners:owner = owners.pop()
                            else:status = 'unresolved'; _warn(warnings, 'DOCX_VERTICAL_MERGE_UNRESOLVED', part, paths[cell], '合并延续缺少相同逻辑列的唯一起始单元格。')
                        elif vmerge not in {None, 'restart', 'continue'}:status = 'unresolved'; _warn(warnings, 'DOCX_MERGE_VALUE_INVALID', part, paths[cell], '垂直合并值无效；未填充内容。')
                        if owner:
                            for col in range(cursor, end):nextactive[col] = owner
                        horizontal_owner = None
                        if hmerge == 'restart':horizontal = cellid; horizontal_owner = cellid
                        elif hmerge == 'continue':
                            horizontal_owner = horizontal
                            if horizontal is None:status = 'unresolved'; _warn(warnings, 'DOCX_HORIZONTAL_MERGE_UNRESOLVED', part, paths[cell], '水平合并延续缺少本行起始单元格。')
                        elif hmerge is None:horizontal = None
                        else:status = 'unresolved'; _warn(warnings, 'DOCX_MERGE_VALUE_INVALID', part, paths[cell], '水平合并值无效；未填充内容。')
                        grid = {'column_start': cursor, 'column_end_exclusive': end, 'column_span': span,
                                'vertical_merge': vmerge, 'vertical_owner_evidence_id': owner,
                                'horizontal_merge': hmerge, 'horizontal_owner_evidence_id': horizontal_owner, 'status': status}
                        loc = {'kind': 'docx_block', 'story': kind, 'paragraph_index': None, 'table_index': table_index, 'row_index': ri, 'cell_index': ci,
                               'page_location': {'status': 'pending', 'page_numbers': [], 'renderer_ref': None, 'reason': '未执行Word布局分页渲染。'}}
                        oldnative = f'{part}#table={table_index},row={ri},cell={ci}'
                        seg = segment_by_native.get(oldnative) if parent_path is None else None
                        if seg is None:
                            seg = segment(celldata['text'], loc, celldata, source_id, asset_id, native(part, cell, paths)); segments.append(seg)
                        else:seg['data'] = celldata
                        celldata.update({'evidence_id': cellid, 'package_part': part, 'xml_path': paths[cell], 'logical_grid': grid, 'note_id': noteid})
                        context = {'source_kind': 'docx', 'block_kind': 'table_cell', 'package_part': part, 'story': kind, 'xml_path': paths[cell],
                                   'native_locator': seg['anchor']['native_locator'], 'table_index': table_index, 'row_index': ri, 'cell_index': ci,
                                   'note_id': noteid, 'logical_grid': grid, 'units': _units(seg['raw_text']),
                                   'heading_refs': copy.deepcopy(headings), 'semantic_status': 'not_inferred', 'physical_page_status': 'pending', 'paragraphs': []}
                        for p, pd in zip(cell.findall('w:p', N), celldata['paragraphs']):
                            pc = {}; annotate_paragraph(p, pd, pc, part, paths, parents, loc); context['paragraphs'].append(pc)
                        # Context stores relation references, not an entire table/body.
                        context['column_header_candidates'] = []
                        if ri:
                            for hi, header in enumerate(data['rows'][0]):
                                hg = header.get('logical_grid', {})
                                if cursor is not None and end is not None and hg.get('column_start') is not None and hg.get('column_end_exclusive') is not None and cursor < hg['column_end_exclusive'] and end > hg['column_start']:
                                    context['column_header_candidates'].append({'row_index': 0, 'cell_index': hi, 'text': header['text'],
                                        'native_locator': f'{part}#table={table_index},row=0,cell={hi}' if parent_path is None else part + '#path=' + header['xml_path'],
                                        'relation_status': 'candidate', 'units': _units(header['text'])})
                        seg['metadata']['source_context'] = context
                        rowdata['cells'].append({'evidence_id': cellid, 'xml_path': paths[cell], 'native_locator': seg['anchor']['native_locator'],
                                                 'text': seg['raw_text'], 'logical_grid': grid, 'units': _units(seg['raw_text'])})
                        nested = []
                        for subtable in cell.findall('w:tbl', N):
                            index = nested_index[0]; nested_index[0] += 1
                            nd = {'kind': 'table', 'table_index': index, 'rows': [[{'kind': 'table_cell', 'paragraphs': [paragraph(p) for p in c.findall('w:p', N)],
                                 'text': '\n'.join(_paragraph_text(p) for p in c.findall('w:p', N)), 'nested_table_count': len(c.findall('.//w:tbl', N)),
                                 'raw_xml': ET.tostring(c, encoding='unicode')} for c in r.findall('w:tc', N)] for r in subtable.findall('w:tr', N)],
                                 'raw_xml': ET.tostring(subtable, encoding='unicode')}
                            table(subtable, nd, index, noteid, paths[cell]); nested.append(nd)
                        celldata['nested_tables'] = nested; cursor = end
                    rowdata['logical_column_count'] = cursor + after if cursor is not None and after is not None else None
                    if rowdata['logical_column_count'] is not None:
                        inferred_width = max(inferred_width, rowdata['logical_column_count'])
                        if tabledata['declared_grid_columns'] is not None and rowdata['logical_column_count'] > tabledata['declared_grid_columns']:
                            _warn(warnings, 'DOCX_GRID_DECLARATION_MISMATCH', part, paths[row], '本行逻辑列数超过声明网格；两者保留，未裁剪单元格。')
                    tabledata['rows'].append(rowdata); active = nextactive
                tabledata['observed_logical_columns'] = inferred_width; data['table_evidence'] = tabledata; evidence['tables'].append(tabledata)
            for (node, noteid), block in zip(blocknodes, story['blocks']):
                if noteid != previous_note_id:headings = []; previous_note_id = noteid
                if node.tag == '{' + W + '}p':
                    pi = block['paragraph_index']; seg = segment_by_native.get(f'{part}#paragraph={pi}')
                    if seg is None:raise TaskError('DOCX_SEGMENT_MAPPING_MISMATCH', 'DOCX段落证据锚点缺失。', 'DocxEvidence', ['IN-003', 'IN-016'])
                    seg['data'] = block; loc = seg['anchor']['locator']; context = {'native_locator': seg['anchor']['native_locator'], 'note_id': noteid}
                    annotate_paragraph(node, block, context, part, paths, parents, loc)
                    block['note_id'] = noteid
                    if block['kind'] == 'heading':
                        level, origin = heading_level(node, block, part, paths[node])
                        context['heading_level'] = level + 1 if level is not None else None; context['heading_level_status'] = 'native_explicit' if level is not None else 'unknown'
                        context['heading_level_origin'] = origin
                        headings = [{'text': seg['raw_text'], 'native_locator': seg['anchor']['native_locator'], 'heading_level': context['heading_level'], 'status': 'native_style_heading'}]
                    context['heading_refs'] = copy.deepcopy(headings); seg['metadata']['source_context'] = context
                    block_records.append({'kind': block['kind'], 'native_locator': seg['anchor']['native_locator'], 'text': seg['raw_text'],
                                          'images': block['image_evidence'], 'segment': seg, 'note_id': noteid})
                elif node.tag == '{' + W + '}tbl':
                    table(node, block, block['table_index'], noteid); block_records.append({'kind': 'table', 'native_locator': native(part, node, paths), 'text': None, 'images': [], 'note_id': noteid})
                else:
                    block['package_part'] = part; block['xml_path'] = paths[node]; block['note_id'] = noteid
            for bi, record in enumerate(block_records):
                if record['kind'] != 'caption':continue
                candidates = []
                for neighbour in [block_records[bi - 1] if bi else None, block_records[bi + 1] if bi + 1 < len(block_records) else None]:
                    if not neighbour or neighbour['note_id'] != record['note_id']:continue
                    if neighbour['kind'] == 'table':candidates.append({'kind': 'table', 'native_locator': neighbour['native_locator'], 'status': 'adjacent_candidate'})
                    candidates += [{'kind': 'image', 'evidence_id': i['evidence_id'], 'native_locator': i['native_locator'], 'status': 'adjacent_candidate'} for i in neighbour['images']]
                item = {'caption_native_locator': record['native_locator'], 'text': record['text'], 'targets': candidates, 'relationship_status': 'candidate', 'semantic_status': 'not_inferred'}
                evidence['caption_candidates'].append(item); record['segment']['metadata']['source_context']['caption_candidates'] = item
            if kind == 'body':
                for si, section in enumerate(body.iter('{' + W + '}sectPr')):
                    links = []
                    for element in section:
                        if element.tag not in {'{' + W + '}headerReference', '{' + W + '}footerReference'}:continue
                        rel = relmaps[part].get(element.get('{' + R + '}id'))
                        links.append({'kind': element.tag.rsplit('}', 1)[-1], 'section_role': element.get('{' + W + '}type'),
                                      'relationship_id': element.get('{' + R + '}id'), 'target_part': rel['target_part'] if rel else None,
                                      'status': 'resolved' if rel and not rel['external'] and rel['target_part'] in names else 'unresolved'})
                    evidence['sections'].append({'section_index': si, 'native_locator': native(part, section, paths), 'story_references': links,
                                                 'physical_page_status': 'pending'})
        for rel in evidence['story_relationships']:
            if rel['external'] or rel['target_part'] not in story_roots:
                _warn(warnings, 'DOCX_STORY_TARGET_UNPARSED', rel['from_part'], rel['id'], '故事关系目标未进入原有结构解析，未声称该来源已完整解释。')
    # Relationship targets are literal package evidence, separate from visible
    # paragraph text. This lets citation grounding quote a real URI without
    # promoting unresolved relationships or fetching the remote resource.
    uri_anchors=set()
    for original in list(segments):
        context=original.get('metadata',{}).get('source_context',{})
        for link in context.get('hyperlinks',[]):
            if link.get('target_kind')!='external' or not isinstance(link.get('target'),str):continue
            uri=link['target']
            if not uri.startswith(('https://','http://')):continue
            location=copy.deepcopy(original['anchor'])
            location['native_locator']=link['native_locator']+'#relationship='+str(link['relationship_id'])+'/@Target'
            if location['native_locator'] in uri_anchors:continue
            uri_anchors.add(location['native_locator'])
            segments.append({'raw_text':uri,'anchor':location,
                'data':{'kind':'docx_hyperlink_target','text':uri,'relationship_id':link['relationship_id'],
                        'referenced_by':link['native_locator'],'target_kind':'external','retrieval':'not_fetched'},
                'metadata':{'semantic_claim_status':'not_inferred','text_basis':'literal_package_relationship_target',
                            'source_context':{'source_kind':'docx','block_kind':'hyperlink_target','native_locator':location['native_locator'],
                                              'referenced_by':link['native_locator'],'retrieval':'not_fetched','physical_page_status':'pending'}}})
    if [s['raw_text'] for s in segments[:len(baseline_text)]] != baseline_text:
        raise TaskError('DOCX_TEXT_CHANGED', 'DOCX增强改变了原始文字，拒绝输出。', 'DocxEvidence', ['IN-003', 'IN-016'])
    anchors = [s['anchor']['native_locator'] for s in segments]
    if len(anchors) != len(set(anchors)):
        raise TaskError('DOCX_ANCHOR_DUPLICATE', 'DOCX增强存在重复原生定位。', 'DocxEvidence', ['IN-003', 'IN-016'])
    document['structure_evidence'] = evidence
    return document, segments, warnings
