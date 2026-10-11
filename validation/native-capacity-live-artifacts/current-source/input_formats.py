"""IN-003/004/006/008/010/011/015/016: structured binary input adapters.

Original bytes remain the EvidenceStore snapshot. All package parts are inventoried;
unsupported semantics are reported, never flattened away or silently fetched.
"""
import csv
import hashlib
import io
import json
import posixpath
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .assets import inspect_image
from .errors import TaskError

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
SUPPORTED_FORMATS = {'docx', 'xlsx', 'csv', 'pptx', 'potx', 'pdf', 'image', 'json', 'xml'}
MAX_RAW = 64 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_PARTS = 4096


def failure(code, message, ids=None, details=None):
    raise TaskError(code, message, 'InputFormatParser', ids or ['IN-015', 'SYS-003'], details or [])


def xml(raw):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        failure('XML_ENTITY_BLOCKED', 'XML DTD/实体声明被禁止。', ['IN-015', 'SEC-005'])
    try:
        return ET.fromstring(raw)
    except ET.ParseError:
        failure('INPUT_XML_CORRUPT', '文件中的XML结构损坏。')


def package(raw, expected):
    if raw.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):
        failure('INPUT_ENCRYPTED_OR_LEGACY', '检测到OLE容器：可能为加密OOXML或旧Office格式，未尝试解密。')
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
        parts = archive.infolist(); names = [p.filename for p in parts]
        if len(parts) > MAX_PARTS or sum(p.file_size for p in parts) > MAX_EXPANDED:
            archive.close(); failure('INPUT_ARCHIVE_LIMIT', 'OOXML展开文件数/总大小超过限制。', ['IN-015', 'SEC-004'])
        if len(names) != len(set(names)):
            archive.close(); failure('INPUT_DUPLICATE_PART', 'OOXML含重复部件路径，拒绝歧义包。')
        for p in parts:
            if p.flag_bits & 1:
                archive.close(); failure('INPUT_ENCRYPTED', '压缩包部件带密码保护。')
            if p.filename.startswith(('/', '\\')) or '\\' in p.filename or '..' in p.filename.split('/'):
                archive.close(); failure('INPUT_UNSAFE_PART', 'OOXML部件包含不安全路径。', ['IN-015', 'SEC-003'])
            if p.file_size > 1024 * 1024 and p.file_size / max(p.compress_size, 1) > 1000:
                archive.close(); failure('INPUT_ARCHIVE_RATIO', 'OOXML压缩比超过限制。', ['IN-015', 'SEC-004'])
        if expected not in names or '[Content_Types].xml' not in names:
            archive.close(); failure('INPUT_FORMAT_DISGUISED', '文件并非声明的OOXML类型。')
        xml(archive.read('[Content_Types].xml'))
        return archive
    except (zipfile.BadZipFile, RuntimeError, OSError):
        failure('INPUT_ARCHIVE_CORRUPT', 'Office压缩包损坏或不可读取。')


def relationships(archive, part):
    parent, name = posixpath.split(part)
    relpart = posixpath.join(parent, '_rels', name + '.rels')
    if relpart not in archive.namelist():return []
    result = []
    for node in xml(archive.read(relpart)):
        external = node.get('TargetMode') == 'External'
        target = node.get('Target', '')
        resolved = None if external else (target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(parent, target)))
        if resolved and (resolved.startswith('../') or '\\' in resolved):
            failure('INPUT_UNSAFE_RELATIONSHIP', 'Office内部关系逃逸包根目录。', ['IN-015', 'SEC-006'])
        result.append({'id': node.get('Id'), 'type': node.get('Type'), 'target': target,
                       'target_part': resolved, 'external': external, 'retrieval': 'not_fetched' if external else 'package_part'})
    return result


def part_inventory(archive):
    return [{'part': p.filename, 'bytes': p.file_size, 'sha256': hashlib.sha256(archive.read(p.filename)).hexdigest()}
            for p in archive.infolist() if not p.is_dir()]


def anchor(source_id, asset_id, native, location, status='located', reason=None):
    return {'source_id': source_id, 'asset_id': asset_id, 'native_locator': native, 'locator': location,
            'locator_status': status, 'reason': reason}


def segment(text, location, data, source_id, asset_id, native):
    return {'raw_text': text, 'anchor': anchor(source_id, asset_id, native, location), 'data': data,
            'metadata': {'semantic_claim_status': 'not_inferred', 'confidence_note': '结构解析不证明来源事实真实性。'}}


def paragraph(node):
    # w:t excludes deleted revisions. Deleted/inserted revision XML remains in raw_xml.
    text = ''.join((x.text or '') if x.tag == '{'+NS['w']+'}t' else '\t' if x.tag == '{'+NS['w']+'}tab' else '\n'
                   for x in node.iter() if x.tag in {'{'+NS['w']+'}t', '{'+NS['w']+'}tab', '{'+NS['w']+'}br'})
    style = node.find('w:pPr/w:pStyle', NS)
    return {'kind': 'paragraph', 'text': text, 'style_id': style.get('{'+NS['w']+'}val') if style is not None else None,
            'hyperlinks': [{'relationship_id': x.get('{'+NS['r']+'}id'), 'anchor': x.get('{'+NS['w']+'}anchor'),
                            'text': ''.join(t.text or '' for t in x.findall('.//w:t', NS))} for x in node.findall('.//w:hyperlink', NS)],
            'images': [{'relationship_id': x.get('{'+NS['r']+'}embed'), 'external_relationship_id': x.get('{'+NS['r']+'}link')}
                       for x in node.findall('.//a:blip', NS)], 'raw_xml': ET.tostring(node, encoding='unicode')}


def parse_docx(raw, source_id, asset_id):
    segments = []; stories = []; issues = [{'code': 'DOCX_PAGE_LOCATION_PENDING', 'message': '段落/表格原生锚点已保存；物理分页需要实际渲染，不由段落序号推测。'}]
    with package(raw, 'word/document.xml') as archive:
        names = archive.namelist()
        story_parts = [('word/document.xml', 'body')] + [(n, 'header' if '/header' in n else 'footer' if '/footer' in n else 'footnote' if 'footnotes' in n else 'endnote')
                       for n in names if re.fullmatch(r'word/(header\d+|footer\d+|footnotes|endnotes)\.xml', n)]
        styles = {}
        if 'word/styles.xml' in names:
            for style in xml(archive.read('word/styles.xml')).findall('w:style', NS):
                name = style.find('w:name', NS)
                styles[style.get('{'+NS['w']+'}styleId')] = name.get('{'+NS['w']+'}val') if name is not None else None
        for part, story in story_parts:
            root = xml(archive.read(part)); body = root.find('w:body', NS) if story == 'body' else root
            blocks = []; pi = 0; ti = 0
            containers = list(body) if story not in {'footnote', 'endnote'} else [block for note in body for block in note]
            for node in containers:
                if node.tag == '{'+NS['w']+'}p':
                    block = paragraph(node); block.update({'paragraph_index': pi, 'style_name': styles.get(block['style_id'])})
                    name = (block['style_name'] or block['style_id'] or '').lower()
                    block['kind'] = 'heading' if name.startswith(('heading', '标题')) else 'caption' if name.startswith(('caption', '题注')) else 'paragraph'
                    loc = {'kind': 'docx_block', 'story': story, 'paragraph_index': pi, 'table_index': None, 'row_index': None, 'cell_index': None,
                           'page_location': {'status': 'pending', 'page_numbers': [], 'renderer_ref': None, 'reason': '未执行Word布局分页渲染。'}}
                    segments.append(segment(block['text'], loc, block, source_id, asset_id, f'{part}#paragraph={pi}')); blocks.append(block); pi += 1
                elif node.tag == '{'+NS['w']+'}tbl':
                    table = {'kind': 'table', 'table_index': ti, 'rows': [], 'raw_xml': ET.tostring(node, encoding='unicode')}
                    for ri, row in enumerate(node.findall('w:tr', NS)):
                        cells = []
                        for ci, cell in enumerate(row.findall('w:tc', NS)):
                            paragraphs = [paragraph(p) for p in cell.findall('w:p', NS)]
                            nested = cell.findall('.//w:tbl', NS)
                            text = '\n'.join(p['text'] for p in paragraphs)
                            data = {'kind': 'table_cell', 'paragraphs': paragraphs, 'text': text, 'nested_table_count': len(nested),
                                    'raw_xml': ET.tostring(cell, encoding='unicode')}
                            if nested:issues.append({'code': 'DOCX_NESTED_TABLE_PRESERVED', 'part': part, 'table_index': ti, 'message': '嵌套表XML完整保留；未把嵌套表文本当作父单元格文本。'})
                            cells.append(data)
                            loc = {'kind': 'docx_block', 'story': story, 'paragraph_index': None, 'table_index': ti, 'row_index': ri, 'cell_index': ci,
                                   'page_location': {'status': 'pending', 'page_numbers': [], 'renderer_ref': None, 'reason': '未执行Word布局分页渲染。'}}
                            segments.append(segment(text, loc, data, source_id, asset_id, f'{part}#table={ti},row={ri},cell={ci}'))
                        table['rows'].append(cells)
                    blocks.append(table); ti += 1
                elif node.tag != '{'+NS['w']+'}sectPr':
                    blocks.append({'kind': 'preserved_uninterpreted', 'raw_xml': ET.tostring(node, encoding='unicode')})
                    issues.append({'code': 'DOCX_BLOCK_UNINTERPRETED', 'part': part, 'tag': node.tag, 'message': '该块完整保留，未作为已解析正文。'})
            stories.append({'part': part, 'story': story, 'blocks': blocks, 'relationships': relationships(archive, part)})
        return {'format': 'docx', 'stories': stories, 'styles': styles, 'package_parts': part_inventory(archive)}, segments, issues


def parse_xlsx(raw, source_id, asset_id):
    segments = []; sheets = []; issues = []
    with package(raw, 'xl/workbook.xml') as archive:
        names = archive.namelist(); shared = []
        if 'xl/sharedStrings.xml' in names:
            shared = [''.join(t.text or '' for t in item.findall('.//s:t', NS)) for item in xml(archive.read('xl/sharedStrings.xml'))]
        root = xml(archive.read('xl/workbook.xml')); rels = {r['id']: r for r in relationships(archive, 'xl/workbook.xml')}
        styles = xml(archive.read('xl/styles.xml')) if 'xl/styles.xml' in names else None
        formats = {int(n.get('numFmtId')): n.get('formatCode') for n in styles.findall('s:numFmts/s:numFmt', NS)} if styles is not None else {}
        cellstyles = [int(n.get('numFmtId', '0')) for n in styles.findall('s:cellXfs/s:xf', NS)] if styles is not None else []
        for sheet in root.findall('s:sheets/s:sheet', NS):
            relation = rels.get(sheet.get('{'+NS['r']+'}id'))
            if not relation or relation['external'] or relation['target_part'] not in names:failure('XLSX_SHEET_MISSING', '工作表关系缺失或为外部关系。', ['IN-008', 'IN-015'])
            part = relation['target_part']; node = xml(archive.read(part)); cells = []
            for cell in node.findall('.//s:sheetData/s:row/s:c', NS):
                ref = cell.get('r'); match = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', ref or '')
                if not match:failure('XLSX_CELL_ADDRESS_INVALID', '工作表单元格缺少合法坐标。', ['IN-008'])
                column = 0
                for letter in match[1]:column = column * 26 + ord(letter) - 64
                row = int(match[2]) - 1; column -= 1; type_ = cell.get('t', 'n'); value = cell.find('s:v', NS); formula = cell.find('s:f', NS)
                stored = value.text if value is not None else None
                if type_ == 's':
                    try:text = shared[int(stored)]
                    except (ValueError, IndexError, TypeError):failure('XLSX_SHARED_STRING_INVALID', '共享字符串索引无效。', ['IN-008', 'IN-015'])
                elif type_ == 'inlineStr':text = ''.join(t.text or '' for t in cell.findall('.//s:is//s:t', NS))
                else:text = stored or ''
                style_index = int(cell.get('s', 0)); format_id = cellstyles[style_index] if style_index < len(cellstyles) else None
                date_candidate = format_id in {14,15,16,17,18,19,20,21,22,45,46,47} or bool(format_id in formats and re.search(r'[dy]|(?<![A-Za-z])m', formats[format_id], re.I))
                data = {'kind': 'cell', 'cell_ref': ref, 'cell_type': type_, 'stored_value': stored, 'text': text,
                        'formula': formula.text if formula is not None else None, 'formula_attributes': formula.attrib if formula is not None else {},
                        'cached_value_status': 'present_unverified_freshness' if formula is not None and stored is not None else 'missing' if formula is not None else 'not_formula',
                        'number_format_id': format_id, 'number_format': formats.get(format_id), 'date_candidate': date_candidate,
                        'raw_xml': ET.tostring(cell, encoding='unicode')}
                if formula is not None and stored is None:issues.append({'code': 'XLSX_FORMULA_CACHE_MISSING', 'sheet': sheet.get('name'), 'cell_ref': ref, 'message': '公式保留但缺少缓存显示值，未执行或猜测计算结果。'})
                cells.append(data)
                loc = {'kind': 'tabular_cell', 'sheet_name': sheet.get('name'), 'cell_ref': ref, 'range_ref': ref,
                       'row_index': row, 'column_index': column, 'csv_record_number': None, 'csv_field_index': None}
                segments.append(segment(text, loc, data, source_id, asset_id, f'{part}#{ref}'))
            sheetrels = relationships(archive, part); tables = []
            for rel in sheetrels:
                if (rel['type'] or '').endswith('/table') and not rel['external'] and rel['target_part'] in names:
                    table = xml(archive.read(rel['target_part'])); tables.append({'part': rel['target_part'], 'name': table.get('name'),
                            'range_ref': table.get('ref'), 'columns': [x.attrib for x in table.findall('s:tableColumns/s:tableColumn', NS)], 'raw_xml': ET.tostring(table, encoding='unicode')})
            sheets.append({'name': sheet.get('name'), 'state': sheet.get('state', 'visible'), 'part': part,
                           'cells': cells, 'tables': tables, 'merged_ranges': [x.get('ref') for x in node.findall('s:mergeCells/s:mergeCell', NS)],
                           'relationships': sheetrels, 'header_candidates': [c['cell_ref'] for c in cells if re.fullmatch('[A-Z]+1', c['cell_ref'])],
                           'raw_xml': ET.tostring(node, encoding='unicode')})
        issues.append({'code': 'XLSX_DISPLAY_FORMAT_NOT_RENDERED', 'message': '原始类型、数字格式、公式及缓存值保留；未把原始数值伪装成Excel实际显示字符串，单位/图表语义待判断。'})
        return {'format': 'xlsx', 'date_system': '1904' if root.find('s:workbookPr', NS) is not None and root.find('s:workbookPr', NS).get('date1904') in {'1','true'} else '1900',
                'sheets': sheets, 'package_parts': part_inventory(archive)}, segments, issues


def parse_csv(raw, source_id, asset_id):
    try:text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:failure('INPUT_ENCODING_UNSUPPORTED', 'CSV须UTF-8；不猜测编码。', ['IN-008', 'IN-015'])
    if '\x00' in text:failure('INPUT_FORMAT_DISGUISED', 'CSV包含NUL字节。')
    try:rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    except csv.Error:failure('CSV_CORRUPT', 'CSV字段/引号结构无效。', ['IN-008', 'IN-015'])
    segments = []
    for ri, row in enumerate(rows):
        for ci, value in enumerate(row):
            loc = {'kind': 'tabular_cell', 'sheet_name': None, 'cell_ref': None, 'range_ref': None,
                   'row_index': ri, 'column_index': ci, 'csv_record_number': ri+1, 'csv_field_index': ci}
            segments.append(segment(value, loc, {'kind': 'cell', 'text': value, 'cell_type': 'string', 'type_inference': 'not_executed'}, source_id, asset_id, f'csv:record={ri+1},field={ci}'))
    widths = sorted(set(map(len, rows)))
    return {'format': 'csv', 'raw_text': text, 'rows': rows, 'header_candidate': rows[0] if rows else None}, segments, ([] if len(widths) <= 1 else [{'code':'CSV_RAGGED_ROWS', 'widths': widths, 'message':'不等长行已完整保留，未补齐或丢弃字段。'}])


def parse_pptx(raw, source_id, asset_id):
    from .templates import parse_template
    segments = []; slides = []; issues = []
    with package(raw, 'ppt/presentation.xml') as archive:
        root = xml(archive.read('ppt/presentation.xml')); rels = {r['id']: r for r in relationships(archive, 'ppt/presentation.xml')}
        for si, slide in enumerate(root.findall('p:sldIdLst/p:sldId', NS)):
            rel = rels.get(slide.get('{'+NS['r']+'}id'))
            if not rel or rel['external'] or rel['target_part'] not in archive.namelist():failure('PPTX_SLIDE_MISSING', '幻灯片关系缺失。', ['IN-006', 'IN-015'])
            part = rel['target_part']; node = xml(archive.read(part)); objects = []; slide_rels = relationships(archive, part)
            for shape in node.findall('.//p:spTree/*', NS):
                tag = shape.tag.rsplit('}',1)[-1]
                if tag in {'nvGrpSpPr','grpSpPr'}:continue
                cprops = shape.find('.//p:cNvPr', NS); sid = cprops.get('id') if cprops is not None else None
                text = '\n'.join(''.join(t.text or '' for t in p.findall('.//a:t', NS)) for p in shape.findall('.//a:p', NS))
                geometry = shape.find('.//a:xfrm', NS)
                data = {'kind': tag, 'shape_id': sid, 'name': cprops.get('name') if cprops is not None else None, 'text': text,
                        'geometry_xml': ET.tostring(geometry, encoding='unicode') if geometry is not None else None,
                        'placeholder': [x.attrib for x in shape.findall('.//p:ph', NS)],
                        'images': [x.attrib for x in shape.findall('.//a:blip', NS)], 'charts': [x.attrib for x in shape.findall('.//c:chart', NS)],
                        'tables': [ET.tostring(x, encoding='unicode') for x in shape.findall('.//a:tbl', NS)],
                        'raw_xml': ET.tostring(shape, encoding='unicode')}
                objects.append(data)
                loc = {'kind': 'presentation_part', 'package_part': part, 'slide_index': si, 'shape_id': sid,
                       'relationship_id': None, 'row_index': None, 'column_index': None, 'group_shape_ids': []}
                segments.append(segment(text, loc, data, source_id, asset_id, f'{part}#shape={sid}'))
            notes = []
            for relation in slide_rels:
                if (relation['type'] or '').endswith('/notesSlide') and not relation['external'] and relation['target_part'] in archive.namelist():
                    note = xml(archive.read(relation['target_part'])); text = '\n'.join(''.join(t.text or '' for t in p.findall('.//a:t', NS)) for p in note.findall('.//a:p', NS))
                    notes.append({'part': relation['target_part'], 'text': text, 'raw_xml': ET.tostring(note, encoding='unicode')})
                    loc = {'kind': 'presentation_part', 'package_part': relation['target_part'], 'slide_index': si, 'shape_id': None,
                           'relationship_id': relation['id'], 'row_index': None, 'column_index': None, 'group_shape_ids': []}
                    segments.append(segment(text, loc, notes[-1], source_id, asset_id, relation['target_part']))
            slides.append({'slide_index': si, 'part': part, 'objects': objects, 'notes': notes, 'relationships': slide_rels})
        charts = [{'part': name, 'raw_xml': archive.read(name).decode('utf-8')} for name in archive.namelist() if re.fullmatch(r'ppt/charts/chart\d+\.xml', name)]
        issues.append({'code': 'PPTX_NATIVE_XML_PRESERVED', 'message': '图表、表格、群组、几何和关系XML保留；文本解释不等于完整可编辑重建或Office行为验证。'})
        return {'format': 'pptx', 'slides': slides, 'charts': charts, 'template': parse_template(raw), 'package_parts': part_inventory(archive)}, segments, issues


def parse_pdf(raw, source_id, asset_id):
    if not raw.startswith(b'%PDF-'):failure('INPUT_FORMAT_DISGUISED', '文件并非PDF。', ['IN-004', 'IN-015'])
    if not shutil.which('pdftotext') or not shutil.which('pdfinfo'):
        failure('PDF_RENDERER_UNAVAILABLE', '容器缺少Poppler解析器；未回退乱码解析。', ['IN-004', 'IN-015'])
    parent = Path('/runtime/input-parser-temp'); parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pdf-', dir=parent) as directory:
        path = Path(directory)/'source.pdf'; output = Path(directory)/'bbox.xhtml'; path.write_bytes(raw)
        try:
            info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
            if info.returncode:
                failure('PDF_PASSWORD_OR_CORRUPT', 'PDF损坏或需密码，Poppler拒绝解析。', ['IN-004', 'IN-015'])
            if re.search(r'Encrypted:\s+yes', info.stdout):failure('INPUT_ENCRYPTED', 'PDF带加密保护，未尝试绕过。', ['IN-015'])
            result = subprocess.run(['pdftotext', '-bbox-layout', '-enc', 'UTF-8', str(path), str(output)], capture_output=True, timeout=60)
            if result.returncode or not output.is_file():failure('PDF_PARSE_FAILED', 'Poppler无法解析PDF。', ['IN-004', 'IN-015'])
            images = subprocess.run(['pdfimages', '-list', str(path)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30) if shutil.which('pdfimages') else None
        except subprocess.TimeoutExpired:failure('PDF_PARSE_TIMEOUT', 'PDF解析超过时间限制。', ['IN-004', 'IN-015'])
        # Poppler generates an XHTML PUBLIC doctype; it is output from our trusted
        # local tool, not an input declaration. No DTD/entity is loaded.
        generated = re.sub(br'<!DOCTYPE[^>]*>', b'', output.read_bytes(), count=1)
        root = xml(generated); pages = []; segments = []; issues = []
        for pi, page in enumerate(x for x in root.iter() if x.tag.rsplit('}',1)[-1] == 'page'):
            blocks = []
            for bi, block in enumerate(x for x in page.iter() if x.tag.rsplit('}',1)[-1] == 'block'):
                lines = []
                for line in (x for x in block.iter() if x.tag.rsplit('}',1)[-1] == 'line'):
                    words = [{'text': w.text or '', 'bbox': {k: float(v) for k,v in w.attrib.items()}} for w in line if w.tag.rsplit('}',1)[-1] == 'word']
                    lines.append({'text': ' '.join(w['text'] for w in words), 'words': words, 'bbox': {k: float(v) for k,v in line.attrib.items()}})
                text = '\n'.join(line['text'] for line in lines)
                data = {'kind': 'text_block', 'text': text, 'lines': lines, 'bbox': {k: float(v) for k,v in block.attrib.items()}, 'coordinate_space': 'pdf_points_top_left'}
                blocks.append(data)
                loc = {'kind': 'pdf_element', 'page_index': pi, 'page_number': pi+1, 'element_index': bi, 'object_kind': 'text', 'row_index': None, 'cell_index': None}
                segments.append(segment(text, loc, data, source_id, asset_id, f'pdf:page={pi+1},block={bi}'))
            if not blocks:
                issues.append({'code': 'PDF_OCR_REQUIRED', 'page_number': pi+1, 'message': '页面无可提取文本，需OCR/视觉解析；未静默认定空白。'})
                loc = {'kind':'pdf_element','page_index':pi,'page_number':pi+1,'element_index':None,'object_kind':'image','row_index':None,'cell_index':None}
                segments.append(segment('',loc,{'kind':'page_without_text','ocr_status':'required_not_executed'},source_id,asset_id,f'pdf:page={pi+1}'))
            pages.append({'page_number': pi+1, 'width': float(page.get('width')), 'height': float(page.get('height')), 'blocks': blocks, 'ocr_status': 'required_not_executed' if not blocks else 'not_required_for_text'})
        issues.append({'code': 'PDF_TABLE_STRUCTURE_UNRESOLVED', 'message': '页/行/字坐标已保留；表格和标题仅有原始几何，未声称已识别表格语义。'})
        if images is None or images.returncode:issues.append({'code': 'PDF_IMAGE_INVENTORY_UNAVAILABLE', 'message': 'PDF图像清单未成功读取。'})
        return {'format': 'pdf', 'pages': pages, 'image_inventory_raw': images.stdout if images is not None and not images.returncode else None,
                'renderer': 'Poppler pdftotext -bbox-layout', 'pdfinfo_raw': info.stdout}, segments, issues


def parse_input(kind, raw, *, source_id, asset_id=None, locator=None):
    """Return preserved document + per-format evidence segments; caller saves original bytes."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_RAW:
        failure('INPUT_SIZE_LIMIT', '输入为空、非字节或超过64MiB限制。')
    kind = kind.lower()
    if kind not in SUPPORTED_FORMATS:failure('INPUT_UNSUPPORTED', '该格式未支持，未静默跳过。', details=[{'kind': kind, 'supported': sorted(SUPPORTED_FORMATS)}])
    try:
        if kind == 'docx':document, segments, issues = parse_docx(raw, source_id, asset_id)
        elif kind == 'xlsx':document, segments, issues = parse_xlsx(raw, source_id, asset_id)
        elif kind == 'csv':document, segments, issues = parse_csv(raw, source_id, asset_id)
        elif kind in {'pptx','potx'}:document, segments, issues = parse_pptx(raw, source_id, asset_id)
        elif kind == 'pdf':document, segments, issues = parse_pdf(raw, source_id, asset_id)
        elif kind == 'image':
            document = inspect_image(raw, locator); issues = document['issues']
            loc = {'kind': 'image_region', 'element_id': None, 'bbox': {'x': 0, 'y': 0, 'width': document['width'], 'height': document['height'], 'coordinate_space': 'raw_source_pixels_top_left'}}
            segments = [segment('', loc, document, source_id, asset_id, 'image:full_frame')]
        else:
            text = raw.decode('utf-8-sig')
            if kind == 'json':
                def unique(pairs):
                    result = {}
                    for k,v in pairs:
                        if k in result:failure('JSON_DUPLICATE_KEY', 'JSON对象含重复键，拒绝覆盖原信息。', ['IN-010', 'IN-015'])
                        result[k] = v
                    return result
                tree = json.loads(text, object_pairs_hook=unique, parse_constant=lambda value: failure('JSON_NONFINITE', 'JSON不允许非有限数。', ['IN-010']))
                document = {'format': 'json', 'raw_text': text, 'tree': tree}
            else:document = {'format': 'xml', 'raw_text': text, 'root_tag': xml(raw).tag}
            loc = {'kind': 'structured_node', 'format': kind, 'node_id': None, 'document_path': '$' if kind=='json' else '/', 'line': None, 'column': None, 'end_line': None, 'end_column': None, 'byte_offset': 0}
            segments = [segment(text, loc, document, source_id, asset_id, kind+':root')]; issues = []
    except TaskError:raise
    except (ValueError, UnicodeDecodeError, KeyError, TypeError, zipfile.BadZipFile, OverflowError, RecursionError):
        failure('INPUT_PARSE_FAILED', '结构文件损坏或解析失败，未继续采用部分结果。')
    if not segments:
        failure('INPUT_NO_PARSED_EVIDENCE','文件没有可解析的文本或定位对象；原文件不可作为已解析来源继续生成。')
    version = 'binary-1:'+hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name('templates.py').read_bytes()+Path(__file__).with_name('assets.py').read_bytes()).hexdigest()
    return {'status': 'partial' if issues else 'parsed', 'document': document, 'segments': segments,
            'warnings': issues, 'parser_version': version+':kind:'+kind, 'source_sha256': hashlib.sha256(raw).hexdigest(),
            'boundary': 'Original bytes must be snapshotted; structure/anchors are not semantic fact extraction or system acceptance.'}
