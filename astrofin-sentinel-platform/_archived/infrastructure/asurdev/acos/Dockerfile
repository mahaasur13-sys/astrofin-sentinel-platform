# =============================================================================
# ACOS — Autonomous Constrained Optimization System
# Multi-stage, slim, non-root, reproducible.
#
# Build:  docker build -t acos:local -f acos/Dockerfile .
# Run:    docker run --rm acos:local                          # invariants check
#         docker run --rm acos:local validate                  # contract check
#         docker run --rm acos:local traces                    # list traces
#         docker run --rm acos:local submit --job-type agent   # submit a job
# Health: docker inspect --format='{{json .State.Health}}' <container>
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
COPY acos/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt


# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    ACOS_HOME=/app \
    PYTHONPATH=/app \
    ACOS_HTTP_PORT=8080

# tini → clean PID 1, signal forwarding, zombie reaping
# ca-certificates → TLS verify when acos reaches out to webhooks / OCI
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 acos \
    && useradd  --system --uid 1001 --gid acos --create-home --shell /usr/sbin/nologin acos

# Bring in installed Python packages from the deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin                       /usr/local/bin

WORKDIR /app

# Copy only what ACOS needs at runtime. The .dockerignore keeps tests, docs,
# and `.venv/` out of the build context.
COPY acos/   ./acos/
COPY acos_cli.py    ./acos_cli.py
COPY acos.py        ./acos.py
COPY l9_ebl/        ./l9_ebl/
COPY ete/           ./ete/
COPY l10_self_healing/ ./l10_self_healing/
COPY constraint_compiler/ ./constraint_compiler/

# Compile bytecode at build time → smaller startup, surfaces import errors
# at build, not at `docker run`.
RUN python -m compileall -q acos l9_ebl ete l10_self_healing constraint_compiler acos_cli.py acos.py

# Drop privileges
USER acos

# tini → acos_cli. Default subcommand is `invariants` (read-only smoke test);
# override with `docker run acos <subcommand>` — see header comment.
ENTRYPOINT ["/usr/bin/tini", "--", "python", "-m", "acos_cli"]
CMD ["invariants"]

# ACOS health: contracts + invariants check (read-only, ~1s). Exits 0 only if
# every L11 invariant passes — gives a real liveness signal without spinning
# up a full HTTP server.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -m acos_cli invariants || exit 1

# 8080 is reserved for a future HTTP /metrics endpoint — kept here so
# compose / k8s port mappings stay stable.
EXPOSE 8080

LABEL org.opencontainers.image.title="ACOS" \
      org.opencontainers.image.description="Autonomous Constrained Optimization System — L0–L11 + EBL + ETE" \
      org.opencontainers.image.source="https://github.com/mahaasur13-sys/AsurDev" \
      org.opencontainers.image.licenses="Apache-2.0"
