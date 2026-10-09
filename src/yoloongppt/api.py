"""SYS-020: shared core API, local deployment; no generation/jobs yet."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from .capabilities import CapabilityRegistry
from .errors import TaskError, internal_error, trace_id
from .jsonio import load_json
from .schemas import SchemaRegistry
from .tasks import validate_task

MAX_BODY_BYTES = 4 * 1024 * 1024


@asynccontextmanager
async def lifespan(app):
    app.state.schemas = SchemaRegistry()
    app.state.capabilities = CapabilityRegistry(app.state.schemas)
    yield


app = FastAPI(title='YoloongPPT', lifespan=lifespan, docs_url=None, redoc_url=None)


@app.middleware('http')
async def trace_request(request, call_next):
    request.state.trace_id = trace_id()
    try:
        response = await call_next(request)
    except Exception:
        # Do not leak exception text, provider credentials, payload or stack paths.
        response = JSONResponse(internal_error().result(request.state.trace_id), status_code=500)
    response.headers['X-Trace-Id'] = request.state.trace_id
    return response


@app.exception_handler(TaskError)
async def task_error(request, error):
    return JSONResponse(error.result(request.state.trace_id), status_code=error.status)


@app.exception_handler(HTTPException)
async def http_error(request, error):
    result = TaskError('HTTP_REQUEST_REJECTED', '不存在该接口或请求方法不受支持。',
                       'HTTP API', ['SYS-020'], status=error.status_code)
    return JSONResponse(result.result(request.state.trace_id), status_code=error.status_code)


@app.get('/health')
def health(request: Request):
    return {'ok': True, 'trace_id': request.state.trace_id, 'state': 'core_ready',
            'generation_ready': False, 'schema_count': len(request.app.state.schemas.documents)}


@app.get('/capabilities')
def capabilities(request: Request):
    return request.app.state.capabilities.list(request.state.trace_id)


@app.get('/schemas')
def schemas(request: Request):
    return {'ok': True, 'trace_id': request.state.trace_id, 'schemas': request.app.state.schemas.list()}


@app.post('/validate')
async def validate(request: Request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_BODY_BYTES:
            raise TaskError('REQUEST_TOO_LARGE', 'JSON任务超过4MiB入口限制；未执行任务。',
                            'HTTP API', ['SYS-020'], status=413)
    document = load_json(body, 'HTTP API')
    return validate_task(document, request.app.state.schemas, request.state.trace_id)
