"""Strict UTF-8 JSON input; ambiguous keys/non-JSON numbers cannot lose data silently."""
import json

from .errors import TaskError


def load_json(raw, component):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('non-JSON numeric constant')

    try:
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode('utf-8')
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise TaskError('INPUT_JSON_INVALID', '任务必须是合法UTF-8 JSON，键不得重复、数值不得为NaN/Infinity。',
                        component, ['SYS-001', 'SYS-019' if component == 'CLI' else 'SYS-020'], status=400) from None
