"""AC-012 / AST-007: finite native gallery alternatives without invented assets.

Only declared image order, roles, crop policy and approved literal captions are
used. Scores describe geometry/retained pixels/DPI, not semantic relevance.
"""
import copy
import math

from .artifacts import entity
from .errors import TaskError
from .layout_decisions import image_fit, geometry, typography, visual_style
from .adaptive_layout import required_height


def _fail(code, message, details=None):
    raise TaskError(code, message, 'GalleryLayout', ['AC-012', 'AST-007', 'DEC-030', 'DEC-036'], details or [])


def _text(slot, role, items, bounds, size, refs, color, **fmt):
    return {'object_id': entity('object'), 'type': 'text', 'role': role, 'slot_key': slot,
            'text': list(items), 'bounds': bounds, 'font_size': size, 'source_refs': list(refs),
            'format': {'color': color, 'margin': 0, 'paragraph_spacing': 0, **fmt}}


def _arrangement(content, style, columns, order=0, count=1):
    images = content.get('images')
    if not isinstance(images, list) or not 1 <= len(images) <= 8:
        _fail('GALLERY_COUNT_INVALID', 'gallery必须有1–8张已解析图片。')
    ids = [image.get('asset_id') for image in images]
    if any(not key for key in ids) or len(set(ids)) != len(ids):
        _fail('IMAGE_ASSET_DUPLICATE', '图片asset_id缺失或重复，无法建立稳定槽位。')
    refs = content.get('evidence_refs', [])
    rows = math.ceil(len(images) / columns)
    # Preserve every paragraph; capacity failure rejects the candidate instead of
    # shrinking text or hiding body/captions behind the image grid.
    body = content.get('body', [])
    title_height = max(.95, required_height([content['title']], 11.95, 30, margin=0, spacing=0))
    title_bottom = .45 + title_height
    top = max(1.72, title_bottom + .2)
    elements = [_text('title', 'title', [content['title']], [.7, .45, 11.95, title_height], 30, refs, style['foreground'], bold=True)]
    if body:
        body_height = max(.42 * len(body), required_height(body, 11.95, 18, margin=0, spacing=0))
        body_y = max(1.48, title_bottom + .16)
        elements.append(_text('body', 'body', body, [.7, body_y, 11.95, body_height], 18, refs, style['foreground']))
        top = body_y + body_height + .2
    bottom = 6.52; gap = .18; width = (11.95-gap*(columns-1))/columns
    cell_height = (bottom-top-gap*(rows-1))/rows
    if cell_height <= .45: _fail('GALLERY_CAPACITY_UNSUPPORTED', '正文占满页面，未删正文或缩小字号。')
    measurements = []
    for index, image in enumerate(images):
        caption = image.get('caption', '')
        caption_height = .46 if caption else 0
        x = .7 + (index % columns) * (width + gap)
        y = top + (index // columns) * (cell_height + gap)
        bounds = [x, y, width, cell_height-caption_height-(.08 if caption else 0)]
        if bounds[3] <= .15: _fail('GALLERY_CAPACITY_UNSUPPORTED', '图注与图片无法保留正尺寸。')
        fit = image_fit(image, bounds)
        minimum = image.get('minimum_dpi', 96)
        if isinstance(minimum, bool) or not isinstance(minimum, (int, float)) or not math.isfinite(minimum) or minimum < 96:
            _fail('IMAGE_MINIMUM_DPI_INVALID', '最低DPI必须为至少96的有限数。')
        effective_dpi = min(image['width_px']*(1-fit['crop'][0]-fit['crop'][2])/fit['bounds'][2],
                            image['height_px']*(1-fit['crop'][1]-fit['crop'][3])/fit['bounds'][3])
        retained = (1-fit['crop'][0]-fit['crop'][2])*(1-fit['crop'][1]-fit['crop'][3])
        measurements.append({'asset_id': image['asset_id'], 'slot_key': 'asset.'+image['asset_id'],
            'declared_fit': image['fit'], 'focal_point': image.get('focal_point'), 'fit': fit,
            'minimum_dpi': minimum, 'effective_dpi_unrounded': effective_dpi, 'dpi_pass': effective_dpi >= minimum,
            'retained_pixel_fraction': round(retained, 6), 'caption': caption,
            'caption_source_refs': image.get('caption_source_refs', []),
            'aspect_check': 'source aspect preserved after explicit crop; no stretch',
            'semantic_relevance': 'independent_review_pending'})
        elements.append({'object_id': entity('object'), 'type': 'image', 'role': 'asset',
            'slot_key': 'asset.'+image['asset_id'], 'data': copy.deepcopy(image),
            'bounds': bounds, 'font_size': 16, 'source_refs': image.get('source_refs', refs)})
        if caption:
            elements.append(_text('caption.'+image['asset_id'], 'body', [caption],
                [x, y+cell_height-caption_height, width, caption_height], 16,
                image.get('caption_source_refs', []), style['foreground']))
    elements.append(_text('footer', 'footer', [f'{order+1:02d} / {count:02d}'], [.7, 6.83, 11.95, .38], 16, [], style['accent']))
    geometry(elements); typography(elements, style); visual_style(elements, style)
    low = [item for item in measurements if not item['dpi_pass']]
    if low: _fail('GALLERY_IMAGE_DPI_INSUFFICIENT', '图片在实际适配尺寸低于最低DPI，未删图、替图或虚构放大。', low)
    return elements, measurements


def evaluate(content, style):
    """Return all policy scores/rejections and the deterministic selected grid."""
    records = []
    for columns in dict.fromkeys([min(4, len(content.get('images', []))), 3, 2, 1]):
        if columns < 1: continue
        record = {'candidate': f'gallery.{columns}columns', 'columns': columns,
            'eligible': False, 'score': None, 'score_semantics': 'geometric retained-pixel ratio and occupied native area; not semantic confidence'}
        try:
            elements, images = _arrangement(content, style, columns)
            occupied = sum(item['fit']['bounds'][2]*item['fit']['bounds'][3] for item in images)
            retained = sum(item['retained_pixel_fraction'] for item in images)/len(images)
            score = round(100*retained + occupied, 6)
            record.update(eligible=True, score=score, images=images, occupied_image_area=round(occupied,6),
                          mean_retained_pixels=round(retained,6), reason='every native image and original text passed geometry/font/contrast/DPI gates')
            title = next(e for e in elements if e['slot_key'] == 'title')
            record['adaptive_title'] = {'before_bounds': [.7, .45, 11.95, .95],
                'after_bounds': title['bounds'], 'expanded': title['bounds'][3] > .95,
                'font_size_preserved': 30, 'title_text_preserved': True,
                'mechanism': 'actual installed Noto glyph advances and ascent/descent; body/grid move below measured title'}
        except TaskError as error:
            record['rejection'] = {'code': error.code, 'message': error.message, 'details': error.details}
        records.append(record)
    eligible = [item for item in records if item['eligible']]
    return {'version': 'native-gallery-1', 'candidates': records,
            'selected': max(eligible, key=lambda item: item['score'])['candidate'] if eligible else None,
            'tie_break': 'declared grid order', 'all_images_preserved': True,
            'semantic_selection': 'explicit caller/model choice; independent review pending',
            'face_object_aware_crop': 'not_implemented; focal point is caller/model declared',
            'system_acceptance': 'not_claimed'}


def candidate(content, order, count, style):
    trace = evaluate(content, style)
    if trace['selected'] is None:
        _fail('GALLERY_CAPACITY_UNSUPPORTED', '全部多图候选失败，未降级成单图或文本。', trace['candidates'])
    selected = next(item for item in trace['candidates'] if item['candidate'] == trace['selected'])
    elements, _ = _arrangement(content, style, selected['columns'], order, count)
    page_style = copy.deepcopy(style); page_style['gallery_selection'] = trace
    # Return original policy/bounds; DEC-036 applies the fit exactly once.
    return elements, page_style
