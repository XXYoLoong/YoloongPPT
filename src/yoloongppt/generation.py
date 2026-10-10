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
from .context import normalize
from .source_roles import assign, fact_input
from .facts import interpret,resolve,boundaries,project
from .narrative import prepare, finalize


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
                                               'decision_coverage': 'DEC-001–021 bounded execution when reached; full original decision acceptance remains incomplete'})
        return result
    try:
        from .observability import version_manifest
        artifacts.json('version-manifest.json',version_manifest(schemas))
        artifacts.json('task.json', task)
        routing = step('DEC-001', lambda: route_task(task, schemas, trace))
        artifacts.json('decision-route.json', routing['decision_trace'])
        artifacts.json('runtime-snapshot.json', routing['decision_trace']['input']['runtime_snapshot'])
        if routing['route']['route_status'] != 'routed':
            raise TaskError('MODE_CLARIFICATION_REQUIRED', '模式或附件保护范围有歧义；先澄清，未调用模型或写入PPT。', 'DEC-001', ['DEC-001'])
        task = {**task, 'route': routing['route']}
        normalized = step('DEC-002', lambda: normalize(task, schemas, trace))
        artifacts.json('decision-context.json', normalized['decision_trace'])
        artifacts.json('presentation-context.json', normalized['context'])
        count, style, warnings = preflight(task, normalized['context'], schemas)
        task = {**task, 'constraints': normalized['context']['constraints']}
        artifacts.json('task-effective.json', task)
        artifacts.json('atomic-registry.json', AtomicRegistry(schemas).snapshot())
        sources = step('SYS-003/004', lambda: inspect_sources(task, schemas, store, trace))
        artifacts.json('source-result.json', sources)
        roles = step('DEC-003', lambda: assign({'task':task,'source_bundle':sources['source_bundle']}, schemas, trace))
        artifacts.json('decision-source-roles.json', roles['decision_trace'])
        artifacts.json('source-role-map.json', roles['source_role_map'])
        if roles['source_role_map']['status'] != 'assigned':
            raise TaskError('SOURCE_ROLES_UNRESOLVED', '来源身份/角色有冲突或无法对应加载结果；未调用模型。', 'DEC-003', ['DEC-003'], roles['source_role_map']['issues'])
        sources = fact_input(sources, roles['source_role_map'])
        if not sources['evidence']:
            raise TaskError('FACT_SOURCE_MISSING', '当前生成路径没有已选事实/指令依据，未把风格或模板当事实。', 'DEC-003', ['DEC-003'])
        artifacts.json('fact-source-result.json', sources)
        if checkpoint:
            if not (checkpoint/'fact-interpretation.json').is_file() or not (checkpoint/'fact-model-call.json').is_file():
                raise TaskError('FACT_CHECKPOINT_MISSING','旧断点缺少事实解释及真实模型记录，不能未经重算复用内容。','Generation',['DEC-004','DEC-005','SYS-005'])
            old=json.loads((checkpoint/'fact-source-result.json').read_text(encoding='utf-8'))
            identity=lambda result:[(e['evidence_id'],e['source_hash'],e['parser_version']) for e in result['evidence']]
            if identity(old)!=identity(sources):raise TaskError('CHECKPOINT_SOURCE_CHANGED','事实来源或解析版本变化，不能复用事实解释。','Generation',['DEC-004','SYS-005'])
            manifest=json.loads((checkpoint/'manifest.json').read_text(encoding='utf-8'))
            from .artifacts import sha256
            for name in ['fact-interpretation.json','fact-source-result.json','fact-model-request.json','fact-model-response.json','fact-model-call.json']:
                entries=[a for a in manifest['artifacts'] if a['path']==name]
                if len(entries)!=1 or sha256(checkpoint/name)!=entries[0]['hash']:raise TaskError('FACT_CHECKPOINT_CHANGED','事实解释断点产物改变，不能复用。','Generation',['DEC-004','SYS-005'])
                if name.startswith('fact-model-'):artifacts.json(name,json.loads((checkpoint/name).read_text(encoding='utf-8')))
            interpretation=json.loads((checkpoint/'fact-interpretation.json').read_text(encoding='utf-8'))
            artifacts.json('fact-checkpoint.json',{'reused_from_run':checkpoint.name,'fresh_fact_model_call':False})
        else:
            interpretation=step('FactInterpreter DEC-004/005',lambda:interpret(task,sources,schemas,artifacts))
        artifacts.json('fact-interpretation.json',interpretation)
        decision_input={'trace_id':trace,'evidence':sources['evidence'],'interpretation':interpretation,'policy':task.get('evidence_policy',{})}
        resolution=step('DEC-004',lambda:resolve(decision_input,schemas))
        artifacts.json('decision-evidence.json',resolution['decision_trace']);artifacts.json('evidence-resolution.json',resolution['resolution'])
        boundary=step('DEC-005',lambda:boundaries({**decision_input,'resolution':resolution['resolution']},schemas))
        artifacts.json('decision-fact-boundary.json',boundary['decision_trace']);artifacts.json('fact-boundary.json',boundary['boundaries'])
        sources=project(sources,resolution['resolution'],boundary['boundaries'],interpretation)
        artifacts.json('approved-source-result.json',sources)
        narrative = step('DEC-006–014 narrative preparation',lambda:prepare(task,sources,normalized['context'],schemas,artifacts))
        previous_deck = None
        if checkpoint and (checkpoint/'model-response.json').is_file():
            old = json.loads((checkpoint/('fact-source-result.json' if (checkpoint/'fact-source-result.json').exists() else 'source-result.json')).read_text(encoding='utf-8'))
            identity = lambda result: [(e['evidence_id'], e['source_hash'], e['parser_version']) for e in result['evidence']]
            if identity(old) != identity(sources):
                raise TaskError('CHECKPOINT_SOURCE_CHANGED', '来源或解析版本变化，断点不能复用旧模型响应。', 'Generation', ['SYS-005'])
            response_path = checkpoint/'model-response-effective.json' if (checkpoint/'model-response-effective.json').is_file() else checkpoint/'model-response.json'
            proposal = json.loads(response_path.read_text(encoding='utf-8'))
            schemas.validate('generation-model.schema.json', proposal)
            if len(proposal['slides']) != count:
                raise TaskError('CHECKPOINT_CONSTRAINT_CHANGED', '当前归一化页数与模型断点不符，不能复用。', 'Generation', ['DEC-002','SYS-005'])
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
            proposal, model = step('SYS-005 partial content planner', lambda: plan(task, sources, schemas, artifacts, count,narrative))
        proposal, narrative_result = step('DEC-009/012/014–021 narrative execution',lambda:finalize(proposal,narrative,sources,schemas,artifacts))
        artifacts.json('model-response-effective.json',proposal)
        deck, execution = step('SYS-010/011', lambda: compile_deck(proposal, style, trace, previous_deck))
        artifacts.json('deck-spec.json', deck); artifacts.json('execution-plan.json', execution)
        artifacts.json('layout-selection.json',{'scope':'DEC-030/031/033/034 subset; full nodes incomplete','slides':[{'slide_id':s['slide_id'],**s['layout']} for s in deck['slides']]})
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


def resume(run_id, schemas, store, trace, task_patch=None):
    try:
        if str(UUID(run_id)) != run_id:raise ValueError()
    except ValueError:
        raise TaskError('CHECKPOINT_ID_INVALID', '断点ID必须为标准UUID。', 'Generation', ['SYS-005']) from None
    folder = Path('/runtime/runs')/run_id
    required = ['task.json', 'source-result.json','fact-source-result.json','fact-interpretation.json','fact-model-request.json','fact-model-response.json','fact-model-call.json']
    if not all((folder/name).is_file() for name in required):
        raise TaskError('CHECKPOINT_INCOMPLETE', '没有可恢复的事实解释阶段断点。', 'Generation', ['SYS-005'])
    task = json.loads((folder/'task.json').read_text(encoding='utf-8'))
    if task_patch is not None:
        if not isinstance(task_patch,dict) or set(task_patch)!={'evidence_policy'}:
            raise TaskError('CHECKPOINT_PATCH_UNSUPPORTED','恢复只允许显式更新evidence_policy，不改来源或事实解释。','Generation',['DEC-004','DEC-005'])
        schemas.validate('evidence-policy.schema.json',task_patch['evidence_policy'])
        task={**task,**task_patch}
    return generate(task, schemas, store, trace, folder)
