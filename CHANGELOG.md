# Changelog

All notable changes to AstroFin Sentinel Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-07 — GA Release

### Added
- **CI stabilisation (4-block recovery)**: Architecture Lint, Code Quality (Ruff + mypy), Security (Bandit + Docker), Secret Scan, gitleaks, and BlackRock Six Tests are green on master. PR #123.
- **Compose / Docker hardening**: bind monitoring ports, require Redis auth, drop all capabilities. PR #124.
- **Phase 2 — Contracts & ops runbooks**: MAINTAINERS.md, RUNBOOK.md, SLO.md, ADR-0009 (unified JWT auth), docs/adr/README.md, docs/api/dash-ui.md, docs/api/openapi.yaml, docs/db/schema.md. PR #131.
- **Phase 3a — Observability configs**: Prometheus recording rules, alert rules, SLO configuration. PR #132.
- **Phase 3b — PII scrubber**: deterministic scrubber applied to logs and traces (api_key, email, JWT, phone, IPv4). PR #133.
- **Phase 4 — Security & Compliance baseline**: SECURITY.md (disclosure policy), PRIVACY.md (GDPR minimum), docs/security/THREAT_MODEL.md (STRIDE), docs/security/compliance/SOC2_checklist.md. PR #134.
- **CHANGELOG.md, DEPLOYMENT.md, LICENSE (MIT)** for production handoff.

### Changed
- **Version bump**: 5.0.0 → 1.0.0 (GA). Package name `astrofin-sentinel-v5` retained — the "v5" in the name is the architecture generation, the `1.0.0` is the release marker.
- **`.coderabbit.yaml`**: migrated from v1 (`path_instructions`/`focus_areas`) to v2 schema; `path_filters` removed.
- **Dockerfile**: multi-stage production build, non-root user, healthcheck, wheels.
- **CI workflows**: gitleaks + detect-secrets + pip-audit + safety + trivy + bandit; quality gate aggregator.

### Fixed
- 26 failing legacy tests documented in #125 (known-issue, blocking GA hardening but not 1.0.0).
- 1,490 legacy Python files in `deploy/` flagged for audit (#130).
- Submodule drift (4 of 5 submodules returned 404) → all dropped from `.gitmodules` (PR #115 follow-up).

### Known issues (not blocking v1.0.0)
- #125 — Tests + Coverage: 194 legacy test files in `tests/` need migration to new layout.
- #126 — Architecture Lint (R1-R9) + Code Quality (Ruff E501/C901, F401/403/404, Bandit B104/B608, mypy): pre-existing in `src/bridges/roma/`, `tests/`, `deploy/`.
- #129 — Backlog gaps: pgvector, Sentry, Vault/SOPS, SLSA/Cosign (PII scrubber already shipped in #133).
- #81 — Dual auth model: `core/auth.py` still uses static `API_KEY`; `web/app.py` uses JWT. Single source of truth scheduled for post-1.0.0.

### References
- PRs: #115, #123, #124, #131, #132, #133, #134
- Issues closed: #127 (RUNBOOK/MAINTAINERS/SLO), #128 (CI red — closed by recovery PRs)
- Issues partially closed: #129 (PII done, 4 artifacts remain)
- Audit reports: `docs/audits/`, `PRODUCTION_BACKLOG.md`

## [Unreleased]

(none)

## [v2026.07.25-audit-closed] — 2026-07-25

### 🔒 Security (P0)
- Fixed SQL injection in `core/history_db_pg.py` (parameterized query)
- Hardcoded `POSTGRES_PASSWORD` → `${POSTGRES_PASSWORD:-env_var}`
- Bandit un-masking: 3 HIGH → 0 (#268)

### 📦 Dependencies (P1)
- Unified deps: `requirements-dev.txt` → `pyproject.toml [dev]` (#270, #278)
- 35 outdated packages updated (websockets 15→16, prometheus_client, aiohttp, etc.)

### 🧹 Code Quality (P2)
- God-object `web/callbacks.py` (1032 линий) → 5 domain modules (#276)
- Ruff: F401 scoped to `__init__.py` via per-file-ignores (#274)
- Ruff: `meta_rl/` + `trading/` removed from exclude (#275)
- 7 root agent duplicates → `agents/_archived/` (#269)

### ⚙️ CI/CD (P2)
- 17 workflows → 9 consolidated (#280)
- CI switched to `pyproject.toml [dev]` extra

### 🧪 Testing
- `test_api_auth` isolation fix — try/finally teardown + client close (#273)

### 📚 Docs
- `AUDIT_REPORT_2026-07-25.md` — полный аудит (368 строк)
- `AUDIT_REPORT_STEP1_2026-07-25.md` — инвентаризация
- `docs/audits/` — audit trail directory
- `docs/CI_CONSOLIDATION_PLAN.md` — план 17→9

