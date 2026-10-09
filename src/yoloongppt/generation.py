"""Actual product pipeline: source -> real model -> specs/DAG -> editable PPTX -> render/QA."""
import time
import json
from pathlib import Path
from uuid import UUID

from .artifacts import RunArtifacts
from .errors import TaskError
from .planning import compile_deck, plan, preflight
from .quality import check
from .rendering import render
from .sources import inspect_sources
from .tasks import validate_task
from .writer import execute
from .review import review, repair_references
from .routing import route_task
from .atomic import AtomicRegistry


def generate(task, schemas, store, trace, checkpoint=None):
    validate_task(task, schemas, trace)
    artifacts = RunArtifacts()
    warnings = []
    timeline = []
    def step(component, action):
        begin = time.monotonic()
        result = action()
        timeline.append({'component': component, 'status': 'executed', 'duration_seconds': round(time.monotonic()-begin, 3)})
        artifacts.json('pipeline-trace.json', {'trace_id': trace, 'steps': timeline, 'warnings': warnings,
                                               'decision_coverage': 'DEC-001 executed; model proposal and fixed compiler subset; DEC-002–040 graph not complete'})
        return result
    try:
        artifacts.json('task.json', task)
        routing = step('DEC-001', lambda: route_task(task, schemas, trace))
        artifacts.json('decision-route.json', routing['decision_trace'])
        artifacts.json('runtime-snapshot.json', routing['decision_trace']['input']['runtime_snapshot'])
        if routing['route']['route_status'] != 'routed':
            raise TaskError('MODE_CLARIFICATION_REQUIRED', '模式或附件保护范围有歧义；先澄清，未调用模型或写入PPT。', 'DEC-001', ['DEC-001'])
        task = {**task, 'route': routing['route']}
        artifacts.json('task-effective.json', task)
        count, style, warnings = preflight(task)
        artifacts.json('atomic-registry.json', AtomicRegistry(schemas).snapshot())
        sources = step('SYS-003/004', lambda: inspect_sources(task, schemas, store, trace))
        artifacts.json('source-result.json', sources)
        previous_deck = None
        if checkpoint:
            old = json.loads((checkpoint/'source-result.json').read_text(encoding='utf-8'))
            identity = lambda result: [(e['evidence_id'], e['source_hash'], e['parser_version']) for e in result['evidence']]
            if identity(old) != identity(sources):
                raise TaskError('CHECKPOINT_SOURCE_CHANGED', '来源或解析版本变化，断点不能复用旧模型响应。', 'Generation', ['SYS-005'])
            response_path = checkpoint/'model-response-effective.json' if (checkpoint/'model-response-effective.json').is_file() else checkpoint/'model-response.json'
            proposal = json.loads(response_path.read_text(encoding='utf-8'))
            schemas.validate('generation-model.schema.json', proposal)
            model = json.loads((checkpoint/'model-call.json').read_text(encoding='utf-8'))
            model = {**model, 'reused_from_run': checkpoint.name, 'fresh_model_call_this_run': False}
            artifacts.json('model-response.json', json.loads((checkpoint/'model-response.json').read_text(encoding='utf-8')))
            artifacts.json('model-call.json', model)
            if response_path.name == 'model-response-effective.json':
                artifacts.json('model-response-effective.json', proposal)
                artifacts.json('checkpoint-reference-repair.json', {'reused_from_run': checkpoint.name, 'artifact': response_path.name})
            artifacts.json('model-request.json', json.loads((checkpoint/'model-request.json').read_text(encoding='utf-8')))
            if (checkpoint/'deck-spec.json').is_file():
                previous_deck = json.loads((checkpoint/'deck-spec.json').read_text(encoding='utf-8'))
                schemas.validate('deck-execution.schema.json', previous_deck)
            timeline.append({'component': 'SYS-005 partial content planner', 'status': 'checkpoint_reused', 'previous_run_id': checkpoint.name})
        else:
            proposal, model = step('SYS-005 partial content planner', lambda: plan(task, sources, schemas, artifacts, count))
        deck, execution = step('SYS-010/011', lambda: compile_deck(proposal, style, trace, previous_deck))
        artifacts.json('deck-spec.json', deck); artifacts.json('execution-plan.json', execution)
        object_map, calls = step('SYS-012/013', lambda: execute(deck, execution, artifacts.path/'deck.pptx', schemas))
        artifacts.json('object-map.json', object_map); artifacts.json('execution-trace.json', calls)
        renders = step('SYS-014', lambda: render(artifacts.path/'deck.pptx', deck, artifacts.path))
        artifacts.json('render-report.json', renders)
        quality = step('SYS-015', lambda: check(deck, artifacts.path/'deck.pptx', object_map, sources, renders, artifacts.path))
        if quality['issues'] and all(i['code'] in {'CHART_VALUE_UNSUPPORTED', 'FACT_NUMBER_UNSUPPORTED'} for i in quality['issues']):
            artifacts.json('quality-before-reference-repair.json', quality)
            proposal = step('SYS-015 reference repair', lambda: repair_references(task, proposal, sources, quality, artifacts, schemas))
            artifacts.json('model-response-effective.json', proposal)
            (artifacts.path/'deck.pptx').rename(artifacts.path/'before-reference-repair.pptx')
            (artifacts.path/'render').rename(artifacts.path/'render-before-reference-repair')
            deck, execution = compile_deck(proposal, style, trace, deck)
            artifacts.json('deck-spec.json', deck); artifacts.json('execution-plan.json', execution)
            object_map, calls = execute(deck, execution, artifacts.path/'deck.pptx', schemas)
            artifacts.json('object-map.json', object_map); artifacts.json('execution-trace.json', calls)
            renders = render(artifacts.path/'deck.pptx', deck, artifacts.path)
            artifacts.json('render-report.json', renders)
            quality = check(deck, artifacts.path/'deck.pptx', object_map, sources, renders, artifacts.path)
        model_review = step('SYS-015 actual visual/fact review', lambda: review(task, deck, sources, renders, artifacts))
        quality['model_review'] = model_review
        quality['p0_issue_count'] += sum(i['severity'] == 'P0' for i in model_review['issues'])
        quality['coverage']['visual_semantic'] = 'model_review_executed'
        quality['coverage']['fact_semantic'] = 'model_review_executed'
        quality['reason'] = 'Deterministic and real image/fact model checks executed; complete decision graph, accessibility, PowerPoint compatibility and revision gates are not proven.'
        artifacts.json('quality-report.json', quality)
        artifacts.json('manifest.json', {'run_id': artifacts.run_id, 'artifacts': artifacts.manifest()})
        result = {'ok': True, 'trace_id': trace, 'task_id': task['task_id'], 'run_id': artifacts.run_id,
                  'operation': 'generate', 'state': 'draft_generated', 'artifact_root': str(artifacts.path),
                  'pptx': str(artifacts.path/'deck.pptx'), 'slide_count': len(deck['slides']), 'model': model,
                  'qa': {'status': quality['status'], 'p0_issue_count': quality['p0_issue_count'], 'acceptance': quality['acceptance']},
                  'warnings': warnings, 'boundary': 'Actual model/PPTX/render/deterministic and image/fact model QA; complete DEC graph, QA coverage, revision scope and system acceptance unfinished.'}
        artifacts.json('result.json', result)
        # Include the result in the final manifest too.
        artifacts.json('manifest.json', {'run_id': artifacts.run_id, 'artifacts': artifacts.manifest()})
        return result
    except TaskError as error:
        error.details.append({'run_id': artifacts.run_id, 'artifact_root': str(artifacts.path)})
        artifacts.json('failure.json', error.result(trace))
        artifacts.json('manifest.json', {'run_id': artifacts.run_id, 'artifacts': artifacts.manifest()})
        raise


def resume(run_id, schemas, store, trace):
    try:
        if str(UUID(run_id)) != run_id:raise ValueError()
    except ValueError:
        raise TaskError('CHECKPOINT_ID_INVALID', '断点ID必须为标准UUID。', 'Generation', ['SYS-005']) from None
    folder = Path('/runtime/runs')/run_id
    required = ['task.json', 'source-result.json', 'model-response.json', 'model-request.json', 'model-call.json']
    if not all((folder/name).is_file() for name in required):
        raise TaskError('CHECKPOINT_INCOMPLETE', '没有可恢复的模型阶段断点。', 'Generation', ['SYS-005'])
    task = json.loads((folder/'task.json').read_text(encoding='utf-8'))
    return generate(task, schemas, store, trace, folder)
