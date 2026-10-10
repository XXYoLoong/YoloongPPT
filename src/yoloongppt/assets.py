"""IN-011/012/013, AST-001/004/011: inspect local assets without inferring facts."""
import hashlib
import io
import mimetypes
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .errors import TaskError

MAX_IMAGE_PIXELS = 40_000_000
MAX_ASSET_BYTES = 64 * 1024 * 1024
ASSET_TYPES = {'.svg': 'vector', '.ttf': 'font', '.otf': 'font', '.woff': 'font', '.woff2': 'font',
               '.mp3': 'audio', '.wav': 'audio', '.ogg': 'audio', '.mp4': 'video', '.webm': 'video',
               '.pptx': 'template', '.potx': 'template'}


def inspect_image(raw, filename=None):
    if not raw or len(raw) > MAX_ASSET_BYTES:
        raise TaskError('ASSET_SIZE_LIMIT', '图片为空或超过64MiB限制；未截断。', 'AssetResolver', ['IN-011', 'AST-004', 'SEC-004'])
    try:
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                raise TaskError('IMAGE_PIXEL_LIMIT', '图片超过四千万像素限制。', 'AssetResolver', ['IN-011', 'AST-004'])
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            # Deterministic bounded palette analysis; original pixels and bytes are not changed.
            preview = image.convert('RGBA'); preview.thumbnail((128, 128))
            opaque = Image.new('RGBA', preview.size, 'white'); opaque.alpha_composite(preview)
            palette = opaque.convert('RGB').quantize(colors=6)
            colors = palette.getcolors() or []; rgb = palette.getpalette()
            total = sum(count for count, _ in colors)
            dominant = [{'color': '#%02X%02X%02X' % tuple(rgb[index*3:index*3+3]),
                         'fraction': round(count / total, 6)} for count, index in sorted(colors, reverse=True)]
            grayscale = opaque.convert('L').resize((9, 8)); pixels = list(grayscale.getdata())
            bits = [pixels[y*9+x] > pixels[y*9+x+1] for y in range(8) for x in range(8)]
            dhash = sum(int(bit) << (63-index) for index, bit in enumerate(bits))
            dpi = image.info.get('dpi'); profile = image.info.get('icc_profile')
            return {'asset_kind': 'image', 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                    'format': image.format, 'mime_type': Image.MIME.get(image.format), 'width': width, 'height': height,
                    'mode': image.mode, 'frame_count': getattr(image, 'n_frames', 1),
                    'aspect_ratio': width / height, 'dpi': list(dpi) if isinstance(dpi, tuple) else None,
                    'color_profile_sha256': hashlib.sha256(profile).hexdigest() if isinstance(profile, bytes) else None,
                    'perceptual_hash': {'algorithm': 'dhash-9x8-white-composite-frame0', 'value': f'{dhash:016x}'},
                    'has_alpha': 'A' in image.getbands() or 'transparency' in image.info,
                    'dominant_colors': dominant, 'dominant_color_method': '128px thumbnail, white alpha composite, Pillow quantize 6',
                    'semantic_status': 'not_inferred', 'ocr_status': 'unsupported',
                    'issues': [{'code': 'IMAGE_OCR_NOT_EXECUTED', 'requirement_ids': ['IN-011'],
                                'message': '仅提取像素元数据和主色，未声称提取图片文字、语义元素或可编辑布局。'}]}
    except TaskError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise TaskError('IMAGE_CORRUPT_OR_UNSUPPORTED', '图片格式不支持或文件损坏。', 'AssetResolver', ['IN-011', 'IN-015', 'AST-004']) from None


def inventory(directory, *, allowed_roots=None, max_files=2048):
    """Read only. Register hashes, unknown license/roles, duplicates and failures explicitly."""
    root = Path(directory).resolve()
    roots = [Path(x).resolve() for x in (allowed_roots or ['/workspace', '/runtime'])]
    if not any(root.is_relative_to(x) for x in roots) or not root.is_dir():
        raise TaskError('ASSET_DIRECTORY_INVALID', '资产目录不存在或不在允许范围。', 'AssetResolver', ['IN-012', 'SEC-003'])
    if any(p in {'secrets','.git','.ssh','.env'} for p in root.parts):
        raise TaskError('ASSET_DIRECTORY_INVALID','禁止登记敏感目录。','AssetResolver',['SEC-003'])
    files = []
    for path in root.rglob('*'):
        if any(p in {'secrets','.git','.ssh','.env'} or p.startswith('.env.') for p in path.relative_to(root).parts):continue
        if path.is_file():files.append(path)
        if len(files) > max_files:
            raise TaskError('ASSET_COUNT_LIMIT', '资产目录超过文件数量限制；未部分登记。', 'AssetResolver', ['IN-012', 'SEC-004'])
    files.sort()
    entries = []; issues = []; groups = {}
    for path in files:
        relative = str(path.relative_to(root))
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            issues.append({'path': relative, 'code': 'ASSET_SYMLINK_BLOCKED'}); continue
        try:
            if path.stat().st_size > MAX_ASSET_BYTES:
                issues.append({'path': relative, 'code': 'ASSET_SIZE_LIMIT'}); continue
            raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
            entry = {'relative_path': relative, 'sha256': digest, 'bytes': len(raw),
                     'asset_kind': ASSET_TYPES.get(path.suffix.lower(), 'unknown'),
                     'mime_type': mimetypes.guess_type(path.name)[0], 'license': 'unknown',
                     'authorization': 'not_provided', 'source_type': 'local', 'role': 'unclassified', 'inspection': None}
            if entry['mime_type'] and entry['mime_type'].startswith('image/') and path.suffix.lower() != '.svg':
                entry['inspection'] = inspect_image(raw, path.name); entry['asset_kind'] = 'image'
            entries.append(entry); groups.setdefault(digest, []).append(relative)
        except (OSError, TaskError) as error:
            issues.append({'path': relative, 'code': error.code if isinstance(error, TaskError) else 'ASSET_READ_FAILED'})
    perceptual = {}
    for entry in entries:
        if entry['inspection']:
            value=entry['inspection']['perceptual_hash']['value'];perceptual.setdefault(value,[]).append(entry['relative_path'])
    return {'status': 'partial' if issues else 'complete', 'root': str(root), 'entries': entries, 'issues': issues,
            'duplicate_groups': [{'sha256': k, 'paths': v, 'basis': 'exact_bytes', 'deliberate_reuse': 'unspecified'}
                                 for k, v in groups.items() if len(v) > 1],
            'perceptual_duplicate_candidates': [{'hash':k,'paths':v,'basis':'dhash-equality','semantic_confirmation':'not_executed'} for k,v in perceptual.items() if len(v)>1],
            'boundary': 'Inventory is not permission, font embedding authorization, media compatibility or semantic duplicate acceptance.'}
