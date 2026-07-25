# syntax=docker/dockerfile:1.6
# =============================================================================
# AstroFinSentinelV5 — Web Dashboard (Dash on Flask + gunicorn)
# Multi-stage build, slim runtime.
# =============================================================================

ARG UV_VERSION=0.6.14

# uv provides the single source of truth for dependencies (pyproject.toml + uv.lock).
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
# Export the "web" extra (Dash/Flask/gunicorn + base runtime) from the locked
# resolution and install it. Replaces the former requirements-web.txt.
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-hashes --no-dev --extra web --no-emit-project \
        -o /tmp/requirements-web.txt \
    && pip install --upgrade pip \
    && pip install -r /tmp/requirements-web.txt

# -------- runtime --------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    GUNICORN_WORKERS=2 \
    GUNICORN_TIMEOUT=60

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -r -u 1001 dash && mkdir -p /app && chown -R dash:dash /app

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --chown=dash:dash web/ ./web/
COPY --chown=dash:dash orchestration/ ./orchestration/ 2>/dev/null || true
COPY --chown=dash:dash meta_rl/ ./meta_rl/ 2>/dev/null || true
COPY --chown=dash:dash knowledge/ ./knowledge/ 2>/dev/null || true
COPY --chown=dash:dash trading/ ./trading/ 2>/dev/null || true
COPY --chown=dash:dash analysis/ ./analysis/ 2>/dev/null || true
COPY --chown=dash:dash core/ ./core/ 2>/dev/null || true
COPY --chown=dash:dash data_provider.py ./
COPY --chown=dash:dash pyproject.toml ./

USER dash
EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8050/health || exit 1

# Production: gunicorn with wsgi.py shim. Dev override: python -m web.app
ENTRYPOINT ["gunicorn"]
CMD ["-w", "2", "-b", "0.0.0.0:8050", "--timeout", "60", "--access-logfile", "-", "web.app:server"]