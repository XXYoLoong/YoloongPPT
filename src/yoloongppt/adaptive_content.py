"""DEC-014..020 literal pagination with explicit budget and cell provenance."""
import copy
import hashlib
import json
import re

from .adaptive_layout import content_geometry, fits_body, table_capacity
from .errors import TaskError

VERSION = 'adaptive-content-1'
TABLE_PAGINATION_NOTICE = '【原表分页展示，完整内容见同标题各页】'
IDS = ['DEC-014', 'DEC-015', 'DEC-018', 'DEC-020', 'TPL-007', 'TPL-012', 'AC-014', 'AC-015']


def _fail(code, message, details=None):
    raise TaskError(code, message, 'AdaptiveContent', IDS, details or [])


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def budget_policy(context, count):
    """Use selected normalized constraint provenance, never infer hard as soft."""
    constraints = context.get('constraints', {})
    hard = [c for c in constraints.get('hard', []) if c.get('field') in ('page_count', 'page_target')]
    soft = [c for c in constraints.get('soft', []) if c.get('field') in ('page_count', 'page_target')
            and c.get('disposition', 'applied') == 'applied']
    kind = 'hard' if hard else 'soft' if soft else 'default'
    declared = context.get('values', {}).get('adaptive_policy', {})
    return {'page_budget': {'kind': kind, 'target': count, 'minimum': count if hard else 1,
        'maximum': count if hard else 30, 'provenance': copy.deepcopy(hard or soft or [
            c for c in constraints.get('defaults', []) if c.get('field') in ('page_count', 'page_target') and c.get('used')])},
        'table_key_columns': copy.deepcopy(declared.get('table_key_columns', {}))}


def _policy(policy, count):
    policy = copy.deepcopy(policy) if policy is not None else {
        'page_budget': {'kind': 'hard', 'target': count, 'minimum': count, 'maximum': count},
        'table_key_columns': {}}
    if not isinstance(policy, dict) or set(policy) - {'page_budget', 'table_key_columns', 'assumption_markers'}:
        _fail('ADAPTIVE_POLICY_INVALID', '容量策略字段未登记，未忽略。')
    b = policy.get('page_budget')
    if not isinstance(b, dict) or set(b) - {'kind', 'target', 'minimum', 'maximum', 'provenance'} or b.get('kind') not in ('hard', 'soft', 'default'):
        _fail('ADAPTIVE_PAGE_BUDGET_INVALID', '需要明确 hard/soft/default 页预算。')
    b.setdefault('minimum', b.get('target') if b['kind'] == 'hard' else 1)
    b.setdefault('maximum', b.get('target') if b['kind'] == 'hard' else 30)
    if any(type(b.get(k)) is not int or not 1 <= b[k] <= 30 for k in ('target', 'minimum', 'maximum')) or not b['minimum'] <= b['target'] <= b['maximum']:
        _fail('ADAPTIVE_PAGE_BUDGET_INVALID', '页预算必须为1至30且范围包含目标。')
    if b['kind'] == 'hard' and (b['minimum'] != b['target'] or b['maximum'] != b['target']):
        _fail('ADAPTIVE_HARD_BUDGET_CHANGED', '硬页数必须保持精确目标，不允许隐式改为软预算。')
    if count != b['target']:
        _fail('ADAPTIVE_INPUT_PAGE_COUNT', '初始规划必须满足原目标页数，不补空页或丢页。', [{'input': count, 'target': b['target']}])
    keys = policy.setdefault('table_key_columns', {})
    if not isinstance(keys, dict):
        _fail('ADAPTIVE_TABLE_KEY_POLICY_INVALID', '关键列必须按原页面索引显式声明。')
    policy.setdefault('assumption_markers', {})
    if not isinstance(policy['assumption_markers'], dict) or any(not isinstance(k, str) or not isinstance(v, str) or not v for k, v in policy['assumption_markers'].items()):
        _fail('ADAPTIVE_ASSUMPTION_MARKER_INVALID', '假设标记映射必须为非空原文字串。')
    for key, value in keys.items():
        if not isinstance(key, str) or not key.isdigit() or not 0 <= int(key) < count or not isinstance(value, list) or not value or any(type(c) is not int or c < 0 for c in value) or len(value) != len(set(value)):
            _fail('ADAPTIVE_TABLE_KEY_POLICY_INVALID', '关键列策略必须引用存在的原页面和唯一原列索引。')
    return policy


def _sentences(text):
    """Explicit punctuation/newline boundaries only; every character retained.

    Decimal dots, abbreviations and unknown sentence semantics are not inferred.
    Oversized indivisible fragments fail instead of arbitrary character slicing.
    """
    ends = []
    for match in re.finditer(r'[。！？；!?;](?:[ \t]*\r?\n)?|\r?\n|\.(?=\s+[A-Z\u4e00-\u9fff])', text):
        if match[0] == '.':
            word = re.search(r'([A-Za-z.]+)$', text[:match.start()])
            if word and (len(word[1]) <= 2 or word[1].lower() in ('dr', 'mr', 'mrs', 'ms', 'prof', 'inc', 'etc', 'vs')):
                continue
        ends.append(match.end())
    result, start = [], 0
    for end in ends + [len(text)]:
        if end > start:
            result.append((start, end, text[start:end])); start = end
    return result


def _markers(slide, policy, original_index):
    refs = slide.get('assumption_refs', [])
    values = [s for s in slide['body'] if '【假设】' in s or '【推算】' in s or '【已选来源】' in s]
    for ref in refs:
        marker = policy['assumption_markers'].get(ref)
        if marker is not None and marker not in values:
            if not isinstance(marker, str) or not marker or not any(marker in s for s in slide['body']):
                _fail('ADAPTIVE_ASSUMPTION_MARKER_INVALID', '假设标记必须已在原正文中可见，未从备注或模型解释发明标记。')
            values.append(marker)
    if refs and not values:
        _fail('ADAPTIVE_ASSUMPTION_VISIBILITY_REQUIRED', '含假设引用的页面缺少可见假设标记，不能分页后隐藏。', [{'page': original_index}])
    return values


def _body_pages(slide, geometry, markers, original_index):
    pieces = []
    for i, text in enumerate(slide['body']):
        reserved = [m for m in markers if m not in text]
        segments = [(0, len(text), text)] if fits_body([text] + reserved, geometry) else _sentences(text)
        for start, end, value in segments:
            if not fits_body([value], geometry):
                _fail('ADAPTIVE_INDIVISIBLE_CONTENT', '完整语义块或明确句界片段仍超出可读容量；未截字或隐藏正文。',
                      [{'page': original_index, 'body_item': i, 'start': start, 'end': end, 'characters': len(value)}])
            pieces.append({'body_item': i, 'start': start, 'end': end, 'text': value})
    pages, current = [], []
    for piece in pieces:
        values = [p['text'] for p in current + [piece]]
        additions = [m for m in markers if not any(m in text for text in values)]
        if current and not fits_body(values + additions, geometry):
            pages.append(current); current = []
            values = [piece['text']]; additions = [m for m in markers if m not in piece['text']]
        if not fits_body(values + additions, geometry):
            _fail('ADAPTIVE_MARKER_CAPACITY', '完整片段与必须可见标记不能共同容纳；未隐藏标记。', [{'page': original_index}])
        current.append(piece)
    if current or not pages:
        pages.append(current)
    return pages


def _table_tiles(slide, geometry, policy, index):
    table = slide['table']
    if not table or not table['columns'] or any(len(r) != len(table['columns']) for r in table['rows']):
        _fail('ADAPTIVE_TABLE_WIDTH', '表格列数必须一致，未补齐或删除单元格。', [{'page': index}])
    bounds = geometry['data_bounds']; allcols = list(range(len(table['columns'])))

    def capacity(cols):
        try:
            return table_capacity([table['columns'][c] for c in cols],
                                  [[row[c] for c in cols] for row in table['rows']], bounds)[0]
        except TaskError as error:
            if error.code in ('ADAPTIVE_SLOT_WIDTH_INVALID', 'TEXT_CAPACITY_EXCEEDED'):
                return 0
            raise

    groups = [allcols]
    keys = policy['table_key_columns'].get(str(index), policy['table_key_columns'].get(index, []))
    if not isinstance(keys, list) or any(type(c) is not int or c not in allcols for c in keys) or len(keys) != len(set(keys)):
        _fail('ADAPTIVE_TABLE_KEY_POLICY_INVALID', '重复关键列必须为原表有效唯一列索引。', [{'page': index}])
    if capacity(allcols) < 1:
        if not keys:
            _fail('ADAPTIVE_TABLE_KEY_COLUMNS_REQUIRED', '多列容量不足；需显式指定重复关键列，未猜测首列含义。', [{'page': index, 'columns': len(allcols)}])
        others = [c for c in allcols if c not in keys]
        if not others or capacity(sorted(keys)) < 1:
            _fail('ADAPTIVE_TABLE_CELL_CAPACITY', '关键列本身超容量，未缩字或删除其内容。', [{'page': index}])
        groups, group = [], []
        for col in others:
            proposed = sorted(keys + group + [col])
            if group and capacity(proposed) < 1:
                groups.append(sorted(keys + group)); group = []
            if capacity(sorted(keys + group + [col])) < 1:
                _fail('ADAPTIVE_TABLE_CELL_CAPACITY', '原表完整单元格与重复关键列不能在页面共同容纳。', [{'page': index, 'column': col}])
            group.append(col)
        if group:
            groups.append(sorted(keys + group))
    tiles = []
    for columns in groups:
        max_rows = capacity(columns)
        if max_rows < 1:
            _fail('ADAPTIVE_TABLE_CELL_CAPACITY', '单行表格超过可读容量。', [{'page': index, 'columns': columns}])
        for start in range(0, max(1, len(table['rows'])), max_rows):
            row_indices = list(range(start, min(start + max_rows, len(table['rows']))))
            tiles.append({'columns': columns, 'rows': row_indices,
                'table': {**copy.deepcopy(table), 'columns': [table['columns'][c] for c in columns],
                          'rows': [[table['rows'][r][c] for c in columns] for r in row_indices]},
                'repeated_key_columns': keys if len(groups) > 1 else []})
    return tiles


def adapt(proposal, policy=None, templates=None, schemas=None, artifacts=None):
    """Return a new proposal and an auditable mapping; no model or rewrite call."""
    if schemas:
        schemas.validate('generation-model.schema.json', proposal)
    original = copy.deepcopy(proposal); policy = _policy(policy, len(original['slides']))
    for page, cols in policy['table_key_columns'].items():
        declared_table = original['slides'][int(page)].get('table')
        if original['slides'][int(page)]['kind'] != 'table' or not declared_table or any(c >= len(declared_table['columns']) for c in cols):
            _fail('ADAPTIVE_TABLE_KEY_POLICY_INVALID', '关键列策略引用非表格页或不存在的原列。', [{'page': int(page), 'columns': cols}])
    if schemas:
        schemas.validate('adaptive-content-policy.schema.json', policy)
    output = copy.deepcopy(original); output['slides'] = []; mappings = []
    if templates is not None and not isinstance(templates, dict):
        _fail('ADAPTIVE_TEMPLATE_INPUT_INVALID', '模板容量上下文必须为明确对象，未猜测列表项。')
    if templates and templates.get('geometry_locked'):
        _fail('ADAPTIVE_TEMPLATE_GEOMETRY_LOCKED', '锁定模板的自适应槽位契约尚未接入，未擅自改变。')
    for index, slide in enumerate(original['slides']):
        geometry = content_geometry(slide); markers = _markers(slide, policy, index)
        unit_label = slide['table'].get('units', '') if slide['kind'] == 'table' and slide.get('table') else ''
        tiles = _table_tiles(slide, geometry, policy, index) if slide['kind'] == 'table' else [None]
        pagination_notice = TABLE_PAGINATION_NOTICE if slide['kind'] == 'table' and len(tiles) > 1 else None
        reserved = markers + ([unit_label] if unit_label and unit_label not in markers else [])
        if pagination_notice:
            reserved.append(pagination_notice)
        body_geometry = geometry
        # Large indivisible visual captions can continue in full-width text
        # pages. Original visual object remains exactly once (tables tiled).
        captions_as_text = slide['kind'] != 'text' and any(not fits_body([s], geometry) and
            any(not fits_body([part[2]], geometry) for part in _sentences(s)) for s in slide['body'])
        if captions_as_text:
            body_geometry = content_geometry({**slide, 'kind': 'text'})
        groups = _body_pages(slide, body_geometry, reserved, index)
        mapping = {'original_page': index, 'original_title': slide['title'], 'original_body_sha256': _digest(slide['body']),
            'original_notes_sha256': _digest(slide['notes']), 'evidence_refs': slide['evidence_refs'],
            'assumption_refs': slide.get('assumption_refs', []), 'outputs': [], 'geometry': geometry,
            'original_table_sha256': _digest(slide['table']) if slide['kind'] == 'table' else None,
            'table_pagination': {'is_paginated': bool(pagination_notice), 'tile_count': len(tiles) if slide['kind'] == 'table' else 0,
                'notice': pagination_notice, 'source_kind': 'execution_metadata', 'business_fact': False},
            'original_visual_sha256': _digest({k: slide[k] for k in ('image', 'images', 'diagram') if k in slide}),
            'visual_object_policy': 'original visual declaration preserved once; visible text continuation carries no visual declaration',
            'gallery_capacity_policy': 'conservative single-image sidebar caption capacity; final gallery geometry is measured independently' if slide.get('images') else None}

        def append(group, tile, visual):
            page = copy.deepcopy(slide)
            page['body'] = [part['text'] for part in group]
            repeated = [m for m in markers if not any(m in text for text in page['body'])]
            page['body'].extend(repeated)
            unit_added = bool(visual and unit_label and not any(unit_label in text for text in page['body']))
            if unit_added:
                page['body'].append(unit_label)
            notice_added = bool(visual and pagination_notice and not any(pagination_notice in text for text in page['body']))
            if notice_added:
                page['body'].append(pagination_notice)
            if not visual:
                page.update(kind='text', table=None, chart=None)
                page.pop('image', None); page.pop('images', None); page.pop('diagram', None)
            elif tile:
                page['table'] = tile['table']
            entry = {'output_page': len(output['slides']), 'kind': page['kind'],
                'body_segments': copy.deepcopy(group), 'repeated_visible_markers': repeated,
                'visible_unit_label': {'text': unit_label, 'source': 'table.units', 'added_to_body': unit_added} if visual and unit_label else None,
                'visible_pagination_notice': {'text': pagination_notice, 'source_kind': 'execution_metadata',
                    'business_fact': False, 'added_to_body': notice_added} if visual and pagination_notice else None,
                'table_coordinates': None if tile is None else {k: v for k, v in tile.items() if k != 'table'},
                'notes_unchanged': page['notes'] == slide['notes'], 'title_unchanged': page['title'] == slide['title']}
            if not fits_body(page['body'], content_geometry(page)):
                _fail('ADAPTIVE_MARKER_CAPACITY', '原可见标记或正文超出继续页容量。', [{'page': index}])
            output['slides'].append(page); mapping['outputs'].append(entry)

        # Body segments retain order; extra visual/table tiles follow the first
        # original visual page. Repeated headers/key cells are marked explicitly.
        if slide['kind'] == 'text':
            for group in groups:
                append(group, None, False)
        elif captions_as_text:
            for group in groups:
                append(group, None, False)
            for tile in tiles:
                append([], tile, True)
        else:
            append(groups[0], tiles[0], True)
            for group in groups[1:]:
                append(group, None, False)
            for tile in tiles[1:]:
                append([], tile, True)
        if len(output['slides']) > policy['page_budget']['maximum']:
            _fail('ADAPTIVE_PAGE_BUDGET_EXCEEDED', '完整可读内容需要的页数超出原预算；未裁内容或改变硬约束。',
                  [{'required_pages_at_least': len(output['slides']), 'page_budget': policy['page_budget'],
                    'source_page': index}])
        # Assert conservation before returning, not merely write a claim.
        for item, text in enumerate(slide['body']):
            parts = [p for entry in mapping['outputs'] for p in entry['body_segments'] if p['body_item'] == item]
            if ''.join(p['text'] for p in parts) != text or [(p['start'],p['end']) for p in parts] != list(zip([0]+[p['end'] for p in parts[:-1]], [p['end'] for p in parts])):
                _fail('ADAPTIVE_TEXT_CONSERVATION_FAILED', '正文原字符映射不完整。', [{'page': index, 'body_item': item}])
        if slide['kind'] == 'table':
            seen = {(r,c) for entry in mapping['outputs'] if entry['table_coordinates'] for r in entry['table_coordinates']['rows'] for c in entry['table_coordinates']['columns']}
            expected = {(r,c) for r in range(len(slide['table']['rows'])) for c in range(len(slide['table']['columns']))}
            if seen != expected:
                _fail('ADAPTIVE_TABLE_CONSERVATION_FAILED', '原表单元格坐标未全部覆盖。')
            for entry in mapping['outputs']:
                coord = entry['table_coordinates']
                if coord is None:
                    continue
                data = output['slides'][entry['output_page']]['table']; table = slide['table']
                if data['columns'] != [table['columns'][c] for c in coord['columns']] or data['rows'] != [[table['rows'][r][c] for c in coord['columns']] for r in coord['rows']] or data.get('units') != table.get('units'):
                    _fail('ADAPTIVE_TABLE_CONSERVATION_FAILED', '原表单元格值、列顺序或单位被改变。')
        elif slide['kind'] in ('image', 'diagram'):
            originals = [output['slides'][entry['output_page']] for entry in mapping['outputs'] if entry['kind'] == slide['kind']]
            if len(originals) != 1 or _digest({k: originals[0][k] for k in ('image', 'images', 'diagram') if k in originals[0]}) != mapping['original_visual_sha256']:
                _fail('ADAPTIVE_VISUAL_CONSERVATION_FAILED', '原视觉声明未完整保留一次，未静默丢图库或图示。')
        mappings.append(mapping)
    count = len(output['slides']); budget = policy['page_budget']
    if not budget['minimum'] <= count <= budget['maximum']:
        _fail('ADAPTIVE_PAGE_BUDGET_EXCEEDED', '完整可读内容需要的页数超出原预算；未裁内容或改变硬约束。',
              [{'required_pages': count, 'page_budget': budget, 'source_page_output_counts': [len(m['outputs']) for m in mappings]}])
    report = {'version': VERSION, 'status': 'adapted', 'system_acceptance': 'not_claimed', 'policy': policy,
        'input_pages': len(original['slides']), 'output_pages': count, 'deviation': count - budget['target'],
        'page_mappings': mappings, 'input_sha256': _digest(original), 'output_sha256': _digest(output),
        'execution_metadata_labels': [{'text': TABLE_PAGINATION_NOTICE, 'source_kind': 'execution_metadata',
            'business_fact': False, 'original_page': m['original_page'],
            'output_pages': [e['output_page'] for e in m['outputs'] if e['table_coordinates']],
            'tile_count': m['table_pagination']['tile_count']}
            for m in mappings if m['table_pagination']['is_paginated']],
        'conservation': {'all_body_characters': True, 'all_table_cells': True, 'titles': True,
                         'notes_unchanged': True, 'evidence_refs': True, 'assumption_refs': True},
        'fallback': 'structured_failure_without_truncation', 'remaining_limits': [
            'explicit sentence boundaries only; no semantic paraphrase or compression',
            'content pagination uses declared default Noto native grammar; selected typography is remeasured before writing',
            'locked template slot adaptation requires a declared geometry contract',
            'physical render and independent fact review remain required']}
    if schemas:
        schemas.validate('adaptive-content-result.schema.json', report)
        schemas.validate('generation-model.schema.json', output)
    if artifacts:
        artifacts.json('adaptive-content-result.json', report)
    return output, report
