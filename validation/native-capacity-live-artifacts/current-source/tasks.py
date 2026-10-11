"""SYS-001: preserve input and stable IDs, validate only; never invent a route."""
import hashlib
import json

from .errors import TaskError


def validate_task(document, schemas, trace):
    version = schemas.validate('task-spec.schema.json', document)
    def check_credentials(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower().replace('-', '_') in {'api_key', 'apikey', 'secret', 'password', 'token', 'access_token', 'authorization'}:
                    raise TaskError('PROVIDER_CREDENTIAL_LITERAL', '供应商凭据只允许引用环境变量名。',
                                    'TaskSpec', ['SYS-001'], [{'pointer': '/providers'}])
                check_credentials(item)
        elif isinstance(value, list):
            for item in value:
                check_credentials(item)
    check_credentials(document['providers'])
    ids = [source['source_id'] for source in document['sources']]
    if len(ids) != len(set(ids)):
        raise TaskError('SOURCE_ID_DUPLICATE', '不同来源不能复用同一source_id。',
                        'TaskSpec', ['SYS-001', 'GOV-007'], [{'pointer': '/sources'}])
    # No request body/credential values are written to logs. Return metadata only.
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'ok': True, 'trace_id': trace, 'task_id': document['task_id'],
            'operation': 'validate_task', 'validation_scope': 'schema and identity only; not execution/QA/E2E',
            'task_sha256': hashlib.sha256(canonical).hexdigest(), 'schema_version': version,
            'mode': document['route']['mode'], 'source_count': len(document['sources']),
            'trace': [{'component': 'TaskSpec', 'requirement_id': 'SYS-001', 'status': 'validated'},
                      {'component': 'SchemaRegistry', 'requirement_id': 'SYS-006', 'status': 'validated'}]}
