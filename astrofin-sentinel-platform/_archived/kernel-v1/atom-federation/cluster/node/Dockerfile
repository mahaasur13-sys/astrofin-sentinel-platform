# =============================================================================
# ATOM Federation OS — cluster node
#
# Multi-stage, slim, non-root, reproducible — same standard as AsurDev/acos.
#
# Build:  docker build -t atom-node:local -f cluster/node/Dockerfile .
#         (MUST be run from the repository root — the Dockerfile references
#          ./requirements.txt, ./cluster/, ./proto/, ./sbs/ which only exist
#          relative to repo root, not relative to cluster/node/.)
# Run:    docker run --rm \
#             -e NODE_ID=node-a \
#             -e PEERS=node-b,node-c \
#             -e NODE_PORT=50051 \
#             atom-node:local
# Compose: see docker-compose.yml (3-node cluster: atom-node-a/b/c).
# Health:  docker inspect --format='{{json .State.Health}}' <container>
# =============================================================================

# ── Stage 1: dependency installer (cached independently of source) ───────────
FROM python:3.12-slim AS deps

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# curl is needed for the HEALTHCHECK (kept in the final image too — small cost,
# large benefit: stable, no `wget`/`python -c` tricks across distros).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY cluster/node/requirements.txt ./requirements.txt
RUN pip install --no-deps -r requirements.txt \
    && pip install grpcio==1.80.0 protobuf==6.33.6


# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    ATOM_HOME=/app \
    PYTHONPATH=/app

# tini → clean PID 1, signal forwarding, zombie reaping
# ca-certificates → TLS verify when the node reaches the cluster mesh
# curl → used by HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 atom \
    && useradd  --system --uid 1001 --gid atom --create-home --shell /usr/sbin/nologin atom

# Bring in installed Python packages from the deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin                       /usr/local/bin

WORKDIR /app

# Copy only what the node runtime needs. The .dockerignore keeps tests,
# docs, .venv/, build/, dist/ and large orchestration subtrees out of the
# build context — keeps the final image lean and the build cache stable.
#
# IMPORTANT: build context MUST be the repository root (`.`). The paths
# below resolve relative to that root, not to cluster/node/.
COPY cluster/   ./cluster/
COPY proto/     ./proto/
COPY sbs/       ./sbs/

# Compile bytecode at build time → smaller startup, surfaces import errors
# at build, not at `docker run`.
RUN python -m compileall -q cluster sbs proto

# Drop privileges
USER atom

# tini → cluster/node/entrypoint.py.
# entrypoint.py reads NODE_ID / PEERS / NODE_PORT from the environment
# (see docker-compose.yml) and keeps the gRPC server alive.
ENTRYPOINT ["/usr/bin/tini", "--", "python", "cluster/node/entrypoint.py"]

# Liveness probe. Delegates to a small standalone module
# (cluster/node/healthcheck.py) instead of an inline `python -c` one-liner —
# same pattern as acos using `python -m acos_cli` for liveness. The module
# performs a real gRPC connectivity check (channel state on
# 127.0.0.1:NODE_PORT) with a /proc/net/tcp LISTEN fallback, and a module-
# import smoke layer. Exits 0 only if the gRPC server is actually accepting
# handshakes OR the port is still bound (degraded-but-alive).
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "-m", "cluster.node.healthcheck"]

# gRPC port is provided per-node by the NODE_PORT env var (see compose).
# We do not pin EXPOSE here to keep the image reusable across node-a/b/c.

LABEL org.opencontainers.image.title="atom-federation-os node" \
      org.opencontainers.image.description="ATOM Federation OS — distributed cluster node (gRPC + DRL + SBS + health)" \
      org.opencontainers.image.source="https://github.com/mahaasur13-sys/atom-federation-os" \
      org.opencontainers.image.licenses="MIT"
