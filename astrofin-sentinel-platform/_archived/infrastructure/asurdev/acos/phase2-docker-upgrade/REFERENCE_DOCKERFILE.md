# Reference Dockerfile — Phase-2 Standard

This file documents the canonical Dockerfile shape that **every**
Phase-2 service in this project follows. Do **not** copy this file
verbatim — instead, use it as a template and adapt:

1. Replace `acos` with your service / image name.
2. Replace `COPY acos/ acos_cli.py acos.py` with the directory list
   your service actually needs at runtime.
3. Replace `requirements.txt` contents with your pinned deps.
4. Replace the `CMD` line with your service's actual entry point.

Both reference images in this project follow this template:

- `AsurDev/acos/Dockerfile` — stdlib-only service, slim Dockerfile,
  healthcheck via `python -m acos_cli`.
- `atom-federation-os/cluster/node/Dockerfile` — gRPC + protobuf
  service, healthcheck via `python -m cluster.node.healthcheck`.

---

## Canonical template

```dockerfile
# =============================================================================
# <SERVICE NAME> — <one-line purpose>
#
# Multi-stage, slim, non-root, reproducible — Phase-2 standard.
#
# Build:  docker build -t <image>:<tag> -f <path/to/Dockerfile> <build-context>
#         (build context is normally the repo root, never the Dockerfile dir
#          unless your service is self-contained in that directory)
# Run:    docker run --rm <image>:<tag>            # default CMD
#         docker run --rm <image>:<tag> <args>     # override CMD
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
COPY <path/to/requirements.txt> ./requirements.txt
RUN pip install -r requirements.txt


# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    <SERVICE>_HOME=/app \
    PYTHONPATH=/app

# tini → clean PID 1, signal forwarding, zombie reaping
# ca-certificates → TLS verify when the service reaches the outside world
# curl → used by HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 <service> \
    && useradd  --system --uid 1001 --gid <service> --create-home --shell /usr/sbin/nologin <service>

# Bring in installed Python packages from the deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin                       /usr/local/bin

WORKDIR /app

# Copy only what the service needs at runtime. The .dockerignore keeps
# tests, docs, .venv/, build/, dist/ and unrelated subtrees out of the
# build context — keeps the final image lean and the build cache stable.
COPY <src-dir-1>/    ./<src-dir-1>/
COPY <src-dir-2>/    ./<src-dir-2>/
# If you have a top-level entry script:
COPY <entry-script>  ./<entry-script>

# Compile bytecode at build time → smaller startup, surfaces import errors
# at build, not at `docker run`.
RUN python -m compileall -q <src-dir-1> <src-dir-2> <entry-script>

# Drop privileges
USER <service>

# tini → real entrypoint. The default subcommand should be a read-only
# smoke test that exits 0 (e.g. `invariants`, `healthcheck`).
ENTRYPOINT ["/usr/bin/tini", "--", "python", "-m", "<entry-module>"]
CMD ["<default-subcommand-or-args>"]

# Liveness probe. Delegates to a small standalone module
# (`<service>.healthcheck` or `<service> <subcommand>`), NOT to an
# inline `python -c "import sys; sys.exit(0)"`. The module must exit
# 0 only when the service is actually serving traffic.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "-m", "<entry-module>", "<healthcheck-subcommand>"]

# HTTP / gRPC ports — set only if your service has a fixed, well-known port.
# Variable per-node ports (e.g. gRPC per node-a/b/c) MUST NOT be EXPOSE'd.
# EXPOSE 8080

LABEL org.opencontainers.image.title="<service>" \
      org.opencontainers.image.description="<one-line description>" \
      org.opencontainers.image.source="<git-url>" \
      org.opencontainers.image.licenses="<license>"
```

---

## What each block does and why

### Stage 1 (`deps`)

The `deps` stage runs once and is **invalidated only by changes to
`requirements.txt`**. As long as the deps don't change, this stage
is cached by Docker and rebuilds in seconds — even if the rest of
the source code changes completely. This is the single biggest
build-time optimization in the whole template.

`tini` is installed here too (not just runtime) so the `apt-get`
update is shared — saves ~200 MB on the cache.

### Stage 2 (`runtime`)

The runtime stage starts from a **clean `python:3.12-slim`** and
copies in only the artifacts that ship:

- Pre-installed Python packages (via `COPY --from=deps` of
  `site-packages` and `bin/`).
- Application source (via `COPY` of directories the service
  actually needs).
- Bytecode (`compileall` runs here, after `COPY`, before `USER`).

There is **no build tooling** (`gcc`, `make`, `pip`) in the final
image. This is what makes it slim — the final image is usually
~150 MB instead of ~600 MB.

### `tini` for PID 1

Linux containers run their `ENTRYPOINT` as PID 1. Without an init
system, PID 1 has to handle signals itself — and Python apps
usually do this poorly (they don't reap zombies, they don't
forward signals to child processes, and `docker stop` ends up
sending SIGKILL after 10 s instead of SIGTERM-then-cleanup).

`tini` is a 30 KB init binary that does exactly one thing well:
handle signals and reap zombies. It is **always** present in
the runtime stage, and `ENTRYPOINT` starts with it.

### Non-root uid 1001

Every service in this project uses **uid 1001** by convention.
This makes it possible to:

- Run a single image across multiple services without uid collisions.
- Mount host volumes knowing the container user matches the host
  user (when the host user is also uid 1001).
- Audit `docker top` output by uid and immediately know which
  service is which.

`--system` makes the user/group appear in `/etc/passwd` without
a home directory password / aging config — it is the right choice
for service accounts.

### `compileall` at build time

Python ships source files in the image, then creates `.pyc` on
first import. The first `import pkg` is therefore slow AND only
catches import errors when a request actually triggers the import.

`python -m compileall` runs the same compilation at build time:

- Cold-start is ~10–30 % faster.
- Broken imports fail the build, not the request.

### `HEALTHCHECK` delegates to a module

The `HEALTHCHECK` directive is **not** an inline `python -c` snippet
because:

1. Inline one-liners can't import the project's own modules
   (sys.path is whatever the inline script sets).
2. They tend to be tautological (`exit 0`) — telling Docker the
   container is alive when it might not be.
3. They can't be tested with `python -m <pkg>.healthcheck` from
   `docker exec` — duplicating logic between Dockerfile and
   `docker-compose.yml`.

The standalone healthcheck module:

- Lives next to the entry module (`<pkg>.healthcheck`).
- Has **no deps on the rest of the codebase** (or only on
  runtime-critical modules like `grpc`).
- Exits 0 on success, 1 on failure, with a single-line
  diagnostic on stdout so `docker inspect` and Loki capture
  WHY it failed.

---

## Examples of compliant images

### `AsurDev/acos/Dockerfile` (stdlib-only)

```dockerfile
FROM python:3.12-slim AS deps
RUN apt-get update && apt-get install -y --no-install-recommends curl tini ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /install
COPY acos/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 \
    ACOS_HOME=/app PYTHONPATH=/app ACOS_HTTP_PORT=8080
RUN apt-get update && apt-get install -y --no-install-recommends tini curl ca-certificates && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 acos \
    && useradd  --system --uid 1001 --gid acos --create-home --shell /usr/sbin/nologin acos
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin                       /usr/local/bin
WORKDIR /app
COPY acos/   ./acos/
COPY acos_cli.py    ./acos_cli.py
COPY acos.py        ./acos.py
COPY l9_ebl/        ./l9_ebl/
COPY ete/           ./ete/
COPY l10_self_healing/ ./l10_self_healing/
COPY constraint_compiler/ ./constraint_compiler/
RUN python -m compileall -q acos l9_ebl ete l10_self_healing constraint_compiler acos_cli.py acos.py
USER acos
ENTRYPOINT ["/usr/bin/tini", "--", "python", "-m", "acos_cli"]
CMD ["invariants"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -m acos_cli invariants || exit 1
EXPOSE 8080
LABEL org.opencontainers.image.title="ACOS" \
      org.opencontainers.image.description="Autonomous Constrained Optimization System — L0–L11 + EBL + ETE" \
      org.opencontainers.image.source="https://github.com/mahaasur13-sys/AsurDev" \
      org.opencontainers.image.licenses="Apache-2.0"
```

### `atom-federation-os/cluster/node/Dockerfile` (gRPC + protobuf)

```dockerfile
FROM python:3.12-slim AS deps
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends curl tini ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /install
COPY cluster/node/requirements.txt ./requirements.txt
RUN pip install --no-deps -r requirements.txt && pip install grpcio==1.80.0 protobuf==6.33.6

FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 \
    ATOM_HOME=/app PYTHONPATH=/app
RUN apt-get update && apt-get install -y --no-install-recommends tini curl ca-certificates && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 atom \
    && useradd  --system --uid 1001 --gid atom --create-home --shell /usr/sbin/nologin atom
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin                       /usr/local/bin
WORKDIR /app
COPY cluster/   ./cluster/
COPY proto/     ./proto/
COPY sbs/       ./sbs/
RUN python -m compileall -q cluster sbs proto
USER atom
ENTRYPOINT ["/usr/bin/tini", "--", "python", "cluster/node/entrypoint.py"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "-m", "cluster.node.healthcheck"]
LABEL org.opencontainers.image.title="atom-federation-os node" \
      org.opencontainers.image.description="ATOM Federation OS — distributed cluster node (gRPC + DRL + SBS + health)" \
      org.opencontainers.image.source="https://github.com/mahaasur13-sys/atom-federation-os" \
      org.opencontainers.image.licenses="MIT"
```

---

## Anti-patterns (do **not** copy these)

❌ `FROM python:latest` — non-reproducible, breaks production on rebuild.

❌ `RUN pip install flask requests numpy pandas` — unpinned, no lockfile,
   different versions every build.

❌ `COPY . .` — copies tests, `.git/`, `.venv/`, docs into the image,
   bloats it by 100+ MB.

❌ `USER root` (or no `USER` at all) — runs as root in production,
   increases blast radius of any compromise.

❌ `ENTRYPOINT ["python", "app.py"]` — Python as PID 1, signals lost,
   zombies accumulate.

❌ `HEALTHCHECK CMD python -c "import sys; sys.exit(0)"` — always
   healthy, even when the service is broken. Useless.

❌ `EXPOSE 8080 50051 50052 50053` — fixed port mapping is wrong for
   services where the port is per-instance (gRPC clusters).

❌ Inline `CMD ["--host", "0.0.0.0", "--port", "8080"]` baked into
   the image — prevents the same image from running on different
   ports in different deployments.
