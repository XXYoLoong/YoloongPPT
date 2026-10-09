"""Current SYS core component checks in Docker; never claims generation E2E."""
import copy
import hashlib
import json
import platform
from importlib.metadata import version
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from yoloongppt.errors import TaskError
from yoloongppt.schemas import ROOT, SchemaRegistry

BASE = 'http://127.0.0.1:8000'
cases = []


def call(path, body=None):
    data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode('utf-8'))
    request = urllib.request.Request(BASE + path, data=data, headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    result = json.loads(response.read())
    assert response.headers['X-Trace-Id'] == result['trace_id']
    return response.status, result


def record(name, condition, observation):
    assert condition, name
    cases.append({'id': name, 'passed': True, 'observed': observation})


routes = json.loads((ROOT / 'contracts/task-route.fixtures.json').read_text(encoding='utf-8'))['cases']
task = {'task_id': 'task_8c2076ae-f9ea-4c81-a341-c005fa4d50ef',
        'route': routes[0]['expected_task_route'],
        'sources': [{'source_id': 'source_3c2076ae-f9ea-4c81-a341-c005fa4d50ef', 'kind': 'prompt', 'content': '中文任务校验；不冒充生成验收。'}],
        'constraints': {'hard': [], 'soft': [], 'defaults': [], 'conflicts': []},
        'style': None, 'template_ref': None, 'output': {'formats': ['pptx']}, 'providers': {}, 'runtime_preferences': {}}
(Path('/runtime') / 'core-task.json').write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
deadline = time.monotonic() + 30
while True:
    try:
        call('/health')
        break
    except urllib.error.URLError:
        if time.monotonic() >= deadline:
            raise
        time.sleep(1)
status, result = call('/health')
record('health', status == 200 and result['ok'] and result['generation_ready'] is False, result)
status, normal = call('/validate', task)
record('HTTP_TaskSpec_valid', status == 200 and normal['ok'] and normal['task_id'] == task['task_id'], normal)
cli = subprocess.run([sys.executable, '-m', 'yoloongppt', 'validate', '/runtime/core-task.json'], capture_output=True, text=True, encoding='utf-8')
cli_result = json.loads(cli.stdout)
record('CLI_API_shared_core', cli.returncode == 0 and cli_result['task_sha256'] == normal['task_sha256'],
       {'task_id_preserved': True, 'same_hash': True, 'input_chinese': True})
for route in routes[:8]:
    candidate = copy.deepcopy(task)
    candidate['route'] = route['expected_task_route']
    status, result = call('/validate', candidate)
    record('pre_routed_' + candidate['route']['mode'], status == 200 and result['mode'] == candidate['route']['mode'],
           'Pre-routed shape validated only; DEC-001 routing algorithm not executed.')
for name, mutation, code in [
    ('missing_route', lambda d: d.pop('route'), 'TASK_SCHEMA_INVALID'),
    ('wrong_protection_policy', lambda d: d['route'].update(protection_policy_id='limit_edits_to_requested_targets'), 'TASK_SCHEMA_INVALID'),
    ('duplicate_source_identity', lambda d: d['sources'].append(copy.deepcopy(d['sources'][0])), 'SOURCE_ID_DUPLICATE'),
    ('provider_literal_secret', lambda d: d['providers'].update(text={'provider':'probe','model':'probe','api_key':'NONSECRET_SENTINEL'}), 'TASK_SCHEMA_INVALID')]:
    candidate = copy.deepcopy(task); mutation(candidate)
    status, result = call('/validate', candidate)
    record(name, status == 422 and result['error']['code'] == code and 'NONSECRET_SENTINEL' not in json.dumps(result), result)
candidate = copy.deepcopy(task)
candidate['providers'] = {'text': {'provider': 'probe', 'model': 'probe', 'parameters': {'token': 'NONSECRET_SENTINEL'}}}
status, result = call('/validate', candidate)
record('nested_provider_secret', status == 422 and result['error']['code'] == 'PROVIDER_CREDENTIAL_LITERAL'
       and 'NONSECRET_SENTINEL' not in json.dumps(result), result)
for name, body in [('duplicate_JSON_key', b'{"task_id":1,"task_id":2}'), ('NaN', b'{"value":NaN}'), ('non_UTF8', b'\xff'), ('bad_JSON', b'{')]:
    status, result = call('/validate', body)
    record(name, status == 400 and result['error']['code'] == 'INPUT_JSON_INVALID', result)
status, result = call('/validate', b' ' * (4 * 1024 * 1024 + 1))
record('HTTP_body_limit', status == 413 and result['error']['code'] == 'REQUEST_TOO_LARGE', result)
status, result = call('/not-implemented')
record('undefined_API_route', status == 404 and result['ok'] is False, result)
cli = subprocess.run([sys.executable, '-m', 'yoloongppt', 'generate'], capture_output=True, text=True, encoding='utf-8')
result = json.loads(cli.stdout)
record('undefined_CLI_command', cli.returncode != 0 and result['error']['code'] == 'CLI_ARGUMENT_INVALID', result)
status, cap = call('/capabilities')
catalog = json.loads((ROOT / 'contracts/capability-status.catalog.json').read_text(encoding='utf-8'))
record('capability_registration', status == 200 and {c['capability_id'] for c in cap['core']} == {'SYS-001','SYS-003','SYS-004','SYS-006','SYS-007'} and cap['ppt_catalog'] == catalog,
       {'core_entries': 5, 'ppt_entries': len(catalog['capabilities']), 'backends': len(catalog['backend_versions']), 'PPT_status_unchanged': True})
schemas = SchemaRegistry()
schemas.documents['blocked.schema.json'] = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$ref': 'https://blocked.invalid/never-fetch.json'}
try:
    schemas.validate('blocked.schema.json', {})
except TaskError as error:
    record('offline_reference_only', error.code == 'SCHEMA_REFERENCE_UNRESOLVED', error.code)
else:
    raise AssertionError('remote schema unexpectedly resolved')
status, result = call('/schemas')
record('schema_hash_registry', status == 200 and len(result['schemas']) == len(schemas.documents)-1 and
       all(len(s['sha256']) == 64 for s in result['schemas']), {'schemas': len(result['schemas'])})
report = {'requirement_ids': ['SYS-001', 'SYS-006', 'SYS-007', 'SYS-019', 'SYS-020'],
          'passed': True, 'cases': cases, 'runtime': {'python': platform.python_version(), 'platform': platform.platform()},
          'task_schema_sha256': hashlib.sha256((ROOT / 'contracts/task-spec.schema.json').read_bytes()).hexdigest(),
          'scope': 'Docker core component and real CLI/HTTP checks; no model, generation, render, QA, revision or AC E2E acceptance.',
          'status': 'All five requirements/tasks remain in progress until their original E2E acceptance is satisfied.'}
dependencies = json.loads((ROOT / 'runtime/dependencies.json').read_text(encoding='utf-8'))
assert platform.python_version() == dependencies['python']
actual = {package['name']: version(package['name']) for package in dependencies['packages']}
assert all(actual[package['name']] == package['version'] for package in dependencies['packages'])
report['installed_versions'] = actual
paths = list((ROOT / 'src/yoloongppt').glob('*.py')) + [ROOT / name for name in [
    'contracts/task-spec.schema.json', 'contracts/capability-status.catalog.json',
    'requirements.lock', 'runtime/dependencies.json', 'Dockerfile.app', 'compose.yaml']]
report['consumed_files'] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
Path('/runtime/runtime-core.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'passed': True, 'cases': len(cases), 'python': platform.python_version(), 'scope': report['scope']}, ensure_ascii=False))
