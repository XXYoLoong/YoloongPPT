"""DEC-022..029: executed visual choices with fact and asset provenance.

No visual choice adds facts. Nodes/edges use literal approved evidence; causal
inference and lexical relation guesses are rejected. Native execution, rendered
quality and independent semantic review are separate downstream obligations.
"""
import copy
import math
import re

from .artifacts import entity
from .asset_resolver import inventory_from_task, resolve
from .errors import TaskError, trace_id
from .facts import approved_text
from .template_registry import select as select_template

NODES = tuple(f'DEC-{number:03d}' for number in range(22, 30))
MAPPING = {'P01': 'Visual_Designer/template/Executor', 'P02': 'layout induction/reference selection/actions',
           'P03': 'slide content/layout/template/assets', 'P04': 'PureLayout/assets/PPTAdapter',
           'P05': 'SlidePlanner/template/assets/native writer'}
DIAGRAM_TYPES = ('process', 'timeline', 'tree', 'network', 'matrix', 'funnel', 'swimlane')


def _fail(code, message, ids, details=None):
    raise TaskError(code, message, 'VisualOrchestrator', ids, details or [])


def _trace(node, inputs, output, options, trace):
    candidates = [{'node_id': node, 'candidate_id': entity('candidate'), 'value': value,
                   'score': 1 if selected else 0, 'reasons': [{'reason': reason}],
                   'evidence_refs': inputs.get('evidence_refs', []),
                   'constraints': [{'no_implicit_fact_inference': True, 'no_silent_fallback': True}]} for value, reason, selected in options]
    return {'trace_id': trace, 'node_id': node, 'input': inputs, 'candidates': candidates,
            'selected': [candidate['candidate_id'] for candidate, option in zip(candidates, options) if option[2]],
            'rules': {'source_project_mapping': MAPPING, 'mechanism': 'validated model intent plus actual structured payload/provenance; no semantic confidence guessed',
                      'score_semantics': 'selected policy outcome, not semantic probability',
                      'fallback': 'structured failure; never invent material or downgrade a requested expression'},
            'output': output, 'duration': 0.0, 'error': None}


def _emit(schemas, artifacts, traces, trace):
    if schemas: schemas.validate('visual-trace.schema.json', trace)
    traces.append(trace)
    if artifacts: artifacts.json('decision-' + trace['node_id'] + '.json', trace)


def prepare(task, sources, context, schemas=None, artifacts=None):
    trace = context.get('trace_id') or trace_id()
    template = select_template(task, context, schemas=schemas)
    styles = task.get('style') or {}
    tokens = {'font': styles.get('font', 'Noto Sans CJK SC'),
              'foreground': styles.get('foreground', '192C32'), 'background': styles.get('background', 'F6F4EE'),
              'accent': styles.get('accent', '147C80'), 'shape_language': 'native_editable',
              'image_treatment': 'contain_without_crop', 'decoration_density': 'minimal',
              'provenance': {'font': 'caller override or declared native renderer font',
                             'colors': 'caller override or explicit product default'},
              'template_tokens': template['record']['design_tokens'] if template['record'] else None}
    if tokens['font'] != 'Noto Sans CJK SC' or any(not isinstance(tokens[field], str) or not re.fullmatch(r'[0-9A-Fa-f]{6}', tokens[field]) for field in ('foreground', 'background', 'accent')):
        _fail('VISUAL_STYLE_UNSUPPORTED', '字体/颜色超出当前已验证执行范围，未替换调用者风格。', ['DEC-029', 'AST-016'])
    declarations = inventory_from_task(task, sources)
    policy = task.get('runtime_preferences', {}).get('asset_policy', {})
    assets = resolve({'requests': declarations, 'allow_network': policy.get('allow_network', False),
                      'minimum_pixels': policy.get('minimum_pixels', [1, 1])}, schemas=schemas)
    traces = []
    _emit(schemas, artifacts, traces, _trace('DEC-028', {'template_ref': task.get('template_ref'), 'constraints': context.get('constraints', {}), 'evidence_refs': []},
         {'family': template['family'], 'template_id': template['record']['template_id'] if template['record'] else None,
          'template_status': template['status'], 'fallback': template['fallback']},
         [(candidate, candidate.get('reason', 'native template structural match; capacity remains explicit'), index == next((i for i, entry in enumerate(template['candidates']) if entry.get('eligible')), -1)) for index, candidate in enumerate(template['candidates'])], trace))
    _emit(schemas, artifacts, traces, _trace('DEC-029', {'style': styles, 'template_id': template['record']['template_id'] if template['record'] else None, 'evidence_refs': []},
         tokens, [(tokens, 'explicit caller values/product defaults; template originals retained without assuming font availability', True)], trace))
    packet = {'version': 'visual-1', 'trace_id': trace, 'template_selection': template, 'design_tokens': tokens,
              'asset_declarations': declarations, 'resolved_assets': assets, 'decision_traces': traces,
              'planner_assets': [{'asset_id': item['asset_id'], 'width_px': item['width_px'], 'height_px': item['height_px'],
                                  'source_type': item['source_type'], 'license': item['license'], 'usage_status': item['usage_status'],
                                  'semantic_status': item['semantic_status']} for item in assets['entries']],
              'planner_rules': ['Only listed asset_id is executable; paths are injected by the resolver, never invented by the model.',
                  'image requires explicit role and alt_text; decorative and information roles are distinct.',
                  'diagram labels and edge evidence_quote must be literal approved-source text; no invented causal edges.',
                  'A list can remain cards/text without connecting nodes; visual flow requires explicit relation evidence.',
                  'table/chart data remain unchanged; native chart types bar/column/line only in this execution version.'],
              'system_acceptance': 'not_claimed'}
    if schemas: schemas.validate('visual-packet.schema.json', packet)
    if artifacts:
        artifacts.json('visual-packet.json', packet)
        artifacts.json('resolved-assets.json', assets)
        artifacts.json('template-selection.json', template)
    return packet


def _texts(sources, refs):
    evidence = {item['evidence_id']: item for item in sources.get('evidence', [])}
    if any(reference not in evidence for reference in refs):
        _fail('VISUAL_EVIDENCE_UNKNOWN', '视觉对象引用未知事实证据。', ['DEC-022', 'DEC-027'])
    return {reference: approved_text(sources, evidence[reference]) for reference in refs}


def _diagram(data, sources, slide_refs):
    if data.get('type') not in DIAGRAM_TYPES:
        _fail('DIAGRAM_TYPE_UNSUPPORTED', '关系图类型未登记。', ['DEC-027', 'AST-014'])
    if not 1 <= len(data.get('nodes', [])) <= 12:
        _fail('DIAGRAM_NODE_LIMIT', '关系图需要1–12个真实结构节点；没有截断。', ['DEC-027'])
    nodes = {item['node_id']: item for item in data['nodes']}
    if len(nodes) != len(data['nodes']): _fail('DIAGRAM_NODE_DUPLICATE', '关系图节点ID重复。', ['DEC-027'])
    for node in nodes.values():
        refs = node.get('evidence_refs', [])
        if not refs or set(refs) - set(slide_refs):
            _fail('DIAGRAM_NODE_EVIDENCE_REQUIRED', '节点须引用当前页面已批准的证据。', ['DEC-027', 'CNT-003'])
        if not node.get('label') or not any(node['label'] in text for text in _texts(sources, refs).values()):
            _fail('DIAGRAM_NODE_LABEL_UNGROUNDED', '关系图节点文字不是已批准证据的原文；未把模型语义解释当事实。', ['DEC-027', 'CNT-003'])
    if len(data.get('edges', [])) > 24: _fail('DIAGRAM_EDGE_LIMIT', '关系图边数超出当前容量，未截断。', ['DEC-027'])
    for edge in data.get('edges', []):
        if edge.get('from') not in nodes or edge.get('to') not in nodes or edge['from'] == edge['to']:
            _fail('DIAGRAM_EDGE_INVALID', '关系边端点缺失或自环；需明确结构策略。', ['DEC-027'])
        refs = edge.get('evidence_refs', [])
        quote = edge.get('evidence_quote', '')
        if not refs or set(refs) - set(slide_refs) or not quote or not any(quote in text for text in _texts(sources, refs).values()):
            _fail('DIAGRAM_EDGE_UNGROUNDED', '关系边缺少已批准原文引句。', ['DEC-027', 'CNT-003'])
        first, second = nodes[edge['from']]['label'], nodes[edge['to']]['label']
        if first not in quote or second not in quote:
            _fail('DIAGRAM_EDGE_UNGROUNDED', '关系引句没有同时出现两个节点，不能按词法暗示连边。', ['DEC-027', 'CNT-003'])
        relation = edge.get('relation')
        if relation in {'causal', 'causes', 'causality'}:
            _fail('DIAGRAM_CAUSAL_PROOF_REQUIRED', '当前实现不证明因果关系，不能以因为/导致词语建立已证因果边。', ['DEC-027', 'DEC-005'])
        # The literal arrow is an explicit structural statement, not a guessed
        # relation from words such as "after", "because", "step" or "process".
        start = quote.find(first); finish = quote.find(second, start + len(first))
        between = quote[start + len(first):finish] if finish >= 0 else ''
        if relation in {'sequence', 'temporal', 'process'}:
            if finish < 0 or not any(separator in between for separator in ('→', '->', '⇒', '=>')):
                _fail('DIAGRAM_RELATION_NOT_EXPLICIT', '顺序边需要原文显式箭头与正确方向；普通词法提示不足以证明关系。', ['DEC-027'])
        else:
            _fail('DIAGRAM_RELATION_REVIEW_REQUIRED', '当前执行器只接入原文明示顺序/时间边；层级/网络等关系须补语义及拓扑校验。', ['DEC-027'], [{'relation': relation}])
        if edge.get('label') and edge['label'] not in quote:
            _fail('DIAGRAM_EDGE_LABEL_UNGROUNDED', '边标签不是关系引句原文。', ['DEC-027'])
    if data['type'] in {'process', 'timeline'} and len(nodes) > 1 and not data.get('edges'):
        _fail('DIAGRAM_RELATION_MISSING', '流程/时间线有多个节点却没有已证原文关系边；可显式选文本/卡片，未自动降级。', ['DEC-027'])
    # Reject cyclic flows rather than inventing a temporal ordering.
    adjacency = {key: [] for key in nodes}
    for edge in data.get('edges', []): adjacency[edge['from']].append(edge['to'])
    visiting, seen = set(), set()
    def visit(key):
        if key in visiting: _fail('DIAGRAM_CYCLE_UNSUPPORTED', '流程/时间线出现环；未强行排序。', ['DEC-027'])
        if key in seen: return
        visiting.add(key)
        for following in adjacency[key]: visit(following)
        visiting.remove(key); seen.add(key)
    if data['type'] in {'process', 'timeline', 'tree'}:
        for key in nodes: visit(key)
    return {**copy.deepcopy(data), 'grounding_status': 'literal_nodes_and_explicit_edges_checked_semantic_review_pending',
            'editable_representation': 'native_shapes_and_connectors', 'causal_proof': 'not_claimed'}


def _slide_nodes(slide, packet, sources):
    refs = slide.get('evidence_refs', [])
    _texts(sources, refs)
    kind = slide['kind']
    allowed = ('text', 'table', 'chart', 'image', 'diagram')
    if kind not in allowed: _fail('VISUAL_KIND_UNSUPPORTED', '主视觉表达尚无执行后端；未改成文本掩盖。', ['DEC-022'])
    result = {}
    result['DEC-022'] = {'expression': {'text': 'cards_or_text', 'image': 'text_image', 'diagram': slide.get('diagram', {}).get('type', 'diagram')}.get(kind, kind),
                         'kind': kind, 'reason': slide.get('rationale', 'explicit structured model proposal'), 'evidence_refs': refs,
                         'preserved_content': True}
    image = slide.get('image')
    result['DEC-023'] = {'required': kind == 'image', 'count': 1 if kind == 'image' else 0,
                         'role': image.get('role') if isinstance(image, dict) else None,
                         'information_value': 'caller/model declared; independent semantic review pending' if kind == 'image' else 'not requested',
                         'fallback': 'fail on missing material'}
    selected_assets = []
    model_image = copy.deepcopy(image)
    if kind == 'image':
        if not isinstance(image, dict) or not image.get('asset_id') or image.get('role') not in {'information', 'decoration', 'logo', 'reference'} or not image.get('alt_text'):
            _fail('IMAGE_REQUIREMENT_INVALID', '图片页缺少asset_id、信息/装饰角色或alt_text。', ['DEC-023', 'AST-006'])
        if image.get('fit', 'contain') != 'contain':
            _fail('IMAGE_CROP_POLICY_REQUIRED', '当前默认只完整contain；裁切必须由明确焦点/裁切策略接入。', ['DEC-023', 'AST-007'])
        matches = [item for item in packet['resolved_assets']['entries'] if item['asset_id'] == image['asset_id']]
        if len(matches) != 1: _fail('IMAGE_ASSET_UNKNOWN', '模型选中的图片没有唯一真实已解析资产。', ['DEC-024', 'SYS-009'])
        asset = matches[0]
        image.update(path=asset['path'], width_px=asset['width_px'], height_px=asset['height_px'], sha256=asset['sha256'], source_refs=refs)
        selected_assets.append(asset)
    result['DEC-024'] = {'selected_asset_ids': [item['asset_id'] for item in selected_assets],
                         'model_image_declaration': model_image,
                         'sources': [{'asset_id': item['asset_id'], 'source_type': item['source_type'], 'sha256': item['sha256'], 'license': item['license'], 'usage_status': item['usage_status']} for item in selected_assets],
                         'all_materialized': True, 'unused_assets_retained': True, 'fallback': 'fail on unavailable or unauthorized requested asset'}
    table = slide.get('table')
    if kind == 'table':
        if not isinstance(table, dict) or not table.get('columns') or not table.get('rows'):
            _fail('VISUAL_TABLE_EMPTY', '表格表达没有结构化行列数据。', ['DEC-025'])
        if any(len(row) != len(table['columns']) for row in table['rows']):
            _fail('VISUAL_TABLE_SHAPE', '表格行列数不一致，未补齐或截断。', ['DEC-025'])
    result['DEC-025'] = {'required': kind == 'table', 'rows': len(table['rows']) if kind == 'table' else 0,
                         'columns': len(table['columns']) if kind == 'table' else 0, 'emphasis_fields': [],
                         'pagination': 'one native table; physical capacity gate must pass' if kind == 'table' else 'not applicable to this slide',
                         'data': copy.deepcopy(table) if kind == 'table' else None}
    chart = slide.get('chart')
    if kind == 'chart':
        if not isinstance(chart, dict) or chart.get('type') not in {'bar', 'column', 'line'}:
            _fail('VISUAL_CHART_TYPE_UNSUPPORTED', '当前已接入原生bar/column/line；未将area/pie/scatter偷偷改型。', ['DEC-026'])
        if not chart.get('categories') or not chart.get('series'):
            _fail('VISUAL_CHART_EMPTY', '图表没有真实结构化数据。', ['DEC-026'])
        for series in chart['series']:
            if len(series.get('values', [])) != len(chart['categories']) or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) for value in series['values']):
                _fail('VISUAL_CHART_VALUES_INVALID', '图表维度不匹配或值不是有限实数，未补齐或裁剪。', ['DEC-026'])
    result['DEC-026'] = {'required': kind == 'chart', 'type': chart['type'] if kind == 'chart' else 'none',
                         'analysis_purpose': slide.get('goal'), 'data': copy.deepcopy(chart) if kind == 'chart' else None,
                         'data_semantic_status': 'subsequent evidence/numeric and independent review required', 'image_fallback': 'not_permitted'}
    diagram = None
    if kind == 'diagram':
        if not isinstance(slide.get('diagram'), dict): _fail('DIAGRAM_SPEC_REQUIRED', '关系图表达缺少结构化nodes/edges。', ['DEC-027'])
        diagram = _diagram(slide['diagram'], sources, refs)
        # Keep model schema fields intact. Grounding metadata lives in traces.
    result['DEC-027'] = {'required': kind == 'diagram', 'diagram': diagram, 'type': diagram['type'] if diagram else 'none',
                         'lexical_relation_inference': 'disabled', 'fallback': 'fail rather than raster-only or inferred relation'}
    return result


def finalize(proposal, packet, sources, schemas=None, artifacts=None):
    proposal = copy.deepcopy(proposal)
    traces = list(packet['decision_traces'])
    outputs = {node: [] for node in NODES[:6]}
    for index, slide in enumerate(proposal['slides']):
        values = _slide_nodes(slide, packet, sources)
        for node, value in values.items(): outputs[node].append({'page_index': index, **value})
    for node, pages in outputs.items():
        _emit(schemas, artifacts, traces, _trace(node, {'page_count': len(proposal['slides']), 'evidence_refs': list(dict.fromkeys(reference for slide in proposal['slides'] for reference in slide['evidence_refs']))},
            {'pages': pages}, [(page, 'validated explicit structured visual choice; facts unchanged', True) for page in pages], packet['trace_id']))
    result = {'version': 'visual-1', 'trace_id': packet['trace_id'], 'status': 'executed_partial', 'decision_traces': sorted(traces, key=lambda item: item['node_id']),
              'visual_specs': outputs['DEC-022'], 'image_requirements': outputs['DEC-023'], 'asset_plan': outputs['DEC-024'],
              'table_specs': outputs['DEC-025'], 'chart_specs': outputs['DEC-026'], 'diagram_specs': outputs['DEC-027'],
              'template_selection': packet['template_selection'], 'design_tokens': packet['design_tokens'], 'resolved_assets': packet['resolved_assets'],
              'remaining_limits': ['Independent semantic image relevance/quality review remains required.',
                  'Hierarchy/network/matrix/funnel/swimlane relation semantics and complete node acceptance remain incomplete.',
                  'Source search and image generation services are not called; materialized outputs retain query/request provenance.',
                  'Template capacity, complete styles and brand lock require downstream validation.'], 'system_acceptance': 'not_claimed'}
    if schemas: schemas.validate('visual-result.schema.json', result)
    if artifacts: artifacts.json('visual-result.json', result)
    return proposal, result


def run_node(node_id, document, schemas=None, artifacts=None):
    if node_id not in NODES: _fail('VISUAL_NODE_UNKNOWN', '视觉节点未登记。', ['SYS-005'])
    if schemas: schemas.validate('visual-request.schema.json', document)
    packet = prepare(document['task'], document['sources'], document['context'], schemas)
    if node_id in {'DEC-028', 'DEC-029'}:
        traces = packet['decision_traces']
    else:
        if 'proposal' not in document: _fail('VISUAL_PROPOSAL_REQUIRED', '该视觉节点需要实际模型规划。', [node_id])
        _, result = finalize(document['proposal'], packet, document['sources'], schemas)
        traces = result['decision_traces']
    trace = next(item for item in traces if item['node_id'] == node_id)
    if artifacts: artifacts.json('decision-' + node_id + '.json', trace)
    return {'node_id': node_id, 'output': trace['output'], 'decision_trace': trace}
