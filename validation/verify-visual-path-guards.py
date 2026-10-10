"""Direct SEC-001 guards, not a rerun of the earlier 50 visual checks."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from yoloongppt.asset_resolver import allowed_path, resolve
from yoloongppt.errors import TaskError
from yoloongppt.schemas import SchemaRegistry
from yoloongppt.template_registry import register

output = Path('/runtime/visual-path-validation')
fixture = output / ('fixture-' + str(uuid4()))
allowed = fixture / 'allowed'; outside = fixture / 'outside'
allowed.mkdir(parents=True); outside.mkdir(parents=True)
public = allowed / 'public.png'; public.write_bytes(b'guard fixture; not a secret')
escaped = outside / 'outside.png'; escaped.write_bytes(b'guard fixture; not a secret')
checks = []


def reject(name, function, expected):
    # Ensure credentials never reach the byte-reading operation. The fixtures
    # contain ordinary test bytes, not actual machine credentials.
    with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected protected file read')):
        try: function()
        except TaskError as error:
            assert error.code == expected, (name, error.code)
            assert 'SEC-001' in error.requirement_ids, name
            checks.append({'id': name, 'passed': True, 'error_code': error.code, 'read_bytes_calls': 0})
        else: raise AssertionError(name + ' accepted')


for directory in ('secrets', '.git', '.ssh', 'SeCrEtS'):
    file = allowed / directory / 'guard.bin';file.parent.mkdir(exist_ok=True);file.write_bytes(b'guard fixture')
    reject(directory + '_asset_path', lambda file=file: allowed_path(file, [allowed]), 'ASSET_SENSITIVE_PATH_FORBIDDEN')
    reject(directory + '_template_register', lambda file=file: register(file, allowed_roots=[allowed]), 'ASSET_SENSITIVE_PATH_FORBIDDEN')
for name in ('.env', '.env.local', '.ENV.production'):
    file = allowed / name;file.write_bytes(b'guard fixture')
    reject(name + '_asset_path', lambda file=file: allowed_path(file, [allowed]), 'ASSET_SENSITIVE_PATH_FORBIDDEN')
    reject(name + '_template_register', lambda file=file: register(file, allowed_roots=[allowed]), 'ASSET_SENSITIVE_PATH_FORBIDDEN')
secret_alias = allowed / 'public-alias.png';secret_alias.symlink_to(allowed/'secrets/guard.bin')
reject('symlink_to_secret_asset', lambda: allowed_path(secret_alias, [allowed]), 'ASSET_SENSITIVE_PATH_FORBIDDEN')
reject('symlink_to_secret_template', lambda: register(secret_alias, allowed_roots=[allowed]), 'ASSET_SENSITIVE_PATH_FORBIDDEN')
escape_alias = allowed / 'outside-alias.png';escape_alias.symlink_to(escaped)
reject('symlink_escape_asset', lambda: allowed_path(escape_alias, [allowed]), 'ASSET_PATH_FORBIDDEN')
reject('symlink_escape_template', lambda: register(escape_alias, allowed_roots=[allowed]), 'ASSET_PATH_FORBIDDEN')
reject('lexical_traversal_outside_root', lambda: allowed_path(allowed/'../outside/outside.png', [allowed]), 'ASSET_PATH_FORBIDDEN')
request={'asset_id':'asset_'+str(uuid4()), 'source_type':'local','path':str(allowed/'.env'),'license':'unknown','usage_status':'authorized'}
reject('actual_resolver_consumer_denies_env', lambda: resolve({'requests':[request]},allowed_roots=[allowed]), 'ASSET_SENSITIVE_PATH_FORBIDDEN')
assert allowed_path(public,[allowed]) == public.resolve()
checks.append({'id':'ordinary_allowed_path_retained','passed':True})
ordinary_alias=allowed/'ordinary-alias.png';ordinary_alias.symlink_to(public)
assert allowed_path(ordinary_alias,[allowed])==public.resolve()
checks.append({'id':'ordinary_in_root_symlink_retained','passed':True})
schemas = SchemaRegistry()
old = json.loads(Path('/workspace/validation/visual-runtime.json').read_text('utf-8'))
schema_names = sorted(old['schema_hashes'])
assert all(old['schema_hashes'][name] == schemas.versions[name] for name in schema_names)
checks.append({'id':'all_eight_existing_schema_hashes_unchanged','passed':True})
report={'passed':len(checks),'checks':checks,
        'source_hashes':{name:hashlib.sha256(Path('/workspace/src/yoloongppt',name).read_bytes()).hexdigest() for name in ('visual.py','asset_resolver.py','template_registry.py')},
        'schema_hashes':{name:schemas.versions[name] for name in schema_names},
        'prior_evidence':{'path':'validation/visual-runtime.json','passed':old['passed'],'source_hashes':old['source_hashes'],
            'scope':'Historical 50 visual checks preserved; only asset_resolver guard source changed. This report does not claim all 50 reran.'},
        'actual_scope':'Direct SEC-001 sensitive spelling/resolved targets, real symlinks and asset/template callers; no secrets read and no model calls.'}
path=output/'visual-path-guards.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(checks),'report':str(path)},ensure_ascii=False))
