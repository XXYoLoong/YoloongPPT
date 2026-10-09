"""SYS-019 CLI entry consuming the same core as HTTP."""
import argparse
import json
import sys
from pathlib import Path

from .capabilities import CapabilityRegistry
from .errors import TaskError, internal_error, trace_id
from .jsonio import load_json
from .schemas import SchemaRegistry
from .tasks import validate_task


class CLIParser(argparse.ArgumentParser):
    def error(self, message):
        error = TaskError('CLI_ARGUMENT_INVALID', '命令或参数无效；使用--help查看已实现命令。', 'CLI', ['SYS-019'])
        print(json.dumps(error.result(trace_id()), ensure_ascii=False))
        raise SystemExit(2)


def main():
    parser = CLIParser(prog='yoloongppt')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('capabilities')
    sub.add_parser('schemas')
    validate = sub.add_parser('validate')
    validate.add_argument('task', help='TaskSpec JSON path or - for stdin')
    args = parser.parse_args()
    trace = trace_id()
    try:
        registry = SchemaRegistry()
        if args.command == 'validate':
            try:
                raw = sys.stdin.buffer.read() if args.task == '-' else Path(args.task).read_bytes()
            except OSError:
                raise TaskError('INPUT_NOT_FOUND', '无法读取任务输入文件。', 'CLI', ['SYS-019', 'SYS-001']) from None
            document = load_json(raw, 'CLI')
            result = validate_task(document, registry, trace)
        elif args.command == 'capabilities':
            result = CapabilityRegistry(registry).list(trace)
        else:
            result = {'ok': True, 'trace_id': trace, 'schemas': registry.list()}
    except TaskError as error:
        result = error.result(trace)
    except Exception:
        result = internal_error().result(trace)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
