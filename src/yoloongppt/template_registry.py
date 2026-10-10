"""SYS-008 / TPL-001..006: content-addressed, inspectable native template registry."""
import hashlib
import json
from pathlib import Path

from .asset_resolver import allowed_path, _write
from .errors import TaskError
from .templates import parse_template, query_layouts


def register(path, *, source=None, license='unknown', root='/runtime/templates', allowed_roots=None, schemas=None):
    file = allowed_path(path, allowed_roots)
    raw = file.read_bytes()
    pack = parse_template(raw, source=source or str(file), license=license)
    digest = pack['package_sha256']
    stored = _write(root, digest + '.pptx', raw)
    colors = {item['token']: item['value'] if item['kind'] == 'srgbClr' else item['last_color']
              for theme in pack['themes'] for item in theme['colors']}
    fonts = [{'theme': theme['part'], 'role': role, **font} for theme in pack['themes'] for role, items in theme['fonts'].items() for font in items]
    record = {'template_id': 'template_' + digest[:24], 'source': source or str(file), 'license': license,
              'sha256': digest, 'path': str(stored), 'version': 'sha256:' + digest, 'slide_size': pack['slide_size'],
              'template_pack': pack, 'design_tokens': {'theme_colors': colors, 'theme_fonts': fonts,
                  'font_availability': 'not_verified', 'spacing_radius_shadow': 'not_inferred'},
              'preview': {'status': 'structural', 'layouts': [{'part': layout['part'], 'name': layout['name'], 'slots': [
                  {'slot_id': slot['slot_id'], 'role': slot['role'], 'bounds': slot['bounds']} for slot in layout['slots']]} for layout in pack['layouts']]},
              'status': 'partial', 'issues': pack['issues']}
    if schemas: schemas.validate('template-registry-record.schema.json', record)
    _write(root, digest + '.json', json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False).encode('utf-8'))
    return record


def get(template_id, *, root='/runtime/templates', schemas=None):
    if not isinstance(template_id, str) or not template_id.startswith('template_'):
        raise TaskError('TEMPLATE_ID_INVALID', '模板ID无效。', 'TemplateRegistry', ['SYS-008'])
    folder = Path(root).resolve()
    if not folder.is_relative_to(Path('/runtime')):
        raise TaskError('TEMPLATE_REGISTRY_PATH_INVALID', '模板注册表只允许F盘绑定/runtime。', 'TemplateRegistry', ['SYS-008'])
    matches = []
    for file in sorted(folder.glob('*.json')):
        record = json.loads(file.read_text('utf-8'))
        if record.get('template_id') == template_id: matches.append(record)
    if len(matches) != 1:
        raise TaskError('TEMPLATE_NOT_FOUND', '未找到唯一已登记模板。', 'TemplateRegistry', ['SYS-008'])
    record = matches[0]
    path = allowed_path(record['path'], ['/runtime'])
    if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        raise TaskError('TEMPLATE_REGISTRY_CHANGED', '已登记模板文件hash改变。', 'TemplateRegistry', ['SYS-008', 'TPL-001'])
    if schemas: schemas.validate('template-registry-record.schema.json', record)
    return record


def candidates(record, *, content_type='text', minimum_slots=1, slide_size=None):
    return query_layouts(record['template_pack'], content_type=content_type, minimum_slots=minimum_slots, slide_size=slide_size)


def select(task, context, *, schemas=None):
    """Caller template constraint never silently falls back to library defaults."""
    reference = task.get('template_ref')
    if not reference:
        return {'family': 'generic', 'record': None, 'candidates': [{'family': 'generic', 'eligible': True, 'reason': 'No custom/brand/reference template requested; native catalog is selected explicitly.'},
                {'family': 'free_layout', 'eligible': True, 'reason': 'Native geometry compiler is available as explicit alternative.'}], 'fallback': 'fail on incompatible capacity', 'status': 'selected'}
    metadata = next((source.get('metadata', {}) for source in task.get('sources', []) if source.get('locator') == reference), {})
    record = get(reference, schemas=schemas) if reference.startswith('template_') else register(reference, license=metadata.get('license', 'unknown'), schemas=schemas)
    family = 'brand' if metadata.get('brand_locked') else 'reference'
    output_size = context.get('values', {}).get('aspect_ratio', '16:9')
    size = record['slide_size']
    ratio = size['width_emu'] / size['height_emu']
    if output_size == '16:9' and abs(ratio - 16/9) > 0.01:
        raise TaskError('TEMPLATE_SIZE_MISMATCH', '所选模板与16:9输出不符；须显式比例转换，未换用默认模板。', 'TemplateRegistry', ['DEC-028', 'TPL-014'])
    return {'family': family, 'record': record, 'candidates': candidates(record), 'fallback': 'fail unless caller explicitly supplies fallback template', 'status': 'selected_partial_capacity_unmeasured'}
