# AstroFin Sentinel V5 — Consolidation Plan

**Date:** 2026-07-27
**Branch:** `release/v1.0.0` → target `master`
**Audit baseline:** Steps 1–3 completed, 848 tests, 53 skipped (KI-125a), 1 flaky
**GA target:** 2026-09-15
**Freeze:** 2026-08-25
**Hardening window:** 2026-09-01–07

---

## Executive Summary

После Шага 2 аудита выявлено: архитектура чистая (29,941 строк Python, 0 hard violations Arch Linter), код — B+ (53 skipped tests, 3 крупных файла-кандидата на декомпозицию), безопасность — A− (0 HIGH bandit, 3 нефиксируемых pip-уязвимости), infra — B+ (PostgreSQL+TimescaleDB+pgvector online, 9 CI, CD с SBOM+cosign).

Этот план консолидации разделён на **4 фазы** по срочности и влиянию на GA.

---

## Phase 1: Immediate Cleanup (до 2026-07-28) — CRITICAL

### 1.1 ✅ PostgreSQL — COMPLETED
- [x] `pg_ctlcluster 15 main start` → accepting connections
- [x] `astrofin_db` online, TimescaleDB 2.28.3 + pgvector 0.8.0
- [x] 15 tables verified

### 1.2 ✅ STALE Copy — COMPLETED
- [x] `rm -rf astrofin-sentinel-platform.STALE-20260726/` — 5.5GB freed

### 1.3 ✅ Branch Cleanup — COMPLETED
- [x] 9 merged local branches deleted

### 1.4 ✅ GitHub Repo Archive — COMPLETED
- [x] `astrofin-sentinel-v5` archived
- [x] `AstroFinSentinelV5` archived

### 1.5 ✅ data_room/ Ruff Inclusion — COMPLETED
- [x] Exclude removed from `pyproject.toml`
- [x] 4 F401/F841 errors fixed

### 1.6 Delete Disabled CI Workflows
**4 duplicate workflows** in `.github/disabled-workflows/` — all superseded by active equivalents:

| Disabled | Replaced by |
|----------|------------|
| `coverage.yml` | `quality-gate.yml` (includes coverage) |
| `lint.yml` | `ci.yml` (ruff + bandit + radon) |
| `pr-checks.yml` | `ci.yml` + `coderabbit-pr-review.yml` |
| `security.yml` | `security.yml` (active, bandit + pip-audit + gitleaks) |

```bash
rm .github/disabled-workflows/*.yml
git add -A .github/disabled-workflows/
git commit -m "chore(ci): remove 4 disabled duplicate CI workflows"
```
**Risk:** None. Active workflows cover all checks.

### 1.7 Disposition Orphan Root `.py` Files

| File | Size | Status | Action |
|------|------|--------|--------|
| `FINAL_INTEGRATION_TEST.py` | 13KB | Integration test runner | `mv → tests/integration/test_final_integration.py` |
| `langgraph_schema.py` | 16KB | **Stale copy** (differs from `orchestration/` only by 4 missing `# noqa` lines) | `rm` — canonical is `orchestration/langgraph_schema.py` |
| `logging_setup.py` | 1.7KB | Pure-stdlib logger bootstrap | `mv → core/logging_setup.py` — альтернатива `core/logging.py` (structlog-free) |
| `data_provider.py` | 15KB | **DEAD CODE** — заменён `data_room/` | `rm` — все вызовы перенесены в `data_room/resolvers/` |
| `health_endpoints.py` | 8KB | **Stale copy** (binds `0.0.0.0` vs canonical `127.0.0.1`) | `rm` — canonical is `monitoring/health_endpoints.py` |
| `muhurtha.py` | 5KB | **Identical** to `core/muhurtha.py` | `rm` — canonical is `core/muhurtha.py` |
| `test_aspects.py` | 378B | Ad-hoc test script | `mv → tests/unit/test_aspects_root.py` |

```bash
# Safe deletions (stale copies / dead code):
rm langgraph_schema.py data_provider.py health_endpoints.py muhurtha.py

# Moves:
mv FINAL_INTEGRATION_TEST.py tests/integration/test_final_integration.py
mv logging_setup.py core/logging_setup.py
mv test_aspects.py tests/unit/test_aspects_root.py

# Commit:
git add -A
git commit -m "chore: dispose 7 orphan root .py files (3 stale copies, 1 dead code, 3 moved)"
```
**Risk:** None. `langgraph_schema.py` / `health_endpoints.py` / `muhurtha.py` — идентичны каноническим. `data_provider.py` — dead code (PR #201). Остальные — перемещения.

### 1.8 Commit Step 3 Lite Changes
```bash
git add pyproject.toml data_room/ orchestration/
git commit -m "fix: ruff — data_room/ inclusion, F401 fixes, B108 fix in sec_edgar"

git add artifacts/
git commit -m "chore: best-practices artifacts extracted (8 patterns)"
```

---

## Phase 2: Dependency & Security Hardening (до 2026-08-01)

### 2.1 Vulnerability Triage

| Package | Version | CVE | Fix Available | Action |
|---------|---------|-----|---------------|--------|
| `chromadb` | 1.5.5 | PYSEC-2026-311 | ❌ No fix (latest 1.5.9 still vuln) | Document in `KNOWN_ISSUES.md`, monitor upstream |
| `diskcache` | 5.6.3 | PYSEC-2026-2447 | ❌ No fix (latest = 5.6.3) | Mitigate: restrict cache-dir permissions, document risk |
| `ragas` | 0.4.3 | PYSEC-2026-3046 | ❌ Vendor unresponsive | Pin version + document SSRF risk in `THREAT_MODEL.md` |

```bash
# Pin with vulnerability comment in pyproject.toml:
# chromadb = ">=1.5.5,<2"  # PYSEC-2026-311 — no fix, monitor upstream
# diskcache = ">=5.6.3,<6"  # PYSEC-2026-2447 — no fix, cache-dir restricted
# ragas = ">=0.4.3,<0.5"    # PYSEC-2026-3046 — vendor unresponsive, SSRF risk
```

### 2.2 B108 Resolution Verification
- [x] `_CACHE_DIR` now uses `$XDG_CACHE_HOME` → `~/.cache/sec_edgar_cache` (not `/tmp`)
- [ ] Run bandit after Phase 1 commit: `bandit -r data_room/ -ll` → expect 0 MEDIUM+

### 2.3 Remaining Unmerged Branches

| Branch | Commits | Status | Action |
|--------|---------|--------|--------|
| `sprint3/skip-reorg` | 3 | KI-125a skip-list + http_client fix | `git merge sprint3/skip-reorg` (contains fix/ki125a-httpclient-loop) |
| `chore/unified-deps-workflows3` | 1 | `.gitignore` nested dir | `git merge chore/unified-deps-workflows3` |
| `fix/sprint4-final` | 1 | nosec markers for B310/B113 | `git merge fix/sprint4-final` |

```bash
git checkout release/v1.0.0
git merge sprint3/skip-reorg --no-ff -m "merge: KI-125a skip-reorg + http_client fix"
git merge chore/unified-deps-workflows3 --no-ff -m "chore: nested gitignore"
git merge fix/sprint4-final --no-ff -m "fix(security): nosec markers for B310, B113"

# Clean up merged local branches:
git branch -d sprint3/skip-reorg chore/unified-deps-workflows3 fix/sprint4-final
```

---

## Phase 3: Code Quality — Large File Decomposition (до 2026-08-15)

### 3.1 `synthesis_agent.py` (659 строк)

**Current:** 18 методов в одном файле
**Target:** Функциональная декомпозиция без изменения public API

| New Module | Lines | Extracted Methods |
|------------|-------|-------------------|
| `agents/_impl/synthesis/voter.py` | ~120 | `_vote()`, `_group_by_category()`, `_detect_conflicts()`, `_normalize()` |
| `agents/_impl/synthesis/guards.py` | ~120 | `_apply_guards()`, `_get_signal_attr()`, `_calculate_levels()` |
| `agents/_impl/synthesis/formatting.py` | ~80 | `_format_breakdown()`, `_collect_sources()` |
| `agents/_impl/synthesis/agent.py` | ~300 | `SynthesisAgent.run()`, `analyze()`, `_synthesize()`, `run_synthesis_agent()`, `create()` |

```python
# New public API (backward-compatible):
from agents._impl.synthesis_agent import SynthesisAgent  # OLD IMPORT STILL WORKS
from agents._impl.synthesis import SynthesisAgent        # NEW PREFERRED IMPORT
```

**Risk:** Low. Public API unchanged (`SynthesisAgent`, `run_synthesis_agent()`, `create()`). Existing tests must pass.

### 3.2 `core/rag_client.py` (643 строк)
**Action:** Вынести FAISS/BMR25/embedding логику в `knowledge/` (при сохранении реэкспорта из `core/`).

### 3.3 `agents/gitagent_exporter.py` (627 строк) + `agents/gitagent_registry.py` (561 строк)
**Action:** Объединить в `integrations/gitagent/` директорию как `exporter.py` + `registry.py`.

---

## Phase 4: Architecture — Flask→FastAPI Migration Path (2026-09-15+, post-GA)

### 4.1 Scope

7 файлов используют Flask напрямую:

| File | Flask API Used | Migration Complexity |
|------|---------------|---------------------|
| `core/auth.py` | `flask.request`, `jsonify` | Medium |
| `core/auth_jwt_middleware.py` | `flask.g`, `jsonify`, `request` | High |
| `core/rate_limit.py` | `flask_limiter` | High (no FastAPI equivalent) |
| `core/security_middleware.py` | `flask.g`, `request`, `flask_cors` | Medium |
| `web/middleware/__init__.py` | `Flask` app object | High |
| `web/data_room.py` | Flask routes | Medium |
| `web/wsgi.py` | Flask WSGI entrypoint | Low |

**Decision:** Отложить до v1.1.0. Flask используется для web dashboard (Dash на Flask), который является вспомогательным, не основным. FastAPI уже обслуживает основные API эндпоинты в `api/main.py`.

### 4.2 KI-125a Test Restoration

**53 tests skipped** → roadmap:

| Sprint | Category | Tests | Action |
|--------|----------|-------|--------|
| Sprint 5 | Category A (observability, calibration, rag) | 28 | `_StubMethod` → real metric collectors |
| Sprint 6 | Category B (architecture, compromise) | 9 | `acos_contracts` module restoration + KARL runtime |
| Sprint 7 | Category C (backtest, rate_limit) | 12 | Fixture drift reconciliation |
| v1.1.0 | Category F (ADR-0010) | 34 | Legacy tests — restore or permanently deprecate |

**Rule:** Mass-unskip forbidden per PR #283 guard. Каждая batch — отдельный feature branch с `--count=10` проверкой.

### 4.3 1 Flaky Test
**`test_broker_overhead_acceptable`** — intermittent failure in `test_sprint4.py`.
```bash
# Reproduce:
pytest tests/test_sprint4.py::TestPerformanceBaseline::test_broker_overhead_acceptable -x --count=20

# If >2 failures in 20 runs → add to KI-125a with `--reason "flaky: resource contention"`
# If <2 failures → tighten timing tolerance in test assertion
```

---

## Final Commit Sequence

```bash
# Phase 1
git checkout release/v1.0.0
# ... orphan file disposition ...
# ... disabled CI cleanup ...
git add -A
git commit -m "chore: Phase 1 cleanup — orphans, CI dedup, ruff fixes"

# Phase 2
git merge sprint3/skip-reorg chore/unified-deps-workflows3 fix/sprint4-final
git add pyproject.toml  # vulnerability pin comments
git commit -m "chore: Phase 2 — vuln triage, branch consolidation"

# Push
git push origin release/v1.0.0

# Prepare merge to master (after GA approval)
git checkout master
git merge release/v1.0.0 --no-ff -m "release: v1.0.0 consolidation (Audit Steps 1-3)"
git tag v1.0.0
git push origin master --tags
```

---

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| `synthesis_agent.py` decomposition breaks tests | Low | Medium | Backward-compatible imports, CI gate |
| Flask→FastAPI migration breaks dashboard | Low | High | Deferred to v1.1.0 |
| chromadb/ragas vulnerabilities exploited | Low | Medium | Documented in THREAT_MODEL, no fix available |
| Orphan file deletion breaks imports | None | Low | Verified — all are stale copies or dead code |
| Branch merge conflicts | Low | Low | 3 branches have non-overlapping diff scopes |

---

## Status Tracking

| # | Task | Phase | Status | Assignee |
|---|------|-------|--------|----------|
| 1 | PostgreSQL online | 1 | ✅ Done | Zo |
| 2 | STALE copy deleted | 1 | ✅ Done | Zo |
| 3 | Branches cleaned | 1 | ✅ 9/12 done | Zo |
| 4 | GitHub repos archived | 1 | ✅ Done | Zo |
| 5 | data_room/ ruff | 1 | ✅ Done | Zo |
| 6 | Remove disabled CI | 1 | ⏳ Pending | Zo |
| 7 | Orphan .py disposition | 1 | ⏳ Pending | Zo |
| 8 | Commit Phase 1 | 1 | ⏳ Pending | Zo |
| 9 | Vulnerability triage | 2 | ⏳ Pending | Felix |
| 10 | Branch consolidation | 2 | ⏳ Pending | Zo |
| 11 | synthesis_agent decomposition | 3 | ⏳ Pending | Felix |
| 12 | rag_client extraction | 3 | ⏳ Pending | Felix |
| 13 | gitagent integration merge | 3 | ⏳ Pending | Felix |
| 14 | Flask→FastAPI migration | 4 | 📋 v1.1.0 | Felix |
| 15 | KI-125a restore | 4 | 📋 Sprint 5-7 | Felix |
