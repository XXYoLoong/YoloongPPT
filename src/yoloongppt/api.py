"""SYS-020: shared core API, local draft generation/revision; full jobs pending."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.concurrency import run_in_threadpool

from .capabilities import CapabilityRegistry
from .errors import TaskError, internal_error, trace_id
from .jsonio import load_json
from .schemas import SchemaRegistry
from .tasks import validate_task
from .evidence import EvidenceStore
from .sources import inspect_sources

MAX_BODY_BYTES = 4 * 1024 * 1024


@asynccontextmanager
async def lifespan(app):
    app.state.schemas = SchemaRegistry()
    app.state.capabilities = CapabilityRegistry(app.state.schemas)
    app.state.evidence = EvidenceStore()
    from .jobs import JobManager
    app.state.jobs = JobManager()
    app.state.jobs.start()
    yield
    app.state.jobs.close()


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
            'generation_ready': False, 'draft_generation_available': True,
            'schema_count': len(request.app.state.schemas.documents)}


@app.get('/capabilities')
def capabilities(request: Request):
    from .native_objects import capabilities as native_capabilities
    return {**request.app.state.capabilities.list(request.state.trace_id),'native_objects':native_capabilities()}


@app.get('/schemas')
def schemas(request: Request):
    return {'ok': True, 'trace_id': request.state.trace_id, 'schemas': request.app.state.schemas.list()}


@app.post('/validate')
async def validate(request: Request):
    document = await task_body(request)
    return validate_task(document, request.app.state.schemas, request.state.trace_id)


async def task_body(request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_BODY_BYTES:
            raise TaskError('REQUEST_TOO_LARGE', 'JSON任务超过4MiB入口限制；未执行任务。',
                            'HTTP API', ['SYS-020'], status=413)
    document = load_json(body, 'HTTP API')
    return document


@app.post('/inspect')
async def inspect(request: Request):
    document = await task_body(request)
    return await run_in_threadpool(inspect_sources, document, request.app.state.schemas, request.app.state.evidence, request.state.trace_id)


@app.post('/route')
async def route(request: Request):
    from .routing import run_route
    document = await task_body(request)
    return await run_in_threadpool(run_route, document, request.app.state.schemas, request.state.trace_id)


@app.post('/generate')
async def generate(request: Request):
    from .generation import generate as generate_deck
    document = await task_body(request)
    return await run_in_threadpool(generate_deck, document, request.app.state.schemas, request.app.state.evidence, request.state.trace_id)


@app.post('/context')
async def context(request: Request):
    from .context import run_context
    return await run_in_threadpool(run_context, await task_body(request), request.app.state.schemas, request.state.trace_id)


@app.post('/source-roles')
async def source_roles(request: Request):
    from .source_roles import run_roles
    return await run_in_threadpool(run_roles, await task_body(request), request.app.state.schemas, request.state.trace_id)


@app.post('/resolve-evidence')
async def resolve_evidence(request: Request):
    from .facts import run_node
    return await run_in_threadpool(run_node,await task_body(request),request.app.state.schemas,'DEC-004',request.state.trace_id)


@app.post('/fact-boundaries')
async def fact_boundaries(request: Request):
    from .facts import run_node
    return await run_in_threadpool(run_node,await task_body(request),request.app.state.schemas,'DEC-005',request.state.trace_id)


@app.get('/evidence/{evidence_id}')
def evidence(evidence_id: str, request: Request):
    return {'ok': True, 'trace_id': request.state.trace_id, 'evidence': request.app.state.evidence.get(evidence_id)}


@app.post('/resume/{run_id}')
async def resume(run_id: str, request: Request):
    from .generation import resume as resume_deck
    return await run_in_threadpool(resume_deck, run_id, request.app.state.schemas, request.app.state.evidence, request.state.trace_id)


@app.post('/revise/{run_id}')
async def revise(run_id: str, request: Request):
    from .revision import revise as revise_deck
    document = await task_body(request)
    return await run_in_threadpool(revise_deck, run_id, document, request.app.state.schemas, request.state.trace_id)


@app.post('/recheck/{run_id}')
async def recheck(run_id: str, request: Request):
    from .revision import recheck as recheck_deck
    return await run_in_threadpool(recheck_deck, run_id, request.app.state.schemas, request.state.trace_id)


@app.post('/create', status_code=202)
async def create(request: Request):
    return request.app.state.jobs.submit('generate', await task_body(request), request.state.trace_id)


@app.post('/jobs', status_code=202)
async def submit_job(request: Request):
    document=await task_body(request)
    if not isinstance(document,dict) or set(document)!={'operation','request'}:
        raise TaskError('JOB_REQUEST_INVALID','输入需operation和request。','JobManager',['SYS-020'])
    return request.app.state.jobs.submit(document['operation'],document['request'],request.state.trace_id)


@app.get('/status/{job_id}')
@app.get('/jobs/{job_id}')
def job_status(job_id: str, request: Request):
    return request.app.state.jobs.status(job_id,request.state.trace_id)


@app.post('/jobs/{job_id}/cancel')
def cancel_job(job_id: str, request: Request):
    return request.app.state.jobs.cancel(job_id,request.state.trace_id)


@app.post('/jobs/{job_id}/retry', status_code=202)
def retry_job(job_id: str, request: Request):
    return request.app.state.jobs.retry(job_id,request.state.trace_id)


@app.get('/artifacts/{run_id}')
def run_artifacts(run_id: str, request: Request):
    from .operations import artifacts
    return artifacts(run_id,request.state.trace_id)


@app.post('/debug-node')
async def debug_node(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'debug',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)


@app.post('/inspect-deck')
async def inspect_deck_api(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'inspect_deck',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)


@app.post('/edit-deck')
async def edit_deck_api(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'edit_deck',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)


@app.post('/parse-template')
async def template_api(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'parse_template',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)


@app.post('/compose-native')
async def compose_native(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'compose_native',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)


@app.post('/instantiate-template')
async def instantiate_template_api(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'instantiate_template',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)


@app.post('/compare-runs')
async def compare_api(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'compare',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)


@app.post('/inventory-assets')
async def inventory_api(request: Request):
    from .operations import dispatch
    return await run_in_threadpool(dispatch,'inventory_assets',await task_body(request),request.state.trace_id,request.app.state.schemas,request.app.state.evidence)
