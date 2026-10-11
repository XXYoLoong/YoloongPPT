"""SYS-003 / IN-001/002: text inputs, preserved structure and immutable evidence."""
import hashlib
from collections import defaultdict
from importlib.metadata import version
from pathlib import Path

from .errors import TaskError
from .markdown import MarkdownParser, parse_plain_text
from .schemas import ROOT
from .tasks import validate_task

PARSER_VERSION = ('text-1:' + hashlib.sha256((Path(__file__).read_bytes()+Path(__file__).with_name('markdown.py').read_bytes())).hexdigest()
                  + ':markdown-it-py-' + version('markdown-it-py') + ':mdit-py-plugins-' + version('mdit-py-plugins'))
MAX_SOURCE_BYTES = 16 * 1024 * 1024


def input_bytes(source):
    binary = {'docx': {'.docx'}, 'xlsx': {'.xlsx'}, 'csv':{'.csv'}, 'json':{'.json'}, 'xml':{'.xml'},
              'pptx': {'.pptx'}, 'potx':{'.potx'}, 'pdf': {'.pdf'},
              'image': {'.png','.jpg','.jpeg','.webp','.gif','.bmp','.tif','.tiff'}}
    if source['kind'] not in {'prompt', 'text', 'markdown', *binary}:
        raise TaskError('INPUT_UNSUPPORTED', '该输入格式尚未接入，未静默跳过。',
                        'SourceLoader', ['SYS-003', 'IN-015'], [{'source_id': source['source_id'], 'supported_formats': ['prompt', 'text', 'markdown', *binary]}])
    if 'content' in source and 'locator' in source:
        raise TaskError('SOURCE_LOCATION_AMBIGUOUS', '来源同时提供content和locator，须明确实际输入。', 'SourceLoader', ['SYS-003'])
    if 'locator' in source:
        path = Path(source['locator'])
        path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
        if any(p in {'secrets','.git','.ssh','.env'} for p in path.parts) or (not path.is_relative_to(ROOT) and not path.is_relative_to(Path('/runtime'))):
            raise TaskError('SOURCE_PATH_OUTSIDE_ROOT', '输入路径超出工作区和运行产物目录。', 'SourceLoader', ['SYS-003'])
        if path.suffix.lower() not in binary.get(source['kind'], {'.md', '.markdown', '.txt'}):
            raise TaskError('INPUT_UNSUPPORTED', '该文件扩展名未支持，禁止改作纯文本读取。', 'SourceLoader', ['SYS-003', 'IN-015'])
        try:
            with path.open('rb') as file:
                raw = file.read(MAX_SOURCE_BYTES + 1)
        except OSError:
            raise TaskError('INPUT_NOT_FOUND', '输入文件不存在或不可读取。', 'SourceLoader', ['SYS-003', 'IN-015'], [{'source_id': source['source_id']}]) from None
        locator = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    else:
        if source['kind'] in binary:
            raise TaskError('INPUT_BINARY_LOCATION_REQUIRED', '二进制来源需文件locator，禁止把字符串或base64当作文件。', 'SourceLoader', ['SYS-003','IN-015'])
        content = source.get('content')
        if not isinstance(content, str):
            raise TaskError('INPUT_TEXT_INVALID', '文本来源content必须为字符串；不隐式转换。', 'SourceLoader', ['SYS-003', 'IN-001', 'IN-002'])
        raw = content.encode('utf-8'); locator = None
    if len(raw) > MAX_SOURCE_BYTES:
        raise TaskError('INPUT_SIZE_LIMIT', '文本来源超过16MiB限制，未截断或继续解析。', 'SourceLoader', ['SYS-003', 'IN-015'])
    if source['kind'] in binary:
        return raw, None, locator
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise TaskError('INPUT_ENCODING_UNSUPPORTED', '当前文本输入需UTF-8；未自动替换字符或猜测编码。', 'SourceLoader', ['SYS-003', 'IN-002']) from None
    if '\x00' in text:
        raise TaskError('INPUT_FORMAT_DISGUISED', '文本包含NUL字符，可能是二进制或格式伪装。', 'SourceLoader', ['SYS-003', 'IN-015'])
    if not text.strip():
        raise TaskError('INPUT_EMPTY', '来源为空或只有空白；没有可解析内容。', 'SourceLoader', ['SYS-003', 'IN-001', 'IN-002'])
    return raw, text, locator


def source_anchor(source_id, asset_id, index, begin, end):
    return {'source_id': source_id, 'asset_id': asset_id, 'native_locator': f'chars:{begin}:{end}',
            'locator': {'kind': 'text_span', 'segment_index': index, 'start_char': begin, 'end_char': end, 'offset_unit': 'unicode_code_points'},
            'locator_status': 'located', 'reason': None}


def inspect_sources(task, schemas, store, trace):
    checked = validate_task(task, schemas, trace)
    if not task['sources']:
        raise TaskError('INPUT_NOT_FOUND', '没有可加载的来源。', 'SourceLoader', ['SYS-003'])
    snapshots = []; items = []; records = []; documents = []
    for order, source in enumerate(task['sources']):
        raw, text, locator = input_bytes(source)
        digest = hashlib.sha256(raw).hexdigest(); id = source['source_id']
        asset = store.asset_id(id, digest, locator is not None)
        snapshots.append({'source_id': id, 'source_hash': digest, 'asset_id': asset, 'bytes': raw})
        if text is None:
            from .input_formats import parse_input
            parsed = parse_input(source['kind'], raw, source_id=id, asset_id=asset, locator=locator)
            schemas.validate('input-format-result.schema.json',parsed)
            document = parsed['document']
            note = 'Native format structure retained; warnings and unsupported semantics are explicit.'
            documents.append({'source_id': id, 'document': document, 'parse_note': note,
                              'warnings': parsed['warnings']})
            for n, segment in enumerate(parsed['segments']):
                schemas.validate('source-anchor.schema.json', segment['anchor'])
                records.append({'source_id':id,'source_hash':digest,'parser_version':parsed['parser_version'],
                                'segment_index':n,'anchor':segment['anchor'],'raw_text':segment['raw_text'],
                                'content':segment['raw_text'],'confidence':None,'data':segment['data'],
                                'metadata':segment['metadata'],'asset_ref':asset,'raw_asset_refs':[asset] if asset else [],'parse_note':note})
            items.append({'source_id':id,'input_order':order,'kind':'file','locator':locator,'raw_text':None,
                          'locator_redaction':'not_required','display_name':None,'raw_asset_refs':[asset] if asset else [],
                          'content_sha256':digest,'priority_rank':None,'claims':[]})
            continue
        if source['kind'] in {'markdown', 'text'}:
            document = MarkdownParser(text).parse() if source['kind'] == 'markdown' else parse_plain_text(text)
            if asset:
                document['raw_asset_refs'] = [asset]
                document['source'] = document['document']['source'] = {'kind': 'asset', 'asset_id': asset}
            schemas.validate('text-document.schema.json', document)
            segments = [(b['source_location']['start_offset'], b['source_location']['end_offset']) for b in document['document']['blocks']]
            note = ('Markdown blocks retain raw Unicode ranges; inline locations are containing-block ranges, not exact lexical spans.'
                    if source['kind'] == 'markdown' else 'Plain text paragraphs preserve original Unicode; Markdown syntax is not interpreted.')
        else:
            loc = {'source_ref': 'raw_text', 'start_offset': 0, 'end_offset': len(text), 'offset_unit': 'unicode_code_point'}
            document = {'raw_text': text, 'raw_asset_refs': [asset] if asset else [], 'status': 'parsed',
                        'normalized_instruction': {'topic': None, 'requirements': [], 'modification_instructions': [],
                                                   'context': [{'text': text, 'source_locations': [loc]}] if text else []}, 'errors': []}
            schemas.validate('prompt-input.schema.json', document)
            segments = [(0, len(text))]
            note = 'Raw prompt/text kept as context; topic, requirements and modification intent are not inferred here.'
        if not segments:segments = [(0, len(text))]
        documents.append({'source_id': id, 'document': document, 'parse_note': note})
        for n, (begin, end) in enumerate(segments):
            anchor = source_anchor(id, asset, n, begin, end)
            schemas.validate('source-anchor.schema.json', anchor)
            records.append({'source_id': id, 'source_hash': digest, 'parser_version': PARSER_VERSION+':kind:'+source['kind'],
                            'segment_index': n, 'anchor': anchor, 'raw_text': text[begin:end],
                            'content': text[begin:end], 'confidence': None,
                            'data': document['document']['blocks'][n] if 'document' in document and document['document']['blocks'] else document.get('normalized_instruction'),
                            'metadata': {'source_kind': source['kind'], 'semantic_claim_status': 'not_inferred', 'confidence_note': '来源真实性/语义置信度未评估，不由哈希验证推定。'},
                            'asset_ref': asset,
                            'raw_asset_refs': [asset] if asset else [], 'parse_note': note})
        items.append({'source_id': id, 'input_order': order, 'kind': 'file' if locator else 'text',
                      'locator': locator, 'raw_text': None if locator else text, 'locator_redaction': 'not_required',
                      'display_name': None, 'raw_asset_refs': [asset] if asset else [], 'content_sha256': digest,
                      'priority_rank': None, 'claims': []})
    groups = defaultdict(list)
    for item in items:groups[item['content_sha256']].append(item['source_id'])
    duplicates = [{'group_id': 'hash-'+digest, 'basis': 'sha256_match', 'status': 'candidate', 'source_ids': ids,
                   'content_sha256': digest, 'canonical_source_id': None} for digest, ids in groups.items() if len(ids)>1]
    bundle = {'record_type': 'source_bundle_result', 'status': 'partial', 'bundle': {
        'model_type': 'SourceBundle', 'sources': items, 'source_priority_policy': {'status': 'unresolved', 'decision_id': 'DEC-004',
        'task_id': 'TASK-DEC-004', 'precedence_source_ids': [], 'unresolved_reason': '来源优先级未由DEC-004选择，所有来源保留。'},
        'dedup_policy': {'mode': 'hash_candidates_only', 'keep_all_sources': True}, 'duplicate_groups': duplicates, 'conflicts': []},
        'coverage': [{'feature': 'source_identity', 'status': 'complete', 'reason': None},
                     {'feature': 'source_anchors', 'status': 'complete', 'reason': None},
                     {'feature': 'priority', 'status': 'partial', 'reason': 'DEC-004尚未执行。'},
                     {'feature': 'conflict_detection', 'status': 'unsupported', 'reason': '没有抽取事实或运行语义冲突检测，不能认定无冲突。'},
                     {'feature': 'deduplication', 'status': 'partial', 'reason': '仅SHA候选，不删除来源。'}], 'errors': []}
    schemas.validate('source-bundle.schema.json', bundle)
    evidence, assets = store.save(snapshots, records)
    for item in items:item['raw_asset_refs'] = [assets[item['source_id']]] if assets[item['source_id']] else []
    for item in documents:
        asset = assets[item['source_id']]
        if asset:
            item['document']['raw_asset_refs'] = [asset]
            if 'document' in item['document']:
                item['document']['source'] = item['document']['document']['source'] = {'kind': 'asset', 'asset_id': asset}
    return {'ok': True, 'trace_id': trace, 'operation': 'inspect_sources', 'task_id': task['task_id'],
            'source_bundle': bundle, 'documents': documents, 'evidence': evidence,
            'trace': checked['trace'] + [{'component': 'SourceLoader', 'requirement_id': 'SYS-003', 'status': 'partial'},
                                       {'component': 'EvidenceStore', 'requirement_id': 'SYS-004', 'status': 'saved'}],
            'boundary': 'Source parsing and evidence only; no fact extraction, model routing, PPTX generation or QA acceptance.'}
