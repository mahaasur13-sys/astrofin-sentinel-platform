# Repository Layout

> **TL;DR for new agents/developers**: this is a **monorepo hub** for the
> `astrofin-sentinel-platform` (trading/orchestration platform). Most "directories"
> at the top level are **either git submodules, vendored legacy snapshots, or
> runtime artifacts**. The **active Python application** lives in the root
> (`core/`, `agents/`, `orchestration/`, `trading/`, `meta_rl/`, `web/`, `tests/`,
> `docs/`). The four huge `astrofin-sentinel-platform*` and `astrofin-monorepo*`
> directories are **historical clones** — do not edit them, work in the root.
> When in doubt, read `AGENTS.md` and `docs/PROJECT_SPEC.md`.

---

## Overview

AstroFin Sentinel is a multi-agent trading / orchestration platform: agents
collect market data, produce signals, route them through a meta-RL layer, and
execute trades. The repo is a **hub repository**: the production source code
lives at the root, and several satellite services (cluster IaC, ML engine,
execution bridge, sentinel v5, atom federation) are pulled in as **git
submodules**. There is no single `main.py` — entry points are scattered
(`run_sentinel_v5`, `web/app.py`, `orchestration/`, integrations/`*`).

Canonical remote: `https://github.com/mahaasur13-sys/astrofin-sentinel-platform.git`.
This `master` branch is the source of truth (currently points at `7f7e32a`).

---

## Current Active Structure

### Root (the production application)

| Path                     | Purpose                                                              |
| ------------------------ | -------------------------------------------------------------------- |
| `core/`                  | Domain primitives: signal models, exchange adapters, data loaders    |
| `agents/`                | Individual agent implementations (CompromiseAgent, SynthesisAgent, …)|
| `orchestration/`         | Top-level orchestrators (sentinel v5, multi-agent system)            |
| `meta_rl/`               | Meta reinforcement learning layer, persistence, A/B testing          |
| `trading/`               | Execution layer: orders, risk, safety guards, TWAP                   |
| `backtest/`              | Backtesting engine + historical data DB (`results.db`)               |
| `web/`                   | FastAPI dashboard (`web/app.py`)                                     |
| `tests/`                 | Pytest suite; has root `conftest.py` with global fixtures/skip list  |
| `docs/`                  | Markdown docs: `PROJECT_SPEC`, `PRD`, `SECURITY`, `KNOWN_ISSUES`, …  |
| `deploy/`                | Docker, K8s manifests, supervisord, monitoring endpoints             |
| `db/`, `data/`, `data_room/` | Runtime databases and cached data (mostly gitignored)            |
| `migrations/`, `migrations_postgres/` | Schema migrations                              |
| `integrations/`          | Third-party integrations: GitAgent, etc.                             |
| `schema/`, `scripts/`, `tools/` | Schemas, utility scripts, internal tools                     |
| `security/`              | Security middleware, auth helpers, threat-model notes                |
| `observability/`         | OpenTelemetry tracing, structured logging                            |
| `models/`, `training/`, `gpu_worker/` | ML model storage + training stack (cuda paths)        |
| `feature_pipeline/`, `ml_engine/`, `sdlc_os/` | ML platform pieces                       |
| `knowledge/`             | RAG knowledge base for agents                                        |
| `config/`                | Configuration loaders, profiles, feature flags                       |
| `keys/`                  | **JWT keys, secrets** (gitignored) — never commit                    |
| `astrofin_sentinel_v5.egg-info/` | Setuptools metadata (auto-generated)                        |
| `atomos_pkg/`, `atom-core/` | ATOM ecosystem core (different from `atom-federation-os/`)         |
| `snapshots/`, `graphify-out/` | Generated artifacts (graphify output, snapshot exports)          |

### Key files at root

- `AGENTS.md` — main agent/orientation doc (read this first)
- `PRD.md` — product requirements
- `PROJECT_SPEC.md` — technical specification
- `CHANGELOG.md`, `CHANGELOG_SESSION.md` — change history
- `pyproject.toml` + `uv.lock` — Python deps (project uses `uv`)
- `.pre-commit-config.yaml`, `.gitleaks.toml`, `.secrets.baseline` — security gates
- `.gitmodules` — submodule list
- `.gitignore` — see "Ignored" section below
- `AUDIT_*.md` — dated audit reports (keep for history)
- `.coderabbit.yaml`, `.cursorrules` — code-review tooling config

### CI / GitHub

`.github/workflows/` contains **10 GitHub Actions workflows** running:
lint (ruff, flake8, mypy), unit + integration tests (pytest, coverage),
security scans (bandit, gitleaks, pip-audit), Docker build, and K8s
deployment dry-runs. Recent CI is on green for `master`; known issues are
tracked in `docs/KNOWN_ISSUES.md` (see KI-119 … KI-126).

---

## Submodules

Five git submodules (declared in `.gitmodules`):

| Path                       | URL                                                                        | Branch    | Purpose                                |
| -------------------------- | -------------------------------------------------------------------------- | --------- | -------------------------------------- |
| `AsurDev/`                 | github.com/mahaasur13-sys/AsurDev.git                                      | `master`  | Internal dev tooling & multi-agent     |
| `home-cluster-iac/`        | github.com/mahaasur13-sys/home-cluster-iac.git                             | `master`  | K8s / cluster infrastructure as code   |
| `roma-execution-bridge/`   | github.com/mahaasur13-sys/roma-execution-bridge.git                        | `master`  | Execution bridge (order routing)       |
| `astrofin-sentinel-v5/`    | github.com/mahaasur13-sys/astrofin-sentinel-v5.git                         | `main`    | Sentinel v5 (older release)            |
| `atom-federation-os/`      | github.com/mahaasur13-sys/atom-federation-os.git                           | `master`  | ATOM Federation OS (orchestration)     |

> ⚠️ These appear as **untracked** in `git status` because they aren't checked
> out in this workspace at the moment. The `.gitmodules` file is committed
> so the structure is reproducible. To populate them: `git submodule update --init`.
> Don't commit their contents into the root repo — that's a submodule antipattern.

---

## Vendored legacy snapshots (do NOT edit)

The following directories at the top level are **standalone git-tracked copies
of the platform from earlier points in time**. They are kept for archaeology
and emergency rollback. The active development happens at the **root** — never
edit these in place.

| Path                                | Size  | Status                                                    |
| ----------------------------------- | ----- | --------------------------------------------------------- |
| `astrofin-sentinel-platform/`       | 154 M | Earliest baseline; superseded by root                     |
| `astrofin-sentinel-platform-fix/`   | 185 M | KI-125a / PR #150 branch state (post-cleanup)             |
| `astrofin-sentinel-platform-new/`   |  61 M | Mid-2026 re-organisation snapshot                         |
| `astrofin-monorepo/`                |  16 M | Pre-submodule monorepo experiment                         |
| `astrofin-federation-stack/`        |  13 M | Federation stack prototype                                |
| `audit_repo/`                       | 3.0 M | Audit-run clone (kept for traceability)                   |
| `pop-os-setup/`                     |   —   | Unrelated local-setup tooling (own lifecycle)             |

If you need to compare an old revision, work from one of these as a read-only
reference. Do not `git checkout` into them.

---

## Untracked / Ignored

After the **2026-07-09 cleanup**, `git status --porcelain` reports
**~132 untracked entries**. The vast majority are:

- Submodule working copies not checked out in this workspace (see table above)
- `*.db` runtime databases: `core/history.db`, `backtest/results.db`,
  `data/`, `data_room/`
- `.venv/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`
- Local-only logs and PR diffs: `_pr_logs/` is **gone** (deleted by
  cleanup), but `.pr-diffs/`, `pr115-logs/` remain
- CI: `.github/actions/setup-astrofin-python/` (vendored action, duplicated)
- Local-only: `AUDIT_*.md` working files, `AUDIT_R_temp2.md`,
  `AUDIT_V2.md`, root-level `.coverage`
- A few workspace scratch files: `Documents/`, `Downloads/`, `Knowledge/`,
  `Projects/`, `Tests/`, `Trash/`

`.gitignore` rules cover: Python build/cache, `.venv`, secrets
(`keys/*`, `.env*`, `*.pem`, `*.key`, `*.enc.yaml` except explicitly
tracked examples), `core/history.db`, `backtest/results.db`, IDE files,
and the **legacy cleanup targets** (see below).

> **Why not commit them?** None of the untracked entries are unique source
> files. They are caches, local-only data, or pre-existing submodule
> working copies. Adding them to git would balloon the repo and
> obscure the real source-of-truth.

### Patterns explicitly ignored after the 2026-07-09 cleanup

The `.gitignore` now includes block-rules for these (so they stay
out of the tree even if re-created):

```
# Legacy snapshots / archives (see docs/REPOSITORY_LAYOUT.md)
as/
audit-astro/
audit-astrofin/
backups/
push_backup/
archive/
_sbs_old/
_pr_logs/
```

---

## Legacy & Archives

**Removed on 2026-07-09** (commit `7f7e32a`, push to `master`):

| Removed           | Status before                | Archive location                                       |
| ----------------- | ---------------------------- | ------------------------------------------------------ |
| `as/`             | 60 M, 2001 files, untracked  | `~/archives/cleanup_20260709/as_archive_*.tar.gz`      |
| `audit-astro/`    | 13 M, untracked              | `~/archives/cleanup_20260709/audit-astro_archive_*.tar.gz` |
| `audit-astrofin/` | 222 M, untracked             | `~/archives/cleanup_20260709/audit-astrofin_archive_*.tar.gz` |
| `backups/`        | 252 M, untracked             | `~/archives/cleanup_20260709/backups_archive_*.tar.gz` |
| `push_backup/`    | untracked                    | `~/archives/cleanup_20260709/push_backup_archive_*.tar.gz` |
| `archive/`        | untracked                    | `~/archives/cleanup_20260709/archive_archive_*.tar.gz` |
| `_sbs_old/`       | 10 tracked files (old sbs)  | `~/archives/cleanup_20260709/_sbs_old_archive_*.tar.gz` |
| `_pr_logs/`       | 7 tracked files (PR logs)    | `~/archives/cleanup_20260709/_pr_logs_archive_*.tar.gz` |

Total compressed archive footprint: **~170 MB**.
`audit_repo/` was inspected but **kept** because the audit source files
were older versions; root has newer equivalents.

**To restore** any of these: `tar -xzf <archive>.tar.gz -C /home/workspace/`.

---

## Important Notes

1. **Never edit `astrofin-sentinel-platform*` or `astrofin-monorepo*`.**
   They are vendored legacy copies. Active code lives in the root.
2. **Never commit secrets.** `.gitignore` blocks `.env*`, `keys/*`, `*.pem`,
   `*.key`, `*.enc.yaml` (except the `.example` templates), and the
   `core/history.db` SQLite file. `gitleaks` runs in CI.
3. **Submodules are not checked out here.** That is intentional — it keeps
   the root repo small. To work on a submodule, `cd` into it and operate
   inside that repo.
4. **Test skip list is policy.** `tests/conftest.py` has a `SKIP_TESTS`
   block (KI-125a, PR #152). When you see a skip, treat it as "known
   broken; do not re-enable without PR review". The list is curated in
   `docs/KNOWN_ISSUES.md`.
5. **Use `uv`, not `pip`.** `pyproject.toml` + `uv.lock` is the source
   of truth. CI uses `uv sync` to install.
6. **Pre-commit is enforced locally.** Install once:
   `uv run pre-commit install`. It runs ruff, mypy, gitleaks, and the
   end-of-file fixers.
7. **Public docs live in `docs/`.** Schema lives in `schema/`. OpenAPI
   specs are colocated with their services (e.g.
   `roma-execution-bridge/openapi.yaml`).

---

## Last Cleanup

| Date         | Commit    | Summary                                                                |
| ------------ | --------- | ---------------------------------------------------------------------- |
| 2026-07-09   | `7f7e32a` | Removed 8 legacy/archived directories (~600 MB untracked + 17 tracked); added block-rules to `.gitignore`; pushed to `master`. See `/tmp/cleanup_log.txt` for full action log. |
| 2026-07-09   | final-docs | Полная очистка репозитория, миграция на uv, стабилизация CI, coverage gate 3%, удаление safety, консолидация openapi, SKIP_REGISTER. |

Earlier housekeeping: `chore(g1): unify SOPS secrets` (#143),
`feat: unified JWT auth` (#136), K8s probes (#140), graceful
shutdown Dash (#139), STRIDE threat model (#146), submodule → subtree
rework (#142) — all landed before the 2026-07-09 cleanup.
