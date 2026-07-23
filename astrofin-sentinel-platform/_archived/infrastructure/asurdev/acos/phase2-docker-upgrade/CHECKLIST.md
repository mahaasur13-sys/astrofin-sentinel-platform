# Phase-2 Dockerfile Standard — Checklist

Canonical, project-agnostic checklist for any production Dockerfile
in the AsurDev / atom-federation-os / AstroFin Sentinel ecosystem.
Every Dockerfile that runs in production must pass **all** of the
items below. The two reference images that define this standard:

- `AsurDev/acos/Dockerfile`            — stdlib-only service
- `atom-federation-os/cluster/node/Dockerfile` — gRPC + protobuf service

Use the checklist as the source of truth — if a Dockerfile
contradicts it, the Dockerfile is wrong, not the checklist.

---

## 1. Base image

- [ ] **Pinned major version**, no `:latest`, no floating tags
  - ✅ `FROM python:3.12-slim`
  - ❌ `FROM python:slim`, `FROM python:latest`, `FROM python:3.12`
- [ ] **`-slim` variant** unless a hard dep (torch, opencv) requires `python:3.12`
- [ ] If GPU is required: `nvidia/cuda:...-runtime-...` (cite the
      exact tag in a comment, e.g. `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04`)

## 2. Multi-stage build

- [ ] **Stage 1 named `deps`** (or `builder`) — installs build tooling
      and Python packages
- [ ] **Stage 2 named `runtime`** — copies installed packages and
      application source, drops build tools
- [ ] `pip install` runs only in `deps` and is copied via
      `COPY --from=deps /usr/local/lib/python3.12/site-packages …`
- [ ] No `apt-get install gcc g++ make` in the `runtime` stage
- [ ] No `pip install` in the `runtime` stage (unless a single line
      for runtime-only metadata, e.g. `pip install --no-deps ./pkg`)

## 3. tini for PID 1

- [ ] `tini` installed in the **`runtime` stage** (so it's present in
      the final image)
- [ ] `ENTRYPOINT` starts with `["/usr/bin/tini", "--", ...]`
- [ ] No `apt-get install tini` in the `deps` stage

## 4. Non-root user

- [ ] Both `groupadd` and `useradd` use **`--system`** flag
- [ ] **uid 1001, gid 1001** (consistent across the project)
- [ ] Shell is `/usr/sbin/nologin`
- [ ] `USER` directive switches to the non-root user before `ENTRYPOINT`
- [ ] All `COPY --chown=…` matches the same uid:gid

## 5. Bytecode compilation at build time

- [ ] `python -m compileall -q <packages>` runs in the `runtime` stage
      AFTER `COPY` and BEFORE `USER`
- [ ] This catches import errors at build time (fail-fast) and gives
      ~10–30 % faster cold-start vs. lazy `.pyc` generation

## 6. Pinned dependencies

- [ ] `requirements.txt` lives next to the Dockerfile (or in a stable
      parent dir; see below)
- [ ] Every line is pinned to **major.minor.patch** (`grpcio==1.80.0`,
      not `grpcio>=1.80`)
- [ ] No `pip install <pkg>` in the Dockerfile itself — always via
      `requirements.txt`
- [ ] Lockfile reference noted in a comment if one exists
      (`# regenerate via: pip freeze | grep …`)
- [ ] Wildcards (`pydantic==2*`) are not acceptable — must be
      `pydantic==2.x.y`

## 7. Healthcheck

- [ ] `HEALTHCHECK` directive present, NOT an inline `CMD` in
      `docker-compose.yml` only
- [ ] Delegates to a **standalone module** (`python -m pkg.healthcheck`),
      never `python -c "import sys; sys.exit(0)"`
- [ ] `--interval`, `--timeout`, `--start-period`, `--retries` all set
      to non-default values
- [ ] The healthcheck module exits 0 on success and 1 on failure —
      nothing else (no `print("ok")` only)

## 8. Environment

- [ ] `PYTHONUNBUFFERED=1` is set (so logs flush to stdout immediately)
- [ ] `PYTHONDONTWRITEBYTECODE=1` is set (don't litter the image with
      `__pycache__`)
- [ ] `PIP_DISABLE_PIP_VERSION_CHECK=1` and `PIP_NO_CACHE_DIR=1` in
      `deps` (builds are reproducible, no `/root/.cache/pip` bloat)
- [ ] A `*_HOME` env var (e.g. `ACOS_HOME=/app`, `ATOM_HOME=/app`)
      is set so paths stay explicit
- [ ] `PYTHONPATH=/app` set so the app can `import pkg` from
      `/app/pkg/`

## 9. Ports

- [ ] `EXPOSE` is **only** set for ports the container actually serves
- [ ] gRPC services do **not** `EXPOSE` — port varies per node, comes
      from `NODE_PORT` env var
- [ ] HTTP services expose a single well-known port (e.g. `8080`)

## 10. Labels

- [ ] At minimum: `org.opencontainers.image.title`,
      `org.opencontainers.image.description`,
      `org.opencontainers.image.source`
- [ ] License label set if the project has one
- [ ] No hardcoded commit SHA in the label (use `--label` at build time
      if needed)

## 11. `.dockerignore`

- [ ] `.git/`, `__pycache__/`, `.venv/`, `venv/`, `*.pyc`,
      `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- [ ] `tests/`, `docs/`, `*.md` (unless the app reads markdown at
      runtime, e.g. RAG)
- [ ] `build/`, `dist/`, `*.egg-info/`
- [ ] Large orchestration subtrees that aren't part of the runtime
      image (e.g. `orchestration/`, `meta_rl/` for a node image)

## 12. CI

- [ ] A workflow runs `hadolint <Dockerfile>` on PRs
- [ ] A workflow runs the static validator
      (`validate-docker.sh <Dockerfile>`) on PRs
- [ ] A workflow runs `docker compose config -q` on PRs that touch
      any `docker-compose*.yml`
- [ ] None of the CI jobs require a running Docker daemon —
      static validation only on PRs (the real `docker build`
      happens post-merge)

---

## Quick score

Count the items checked. The minimum bar for production:

| Score | Verdict |
|---|---|
| 40–44 | ✅ Reference-grade — accept |
| 30–39 | ⚠️  Acceptable with comment in PR explaining the gap |
| 20–29 | ❌ Block merge until fixed |
| <20   | 💥 Don't ship |

The two reference images (acos, cluster/node) score 44/44.
