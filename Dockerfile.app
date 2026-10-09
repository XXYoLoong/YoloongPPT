FROM python:3.13.16-slim-bookworm@sha256:f040863673aea2570c3ff6a5c3fb4c673a016cbc5375005ad145915922b6b78a

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1 \
    PYTHONPATH=/workspace/src YOLOONGPPT_ROOT=/workspace \
    TMPDIR=/runtime/tmp TEMP=/runtime/tmp TMP=/runtime/tmp

# Render in the project container. Package versions are the observed Debian
# bookworm candidates; the complete installed inventory is retained in image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-impress=4:7.4.7-1+deb12u14 \
    poppler-utils=22.12.0-2+deb12u3 \
    fonts-noto-cjk=1:20220127+repack1-1 \
    && dpkg-query -W > /opt/yoloongppt-system-packages.txt \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /opt/yoloongppt/requirements.lock
RUN python -m pip install --disable-pip-version-check --no-cache-dir --require-hashes \
    -r /opt/yoloongppt/requirements.lock

USER 10001:10001
WORKDIR /workspace
CMD ["python", "-m", "uvicorn", "yoloongppt.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
