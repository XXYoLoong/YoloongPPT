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
                         ('SYS-003', 'yoloongppt.sources.inspect_sources'),
                         ('SYS-004', 'yoloongppt.evidence.EvidenceStore'),
                         ('SYS-005', 'yoloongppt.planning.plan'),
                         ('SYS-006', 'yoloongppt.schemas.SchemaRegistry'),
                         ('SYS-007', 'yoloongppt.capabilities.CapabilityRegistry'),
                         ('SYS-010', 'yoloongppt.planning.compile_deck'),
                         ('SYS-011', 'yoloongppt.planning.compile_deck'),
                         ('SYS-012', 'yoloongppt.writer.execute'),
                         ('SYS-013', 'yoloongppt.writer.execute'),
                         ('SYS-014', 'yoloongppt.rendering.render'),
                         ('SYS-015', 'yoloongppt.quality.check'),
                         ('SYS-016', 'yoloongppt.revision.revise'),
                         ('SYS-017', 'yoloongppt.artifacts.RunArtifacts')]:
            core.append({'capability_id': id, 'implementation': impl, 'backend': 'python-core',
                         'platform': platform.system() + '/' + platform.machine(),
                         'dependencies': {'python': platform.python_version(), 'jsonschema': version('jsonschema')},
                         'version': hashlib.sha256((ROOT / 'src/yoloongppt' / {
                             'SYS-001': 'tasks.py', 'SYS-003': 'sources.py', 'SYS-004': 'evidence.py',
                             'SYS-005': 'planning.py', 'SYS-010': 'planning.py', 'SYS-011': 'planning.py',
                             'SYS-012': 'writer.py', 'SYS-013': 'writer.py', 'SYS-014': 'rendering.py',
                             'SYS-015': 'quality.py', 'SYS-016': 'revision.py', 'SYS-017': 'artifacts.py',
                             'SYS-006': 'schemas.py', 'SYS-007': 'capabilities.py'}[id]).read_bytes()).hexdigest(),
                         'status': 'Partial', 'priority': 'P0',
                         'health': {'available': True, 'checked': 'runtime schema/catalog loaded'},
                         'evidence': ['ARCHITECTURE.md', 'validation/source-runtime.json' if id in {'SYS-003', 'SYS-004'} else 'validation/runtime-core.json' if id in {'SYS-001','SYS-006','SYS-007'} else 'validation/generation-runtime.json'],
                         'reason': 'Component entry available; required generation/QA/revision E2E not yet executed.'})
        return {'ok': True, 'trace_id': trace, 'operation': 'capabilities', 'core': core,
                'ppt_catalog': copy.deepcopy(self.catalog),
                'boundary': 'Historical draft PPT statuses do not certify the selected writer or runtime adapters. Health is separate from object support.'}
