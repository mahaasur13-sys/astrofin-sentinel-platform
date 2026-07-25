# AstroFin Sentinel V5 — Release Notes v2026.07.25 (Audit Closed)

> **Git Tag:** `v2026.07.25-audit-closed`
> **Date:** 2026-07-25
> **Scope:** Security audit + technical debt consolidation (3 waves, 10 findings, 13 PRs)

---

## 🔒 Security (P0 — Wave 1)

- **SQL injection** fixed in `core/history_db_pg.py` — parameterized query with `%s`
- **Hardcoded password** `POSTGRES_PASSWORD: astrofin` → `${POSTGRES_PASSWORD:-change_me_in_production}`
- **Bandit**: 3 HIGH findings → 0 (SQLi, RCE eval, weak MD5 hashes replaced with SHA256)
- **Gitleaks** now runs in CI on every PR/push

## 📦 Dependencies (P1 — Wave 1)

- **Unified deps**: `requirements-dev.txt` deleted → all dev deps in `pyproject.toml [dev]`
- **35 packages updated**: `websockets` 15→16 (breaking), `aiohttp`, `fastapi`, `openai`, `mypy`, `ruff`, `prometheus-client`
- **uv.lock** synced (20 packages bumped in `0b6a9d0e`)

## 🧹 Code Quality (P2 — Wave 2)

- **`web/callbacks.py`**: 1032-line god-object → 5 domain modules (`routing`, `evolution`, `live`, `strategy`, `sessions`)
- **Ruff**: F401 no longer globally ignored — scoped to `__init__.py` via per-file-ignores
- **Ruff**: `meta_rl/` and `trading/` directories now linted (removed from exclude)
- **7 root agent duplicates** → `agents/_archived/` (dedup)

## ⚙️ CI/CD (P2 — Wave 3)

- **CI consolidation**: 17 → 9 workflows
  - Removed: `lint`, `pr-checks`, `compose-check`, `coverage`, `graphify-healthcheck`
  - Removed: `ci.security.yml`, `secret-scan.yml`, `coderabbit-safety-scan`
  - `security.yml` now aggregates: bandit + pip-audit + gitleaks + safety
  - CI switched to `pip install ".[dev]"` via `pyproject.toml`

## 🧪 Testing (Wave 1)

- `test_api_auth` isolation fixed — try/finally teardown, fixture ordering, TestClient close

## 📚 Documentation

- `AUDIT_REPORT_2026-07-25.md` — full audit report (368 lines)
- `docs/audits/` — audit trail directory
- `docs/CI_CONSOLIDATION_PLAN.md` — CI consolidation rationale
- `CHANGELOG.md` — updated with full audit history

---

## Migration Notes

- **Breaking**: `requirements-dev.txt` deleted — use `pip install ".[dev]"` for development dependencies
- **Breaking**: `websockets` 15→16 — API compatibility verified, no code changes needed
- **CI**: If you had local CI scripts referencing deleted workflows (`lint`, `pr-checks`, etc.) — update to `ci.yml`

## Contributors

- **mahaasur13-sys** — audit execution, PRs #268–#280
- **Zo Computer** (asurdev) — automated audit, CI consolidation, patch generation

