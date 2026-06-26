# syntax=docker/dockerfile:1.7
# Multi-stage production build for AstroFin Sentinel V5.
# Stage 1 (builder): resolve and install all Python wheels.
# Stage 2 (runtime): slim image, non-root user, minimal surface.

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
WORKDIR /build

# Build deps for psycopg2 / swisseph wheels.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip wheel \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt -r requirements-dev.txt


FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
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

# Copy requirements.txt for runtime dependency installation.
COPY requirements.txt .

# Install pre-built wheels from the builder stage.
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels \
        -r requirements.txt \
 && rm -rf /wheels

# Copy only the runtime tree (use .dockerignore to exclude .git, __pycache__, tests, etc.).
COPY --chown=appuser:appuser . /app

USER appuser

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8050/healthz || exit 1

CMD ["python", "-m", "web.app"]