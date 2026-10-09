"""RES-032/033 minimal provenance/decision validation, without rerunning generators."""
import ast
import collections
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECTS = {'P01', 'P02', 'P03', 'P04', 'P05'}
METHODS = {'直接复用', '抽象复用', '仅参考', '不采用'}


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(registry, fixtures, manifest):
    sources = manifest['source_files']
    assert registry['requirement_id'] == 'RES-032'
    assert fixtures['requirement_id'] == 'RES-033'
    assert set(registry['methods']) == METHODS
    assert set(registry['projects']) == PROJECTS
    assert set(m['project'] for m in registry['modules']) == PROJECTS
    assert set(a['project'] for a in fixtures['assets']) == PROJECTS
    assert set(a['kind'] for a in fixtures['assets']) == {
        'PPTX', 'templates', 'screenshots', 'schemas', 'golden cases', 'QA cases'}
    assert fixtures['coverage_by_project'] == dict(collections.Counter(a['project'] for a in fixtures['assets']))
    assert {'P02', 'P03', 'P04'} <= set(fixtures['explicit_gaps'])
    assert manifest['cross_matrix_sha256'] == sha(ROOT / 'research/cross-project/CrossProjectMatrix.json')
    assert manifest['cross_validation_sha256'] == sha(ROOT / 'research/cross-project/validation.json')
    for key, entry in sources.items():
        path = Path(entry['local_path'])
        assert path.drive.upper() == 'F:', (key, 'disk')
        assert path.is_file() and sha(path) == entry['sha256'], (key, 'hash')
        assert path.stat().st_size == entry['bytes'], (key, 'size')
        assert entry['project'] in PROJECTS
        if entry['origin'] == 'fixed upstream':
            assert entry['commit'] == registry['projects'][entry['project']]['fixed_commit']
            assert '/blob/' + entry['commit'] + '/' in entry['source_url']
        else:
            assert entry['origin'] == 'project research artifact'
            assert entry['producer'] and entry['rights_boundary']
            assert entry['source_url'] is None
    modules = {m['id']: m for m in registry['modules']}
    assert len(modules) == len(registry['modules'])
    direct = []
    for module in modules.values():
        for field in ['module', 'source_files', 'license_files', 'license_observed',
                      'obligations', 'consumer', 'reason', 'limits', 'copy_permission',
                      'dependencies', 'implementation_state', 'unknown_rights']:
            assert module[field], (module['id'], field)
        assert module['method'] in METHODS
        assert module['implementation_state'] == 'registry decision only; no source imported into product'
        for key in module['source_files'] + module['license_files']:
            assert key in sources and sources[key]['project'] == module['project']
        if module['project'] == 'P05':
            assert module['method'] in {'仅参考', '不采用'}
            assert 'Unresolved' in module['license_observed']
            assert 'conflict' in module['license_observed'] or 'vs' in module['license_observed']
        if module['method'] == '直接复用':
            direct.append(module['id'])
            assert module['project'] == 'P01' and len(module['source_files']) == 1
            assert set(module['license_files']) == {'P01:LICENSE', 'P01:skills/ppt-master/LICENSE'}
            for key in module['license_files']:
                notice = Path(sources[key]['local_path']).read_text(encoding='utf-8')
                assert 'MIT License' in notice and 'Copyright' in notice
                assert 'permission notice' in notice
            tree = ast.parse(Path(sources[module['source_files'][0]]['local_path']).read_text(encoding='utf-8'))
            imports = sorted({a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
                              for a in n.names} | {n.module.split('.')[0] for n in ast.walk(tree)
                                                  if isinstance(n, ast.ImportFrom) and n.module})
            assert imports == module['imports']
            assert all(i in sys.stdlib_module_names or i == '__future__' for i in imports)
    assert sorted(direct) == ['R01', 'R02']
    for asset in fixtures['assets']:
        assert asset['source_file'] in sources
        assert sources[asset['source_file']]['project'] == asset['project']
        assert asset['related_reuse_ids'] and all(key in modules for key in asset['related_reuse_ids'])
        assert asset['license_files'] and all(key in sources for key in asset['license_files'])
        assert asset['license_and_rights'] and asset['test_consumer']
        assert asset['reuse_method'] in {'仅参考', '不采用'}
        assert asset['copy_state'] == 'not copied by this task; reference/recreate only'
        assert asset['execution_boundary']
        if asset['execution_evidence']:
            assert (ROOT / asset['execution_evidence']).is_file()
        if asset['project'] == 'P03' or not asset['execution_evidence']:
            assert asset['execution_status'] == 'source located; not executed'
        else:
            assert asset['execution_status'] == 'existing selected research observation; not whole-suite/product acceptance'
    for boundary in registry['third_party_boundaries']:
        assert boundary['source_file'] in sources and boundary['declaration'] and boundary['decision']
        assert boundary['decision'] != 'licensed under root MIT; copied'
    assert any(b['kind'] == 'icons' and 'CC BY4.0' in b['declaration'] for b in registry['third_party_boundaries'])
    # Conflicting metadata is observed directly, not inferred from a repository summary.
    p05 = lambda path: Path(sources['P05:' + path]['local_path']).read_text(encoding='utf-8')
    assert 'GNU AFFERO GENERAL PUBLIC LICENSE' in p05('LICENSE')
    assert json.loads(p05('package.json'))['license'] == 'AGPL-3.0-only'
    assert 'Apache-2.0' in p05('pyproject.toml') and 'Apache-2.0' in p05('package-lock.json')
    assert 'Apache License' in Path(sources['P03:LICENSE']['local_path']).read_text(encoding='utf-8')
    assert sources['P03:NOTICE']['bytes'] > 0
    return {'modules': len(modules), 'assets': len(fixtures['assets']), 'source_files': len(sources),
            'direct_eligible_files': direct, 'fixture_projects': fixtures['coverage_by_project']}


def main():
    original = [read('ReuseDecisionRegistry.json'), read('ResearchFixtureIndex.json'), read('source-manifest.json')]
    observed = check(*original)
    cases = [{'id': 'normal', 'passed': True, 'observed': observed}]

    def rejects(name, mutate):
        data = copy.deepcopy(original)
        mutate(*data)
        try:
            check(*data)
        except (AssertionError, KeyError):
            cases.append({'id': name, 'passed': True, 'observed': 'invalid in-memory copy rejected'})
        else:
            raise AssertionError(name + ' unexpectedly accepted')

    rejects('missing_license', lambda r, f, s: r['modules'][0].update(license_files=[]))
    rejects('unknown_source', lambda r, f, s: f['assets'][0].update(source_file='unknown'))
    rejects('source_hash_drift', lambda r, f, s: next(iter(s['source_files'].values())).update(sha256='0' * 64))
    rejects('P05_direct_copy', lambda r, f, s: r['modules'][-1].update(method='直接复用'))
    rejects('P05_conflict_hidden', lambda r, f, s: r['modules'][-1].update(license_observed='MIT'))
    rejects('icons_root_license_overclaim', lambda r, f, s: r['third_party_boundaries'][0].update(decision='licensed under root MIT; copied'))
    rejects('P03_execution_overclaim', lambda r, f, s: next(a for a in f['assets'] if a['project'] == 'P03').update(execution_status='executed passed'))
    rejects('project_fixture_missing', lambda r, f, s: f.update(assets=[a for a in f['assets'] if a['project'] != 'P04']))
    rejects('uncleared_artwork_copied', lambda r, f, s: next(a for a in f['assets'] if a['id'] == 'FIX-021').update(copy_state='copied into product'))
    ns = {}
    exec((ROOT / 'research/P05/baseline-rows.py').read_text(encoding='utf-8').split('data,_=')[0], ns)
    baseline, _ = ns['read'](ROOT / 'AI_PPT_完整需求与任务矩阵_V0.3.xlsx')
    assert baseline['需求主表']['A37'][1] == 'RES-031' and baseline['需求主表']['N37'][1] == '已完成'
    for row, req, task in [(38, 'RES-032', 66), (39, 'RES-033', 67)]:
        assert baseline['需求主表'][f'A{row}'][1] == req
        assert baseline['需求主表'][f'I{row}'][1] == 'RES-031'
        assert baseline['可执行任务'][f'A{task}'][1] == 'TASK-' + req
    report = {'requirement_ids': ['RES-032', 'RES-033'], 'task_ids': ['TASK-RES-032', 'TASK-RES-033'],
              'passed': True, 'cases': cases, 'observed': observed, 'explicit_gaps': original[1]['explicit_gaps'],
              'boundary': 'Provenance and reuse registration only. No product source/assets imported, model calls, regeneration, full upstream test execution or AC acceptance.',
              'runtime_observation': 'Host stdlib used to inspect metadata, not product runtime selection.'}
    (HERE / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'cases': len(cases), **observed}, ensure_ascii=False))


if __name__ == '__main__':
    main()
