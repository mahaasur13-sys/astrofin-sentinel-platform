# 🔍 AstroFin Sentinel Platform — Step 1: Inventory & Architecture Map

**Date:** 2026-07-21
**Auditor:** Zo Computer (Senior Architect & Code Auditor)
**Scope:** Full workspace + GitHub repos + branches

---

## 1. Executive Summary

Единый master-проект — **AstroFin Sentinel Platform**. Это монорепо в репозитории `mahaasur13-sys/astrofin-sentinel-platform`. Обнаружено, что workspace root (`/home/workspace`) сам является git-репозиторием, указывающим на тот же origin, но **все активные файлы дублируются** — в root и в `astrofin-sentinel-platform/`. Platform-версии файлов — авторитетные (новее и полнее). Root — замороженный клон.

## 2. Repository Inventory

### 2.1 Primary Repository (ACTIVE)

| Параметр | Значение |
|---|---|
| **Repo** | `mahaasur13-sys/astrofin-sentinel-platform` |
| **Active branch** | `feature/architecture-consolidation` (workspace) |
| **Remote branches** | `master`, `main`, `feature/architecture-consolidation`, `feat/calendar-visualizer`, `feat/council-orchestrator-wireup`, `feat/hmm-risk-karl-v2` |
| **Dependabot** | 3 active (Azure kubectl, Docker login, pip dev+prod) |
| **Last commit** | `85e039f` — "fix: Gann price uses real CoinGecko data (~$64k)" (2026-07-20) |

### 2.2 Satellite GitHub Repositories

| Repo | Status | Relevance |
|---|---|---|
| `astrofin-sentinel-v5` | Archive | Предок Sentinel V5 (исходный) |
| `AstroFinSentinelV5` | Archive | Другой архивный слепок |
| `AsurDev` (1.1) | Archive | Инфраструктурные конфиги |
| `atom-federation-os` | Frozen | ATOM kernel + ROMA bridge |
| `atom-federation-core` | Frozen | K8s control plane |
| `atom-kernel`, `atom-agent`, `atom-operator`, `atom-runtime`, `atom-federation` | Frozen | ATOM экосистема (v10) |
| `atom-router` | Frozen | REDEREF router v10 |
| `ATOMFederationOS` | Frozen | GoA + Go implementation |
| `astrofin-federation-stack` | Frozen | Federation stack |
| `home-cluster-iac` | Active? | Home cluster IAC |
| `pop-os-setup` | Active | Pop!_OS setup scripts |
| `integrations-gitagent` | Active? | GitAgent MCP integration |
| `_afs_token_probe_DO_NOT_USE` | Dead | Удалить |

**Вывод:** Из 23 репозиториев — **1 активный** (astrofin-sentinel-platform), 2 смежных активных (pop-os-setup, home-cluster-iac), остальные — замороженные/архивные.

### 2.3 Workspace Layout

```
/home/workspace/                          ← Git repo (root) — замороженный клон
├── AGENTS.md                             ← УСТАРЕЛ (19K vs 24K в platform)
├── SOUL.md                               ← ИДЕНТИЧЕН с platform
├── requirements.txt / pyproject.toml     ← УСТАРЕЛИ
├── astrofin-sentinel-platform/           ← **АКТИВНАЯ РАЗРАБОТКА** (тот же origin!)
│   ├── agents/_impl/                     ← 27 agents (реализации)
│   ├── core/                             ← ~50 модулей (ephemeris, aspects, auth, volatility...)
│   ├── orchestration/                    ← sentinel_v5, karl_cli, router
│   ├── api/                              ← FastAPI main
│   ├── web-react/                        ← React 19 + Vite 8 + Redux Toolkit
│   ├── web/                              ← Dash (legacy)
│   ├── tests/                            ← ~120 test files
│   ├── docs/                             ← ~80 .md файлов
│   ├── deploy/ / k8s/                    ← Docker + K8s манифесты
│   └── data_room/ / knowledge/ / meta_rl/ ← Специализированные слои
├── v6/ v7/ v8/                           ← Version snapshots (24 files total)
├── audit_repo/                           ← 485 archived files
└── [43 DUPLICATE directories]            ← Копии из platform в root
```

## 3. Architecture Map

### 3.1 Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **Backend runtime** | Python 3.12 | 3.12+ |
| **API framework** | FastAPI | 0.139.2 |
| **Orchestration** | LangGraph (custom schema) | — |
| **ML/RL** | Thompson Sampling, Meta-RL, Bayesian belief | — |
| **Astro engine** | Swiss Ephemeris (pyswisseph) | 2.10.3.2 |
| **Frontend (new)** | React 19 + Vite 8 + Redux Toolkit | Latest |
| **Frontend (legacy)** | Plotly Dash | — |
| **Database** | SQLite → PostgreSQL + TimescaleDB + pgvector (migration WIP) | — |
| **Vector DB** | FAISS / pgvector | — |
| **Caching** | Redis | — |
| **Container** | Docker + docker-compose | — |
| **Orchestration** | Kubernetes (k3s) | — |
| **CI/CD** | GitHub Actions, pre-commit hooks | — |
| **Linting** | Ruff, Bandit, gitleaks, mypy | — |
| **Observability** | OpenTelemetry, structlog, Prometheus | — |

### 3.2 Agent Board (27 agents)

```
agents/_impl/  ← 27 реализаций
├── 🟢 Core (15): fundamental, macro, quant, options_flow, sentiment,
│                 technical, bull_researcher, bear_researcher,
│                 bradley, electoral, time_window, gann, cycle, elliot, synthesis
├── 🟡 Specialized (8): hmm_regime, ml_predictor, risk, insider,
│                        market_analyst, compromise, ephemeris_decorator
├── 🟣 Astro Council: astro_council/agent.py (228 lines)
├── ⚪ AMRE: amre/ (15 modules: audit, backtest, karl, oap, reward...)
└── 📋 types.py — AgentResponse, TradingSignal, SignalDirection
```

### 3.3 Module Map

```
astrofin-sentinel-platform/
│
├── agents/           ← Agent implementations (54 .py files)
├── core/             ← Core engine (~50 modules)
│   ├── ephemeris.py  ← Swiss Ephemeris wrapper
│   ├── aspects.py     ← Aspects engine
│   ├── volatility.py  ← Dynamic risk engine
│   ├── auth_jwt.py    ← JWT auth
│   ├── history_db.py  ← SQLite session persistence
│   └── ...
├── orchestration/    ← Run loop & coordination
├── api/              ← FastAPI endpoints
├── web-react/        ← React 19 SPA (15 TS/TSX files)
├── web/              ← Dash legacy
├── data_room/        ← Data access layer (R-01 boundary)
├── knowledge/        ← RAG + vector index
├── meta_rl/          ← Meta-RL training & AB testing
├── trading/          ← Execution, risk, safety gates
├── tools/            ← CLI tools (healthcheck, run_agents, migrations...)
├── tests/            ← 120 test files
├── docs/             ← 80+ архитектурных документов
│   ├── adr/          ← 9 ADR
│   ├── audit/        ← Аудиты
│   ├── security/     ← Threat model, SOC2
│   └── sprints/      ← Sprint planning
├── deploy/           ← Docker, K8s, IAC
├── scripts/          ← CI scripts, validation
└── integrations/     ← Telegram, GitAgent MCP
```

## 4. Critical Findings

### 🔴 F1 — MAJOR: Duplicate Root Structure (43 directories + 38 .md + 7 .py)

Workspace root содержит почти полную копию `astrofin-sentinel-platform/`. Root-версии устарели:
- `AGENTS.md`: 19K vs 24K (platform новее на 7.5K)
- `pyproject.toml`: 1.4K vs 4.7K (platform в 3.3× больше)
- `Makefile`: 9.9K vs 11.7K (platform новее)
- `requirements.txt`: 486B vs 507B

**Impact:** Любые правки в root — мёртвый код. Единственная активная директория: `astrofin-sentinel-platform/`. Это создаёт путаницу и риск случайного редактирования не того файла.

### 🔴 F2 — Empty Placeholder Directories

`AstroFinSentinelV5/`, `AsurDev/`, `astrofin-sentinel-v5/`, `roma-execution-bridge/`, `home-cluster-iac/` — пустые. Это артефакты бывших git submodules или subtree-экспериментов.

**Impact:** Захламление workspace. 5 пустых директорий.

### 🔴 F3 — Version Snapshots (v6/v7/v8)

24 файла в трёх директориях — старые версии constraint engine, policy evaluator, solver и т.д. Уже не используются.

**Impact:** Мёртвый код. 24 файла без активных импортов.

### 🟠 F4 — audit_repo (485 files)

Огромный архив — включает полные копии `deploy/docker/`, старые agent-файлы, docker-compose.

**Impact:** 485 файлов мусора. Включает `docker-compose.yml`, `Dockerfile` и даже `.env.example` — риск утечки конфигурации.

### 🟠 F5 — Branch Proliferation

11 remote branches, из которых активны: `feature/architecture-consolidation`, `master`, `main`. Остальные 8 — stale feature-ветки (calendar-visualizer, council-orchestrator-wireup, hmm-risk-karl-v2) + 4 dependabot-ветки.

### 🟡 F6 — Тестовое окружение не настроено

`venv/bin/python` не имеет `pytest` и `ruff` — невозможно запустить тесты или линтер без доустановки зависимостей.

### 🟡 F7 — Dashboard service не запущен локально

Нет ответа от `localhost:8050` — production dashboard работает через Zo service (`astrofin-dashboard-asurdev.zocomputer.io`), но локальное тестирование недоступно.

### 🟡 F8 — Dual Frontend (Dash + React)

Одновременно существуют `web/` (Dash, legacy) и `web-react/` (React 19 + Vite 8). React-версия имеет собранный `dist/` и активна на production. Dash — legacy без активного использования.

## 5. GitHub Repository Decision Matrix

| Repo | Action |
|---|---|
| `astrofin-sentinel-platform` | ✅ **KEEP** — единственный активный |
| `astrofin-sentinel-v5` | 📦 ARCHIVE (already frozen) |
| `AstroFinSentinelV5` | 📦 ARCHIVE |
| `ATOMFederationOS` | 📦 ARCHIVE |
| `atom-federation-os` | 📦 ARCHIVE |
| `atom-federation-core` | 📦 ARCHIVE |
| `atom-kernel` / `atom-agent` / `atom-operator` / `atom-runtime` / `atom-federation` / `atom-router` | 📦 ARCHIVE (v10, inlined in platform) |
| `astrofin-federation-stack` | 📦 ARCHIVE |
| `roma-execution-bridge` | 📦 ARCHIVE |
| `home-cluster-iac` | 🔄 KEEP (infra) |
| `pop-os-setup` | 🔄 KEEP (separate product) |
| `integrations-gitagent` | 🔄 KEEP |
| `AsurDev` / `AsurDev1.1` | 📦 ARCHIVE |
| `_afs_token_probe_DO_NOT_USE` | 🗑️ DELETE |
| `VIMANA_MAIN_PROJECT_SHANTI` | 📦 ARCHIVE (unrelated) |

## 6. Next Steps → Step 2

Предлагаю перейти к **Шагу 2: Глубокий аудит** по категориям:

1. **Архитектура и структура** — проверить coupling/cohesion, соответствие Clean Architecture
2. **Код и качество** — SOLID, DRY, дубликаты, устаревшие паттерны
3. **Безопасность** — secrets scan, auth audit, error handling
4. **Производительность** — bottlenecks, неэффективные запросы
5. **Зависимости** — outdated packages, security vulnerabilities
6. **Полезные артефакты** — каталогизация лучших кусков кода

После твоего approve — запускаю полный аудит по каждому разделу и формирую развёрнутый `AUDIT_REPORT.md` с конкретными finding'ами, code snippets и рекомендациями.

---

**Промт для продолжения:** «Начинай Шаг 2 — глубокий аудит по всем 6 категориям. Сначала архитектура и код, потом безопасность и производительность.»
