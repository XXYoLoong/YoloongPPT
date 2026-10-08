#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export HOME=/artifacts/home
export TMPDIR=/artifacts/tmp
export UV_CACHE_DIR=/artifacts/cache/uv
export npm_config_cache=/artifacts/cache/npm
export PLAYWRIGHT_BROWSERS_PATH=/artifacts/cache/ms-playwright
mkdir -p "$HOME" "$TMPDIR" "$UV_CACHE_DIR" "$npm_config_cache" "$PLAYWRIGHT_BROWSERS_PATH" /artifacts/main-skill
cp -a /research/skills/pptagent/. /artifacts/main-skill/
apt-get update
apt-get install --no-install-recommends -y build-essential python3 python3-dev python3-pip python3-venv nodejs npm libreoffice-impress
python3 -m pip install --break-system-packages --no-cache-dir uv
uv venv --clear --python /usr/bin/python3 /artifacts/main-skill/.venv
uv pip install --python /artifacts/main-skill/.venv/bin/python -r /artifacts/main-skill/requirements.txt
/artifacts/main-skill/.venv/bin/python -m playwright install --with-deps chromium
cd /artifacts/main-skill
export PYTHONPATH="/artifacts/main-skill${PYTHONPATH:+:$PYTHONPATH}"
/artifacts/main-skill/.venv/bin/python scripts/install.py --client codex --home "$HOME"
bash /artifacts/post-check.sh