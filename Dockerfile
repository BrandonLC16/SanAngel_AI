# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
FROM python:3.14-slim-bookworm@sha256:48b13b003dda20b16f9442b8475aa05fe21bf6579a8c881db92ffb4d8fd20f83 AS dependencies

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements-prod.lock /tmp/requirements-prod.lock
RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-compile --require-hashes --only-binary=:all: \
        -r /tmp/requirements-prod.lock \
    && find /opt/venv -type f -name '*.pyc' -delete \
    && find /opt/venv -depth -type d -name '__pycache__' -empty -delete

FROM python:3.14-slim-bookworm@sha256:48b13b003dda20b16f9442b8475aa05fe21bf6579a8c881db92ffb4d8fd20f83

ENV APP_ENV=production \
    APP_HOST=127.0.0.1 \
    APP_PORT=8000 \
    SECRETS_DIR=/run/secrets \
    PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 sanangel \
    && useradd --system --uid 10001 --gid sanangel --home-dir /app --no-create-home sanangel \
    && install -d -o 10001 -g 10001 /app \
    && install -d -m 0700 -o 10001 -g 10001 /data

COPY --from=dependencies /opt/venv /opt/venv
WORKDIR /app
COPY --chown=10001:10001 backend/app /app/backend/app
COPY --chown=10001:10001 backend/__init__.py /app/backend/__init__.py
COPY --chown=10001:10001 scripts/__init__.py scripts/run_backend.py scripts/container_healthcheck.py scripts/backup_sqlite.py scripts/restore_sqlite.py scripts/sqlite_validation.py /app/scripts/
COPY --chown=10001:10001 migrations /app/migrations
COPY --chown=10001:10001 alembic.ini /app/alembic.ini

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-m", "scripts.container_healthcheck"]
CMD ["python", "-m", "scripts.run_backend"]
