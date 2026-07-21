# Architecture & Code Audit Report — AstroFin Sentinel Platform

**Date:** 2026-07-21  
**Auditor:** Senior Architect & Code Auditor (Zo Agent)  
**Scope:** Full workspace + all 24 connected GitHub repositories  
**Report Version:** 1.0 (Step 1 — Inventory & Baseline)

---

## Executive Summary

Проведён глубокий аудит единого master-проекта AstroFin Sentinel Platform. Выявлена **критическая проблема дублирования**: workspace root (`/home/workspace`) и подпапка `astrofin-sentinel-platform/` содержат **один и тот же Git-репозиторий**, но с **разной степенью синхронизации**. Из 54 top-level директорий — **43 дублируются** (80%). Из 38+ `.md` файлов корня — **все дублируются** внутри `astrofin-sentinel-platform/`.

Проект — это **монолитное Python-ядро** (290K LOC) с React-фронтендом (278K TS/TSX LOC), 27 активными AI-агентами, оркестратором, KARL-синтезом, RAG-слоем и инфраструктурным кодом (K8s, Docker, CI/CD).

---

## 1. Inventory Map

### 1.1 Primary Git Repositories (Source of Truth)

| Repository | GitHub | Relevance | Branch | Status |
|---|---|---|---|---|
| **astrofin-sentinel-platform** | `mahaasur13-sys/astrofin-sentinel-platform` | **PRIMARY** — основной продукт | `feature/architecture-consolidation` (local), `master` (remote HEAD) | Активно разрабатывается |
| astrofin-sentinel-v5 | `mahaasur13-sys/astrofin-sentinel-v5` | Предшественник (legacy) | `main` | Заморожен |
| AstroFinSentinelV5 | `mahaasur13-sys/AstroFinSentinelV5` | Старый репо (пустой локально) | `master` | Archived |
| AsurDev | `mahaasur13-sys/AsurDev` | Пустой локально | `main` | Unknown |

### 1.2 Federation / ATOM Ecosystem (Sister Projects)

| Repository | Purpose |
|---|---|
| **astrofin-federation-stack** | Federation stack: ATOM kernel + ROMA bridge + AsurDev infra |
| **atom-federation-os** | Federation OS monorepo |
| **ATOMFederationOS** | GoA, REDEREF, DESC event-sourcing, K8s controllers |
| **atom-federation** | Federation + messaging (MessageQueue, Gossip, BFT) |
| **atom-federation-core** | K8s control plane: deterministic controllers, EventStore |
| **atom-kernel** | Deterministic execution kernel (clock, UUID, RNG, GEB) |
| **atom-agent** | Deterministic agent executor (sandbox, checkpoint, SBS) |
| **atom-operator** | K8s Operator (CRDs: ATOMCluster, Workflow, Task) |
| **atom-runtime** | Runtime layer |
| **atom-router** | REDEREF-style adaptive router (Thompson sampling, cost-aware) |
| **roma-execution-bridge** | ROMA execution bridge |
| **home-cluster-iac** | Home cluster infrastructure-as-code |

### 1.3 Infra/Support Repos

| Repository | Purpose |
|---|---|
| **pop-os-setup** | Pop!_OS 24.04 workstation auto-setup (26 stages) |
| **integrations-gitagent** | GitAgent MCP integration |
| **_afs_token_probe_DO_NOT_USE** | Token probe (should be deleted) |
| **VIMANA_MAIN_PROJECT_SHANTI** | DDEV-проект SHANTI (legacy) |
| **ollama-transfer-template** | Ollama transfer template (legacy) |

### 1.4 Workspace Physical Layout

```
/home/workspace/                          ← GIT REPO (same as astrofin-sentinel-platform)
├── .git/                                 ← points to astrofin-sentinel-platform
├── astrofin-sentinel-platform/           ← ALSO A GIT REPO (same remote!)
│   ├── agents/                           ← 27 active agents in _impl/
│   ├── api/                              ← FastAPI back-end
│   ├── core/                             ← ~45 core modules (ephemeris, aspects, auth, etc.)
│   ├── orchestration/                    ← sentinel_v5.py, router, council orchestration
│   ├── web/                              ← Dash (legacy UI)
│   ├── web-react/                        ← React + Vite + Redux (current UI)
│   ├── data_room/                        ← Data access layer (blueprint)
│   ├── knowledge/                        ← RAG + FAISS/pgvector indexes
│   ├── trading/                          ← Backtester, safety gate, portfolio, monitoring
│   ├── meta_rl/                          ← Thompson Sampling, AB testing
│   ├── db/                               ← SQLAlchemy models + migrations
│   ├── tests/                            ← 120 test files
│   ├── docs/                             ← 80+ .md docs incl. 9 ADRs
│   ├── v6/, v7/, v8/                     ← Version snapshots (7-10 files each)
│   ├── audit_repo/                       ← 485 files — legacy audit copy
│   ├── deploy/, infrastructure/, k8s/    ← DevOps artifacts
│   └── ...
├── [43 DUPLICATE directories]            ← Mirror astrofin-sentinel-platform/
├── [38 DUPLICATE .md files]              ← Mirror astrofin-sentinel-platform/
└── [7 DUPLICATE .py files at root]       ← Mirror astrofin-sentinel-platform/
```

### 1.5 Empty/Derelict Directories

| Directory | Status |
|---|---|
| `AstroFinSentinelV5/` | Empty — legacy placeholder |
| `AsurDev/` | Empty — legacy placeholder |
| `astrofin-sentinel-v5/` | Empty — legacy placeholder |
| `roma-execution-bridge/` | Empty — legacy placeholder |
| `home-cluster-iac/` | Empty — legacy placeholder |
| `pop-os-setu` | Stale file (typo'd name) |

---

## 2. Duplication Analysis

### 2.1 Directory Duplication (Root vs Platform)

**43 из 54 директорий корня** дублируются внутри `astrofin-sentinel-platform/`:

```
acos-contracts, ai_scheduler, artifacts, astrology, atom-core,
audit_repo, bench, bridge, common, config, data, db, deploy,
docs, examples, feature_pipeline, gpu_worker, infrastructure,
k8s, kernel, l10_self_healing, l11_verifier, l9_ebl, mas_factory,
migrations, migrations_postgres, ml_engine, models, monitoring,
pop-os-setup, research, scheduler_v3, schema, scripts, security,
slsa4, src, strategies, tests, tools, training, v6, v7, v8
```

**Root-only directories** (10): `AstroFinSentinelV5`, `AsurDev`, `Knowledge`, `Trash`, `astrofin-sentinel-platform`, `astrofin-sentinel-v5`, `home-cluster-iac`, `reports`, `roma-execution-bridge`, `utils`

### 2.2 File Duplication

| Type | Count | Examples |
|---|---|---|
| Markdown docs | **38 files** | `AGENTS.md`, `SOUL.md`, `AUDIT_*.md`, `SPRINT_*.md`, etc. |
| Python files (root) | **7 files** | `data_provider.py`, `health_endpoints.py`, `langgraph_schema.py`, `logging_setup.py`, `muhurtha.py`, `test_aspects.py`, `FINAL_INTEGRATION_TEST.py` |
| Config files | Multiple | `.coderabbit.yaml`, `.pre-commit-config.yaml`, `.flake8`, `.gitleaks.toml`, `Dockerfile`, `Makefile`, `docker-compose.yml`, etc. |

### 2.3 Git Repository Identity Crisis

Корень и `astrofin-sentinel-platform/` — это **один и тот же Git remote** (`mahaasur13-sys/astrofin-sentinel-platform`), но они могут расходиться в состоянии:

```bash
# Root: branch feature/architecture-consolidation (HEAD: 85e039f)
# Platform: branch feature/architecture-consolidation (HEAD: 85e039f)  
# Current: identical HEAD — но структура разная!
```

**Проблема:** Git-операции в корне затрагивают только файлы корня. Файлы внутри `astrofin-sentinel-platform/` отслеживаются *отдельным* git-репозиторием. Это означает, что `git push` из корня не отправляет изменения из `astrofin-sentinel-platform/`, и наоборот.

---

## 3. Architecture Map

### 3.1 Monolith Structure

```
┌─────────────────────────────────────────────────────────┐
│                   ASTROFIN SENTINEL V5                   │
├─────────────────────────────────────────────────────────┤
│  ENTRY POINTS                                            │
│  ├── orchestration/sentinel_v5.py     (CLI)              │
│  ├── api/main.py                      (FastAPI)          │
│  ├── web/app.py                       (Dash legacy)      │
│  └── web-react/                       (React SPA)        │
├─────────────────────────────────────────────────────────┤
│  AGENT LAYER (27 agents)                                 │
│  ├── agents/base_agent.py             (BaseAgent)        │
│  ├── agents/_impl/types.py            (TradingSignal)    │
│  ├── agents/_impl/     ← 27 active implementations       │
│  │   ├── fundamental_agent.py   (20%)                    │
│  │   ├── quant_agent.py         (20%)                    │
│  │   ├── macro_agent.py         (15%)                    │
│  │   ├── options_flow_agent.py  (15%)                    │
│  │   ├── sentiment_agent.py     (10%)                    │
│  │   ├── technical_agent.py     (10%)                    │
│  │   ├── bull_researcher.py     (5%)                     │
│  │   ├── bear_researcher.py     (5%)                     │
│  │   ├── cycle_agent.py         (5%)                     │
│  │   ├── bradley_agent.py       (3%)                     │
│  │   ├── electoral_agent.py     (3%)                     │
│  │   ├── gann_agent.py          (3%)                     │
│  │   ├── time_window_agent.py   (2%)                     │
│  │   ├── elliot_agent.py        (—)                      │
│  │   ├── hmm_regime_agent.py    (—)                      │
│  │   ├── insider_agent.py       (—)                      │
│  │   ├── risk_agent.py          (—)                      │
│  │   ├── ml_predictor_agent.py  (—)                      │
│  │   ├── compromise_agent.py    (—)                      │
│  │   ├── astro_council/agent.py (coordinator)            │
│  │   └── synthesis_agent.py     (KARL synthesis)         │
│  └── agents/_archived/      ← 7 archived duplicates      │
├─────────────────────────────────────────────────────────┤
│  CORE LAYER (~45 modules)                                │
│  ├── ephemeris.py       (Swiss Ephemeris wrapper)        │
│  ├── aspects.py         (Astrological aspects engine)     │
│  ├── panchanga.py       (Hindu calendar)                 │
│  ├── houses.py          (Astrological houses)            │
│  ├── volatility.py      (Volatility regime)              │
│  ├── history_db.py      (SQLite session persistence)     │
│  ├── checkpoint.py       (State checkpointing)            │
│  ├── auth_jwt.py         (JWT authentication)             │
│  ├── thompson.py         (Thompson sampling)              │
│  ├── kepler*.py          (Kepler calibration models)     │
│  ├── rag_client.py       (RAG client)                    │
│  ├── ensemble_voting.py  (Ensemble consensus)            │
│  └── ...                                                 │
├─────────────────────────────────────────────────────────┤
│  DATA LAYER                                              │
│  ├── data_room/blueprint.py  (Data access contract)      │
│  ├── data_room/resolvers/    (API resolvers)             │
│  ├── db/models.py            (SQLAlchemy models)         │
│  ├── db/session.py           (DB sessions)               │
│  └── knowledge/              (RAG index)                 │
├─────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE                                          │
│  ├── Dockerfile + docker-compose.yml                     │
│  ├── deploy/docker/, deploy/iac/, k8s/                   │
│  ├── .github/workflows/      (CI/CD)                    │
│  └── .pre-commit-config.yaml (Code quality)              │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, LangGraph, PyTorch, FAISS, pgvector |
| **Frontend** | React 19, TypeScript 6, Vite 8, Redux Toolkit, React Router 7 |
| **Database** | PostgreSQL + TimescaleDB + pgvector (primary), SQLite (fallback) |
| **Cache** | Redis |
| **ML/RL** | Thompson Sampling, HMM, PPO, Custom Reward Models (AMRE) |
| **Astro** | Swiss Ephemeris (pyswisseph), Panchanga, Vedic |
| **Observability** | OpenTelemetry, structlog, Prometheus, Grafana |
| **Infra** | Docker, Kubernetes (k3s), Helm, ArgoCD |
| **CI/CD** | GitHub Actions, pre-commit hooks (Ruff, Bandit, gitleaks) |

### 3.3 Lines of Code

| Type | Lines |
|---|---|
| Python | **290,209** |
| TypeScript/TSX | **278,520** |
| Markdown (docs) | **84,970** |
| **Total** | **~653,699** |

---

## 4. Key Findings (Step 1)

### 🔴 Critical

### 🔴 Critical — CONFIRMED: File Drift Between Root and Platform

| File | Root Size | Platform Size | Verdict |
|---|---|---|---|
|  | 19,261 B | 23,765 B | **DIFFER** — platform версия новее (7.5K больше) |
|  | 4,642 B | 4,642 B | ✅ IDENTICAL |
|  | 486 B | 507 B | **DIFFER** |
|  | 1,432 B | 4,732 B | **DIFFER** — platform версия в 3.3× больше |
|  | 9,893 B | 11,749 B | **DIFFER** — platform версия новее |

**Вывод:** Platform-версии — авторитетные. Root-версии устарели. Это доказывает, что активная разработка велась в , а root — замороженная копия.

| # | Finding | Impact |
|---|---|---|
| **F-1** | **Double Git repo** — root и `astrofin-sentinel-platform/` указывают на один remote, но независимы | Git push из корня ≠ push из platform. Неопределённость source of truth. |
| **F-2** | **43 дублирующихся директорий** (80% от всех) | Кто редактирует корень, кто platform? Дрейф контента неизбежен. |
| **F-3** | **38 дублирующихся .md файлов** | AGENTS.md, SOUL.md, AUDIT_*.md — какая версия авторитетна? |

### 🟠 High

| # | Finding | Impact |
|---|---|---|
| **F-4** | **6 пустых директорий** — `AstroFinSentinelV5`, `AsurDev`, `astrofin-sentinel-v5`, etc. | Мусор, сбивает с толку при навигации |
| **F-5** | **audit_repo/** — 485 файлов, дублирует функциональность `agents/`, `core/`, `web/` | Устаревшая копия; может содержать secrets |
| **F-6** | **v6, v7, v8** — старые version snapshots (7-10 файлов каждая) | Неиспользуемый код; занимает место |
| **F-7** | **venv без pytest и ruff** — `pip list` показывает только 16 пакетов | Невозможно запустить тесты и линтер локально |
| **F-8** | **7 корневых .py файлов** — дубликаты `data_provider.py`, `muhurtha.py` etc. | Какая версия импортируется? |

### 🟡 Medium

| # | Finding | Impact |
|---|---|---|
| **F-9** | **24 GitHub репозитория** — многие архивные/неактивные (`_afs_token_probe_DO_NOT_USE`, `VIMANA_MAIN_PROJECT_SHANTI`) | Шум в GitHub org |
| **F-10** | **11 веток на remote** — 4 dependabot, 3 feature, main, master | Ветки `main` и `master` расходятся |
| **F-11** | **AGENTS.md (19K) + SOUL.md (4.6K)** — богатая, но частично противоречивая документация | AGENTS.md говорит "7 корневых дублей архивированы", но они до сих пор на месте |
| **F-12** | **456 .md файлов** — документационный шум | Многие устарели (SPRINT_1.md, DAILY_REPORT_*.md) |

### ⚪ Low

| # | Finding |
|---|---|
| **F-13** | `pop-os-setu` — файл с опечаткой в имени |
| **F-14** | `.patch_optionb.py` — патч-файл в корне |
| **F-15** | `nano` — файл без расширения в корне |

---

## 5. GitHub Repository Health

### Active (разрабатываются)
- ✅ `astrofin-sentinel-platform` — основной продукт

### Sister (связанные, активны)
- ✅ `astrofin-federation-stack`, `atom-federation-os`, `ATOMFederationOS`
- ✅ `atom-kernel`, `atom-agent`, `atom-operator`, `atom-federation-core`
- ✅ `atom-router`, `roma-execution-bridge`, `home-cluster-iac`

### Standalone Utility
- ✅ `pop-os-setup`, `integrations-gitagent`

### Dead / To Be Archived
- ❌ `_afs_token_probe_DO_NOT_USE` — удалить
- ❌ `VIMANA_MAIN_PROJECT_SHANTI` — legacy
- ❌ `ollama-transfer-template`, `ollama-transfer-templateRobot` — legacy
- ❌ `asurdev-workspace-backup-20260326` — старый backup

---

## 6. Next Steps (Step 2)

Перед началом глубокого аудита (Шаг 2) необходимо **разрешить проблему дублирования (F-1, F-2, F-3)**:

### Priority A: Resolve Source of Truth

1. **Подтвердить:** какой путь — корень или `astrofin-sentinel-platform/` — должен быть **единственным source of truth**.
2. **Вариант A:** Удалить `astrofin-sentinel-platform/` как подпапку, работать только в корне.
3. **Вариант B:** Перенести все изменения в `astrofin-sentinel-platform/`, сделать корень чистым gateway.
4. **Рекомендация:** Вариант B — `astrofin-sentinel-platform/` как source of truth, корень очистить.

### Priority B: Cleanup

5. Удалить 6 пустых директорий.
6. Архивировать `v6/`, `v7/`, `v8/`, `audit_repo/`.
7. Удалить 7 дублирующихся `.py` файлов из корня.
8. Консолидировать 38 `.md` файлов — выбрать авторитетные версии.

### Priority C: Begin Deep Audit (Step 2)

После консолидации — глубокий аудит по всем категориям.

---

## Appendix A: Full Directory Comparison

| Directory | Root | Platform | Verdict |
|---|---|---|---|
| acos-contracts | ✅ | ✅ | DUPLICATE |
| ai_scheduler | ✅ | ✅ | DUPLICATE |
| artifacts | ✅ | ✅ | DUPLICATE |
| astrology | ✅ | ✅ | DUPLICATE |
| atom-core | ✅ | ✅ | DUPLICATE |
| audit_repo | ✅ | ✅ | DUPLICATE |
| bench | ✅ | ✅ | DUPLICATE |
| bridge | ✅ | ✅ | DUPLICATE |
| common | ✅ | ✅ | DUPLICATE |
| config | ✅ | ✅ | DUPLICATE |
| data | ✅ | ✅ | DUPLICATE |
| db | ✅ | ✅ | DUPLICATE |
| deploy | ✅ | ✅ | DUPLICATE |
| docs | ✅ | ✅ | DUPLICATE |
| examples | ✅ | ✅ | DUPLICATE |
| feature_pipeline | ✅ | ✅ | DUPLICATE |
| gpu_worker | ✅ | ✅ | DUPLICATE |
| infrastructure | ✅ | ✅ | DUPLICATE |
| k8s | ✅ | ✅ | DUPLICATE |
| kernel | ✅ | ✅ | DUPLICATE |
| l10_self_healing | ✅ | ✅ | DUPLICATE |
| l11_verifier | ✅ | ✅ | DUPLICATE |
| l9_ebl | ✅ | ✅ | DUPLICATE |
| mas_factory | ✅ | ✅ | DUPLICATE |
| migrations | ✅ | ✅ | DUPLICATE |
| migrations_postgres | ✅ | ✅ | DUPLICATE |
| ml_engine | ✅ | ✅ | DUPLICATE |
| models | ✅ | ✅ | DUPLICATE |
| monitoring | ✅ | ✅ | DUPLICATE |
| pop-os-setup | ✅ | ✅ | DUPLICATE |
| research | ✅ | ✅ | DUPLICATE |
| scheduler_v3 | ✅ | ✅ | DUPLICATE |
| schema | ✅ | ✅ | DUPLICATE |
| scripts | ✅ | ✅ | DUPLICATE |
| security | ✅ | ✅ | DUPLICATE |
| slsa4 | ✅ | ✅ | DUPLICATE |
| src | ✅ | ✅ | DUPLICATE |
| strategies | ✅ | ✅ | DUPLICATE |
| tests | ✅ | ✅ | DUPLICATE |
| tools | ✅ | ✅ | DUPLICATE |
| training | ✅ | ✅ | DUPLICATE |
| v6 | ✅ | ✅ | DUPLICATE |
| v7 | ✅ | ✅ | DUPLICATE |
| v8 | ✅ | ✅ | DUPLICATE |
| AstroFinSentinelV5 | ✅ | ❌ | ROOT-ONLY (empty) |
| AsurDev | ✅ | ❌ | ROOT-ONLY (empty) |
| Knowledge | ✅ | ❌ | ROOT-ONLY |
| Trash | ✅ | ❌ | ROOT-ONLY (system) |
| astrofin-sentinel-v5 | ✅ | ❌ | ROOT-ONLY (empty) |
| home-cluster-iac | ✅ | ❌ | ROOT-ONLY (empty) |
| reports | ✅ | ❌ | ROOT-ONLY |
| roma-execution-bridge | ✅ | ❌ | ROOT-ONLY (empty) |
| utils | ✅ | ❌ | ROOT-ONLY |
| agents | ❌ | ✅ | PLATFORM-ONLY |
| api | ❌ | ✅ | PLATFORM-ONLY |
| backtest | ❌ | ✅ | PLATFORM-ONLY |
| core | ❌ | ✅ | PLATFORM-ONLY |
| data_room | ❌ | ✅ | PLATFORM-ONLY |
| integrations | ❌ | ✅ | PLATFORM-ONLY |
| knowledge | ❌ | ✅ | PLATFORM-ONLY |
| logs | ❌ | ✅ | PLATFORM-ONLY |
| meta_rl | ❌ | ✅ | PLATFORM-ONLY |
| observability | ❌ | ✅ | PLATFORM-ONLY |
| orchestration | ❌ | ✅ | PLATFORM-ONLY |
| trading | ❌ | ✅ | PLATFORM-ONLY |
| web | ❌ | ✅ | PLATFORM-ONLY |
| web-react | ❌ | ✅ | PLATFORM-ONLY |

**Итого:** 43 дубликата, 10 root-only (6 пустых), 13 platform-only (основной код).
