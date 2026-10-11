"""SYS-017: isolated runs, atomic JSON and hashed manifests on /runtime."""
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from .errors import TaskError


def entity(kind):
    return kind + '_' + str(uuid4())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RunArtifacts:
    def __init__(self, root='/runtime/runs'):
        root = Path(root).resolve()
        if not root.is_relative_to(Path('/runtime')):
            raise TaskError('ARTIFACT_PATH_INVALID', '产物只允许保存到F盘绑定的运行目录。', 'ArtifactStore', ['SYS-017'])
        self.run_id = str(uuid4())
        self.path = root / self.run_id
        self.path.mkdir(parents=True, exist_ok=False)

    def json(self, name, value):
        destination = self.path / name
        raw = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
        temporary = destination.with_suffix('.tmp')
        temporary.write_bytes(raw)
        temporary.replace(destination)
        return destination

    def manifest(self):
        return [{'artifact_id': entity('artifact'), 'type': p.suffix.lstrip('.'),
                 'path': str(p.relative_to(self.path)), 'bytes': p.stat().st_size, 'hash': sha256(p)}
                for p in sorted(self.path.rglob('*')) if p.is_file() and p.name != 'manifest.json']
