"""EXEC-20261012-01 / IN-003..005,008,016, SYS-003: local Docling fusion.

Docling owns conversion, layout, table recognition and OCR. Native OOXML evidence
supplements fields that Docling does not preserve (formula caches, relationships,
notes, exact paragraph/cell anchors). Neither parser establishes semantic truth.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import math
import os
import threading
from pathlib import Path

from .errors import TaskError
from . import input_formats, docx_evidence, xlsx_evidence, assets

# Attest the code loaded in this process, rather than subsequently edited bind
# files. The project restart loads a new version; old workers keep their true ID.
_VERSION_SOURCES={name:Path(__file__).with_name(name).read_bytes() for name in
    ['docling_adapter.py','input_formats.py','docx_evidence.py','xlsx_evidence.py','assets.py']}

DOCLING_VERSION = '2.138.0'
SUPPORTED = {'docx', 'pdf', 'image', 'xlsx', 'html'}
MAX_RAW = 64 * 1024 * 1024
MAX_PAGES = 256
MAX_SEGMENTS = 65536
_LOCK = threading.RLock()
_CONVERTERS = {}


def _fail(code, message, details=None):
    raise TaskError(code, message, 'DoclingAdapter',
                    ['IN-003', 'IN-004', 'IN-005', 'IN-008', 'IN-016', 'SYS-003'], details or [])


def _runtime():
    """Product models, scratch and caches live on the F-backed /runtime bind."""
    if os.name != 'posix' or not Path('/runtime').is_dir():
        _fail('DOCLING_RUNTIME_REQUIRED', 'Docling须在项目Docker运行时执行，禁止主机缓存或临时文件。')
    paths = {'TMPDIR': '/runtime/input-parser-temp', 'HF_HOME': '/runtime/cache/huggingface',
             'XDG_CACHE_HOME': '/runtime/cache', 'TORCH_HOME': '/runtime/cache/torch'}
    for name, value in paths.items():
        actual = Path(os.environ.get(name, value)).resolve()
        if not actual.is_relative_to(Path('/runtime')):
            _fail('DOCLING_CACHE_LOCATION_INVALID', 'Docling缓存与临时目录须位于/runtime。', [{'variable': name}])
        actual.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(actual)
    # Models are provisioned separately and never fetched while converting user input.
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    model_path = Path(os.environ.get('YOLOONGPPT_DOCLING_MODELS', '/runtime/cache/docling/models')).resolve()
    if not model_path.is_relative_to(Path('/runtime')):
        _fail('DOCLING_MODEL_LOCATION_INVALID', 'Docling模型须位于/runtime。')
    return model_path


def _converter(kind):
    model_path = _runtime()
    try:
        actual = importlib.metadata.version('docling')
    except importlib.metadata.PackageNotFoundError:
        _fail('DOCLING_UNAVAILABLE', '运行镜像缺少固定Docling依赖。')
    if actual != DOCLING_VERSION:
        _fail('DOCLING_VERSION_MISMATCH', 'Docling运行版本与固定适配版本不同。',
              [{'expected': DOCLING_VERSION, 'actual': actual}])
    key = (kind, str(model_path))
    if key in _CONVERTERS:
        return _CONVERTERS[key]
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
        from docling.datamodel.backend_options import HTMLBackendOptions, MsWordBackendOptions
        from docling.document_converter import (DocumentConverter, PdfFormatOption, ImageFormatOption,
                                                WordFormatOption, HTMLFormatOption, ExcelFormatOption)
        fmt = {'docx': InputFormat.DOCX, 'pdf': InputFormat.PDF, 'image': InputFormat.IMAGE,
               'xlsx': InputFormat.XLSX, 'html': InputFormat.HTML}[kind]
        if kind in {'pdf', 'image'}:
            if not model_path.is_dir():
                _fail('DOCLING_MODELS_MISSING', '本地Docling布局、表格及OCR模型尚未配置，未联网或回退。')
            options = PdfPipelineOptions(artifacts_path=model_path, enable_remote_services=False,
                                         allow_external_plugins=False, do_ocr=True, do_table_structure=True,
                                         generate_parsed_pages=True, generate_picture_images=True,
                                         document_timeout=600.0,
                                         ocr_options=RapidOcrOptions(backend='onnxruntime', lang=['ch'], text_score=0.0))
            option = (PdfFormatOption if kind == 'pdf' else ImageFormatOption)(pipeline_options=options)
        elif kind == 'docx':
            option = WordFormatOption(backend_options=MsWordBackendOptions(
                enable_remote_fetch=False, enable_local_fetch=False))
        elif kind == 'html':
            option = HTMLFormatOption(backend_options=HTMLBackendOptions(
                fetch_images=False, render_page=False, enable_remote_fetch=False, enable_local_fetch=False))
        else:
            option = ExcelFormatOption()
        converter = DocumentConverter(allowed_formats=[fmt], format_options={fmt: option})
        _CONVERTERS[key] = converter
        return converter
    except TaskError:
        raise
    except (ImportError, ValueError, TypeError) as exc:
        _fail('DOCLING_CONFIGURATION_INVALID', 'Docling固定API或本地运行配置不可用。',
              [{'exception_type': type(exc).__name__}])


def _json(value):
    if hasattr(value, 'model_dump'):
        value = value.model_dump(mode='json')
    if isinstance(value, float) and not math.isfinite(value):
        # Docling uses NaN for an unavailable aggregate score. JSON null preserves
        # that absence; it is never replaced with a fabricated zero/confidence.
        return None
    if isinstance(value, dict):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(item) for item in value]
    return value


def _anchor(source_id, asset_id, ref, loc, partial=False):
    return {'source_id': source_id, 'asset_id': asset_id, 'native_locator': 'docling:' + ref,
            'locator': loc, 'locator_status': 'partial' if partial else 'located',
            'reason': {'code': 'native_locator_not_normalized',
                       'summary': 'Docling结构引用已保存；该格式无已测量物理页/原生坐标。'} if partial else None}


def _segment(text, source_id, asset_id, ref, loc, data, partial=False):
    return {'raw_text': text, 'anchor': _anchor(source_id, asset_id, ref, loc, partial), 'data': data,
            'metadata': {'semantic_claim_status': 'not_inferred',
                         'confidence_note': '结构、布局与OCR置信度不证明来源事实真实性。',
                         'source_context': {'parser': 'Docling', 'self_ref': ref,
                                            'provenance': data.get('prov', []),
                                            'label': data.get('label'), 'candidate_status': 'not_semantic_truth'}}}


def _node_locator(ref):
    return {'kind': 'structured_node', 'format': 'json', 'node_id': ref, 'document_path': ref,
            'line': None, 'column': None, 'end_line': None, 'end_column': None, 'byte_offset': None}


def _page_locator(page, index, label, row=None, cell=None):
    return {'kind': 'pdf_element', 'page_index': page - 1, 'page_number': page,
            'element_index': index, 'object_kind': label, 'row_index': row, 'cell_index': cell}


def _ocr_pages(result):
    pages = []
    for page in result.pages:
        cells = []
        native_count = 0
        for cell in page.cells:
            data = _json(cell)
            if not data.get('from_ocr'):
                native_count += 1
                continue
            confidence = cell.confidence
            if not isinstance(confidence, (float, int)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                _fail('OCR_CONFIDENCE_UNAVAILABLE', '实际OCR文本缺少有效引擎置信度，拒绝伪造或继续无置信度结果。',
                      [{'page_number': page.page_no}])
            cells.append(data)
            data['confidence'] = float(confidence)
            if page.size is None:
                _fail('OCR_GEOMETRY_UNAVAILABLE', 'OCR页面缺少真实尺寸。')
            bbox = cell.rect.to_top_left_origin(page.size.height).to_bounding_box()
            data['bbox_top_left'] = {'x_min': bbox.l, 'y_min': bbox.t, 'x_max': bbox.r, 'y_max': bbox.b}
            if any(not math.isfinite(v) or v < 0 for v in data['bbox_top_left'].values()):
                _fail('OCR_COORDINATE_INVALID', 'OCR返回无效坐标，未伪造或裁剪。')
        pages.append({'page_number': page.page_no, 'size': _json(page.size), 'ocr_cells': cells,
                      'native_text_cell_count': native_count,
                      'ocr_status': 'executed' if cells else 'no_ocr_text_returned',
                      'confidence_source': 'Docling RapidOCR TextCell.confidence' if cells else None,
                      'parsed_page': _json(page.parsed_page) if page.parsed_page is not None else None})
    return pages


def _ocr_processor():
    """Read the pinned upstream registry and files; conversion performs no fetch."""
    from docling.models.stages.ocr.rapid_ocr_model import (
        RapidOcrModel, _resolve_rapidocr, _backend_to_engine_type, _rapidocr_artifacts)
    spec = _resolve_rapidocr('ch', 'onnxruntime')
    artifacts = _rapidocr_artifacts(_runtime() / RapidOcrModel._model_repo_folder,
                                   _backend_to_engine_type('onnxruntime'), spec.ppocr_version,
                                   spec.rapidocr_code, model_size='small')
    files = []
    for task, artifact in artifacts.items():
        for path, url in artifact.files.items():
            if not path.is_file():
                _fail('DOCLING_MODELS_MISSING', '已执行OCR的实际模型文件缺失。')
            files.append({'task': task, 'filename': path.name, 'source_url': url,
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    known = bool(files) and all('/RapidAI/RapidOCR/resolve/v3.10.0/' in f['source_url'] for f in files)
    # This versioned weight repository's own model card explicitly grants Apache 2.0.
    # Code license alone is not used to infer the license of another model revision.
    return {'status': 'observed', 'execution_status': 'executed', 'engine_name': 'RapidOCR/onnxruntime',
            'engine_version': importlib.metadata.version('rapidocr'),
            'model_name': ','.join(f['filename'] for f in files),
            'license_status': 'known' if known else 'unknown',
            'license_identifiers': ['Apache-2.0'] if known else [],
            'license_reason': None if known else '模型注册表来源版本与已核对v3.10.0模型许可不同。',
            'reason': None}, {'files': files,
                              'license_source': 'https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/README.md',
                              'license_scope': 'versioned model repository; independently checked from OCR code package'}


def _ocr_contract(raw, pages, asset_id):
    """Map actual PDF crop dimensions/rotation and OCR scores to the original schema."""
    if asset_id is None:
        _fail('OCR_SOURCE_ASSET_REQUIRED', '扫描PDF OCR须绑定原始资产ID，不能创建虚假身份。')
    import pypdfium2
    processor, identity = _ocr_processor()
    out = []; errors = []
    with pypdfium2.PdfDocument(raw) as pdf:
        if len(pdf) != len(pages):
            _fail('OCR_PAGE_COUNT_MISMATCH', 'OCR页集合与原PDF真实页数不同。')
        for page in pages:
            number = page['page_number']
            physical=pdf[number - 1]
            try:
                width, height = physical.get_size(); rotation = physical.get_rotation()
                crop_box = physical.get_cropbox()
            finally:
                physical.close()
            size = page['size']
            if (not size or rotation not in {0, 90, 180, 270}
                    or not math.isclose(width, size['width'], abs_tol=0.01)
                    or not math.isclose(height, size['height'], abs_tol=0.01)):
                _fail('OCR_COORDINATE_FRAME_MISMATCH', 'Docling页尺寸与原PDF旋转crop frame不一致，未猜测或重标坐标。',
                      [{'page_number': number, 'docling_size': size, 'pdf_size': [width, height], 'rotation': rotation}])
            cells = page['ocr_cells']; native = page['native_text_cell_count']
            status = 'partial' if cells and native else 'absent' if not native else 'present'
            blocks = []
            for index, cell in enumerate(cells):
                bbox = cell['bbox_top_left']
                if any(not math.isfinite(v) or v < 0 for v in bbox.values()):
                    _fail('OCR_COORDINATE_INVALID', 'OCR坐标无法符合原PDF契约；未裁剪坐标。')
                blocks.append({'block_index': index, 'text': cell['text'],
                               'confidence': {'status': 'measured', 'score': cell['confidence'],
                                              'scale': 'zero_to_one', 'assessment': 'not_assessed',
                                              'assessment_basis': '原始引擎分数；未冒作事实真值或产品低置信阈值。'},
                               'bbox': bbox,
                               'source_anchor': {'source_ref': 'pdf_asset', 'page_index': number - 1,
                                                 'page_number': number, 'element_index': index,
                                                 'object_kind': 'text', 'row_index': None, 'cell_index': None}})
            if not native and not cells:
                errors.append({'error_id': 'ERR-006', 'reason_code': 'PARSE_PARTIAL',
                               'message': f'第{number}页无原生文本且OCR未返回可识别文本，页面仍完整保留。',
                               'source_anchor': None})
            out.append({'page_index': number - 1, 'page_number': number,
                        'coordinate_frame': {'units': 'pt_1_over_72_inch', 'origin': 'top_left',
                                             'page_box': 'rotated_crop_box', 'rotation_degrees': rotation,
                                             'width': width, 'height': height},
                        'text_layer_status': status,
                        'route': 'native_text' if status == 'present' else 'ocr_visual',
                        'ocr_status': 'not_required' if status == 'present' else 'completed' if cells else 'partial',
                        'visual_status': 'completed' if cells else 'not_required', 'text_blocks': blocks})
            identity.setdefault('pdf_geometry', []).append({'page_number': number, 'crop_box': crop_box,
                                                            'rotation_degrees': rotation,
                                                            'size_comparison_tolerance_points': 0.01})
    return {'record_type': 'ocr_parse_result', 'source_asset_id': asset_id, 'raw_asset_refs': [asset_id],
            'processor': processor, 'status': 'partial' if errors else 'parsed',
            'evidence': {'model_type': 'OcrEvidence', 'source_asset_id': asset_id, 'pages': out}, 'errors': errors}, identity


def _docling_segments(document, kind, source_id, asset_id):
    segments = []
    items = document.get('texts', []) + document.get('tables', []) + document.get('pictures', [])
    # Docling refs and child lists preserve reading order; arrays are not flattened into prose.
    for index, item in enumerate(items):
        ref = item.get('self_ref')
        if not isinstance(ref, str):
            _fail('DOCLING_STRUCTURE_INVALID', 'Docling元素缺少稳定self_ref。')
        label = item.get('label', 'text')
        object_kind = 'table' if label == 'table' else 'image' if label == 'picture' else 'text'
        provs = item.get('prov', [])
        if kind == 'pdf' and not provs:
            _fail('DOCLING_PAGE_ANCHOR_MISSING', 'PDF元素缺少真实页码/来源定位。', [{'self_ref': ref}])
        if kind == 'pdf' and object_kind == 'table' and len({p.get('page_no') for p in provs}) > 1:
            _fail('DOCLING_TABLE_PAGE_AMBIGUOUS', '跨页表格单元格缺少独立页码，不能把全部单元格重复归属各页。',
                  [{'self_ref': ref, 'provenance': provs}])
        locations = provs if provs else [None]
        for prov in locations:
            if kind == 'pdf':
                page = prov.get('page_no')
                if not isinstance(page, int) or page < 1:
                    _fail('DOCLING_PAGE_ANCHOR_INVALID', 'Docling页码不合法。')
                loc = _page_locator(page, index, object_kind); partial = False
            elif kind == 'image':
                loc = {'kind': 'image_region', 'element_id': ref, 'bbox': None}; partial = True
            else:
                loc = _node_locator(ref); partial = True
            data = dict(item)
            data.update({'kind': object_kind, 'docling_label': label, 'selected_provenance': prov,
                         'candidate_status': 'not_semantic_truth'})
            if object_kind == 'table':
                # Table cells, including spans/headers/bboxes, stay individual evidence units.
                cells = item.get('data', {}).get('table_cells', [])
                if not cells:
                    segments.append(_segment('', source_id, asset_id, ref, loc, data, partial))
                for ci, cell in enumerate(cells):
                    cell_ref = ref + '/data/table_cells/' + str(ci)
                    cell_loc = dict(loc)
                    if kind == 'pdf':
                        cell_loc.update(object_kind='table_cell', row_index=cell.get('start_row_offset_idx'), cell_index=ci)
                    elif kind not in {'image'}:
                        cell_loc = _node_locator(cell_ref)
                    cell_data = {'kind': 'table_cell', 'label': label, 'table_ref': ref,
                                 'prov': provs, 'selected_provenance': prov, 'cell': cell,
                                 'num_rows': item.get('data', {}).get('num_rows'),
                                 'num_cols': item.get('data', {}).get('num_cols')}
                    seg = _segment(cell.get('text', ''), source_id, asset_id,
                                   cell_ref, cell_loc, cell_data, partial)
                    seg['metadata']['source_context']['table_structure_candidate'] = {
                        'table_ref': ref, 'cell_ref': cell_ref,
                        'row_start': cell.get('start_row_offset_idx'), 'row_end': cell.get('end_row_offset_idx'),
                        'column_start': cell.get('start_col_offset_idx'), 'column_end': cell.get('end_col_offset_idx'),
                        'headers': [{'self_ref': ref + '/data/table_cells/' + str(hi), 'text': header.get('text', ''),
                                     'row_start': header.get('start_row_offset_idx'),
                                     'column_start': header.get('start_col_offset_idx'),
                                     'column_header': header.get('column_header'), 'row_header': header.get('row_header')}
                                    for hi, header in enumerate(cells) if header.get('column_header') or header.get('row_header')],
                        'candidate_status': 'layout_not_semantic_relationship'}
                    segments.append(seg)
            else:
                text = item.get('orig', item.get('text', ''))
                if not isinstance(text, str):
                    _fail('DOCLING_TEXT_INVALID', 'Docling文本字段不是字符串。')
                if len(provs) > 1 and text:
                    span = prov.get('charspan')
                    if (not isinstance(span, (list, tuple)) or len(span) != 2
                            or any(not isinstance(i, int) for i in span)
                            or not 0 <= span[0] <= span[1] <= len(text)):
                        _fail('DOCLING_TEXT_PAGE_AMBIGUOUS', '跨页文本缺少有效原字符范围，不能猜测页归属。')
                    text = text[span[0]:span[1]]
                segments.append(_segment(text, source_id, asset_id, ref, loc, data, partial))
    return segments


def _native_supplement(kind, raw, source_id, asset_id, docling_json):
    from .input_formats import parse_docx, parse_xlsx
    if kind == 'docx':
        from .docx_evidence import enhance_docx
        native, segments, warnings = parse_docx(raw, source_id, asset_id)
        native, segments, extra = enhance_docx(raw, native, segments)
    else:
        from .xlsx_evidence import enhance_xlsx
        native, segments, warnings = parse_xlsx(raw, source_id, asset_id)
        native, segments, extra = enhance_xlsx(native, segments)
        warnings = [w for w in warnings if w['code'] != 'XLSX_DISPLAY_FORMAT_NOT_RENDERED']
        import copy
        for cell in list(segments):
            formula=cell.get('data',{}).get('formula')
            if not formula:continue
            anchor=copy.deepcopy(cell['anchor']);anchor['native_locator']+='/formula'
            segments.append({'raw_text':formula,'anchor':anchor,
                'data':{'field_kind':'formula','formula':formula,'cache_status':cell['data'].get('cached_value_status')},
                'metadata':{'semantic_claim_status':'not_inferred','source_context':{
                    'source_kind':'xlsx','source_field':'formula','original_cell_locator':cell['anchor']['native_locator'],
                    'policy':'Exact stored OOXML formula; not re-executed, not a new business quantity or proof of cache freshness.'}}})
    if kind=='docx':
        # Word bibliography values are real source bytes in custom XML, even
        # when the visible citation is abbreviated. Expose literal evidence;
        # keep their identity separate from paragraph/page locators.
        bibliography={}
        for segment in list(segments):
            for citation in segment.get('data',{}).get('citation_fields',[]):
                for binding in citation.get('bibliography_sources',[]):
                    source=binding.get('source') if binding.get('status')=='resolved' else None
                    if not source:continue
                    for index,field in enumerate(source.get('fields',[])):
                        if not field.get('text'):continue
                        key=(source['part'],source['tag'],index)
                        bibliography[key]=(source,field)
        for (part,tag,index),(source,field) in bibliography.items():
            ref=part+'#bibliography='+json.dumps(tag,ensure_ascii=False)+'/field='+str(index)
            loc=_node_locator(ref);loc['format']='xml'
            segment=_segment(field['text'],source_id,asset_id,ref,loc,
                {'source_part':part,'bibliography_tag':tag,'field_index':index,'field_name':field['name'],'field_text':field['text']})
            segment['metadata']['source_context'].update(source_kind='docx',source_field='bibliography',
                field_name=field['name'],bibliography_tag=tag,source_part=part,
                binding_policy='literal custom XML field; not inferred visible paragraph or fact truth')
            segments.append(segment)
    refs = {}
    for item in docling_json.get('texts', []):
        refs.setdefault(item.get('orig', item.get('text', '')), []).append(
            {'self_ref': item['self_ref'], 'label': item.get('label'), 'heading_level': item.get('level'),
             'provenance': item.get('prov', [])})
    for table in docling_json.get('tables', []):
        for index, cell in enumerate(table.get('data', {}).get('table_cells', [])):
            refs.setdefault(cell.get('text', ''), []).append(
                {'self_ref': table['self_ref'] + '/data/table_cells/' + str(index), 'label': 'table_cell',
                 'table_ref': table['self_ref'], 'row_start': cell.get('start_row_offset_idx'),
                 'row_end': cell.get('end_row_offset_idx'), 'column_start': cell.get('start_col_offset_idx'),
                 'column_end': cell.get('end_col_offset_idx'), 'column_header': cell.get('column_header'),
                 'row_header': cell.get('row_header'), 'provenance': table.get('prov', [])})
    for seg in segments:
        context = seg['metadata'].setdefault('source_context', {})
        matches = refs.get(seg['raw_text'], [])
        context['docling'] = {'matching_literal_refs': [item['self_ref'] for item in matches],
                             'literal_matches': matches,
                             'matching_policy': 'exact_literal_only_no_location_guess',
                             'structure_ref': 'document.docling', 'native_fields_preserved': True,
                             'candidate_status': 'not_semantic_truth'}
    return native, segments, warnings + extra


def parse_docling(kind, raw, *, source_id, asset_id=None, locator=None):
    """Convert bytes locally; return the existing input-format-result contract.

    Non-success (including timed-out partial conversion) is a structured failure.
    OOXML native fields supplement successful conversion; they are never a failure
    fallback. Original byte hash remains the identity of both evidence layers.
    """
    kind = kind.lower()
    if kind not in SUPPORTED:
        _fail('DOCLING_FORMAT_UNSUPPORTED', '该格式不在Docling融合路由中。', [{'format': kind}])
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_RAW:
        _fail('INPUT_SIZE_LIMIT', '输入须非空字节且不超过64MiB。')
    # Reuse bounded archive validation before invoking third-party package readers.
    if kind in {'docx', 'xlsx'}:
        from .input_formats import package, xml
        with package(raw, 'word/document.xml' if kind == 'docx' else 'xl/workbook.xml') as archive:
            for part in archive.namelist():
                if part.endswith(('.xml', '.rels')):
                    xml(archive.read(part))
    if kind == 'pdf' and not raw.startswith(b'%PDF-'):
        _fail('INPUT_FORMAT_DISGUISED', '声明PDF的输入缺少PDF标识。')
    image_info = None
    if kind == 'image':
        from .assets import inspect_image
        image_info = inspect_image(raw, locator)
    source_hash = hashlib.sha256(raw).hexdigest()
    warnings = []
    with _LOCK:
        converter = _converter(kind)
        try:
            from docling.datamodel.base_models import DocumentStream
            extension = 'png' if kind == 'image' else kind
            stream = DocumentStream(name='source.' + extension, stream=io.BytesIO(raw))
            result = converter.convert(stream, raises_on_error=False,
                                       max_num_pages=MAX_PAGES, max_file_size=MAX_RAW)
            status = getattr(result.status, 'value', str(result.status))
            if status != 'success':
                _fail('DOCLING_CONVERSION_FAILED', 'Docling未完整成功转换；未采用部分结果或回退解析器。',
                      [{'status': status, 'errors': [_json(error) for error in result.errors]}])
            converted = _json(result.document.export_to_dict())
            pages = _ocr_pages(result)
            conversion_errors = [_json(error) for error in result.errors]
            if image_info is not None and image_info['frame_count'] != len(pages):
                _fail('IMAGE_FRAME_COVERAGE_INCOMPLETE', 'Docling未完整覆盖原图片所有帧；未静默只取首帧。',
                      [{'source_frames': image_info['frame_count'], 'parsed_pages': len(pages)}])
        except TaskError:
            raise
        except Exception as exc:
            _fail('DOCLING_CONVERSION_FAILED', 'Docling本地转换失败；未联网或回退其他解析器。',
                  [{'exception_type': type(exc).__name__}])
    if kind in {'docx', 'xlsx'}:
        native, segments, warnings = _native_supplement(kind, raw, source_id, asset_id, converted)
        document = native
    else:
        document = {'format': kind}
        segments = _docling_segments(converted, kind, source_id, asset_id)
        if image_info is not None:
            document['image_source'] = image_info
            warnings.extend(image_info['issues'])
    document.update(docling=converted, docling_pages=pages,
                    docling_conversion={'version': DOCLING_VERSION, 'status': status,
                                        'local_only': True, 'source_sha256': source_hash,
                                        'remote_resource_fetch': False,
                                        'errors': conversion_errors,
                                        'unavailable_score_serialization': 'Docling NaN aggregate scores are JSON null; no inferred confidence.',
                                        'confidence': _json(result.confidence)})
    for error in conversion_errors:
        warnings.append({'code': 'DOCLING_CONVERSION_WARNING',
                         'message': 'Docling成功状态附带组件问题，原问题完整保留。', 'error': error})
    if kind == 'html':
        warnings.append({'code': 'HTML_EXTERNAL_RESOURCES_NOT_FETCHED',
                         'message': 'HTML结构已解析；外部及本地图片引用未加载，未执行网页脚本。'})
    if kind == 'docx':
        warnings.append({'code': 'DOCLING_DOCX_PHYSICAL_PAGES_NOT_MEASURED',
                         'message': 'Docling提取DOCX结构；Word实际分页沿用原生pending标记，不以结构序号猜页码。'})
    ocr_cells = sum(len(page['ocr_cells']) for page in pages)
    if kind == 'pdf' and ocr_cells:
        ocr_result, model_identity = _ocr_contract(raw, pages, asset_id)
        from .schemas import SchemaRegistry
        SchemaRegistry().validate('ocr-evidence.schema.json', ocr_result)
        document['ocr_evidence'] = ocr_result
        document['ocr_model_identity'] = model_identity
        if ocr_result['processor']['license_status'] != 'known':
            warnings.append({'code': 'OCR_MODEL_LICENSE_UNKNOWN', 'message': '实际OCR模型许可尚未核对，不能冒作许可验收通过。'})
        for error in ocr_result['errors']:
            warnings.append({'code': error['reason_code'], 'message': error['message'], 'error': error})
    if image_info is not None:
        image_info['ocr_status'] = 'executed' if ocr_cells else 'no_text_returned'
        image_info['ocr_evidence_ref'] = 'document.docling_pages'
        image_info['issues'] = [w for w in image_info['issues'] if w['code'] != 'IMAGE_OCR_NOT_EXECUTED']
        warnings = [w for w in warnings if w['code'] != 'IMAGE_OCR_NOT_EXECUTED']
    if kind in {'pdf', 'image'}:
        for seg in segments:
            provenance = seg['data'].get('selected_provenance') or {}
            page_number = seg['anchor']['locator'].get('page_number', provenance.get('page_no'))
            page_ocr = next((p['ocr_cells'] for p in pages if p['page_number'] == page_number), [])
            seg['metadata']['source_context']['ocr_page_evidence'] = {
                'page_number': page_number, 'document_ref': 'document.docling_pages',
                'page_has_ocr': bool(page_ocr), 'review_required': bool(page_ocr),
                'literal_matching_cells': [{'text': c['text'], 'confidence': c['confidence'],
                                            'rect': c.get('rect'), 'from_ocr': True}
                                           for c in page_ocr if c['text'] == seg['raw_text']],
                'confidence_policy': 'individual_engine_scores_only_no_fabricated_item_confidence'}
    if ocr_cells:
        warnings.append({'code': 'OCR_TEXT_REQUIRES_FACT_REVIEW',
                         'message': 'OCR真实文本、页码、坐标及引擎置信度已保存；识别结果仍须事实复核。',
                         'ocr_cell_count': ocr_cells})
    if not segments:
        _fail('INPUT_NO_PARSED_EVIDENCE', 'Docling未返回可定位结构，不把无证据文件当作成功来源。')
    for segment in segments:
        segment['metadata'].setdefault('source_context',{})['source_kind']=kind
    if len(segments) > MAX_SEGMENTS:
        _fail('INPUT_STRUCTURE_LIMIT', '结构元素超过限制；未裁剪来源内容。')
    version_files = ['docling_adapter.py', 'input_formats.py']
    version_files += {'docx': ['docx_evidence.py'], 'xlsx': ['xlsx_evidence.py'], 'image': ['assets.py']}.get(kind, [])
    version_hash = hashlib.sha256(b''.join(_VERSION_SOURCES[name] for name in version_files)).hexdigest()
    return {'status': 'partial' if warnings else 'parsed', 'document': document, 'segments': segments,
            'warnings': warnings, 'parser_version': 'docling-' + DOCLING_VERSION + ':' + version_hash + ':kind:' + kind,
            'source_sha256': source_hash,
            'boundary': 'Original bytes are the immutable snapshot; Docling/native structure and OCR confidence are not semantic truth or system acceptance.'}
