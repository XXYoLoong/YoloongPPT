"""SYS-007: separate product implementation health from research object status."""
import copy
import hashlib
import json
import platform
from importlib.metadata import version

from .schemas import ROOT


class CapabilityRegistry:
    def __init__(self, schemas):
        self.schemas = schemas
        self.catalog = json.loads((ROOT / 'contracts/capability-status.catalog.json').read_text(encoding='utf-8'))
        self.schemas.validate('capability-status.schema.json', self.catalog)

    def list(self, trace):
        core = []
        for id, impl in [('SYS-001', 'yoloongppt.tasks.validate_task'),
                         ('SYS-006', 'yoloongppt.schemas.SchemaRegistry'),
                         ('SYS-007', 'yoloongppt.capabilities.CapabilityRegistry')]:
            core.append({'capability_id': id, 'implementation': impl, 'backend': 'python-core',
                         'platform': platform.system() + '/' + platform.machine(),
                         'dependencies': {'python': platform.python_version(), 'jsonschema': version('jsonschema')},
                         'version': hashlib.sha256((ROOT / 'src/yoloongppt' / {
                             'SYS-001': 'tasks.py', 'SYS-006': 'schemas.py', 'SYS-007': 'capabilities.py'}[id]).read_bytes()).hexdigest(),
                         'status': 'Partial', 'priority': 'P0',
                         'health': {'available': True, 'checked': 'runtime schema/catalog loaded'},
                         'evidence': ['ARCHITECTURE.md', 'validation/runtime-core.json'],
                         'reason': 'Component entry available; required generation/QA/revision E2E not yet executed.'})
        return {'ok': True, 'trace_id': trace, 'operation': 'capabilities', 'core': core,
                'ppt_catalog': copy.deepcopy(self.catalog),
                'boundary': 'Historical draft PPT statuses do not certify the selected writer or runtime adapters. Health is separate from object support.'}
