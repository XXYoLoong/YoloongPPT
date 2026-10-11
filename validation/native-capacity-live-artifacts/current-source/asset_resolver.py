"""SYS-009 / AST-001..012: resolve declared assets to verified, real bytes.

This resolver never invents an image, license, semantic score or generation result.
All writing happens below the F-backed /runtime mount. Remote fetching is opt-in,
HTTPS only, pinned to a validated public address, and does not follow redirects.
"""
import hashlib
import http.client
import ipaddress
import json
import os
import socket
import ssl
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from .assets import MAX_ASSET_BYTES, inspect_image
from .errors import TaskError

SOURCE_TYPES = ('user', 'local', 'template', 'url', 'search', 'generation', 'derived')


def _fail(code, message, details=None):
    ids = ['SYS-009', 'DEC-024', 'AST-001', 'AST-003', 'AST-012']
    if code in {'ASSET_PATH_FORBIDDEN', 'ASSET_PATH_INVALID', 'ASSET_SENSITIVE_PATH_FORBIDDEN'}:
        ids.append('SEC-001')
    raise TaskError(code, message, 'AssetResolver', ids, details or [])


def allowed_path(path, roots=None):
    declared = Path(path).absolute()
    def sensitive(value):
        for component in value.parts:
            name = component.casefold()
            if name in {'secrets', '.git', '.ssh', '.env'} or name.startswith('.env.'):
                return True
        return False
    # Check both the caller spelling and the real target. A harmless-looking
    # symlink must not make credentials eligible as material; nor may a secret
    # alias pointing to a public image bypass the explicitly excluded boundary.
    if sensitive(declared):
        _fail('ASSET_SENSITIVE_PATH_FORBIDDEN', '凭据、环境、Git或SSH路径不能作为素材或模板；未读取文件。')
    try:
        path = declared.resolve()
    except (OSError, RuntimeError):
        _fail('ASSET_PATH_INVALID', '素材路径不可解析或符号链接循环；未读取文件。')
    if sensitive(path):
        _fail('ASSET_SENSITIVE_PATH_FORBIDDEN', '素材链接实际指向凭据、环境、Git或SSH路径；未读取文件。')
    roots = [Path(x).resolve() for x in (roots or ['/workspace', '/runtime'])]
    if not any(path.is_relative_to(root) for root in roots):
        _fail('ASSET_PATH_FORBIDDEN', '素材路径不在已授权工作区/运行目录。')
    if not path.is_file():
        _fail('ASSET_FILE_MISSING', '已声明素材文件不存在；未替换为空白或虚构图片。')
    if not 0 < path.stat().st_size <= MAX_ASSET_BYTES:
        _fail('ASSET_SIZE_LIMIT', '素材为空或超过64MiB，未裁剪原始文件。')
    return path


def _write(root, name, raw):
    root = Path(root).resolve()
    if not root.is_relative_to(Path('/runtime')):
        _fail('ASSET_OUTPUT_FORBIDDEN', '素材缓存必须在F盘绑定的/runtime目录。')
    root.mkdir(parents=True, exist_ok=True)
    destination = root / name
    if destination.exists():
        if destination.read_bytes() != raw:
            _fail('ASSET_CACHE_CHANGED', '同一内容寻址缓存已改变，拒绝覆盖。')
        return destination
    temporary = root / (name + '.' + str(uuid4()) + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


class _PublicHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address, port):
        super().__init__(host, port=port, timeout=20, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        sock = socket.create_connection((self.address, self.port), timeout=self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def download(url, *, enabled=False, expected_sha256=None):
    if not enabled:
        _fail('ASSET_REMOTE_DISABLED', '远程素材下载须由调用者显式开启；未执行网络请求。')
    parsed = urlsplit(url)
    try:
        port = parsed.port or 443
    except ValueError:
        _fail('ASSET_URL_INVALID', '素材URL端口不合法。')
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or port != 443 or parsed.fragment:
        _fail('ASSET_URL_FORBIDDEN', '素材只允许无凭据、无fragment的HTTPS 443 URL。')
    host = parsed.hostname.encode('idna').decode('ascii')
    try:
        addresses = sorted({entry[4][0] for entry in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)})
    except (OSError, UnicodeError):
        _fail('ASSET_DNS_FAILED', '素材域名解析失败；未缓存半文件。')
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        _fail('ASSET_SSRF_BLOCKED', '素材域名指向非公共地址；已阻断请求。')
    connection = _PublicHTTPS(host, addresses[0], port)
    try:
        target = parsed.path or '/'
        if parsed.query: target += '?' + parsed.query
        connection.request('GET', target, headers={'Accept': 'image/png,image/jpeg,image/webp,image/gif', 'User-Agent': 'YoloongPPT-AssetResolver/1'})
        response = connection.getresponse()
        if response.status != 200:
            _fail('ASSET_HTTP_FAILED', '远程素材未返回200；redirect不自动跟随。', [{'status': response.status}])
        mime = response.getheader('Content-Type', '').split(';')[0].strip().lower()
        if mime not in {'image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff'}:
            _fail('ASSET_MIME_UNSUPPORTED', '下载响应不是可核验的栅格图片MIME。', [{'mime': mime}])
        length = response.getheader('Content-Length')
        if length is not None:
            try: size = int(length)
            except ValueError: _fail('ASSET_HTTP_INVALID_LENGTH', '下载长度字段无效。')
            if not 0 < size <= MAX_ASSET_BYTES: _fail('ASSET_SIZE_LIMIT', '下载声明长度为空或超限。')
        raw = response.read(MAX_ASSET_BYTES + 1)
        if not 0 < len(raw) <= MAX_ASSET_BYTES: _fail('ASSET_SIZE_LIMIT', '下载实际字节为空或超限。')
        inspection = inspect_image(raw)
        if inspection['mime_type'] != mime:
            _fail('ASSET_MIME_MISMATCH', 'HTTP MIME与实际图片编码不匹配。')
        if length is not None and int(length) != len(raw): _fail('ASSET_HTTP_INCOMPLETE', '响应长度不符；未写入半文件。')
        if expected_sha256 and hashlib.sha256(raw).hexdigest() != expected_sha256:
            _fail('ASSET_HASH_MISMATCH', '下载hash与调用者声明不符。')
        return raw
    except TaskError:
        raise
    except (OSError, ValueError, http.client.HTTPException):
        _fail('ASSET_DOWNLOAD_FAILED', '远程下载失败；未写入半文件；调用者可显式重试。')
    finally:
        connection.close()


def resolve(plan, *, allowed_roots=None, output_root='/runtime/assets', schemas=None):
    """Resolve AssetPlan requests. Permission fields are claims with provenance.

    source_type search/generation requires an already materialized file and its
    original query/request metadata. The resolver is not a search/image service.
    """
    if schemas: schemas.validate('asset-resolver-plan.schema.json', plan)
    requests = plan.get('requests', [])
    ids = [item.get('asset_id') for item in requests]
    if len(ids) != len(set(ids)): _fail('ASSET_ID_DUPLICATE', '素材ID重复。')
    entries, issues = [], []
    for request in requests:
        source_type = request.get('source_type', 'user')
        if source_type not in SOURCE_TYPES: _fail('ASSET_SOURCE_UNSUPPORTED', '素材来源类型未登记。')
        locator = request.get('path') or request.get('url')
        if not locator:
            _fail('ASSET_NOT_MATERIALIZED', '素材没有真实文件或URL，生成请求不等于生成结果。')
        if request.get('path'):
            path = allowed_path(request['path'], allowed_roots)
            raw = path.read_bytes()
            source_locator = str(path)
        else:
            raw = download(request['url'], enabled=bool(plan.get('allow_network', False)), expected_sha256=request.get('expected_sha256'))
            source_locator = request['url']
        digest = hashlib.sha256(raw).hexdigest()
        if request.get('expected_sha256') and request['expected_sha256'] != digest:
            _fail('ASSET_HASH_MISMATCH', '素材hash与声明不符。', [{'asset_id': request['asset_id']}])
        metadata = inspect_image(raw)
        if metadata['frame_count'] != 1:
            _fail('ANIMATED_IMAGE_POLICY_REQUIRED', '多帧图片需显式动画或取帧策略；未静默保留首帧。')
        if source_type in {'search', 'generation'} and not request.get('request_metadata'):
            _fail('ASSET_SOURCE_PROVENANCE_MISSING', '检索或生成素材缺少query/生成请求的来源记录。')
        license_record = request.get('license', 'unknown')
        usage = request.get('usage_status', 'unverified')
        if usage != 'authorized':
            _fail('ASSET_USAGE_UNAUTHORIZED', '素材可登记但没有调用者明确使用授权；未写入PPT。', [{'asset_id': request['asset_id'], 'license': license_record, 'usage_status': usage}])
        suffix = {'PNG': '.png', 'JPEG': '.jpg', 'WEBP': '.webp', 'GIF': '.gif', 'BMP': '.bmp', 'TIFF': '.tiff'}.get(metadata['format'])
        if suffix is None: _fail('ASSET_ENCODING_UNSUPPORTED', '该图片编码没有已验证的执行后端，未静默转换。')
        cached = _write(output_root, digest + suffix, raw)
        record = {'asset_id': request['asset_id'], 'source_id': request.get('source_id'), 'source_type': source_type, 'source_locator': source_locator,
                  'source_url': request.get('url') or request.get('source_url'), 'path': str(cached), 'sha256': digest,
                  'bytes': len(raw), 'mime_type': metadata['mime_type'], 'width_px': metadata['width'], 'height_px': metadata['height'],
                  'inspection': metadata, 'license': license_record, 'usage_status': usage,
                  'authorization_basis': request.get('authorization_basis', 'explicit caller authorization'),
                  'attribution': request.get('attribution'), 'transform_history': request.get('transform_history', []),
                  'request_metadata': request.get('request_metadata'), 'source_refs': request.get('source_refs', []),
                  'semantic_status': 'caller_role_declared_not_independently_reviewed',
                  'deliberate_reuse': bool(request.get('deliberate_reuse', False)), 'cache_status': 'complete_and_hash_verified'}
        if license_record == 'unknown':
            issues.append({'code': 'ASSET_LICENSE_UNKNOWN', 'asset_id': record['asset_id'], 'message': '使用由调用者授权；license仍unknown，不推断版权许可。'})
        minimum = plan.get('minimum_pixels', [1, 1])
        if metadata['width'] < minimum[0] or metadata['height'] < minimum[1]:
            _fail('ASSET_RESOLUTION_INSUFFICIENT', '图片低于调用者的像素门槛；未放大假装更清晰。', [{'asset_id': record['asset_id'], 'actual': [metadata['width'], metadata['height']], 'minimum': minimum}])
        entries.append(record)
    duplicates = []
    for digest in sorted({item['sha256'] for item in entries}):
        group = [item for item in entries if item['sha256'] == digest]
        if len(group) > 1:
            deliberate = all(item['deliberate_reuse'] for item in group)
            duplicates.append({'sha256': digest, 'asset_ids': [item['asset_id'] for item in group], 'basis': 'exact_bytes', 'deliberate_reuse': deliberate})
            if not deliberate: issues.append({'code': 'ASSET_DUPLICATE_UNCONFIRMED', 'asset_ids': [item['asset_id'] for item in group]})
    result = {'status': 'partial' if issues else 'resolved', 'entries': entries, 'issues': issues, 'duplicate_groups': duplicates,
              'boundary': 'Real bytes/hash/MIME/pixels and caller authorization checked; semantic appropriateness, watermark, perceptual duplicates and full AST acceptance remain unproven.'}
    if schemas: schemas.validate('asset-resolver-result.schema.json', result)
    return result


def inventory_from_task(task, sources=None):
    """Return declarations only; DEC-003 caller asset role is mandatory."""
    result = []
    loaded = {item['source_id']: item for item in (sources or {}).get('source_bundle', {}).get('bundle', {}).get('sources', [])}
    for source in task.get('sources', []):
        metadata = source.get('metadata', {})
        role = metadata.get('source_role')
        if role not in ('asset', 'image_asset', ['asset'], ['image_asset']): continue
        if not source.get('locator'):
            _fail('ASSET_LOCATOR_REQUIRED', '素材来源必须指向真实文件或URL。')
        loaded_refs = loaded.get(source['source_id'], {}).get('raw_asset_refs', [])
        stable_asset = 'asset_' + str(UUID(bytes=hashlib.sha256(source['source_id'].encode('utf-8')).digest()[:16], version=4))
        asset_id = metadata.get('asset_id') or (loaded_refs[0] if len(loaded_refs) == 1 else stable_asset)
        result.append({'asset_id': asset_id, 'source_id': source['source_id'], 'source_type': metadata.get('asset_source_type', 'user'),
                       'path' if not source['locator'].startswith('https://') else 'url': source['locator'],
                       'license': metadata.get('license', 'unknown'), 'usage_status': metadata.get('usage_status', 'authorized'),
                       'authorization_basis': metadata.get('authorization_basis', 'caller supplied file with explicit asset role'),
                       'attribution': metadata.get('attribution'), 'source_url': metadata.get('source_url'),
                       'source_refs': [], 'deliberate_reuse': metadata.get('deliberate_reuse', False),
                       'request_metadata': metadata.get('request_metadata'), 'transform_history': metadata.get('transform_history', [])})
    return result
