#!/usr/bin/env bash
set -euo pipefail
export HOME=/artifacts/home
export TMPDIR=/artifacts/tmp
export PLAYWRIGHT_BROWSERS_PATH=/artifacts/cache/ms-playwright
BASE=/artifacts/main-skill
uv pip check --python "$BASE/.venv/bin/python"
uv pip freeze --python "$BASE/.venv/bin/python" | sort > /artifacts/packages-freeze.txt
"$BASE/.venv/bin/python" "$BASE/scripts/pptagent.py" doctor --workspace "$BASE" > /artifacts/official-doctor.json
"$BASE/.venv/bin/python" - <<'PY'
import json
from pathlib import Path
result=json.loads(Path('/artifacts/official-doctor.json').read_text(encoding='utf-8'))
if not result.get('ok') or result.get('failed'):
    raise SystemExit('PPTAgent official doctor failed: '+json.dumps(result,ensure_ascii=False))
print('official_doctor=passed')
print('official_doctor_check_count='+str(len(result.get('checks',{}))))
print('official_doctor_mode='+str(result.get('mode')))
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    page.set_content('<title>P02 isolated browser smoke</title>')
    print('browser_title='+page.title())
    browser.close()
PY
if env | cut -d= -f1 | grep -Eiq 'ATRIA|VISUAL_API'; then
  provider_vars='present (values withheld)'
else
  provider_vars='none forwarded/configured in this container run'
fi
{
  echo "upstream_commit=$(git -C /research rev-parse HEAD)"
  echo 'base_image=yoloongppt-workspace (project Debian bookworm-slim image)'
  echo "python=$(python3 --version 2>&1) (container observation only; not product selection)"
  echo "uv=$(uv --version)"
  echo "node=$(node --version)"
  echo "npm=$(npm --version)"
  echo "libreoffice=$(libreoffice --version 2>&1 | head -1)"
  echo "playwright=$($BASE/.venv/bin/python -m playwright --version)"
  echo "npm_lock_sha256=$(sha256sum $BASE/package-lock.json | cut -d' ' -f1)"
  echo "requirements_sha256=$(sha256sum $BASE/requirements.txt | cut -d' ' -f1)"
  echo "python_package_count=$(wc -l < /artifacts/packages-freeze.txt)"
  echo 'uv_pip_check=passed'
  echo 'official_quickstart_doctor=passed'
  echo 'chromium_headless_smoke=passed'
  echo "provider_credential_variable_names=$provider_vars"
  echo 'skill_registration=/artifacts/home/.agents/skills/pptagent -> /artifacts/main-skill (container-local)'
  echo 'npm_install_audit=upstream install emitted 6 high severity findings; not auto-fixed'
} > /artifacts/environment.txt
cat /artifacts/environment.txt