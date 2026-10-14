"""RES-032: check the fixed imported dependency closure before executing it."""
import hashlib,json
from .errors import TaskError

def verify_vendor(folder,commit):
    manifest_path=folder/'SOURCE.json';manifest=json.loads(manifest_path.read_text('utf-8'))
    if manifest.get('commit')!=commit or not manifest.get('files'):
        raise TaskError('UPSTREAM_VERSION_UNVERIFIED','上游固定版本或源码清单缺失。','ReuseRegistry',['RES-032'])
    root=folder.parents[1]
    for item in manifest['files']:
        path=(root/item['target']).resolve()
        if not path.is_relative_to(folder.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['vendored_sha256']:
            raise TaskError('UPSTREAM_SOURCE_CHANGED','已登记上游模块或许可文件改变。','ReuseRegistry',['RES-032','SEC-001'])
    return {'commit':commit,'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'verified_files':len(manifest['files'])}
