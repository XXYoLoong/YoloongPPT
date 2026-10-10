"""One isolated operation; exception text and credentials never enter worker logs."""
import json
import sys
from pathlib import Path
from .errors import TaskError, internal_error
from .operations import dispatch


def main():
    operation, folder, trace = sys.argv[1:]
    folder = Path(folder).resolve()
    if not folder.is_relative_to(Path('/runtime/jobs')):
        return 2
    try:
        request=json.loads((folder/'request.json').read_text('utf-8'))
        result=dispatch(operation,request,trace)
    except TaskError as error:
        result=error.result(trace)
    except Exception:
        result=internal_error().result(trace)
    temporary=folder/'result.tmp'
    temporary.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    temporary.replace(folder/'result.json')
    return 0 if result.get('ok') else 1


if __name__=='__main__':
    sys.exit(main())
