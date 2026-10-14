from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def render_current(
    workspace: Path, render: dict[str, Any], inputs: dict[str, Any]
) -> bool:
    images = render.get("images", {})
    return (
        render.get("inputs") == inputs
        and bool(images)
        and all(
            (workspace / name).is_file() and sha256(workspace / name) == digest
            for name, digest in images.items()
        )
    )
