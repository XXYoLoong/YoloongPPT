"""Measured native geometry, retaining literal text and readable font sizes.

This is conservative font measurement, not a claim of render/semantic acceptance.
"""
import copy
import math
from functools import lru_cache

from PIL import ImageFont

from .errors import TaskError
from .writer import capacity, FONT_FILE

VERSION = 'adaptive-layout-1'
BOTTOM = 6.54


def fail(code, message, details=None):
    raise TaskError(code, message, 'AdaptiveLayout', ['DEC-018', 'TPL-007', 'TPL-012', 'AC-015'], details or [])


@lru_cache(maxsize=16)
def _font(size, font_file):
    return ImageFont.truetype(font_file, int(size * 4 / 3))


@lru_cache(maxsize=8192)
def _required_height(texts, width, size, margin, spacing, font_file):
    font = _font(size, font_file); pixels = (width - 2 * margin) * 96; lines = 0
    for text in texts:
        current = 0; lines += 1
        for char in text:
            if char == '\n':
                current = 0; lines += 1; continue
            advance = font.getlength(char)
            if current + advance > pixels:
                lines += 1; current = advance
            else:
                current += advance
    line_height = max(size * 4 / 3 * 1.25, sum(font.getmetrics()))
    used = lines * line_height + max(0, len(texts)-1) * spacing * 4/3
    # Positive pixel/rounding allowance beyond the identical writer formula.
    return math.ceil((used / 96 + margin * 2 + .04) * 1000) / 1000


def required_height(texts, width, size, margin=0, spacing=0, font_file=None):
    """Use the writer's font and line rules, with a positive pixel safety margin."""
    if width <= margin * 2:
        fail('ADAPTIVE_SLOT_WIDTH_INVALID', '槽位宽度不足，未删除字符。')
    return _required_height(tuple(texts), width, size, margin, spacing, font_file or FONT_FILE)


def content_geometry(content):
    """The feasible native editorial/table grammar used by content pagination."""
    title_h = max(1.25, required_height([content['title']], 11.95, 32))
    if title_h > BOTTOM - .6 - .6:
        fail('ADAPTIVE_TITLE_CAPACITY', '完整标题无法在可读字号下留出正文区域；未截断标题。',
             [{'title_characters': len(content['title']), 'required_height': title_h}])
    body_y = max(2.0, .6 + title_h + .16)
    height = min(4.35, BOTTOM - body_y)
    if content['kind'] == 'text':
        body = [0.72, body_y, 11.85, height]
        size, spacing = 24, 15
        data = None
    else:
        body_y = max(1.96, .6 + title_h + .16)
        height = min(4.55, BOTTOM - body_y)
        body = [.7, body_y, 3.25, height]
        size, spacing = 21, 16
        data = [4.32, body_y, 8.28, min(4.58, BOTTOM - body_y)]
    return {'title_bounds': [.7, .6, 11.95, title_h], 'body_bounds': body,
            'body_size': size, 'body_spacing': spacing, 'data_bounds': data,
            'table_size': 16, 'minimum_size': 16, 'measurement': VERSION}


def fits_body(items, geometry):
    try:
        capacity(items, geometry['body_bounds'], geometry['body_size'],
                 padding=0, paragraph_spacing=geometry['body_spacing'])
        return required_height(items, geometry['body_bounds'][2], geometry['body_size'],
                               spacing=geometry['body_spacing']) <= geometry['body_bounds'][3]
    except TaskError as error:
        if error.code != 'TEXT_CAPACITY_EXCEEDED':
            raise
        return False


def table_capacity(columns, rows, bounds):
    """Writer uses equal cells; every row must accommodate the tallest cell."""
    width = bounds[2] / len(columns)
    heights = [required_height([str(cell)], width, 16, .07) for row in [columns, *rows] for cell in row]
    row_h = max(heights)
    return max(0, math.floor(bounds[3] / row_h) - 1), row_h


def fit_elements(content, elements, page_style, templates=None):
    """Expand overflowing title and move related geometry; never change text/font.

    Caller may set templates={'geometry_locked': True}. Locked slots fail rather
    than moving outside their declared geometry. Native blank-master execution
    keeps the master/theme separately; it does not imply locked slot geometry.
    """
    result, style = copy.deepcopy(elements), copy.deepcopy(page_style)
    if templates is not None and not isinstance(templates, dict):
        fail('ADAPTIVE_TEMPLATE_INPUT_INVALID', '模板容量上下文必须为明确对象。')
    changes = []
    title = next((e for e in result if e.get('slot_key') == 'title'), None)
    if title is None:
        fail('ADAPTIVE_TITLE_SLOT_MISSING', '缺少标题槽位。')
    minimum = style.get('minimum_size', 16)
    if any(e.get('font_size', minimum) < minimum for e in result):
        fail('ADAPTIVE_UNREADABLE_FONT', '元素字号低于声明的最小字号。')
    original = copy.deepcopy(title['bounds'])
    fmt = title.get('format', {})
    needed = required_height(title['text'], original[2], title['font_size'],
                             fmt.get('margin', .12), fmt.get('paragraph_spacing', 10),
                             title.get('typography', {}).get('font_file'))
    if needed > original[3]:
        if templates and templates.get('geometry_locked'):
            fail('ADAPTIVE_TEMPLATE_GEOMETRY_LOCKED', '模板槽位被锁定，标题超容量时未擅自移动。')
        # Side-by-side cover/closing title grammar cannot consume adjacent body.
        # It can reject this candidate; editorial is independently evaluated.
        if original[0] + original[2] < 12:
            fail('ADAPTIVE_CANDIDATE_TITLE_CAPACITY', '当前窄标题候选无法容纳完整标题。')
        if original[1] + needed + .16 >= BOTTOM:
            fail('ADAPTIVE_TITLE_CAPACITY', '完整标题超过可读页面容量。')
        title['bounds'][3] = needed
        old_top = min((e['bounds'][1] for e in result if e.get('role') not in ('title', 'footer')), default=BOTTOM)
        new_top = max(old_top, original[1] + needed + .16)
        if new_top > old_top:
            old_bottom = max((e['bounds'][1] + e['bounds'][3] for e in result if e.get('role') not in ('title', 'footer')), default=BOTTOM)
            scale = min(1, (BOTTOM - new_top) / (old_bottom - old_top))
            if scale <= 0:
                fail('ADAPTIVE_GEOMETRY_CAPACITY', '标题后没有正文空间。')
            for e in result:
                if e.get('role') in ('title', 'footer'):
                    continue
                b = e['bounds']; b[1] = new_top + (b[1] - old_top) * scale; b[3] *= scale
                if e['type'] == 'connector':
                    for endpoint in ('start', 'end'):
                        e['data'][endpoint][1] = new_top + (e['data'][endpoint][1] - old_top) * scale
        changes.append({'slot_key': 'title', 'before_bounds': original, 'after_bounds': title['bounds'],
                        'action': 'expand_title_and_reflow_geometry', 'font_size_preserved': title['font_size']})
    measurements = []
    for element in result:
        fmt = element.get('format', {})
        if element['type'] == 'text':
            required = required_height(element['text'], element['bounds'][2], element['font_size'],
                                       fmt.get('margin', .12), fmt.get('paragraph_spacing', 10),
                                       element.get('typography', {}).get('font_file'))
            if required > element['bounds'][3]:
                fail('ADAPTIVE_NATIVE_TEXT_CAPACITY', '真实字体行高超出原生槽位，未缩小字号或隐藏正文。',
                     [{'slot_key': element['slot_key'], 'required_height': required, 'bounds': element['bounds']}])
            witness = capacity(element['text'], element['bounds'], element['font_size'],
                               padding=fmt.get('margin', .12), paragraph_spacing=fmt.get('paragraph_spacing', 10),
                               font_file=element.get('typography', {}).get('font_file'))
            measurements.append({'slot_key': element['slot_key'], **witness})
        elif element['type'] == 'table':
            data = element['data']; rows = [data['columns'], *data['rows']]
            for row in rows:
                for cell in row:
                    capacity([str(cell)], [0, 0, element['bounds'][2]/len(data['columns']),
                             element['bounds'][3]/len(rows)], element['font_size'], padding=.07, paragraph_spacing=0)
    return result, style, {'version': VERSION, 'status': 'measured', 'changes': changes,
        'measurements': measurements, 'text_preserved': True, 'font_sizes_preserved': True,
        'semantic_acceptance': 'not_claimed', 'render_acceptance': 'required'}
