"""SYS-007: stable definitions selected and checked before any native write."""
import copy
import hashlib
import json
import math
import platform
from importlib.metadata import version

from jsonschema import Draft202012Validator

from .errors import TaskError
from .schemas import ROOT


class AtomicRegistry:
    def __init__(self, schemas):
        self.catalog = json.loads((ROOT/'contracts/atomic-registry.catalog.json').read_text(encoding='utf-8'))
        schemas.validate('atomic-registry.schema.json', self.catalog)
        self.by_name = {}
        seen = set()
        for item in self.catalog['capabilities']:
            ids = [item['capability_id'], *[i['implementation_id'] for i in item['implementations']]]
            if item['name'] in self.by_name or len(ids) != len(set(ids)) or set(ids) & seen:
                raise TaskError('CAPABILITY_ID_DUPLICATE', '能力名称或实体ID重复。', 'CapabilityRegistry', ['SYS-007'], status=500)
            seen.update(ids)
            for contract in ['input_schema', 'output_schema']:
                Draft202012Validator.check_schema(item[contract])
            self.by_name[item['name']] = item

    def available(self, implementation):
        machine = {'x86_64': 'amd64', 'aarch64': 'arm64'}.get(platform.machine(), platform.machine())
        return (implementation['version'] == version('python-pptx') and
                platform.system()+'/'+machine in implementation['platform'])

    def select(self, name):
        if name not in self.by_name:
            raise TaskError('CAPABILITY_UNREGISTERED', '原子能力未登记。', 'CapabilityRegistry', ['SYS-007'])
        item = self.by_name[name]
        candidates = [i for i in item['implementations'] if self.available(i)]
        if len(candidates) != 1:
            raise TaskError('IMPLEMENTATION_UNAVAILABLE', '当前平台或锁定依赖没有唯一可用实现；未替换。', 'CapabilityRegistry', ['SYS-007'])
        return item, candidates[0]

    def check_call(self, call, output=None):
        item, impl = self.select(call['capability'])
        if call['capability_id'] != item['capability_id'] or call['implementation_id'] != impl['implementation_id'] or call['backend'] != impl['backend']:
            raise TaskError('IMPLEMENTATION_BINDING_INVALID', '调用未绑定已登记的能力与实现。', 'CapabilityRegistry', ['SYS-007', 'SYS-011'])
        schema = item['output_schema' if output is not None else 'input_schema']
        if not Draft202012Validator(schema).is_valid(output if output is not None else call['inputs']):
            raise TaskError('ATOMIC_CONTRACT_INVALID', '原子能力输入/输出不符合登记契约。', 'CapabilityRegistry', ['SYS-007', 'SYS-012'])
        if output is None and call['capability'] in {'add_text', 'add_table', 'add_chart', 'add_image', 'add_shape', 'add_connector'}:
            bounds = call['inputs']['bounds']
            if any(not math.isfinite(v) for v in bounds) or min(bounds[:2]) < 0 or min(bounds[2:]) <= 0:
                raise TaskError('ATOMIC_GEOMETRY_INVALID', '原子能力几何须为有限正尺寸。', 'CapabilityRegistry', ['SYS-007', 'SYS-012'])
            data = call['inputs'].get('data')
            if call['capability'] == 'add_table' and any(len(row) != len(data['columns']) for row in data['rows']):
                raise TaskError('ATOMIC_DATA_INVALID', '表格行宽必须等于列数。', 'CapabilityRegistry', ['SYS-007', 'SYS-012'])
            if call['capability'] == 'add_chart' and any(len(s['values']) != len(data['categories']) or any(not math.isfinite(v) for v in s['values']) for s in data['series']):
                raise TaskError('ATOMIC_DATA_INVALID', '图表系列长度或数值非法。', 'CapabilityRegistry', ['SYS-007', 'SYS-012'])
        return impl

    def snapshot(self):
        result = copy.deepcopy(self.catalog)
        for item in result['capabilities']:
            for impl in item['implementations']:
                impl['health'] = {'available': self.available(impl), 'checked': 'platform and exact installed library version',
                                  'source_sha256': hashlib.sha256((ROOT/'src/yoloongppt/writer.py').read_bytes()).hexdigest(),
                                  'reason': 'Native subset; health is not full object/round-trip acceptance.'}
        return result
