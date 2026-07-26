# AstroFin Sentinel Platform — Comprehensive Audit Report

**Date:** 2026-07-26
**Auditor:** Senior Architect & Code Auditor (Zo Agent)
**Scope:** Full workspace + 27 GitHub repositories
**Project:** astrofin-sentinel-platform (master @ d1b8e15e)

---

## Executive Summary

AstroFin Sentinel — зрелый production-beta проект с 9 CI-воркфлоу, 122 тестовыми файлами, 20 000+ строк Python, 14 активными агентами и чистым архитектурным линтером (0 hard violations). Проект прошёл через 6 спринтов (A–F) и недавний аудит (July 25, 10 findings closed, 13 PRs merged).

**Ключевой риск:** В workspace обнаружено **два параллельных дерева исходников** — root `/home/workspace/` (полная реализация, 68 файлов в core/, 26 агентов) и вложенный `astrofin-sentinel-platform/` (stale-клон от July 25, содержит только `_archived/`, `amre/`, `astro_council/` — 4 файла в agents/_impl/ против 26 в root). Это создаёт дрейф и риск потери кода.

**Оценка:** 8.2/10 — проект в хорошем состоянии, фокус на устранении оставшихся проблем.

---

## 1. Инвентаризация (Step 1)

### 1.1 GitHub Repositories (27 total)

| # | Repository | Updated | Active? | Relationship |
|---|-----------|---------|---------|-------------|
| 1 | `astrofin-sentinel-platform` | 2026-07-26 | ✅ **MASTER** | Основной проект |
| 2 | `AstroFinSentinelV5` | 2026-06-19 | ❌ Stale | Предыдущая версия (v5 legacy) |
| 3 | `astrofin-sentinel-v5` | 2026-06-17 | ❌ Stale | Initial import (1 commit) |
| 4 | `astrofin-federation-stack` | 2026-07-02 | 🟡 Partial | ROMA bridge + federation |
| 5 | `AsurDev` | 2026-07-14 | 🟡 Partial | ML engine + infra components |
| 6 | `atom-federation-os` | 2026-06-24 | ❌ Stale | ATOM federation OS (archived) |
| 7 | `roma-execution-bridge` | 2026-06-18 | ❌ Stale | ROMA k8s bridge (archived) |
| 8 | `home-cluster-iac` | 2026-06-18 | ❌ Stale | Home cluster IAC (archived) |
| 9 | `atom-federation-core` | 2026-04-25 | ❌ Stale | ATOM core (archived) |
| 10 | `atom-router` | 2026-05-18 | ❌ Stale | ATOM router |
| 11 | `atom-runtime` | 2026-04-25 | ❌ Stale | ATOM runtime |
| 12 | `atom-agent` | 2026-04-25 | ❌ Stale | ATOM agent |
| 13 | `atom-operator` | 2026-04-25 | ❌ Stale | ATOM k8s operator |
| 14 | `atom-kernel` | 2026-04-25 | ❌ Stale | ATOM kernel |
| 15 | `ATOMFederationOS` | 2026-06-26 | ❌ Stale | Mirror/fork |
| 16 | `atom-federation` | 2026-04-25 | ❌ Stale | Federation |
| 17 | `integrations-gitagent` | 2026-07-14 | 🟡 Partial | GitAgent integration |
| 18 | `pop-os-setup` | 2026-05-10 | ❌ Stale | Pop!_OS setup |
| 19 | `asurdev-workspace-backup-2026-03-26` | 2026-07-23 | 🔴 Backup | Backup (DO NOT MERGE) |
| 20-27 | Others | Various | ❌ | Templates, obsidian, etc. |

**Вывод:** Из 27 репозиториев только **1 активный** (`astrofin-sentinel-platform`). 3 частично релевантны (AsurDev, federation-stack, gitagent). Остальные 16+ — архивные/старые версии. Нужна чистка или явная маркировка.

### 1.2 Workspace Structure (Key Dirs)

```
/home/workspace/                          ← ROOT (АКТИВНЫЙ КОД)
├── agents/_impl/         26 files        ← Все 14+ агентов ✅
├── core/                 68 files        ← Полный core: ephemeris, aspects, etc.
├── orchestration/        14 files        ← Sentinel v5 orchestrator
├── meta_rl/              45 files        ← Meta-RL + AMRE
├── web/                  24 files        ← Dash dashboard (callbacks split!)
├── web-react/             -              ← React frontend
├── api/                  5 files         ← FastAPI backend
├── telegram_bot/         3 files         ← Telegram alerts
├── data_room/            11 files        ← Network gateway (resolvers)
├── knowledge/            17 files        ← RAG index + retrieval
├── backtest/             11 files        ← Backtesting engine
├── trading/              20 files        ← Execution engine
├── tests/                122 files       ← Test suite
├── deploy/               145 files       ← Docker, k8s, monitoring, WAL-G
├── docs/                 many            ← Architecture, ADR, runbooks, sprints
├── scripts/              22 files        ← CI helpers, validators, migration
├── .github/workflows/    9 files         ← CI/CD pipelines
│
├── v6/                   archived        ← AMRE constraint engine (LEGACY)
├── v7/                   archived        ← Meta-RL reweight/governor (LEGACY)
├── v8/                   archived        ← Safety kernel/admission (LEGACY)
│
├── infrastructure/asurdev/               ← Home cluster IAC (Ansible, k8s)
├── kernel/atom-federation/               ← ATOM federation docs (LEGACY)
├── bridge/roma/                          ← ROMA execution bridge (LEGACY)
├── atom-core/                            ← ATOM core packages (LEGACY)
├── acos-contracts/                       ← Smart contracts
│
├── astrofin-sentinel-platform/  5.5GB    ← STALE CLONE (⚠️ DANGER)
│   └── agents/_impl/         4 files     ← ТОЛЬКО amre + astro_council
│   └── core/                 3 files     ← Минимальный core
│   └── venv/                 4+ GB       ← Виртуальное окружение!
│
└── .zo_scratch/submodule-archive-2026-07-12/  ← Archived submodules
```

### 1.3 GitHub Branches (astrofin-sentinel-platform)

**Активные:**
- `master` — основной бранч (d1b8e15e, July 26)
- `main` — синхронизирован с master

**Мёртвые ветки (23 ветки, все кроме master/main уже merged):**
22 feature/fix/chore ветки, последний PR merged July 25. Все могут быть удалены.

### 1.4 Duplicate Detection

| Дубликат | Описание | Размер |
|----------|---------|--------|
| **root ↔ nested `astrofin-sentinel-platform/`** | Полный дубликат проекта, nested — stale | 5.5 GB |
| `agents/_impl/` root (26 files) vs nested (4 files) | Nested содержит только amre + astro_council | Критично |
| `core/` root (68 files) vs nested (3 files) | Nested core почти пуст | Критично |
| `AstroFinSentinelV5` GitHub repo vs master | Старая версия v5 (June 19) | Archive |
| `astrofin-sentinel-v5` GitHub repo | Initial import (June 17) | Delete? |
| `ATOMFederationOS` GitHub repo vs `atom-federation-os` | Похоже на mirror/fork | Archive |
| v6/v7/v8 vs `meta_rl/amre/` | Архивные версии AMRE/Meta-RL/Safety | Archive |

---

## 2. Глубокий Аудит (Step 2)

### 2.1 Архитектура и Структура — Оценка: 8.5/10

**Сильные стороны:**
- Чёткая Clean Architecture: `agents/` → `core/` → `orchestration/` → `web/`
- RAG-First паттерн с `data_room/` как единым сетевым шлюзом (R-01)
- Multi-Agent Council с явными весами (Fundamental 20%, Quant 20%, Macro 15%, и т.д.)
- Аудит-трейл (ATOM-KARL-009) и KPI Control Loop (ATOM-KARL-010)
- Pre-commit hooks + архитектурный линтер + CodeRabbit review
- Хорошее разделение: `agents/_impl/` (активные) vs `agents/_archived/` (в AGENTS.MD)
- `web/callbacks/` успешно разделены из god-object `callbacks.py` (PR #276)

**Проблемы:**
- ⚠️ **Два параллельных дерева исходников** — root и nested `astrofin-sentinel-platform/`. Nested содержит stale код (4 agent-файла против 26 в root). Это сбивает с толку и может привести к потере правок.
- 📦 **7 root-level .py файлов** (`muhurtha.py`, `langgraph_schema.py`, `data_provider.py`, `health_endpoints.py`, `logging_setup.py`, `test_aspects.py`, `FINAL_INTEGRATION_TEST.py`) — загрязняют корень проекта, должны быть в соответствующих модулях.
- 📁 **v6, v7, v8** (3 архивные версии AMRE/Meta-RL/Safety) занимают место, но не являются частью активного кода. `meta_rl/amre/` уже содержит актуальную реализацию.
- 📁 **33 root-only директории** (kernel, bridge, infrastructure, atom-core, acos-contracts, etc.) не являются частью основного Python-пакета, но живут рядом. Часть — легаси, часть — независимые подпроекты.

### 2.2 Код и Качество — Оценка: 7.5/10

| Метрика | Значение | Статус |
|--------|---------|--------|
| `.py` файлов (активный код) | ~20 000 строк | ✅ |
| Ruff lint | All checks passed! | ✅ |
| Pre-commit hooks | validate_agent, arch_linter, bandit, etc. | ✅ |
| `print()` в production-коде | 294 файла | ⚠️ Нужен structlog |
| `import requests` вне `data_room/` | 12 файлов (вне архивов) | ⚠️ Нарушение R-01 |
| `except:` (bare) | 3 файла | ⚠️ |
| TODO/FIXME/HACK | 8 маркеров | 🟡 Приемлемо |
| `__init__.py` в корне | Отсутствует (не пакет?) | 🟡 |

**Detected Anti-Patterns:**
- `backtest/engine.py` — прямой `import requests` (R-01 violation)
- `bridge/roma/` — 3 файла с `import requests`
- `infrastructure/asurdev/` — 2 файла с `import requests`
- `kernel/atom-federation/` — 1 файл с `import requests`
- 294 файла используют `print()` вместо `structlog`

### 2.3 Безопасность и Надёжность — Оценка: 8.5/10

**Сильные стороны:**
- Bandit — 0 HIGH findings (после PR #268-280)
- `@require_auth` на всех production API routes (P0/SEC-01)
- Secrets — только в `.env` / GitHub Secrets (R-10)
- Pre-commit: detect-secrets, bandit, gitleaks
- `.sops.yaml` для шифрования секретов
- Bearer token auth pattern в API routes

**Проблемы:**
- 3 bare `except:` блока (потенциальная потеря ошибок)
- `certifi` package: 2024.8.30 → 2026.7.22 (2 года отставания — критично для TLS)
- ~300 outdated пакетов (см. секцию 2.5)

### 2.4 Тестирование — Оценка: 7.0/10

| Метрика | Значение |
|--------|---------|
| Тестовых файлов | 122 |
| Последний CI (master) | ✅ Success |
| Предыдущие 2 CI | ❌ Failure (flaky LLM router tests) |
| CI воркфлоу | 9 (сокращено с 17, PR #280) |

**Проблемы:**
- **Flaky CI:** 2 из 5 последних запусков упали на тестах LLM fallback. Последний коммит (d1b8e15e) чинит это, но стабильность под вопросом.
- **Pytest не показывает количество тестов** — вывод обрезан, невозможно оценить coverage визуально.
- 122 test-файла — много, но без видимого coverage report сложно судить о gaps.

### 2.5 Зависимости и Инфраструктура — Оценка: 7.0/10

**Критичные outdated пакеты:**
| Package | Current | Latest | Lag |
|---------|---------|--------|-----|
| `certifi` | 2024.8.30 | 2026.7.22 | **23 months** 🔴 |
| `cffi` | 2.0.0 | 2.1.0 | minor |
| `boto3` | 1.40.61 | 1.43.56 | 3 minor |
| `anthropic` | 0.117.0 | 0.120.0 | 3 versions |
| `bandit` | 1.8.0 | 1.9.4 | 1 minor |
| `black` | 26.3.1 | 26.5.1 | 2 versions |
| `ccxt` | 4.5.45 | 4.5.68 | 23 versions |
| `ansible` | 13.5.0 | 14.2.0 | Major |

**Инфраструктура:**
- ✅ Docker Compose (3 файла: dev, pgvector, production)
- ✅ TimescaleDB + pgvector + WAL-G
- ✅ Grafana + Loki + Prometheus
- ✅ CI/CD: 9 GitHub Actions workflows
- ✅ Pre-commit hooks
- ⚠️ `.venv/` внутри nested `astrofin-sentinel-platform/` (~4 GB) — должно быть в корне или удалено
- ⚠️ Dependabot активен (2 открытых PR), но большинство пакетов outdated

### 2.6 Производительность — Оценка: 8.0/10

- ✅ Volatility-adjusted position sizing (R-07)
- ✅ RAG с FAISS + BM25 + RRF (гибридный retrieval)
- ✅ LLM Router: простые → Ollama (local), сложные → OpenRouter (cloud) — снижает latency и cost
- ✅ PostgreSQL/TimescaleDB для production, SQLite fallback
- ✅ Redis для кэширования
- ⚠️ `venv/` внутри nested (5.5 GB всего nested) — диск space waste
- ⚠️ 294 `print()` — лишний I/O в production

---

## 3. Полезные Артефакты (Best Practices)

Ключевые паттерны, достойные сохранения как best practices:

### 3.1 Уже в `artifacts/best_practices/`
- ✅ `data_room/` — паттерн сетевого шлюза
- ✅ `@require_auth` middleware
- ✅ Agent Contract (`core/agent_contract.py`)
- ✅ Architecture Linter (`scripts/architecture_linter.py`)

### 3.2 Стоит добавить
- `web/callbacks/` — пример splitting god-object (PR #276) — образцовый рефакторинг
- `agents/_impl/types.py` — `AgentResponse`, `TradingSignal`, `SignalDirection` — чистый интерфейс
- `core/llm_router.py` — routing pattern (local vs cloud LLM)
- `meta_rl/amre/` — AMRE decision audit trail (ATOM-KARL-009/010)

---

## 4. План Консолидации (Step 3) — Приоритеты

### 🔴 P0 — Critical (блокирует GA)

| # | Задача | Усилия | Риск |
|---|--------|--------|------|
| P0-1 | **Удалить `astrofin-sentinel-platform/` (nested stale clone)** | 30 мин | Средний — проверить, что ничего не потеряно |
| P0-2 | Обновить `certifi` (2024→2026) — TLS security | 5 мин | Низкий |

### 🟡 P1 — High (перед v1.0.0 GA)

| # | Задача | Усилия | Риск |
|---|--------|--------|------|
| P1-1 | Удалить 22 merged feature-ветки на GitHub | 5 мин | Низкий |
| P1-2 | Переместить 7 root-level .py в правильные модули | 1 час | Низкий |
| P1-3 | Заменить `import requests` → `data_room.blueprint` в backtest/engine.py | 30 мин | Низкий |
| P1-4 | Удалить `bridge/roma/` (архивирован в federation-stack) | 15 мин | Низкий |
| P1-5 | Стабилизировать flaky LLM router CI тесты | 3 часа | Средний |

### 🟢 P2 — Medium (Sprint H)

| # | Задача | Усилия | Риск |
|---|--------|--------|------|
| P2-1 | Мигрировать 12 files c `print()` → `structlog` | 4 часа | Низкий |
| P2-2 | Обновить ~300 outdated пакетов (batch update) | 2 часа | Средний |
| P2-3 | Пометить v6/v7/v8 как `_archived/` или `research/` | 30 мин | Низкий |
| P2-4 | Архивировать/удалить stale GitHub репозитории (16+) | 1 час | Низкий |
| P2-5 | Добавить coverage report в CI (pytest-cov) | 1 час | Низкий |
| P2-6 | Fix 3 bare `except:` блоков | 30 мин | Низкий |

### 🔵 P3 — Low (Post-GA)

| # | Задача |
|---|--------|
| P3-1 | Решить: монорепо vs выделить `infrastructure/`, `kernel/`, `bridge/` в отдельные репо |
| P3-2 | Создать `CONTRIBUTING.md` для внешних контрибьюторов |
| P3-3 | Автоматизировать cleanup stale branches через GitHub Actions |

---

## 5. Статус соответствия Правилам (R-01…R-12)

| Rule | Статус | Комментарий |
|------|--------|------------|
| R-01 | 🟡 88% | 12 файлов вне data_room с `import requests` (в основном легаси) |
| R-02 | ✅ | Сетевой I/O изолирован |
| R-03 | ✅ | Архитектурный линтер — 0 hard violations |
| R-04 | ✅ | Все агенты реализуют `AgentResponse` |
| R-05 | ✅ | `risk_pct` динамический |
| R-06 | ✅ | Session history в SQLite/PostgreSQL |
| R-07 | ✅ | KARL синтез — единая точка арбитража |
| R-08 | ✅ | Audit trail (AMRE) |
| R-09 | ✅ | Pre-commit hooks активны |
| R-10 | ✅ | Secrets в `.env` / GitHub Secrets |
| R-11 | 🟡 | Coverage не проверяется в CI |
| R-12 | ✅ | Submodules inlined (July 12) |

**Общий compliance: 11/12 = 92%**

---

## 6. Рекомендации и Следующие Шаги

### Немедленно (сегодня):
1. ✅ Подтвердить — удаляем `astrofin-sentinel-platform/` (5.5 GB stale clone)?
2. Обновить `certifi`

### Эта неделя:
3. Очистить GitHub: удалить merged branches + архивировать 16 stale репозиториев
4. Переместить root-level .py files
5. Fix `backtest/engine.py` → data_room
6. Стабилизировать CI

### Sprint H:
7. Print → structlog миграция
8. Batch update зависимостей
9. Добавить pytest-cov в CI

---

## Appendix A: GitHub Repository Map

```
mahaasur13-sys/
├── astrofin-sentinel-platform     ⭐ MASTER (active, July 26)
├── AstroFinSentinelV5             📦 v5 legacy (June 19)
├── astrofin-sentinel-v5           📦 Initial import (June 17)
├── astrofin-federation-stack      📦 Federation + ROMA bridge
├── AsurDev                        📦 ML engine + infra
├── AsurDev1.1                     📦 Old version
├── atom-federation-os             📦 Archive
├── roma-execution-bridge          📦 Archive
├── atom-federation-core           📦 Archive
├── atom-federation                📦 Archive
├── ATOMFederationOS               📦 Mirror
├── atom-router/runtime/agent/
│   operator/kernel                📦 Archive
├── home-cluster-iac               📦 Archive
├── integrations-gitagent          🟡 Partial
├── pop-os-setup                   📦 Archive
├── asurdev-workspace-backup-*     🔴 Backup (DO NOT TOUCH)
├── VIMANA_MAIN_PROJECT_SHANTI     📦 Archive
└── ...other templates/obsidian    📦 Misc
```

## Appendix B: Directory Classification

| Директория | Тип | Действие |
|-----------|-----|---------|
| `agents/`, `core/`, `orchestration/` | **Production core** | Оставить |
| `meta_rl/`, `web/`, `api/` | **Production** | Оставить |
| `data_room/`, `knowledge/` | **Production** | Оставить |
| `backtest/`, `trading/` | **Production** | Оставить |
| `deploy/`, `scripts/`, `.github/` | **Infrastructure** | Оставить |
| `tests/`, `docs/` | **QA/Docs** | Оставить |
| `astrofin-sentinel-platform/` | **STALE CLONE** | 🗑️ Удалить |
| `v6/`, `v7/`, `v8/` | **Archived** | → `_archived/` |
| `bridge/`, `kernel/`, `atom-core/` | **Archived** | → `_archived/` или отдельный репо |
| `infrastructure/asurdev/` | **IAC (отдельный проект)** | → свой репо |
| `.zo_scratch/submodule-archive-*` | **Archive** | 🗑️ Удалить |
