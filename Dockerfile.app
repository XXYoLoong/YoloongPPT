FROM python:3.13.16-slim-bookworm@sha256:f040863673aea2570c3ff6a5c3fb4c673a016cbc5375005ad145915922b6b78a

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1 \
    PYTHONPATH=/workspace/src YOLOONGPPT_ROOT=/workspace \
    TMPDIR=/runtime/tmp TEMP=/runtime/tmp TMP=/runtime/tmp

COPY requirements.lock /opt/yoloongppt/requirements.lock
RUN python -m pip install --disable-pip-version-check --no-cache-dir --require-hashes \
    -r /opt/yoloongppt/requirements.lock

USER 10001:10001
WORKDIR /workspace
CMD ["python", "-m", "uvicorn", "yoloongppt.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
