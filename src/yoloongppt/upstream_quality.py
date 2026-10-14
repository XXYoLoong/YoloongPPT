"""RES-032/SYS-015: thin adapters for the fixed PPTAgent MIT modules."""
import importlib.util
import json
import re
import sys
from pathlib import Path

from .errors import TaskError
from .quality_rules import issue

VENDOR = Path(__file__).resolve().parents[2] / 'vendor' / 'pptagent_quality'


def _module(name):
    from .vendor_integrity import verify_vendor
    verify_vendor(VENDOR,'833cda553b343be0e486a93b0b57cac962cdd566')
    package = '_yoloongppt_pptagent_quality'
    if package not in sys.modules:
        spec = importlib.util.spec_from_file_location(package, VENDOR/'__init__.py', submodule_search_locations=[str(VENDOR)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        spec.loader.exec_module(module)
    return __import__(package+'.'+name, fromlist=[name])


def validate_upstream_review(payload, *, slide_count=None):
    """Execute upstream validation, then enforce this system's deck bounds."""
    try:
        result = _module('visual').validate_review(payload)
        if slide_count is not None and any(i['slide'] > slide_count for i in result['issues']):
            raise ValueError('review slide exceeds the actual deck')
        return result
    except (ValueError, TypeError) as exc:
        raise TaskError('UPSTREAM_VISUAL_REVIEW_INVALID', str(exc), 'QAEngine', ['QA-020','SYS-015']) from None


def validate_product_review(payload, deck):
    """Map the existing independently reviewed response to the upstream contract.

    The upstream does not cover fact truth or editability. No claim is added.
    """
    severity = {'P0':'blocker', 'P1':'major', 'P2':'minor'}
    problems = [{'severity':severity[i['severity']], 'slide':i['slide_order']+1,
                 'description':i['detail'],
                 'suggested_fix':'Fail pending an explicit scoped RevisionAction; retain original issue and evidence.'}
                for i in payload['issues']]
    verdict = 'fail' if any(i['severity'] in {'blocker','major'} for i in problems) else 'pass'
    return validate_upstream_review({'verdict':verdict,'summary':payload['summary'],'issues':problems}, slide_count=len(deck['slides']))


def _scoped_path(root, value):
    path = (root/value).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise TaskError('UPSTREAM_RENDER_PATH_INVALID', 'Render path is missing or outside the current run.', 'QAEngine',['SYS-014','QA-020'])
    return path


def instruction_leaks(deck, task):
    """Detect copied normalized page-budget controls, never bare keywords.

    Only standalone audience-facing body text matching the actual task's page
    preference and literal prompt is checked. Quotes/provenance and arbitrary
    business uses of PPT/budget remain outside this bounded deterministic rule.
    """
    count = task.get('runtime_preferences',{}).get('page_count')
    raw = task.get('raw_request',{}).get('request',{}).get('raw_text','')
    if type(count) is not int or not raw:
        return []
    budget = re.compile(r'^(?:偏好|希望|期望)\s*'+str(count)+r'\s*页(?:[；;，,。\s]|$)')
    source_budget = re.search(r'(?:偏好|希望|期望)\s*'+str(count)+r'\s*页', raw)
    if not source_budget:
        return []
    issues=[]
    for slide in deck['slides']:
        for text in slide.get('content',{}).get('body',[]):
            if not isinstance(text,str) or not budget.search(text.strip()):
                continue
            targets=[e['object_id'] for e in slide.get('elements',[]) if e.get('type')=='text' and text in e.get('text',e.get('data',{}).get('paragraphs',[]))]
            issues.append(issue('TASK_INSTRUCTION_LEAK',slide['slide_id'],
                'A page-count task control was copied into audience-facing body text.','QA-013','P1',
                object_id=targets[0] if len(targets)==1 else None,
                measurement={'text':text,'normalized_page_preference':count,'prompt_span':source_budget.group(),'target_candidates':targets},
                threshold={'task_controls_in_audience_body':0},
                action={'node':'content','mode':'fail','reason':'Requires explicit scoped text revision preserving all selected business facts.'}))
    return issues


def audit_upstream_quality(deck, pptx, object_map, renders, root):
    root = Path(root).resolve()
    fresh = _module('freshness')
    versions = json.loads((VENDOR/'SOURCE.json').read_text('utf-8'))
    checks=[]; issues=[]
    images={}
    for artifact in renders.get('artifacts',[]):
        if artifact.get('type')!='png':
            continue
        path=_scoped_path(root,artifact['path'])
        images[str(path.relative_to(root))]=artifact['hash']
    pptx=Path(pptx).resolve()
    if not pptx.is_relative_to(root):
        raise TaskError('UPSTREAM_RENDER_PATH_INVALID','PPTX is outside the current run.','QAEngine',['SYS-014','QA-020'])
    _scoped_path(root,str(pptx.relative_to(root)))
    inputs={'artifact_sha256':fresh.sha256(pptx)}
    # Preserve recorded hashes; rebuilding them here would conceal stale images.
    current=fresh.render_current(root,{'inputs':inputs,'images':images},inputs)
    checks.append({'kind':'upstream_quality','check':'PPTAgent render_current: saved PNG bytes match declared hashes','status':'executed','passed':current,'pptx_sha256':inputs['artifact_sha256'],'images':images})
    if not current:
        issues.append(issue('UPSTREAM_RENDER_STALE',None,'Missing or changed rendered PNG evidence.','SYS-014',measurement={'images':images},threshold={'all_recorded_image_hashes_match':True}))
    expected={s['slide_id'] for s in deck['slides']}
    actual=[a.get('slide_id') for a in renders.get('artifacts',[]) if a.get('type')=='png']
    if len(actual)!=len(expected) or set(actual)!=expected:
        issues.append(issue('UPSTREAM_RENDER_SCOPE_INCOMPLETE',None,'Rendered image scope differs from deck.','SYS-014',measurement={'actual':actual,'expected':sorted(expected)},threshold={'one_image_per_slide':True}))
    task_path=root/'task.json'
    if task_path.is_file():
        task=json.loads(task_path.read_text('utf-8'))
        found=instruction_leaks(deck,task);issues.extend(found)
        checks.append({'kind':'semantic','check':'Task-bound page-control leakage into visible body','status':'executed','issues':len(found),'scope':'literal page preference matching actual TaskContext; full semantic relevance requires independent model review'})
    review_path=root/'review-response.json'
    if review_path.is_file():
        response=json.loads(review_path.read_text('utf-8'))
        upstream=validate_product_review(response,deck)
        checks.append({'kind':'upstream_quality','check':'PPTAgent validate_review executed against mapped saved independent response','status':'executed','result':upstream})
    return {'issues':issues,'checks':checks,'versions':{'PPTAgent':versions['commit'],'license':versions['license']}}
