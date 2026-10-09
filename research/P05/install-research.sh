#!/bin/bash
set -eu
cd /app
export HOME=/scratch/home TMPDIR=/scratch/tmp UV_CACHE_DIR=/scratch/uv-cache npm_config_cache=/scratch/npm-cache
mkdir -p "$HOME" "$TMPDIR" /evidence/validation /scratch/venv
python3 --version
node --version
npm --version
sha256sum package-lock.json > /evidence/validation/npm-lock-before.txt
npm install
sha256sum package-lock.json > /evidence/validation/npm-lock-after.txt
uv venv --python /usr/bin/python3 /scratch/venv
uv pip install --python /scratch/venv/bin/python . -r requirements.txt
uv pip check --python /scratch/venv/bin/python
uv pip freeze --python /scratch/venv/bin/python > /evidence/validation/python-freeze.txt
npm ls --all --json > /evidence/validation/npm-tree.json
printf 'P05 isolated setup completed\n'
