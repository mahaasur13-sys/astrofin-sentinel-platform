# 📋 AstroFin Sentinel Platform — Consolidation Plan v2

**Date:** 2026-07-15 08:40 (+04)
**Branch:** consolidation-v1  
**PR status:** CLOSED (#212, not merged)  
**Commit:** 85efbf9

---

## 1. Current State Summary

| Metric | Production scope | Full scope |
|--------|-----------------|------------|
| Python files | 142 | 1869 |
| Ruff errors | **86** | 1874 |
| Syntax errors | 0 | **7** |
| Pytest | 572 passed | 572 passed |
| Coverage | 42.41% | — |
| pip check conflicts | — | **15** |
| CI workflows | — | 17 valid |

**Designation:**
- **Production scope** = `agents/_impl` `core` `orchestration` `web` `scripts` (86 ruff errors, zero syntax errors)
- **Full scope** = everything including `audit_repo` `bridge` `infrastructure` `kernel` `v6` `v7` `v8` (1874 ruff errors, 7 syntax errors)

---

## 2. Blockers (must fix before v1.0.0)

### 2.1 — Syntax errors (7 files, 7 errors)

| File | Error |
|------|-------|
| `bridge/roma/roma_sdk.py:79` | invalid syntax |
| `deploy/iac/v8/rollback/engine.py:8` | from __future__ after code |
| `infrastructure/asurdev/v8/rollback/engine.py:8` | from __future__ after code |
| `deploy/iac/v8/incident/model.py:9` | `[` was never closed |
| `infrastructure/asurdev/v8/incident/model.py:9` | `[` was never closed |
| `infrastructure/asurdev/v6/digital_twin/simulator.py:88` | from __future__ after code |
| `audit_repo/tests/test_ralph_safety.py:6` | `import pytest` in wrong location |

**Fix approach:** targeted edits — move `from __future__` to line 1, close brackets, fix import placement.

### 2.2 — pip dependency conflicts (15)

| Conflict | Impact |
|----------|--------|
| `opentelemetry-sdk 1.40` ↔ `opentelemetry-api 1.42` | High — tracing breakage |
| `langchain 0.3` ↔ `langchain-core 1.2` | High — RAG/agents breakage |
| `protobuf 6.33` ↔ `autogen-core 0.7 (needs 5.29)` | Medium |
| `pydantic 2.10.6` ↔ `llama-index (needs 2.11.5)` | Medium |
| `fastapi 0.139` ↔ `aiqtoolkit (needs 0.115)` | Low |
| 10 other minor | Low |

**Fix approach:** pin compatible versions or remove unused deps. Run `pip install -r requirements.txt --upgrade` and resolve conflicts.

### 2.3 — PR #212 closed, needs reopening

PR was manually closed on 2026-07-14. Need to:
1. Rebase consolidation-v1 on latest main
2. Force-push
3. Reopen or create new PR

---

## 3. Ruff Error Reduction Plan

### Phase A — Production scope (86 → 0)

| Code | Count | Fix approach | Time |
|------|-------|-------------|------|
| BLE001 | 72 | `# noqa: BLE001` on legitimate except: blocks; replace others with specific exceptions | 2h |
| E402 | 10 | Move lazy imports to top or wrap in functions | 1h |
| F401 | 4 | Remove unused imports | 15min |

**Target:** 0 errors in production scope. Then add `ruff check --extend-exclude='audit_repo,bridge,infrastructure,kernel,v6,v7,v8' .` to CI.

### Phase B — Full scope (1874 → <500)

| Code | Count | Auto-fix? | Note |
|------|-------|-----------|------|
| BLE001 | 310 | No | Across audit_repo, bridge, infrastructure |
| E402 | 305 | No | Module-level imports not at top |
| E702 | 206 | Yes (unsafe) | Multiple statements on one line |
| F401 | 130 | No (84 in __init__.py) | Re-exports in public API |
| F821 | 85 | Partial | Missing type imports |
| F403 | 103 | No | Wildcard imports |
| E501 | 104 | No | Line too long (cosmetic) |

**Target:** 1094 → <500. Focus on E702 (auto-fix unsafe), E402, BLE001.

---

## 4. Execution Order

```
Step 1: Recover .git from origin + stash working tree → 10 min
Step 2: Fix 7 syntax errors → 30 min (parallel)
Step 3: Fix production-scope ruff (86 → 0) → 3h
Step 4: Pin dependencies, resolve 15 conflicts → 1h
Step 5: Rebase consolidation-v1 on main + force-push → 15 min
Step 6: Reopen PR or create new + add CI gate → 15 min
Step 7: Phase B ruff reduction (1874 → <500) → 4h (after v1.0.0)
```

---

## 5. What's NOT in this plan

- `audit_repo/` — stays as-is (archived snapshot); excluded from CI ruff gate
- `bridge/`, `infrastructure/`, `kernel/` — deferred to v1.1
- `v6`, `v7`, `v8` — legacy, excluded from CI
- Trash cleanup — separate task after v1.0.0
- P2/P5 (TimescaleDB, PostGIS) — Sprint 2 per `SPRINT_2_REVISED.md`

---

**Next action:** execute Step 1 — recover .git and re-validate pytest baseline.
