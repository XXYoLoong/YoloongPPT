"""SYS-006: offline, versioned JSON Schema registry; no automatic HTTP refs."""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

from .errors import TaskError

ROOT = Path(os.environ.get('YOLOONGPPT_ROOT', '/workspace'))
SCHEMA_BASE = 'https://yoloongppt.local/contracts/'


class SchemaRegistry:
    def __init__(self, folder=None):
        self.folder = Path(folder) if folder else ROOT / 'contracts'
        self.documents = {}
        self.versions = {}
        registry = Registry()  # Unknown URI raises, never fetched over the network.
        for path in sorted(self.folder.glob('*.schema.json')):
            raw = path.read_bytes()
            schema = json.loads(raw)
            Draft202012Validator.check_schema(schema)
            self.documents[path.name] = schema
            self.versions[path.name] = hashlib.sha256(raw).hexdigest()
            uri = urljoin(SCHEMA_BASE, path.name)
            resource = Resource.from_contents(schema)
            registry = registry.with_resource(uri, resource).with_resource(path.as_uri(), resource)
            if '$id' in schema:
                registry = registry.with_resource(schema['$id'], resource)
        self.registry = registry

    def validate(self, name, document):
        if name not in self.documents:
            raise TaskError('SCHEMA_NOT_REGISTERED', '未登记该Schema。', 'SchemaRegistry', ['SYS-006'])
        schema = self.documents[name]
        # Establish an absolute base for relative references without editing contract files.
        schema = {**schema, '$id': schema.get('$id', urljoin(SCHEMA_BASE, name))}
        try:
            errors = list(Draft202012Validator(schema, registry=self.registry).iter_errors(document))
        except Unresolvable:
            raise TaskError('SCHEMA_REFERENCE_UNRESOLVED', 'Schema引用未登记；禁止网络获取。',
                            'SchemaRegistry', ['SYS-006'], status=500) from None
        if errors:
            details = []
            for error in errors:
                pointer = '/' + '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in error.absolute_path)
                details.append({'pointer': pointer, 'keyword': error.validator})
            raise TaskError('TASK_SCHEMA_INVALID', '输入不符合Schema；字段路径见details。',
                            'SchemaRegistry', ['SYS-001', 'SYS-006'], details)
        return {'schema': name, 'sha256': self.versions[name]}

    def list(self):
        return [{'name': name, 'sha256': version} for name, version in self.versions.items()]
