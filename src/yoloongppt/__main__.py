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
from .sources import inspect_sources
from .evidence import EvidenceStore


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
    sub.add_parser('mcp-serve')
    sub.add_parser('artifacts').add_argument('run_id')
    sub.add_parser('debug-node').add_argument('task')
    sub.add_parser('doctor')
    sub.add_parser('render').add_argument('run_id')
    for name in ['inspect-deck','edit-deck','parse-template','instantiate-template','compose-native','compare-runs','inventory-assets']:
        sub.add_parser(name).add_argument('task')
    for command in ['validate', 'inspect', 'generate', 'route', 'context', 'source-roles', 'resolve-evidence', 'fact-boundaries']:
        task = sub.add_parser(command)
        task.add_argument('task', help='TaskSpec JSON path or - for stdin')
    sub.add_parser('evidence').add_argument('evidence_id')
    sub.add_parser('resume').add_argument('run_id')
    sub.add_parser('recheck').add_argument('run_id')
    revision = sub.add_parser('revise')
    revision.add_argument('run_id'); revision.add_argument('request')
    args = parser.parse_args()
    if args.command == 'mcp-serve':
        from .mcp_server import serve
        serve()
        return 0
    trace = trace_id()
    try:
        registry = SchemaRegistry()
        if args.command in {'doctor','render'}:
            from .operations import dispatch
            result=dispatch(args.command,{'run_id':args.run_id} if args.command=='render' else {},trace,registry)
        elif args.command == 'artifacts':
            from .operations import artifacts
            result=artifacts(args.run_id,trace)
        elif args.command in {'validate', 'inspect', 'generate', 'route', 'context', 'source-roles', 'resolve-evidence', 'fact-boundaries','debug-node','inspect-deck','edit-deck','parse-template','instantiate-template','compose-native','compare-runs','inventory-assets'}:
            try:
                raw = sys.stdin.buffer.read() if args.task == '-' else Path(args.task).read_bytes()
            except OSError:
                raise TaskError('INPUT_NOT_FOUND', '无法读取任务输入文件。', 'CLI', ['SYS-019', 'SYS-001']) from None
            document = load_json(raw, 'CLI')
            if args.command in {'inspect-deck','edit-deck','parse-template','instantiate-template','compose-native','compare-runs','inventory-assets'}:
                from .operations import dispatch
                result=dispatch('compare' if args.command=='compare-runs' else args.command.replace('-','_'),document,trace,registry)
            elif args.command == 'debug-node':
                from .operations import dispatch
                result=dispatch('debug',document,trace,registry)
            elif args.command in {'resolve-evidence','fact-boundaries'}:
                from .facts import run_node
                result=run_node(document,registry,'DEC-004' if args.command=='resolve-evidence' else 'DEC-005',trace)
            elif args.command == 'context':
                from .context import run_context
                result = run_context(document, registry, trace)
            elif args.command == 'source-roles':
                from .source_roles import run_roles
                result = run_roles(document, registry, trace)
            elif args.command == 'route':
                from .routing import run_route
                result = run_route(document, registry, trace)
            elif args.command == 'generate':
                from .generation import generate
                result = generate(document, registry, EvidenceStore(), trace)
            else:
                result = validate_task(document, registry, trace) if args.command == 'validate' else inspect_sources(document, registry, EvidenceStore(), trace)
        elif args.command == 'revise':
            from .revision import revise
            try:
                raw = sys.stdin.buffer.read() if args.request == '-' else Path(args.request).read_bytes()
            except OSError:
                raise TaskError('INPUT_NOT_FOUND', '无法读取修订请求。', 'CLI', ['SYS-019']) from None
            result = revise(args.run_id, load_json(raw, 'CLI'), registry, trace)
        elif args.command == 'recheck':
            from .revision import recheck
            result = recheck(args.run_id, registry, trace)
        elif args.command == 'resume':
            from .generation import resume
            result = resume(args.run_id, registry, EvidenceStore(), trace)
        elif args.command == 'evidence':
            result = {'ok': True, 'trace_id': trace, 'evidence': EvidenceStore().get(args.evidence_id)}
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
