"""Bounded DEC-006..021 execution cases; no model/network calls."""
import copy
import hashlib
import json
from pathlib import Path

from yoloongppt.errors import TaskError
from yoloongppt.narrative import NODES, finalize, model_packet, prepare, run_node
from yoloongppt.schemas import ROOT, SchemaRegistry

s = SchemaRegistry()
folder = ROOT / 'validation/fact-artifacts/generated'
read = lambda name: json.loads((folder / name).read_text('utf-8'))
task, sources, context, proposal = [read(name) for name in (
    'task-effective.json', 'approved-source-result.json', 'presentation-context.json', 'model-response.json')]
context['values']['page_count'] = len(proposal['slides'])
cases = []


def record(key, condition, actual):
    assert condition, (key, actual)
    cases.append({'id': key, 'passed': True, 'actual': actual})


def rejected(key, fn, expected):
    try:
        fn()
    except TaskError as error:
        record(key, error.code == expected, error.code)
    else:
        raise AssertionError(key)


families = [
    {'audience': '管理层', 'scenario': '汇报', 'duration': '约十分钟', 'tone': '简明正式'},
    {'audience': {'knowledge_level': '入门', 'roles': ['学员'], 'concerns': ['操作方法'], 'expected_actions': ['练习']},
     'scenario': '教学培训', 'duration': '十五至二十分钟', 'tone': '清楚平实'},
    {'audience': None, 'scenario': None, 'duration': None, 'tone': None},
]
for family_index, changes in enumerate(families):
    current = copy.deepcopy(context)
    current['values'].update(changes)
    document = {'task': task, 'sources': sources, 'context': current, 'proposal': proposal}
    for node in NODES:
        result = run_node(node, document, s)
        record(node + '-normal-' + str(family_index + 1), result['node_id'] == node and bool(result['output']),
               {'candidate_count': len(result['decision_trace']['candidates']), 'selected_count': len(result['decision_trace']['selected'])})


def boundary(node, context_change=None, proposal_change=None, source_change=None, code='TASK_SCHEMA_INVALID'):
    document = {'task': copy.deepcopy(task), 'sources': copy.deepcopy(sources),
                'context': copy.deepcopy(context), 'proposal': copy.deepcopy(proposal)}
    if context_change:
        context_change(document['context'])
    if proposal_change:
        proposal_change(document['proposal'])
    if source_change:
        source_change(document['sources'])
    rejected(node + '-boundary', lambda: run_node(node, document, s), code)


boundary('DEC-006', lambda c: c['values'].update(audience={'undocumented': '内容'}), code='AUDIENCE_FIELD_UNSUPPORTED')
boundary('DEC-007', lambda c: c['values'].update(duration=10), code='NARRATIVE_CONTEXT_INVALID')
boundary('DEC-008', lambda c: c['values'].update(language='unknown'), code='NARRATIVE_LANGUAGE_UNSUPPORTED')
boundary('DEC-009', proposal_change=lambda p: p['slides'][0].update(evidence_refs=['evidence_00000000-0000-4000-8000-000000000000']), code='NARRATIVE_EVIDENCE_UNKNOWN')
boundary('DEC-010', source_change=lambda x: x.update(approved_texts={k: '' for k in x['approved_texts']}), code='NARRATIVE_EVIDENCE_EMPTY')
boundary('DEC-011', source_change=lambda x: x.pop('approved_texts'), code='FACT_PROJECTION_INCOMPLETE')
boundary('DEC-012', lambda c: c['values'].update(page_count=1), code='NARRATIVE_PAGE_COUNT_MISMATCH')
boundary('DEC-013', lambda c: c['values'].update(page_count=0), code='NARRATIVE_PAGE_BUDGET_INVALID')
boundary('DEC-014', lambda c: c['values'].update(page_count=1), code='NARRATIVE_PAGE_COUNT_MISMATCH')
boundary('DEC-015', lambda c: c['values'].update(page_count=1), code='NARRATIVE_PAGE_COUNT_MISMATCH')
boundary('DEC-016', proposal_change=lambda p: p['slides'][0].update(goal=''))
boundary('DEC-017', proposal_change=lambda p: p['slides'][0].update(table={'columns':['a'],'rows':[['b']],'units':''}), code='TASK_SCHEMA_INVALID')


def invalid_table(p):
    p['slides'][0].update(kind='table', table={'columns': ['a', 'b'], 'rows': [['value']], 'units': ''})


boundary('DEC-018', proposal_change=invalid_table, code='NARRATIVE_TABLE_WIDTH')
boundary('DEC-019', proposal_change=lambda p: p['slides'][0].update(title='长' * 61))


def oversized(p):
    p['slides'][0].update(kind='chart', chart={'type': 'column', 'categories': ['a'],
        'series': [{'name': 'b', 'values': [8]}], 'units': '%'}, body=['补充限定说明' * 25])


boundary('DEC-020', proposal_change=oversized, code='NARRATIVE_CONTENT_CAPACITY')
boundary('DEC-021', lambda c: c['values'].update(citation_policy='inline'), code='NARRATIVE_CITATION_UNSUPPORTED')

packet = prepare(task, sources, context, s)
larger = copy.deepcopy(proposal)
larger['slides'][0].update(kind='text', table=None, chart=None, body=['限定说明原文' * 10] * 4)
before = copy.deepcopy(larger)
changed, result = finalize(larger, packet, sources, s)
record('literal_notes_preservation', all(text in changed['slides'][0]['body'] or text in changed['slides'][0]['notes']
       for text in before['slides'][0]['body']), result['rewrites'][0]['action'])
record('input_not_mutated', larger == before, 'copy-on-execution')
record('all_sixteen_nodes_executed', [t['node_id'] for t in result['decision_traces']] == list(NODES),
       [t['node_id'] for t in result['decision_traces']])
record('model_packet_actual_policy', model_packet(packet)['page_budget']['target'] == len(proposal['slides']), model_packet(packet)['storyline'])
record('selected_storyline_consumed', changed['storyline']['pattern'] == packet['storyline']['pattern'], changed['storyline'])
record('no_invented_causal_edges', packet['content_graph']['edges'] == [], 'lexical candidates explicitly unverified')
record('allocation_conservation', sum(x['pages'] for x in result['section_budget']['sections']) == len(proposal['slides']), result['section_budget']['total'])
record('citation_backlinks', all(len(p['source_backlinks']) == len(p['evidence_refs']) for p in result['placements']), 'source identity retained')
marked = copy.deepcopy(proposal)
marked['slides'][0].update(kind='text', table=None, chart=None, body=['补充说明原文' * 10] * 3 + ['【已选来源】保留可见的选择标记'])
retained, _ = finalize(marked, packet, sources, s)
record('selected_source_marker_visible', any('【已选来源】' in x for x in retained['slides'][0]['body']), retained['slides'][0]['body'])
marked['slides'][0]['body'] = ['【假设】' + '限定说明' * 15] * 4
rejected('visible_marker_overflow_blocks', lambda: finalize(marked, packet, sources, s), 'NARRATIVE_CONTENT_CAPACITY')
placeholder_sources = copy.deepcopy(sources)
placeholder_sources['fact_boundary']['actions'].append({'mode': 'placeholder', 'label': '【待补充：客户名称】'})
marked['slides'][0]['body'] = ['补充说明原文' * 10] * 3 + ['【待补充：客户名称】']
retained, _ = finalize(marked, packet, placeholder_sources, s)
record('placeholder_visible', any('【待补充：客户名称】' in x for x in retained['slides'][0]['body']), retained['slides'][0]['body'])
own = [ROOT/'src/yoloongppt/narrative.py', Path(__file__), *sorted((ROOT/'contracts').glob('narrative-*.schema.json'))]
report = {'requirement_ids': list(NODES) + ['CNT-005', 'CNT-006', 'CNT-007', 'CNT-008', 'CNT-009', 'CNT-011', 'CNT-013', 'SYS-005'],
          'status': 'passed', 'cases': cases, 'case_count': len(cases), 'source_sha256': {
              str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in own},
          'scope': 'module/runtime verification; no new model calls, no system acceptance claim',
          'remaining_limits': result['remaining_limits']}
destination = Path('/runtime/narrative-validation')
destination.mkdir(parents=True, exist_ok=True)
(destination/'narrative-runtime.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
(destination/'narrative-context.json').write_text(json.dumps(packet, ensure_ascii=False, indent=2), 'utf-8')
(destination/'narrative-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
print(json.dumps({'status': 'passed', 'case_count': len(cases), 'report': str(destination/'narrative-runtime.json')}))
