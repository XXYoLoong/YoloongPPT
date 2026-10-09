"""DEC-001: explicit intent, bounded rules, attachment roles and observable conflict."""
import hashlib
import json
import platform
import re
import shutil
import time
from importlib.metadata import version
from pathlib import Path

from .artifacts import entity, RunArtifacts
from .atomic import AtomicRegistry
from .errors import TaskError
from .schemas import ROOT

POLICIES = {
    'create_from_scratch': 'protect_scratch_scope',
    'create_from_materials': 'preserve_material_facts_and_sources',
    'create_from_reference_style': 'isolate_reference_style_from_content',
    'fill_template': 'preserve_template_structure_and_locks',
    'modify_existing_deck': 'limit_edits_to_requested_targets',
    'reconstruct_from_image': 'preserve_image_evidence_and_uncertainty',
    'beautify_existing_deck': 'preserve_facts_data_and_locked_objects',
    'create_or_replace_single_slide': 'limit_change_to_one_slide',
}
# These rules recognize action phrases only in caller raw_text, never attachment contents.
PATTERNS = {
    'create_from_scratch': r'从零|仅依据主题|从头|\bfrom scratch\b',
    'create_from_materials': r'(?:根据|依据|基于).{0,30}(?:材料|报告|文档|数据|markdown)|\bfrom (?:materials|documents)\b',
    'create_from_reference_style': r'参考.{0,15}(?:风格|样式)|风格参考|\breference style\b',
    'fill_template': r'(?:填充|使用|沿用|放入|套用).{0,25}模板|模板填充|\bfill (?:the )?template\b',
    'modify_existing_deck': r'修改.{0,25}(?:PPT|演示|文案)|\bmodify (?:the )?(?:existing )?deck\b',
    'reconstruct_from_image': r'(?:截图|图片).{0,20}(?:还原|重建)|(?:还原|重建).{0,20}(?:截图|图片)|\breconstruct\b',
    'beautify_existing_deck': r'美化|beautify|视觉重排|整理.{0,25}布局|重排.{0,20}(?:PPT|演示|布局)',
    'create_or_replace_single_slide': r'单页|(?:第\s*[0-9一二三四五六七八九十]+\s*页).{0,15}替换|替换.{0,15}第\s*[0-9一二三四五六七八九十]+\s*页|\bsingle slide\b',
}
ROLE_MODES = {'content': 'create_from_materials', 'style_reference': 'create_from_reference_style',
              'template': 'fill_template', 'reconstruction': 'reconstruct_from_image'}


def runtime_snapshot(schemas):
    """Local observed subset of SYS-002; remote model/Office/API set are not guessed."""
    atomic = AtomicRegistry(schemas).snapshot()
    writer = all(i['health']['available'] for c in atomic['capabilities'] for i in c['implementations'])
    renderer = bool(shutil.which('libreoffice') and shutil.which('pdftoppm'))
    fonts = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').is_file()
    return {'os': platform.system()+'/'+platform.machine(), 'office_version': None,
            'powerpoint_state': 'not_probed_in_container', 'api_sets': [],
            'adapters': atomic, 'models': {'status': 'not_probed_here', 'reason': 'Provider verifies actual models at invocation; credentials omitted.'},
            'fonts': {'Noto Sans CJK SC': fonts}, 'renderers': {'libreoffice': renderer},
            'tools': {'python': platform.python_version(), 'python-pptx': version('python-pptx')},
            'mode_support': {m: {'status': 'Partial' if m in {'create_from_materials', 'create_from_scratch'} else 'Unsupported',
                'available': writer and renderer and fonts if m in {'create_from_materials', 'create_from_scratch'} else False,
                'reason': 'Current native text/table/chart draft path only; provider/source/constraint checks still required.' if m in {'create_from_materials', 'create_from_scratch'} else 'Downstream mode not integrated; original route retained.'}
                for m in POLICIES}, 'provenance': 'actual local probes; partial SYS-002, not complete runtime doctor'}


def decide(document, schemas, trace):
    begin = time.monotonic()
    schemas.validate('route-request.schema.json', document)
    raw = document['raw_request']; request = raw['request']; text = request['raw_text']
    snapshot = document.get('runtime_snapshot') or runtime_snapshot(schemas)
    support = snapshot.get('mode_support', {})
    if set(support) != set(POLICIES) or any(not isinstance(support[m], dict) or type(support[m].get('available')) is not bool or support[m].get('status') not in {'Supported', 'Partial', 'Unsupported', 'Unknown'} for m in POLICIES):
        raise TaskError('RUNTIME_SNAPSHOT_INVALID', '模式能力快照须明确覆盖八种路线和可用状态。', 'DEC-001', ['DEC-001'])
    bindings = raw['attachment_roles']; assets = request['attachments']
    if len(assets) != len(set(assets)) or len({b['asset_id'] for b in bindings}) != len(bindings) or any(b['asset_id'] not in assets for b in bindings):
        raise TaskError('ATTACHMENT_ROLE_INVALID', '附件身份/角色重复或引用不存在。', 'DEC-001', ['DEC-001', 'GOV-007'])
    reasons = {m: [] for m in POLICIES}; evidence = {m: [] for m in POLICIES}
    def signal(mode, why, ref):
        reasons[mode].append(why); evidence[mode].append(ref)
    requested = request['requested_mode']
    if requested is not None:
        if requested not in POLICIES:
            raise TaskError('REQUESTED_MODE_UNKNOWN', '显式模式标识未登记，未猜测替换。', 'DEC-001', ['DEC-001'])
        signal(requested, {'kind': 'explicit_mode', 'reason': 'Caller explicitly selected this operation.'}, 'request.requested_mode')
    negated = []
    for mode, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text, re.I):
            prefix = text[max(0, match.start()-8):match.start()]
            loc = f'raw_text:{match.start()}:{match.end()}'
            if re.search(r'(?:不要|不必|无需|不得|不|do not|don.t)\s*$', prefix, re.I):
                negated.append({'mode': mode, 'location': loc}); continue
            signal(mode, {'kind': 'action_phrase', 'start_offset': match.start(), 'end_offset': match.end(), 'text': match.group()}, loc)
    roles = {b['role'] for b in bindings}
    for binding in bindings:
        if binding['role'] in ROLE_MODES:
            mode = ROLE_MODES[binding['role']]
            signal(mode, {'kind': 'attachment_role', 'asset_id': binding['asset_id'], 'role': binding['role']}, binding['asset_id'])
    active = {m for m in POLICIES if reasons[m]}
    # Content can accompany a specific style/template/edit/reconstruction/single-page operation.
    special = active - {'create_from_scratch', 'create_from_materials'}
    eligible = active - {'create_from_materials'} if special else active
    conflicts = []
    if len(eligible) > 1:conflicts.append('Multiple operation scopes; caller must select the intended mode and protection boundary.')
    if requested is not None and requested not in eligible:conflicts.append('Explicit requested mode conflicts with another operation scope.')
    if requested is not None and any(n['mode'] == requested for n in negated):conflicts.append('Explicit mode is negated in caller instructions.')
    if 'create_from_scratch' in active and 'content' in roles:conflicts.append('Scratch mode conflicts with attachments explicitly bound as factual content.')
    if set(assets) != {b['asset_id'] for b in bindings}:conflicts.append('Attachment role unspecified: content/style/template/existing/reconstruction cannot be guessed.')
    if 'existing_deck' in roles and not special:
        eligible.update({'modify_existing_deck', 'beautify_existing_deck', 'create_or_replace_single_slide'})
        for m in eligible:
            if not reasons[m]:signal(m, {'kind': 'unresolved_existing_deck', 'reason': 'Existing deck supplied without explicit mutation operation.'}, 'attachment_roles')
        conflicts.append('Existing deck supplied without a mutation scope.')
    if not eligible:
        eligible = set(POLICIES);conflicts.append('No explicit operation or recognized action; do not infer intent from source data.')
        for m in POLICIES:signal(m, {'kind': 'unknown_intent', 'reason': 'Clarification required.'}, 'request.raw_text')
    if eligible == {'create_or_replace_single_slide'} and 'single_slide' not in raw:
        if not re.search(r'(?:替换|新增|创建|生成)', text) or not re.search(r'第\s*[0-9一二三四五六七八九十]+\s*页|独立.{0,3}单页', text):
            conflicts.append('Single-slide action and target/standalone destination are not explicit.')
    selected = next(iter(eligible)) if len(eligible) == 1 and not conflicts else None
    candidates = []
    for mode in POLICIES:
        if mode not in active | eligible:continue
        available = support[mode]['available'] and support[mode]['status'] in {'Supported', 'Partial'}
        candidates.append({'node_id': 'DEC-001', 'candidate_id': entity('candidate'), 'value': mode,
            'score': 1.0 if requested == mode else 0.8 if mode in active else 0.0,
            'reasons': reasons[mode] or [{'kind': 'unresolved', 'reason': 'No unique intent'}],
            'evidence_refs': evidence[mode], 'constraints': [{'kind': 'runtime', 'available': available, 'status': support[mode]['status'],
            'reason': support[mode].get('reason', '')}, {'kind': 'protection', 'policy_id': POLICIES[mode]},
            {'kind': 'scope', 'eligible': mode in eligible}]})
    reason = ('User intent selected '+selected+'. Content sources do not override its protection policy.' if selected else ' / '.join(conflicts))
    output = {'route_status': 'routed' if selected else 'needs_clarification', 'mode': selected,
              'routing_reason': reason, 'protection_policy_id': POLICIES[selected] if selected else None,
              'decision_id': 'DEC-001', 'trace': {'candidate_modes': [c['value'] for c in candidates], 'selection_basis': reason,
              'conflict_summary': ' / '.join(conflicts), 'trace_id': trace, 'negated_signals': negated,
              'executable': bool(selected and support[selected]['available'] and support[selected]['status'] in {'Supported', 'Partial'}),
              'fallback': 'No alternate mode substitution; clarify scope or expose missing implementation.'}}
    schemas.validate('task-route.schema.json', output)
    decision = {'trace_id': trace, 'node_id': 'DEC-001', 'input': {'raw_request': raw, 'runtime_snapshot': snapshot},
                'candidates': candidates, 'selected': next((c['candidate_id'] for c in candidates if c['value'] == selected), None),
                'rules': {'version': 'DEC-001-rules-1', 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'mechanism': 'Explicit mode, bounded action phrases and typed attachment roles; no highest-score tie breaking.',
                'precedence': 'specific operation may consume content; incompatible scopes require clarification',
                'model': None, 'snapshot_origin': 'caller_provided' if 'runtime_snapshot' in document else 'actual_runtime'},
                'output': output, 'duration': round(time.monotonic()-begin, 6),
                'error': {'code': 'MODE_CLARIFICATION_REQUIRED', 'reasons': conflicts} if conflicts else None}
    schemas.validate('route-trace.schema.json', decision)
    return {'ok': True, 'trace_id': trace, 'operation': 'route', 'route': output, 'decision_trace': decision}


def route_task(task, schemas, trace):
    raw = task.get('raw_request')
    if raw is None:
        # Legacy TaskSpec route is an explicit assertion, not invented user prose.
        raw = {'request': {'raw_text': '', 'attachments': [], 'requested_mode': task['route']['mode'], 'requested_outputs': task['output'].get('formats', [])}, 'attachment_roles': []}
    result = decide({'raw_request': raw}, schemas, trace)
    if result['route']['route_status'] != 'routed':return result
    if task['route']['route_status'] == 'routed' and task['route']['mode'] != result['route']['mode']:
        reason = 'TaskSpec route assertion conflicts with the operation selected from RawTaskRequest; clarify before execution.'
        result['route'].update(route_status='needs_clarification', mode=None, protection_policy_id=None, routing_reason=reason)
        result['route']['trace'].update(conflict_summary=reason, selection_basis=reason, executable=False)
        result['decision_trace'].update(selected=None, error={'code':'TASK_ROUTE_CONFLICT','reason':reason})
        schemas.validate('route-trace.schema.json', result['decision_trace'])
    result['decision_trace']['input']['input_origin'] = 'raw_task_request' if 'raw_request' in task else 'explicit_task_spec_route_assertion'
    return result


def run_route(document, schemas, trace):
    """Standalone node execution stores the same trace consumed by generation."""
    artifacts = RunArtifacts()
    try:
        result = decide(document, schemas, trace)
        artifacts.json('decision-route.json', result['decision_trace'])
        result.update(run_id=artifacts.run_id, artifact_root=str(artifacts.path))
        artifacts.json('result.json', result)
        artifacts.json('manifest.json', {'run_id': artifacts.run_id, 'artifacts': artifacts.manifest()})
        return result
    except TaskError as error:
        error.details.append({'run_id': artifacts.run_id})
        artifacts.json('failure.json', error.result(trace))
        raise
