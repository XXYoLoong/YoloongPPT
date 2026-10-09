"""Run the pending RES-P01-05 checks in a pinned, offline research container."""
import hashlib
import io
import json
import os
import platform
import sys
import unittest
from pathlib import Path

source = Path(os.environ.get('P01_SOURCE_ROOT', '/source'))
evidence = Path(os.environ.get('P01_EVIDENCE_ROOT', '/evidence'))
scripts = source / 'skills/ppt-master/scripts'
sys.path.insert(0, str(scripts))
selected = [
    'tests.test_edit_native_batch_b.EditNativeBatchBTests.test_b2_inherited_deletion_and_edit_fail',
    'tests.test_edit_native_batch_b.EditNativeBatchBTests.test_b3_proxy_ancestor_change_is_rejected',
    'tests.test_edit_native_batch_b.EditNativeBatchBTests.test_b5_page_plan_resets_custom_show_selection',
    'tests.test_edit_native_batch_b.EditNativeBatchBTests.test_b7_diagram_is_atomic_proxy',
    'tests.test_edit_native_batch_b.EditNativeBatchBTests.test_b7_ole_and_unknown_graphic_frames_are_proxies',
    'tests.test_edit_native_batch_c.EditNativeBatchCTests.test_c2_roundtrip_quality_receipt_tracks_authoring_and_page_plan',
    'tests.test_native_chart_table_parity',
]

class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed_ids = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed_ids.append(test.id())

stream = io.StringIO()
suite = unittest.TestLoader().loadTestsFromNames(selected)
result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult).run(suite)
map_data = json.loads((evidence / 'project_capability_map.json').read_text(encoding='utf-8'))
assert map_data['source']['commit'] == '2d72da616cf9fa40d4dcaf59fd4c980ecf534b7d'
assert len({r['id'] for r in map_data['capabilities']}) == 30
normal = evidence / 'projects/p01_hello_world_20261007/exports/p01-hello-world.pptx'
assert hashlib.sha256(normal.read_bytes()).hexdigest() == 'c39b6b596b6c6df0c69d8bdc2886eac5d1339cab5f148833951f1370095acd25'
source_hashes = {}
for name in ['test_edit_native_batch_b.py', 'test_edit_native_batch_c.py', 'test_native_chart_table_parity.py']:
    source_hashes['skills/ppt-master/scripts/tests/' + name] = hashlib.sha256((scripts / 'tests' / name).read_bytes()).hexdigest()
report = {
    'requirement_id': 'RES-P01-05',
    'source_commit': map_data['source']['commit'],
    'source_test_sha256': source_hashes,
    'environment': {'python_observed': platform.python_version(), 'network': 'Docker --network none', 'runtime_scope': 'candidate research only, not product selection'},
    'selected': selected,
    'tests_run': result.testsRun,
    'passed_ids': result.passed_ids,
    'failures': [{'id': t.id(), 'detail': detail} for t, detail in result.failures],
    'errors': [{'id': t.id(), 'detail': detail} for t, detail in result.errors],
    'skipped': [{'id': t.id(), 'reason': reason} for t, reason in result.skipped],
    'successful': result.wasSuccessful() and not result.skipped,
    'normal_pptx_sha256_reused': hashlib.sha256(normal.read_bytes()).hexdigest(),
    'scope': 'Selected upstream boundaries and negative cases; not full upstream suite, real model, Office or product AC acceptance',
}
(evidence / 'validation/p01-boundary-tests.txt').write_text(stream.getvalue(), encoding='utf-8')
(evidence / 'validation/p01-boundary-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(stream.getvalue())
print(json.dumps({'tests_run': result.testsRun, 'successful': report['successful'], 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)}))
sys.exit(0 if report['successful'] else 1)
