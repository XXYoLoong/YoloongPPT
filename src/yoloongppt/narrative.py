"""Executable DEC-006..021 narrative policy; preserves evidence and literal text.

This module does not assert semantic truth from lexical cues. It gives the real
planner a bounded audience/style/story packet and validates its page decisions.
"""
import copy
import hashlib
import json
import re
import time

from .artifacts import entity
from .errors import TaskError, trace_id
from .facts import approved_text

NODES = tuple(f'DEC-{i:03d}' for i in range(6, 22))
MAPPING = {
    'P01': 'routing/Strategist/design_spec/spec_lock/template/QC',
    'P02': 'induction/outline/reference/action/reflection/eval',
    'P03': 'Standard/Smart/layout/template/API/MCP',
    'P04': 'outline/content/layout/PureLayout/PPTAdapter',
    'P05': 'planning/schema/theme/layout/render/QA/revise/MCP',
}
STORIES = ('linear', 'problem_solution', 'conclusion_first', 'timeline', 'teaching_progression', 'data_driven')
RELATION_CUES = {
    'comparison': ('相比', '对比', 'versus', ' compared '),
    'temporal': ('随后', '之前', '之后', '然后', 'before', 'after'),
    'process': ('步骤', '流程', '首先', '其次', '最后'),
    'hierarchy': ('包含', '组成', '分为'),
    'classification': ('类别', '分类', '类型'),
    'problem_solution': ('问题', '方案', '解决'),
    'causal_unverified': ('因为', '导致', '由于', '因此', 'because'),
}


def _fail(code, message, ids, details=None):
    raise TaskError(code, message, 'NarrativeOrchestrator', ids, details or [])


def _local(prefix, value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')
    return prefix + '_' + hashlib.sha256(raw).hexdigest()[:20]


def _unique(values):
    return list(dict.fromkeys(values))


def _validate(schemas, filename, value):
    if schemas is not None:
        schemas.validate(filename, value)


def _trace(node, inputs, candidates, selected, output, trace, start=None, rules=None):
    options = []
    for value, reason, refs, score in candidates:
        options.append({'node_id': node, 'candidate_id': entity('candidate'), 'value': value,
                        'score': score, 'reasons': [{'rule': reason}], 'evidence_refs': refs,
                        'constraints': [{'preserve_evidence': True, 'no_implicit_fact_inference': True}]})
    return {'trace_id': trace, 'node_id': node, 'input': inputs, 'candidates': options,
            'selected': [options[i]['candidate_id'] for i in selected],
            'rules': {'source_project_mapping': MAPPING, 'score_semantics': 'policy ranking, not calibrated confidence',
                      'confidence': 'unknown', 'fallback': 'explicit unknown or structured failure', **(rules or {})},
            'output': output, 'duration': max(0, time.monotonic() - start) if start else 0.0, 'error': None}


def _record(traces, node, inputs, output, trace, candidates=None, selected=None, rules=None):
    if candidates is None:
        candidates = [(output, 'execute validated policy; retain uncertainty explicitly', [], 1.0)]
    result = _trace(node, inputs, candidates, list(range(len(candidates))) if selected is None else selected,
                    output, trace, rules=rules)
    traces.append(result)
    return output


def _profile(value):
    profile = {'knowledge_level': None, 'roles': [], 'concerns': [], 'expected_actions': [], 'field_provenance': []}
    if value is None:
        return profile
    if isinstance(value, str) and value.strip():
        profile['roles'] = [value]
    elif isinstance(value, dict):
        if set(value) - {'knowledge_level', 'roles', 'concerns', 'expected_actions'}:
            _fail('AUDIENCE_FIELD_UNSUPPORTED', '受众字段未登记，未忽略。', ['DEC-006', 'CNT-005'])
        profile.update(copy.deepcopy(value))
    else:
        _fail('AUDIENCE_INPUT_INVALID', '受众必须为原文字符串或受众字段对象。', ['DEC-006', 'CNT-005'])
    for field in ('knowledge_level', 'roles', 'concerns', 'expected_actions'):
        if profile[field]:
            profile['field_provenance'].append({'field': field, 'source': {
                'kind': 'presentation_context', 'context_pointer': '/values/audience'}})
    return profile


def _text_or_null(value, field):
    if value is not None and (not isinstance(value, str) or not value.strip()):
        _fail('NARRATIVE_CONTEXT_INVALID', '场景/时长/语气要求保留非空原文字符串，未猜测单位或等级。',
              ['DEC-007', 'DEC-008'], [{'field': field}])
    return value


def _graph(sources):
    nodes, edges, refs, cues = [], [], [], []
    for evidence in sources['evidence']:
        text = approved_text(sources, evidence)
        if not text.strip():
            continue
        eid = evidence['evidence_id']
        key = _local('content', [eid, text])
        nodes.append({'node_id': key, 'text': text, 'evidence_refs': [eid], 'assumption_refs': []})
        refs.append(eid)
        for relation, words in RELATION_CUES.items():
            present = [word for word in words if word in text.lower()]
            if present:
                cues.append({'node_id': key, 'relation': relation, 'literal_cues': present,
                             'evidence_refs': [eid], 'status': 'candidate_only',
                             'reason': 'literal cue is not a proven semantic relation'})
    # No fabricated causal/temporal edges between independent source blocks.
    return {'nodes': nodes, 'edges': edges, 'evidence_refs': _unique(refs)}, cues


def prepare(task, sources, context, schemas=None, artifacts=None):
    """Run context decisions before the existing real model call.

    Return a JSON packet for planning.plan's user message. Selected facts only
    are read through approved_text, so losing conflict values cannot re-enter.
    """
    values = context['values']
    trace = context.get('trace_id') or trace_id()
    traces = []
    if context.get('issues') or context.get('constraints', {}).get('conflicts'):
        _fail('NARRATIVE_CONTEXT_UNRESOLVED', '上游约束未决，叙事不替换或吞掉冲突。', ['DEC-002', 'DEC-006'])
    audience = _profile(values.get('audience'))
    _validate(schemas, 'audience-profile.schema.json', audience)
    _record(traces, 'DEC-006', {'audience': values.get('audience')}, audience, trace,
            rules={'missing_profile': 'retain null/empty; do not stereotype audience'})
    scenario = {'scenario': _text_or_null(values.get('scenario'), 'scenario'),
                'duration': _text_or_null(values.get('duration'), 'duration'), 'field_provenance': []}
    for field in ('scenario', 'duration'):
        if scenario[field] is not None:
            scenario['field_provenance'].append({'field': field, 'source': {
                'kind': 'presentation_context', 'context_pointer': '/values/' + field}})
    _validate(schemas, 'presentation-scenario.schema.json', scenario)
    _record(traces, 'DEC-007', {'scenario': values.get('scenario'), 'duration': values.get('duration')}, scenario, trace)
    language = values.get('language', 'zh-CN')
    if language not in ('zh-CN', 'en', 'mixed'):
        _fail('NARRATIVE_LANGUAGE_UNSUPPORTED', '语言要求未登记，未替换为中文。', ['DEC-008', 'CNT-007'])
    style = {'language': language, 'tone': _text_or_null(values.get('tone'), 'tone'), 'formal_level': None,
             'terminology_rules': [], 'brand_terms': [], 'field_provenance': [
                 {'field': 'language', 'source': {'kind': 'presentation_context', 'context_pointer': '/values/language'}}]}
    if style['tone']:
        style['field_provenance'].append({'field': 'tone', 'source': {
            'kind': 'presentation_context', 'context_pointer': '/values/tone'}})
    _validate(schemas, 'language-style-spec.schema.json', style)
    _record(traces, 'DEC-008', {'language': language, 'tone': values.get('tone'), 'audience': audience}, style, trace)
    graph, cues = _graph(sources)
    if not graph['nodes']:
        _fail('NARRATIVE_EVIDENCE_EMPTY', '没有选定可用事实文本，不能编造叙事。', ['DEC-009', 'CNT-012'])
    _validate(schemas, 'content-graph.schema.json', graph)
    _record(traces, 'DEC-010', {'evidence_refs': graph['evidence_refs']},
            {'content_graph': graph, 'relation_candidates': cues, 'semantic_edges_status': 'not_inferred'}, trace)
    count = values.get('page_count')
    if type(count) is not int or not 1 <= count <= 30:
        _fail('NARRATIVE_PAGE_BUDGET_INVALID', '页数必须为1至30整数；不补页或裁剪。', ['DEC-013'])
    candidates = []
    scene = (scenario['scenario'] or '').lower()
    relations = {c['relation'] for c in cues}
    for pattern in STORIES:
        score = 1.0 if pattern == 'linear' else 0.0
        reason = 'stable source-order presentation default'
        if pattern == 'conclusion_first' and any(w in scene for w in ('汇报', '路演', 'report', 'pitch')):
            score, reason = 4.0, 'caller scenario benefits from presenting the selected thesis first'
        elif pattern == 'teaching_progression' and any(w in scene for w in ('教学', '培训', 'training', 'teach')):
            score, reason = 4.0, 'caller teaching scenario orders explanation before application'
        elif pattern == 'timeline' and 'temporal' in relations:
            score, reason = 2.0, 'literal temporal cues suggest a candidate sequence; not a causal claim'
        elif pattern == 'problem_solution' and 'problem_solution' in relations:
            score, reason = 2.0, 'literal problem/solution cue; no invented solution facts'
        elif pattern == 'data_driven' and any(re.search(r'\d+(?:\.\d+)?\s*[%％]', n['text']) for n in graph['nodes']):
            score, reason = 1.5, 'selected evidence contains percentages; use only grounded values'
        candidates.append(({'pattern': pattern}, reason, graph['evidence_refs'], score))
    chosen = max(range(len(candidates)), key=lambda i: candidates[i][3])
    storyline = {'pattern': candidates[chosen][0]['pattern'], 'rationale': candidates[chosen][1],
                 'evidence_refs': graph['evidence_refs']}
    _record(traces, 'DEC-011', {'scenario': scenario, 'relation_candidates': cues}, storyline, trace, candidates, [chosen])
    budget = {'target': count, 'minimum': count, 'maximum': count, 'allowed_deviation': 0,
              'duration_original': scenario['duration'], 'source_characters': sum(len(n['text']) for n in graph['nodes']),
              'policy': 'normalized page count is binding; duration guides density and speaker notes, not implicit count replacement'}
    _record(traces, 'DEC-013', {'page_count': count, 'duration': scenario['duration']}, budget, trace)
    citation = values.get('citation_policy', 'notes')
    if citation != 'notes':
        _fail('NARRATIVE_CITATION_UNSUPPORTED', '当前写入器仅接入notes；未静默替换请求的引用模式。', ['DEC-021', 'CNT-010'])
    packet = {'version': 'narrative-1', 'trace_id': trace, 'audience': audience, 'scenario': scenario,
              'language_style': style, 'content_graph': graph, 'relation_candidates': cues,
              'storyline': storyline, 'page_budget': budget, 'citation_mode': citation,
              'content_policy': {'title_max_characters': 60, 'body_max_characters': 180,
                  'list_max_items': 6, 'table_max_columns': 6, 'table_max_rows': 8,
                  'notes_preserve_overflow': True, 'no_text_truncation': True},
              'decision_traces': traces}
    _validate(schemas, 'narrative-context.schema.json', packet)
    if artifacts:
        artifacts.json('narrative-context.json', packet)
        for item in traces:
            artifacts.json('decision-' + item['node_id'] + '.json', item)
    return packet


def model_packet(context):
    """Consume the decisions as real planner instructions without trace bloat."""
    return {key: copy.deepcopy(context[key]) for key in ('audience', 'scenario', 'language_style',
            'storyline', 'page_budget', 'content_policy', 'citation_mode')}


def finalize(proposal, narrative_context, sources, schemas=None, artifacts=None):
    """Execute page grouping/content budgets on real model output.

    Complete text items can move into notes with before/after trace. No fact is
    shortened, no page silently removed, and a sole over-capacity item fails.
    """
    context = copy.deepcopy(narrative_context)
    _validate(schemas, 'narrative-context.schema.json', context)
    _validate(schemas, 'generation-model.schema.json', proposal)
    proposal = copy.deepcopy(proposal)
    traces = copy.deepcopy(context['decision_traces'])
    trace = context['trace_id']
    count = context['page_budget']['target']
    slides = proposal['slides']
    if len(slides) != count:
        _fail('NARRATIVE_PAGE_COUNT_MISMATCH', '实际规划页数不满足绑定预算；不删页或补空页。', ['DEC-013', 'DEC-015'])
    # The selected story policy is actually written into the compiled proposal;
    # model prose cannot replace the policy silently. Page order itself remains
    # the source-grounded model's output, with the stated review limitation.
    model_story = copy.deepcopy(proposal['storyline'])
    proposal['storyline'] = {key: context['storyline'][key] for key in ('pattern', 'rationale')}
    known = {e['evidence_id']: e for e in sources['evidence']}
    known_assumptions = sources.get('fact_boundary', {}).get('assumption_values', {})
    for index, slide in enumerate(slides):
        if set(slide['evidence_refs']) - set(known):
            _fail('NARRATIVE_EVIDENCE_UNKNOWN', '页面引用未知证据。', ['DEC-009', 'DEC-015'], [{'page': index}])
        if set(slide.get('assumption_refs', [])) - set(known_assumptions):
            _fail('NARRATIVE_ASSUMPTION_UNKNOWN', '页面引用未知假设。', ['DEC-005', 'DEC-009'], [{'page': index}])
    thesis = {'main_takeaway': proposal['main_takeaway'], 'supporting_points': [
        {'text': p['goal'], 'evidence_refs': p['evidence_refs'], 'assumption_refs': p.get('assumption_refs', [])}
        for p in slides], 'evidence_refs': _unique([ref for p in slides for ref in p['evidence_refs']])}
    _validate(schemas, 'deck-thesis.schema.json', thesis)
    _record(traces, 'DEC-009', {'model_main_takeaway': proposal['main_takeaway']}, thesis, trace,
            rules={'semantic_truth': 'requires independent fact review; reference existence is not entailment proof'})
    sections = []
    for index, page in enumerate(slides):
        section_id = _local('section', [index, page['title'], page['evidence_refs']])
        sections.append({'section_id': section_id, 'order': index, 'title': page['title'], 'parent_section_id': None,
                         'transition': 'continue' if index else 'open', 'page_indices': [index],
                         'evidence_refs': page['evidence_refs']})
    outline = {'sections': sections, 'ordering': context['storyline']['pattern'],
               'ordering_origin': 'model consumes selected narrative_context; literal model page order retained',
               'subsections_status': 'not_requested'}
    _record(traces, 'DEC-012', {'storyline': context['storyline'], 'titles': [p['title'] for p in slides]}, outline, trace)
    allocation = {'total': count, 'sections': [{'section_id': s['section_id'], 'pages': len(s['page_indices']),
                   'page_indices': s['page_indices']} for s in sections],
                  'reservation_policy': 'actual cover/conclusion participate in fixed count; no invented appendix or agenda page'}
    _record(traces, 'DEC-014', {'outline': outline, 'page_budget': context['page_budget']}, allocation, trace)
    page_plan, intents, types, budgets, rewrites, placements = [], [], [], [], [], []
    contents = []
    for index, page in enumerate(slides):
        before = copy.deepcopy(page)
        key = _local('page', [index, page['title'], page['evidence_refs']])
        intent = {'page_key': key, 'page_index': index, 'goal': page['goal'], 'core_message': page['title'],
                  'evidence_refs': page['evidence_refs'], 'assumption_refs': page.get('assumption_refs', [])}
        intents.append(intent)
        role = 'data_table' if page['kind'] == 'table' else 'data_chart' if page['kind'] == 'chart' else (
            'cover' if index == 0 and count > 1 else 'summary' if index == count - 1 and count > 1 else 'explanation')
        types.append({'page_key': key, 'selected_type': role, 'native_kind': page['kind'],
                      'reason': 'actual data kind takes precedence; position only classifies text pages',
                      'unselected_advanced_types': ['SWOT', 'timeline', 'flow', 'comparison', 'KPI'],
                      'advanced_types_status': 'not_claimed_from_unverified_keywords'})
        if page['kind'] == 'table':
            if page['table'] is None or len(page['table']['columns']) > 6 or len(page['table']['rows']) > 8:
                _fail('NARRATIVE_TABLE_CAPACITY', '表格超过当前原生容量，未裁剪行列。', ['DEC-018'], [{'page': index}])
            if any(len(row) != len(page['table']['columns']) for row in page['table']['rows']):
                _fail('NARRATIVE_TABLE_WIDTH', '表格宽度不一致，未补空或删单元格。', ['DEC-018'], [{'page': index}])
        if page['kind'] == 'chart':
            if page['chart'] is None or any(len(s['values']) != len(page['chart']['categories']) for s in page['chart']['series']):
                _fail('NARRATIVE_CHART_CAPACITY', '图表类别与数据系列不一致。', ['DEC-018'], [{'page': index}])
        if (page['kind'] != 'table' and page['table'] is not None) or (page['kind'] != 'chart' and page['chart'] is not None):
            _fail('NARRATIVE_DATA_KIND_CONFLICT', '页面类型与数据对象冲突，不丢弃额外数据。', ['DEC-017', 'DEC-018'])
        max_items = 6 if page['kind'] == 'text' else 2
        max_chars = 180 if page['kind'] == 'text' else 100
        moved = []
        labels = ['【假设】', '【推算】', '【已选来源】']
        labels += [v.get('raw_text', '') for aid, v in known_assumptions.items()
                   if aid in page.get('assumption_refs', []) and isinstance(v, dict)]
        labels += [action['label'] for action in sources.get('fact_boundary', {}).get('actions', [])
                   if action.get('mode') == 'placeholder' and action.get('label')]
        labels = [label for label in labels if label]
        # Move whole supplementary bullets, preserving their relative order in
        # notes. Never remove the only item or truncate a sentence/unit/value.
        while len(page['body']) > 1 and (len(page['body']) > max_items or sum(map(len, page['body'])) > max_chars):
            removable = [i for i, text in enumerate(page['body']) if not any(label in text for label in labels)]
            if not removable:
                break
            original_index = removable[-1]
            moved.insert(0, page['body'].pop(original_index))
        if sum(map(len, page['body'])) > max_chars or len(page['body']) > max_items:
            _fail('NARRATIVE_CONTENT_CAPACITY', '核心段或需可见标记超过正文容量，需显式改写/拆页；没有截字或隐藏标记。',
                  ['DEC-018', 'DEC-020'], [{'page': index, 'characters': sum(map(len, page['body']))}])
        if moved:
            preserved = '\n'.join(moved)
            page['notes'] += ('\n' if page['notes'] else '') + '【容量决策：完整补充内容移入备注】\n' + preserved
        budget = {'page_key': key, 'title_max_characters': 60, 'body_max_characters': max_chars,
                  'list_max_items': max_items, 'table_max_columns': 6, 'table_max_rows': 8,
                  'actual_title_characters': len(page['title']), 'actual_body_characters': sum(map(len, page['body'])),
                  'notes_characters': len(page['notes']), 'images': {'capacity': 0, 'status': 'not_selected'},
                  'geometry_capacity_status': 'subsequent native-layout capacity decision required'}
        budgets.append(budget)
        contents.append({'page_key': key, 'title': page['title'], 'body_hierarchy': [
            {'order': i, 'text': text, 'level': 1} for i, text in enumerate(page['body'])],
            'evidence_refs': page['evidence_refs'], 'subtitle_status': 'not_invented'})
        rewrites.append({'page_key': key, 'action': 'move_complete_items_to_notes' if moved else 'retain',
                         'before': before, 'after': copy.deepcopy(page), 'moved_items': moved,
                         'evidence_refs': page['evidence_refs'], 'assumption_refs': page.get('assumption_refs', []),
                         'preservation': 'all literal input title/body/notes/data retained; no character truncation',
                         'semantic_rewrite_status': 'no paraphrase performed'})
        placements.append({'page_key': key, 'mode': 'notes', 'surface': 'speaker_notes', 'visible_on_slide': False,
                           'layout_occupancy': 0, 'evidence_refs': page['evidence_refs'],
                           'source_backlinks': [{'evidence_id': eid, 'source_id': known[eid]['source_id']} for eid in page['evidence_refs']],
                           'writer_consumer': 'python-pptx.add_notes + ObjectMap source_refs'})
        page_plan.append({'page_key': key, 'page_index': index, 'section_id': sections[index]['section_id'],
                          'title': page['title'], 'evidence_refs': page['evidence_refs'],
                          'pagination_policy': 'model semantic grouping validated against exact budget; capacity overflow explicit'})
    values = {
        'DEC-015': {'pages': page_plan, 'total': len(page_plan)},
        'DEC-016': {'intents': intents}, 'DEC-017': {'slide_types': types},
        'DEC-018': {'content_budgets': budgets}, 'DEC-019': {'slide_contents': contents},
        'DEC-020': {'rewrites': rewrites}, 'DEC-021': {'placements': placements},
    }
    for node, output in values.items():
        _record(traces, node, {'page_count': count, 'source_evidence_refs': list(known)}, output, trace)
    _validate(schemas, 'generation-model.schema.json', proposal)
    result = {'version': 'narrative-1', 'trace_id': trace, 'status': 'executed',
              'system_acceptance': 'not_claimed', 'deck_thesis': thesis, 'outline': outline,
              'model_storyline_original': model_story,
              'section_budget': allocation, **{key: value for value in values.values() for key, value in value.items()},
              'decision_traces': sorted(traces, key=lambda t: t['node_id']),
              'remaining_limits': ['semantic content relations require extraction/review',
                  'full hierarchical section generation and advanced page types not completed',
                  'only notes citation rendering integrated', 'capacity is followed by physical layout and render QA']}
    _validate(schemas, 'narrative-result.schema.json', result)
    if artifacts:
        artifacts.json('narrative-result.json', result)
        for item in result['decision_traces']:
            artifacts.json('decision-' + item['node_id'] + '.json', item)
    return proposal, result


def run_node(node_id, document, schemas=None, artifacts=None):
    """Independent runnable node using the same implementation as generation."""
    if node_id not in NODES:
        _fail('NARRATIVE_NODE_UNKNOWN', '叙事节点未登记。', ['SYS-005'])
    if schemas is not None:
        schemas.validate('narrative-request.schema.json', document)
    context = prepare(document['task'], document['sources'], document['context'], schemas)
    if node_id not in {t['node_id'] for t in context['decision_traces']}:
        if 'proposal' not in document:
            _fail('NARRATIVE_PROPOSAL_REQUIRED', '此节点须提供实际模型规划作为输入。', [node_id])
        _, result = finalize(document['proposal'], context, document['sources'], schemas)
        traces = result['decision_traces']
    else:
        traces = context['decision_traces']
    selected = next(t for t in traces if t['node_id'] == node_id)
    _validate(schemas, 'narrative-trace.schema.json', selected)
    if artifacts:
        artifacts.json('decision-' + node_id + '.json', selected)
    return {'node_id': node_id, 'output': selected['output'], 'decision_trace': selected}
