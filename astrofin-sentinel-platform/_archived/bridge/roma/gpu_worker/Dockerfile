# syntax=docker/dockerfile:1.6
# =============================================================================
# ROMA Execution Bridge — GPU Worker
# Multi-stage build, slim runtime image, NVIDIA CUDA 12.6 base.
# Designed for execution on a host with nvidia-container-toolkit.
# =============================================================================

ARG PYTHON_VERSION=3.12
ARG CUDA_VERSION=12.6.3

# -------- builder stage --------
FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu24.04 AS builder
ARG PYTHON_VERSION
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} python3-pip python3-venv \
        build-essential gcc \
    && ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements-worker.txt ./
RUN pip install --upgrade pip && pip install -r requirements-worker.txt

# -------- runtime stage --------
FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu24.04 AS runtime
ARG PYTHON_VERSION
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    GPU_WORKER_HOST=0.0.0.0 \
    GPU_WORKER_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} python3-pip \
        libgomp1 curl ca-certificates \
    && ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -r -u 1001 roma && mkdir -p /app && chown -R roma:roma /app

WORKDIR /app
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/dist-packages /usr/local/lib/python${PYTHON_VERSION}/dist-packages
COPY --chown=roma:roma gpu_worker/ ./gpu_worker/

USER roma
EXPOSE 8000 8001 8002 8003

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Default: launch primary FastAPI worker (uvicorn) via server.py
# Override with `docker run ... <module>` for lock-manager/observability/etc.
ENTRYPOINT ["python3", "-m", "uvicorn"]
CMD ["gpu_worker.server:app", "--host", "0.0.0.0", "--port", "8000"]
