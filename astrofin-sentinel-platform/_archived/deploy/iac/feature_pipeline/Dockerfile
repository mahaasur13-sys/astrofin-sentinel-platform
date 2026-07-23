# syntax=docker/dockerfile:1.6
# =============================================================================
# ACOS Feature Pipeline — multi-stage slim image.
# Long-running orchestrator: build features, embeddings, exports.
# =============================================================================

FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements-features.txt ./
RUN pip install --upgrade pip && pip install -r requirements-features.txt

# -------- runtime --------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -r -u 1001 features && mkdir -p /app && chown -R features:features /app

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --chown=features:features feature_pipeline/ ./feature_pipeline/
COPY --chown=features:features acos/ ./acos/ 2>/dev/null || true
COPY --chown=features:features pyproject.toml ./

USER features
EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8090/health || exit 1

# Default: continuous feature pipeline. Override CMD for one-shot modes:
#   --nodes <n>     compute a single batch
#   --validate-registry
#   --export-csv --output <path>
ENTRYPOINT ["python3", "-m", "feature_pipeline.pipeline"]
CMD ["--continuous", "--interval", "60"]
