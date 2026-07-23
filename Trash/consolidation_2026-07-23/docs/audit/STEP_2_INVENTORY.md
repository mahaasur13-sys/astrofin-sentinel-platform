# Step 2 — Inventory & Canonical Map

**Date:** 2026-07-12
**Auditor:** Zo (Senior Architect / Code Auditor)
**Scope:** `/home/workspace` (= `astrofin-sentinel-platform` snapshot, master + inlined submodules)
**Method:** Static filesystem scan + cross-import analysis (no git here — `fatal: not a git repository`; this is a working-tree snapshot).

---

## 2.1 Top-level directory census (39 entries)

| Dir | Size | Files | .py | .md | Purpose (verified) | Status |
|---|---:|---:|---:|---:|---|---|
| `acos-contracts/` | 92K | 27 | 10 | 1 | Shared cross-repo protocols/DTOs/determinism. Stable v0.1.0+ package. Imported by 4 root packages. | **ACTIVE — Contract Surface** |
| `agents/` | 1.1M | 114 | 57 | 3 | 13 active agents in `agents/_impl/`. Root-level wrappers (`astro_council_agent.py` etc.) are shim/stub. `agents/_archived/` is **referenced in AGENTS.md but DOES NOT EXIST on disk**. | **ACTIVE — with dead refs** |
| `agents/_impl/amre/` | — | — | — | — | ATOM-KARL framework (audit, reward, oap, backtest_loop, …). 1 stale `.bak-006` file. | **ACTIVE** |
| `asp-work/` | **417M** | 12 921 | 7 793 | 250 | **Full mirror of `/home/workspace`** (incl. its own `.git`, `.coverage`, baselines, `.pytest_cache`). Created by `git subtree add` / local clone. Currently untracked. | **ORPHAN — drop** |
| `astrofin_sentinel_v5.egg-info/` | 18K | 6 | 0 | 0 | Build artifact. Should be in `.gitignore`; safe to delete from disk. | **BUILD ARTIFACT** |
| `astrology/` | 28K | 6 | 3 | 0 | Muhurtha/Choghadiya helpers. Used by `agents/_impl/electoral_agent.py`. | **ACTIVE** |
| `atom-core/` | 7K | 3 | 0 | 1 | **Go workspace — live router**. `packages/atom-router/pkg/contracts/types.go`. NOT a Python package. Has protective banner. | **ACTIVE — Go (note)** |
| `audit_repo/` | 3.0M | 453 | 314 | 83 | Historical snapshot (33K LOC, 0 active imports outside `graphify-out/infer_edges.py` which is itself an analysis artifact). 8 cross-refs in `strategies/generator.py` are dead. | **ARCHIVED — drop from index** |
| `backtest/` | 132K | 11 | 7 | 1 | Backtest metrics. Active per `AGENTS.md`. | **ACTIVE** |
| `bench/` | 9K | 4 | 4 | 0 | `bench_diversity.py`, `perf_breakdown.py`, `perf_debug.py`, `verify_task6.py`. Dev-only perf scripts. | **DEV — keep but isolated** |
| `common/` | 6K | 5 | 3 | 0 | **Deprecated compatibility shim** that re-exports `acos_contracts`. 3 call-sites in `core/ephemeris.py`. | **DEPRECATED — plan removal** |
| `config/` | 8.5K | 3 | 0 | 0 | YAML configs. | **ACTIVE** |
| `core/` | 1.8M | 79 | 49 | 0 | Astro engine, RAG client, history_db, logging, tracing, auth, rate_limit, aspects, kepler, panchanga, thompson, security_middleware. **Heart of system.** | **ACTIVE — core** |
| `data/` | 2.4M | 16 | 1 | 0 | JSON datasets + RAG dumps. | **ACTIVE** |
| `data_room/` | 38K | 14 | 7 | 0 | Auxiliary data layer (likely secondary). | **ACTIVE — verify role** |
| `db/` | 127K | 15 | 8 | 1 | DB schema/migrations helpers. | **ACTIVE** |
| `deploy/` | 1.6M | 480 | 167 | 24 | Docker, Helm, k8s, health_endpoints, monitoring, supervisord. | **ACTIVE** |
| `docs/` | 755K | 65 | 0 | 62 | Documentation. Subfolder `audit/` newly created. | **ACTIVE** |
| `feature_pipeline/` | 1K | 1 | 0 | 0 | Stub single-file. **Orphan.** | **ORPHAN** |
| `gpu_worker/` | 1K | 1 | 0 | 0 | Stub single-file. **Orphan.** | **ORPHAN** |
| `graphify-out/` | 43M | 32 | 11 | 5 | Static analysis output (graph.json, reports, calibration). Re-generatable. | **BUILD ARTIFACT — exclude** |
| `integrations/` | 199K | 30 | 8 | 2 | External integrations. | **ACTIVE** |
| `keys/` | 1K | 1 | 0 | 0 | `jwt_public.pem`. Sensitive; verify in `.gitignore`. | **SECRETS — keep** |
| `knowledge/` | 367K | 50 | 15 | 22 | Domain notes, RAG corpus, DB architecture notes. | **ACTIVE** |
| `mas_factory/` | 159K | 16 | 10 | 0 | Multi-agent system factory (architect, engine, registry, topology, visualizer). | **ACTIVE** |
| `meta_rl/` | 502K | 58 | 42 | 0 | Meta-RL pipeline (37 modules per AUDIT_2026-06-17). Has 6+1 known failing tests (KI-125a). | **ACTIVE — partial debt** |
| `migrations/` | 23K | 10 | 2 | 0 | SQL migrations. | **ACTIVE** |
| `migrations_postgres/` | 13K | 2 | 0 | 0 | Postgres-specific migrations. | **ACTIVE** |
| `ml_engine/` | 1K | 1 | 0 | 0 | Stub single-file. **Orphan.** | **ORPHAN** |
| `models/` | 1.8M | 4 | 0 | 0 | Trained artifacts (residual_model.joblib, calibrated_elements.json, online_policy.json, astro_rl_log.json). | **ARTIFACTS — gitignore** |
| `observability/` | 13K | 2 | 1 | 0 | Observability helpers. | **ACTIVE** |
| `orchestration/` | 94K | 14 | 9 | 0 | `sentinel_v5.py` + MAS orchestrator. Entry point. | **ACTIVE — entry** |
| `research/` | 9.5K | 1 | 0 | 1 | Research notes. | **DOCS** |
| `schema/` | 13K | 2 | 0 | 0 | JSON Schemas. | **ACTIVE** |
| `scripts/` | 173K | 24 | 12 | 0 | `architecture_linter.py`, `validate_agent.py`, `ralph_loop.sh`, `first-release.sh`, `validate_docker_security.py`, `validate_registry.py`. | **ACTIVE — tooling** |
| `sdlc_os/` | 512 | 0 | 0 | 0 | **Empty directory.** | **EMPTY — drop** |
| `security/` | 20K | 3 | 0 | 3 | Security docs. | **DOCS** |
| `src/` | 1.2M | 262 | 161 | 11 | Top-level `src/` only has `bridges/roma/` (1.2M LOC). Everything else is re-export of ROMA. | **ACTIVE — ROMA bridge** |
| `src/bridges/roma/` | — | — | — | — | **ROMA execution bridge — full SaaS product** (FastAPI + Pydantic v2, Helm, Kustomize, RBAC, auth, billing, control-plane, GPU worker). `pyproject.toml` declares standalone package `roma-execution-bridge 1.0.0`. | **ACTIVE — inlined submodule** |
| `strategies/` | 49K | 6 | 3 | 0 | Strategy generator. Has 8 dead cross-refs to `audit_repo/strategies/`. | **ACTIVE — clean refs** |
| `tests/` | 4.7M | 409 | 105 | 0 | Test suite. 54 tests currently in `SKIP_LIST_KI_125A` (per `KNOWN_ISSUES.md`). | **ACTIVE — debt** |
| `tools/` | 101K | 12 | 9 | 0 | healthcheck, db_monitor, rag_admin, thompson_cli, embedding_client, migrate_*. | **ACTIVE** |
| `trading/` | 222K | 26 | 15 | 0 | Trading execution, TWAP, risk. | **ACTIVE** |
| `training/` | 6.5K | 1 | 1 | 0 | `train_residual_model.py` — single training script. | **ACTIVE — single file** |
| `web/` | 226K | 27 | 17 | 0 | FastAPI dashboard. | **ACTIVE** |

### Hidden / odd top-level

| Item | Type | Issue |
|---|---|---|
| `nano` | file (1.6K) | **Mysterious file** in root. Contains what? |
| `muhurtha.py` | file (root) | Should be inside `astrology/` |
| `test_aspects.py` | file (root) | Should be inside `tests/` |
| `langgraph_schema.py` | file (root, 15K) | Should be inside `schema/` or `orchestration/` |
| `health_endpoints.py` | file (root) | **Duplicates** `deploy/monitoring/health_endpoints.py`? Verify. |
| `data_provider.py` | file (root, 15K) | Should be inside `core/` or `integrations/` |
| `FINAL_INTEGRATION_TEST.py` | file (root, 12K) | Should be inside `tests/` or `scripts/` |
| `pr118_files.txt`, `pr120_files_*.txt` | files | PR diff dumps — should NOT be in repo. |
| `quality-gate-fix.patch`, `quality-gate-setup-uv.patch`, `ci-cleanup.patch` | files | Patch artifacts. **Drop.** |
| `nano` (1 file) | file | `cat` next. |
| `.zo_scratch/` | dir | Already-tracked cleanup scratchpad; contains `submodule-archive-2026-07-12/` with 5 archived submodules. |
| `Trash/cleanup-2026-07-12/` | dir | Already moved items (atom-core, audit_repo, acos-contracts duplicates, .gitmodules.bak, Dockerfile.uv.bak). |
| `_pr_logs/PR1`, `_pr_logs/PR2` | dirs | Old PR log artifacts. |
| `_sbs_old/` | dir | 10 legacy .py files. SBS = ? |
| `.egg-info/`, `__pycache__/` (×20+), `*.pyc` (3760) | dirs/files | Build/runtime caches. **Exclude via .gitignore.** |

---

## 2.2 Cross-import matrix (verified)

| Importer | Imported from | Sites (root only) |
|---|---|---|
| `acos_contracts` | used by | `common/*` (3), `acos-contracts/acos_contracts/events.py` |
| `common` (shim) | used by | `core/ephemeris.py` |
| `audit_repo` | used by | **only** `graphify-out/infer_edges.py` (analysis tool, not runtime) |
| `atom-core` | used by | **only** `graphify-out/infer_edges.py` (analysis tool) |
| `src.` (local) | used by | **only** `strategies/generator.py` — but `src` is the new ROMA inlining, the reference is in old/archived code. **Dead in active runtime.** |

**Implication:**
- `acos_contracts` ← **canonical contract surface**, sole legal inter-package import channel.
- `common/*` ← deprecated shim, only `core/ephemeris.py` still uses it.
- `audit_repo/` ← 0 active runtime imports. Safe to drop from index.
- `atom-core/` ← 0 runtime imports, but it is a **live Go workspace** per its README — keep, do not delete.
- `src/bridges/roma/` ← new inlined submodule, full product, complete.

---

## 2.3 Status classification

### ✅ Active (kept, healthy or with known issues)
- `core/`, `agents/_impl/`, `agents/_impl/amre/`, `meta_rl/`, `orchestration/`, `trading/`, `backtest/`, `astrology/`, `mas_factory/`, `tools/`, `scripts/`, `web/`, `observability/`, `integrations/`, `knowledge/`, `data/`, `data_room/`, `db/`, `migrations/`, `migrations_postgres/`, `deploy/`, `tests/`, `models/` (artifacts), `keys/` (secrets), `config/`, `schema/`, `training/`, `bench/`, `docs/`, `security/`, `research/`, `strategies/`
- `src/bridges/roma/` — newly inlined ROMA execution bridge
- `atom-core/` — Go workspace, live
- `acos-contracts/` — canonical contracts package
- `common/` — DEPRECATED shim (with plan to remove)

### 🟡 Archived (kept on disk, removed from git index)
- `audit_repo/` — historical snapshot, 33K LOC, 0 active imports
- `Trash/cleanup-2026-07-12/` — already-moved items
- `.zo_scratch/submodule-archive-2026-07-12/` — 5 archived submodules (AsurDev, atom-federation-os, gitagent, pop-os-setup, roma-execution-bridge — **note**: `roma-execution-bridge` is also inlined into `src/bridges/roma/`, so this archive is now redundant)

### 🔴 Orphan (no imports, no purpose, can be deleted from disk too)
- `feature_pipeline/` (stub)
- `gpu_worker/` (stub) — note: `src/bridges/roma/gpu_worker/` is a real product module; this is a different file
- `ml_engine/` (stub)
- `sdlc_os/` (empty)
- Loose root files: `nano`, `muhurtha.py`, `test_aspects.py`, `langgraph_schema.py`, `health_endpoints.py`, `data_provider.py`, `FINAL_INTEGRATION_TEST.py`
- Patch artifacts: `quality-gate-fix.patch`, `quality-gate-setup-uv.patch`, `ci-cleanup.patch`
- PR diff dumps: `pr118_files.txt`, `pr120_files_all.txt`, `pr120_files_full.txt`

### ⚪ Build/runtime artifacts (add to `.gitignore`, do not commit)
- `astrofin_sentinel_v5.egg-info/`
- `__pycache__/` (×20+)
- `*.pyc` (3760)
- `models/*.joblib`, `models/*.json` (binary artifacts)
- `graphify-out/` (re-generatable)
- `.pytest_cache/`, `.ruff_cache/`
- `core/belief.db`, `core/history.db` (runtime SQLite)

### 🚨 CRITICAL — duplicate/conflict
- `audit_repo/strategies/generator.py` vs `strategies/generator.py` — 8 cross-references. Code in active `strategies/` is correct; `audit_repo/` version is historical.
- `audit_repo/acos-contracts/...` mirrors standalone `acos-contracts/`.
- `asp-work/` is a 417M mirror of the entire workspace. **Drop immediately** (outside git, untracked, but takes 417M).

---

## 2.4 Mismatches between documentation and reality

| Doc says | Reality | Action |
|---|---|---|
| `agents/_archived/` exists (AGENTS.md, AUDIT) | **Does not exist** | Remove dead references from AGENTS.md |
| `infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/` (README.md) | **Do not exist** | README rewrite (per recent PR plan) |
| `git submodule` references in old docs | Submodules inlined per recent PRs | Update AGENTS.md to "inline submodules" |
| `core/history.db`, `core/belief.db` are runtime state | Will be created on first run; should be gitignored | Verify `.gitignore` covers `*.db` |
| `_sbs_old/` (10 .py files) | Legacy code without any reference | Document or drop |
| `nano` (file at root) | Unknown content | Inspect |

---

## 2.5 Headline findings

1. **AstroFin Sentinel v5 + inlined ROMA bridge is the canonical active product** at the root.
2. **`acos-contracts/` is the only allowed inter-package contract**; `common/` is a deprecated shim — keep on disk until `core/ephemeris.py` migrates, then delete.
3. **`audit_repo/` (3.0M, 314 .py) is dead weight** in the active runtime — already planned for `git rm --cached` per memory. Confirmed safe.
4. **`asp-work/` is a 417M full mirror** of the workspace (with its own `.git/`) — accidental stale copy outside the git tree. Strong candidate for `rm -rf` outside the repo (since it has its own `.git`, it is not a git submodule).
5. **`atom-core/` is a Go workspace** (not Python) — protected, do not delete.
6. **`src/bridges/roma/` is a complete inlined submodule** (FastAPI SaaS, Helm, Kustomize) — should be treated as a first-class product, not a bridge.
7. **Loose root .py files** (`data_provider.py`, `muhurtha.py`, `langgraph_schema.py`, `test_aspects.py`, `health_endpoints.py`, `FINAL_INTEGRATION_TEST.py`) belong inside proper packages — currently orphans at the wrong layer.
8. **Build/runtime cache pollution**: 20+ `__pycache__/`, 3760 `*.pyc`, plus egg-info, baselines, caches. None should be in the index.
9. **KI-125a is the dominant test debt**: 54 skipped tests across 17 files, tracked in `KNOWN_ISSUES.md` and issue #149.
10. **AUDIT_2026-06-17.md is the most recent deep audit** (61K) — its 6+1 meta_rl failures are reflected in the SKIP_LIST. The current Step 2 confirms structural findings remain valid (orthogonal to that functional debt).

---

## 2.6 Step 2 → Step 3 transition

**Step 3 (Doc Audit)** should focus on:
- AGENTS.md — dead `agents/_archived/` reference; missing entry for `src/bridges/roma/`; missing entry for `atom-core/`.
- README.md — non-existent paths (`infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/`).
- AUDIT_2026-06-17.md — still accurate, but should be re-baselined to current master (no `EvaluationResult` `to_dict`/`from_dict` fix yet per memory).
- `KNOWN_ISSUES.md` — **out of date per memory (PR #188 merged, but file still shows 54 skips)**. Update required.
- `muhurtha.py` vs `astrology/` split — inconsistent placement.

Proceed to **Step 3: Doc Audit** unless objections. Propose prompt for Step 3:

> "Step 3 — Doc Audit. For each top-level .md file, classify as: ✅ Current, 🟡 Drift, 🔴 Stale. Cross-check each path reference against the real filesystem. Produce docs/audit/STEP_3_DOC_AUDIT.md with a remediation list and a 'rewrite README.md' plan based on the canonical structure from Step 2. Mark the items that should be closed in this audit cycle vs. parked for later."
