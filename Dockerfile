# syntax=docker/dockerfile:1.7
# Multi-stage production build for AstroFin Sentinel V5.
# Stage 1 (builder): resolve and install all Python wheels via uv.
# Stage 2 (runtime): slim image, non-root user, minimal surface.
#
# This Dockerfile uses uv for dependency management. The lockfile (uv.lock)
# is the single source of truth for transitive resolution. See ADR-0010.

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.6.14

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
# Pure multi-stage importer; no runtime cost.

FROM python:${PYTHON_VERSION}-slim AS builder
WORKDIR /build

# Build deps for psycopg2 / swisseph wheels.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy uv from official image (smaller than installing it ourselves).
COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv

# Copy project metadata + lockfile first for better Docker layer caching.
COPY pyproject.toml uv.lock ./

# Export the lock-resolved wheel set so the runtime stage can install offline.
RUN uv export --frozen --no-hashes --format requirements-txt \
        --extra dev \
        -o /tmp/requirements.txt \
 && uv pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt


FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    PORT=8050

# OS-level runtime deps only.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
 && rm -rf /var/lib/apt/lists/*

# Non-root user.
RUN groupadd --system --gid 1001 appuser \
 && useradd  --system --uid 1001 --gid appuser \
              --home-dir /app --shell /usr/sbin/nologin \
              appuser

WORKDIR /app

# Install pre-built wheels from the builder stage. --no-deps is safe because
# /wheels already contains every transitive package (uv export + uv pip wheel).
COPY --from=builder /wheels /wheels
COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
        -r /tmp/requirements.txt \
 && rm -rf /wheels /tmp/requirements.txt

# Copy only the runtime tree (use .dockerignore to exclude .git, __pycache__, tests, etc.).
COPY --chown=appuser:appuser . /app

USER appuser

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8050/healthz || exit 1

CMD ["python", "-m", "web.app"]
