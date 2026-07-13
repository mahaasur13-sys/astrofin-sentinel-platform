# 🔍 ASTROFIN-SENTINEL-PLATFORM — Master Audit Report
**Auditor:** Senior Architect & Code Auditor
**Date:** 2026-07-12
**Scope:** `mahaasur13-sys/astrofin-sentinel-platform` @ `master` (post PR #199)
**Branch state:** clean (36bb943, ahead 0 / behind 0)

---

## STEP 1 — Workspace Inventory & Structural Snapshot

### 1.1 High-Level Metrics

| Metric | Value |
|---|---|
| **Repo size** (excl. `.git`, `__pycache__`, `.venv`, `node_modules`) | ~500+ directories |
| **Source files** (excl. venv/cache) | **1,503** |
| **Python files** | **756** (50.3%) |
| **Markdown** | 217 |
| **YAML/YML** | 186 |
| **Shell scripts** | 86 |
| **JSON** | 49 |
| **Jinja2 templates** | 30 |
| **Terraform** | 29 |
| **SQL** | 14 |
| **TOML** | 5 |
| **Top-heavy dirs** | `graphify-out/` (43M), `data/` (1.9M), `models/` (1.8M), `deploy/` (1.6M), `src/` (1.2M) |
| **Submodule markers** | **0** (clean inlining confirmed) |
| **Top-level .py scripts** | 6 (FINAL_INTEGRATION_TEST, data_provider, health_endpoints, langgraph_schema, muhurtha, test_aspects) |
| **Last 5 commits** | PR #199 (metrics), PR #198 (xfail→pass), PR #194 (GPU shlex), PR #193 (ROMA shlex), PR #192 (bare except) |

### 1.2 Top-Level Architecture (5-Product Monolith)

Per `README.md`, this is a **unified monorepo** of 4 inline products:

| # | Path | Origin | Domain |
|---|---|---|---|
| 1 | `/` (root) | `push/` | KARL/AMRE orchestration, meta-RL, web dashboard, astro agents |
| 2 | `infrastructure/asurdev/` *(expected: `deploy/iac/`)* | `AsurDev/` | Home-cluster IaC, ACOS admission controllers, monitoring |
| 3 | `kernel/atom-federation/` *(expected: `atom-core/`)* | `atom-federation-os/` | Deterministic alignment kernel, formal verification, K8s operator |
| 4 | `bridge/roma/` *(expected: `src/bridges/roma/`)* | `roma-execution-bridge/` | GPU execution bridge, SaaS billing, Stripe webhooks |

> ⚠️ **Drift finding #1:** README.md claims paths `infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/`, but the **actual filesystem has** `deploy/iac/`, `atom-core/`, `src/bridges/roma/`. Either the README is wrong or the path migration is incomplete. **Critical to verify.**

### 1.3 Actual Top-Level Structure (44 dirs)

**Core product (root):**
- `agents/` (489K) — KARL/AMRE agents (`_impl/` active, `_archived/` legacy)
- `core/` (375K) — ephemeris, aspects, history_db, volatility, checkpoint
- `orchestration/` — Sentinel V5, router, MAS
- `meta_rl/` (481K) — meta-RL pipeline, A/B testing, quant/risk (renamed in PR #199)
- `trading/` (130K) — execution, broker
- `web/` (146K) — FastAPI/Dash dashboard
- `knowledge/` (321K) — RAG, FAISS, daily-digest
- `models/` (1.8M) — ML model artifacts
- `data/` (1.9M) — SQLite DBs, session history
- `observability/`, `monitoring/` — Prometheus exporters, OTel
- `trading/`, `trading/broker/`, `trading/execution/`

**Infrastructure sub-projects:**
- `atom-core/` — atom-router pkg, contract bindings (likely inlined atom-federation)
- `acos-contracts/` — ACOS event sourcing contracts
- `src/bridges/roma/` — full ROMA tree (audit, auth, billing, charts, control_plane, gpu_worker, saas, …)
- `deploy/iac/` — ACOS, ansible roles (argocd, ceph, k8s, slurm, wireguard, monitoring), Terraform modules, Prometheus/Grafana
- `pop-os-setup/` — installer + sandbox integrity engine (v11.x stage files)
- `mas_factory/` — multi-agent system factory

**Test surface:**
- `tests/` (513K) — unit, integration, e2e, architecture, auth, data_room, error_handling, knowledge, load, observability, loopcraft, ralph_benchmark
- Test files: 150+ expected

**Tooling & docs:**
- `tools/`, `scripts/`, `docs/` (adr, api, architecture, archive, db, deploy, monitoring, refactor, security, sprints)
- `graphify-out/` (43M) — **⚠️ SUSPICIOUS** — likely graph-rendered output of docs

### 1.4 AGENTS.md vs. Reality — Cross-Check

The AGENTS.md says: *"Каждый агент использует `@require_ephemeris` декоратор"* and *"Active Modules: Only use agent implementations from `agents/_impl/`"*.

**Real `agents/_impl/` modules found:**
- 13 base agents (fundamental, macro, quant, options_flow, sentiment, bull_researcher, bear_researcher, bradley, gann, cycle, time_window)
- `astro_council/agent.py` — full AstroCouncilAgent
- `ml_predictor_agent.py`, `risk_agent.py`, `insider_agent.py`, `elliot_agent.py`
- `types.py` (AgentResponse, TradingSignal, SignalDirection)
- `ephemeris_decorator.py` (require_ephemeris)
- `amre/` (15 modules: audit, backtest_loop, karl_integration, reward, oap_optimizer, etc.)

**Archived (`_archived/`):** 7 duplicates, presumably one per legacy root-level agent.

> ⚠️ **Drift finding #2:** AGENTS.md still references paths like `cd /home/workspace/AstroFinSentinelV5` (the old standalone repo) in Usage section. This is **stale documentation** from pre-monorepo era.

### 1.5 pyproject.toml — Package Configuration

- **name**: `astrofin-sentinel-v5` v1.0.0 (still v1 — should be v5 per project name)
- **Python**: ≥3.10
- **Deps**: 25+ runtime, focused on numerics + astro + KARL + FastAPI + OTel
- **Entry points**: `astrofin`, `astrofin-karl`, `astrofin-dashboard` (via orchestration.sentinel_v5, karl_cli, web.wsgi)
- **Pytest coverage**: agents, core, data_room, observability; `--cov-fail-under=3` (very low threshold)
- **Ruff**: excludes 19+ directories (orchestration, meta_rl, trading, web, agents, knowledge, deploy/iac, src, atom-core, etc.) — **⚠️ most code is NOT linted!**
- **Bandit**: skips B608 (SQL injection) — risky if any external input ever reaches `history_db.py`

### 1.6 Git State

```
36bb943 chore(phase-a): consolidate metrics — delete empty + rename to risk.py (#199)
aaca760 test(stabilize): Phase 5.A — fix test ordering and convert xfail→pass (#198)
d94d5df fix(security): replace shell=True with shlex.split in GPU worker (#194)
a6b0cd9 fix(security): replace shell=True with shlex.split in ROMA scheduler (#193)
0ec0b69 fix(security): narrow bare except in AsyncWebhookQueue._load (#192)
```

Clean. No uncommitted changes. PR #199 (Phase A metrics cleanup) just merged — `meta_rl/quant/metrics.py` → `meta_rl/quant/risk.py`, deleted `src/bridges/roma/observability/metrics.py`.

---

## 🚩 Initial Findings (consolidated)

### F-01: **README.md ↔ Filesystem path drift** (HIGH)
README claims `infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/`. Actual: `deploy/iac/`, `atom-core/`, `src/bridges/roma/`. Affects Quickstart, CLI examples, and Architecture diagram. **Either migrate the paths in the code or fix the README.**

### F-02: **AGENTS.md references pre-monorepo workspace** (MEDIUM)
Usage example: `cd /home/workspace/AstroFinSentinelV5`. Project is now at `/home/workspace/Projects/asp-canonical-real/`. **Update all path examples.**

### F-03: **pyproject.toml version mismatch** (LOW)
Name says `astrofin-sentinel-v5` (v1.0.0), but actual is v5 with hybrid signal architecture. **Bump to 5.0.0 to match semantic intent.**

### F-04: **Ruff excludes nearly the entire codebase** (HIGH)
~90% of source dirs (orchestration, meta_rl, trading, web, agents, knowledge, deploy, src, atom-core) are excluded from linting. Linter provides almost no value. **This is the #1 hygiene risk.**

### F-05: **Bandit B608 disabled** (MEDIUM)
SQL injection check disabled. Comment says it's only internal allow-list — needs manual audit of `core/history_db.py` and any module that builds SQL from strings.

### F-06: **Coverage threshold `--cov-fail-under=3` is 3%** (HIGH)
3% means almost any test loss keeps CI green. This is a CI quality issue, not a coverage issue per se.

### F-07: **`graphify-out/` 43MB** (LOW)
Likely build artifact of doc-graph visualization. Should be git-ignored or generated on-demand. Not source code.

### F-08: **6 root-level `.py` files** (LOW)
`FINAL_INTEGRATION_TEST.py`, `data_provider.py`, `health_endpoints.py`, `langgraph_schema.py`, `muhurtha.py`, `test_aspects.py` — may be either test scripts (should be in `tests/`) or shared entry points (should be documented).

### F-09: **5 sub-product "factions" with overlapping responsibilities** (HIGH)
- `meta_rl/quant/` (just renamed to risk.py in PR #199)
- `agents/_impl/` (KPI/audit/reward/oap_optimizer)
- `core/` (volatility, history_db)
- `src/bridges/roma/observability/` (was metrics.py, deleted)
- `deploy/iac/` (constraint_compiler, l9_ebl, l10_self_healing)

Likely a **shadow metrics/KPI/policy** family split across 4+ places. Need to map responsibilities.

### F-10: **Test count "561 passed" per recent context, but structure scattered**
`tests/` has 11 sub-dirs: unit, integration, e2e, architecture, auth, data_room, error_handling, knowledge, load, observability, loopcraft, ralph_benchmark. Real coverage is unclear without running the full suite.

---

## 📋 Next Proposed Actions (Step 2)

In Step 2, I will:
1. **Verify the path drift** (F-01) — search for any `infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/` references in code/CI
2. **Map the 5 sub-products** to actual filesystem paths and produce a **canonical paths table**
3. **Run the test suite** to confirm current 561/0/69 baseline
4. **Inventory duplicates/orphans** (especially `core/metrics.py` vs `agents/metrics.py` — known F2 WIP per context)
5. **Identify the "shadow metrics/KPI/policy" family** across meta_rl/quant, agents/_impl, core, deploy/iac

### Prompt for continuation

> **Продолжай Шаг 2:** картирование путей и теневых модулей. Покажи:
> 1. Реальные пути vs заявленные в README — какие файлы/CI-команды сломаны
> 2. Карта "shadow families" — где живут metrics/KPI/policy/audit (с file refs и LOC)
> 3. Полный список root-level orphan-скриптов с их реальной ролью
> 4. Результат прогона `pytest -q --collect-only | tail -10` (быстрая проверка тестовой базы)
> 5. Топ-10 крупнейших `.py` файлов в проекте (≥ 500 LOC) — кандидаты на декомпозицию
