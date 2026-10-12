"""IN-008/016, SYS-003: bounded SpreadsheetML evidence projections.

This is a projection of saved source data, not Excel rendering or calculation.
No formula, macro, external link, locale inference, or semantic unit inference runs.
Unsupported display formats keep their original data and emit no numeric text.
"""
import copy
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from xml.etree import ElementTree as ET

from .errors import TaskError

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
BUILTINS = {0: 'General', 1: '0', 2: '0.00', 3: '#,##0', 4: '#,##0.00',
            9: '0%', 10: '0.00%', 11: '0.00E+00', 12: '# ?/?', 13: '# ??/??',
            37: '#,##0 ;(#,##0)', 38: '#,##0 ;[Red](#,##0)',
            39: '#,##0.00;(#,##0.00)', 40: '#,##0.00;[Red](#,##0.00)', 49: '@'}
LOCALE_DATES = set(range(14, 23)) | {27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 50, 51, 52, 53, 54, 55, 56, 57, 58}
COLORS = {'black', 'blue', 'cyan', 'green', 'magenta', 'red', 'white', 'yellow'}
MAX_CELLS = 250000
MAX_RANGES = 128
VERSION = 'xlsx-evidence-1'


def _fail(code, message, details=None):
    raise TaskError(code, message, 'XlsxEvidenceProjection', ['IN-008', 'IN-016', 'SYS-003'], details or [])


def _xml(text):
    if not isinstance(text, str) or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        _fail('XLSX_PROJECTION_XML_INVALID', '显示证据的结构XML无效或含实体声明。')
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        _fail('XLSX_PROJECTION_XML_INVALID', '显示证据的结构XML无法解析。')


def _address(ref):
    m = re.fullmatch(r'([A-Z]{1,3})([1-9][0-9]{0,6})', ref or '')
    if not m:
        _fail('XLSX_PROJECTION_ADDRESS_INVALID', '显示证据单元格坐标无效。')
    col = 0
    for char in m[1]:
        col = col * 26 + ord(char) - 64
    row = int(m[2])
    if col > 16384 or row > 1048576:
        _fail('XLSX_PROJECTION_ADDRESS_INVALID', '单元格坐标超过XLSX范围。')
    return row, col


def _range(ref):
    pieces = (ref or '').replace('$', '').split(':')
    if len(pieces) not in {1, 2}:
        _fail('XLSX_PROJECTION_RANGE_INVALID', '表格/合并范围无效。')
    a = _address(pieces[0]); b = _address(pieces[-1])
    if a[0] > b[0] or a[1] > b[1]:
        _fail('XLSX_PROJECTION_RANGE_INVALID', '表格/合并范围顺序无效。')
    return a[0], a[1], b[0], b[1]


def _column(col):
    text = ''
    while col:
        col, rem = divmod(col - 1, 26); text = chr(65 + rem) + text
    return text


def _inside(position, bounds):
    return bounds[0] <= position[0] <= bounds[2] and bounds[1] <= position[1] <= bounds[3]


def _tokens(code):
    """Retain quoted/escaped literals; reject conditions/locale/fill/spacing codes."""
    sections = [[]]; i = 0
    while i < len(code):
        ch = code[i]
        if ch == ';':
            sections.append([])
            if len(sections) > 4: raise ValueError('too_many_sections')
        elif ch == '"':
            end = code.find('"', i + 1)
            if end == -1: raise ValueError('unclosed_literal')
            sections[-1].append(('literal', code[i+1:end])); i = end
        elif ch == '\\':
            i += 1
            if i >= len(code): raise ValueError('invalid_escape')
            sections[-1].append(('literal', code[i]))
        elif ch == '[':
            end = code.find(']', i+1)
            if end == -1: raise ValueError('unclosed_bracket')
            label = code[i+1:end]
            if label.lower() not in COLORS or sections[-1]:
                raise ValueError('condition_locale_or_elapsed_format_unsupported')
            sections[-1].append(('color', label)); i = end
        elif ch in '_*':
            raise ValueError('width_dependent_spacing_or_fill_unsupported')
        elif ch in '0#.,%?@ymdhsEe':
            sections[-1].append(('code', ch))
        elif ch in '$+-():/ ^\'{}<>=!&~':
            sections[-1].append(('literal', ch))
        else:
            raise ValueError('unquoted_literal_or_format_unsupported')
        i += 1
    return sections


def _decimal(value):
    if not isinstance(value, str) or len(value) > 512:
        raise ValueError('numeric_storage_invalid_or_too_large')
    try: result = Decimal(value)
    except InvalidOperation: raise ValueError('numeric_storage_invalid')
    if not result.is_finite() or abs(result.adjusted()) > 308 or len(result.as_tuple().digits) > 64:
        raise ValueError('numeric_nonfinite_or_precision_limit')
    return result


def _numeric(tokens, value, auto_minus):
    tokens = [x for x in tokens if x[0] != 'color']
    idx = [i for i, t in enumerate(tokens) if t[0] == 'code' and t[1] in '0#.,']
    if not idx:
        if any(kind == 'code' for kind, _ in tokens): raise ValueError('numeric_format_unsupported')
        return ''.join(v for _, v in tokens), [], None
    start, end = min(idx), max(idx)
    if any(k != 'code' for k, _ in tokens[start:end+1]): raise ValueError('interleaved_literal_unsupported')
    pattern = ''.join(v for _, v in tokens[start:end+1])
    m = re.fullmatch(r'(0{1,20}|#,##0)(?:\.(0{0,12}#{0,12}))?', pattern)
    if not m or ('.' in pattern and not m[2]): raise ValueError('numeric_format_unsupported')
    prefix, suffix = tokens[:start], tokens[end+1:]
    if any(k == 'code' for k, _ in prefix): raise ValueError('numeric_prefix_unsupported')
    percent = bool(suffix and suffix[0] == ('code', '%'))
    if percent: suffix = suffix[1:]
    if any(k == 'code' for k, _ in suffix): raise ValueError('numeric_suffix_unsupported')
    prefix_text = ''.join(v for _, v in prefix); suffix_text = ''.join(v for _, v in suffix)
    # Prefix sign placement depends on the exact format. Require an explicit
    # negative section for prefix formats instead of guessing an Excel display.
    if auto_minus and prefix_text: raise ValueError('implicit_negative_prefix_unsupported')
    decimals = m[2] or ''; digits = len(decimals)
    with localcontext() as context:
        context.prec = 400
        scaled = value.copy_abs() * (100 if percent else 1)
        rounded = scaled.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    number = format(rounded, ',.' + str(digits) + 'f' if ',' in m[1] else '.' + str(digits) + 'f')
    if '#' in decimals:
        trim = len(decimals) - len(decimals.rstrip('#'))
        for _ in range(trim):
            if number.endswith('0'): number = number[:-1]
            else: break
        number = number.rstrip('.')
    if ',' not in m[1]:
        integer, dot, tail = number.partition('.')
        number = integer.zfill(len(m[1])) + (dot + tail if dot else '')
    if auto_minus: number = '-' + number
    literals = [{'text': ''.join(v for k, v in group if k == 'literal'), 'position': position,
                 'status': 'literal_format_candidate_not_semantic_unit'}
                for position, group in [('prefix', prefix), ('suffix', suffix)] if group]
    if percent: literals.append({'text': '%', 'position': 'suffix', 'status': 'explicit_percent_format', 'numeric_scale': '100'})
    return prefix_text + number + ('%' if percent else '') + suffix_text, literals, '100' if percent else '1'


def _date_projection(tokens, value, system):
    tokens = [x for x in tokens if x[0] != 'color']
    # Only numeric calendar forms and 24-hour time are deterministic here.
    parts = []; i = 0
    while i < len(tokens):
        kind, text = tokens[i]
        if kind == 'literal': parts.append(('literal', text)); i += 1; continue
        if text not in 'ymdhs': raise ValueError('date_format_unsupported')
        run = text; i += 1
        while i < len(tokens) and tokens[i] == ('code', text): run += text; i += 1
        parts.append(('date', run))
    runs = [v for k, v in parts if k == 'date']
    if not runs or any(v not in {'yy','yyyy','m','mm','d','dd','h','hh','ss','s'} for v in runs):
        raise ValueError('date_format_unsupported')
    calendar = any('y' in v or 'd' in v for v in runs)
    if calendar and not ({'y','m','d'} <= {v[0] for v in runs}): raise ValueError('partial_calendar_format_unsupported')
    if value < 0: raise ValueError('negative_date_serial_unsupported')
    day = int(value); has_seconds = any(v[0] == 's' for v in runs)
    has_time = any(v[0] == 'h' for v in runs)
    resolution = Decimal(1 if has_seconds else 60)
    with localcontext() as context:
        context.prec = 400
        seconds_value = (value - day) * 86400
    if has_time and seconds_value % resolution:
        raise ValueError('subdisplay_time_precision_unsupported')
    seconds = int(seconds_value) if has_time else 0
    if calendar and system == '1900' and day in {0, 60}:
        raise ValueError('excel_1900_noncalendar_serial')
    try:
        origin = date(1904, 1, 1) if system == '1904' else date(1899, 12, 31)
        actual = origin + timedelta(days=day if system == '1904' or day < 60 else day-1)
    except (ValueError, OverflowError): raise ValueError('date_out_of_range')
    hour, rem = divmod(seconds, 3600); minute, second = divmod(rem, 60)
    rendered = []; in_time = False
    for index, (kind, run) in enumerate(parts):
        if kind == 'literal': rendered.append(run); continue
        ch = run[0]
        if ch == 'h': in_time = True
        if ch == 'm':
            future_seconds = any(k == 'date' and v[0] == 's' for k, v in parts[index+1:])
            if in_time or (not calendar and future_seconds): number = minute
            elif calendar: number = actual.month
            else: raise ValueError('month_minute_ambiguous')
        else: number = {'y': actual.year % 100 if run == 'yy' else actual.year,
                         'd': actual.day, 'h': hour, 's': second}[ch]
        rendered.append(str(number).zfill(len(run)))
    iso = actual.isoformat() + (f'T{hour:02}:{minute:02}:{second:02}' if has_time else '') if calendar else f'{hour:02}:{minute:02}:{second:02}'
    return ''.join(rendered), {'date_system': system, 'serial': str(value), 'iso_projection': iso,
                               'calendar_valid': True, 'timezone': 'unspecified', 'calendar_present': calendar}


def _project(cell, system):
    type_ = cell.get('cell_type', 'n'); stored = cell.get('stored_value')
    formula_node = _xml(cell['raw_xml']).find('s:f', NS)
    formula = formula_node is not None
    code = cell.get('number_format')
    fmt_id = cell.get('number_format_id')
    if code is None: code = BUILTINS.get(fmt_id)
    result = {'version': VERSION, 'status': 'unsupported', 'derived': True, 'display_text': '',
              'format_code': code, 'number_format_id': fmt_id, 'logical_type': 'unknown',
              'basis': 'saved_value_and_explicit_bounded_format', 'excel_rendered': False,
              'formula_evaluated': False, 'cache_freshness': 'unverified' if formula else 'not_formula',
              'unit_candidates': [], 'reason': None}
    if formula and (stored is None or cell.get('cached_value_status') == 'missing'):
        result.update(reason='formula_cache_missing', logical_type='formula_without_cache'); return result
    if type_ == 'e':
        result.update(reason='error_cell_not_fact_text', logical_type='error', error_value=stored); return result
    if stored is None and type_ not in {'s', 'inlineStr', 'str'}:
        result.update(status='blank', reason=None, logical_type='blank', derived=False); return result
    try:
        if type_ in {'s', 'inlineStr', 'str'}:
            text = cell.get('text', '')
            if not isinstance(text, str): raise ValueError('text_storage_invalid')
            if code and code not in {'General', '@'}:
                sections = _tokens(code)
                if len(sections) == 4:
                    chosen = [x for x in sections[3] if x[0] != 'color']
                    if any(k == 'code' and v != '@' for k, v in chosen): raise ValueError('text_format_unsupported')
                    text = ''.join(text if (k,v) == ('code','@') else v for k,v in chosen)
                    result['derived'] = True
                else: result['derived'] = False
            else: result['derived'] = False
            result.update(status='source_text' if not result['derived'] else 'derived_projection', display_text=text, logical_type='string'); return result
        if type_ == 'b':
            if stored not in {'0', '1'}: raise ValueError('boolean_storage_invalid')
            result.update(status='derived_projection', display_text='TRUE' if stored == '1' else 'FALSE', logical_type='boolean', typed_value=stored == '1'); return result
        if type_ == 'd':
            # OOXML ISO dates preserve their source spelling; no locale conversion.
            if not isinstance(stored, str) or not re.fullmatch(r'\d{4}-\d\d-\d\d(?:T\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)?)?', stored):
                raise ValueError('iso_date_storage_invalid')
            date.fromisoformat(stored[:10])
            if len(stored) > 10:
                from datetime import datetime
                datetime.fromisoformat(stored)
            result.update(status='source_iso_date', display_text=stored, logical_type='datetime', derived=False, typed_value=stored); return result
        if type_ != 'n': raise ValueError('cell_type_unsupported')
        value = _decimal(stored); result.update(logical_type='number', typed_value=str(value))
        if code is None:
            raise ValueError('locale_dependent_builtin_date' if fmt_id in LOCALE_DATES else 'number_format_missing_or_unsupported')
        if code == 'General' or code == '@':
            # General depends on column width. This exact scalar projection is
            # explicitly not an assertion of Excel's displayed string.
            text = format(value, 'f')
            if len(text) > 512: raise ValueError('general_projection_length_limit')
            result.update(status='typed_numeric_projection', display_text=text,
                          basis='exact_saved_numeric_scalar_not_excel_general_display', numeric_scale='1'); return result
        sections = _tokens(code)
        count = min(len(sections), 3)
        index = 1 if value < 0 and count >= 2 else 2 if value == 0 and count >= 3 else 0
        chosen = sections[index]
        result['selected_format_section'] = index
        if not chosen:
            result.update(status='hidden_by_format', reason=None); return result
        date_codes = any(k == 'code' and v in 'ymdhs' for k, v in chosen)
        if date_codes:
            if value < 0: raise ValueError('negative_date_serial_unsupported')
            text, typed = _date_projection(chosen, value, system)
            result.update(status='derived_projection', display_text=text, logical_type='datetime', typed_value=typed)
        else:
            text, units, scale = _numeric(chosen, value, value < 0 and count == 1)
            result.update(status='derived_projection', display_text=text, unit_candidates=units, numeric_scale=scale)
        return result
    except (ValueError, InvalidOperation, OverflowError) as error:
        result.update(reason=str(error) or 'projection_invalid'); return result


def _native_anchor(segment):
    return copy.deepcopy(segment['anchor'])


def enhance_xlsx(document, segments):
    """Return independent enhanced copies and explicit warnings; no IO or models."""
    if not isinstance(document, dict) or document.get('format') != 'xlsx' or not isinstance(segments, list):
        _fail('XLSX_PROJECTION_INPUT_INVALID', '显示证据仅接受既有XLSX解析文档和锚点列表。')
    document = copy.deepcopy(document); segments = copy.deepcopy(segments); warnings = []
    sheets = document.get('sheets', []); system = document.get('date_system')
    if system not in {'1900','1904'} or not isinstance(sheets, list) or len(sheets) > 1024:
        _fail('XLSX_PROJECTION_INPUT_INVALID', 'XLSX日期系统或工作表清单无效。')
    if sum(len(s.get('cells', [])) for s in sheets) > MAX_CELLS:
        _fail('XLSX_PROJECTION_LIMIT', 'XLSX单元格数超过有界显示投影限制。')
    segment_map = {}
    for item in segments:
        loc = item.get('anchor', {}).get('locator', {})
        if loc.get('kind') != 'tabular_cell': _fail('XLSX_PROJECTION_ANCHOR_INVALID', 'XLSX证据缺少单元格锚点。')
        key = (loc.get('sheet_name'), loc.get('cell_ref'))
        if key in segment_map: _fail('XLSX_PROJECTION_DUPLICATE_CELL', 'XLSX证据含重复单元格锚点。')
        segment_map[key] = item
    names = set(); handled = set(); cell_count = 0
    for sheet in sheets:
        name = sheet.get('name')
        if name in names: _fail('XLSX_PROJECTION_DUPLICATE_SHEET', 'XLSX工作表名称重复。')
        names.add(name); node = _xml(sheet['raw_xml']); cells = sheet.get('cells', [])
        hidden_rows = {int(row.get('r')) for row in node.findall('s:sheetData/s:row', NS) if row.get('hidden') in {'1','true'}}
        hidden_cols = []
        for col in node.findall('s:cols/s:col', NS):
            if col.get('hidden') in {'1','true'}:
                lo, hi = int(col.get('min')), int(col.get('max'))
                if not 1 <= lo <= hi <= 16384: _fail('XLSX_PROJECTION_ADDRESS_INVALID', '隐藏列范围无效。')
                hidden_cols.append((lo,hi))
        merged = [(ref, _range(ref)) for ref in sheet.get('merged_ranges', [])]
        conditional = [_range(ref) for rule in node.findall('s:conditionalFormatting', NS)
                       for ref in (rule.get('sqref') or '').split()]
        if len(conditional) > MAX_RANGES:
            _fail('XLSX_PROJECTION_LIMIT', '条件格式范围超过有界关系检查限制。')
        if len(merged) > MAX_RANGES:
            _fail('XLSX_PROJECTION_LIMIT', '合并范围超过有界关系检查限制。')
        positions = {}; by_ref = {}; local_segments = {}
        for cell in cells:
            ref = cell['cell_ref']; position = _address(ref); key = (name,ref)
            if ref in by_ref: _fail('XLSX_PROJECTION_DUPLICATE_CELL', '工作表包含重复单元格。')
            if key not in segment_map: _fail('XLSX_PROJECTION_ANCHOR_INVALID', '工作表单元格没有对应证据。')
            item = segment_map[key]
            native = item['anchor'].get('native_locator')
            if native != sheet['part'] + '#' + ref or item.get('data') != cell:
                _fail('XLSX_PROJECTION_ANCHOR_INVALID', '工作表部件或原单元格数据与锚点不一致。')
            handled.add(key); positions[ref] = position; by_ref[ref] = cell; local_segments[ref] = item; cell_count += 1
            projection = _project(cell, system)
            if any(_inside(position, bounds) for bounds in conditional):
                projection = {**projection, 'status':'unsupported', 'display_text':'',
                              'reason':'conditional_final_display_unresolved',
                              'base_format_projection':copy.deepcopy(projection)}
            membership = [(r,b) for r,b in merged if _inside(position,b)]
            if len(membership) > 1: _fail('XLSX_PROJECTION_MERGE_OVERLAP', '合并范围相交，拒绝歧义显示证据。')
            merge_info = None
            if membership:
                r,b = membership[0]; top_left = _column(b[1]) + str(b[0])
                merge_info = {'range_ref': r, 'anchor_cell': top_left, 'role': 'anchor' if ref == top_left else 'covered'}
                if ref != top_left:
                    projection.update(status='merged_covered_nontext', display_text='', reason='merged_nonanchor_source_preserved')
            visibility = {'sheet_state': sheet.get('state','visible'), 'row_hidden': position[0] in hidden_rows,
                          'column_hidden': any(lo <= position[1] <= hi for lo,hi in hidden_cols)}
            visibility['visible'] = visibility['sheet_state'] == 'visible' and not visibility['row_hidden'] and not visibility['column_hidden']
            cell['display_projection'] = projection; cell['visibility'] = visibility; cell['merge_membership'] = merge_info
            # Original stored value, decoded text, formula and XML stay unchanged.
            item['data'] = cell; item['raw_text'] = projection['display_text']
            metadata = item.setdefault('metadata', {})
            metadata.update({'text_basis': 'source_display_projection' if projection['derived'] else 'source_literal',
                             'derived': projection['derived'], 'semantic_claim_status': 'not_inferred',
                             'display_projection_status': projection['status']})
            metadata['source_context'] = {
                'source_kind': 'xlsx', 'cell_ref': ref, 'sheet_name': name, 'row_index': position[0]-1, 'column_index': position[1]-1,
                'cell_type': cell.get('cell_type'), 'logical_type': projection['logical_type'], 'stored_value': cell.get('stored_value'),
                'number_format_id': cell.get('number_format_id'), 'number_format': projection['format_code'],
                'formula': cell.get('formula'), 'formula_attributes': copy.deepcopy(cell.get('formula_attributes', {})),
                'external_formula_reference_candidate': bool(cell.get('formula') and '[' in cell['formula']),
                'cached_value_status': cell.get('cached_value_status'), 'cache_freshness': projection['cache_freshness'],
                'display_projection': copy.deepcopy(projection), 'cell_anchor': _native_anchor(item),
                'visibility': visibility, 'merge_membership': merge_info, 'header_candidates': [], 'range_candidates': [], 'unit_candidates': []}
            if projection['status'] == 'unsupported':
                warnings.append({'code': 'XLSX_DISPLAY_PROJECTION_UNSUPPORTED', 'sheet': name, 'cell_ref': ref,
                                 'reason': projection['reason'], 'message': '原存储与格式完整保留；该显示值未支持，未将原始数值当作显示事实。'})
            if not visibility['visible']:
                warnings.append({'code':'XLSX_HIDDEN_CELL_PRESERVED','sheet':name,'cell_ref':ref,
                                 'message':'隐藏来源数据已保留并标记；不静默当作可见表格或推断应排除。'})
            if membership and merge_info['role'] == 'covered':
                warnings.append({'code':'XLSX_MERGED_COVERED_CELL_PRESERVED','sheet':name,'cell_ref':ref,
                                 'message':'合并范围非左上角数据完整保留，未冒作可见显示文本。'})
            if _xml(cell['raw_xml']).find('s:f', NS) is not None:
                warnings.append({'code':'XLSX_FORMULA_CACHE_FRESHNESS_UNVERIFIED','sheet':name,'cell_ref':ref,
                                 'message':'只投影已有缓存；没有计算或证明缓存新鲜度，也没有读取外部引用。'})
        ranges = []
        for table in sheet.get('tables', []):
            bounds = _range(table.get('range_ref')); table_node = _xml(table['raw_xml'])
            ranges.append({'range_ref':table['range_ref'], 'bounds':bounds, 'origin':'declared_table', 'table_name':table.get('name'),
                           'header_row': bounds[0] if table_node.get('headerRowCount','1') == '1' else None, 'status':'candidate_not_semantic_truth'})
        if not ranges and cells:
            rows = [p[0] for p in positions.values()]; cols = [p[1] for p in positions.values()]
            bounds = (min(rows),min(cols),max(rows),max(cols))
            ranges.append({'range_ref':_column(bounds[1])+str(bounds[0])+':'+_column(bounds[3])+str(bounds[2]),
                           'bounds':bounds,'origin':'used_cell_bounding_range','table_name':None,'header_row':bounds[0], 'status':'candidate_not_semantic_truth'})
        if len(ranges) > MAX_RANGES: _fail('XLSX_PROJECTION_LIMIT', '表格范围超过有界候选检查限制。')
        headers = []; chart_candidates = []
        for relation in ranges:
            group = [ref for ref,p in positions.items() if _inside(p,relation['bounds'])]
            header_row = relation['header_row']; columns = {}
            for ref in group: columns.setdefault(positions[ref][1], []).append(ref)
            for col, refs in columns.items():
                header_ref = _column(col)+str(header_row) if header_row is not None else None
                header = None
                if header_ref in by_ref and by_ref[header_ref]['display_projection']['display_text']:
                    header = {'cell_ref':header_ref, 'text':by_ref[header_ref]['display_projection']['display_text'],
                              'anchor':_native_anchor(local_segments[header_ref]), 'status':'candidate_not_semantic_truth',
                              'range_ref':relation['range_ref']}
                    headers.append(header)
                numeric = [ref for ref in refs if ref != header_ref and by_ref[ref]['display_projection']['logical_type']=='number'
                           and by_ref[ref]['display_projection']['status'] in {'typed_numeric_projection','derived_projection'}]
                if numeric:
                    chart_candidates.append({'range_ref':relation['range_ref'],'series_column_index':col-1,
                                             'header_candidate':header,'value_cell_refs':sorted(numeric,key=lambda r:positions[r]),
                                             'status':'candidate_not_chart_data_selection','number_and_unit_selection':'requires_explicit_evidence_review'})
                for ref in refs:
                    ctx = local_segments[ref]['metadata']['source_context']
                    ctx['range_candidates'].append({k:copy.deepcopy(v) for k,v in relation.items() if k != 'bounds'})
                    if header and ref != header_ref: ctx['header_candidates'].append(copy.deepcopy(header))
                    units = copy.deepcopy(by_ref[ref]['display_projection']['unit_candidates'])
                    for unit in units:
                        unit.update({'origin':'explicit_number_format','cell_ref':ref,'anchor':_native_anchor(local_segments[ref])})
                    if header:
                        for m in re.finditer(r'[（(]([^()（）]+)[）)]',header['text']):
                            units.append({'text':m[1], 'origin':'header_parenthesized_text', 'status':'candidate_not_semantic_unit',
                                          'cell_ref':header_ref,'anchor':copy.deepcopy(header['anchor'])})
                    ctx['unit_candidates'].extend(units)
        sheet['evidence_header_candidates'] = headers; sheet['evidence_range_candidates'] = [{k:v for k,v in r.items() if k!='bounds'} for r in ranges]
        sheet['chart_candidates'] = chart_candidates
        sheet['visibility_evidence'] = {'hidden_rows':sorted(hidden_rows),'hidden_column_ranges':[list(x) for x in hidden_cols]}
        for rel in sheet.get('relationships', []):
            if rel.get('external'):
                warnings.append({'code':'XLSX_EXTERNAL_RELATIONSHIP_NOT_FETCHED','sheet':name,'relationship_id':rel.get('id'),
                                 'message':'外部关系按原路径保留；未打开、下载或计算。'})
            elif (rel.get('type') or '').endswith('/drawing'):
                warnings.append({'code':'XLSX_DRAWING_SEMANTICS_UNRESOLVED','sheet':name,'relationship_id':rel.get('id'),
                                 'message':'原图形/图表部件保留；本组件只产生单元格图表候选，未解析原图表语义。'})
        if node.findall('s:conditionalFormatting',NS):
            warnings.append({'code':'XLSX_CONDITIONAL_FORMATTING_UNINTERPRETED','sheet':name,
                             'message':'条件格式XML保留；本组件未声称基础格式投影就是条件格式后的最终显示。'})
    if handled != set(segment_map): _fail('XLSX_PROJECTION_ANCHOR_INVALID', '存在未关联原工作表单元格的证据。')
    external_parts = [p['part'] for p in document.get('package_parts', []) if p.get('part','').startswith('xl/externalLinks/')]
    if external_parts: warnings.append({'code':'XLSX_EXTERNAL_LINK_PARTS_NOT_EVALUATED','parts':external_parts,
                                         'message':'外部链接部件完整保留，未获取引用值或刷新公式缓存。'})
    document['evidence_projection'] = {'version':VERSION,'cells':cell_count,'formula_evaluation':'not_executed',
                                       'excel_rendering':'not_executed','semantic_unit_inference':'not_executed',
                                       'boundary':'Only explicit saved cell projections and anchored candidates; full Excel display, formulas, semantics and AC-005 remain unverified.'}
    return document, segments, warnings
