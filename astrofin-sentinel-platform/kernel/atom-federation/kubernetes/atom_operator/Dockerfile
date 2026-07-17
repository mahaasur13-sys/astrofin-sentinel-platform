# =============================================================================
# ATOM Operator — production Dockerfile (Phase 2.A standard)
# Mirrors AsurDev/acos/Dockerfile conventions:
#   - multi-stage build (builder -> runtime)
#   - python:3.12-slim base
#   - non-root user (uid 1001, /usr/sbin/nologin)
#   - tini as PID 1 (signal handling, zombie reaping)
#   - bytecode compilation at build time (faster startup)
#   - HEALTHCHECK against /healthz on port 8080
# =============================================================================

# ---- Stage 1: builder ---------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build deps into an isolated prefix so we can copy them cleanly.
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# ---- Stage 2: runtime ---------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/install/lib/python3.12/site-packages:/app"

# tini = minimal init, reaps zombies, forwards signals (PID 1 in the runtime stage)
ARG TINI_VERSION=v0.19.0
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*; \
    curl -fsSL -o /usr/local/bin/tini \
        "https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-static"; \
    chmod +x /usr/local/bin/tini; \
    tini --version || true

# Non-root user: matches AsurDev/acos convention (uid 1001, no shell).
RUN groupadd --system --gid 1001 atom \
    && useradd  --system --uid 1001 --gid atom \
                --home-dir /app --shell /usr/sbin/nologin \
                atom

WORKDIR /app

# Bring in installed dependencies from builder.
COPY --from=builder /install /install

# Copy operator source. Layout is /app/atom_operator/*.py so `python -m atom_operator.main` works.
COPY --chown=atom:atom . /app/atom_operator/

# Pre-compile bytecode — first start in-cluster is measurably faster.
RUN python -m compileall -q /install/lib/python3.12/site-packages /app/atom_operator

USER atom:atom

# Expose metrics + health ports (matches Helm service definitions).
EXPOSE 9464 8080

# Healthcheck hits the in-process /healthz endpoint launched by main.py.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).status == 200 else 1)"

ENTRYPOINT ["/usr/local/bin/tini", "--", "python", "-m", "atom_operator.main"]