"""OBS-007/009 runtime version evidence and comparable saved artifacts."""
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from .schemas import ROOT
from .errors import TaskError


def version_manifest(schemas):
    try:
        commit=subprocess.run(['git','-c','core.autocrlf=true','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,timeout=5)
        revision=commit.stdout.strip() if commit.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired): revision=None
    lock=ROOT/'requirements.lock'
    return {'runtime':{'python':platform.python_version(),'platform':platform.platform()},'commit':revision,
            'commit_status':'available' if revision else 'git_unavailable_in_runtime',
            'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/yoloongppt').glob('*.py'))},
            'dependency_lock':hashlib.sha256(lock.read_bytes()).hexdigest(),'schemas':schemas.versions,
            'backend':{'id':'PP-05','library':'python-pptx','version':'1.0.2'},
            'office_api_set':{'status':'not_available','reason':'Docker OOXML backend does not run Microsoft Office'},
            'templates':{'status':'per_run_import_report'},'renderer':{'id':'LibreOffice','version':'7.4.7.2'}}


def compare_runs(left_id,right_id,trace):
    from .operations import run_folder,artifacts
    artifacts(left_id,trace);artifacts(right_id,trace)
    left,right=run_folder(left_id),run_folder(right_id)
    differences=[]
    for name in ['deck-spec.json','object-map.json','pipeline-trace.json','quality-report.json','narrative-result.json']:
        a=json.loads((left/name).read_text('utf-8')) if (left/name).is_file() else None
        b=json.loads((right/name).read_text('utf-8')) if (right/name).is_file() else None
        differences.append({'artifact':name,'equal':a==b,'left':a,'right':b})
    return {'ok':True,'trace_id':trace,'left_run_id':left_id,'right_run_id':right_id,'differences':differences,
            'scope':'saved structured snapshots; semantic equivalence is not inferred from equality'}
