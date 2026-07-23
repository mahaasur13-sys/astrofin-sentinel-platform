# AstroFin Sentinel — Аудит Шаг 1: Инвентаризация (2026-07-23)

> **Аудитор:** Senior Architect & Code Auditor (Zo Computer)
> **Дата:** 2026-07-23 08:15 SAMT (04:15 UTC)
> **Scope:** `/home/workspace` + GitHub `mahaasur13-sys` (27 репозиториев)

---

## 1. Исполнительное резюме

**AstroFin Sentinel** — зрелый монорепо (~294K LOC Python, 1417 .py файлов, 214 тестовых файлов) в состоянии **Production-Beta → GA-ready**. Проект прошёл значительную консолидацию (Phase B1, Sprint 1-8), но страдает от структурного дублирования workspace и дрейфа веток.

**Главный артефакт:** `astrofin-sentinel-platform/` (5.6 GB) — активный код, 25 агентов, KARL/AMRE, RAG-first, FastAPI + React фронтенд.

### Ключевые цифры одним взглядом

| Метрика | Значение |
|---------|----------|
| Основной репозиторий | `mahaasur13-sys/astrofin-sentinel-platform` |
| Активная ветка | `main` (локально), `origin/main` (удалённо) |
| Python файлов | 1417 (в `astrofin-sentinel-platform/`) |
| Тестовых файлов | 214 |
| Агентов | 25 в `agents/_impl/` |
| GitHub-репозиториев всего | 27 |
| Дублирующих репозиториев | 5 (кандидаты на удаление/архивацию) |
| Дублирующих директорий (root↔platform) | 39 |
| Коммитов в `origin/master` | 241 впереди локального `main` |
| Bandit HIGH | 0 (P0 исправлены ✅) |
| Bandit MEDIUM | 24 |
| Тестов: passed | 664 (последний прогон) |
| Тестов: failed | 1 (`test_infer_edges.py` — missing file) |

---

## 2. Карта workspace

### 2.1 Структура верхнего уровня

```
/home/workspace/                        ← git clone astrofin-sentinel-platform (ветка main)
│
├── astrofin-sentinel-platform/ 5.6G    ← 🔵 ОСНОВНОЙ КОД (активная разработка)
│   ├── agents/_impl/         25 агентов (fundamental, quant, sentiment, risk, ...)
│   ├── core/                 44 .py — BaseAgent, belief, cache, circuit_breaker, auth
│   ├── orchestration/        14 .py — sentinel_v5, broker, council_orchestrator
│   ├── meta_rl/              33 .py — Thompson Sampling, HMM, calibration
│   ├── data_room/            11 .py — HTTP gateway (SEC, CoinGecko, Binance resolvers)
│   ├── knowledge/             8 .py — RAG index (FAISS + BM25 + RRF)
│   ├── trading/               9 .py — PaperBroker, BinanceBroker, TWAP execution
│   ├── web/                   6 .py — Dash dashboard (8 панелей)
│   ├── web-react/             React + Redux Toolkit фронтенд
│   ├── api/                   4 .py — FastAPI бэкенд
│   ├── telegram_bot/          6 .py — Telegram-бот
│   ├── tests/                125 файлов — 664+ тестов
│   ├── scripts/              26 .py — архитектурный линтер, валидаторы
│   ├── tools/                17 .py — утилиты
│   ├── deploy/                Docker, k8s, мониторинг
│   ├── docs/                 51 .md — ADR, архитектура, спринты
│   ├── artifacts/best_practices/ — каталог лучших компонентов
│   └── venv/                 544 MB — виртуальное окружение
│
├── kernel/             7.8M   ← ⚠️ ДУБЛИКАТ (из старого master)
├── infrastructure/     1.4M   ← ⚠️ ДУБЛИКАТ
├── deploy/             1.7M   ← ⚠️ ДУБЛИКАТ
├── tests/              571K   ← ⚠️ ДУБЛИКАТ (112 .py, старее чем platform/tests/)
├── scripts/            208K   ← ⚠️ ДУБЛИКАТ (20 .py)
├── models/             1.8M   ← ⚠️ ДУБЛИКАТ
├── docs/               825K   ← ⚠️ ДУБЛИКАТ
├── [ещё 33 дублирующих директории]
│
├── Knowledge/          223K   ← Уникальные root-only артефакты
├── artifacts/           76K   ← best_practices (root-копия)
├── pop-os-setup/        55K   ← Отдельный проект (Pop!_OS setup)
│
├── SOUL.md, AGENTS.md          ← ДУБЛИКАТЫ (есть и в platform/)
├── requirements.txt             ← РАСХОДИТСЯ с platform/requirements.txt
├── pyproject.toml               ← РАСХОДИТСЯ
└── [38 .md файлов]              ← Большинство — дубликаты
```

### 2.2 Ключевые технологии

| Слой | Технологии |
|------|-----------|
| **Язык** | Python 3.12, TypeScript (React) |
| **ML/RL** | numpy, pandas, scikit-learn, FAISS, hmmlearn, sentence-transformers |
| **Астрология** | pyswisseph (Swiss Ephemeris) |
| **БД** | SQLite (primary), PostgreSQL + TimescaleDB + pgvector |
| **API** | FastAPI, Dash (Plotly), uvicorn |
| **Фронтенд** | React 19 + Redux Toolkit + TradingView-style компоненты |
| **Мониторинг** | Prometheus, Grafana, OpenTelemetry, structlog |
| **CI/CD** | GitHub Actions (16 workflow), CodeRabbit, pre-commit hooks |
| **Безопасность** | Bandit, Gitleaks, detect-secrets, SOPS |
| **Инфра** | Docker, docker-compose, k8s (kind) |

### 2.3 Архитектурные слои (Clean Architecture)

```
┌─────────────────────────────────────────────┐
│  Presentation:  web/ (Dash) + api/ (FastAPI) │
├─────────────────────────────────────────────┤
│  Application:   orchestration/ (sentinel_v5) │
├─────────────────────────────────────────────┤
│  Domain:        agents/_impl/ (25 agents)    │
│                 core/ (BaseAgent, belief...)  │
├─────────────────────────────────────────────┤
│  Infrastructure: data_room/ (HTTP gateway)   │
│                  knowledge/ (RAG index)       │
│                  trading/ (execution)         │
│                  meta_rl/ (ML pipeline)       │
└─────────────────────────────────────────────┘
```

Направление зависимостей — строго однонаправленное:
- `data_room/` → `core/` → `agents/` → `orchestration/`  ✅
- 0 обратных импортов (core → agents) ✅

---

## 3. GitHub-репозитории: полная карта

### 3.1 Основной репозиторий

| Параметр | Значение |
|----------|----------|
| **Имя** | `mahaasur13-sys/astrofin-sentinel-platform` |
| **Default branch** | `master` |
| **Активная ветка** | `main` |
| **Локально** | `main` (2 коммита впереди origin/master) |
| **origin/master** | 241 коммит впереди локального `main` (merge `main` → `master`) |

### 3.2 Смежные репозитории — полный список

#### 🔵 АКТИВНЫЕ (федеративный стек)

| Репо | Назначение | Последний push |
|------|-----------|----------------|
| `astrofin-federation-stack` | Federation: ATOM kernel + ROMA bridge + AsurDev | 2026-07-02 |
| `atom-federation-os` | ATOM Federation OS core | 2026-06-24 |
| `roma-execution-bridge` | ROMA execution bridge | 2026-06-18 |
| `integrations-gitagent` | GitAgent MCP integration | 2026-07-14 |

#### 🟡 ЗАМОРОЖЕННЫЕ (ATOM ecosystem v10.x, стабильные)

| Репо | Назначение | Последний push |
|------|-----------|----------------|
| `atom-kernel` | Deterministic execution kernel | 2026-04-25 |
| `atom-agent` | Deterministic agent executor | 2026-04-25 |
| `atom-operator` | Kubernetes Operator (CRDs) | 2026-04-25 |
| `atom-federation` | Federation messaging (BFT, consensus) | 2026-04-25 |
| `atom-federation-core` | Production K8s control plane | 2026-04-25 |
| `atom-router` | REDEREF-style adaptive router | 2026-05-18 |
| `atom-runtime` | Runtime | 2026-04-25 |

#### 🔴 ДУБЛИКАТЫ (кандидаты на удаление/архивацию)

| Репо | Проблема | Последний push |
|------|----------|----------------|
| `AstroFinSentinelV5` | **Полный дубликат** основного репо | 2026-06-26 |
| `astrofin-sentinel-v5` | **Дубликат** (LangGraph, Thompson Sampling) | 2026-06-26 |
| `ATOMFederationOS` | **Дубликат** `atom-federation-os` | 2026-06-26 |
| `asurdev-workspace-backup-20260326` | Устаревший бэкап | 2026-03-29 |
| `_afs_token_probe_DO_NOT_USE` | Токен-проб (должен быть удалён) | 2026-07-02 |

#### ⚪ НЕАКТИВНЫЕ / ЭКСПЕРИМЕНТАЛЬНЫЕ

| Репо | Назначение |
|------|-----------|
| `AsurDev` | Infra/IaC |
| `AsurDev1.1` | Infra/IaC v1.1 |
| `home-cluster-iac` | Home cluster IaC |
| `pop-os-setup` | Pop!_OS workstation setup |
| `VIMANA_MAIN_PROJECT_SHANTI` | DDEV-проект |
| `ollama-transfer-template*` (×2) | Шаблоны |
| `-my-obsidian-vault-` | Obsidian vault |
| `desktop-tutorial` | GitHub Desktop tutorial |

---

## 4. Дубликаты и расхождения

### 4.1 КРИТИЧЕСКИЕ: Дублирование workspace

**39 директорий существуют одновременно в корне `/home/workspace/` и в `astrofin-sentinel-platform/`.**

Корневые копии — артефакты из старой ветки `master` (241 коммит впереди локального `main`, но это merge-коммиты). Актуальный код — в `astrofin-sentinel-platform/`.

**Самые крупные дубликаты:**

| Директория | Root размер | Platform размер | Статус |
|-----------|-------------|-----------------|--------|
| `kernel/` | 7.8M (685 .py) | 7.8M (685 .py) | Идентичны |
| `infrastructure/` | 1.4M (178 .py) | 1.4M (178 .py) | Идентичны |
| `deploy/` | 1.7M | 1.7M | Идентичны |
| `tests/` | 571K (112 .py) | ~600K (125 .py) | Platform новее (+13 файлов) |
| `scripts/` | 208K (20 .py) | ~250K (26 .py) | Platform новее |
| `docs/` | 825K (49 .md) | ~850K (51 .md) | Platform новее |

### 4.2 Расхождение `requirements.txt`

```
Root:      md5 87fa5d1a... (старая версия, без structlog, pydantic-settings)
Platform:  md5 95c65b61... (консолидированная версия от 2026-07-22)
```

Platform-версия содержит дополнительные зависимости: `structlog`, `pydantic-settings`, `python-dotenv`, `python-telegram-bot[job-queue]`.

### 4.3 Ветки с дрейфом

```
Локальный main:        82a602a (dashboard, SessionTable, ContextDrawer)
origin/main:           82a602a (синхронизирован)
origin/master:         6e520b1 (merge main → master)
```

`origin/master` содержит merge `main` и 240 дополнительных коммитов (consolidation, CI fixes, ruff, архитектурный линтер). Локальный `main` отстаёт на 241 коммит от `origin/master`.

### 4.4 Дублирующие GitHub-репозитории

| Репо | Тип дублирования | Рекомендация |
|------|-----------------|--------------|
| `AstroFinSentinelV5` | Полная копия основного | **Удалить** |
| `astrofin-sentinel-v5` | Копия с другим описанием | **Удалить** |
| `ATOMFederationOS` | Копия `atom-federation-os` | **Удалить** |
| `asurdev-workspace-backup-20260326` | Устаревший бэкап | **Удалить** |
| `_afs_token_probe_DO_NOT_USE` | Токен-проб | **Удалить** |

---

## 5. Аудит безопасности (Bandit)

| Severity | Count | Примечание |
|----------|-------|-----------|
| **HIGH** | **0** ✅ | P0 исправлены (SQL-инъекция, eval(), MD5/SHA1 — не найдены) |
| **MEDIUM** | 24 | subprocess shell=True, 0.0.0.0 bind |
| **LOW** | 521 | assert в production, try/except: pass, стандартный random |

17 файлов пропущены bandit из-за syntax error (в основном в `kernel/atom-federation/`).

---

## 6. Аудит тестов

| Метрика | Значение |
|---------|----------|
| Тестовых файлов | 125 (в platform/tests/) |
| Всего тестов | 664 passed (предыдущий полный прогон) |
| Текущий прогон | 1 FAIL: `test_infer_edges.py` — `FileNotFoundError: graphify-out/infer_edges.py` |

**Проблемный тест:** `tests/architecture/test_infer_edges.py::test_tier_T1_for_high_confidence_valid` — ожидает файл `graphify-out/infer_edges.py`, который отсутствует (возможно, graphify не был запущен).

**Coverage gaps:**
- `trading/` — 0% (0 прямых тестов)
- `orchestration/` — 0% (0 прямых тестов)
- `core/` — ~0% прямых (тестируется косвенно)

---

## 7. Агенты: полный список

25 агентов в `agents/_impl/`:

| # | Агент | Тип | Сигнал |
|---|-------|-----|--------|
| 1 | `fundamental_agent.py` | Fundamental | BUY/SELL/HOLD |
| 2 | `quant_agent.py` | Quant | STRONG BUY/SELL/HOLD |
| 3 | `sentiment_agent.py` | Sentiment | BUY/SELL/HOLD |
| 4 | `technical_agent.py` | Technical | BUY/SELL/HOLD |
| 5 | `macro_agent.py` | Macro | BUY/SELL/HOLD |
| 6 | `risk_agent.py` | Risk | Risk assessment |
| 7 | `ml_predictor_agent.py` | ML | Prediction |
| 8 | `hmm_regime_agent.py` | HMM | Regime detection |
| 9 | `options_flow_agent.py` | Options | Flow analysis |
| 10 | `insider_agent.py` | Insider | Insider tracking |
| 11 | `bull_researcher.py` | Research | Bull thesis |
| 12 | `bear_researcher.py` | Research | Bear thesis |
| 13 | `compromise_agent.py` | Synthesis | Compromise |
| 14 | `synthesis_agent.py` | Synthesis | Meta-synthesis |
| 15 | `cycle_agent.py` | Astro | Cycles |
| 16 | `gann_agent.py` | Astro | Gann angles |
| 17 | `elliot_agent.py` | Astro | Elliot waves |
| 18 | `bradley_agent.py` | Astro | Bradley siderograph |
| 19 | `time_window_agent.py` | Astro | Time windows |
| 20 | `electoral_agent.py` | Astro | Electoral astrology |
| 21 | `ephemeris_decorator.py` | Astro | Ephemeris decorator |
| 22 | `market_analyst.py` | Analysis | Market analysis |
| 23 | `amre/` | Meta | AMRE self-improvement |
| 24 | `astro_council/` | Council | Astro council |
| 25 | `types.py` | Types | Agent types |

---

## 8. Сводная таблица: Состояние проекта

| Категория | Оценка | Ключевой факт |
|-----------|--------|---------------|
| Архитектура | ⭐⭐⭐⭐☆ (4/5) | Clean Architecture, однонаправленные зависимости |
| Структура workspace | ⭐⭐☆☆☆ (2/5) | 39 дублирующих директорий, дрейф main↔master |
| Код и качество | ⭐⭐⭐☆☆ (3/5) | 438 print(), 2213 except:pass, 81 bare logging |
| Безопасность | ⭐⭐⭐⭐☆ (4/5) | 0 HIGH bandit, JWT auth, SOPS, gitleaks |
| Тестирование | ⭐⭐⭐⭐☆ (4/5) | 664 passed, но trading/orchestration без тестов |
| Зависимости | ⭐⭐⭐☆☆ (3/5) | 7 requirements файлов, 16 CI workflow |
| GitHub hygiene | ⭐⭐☆☆☆ (2/5) | 5 дублирующих репозиториев, stale branches |
| **Общая** | **⭐⭐⭐½☆ (3.3/5)** | **Production-Beta: готов к GA после чистки** |

---

## 9. Приоритизированный план (Что делать дальше)

### P0 — СДЕЛАТЬ ПРЯМО СЕЙЧАС (Шаг 3)

| # | Действие | Оценка |
|---|----------|--------|
| P0-01 | Синхронизировать `main` с `origin/master` (pull 241 коммит) | 5 мин |
| P0-02 | Удалить дублирующие GitHub-репозитории (5 шт.) | 10 мин |
| P0-03 | Починить `test_infer_edges.py` (missing graphify-out) | 15 мин |

### P1 — КРИТИЧЕСКИЙ ТЕХДОЛГ

| # | Действие | Оценка |
|---|----------|--------|
| P1-01 | Удалить 39 дублирующих директорий из корня workspace | 30 мин |
| P1-02 | Консолидировать 7 requirements → 3 файла | 30 мин |
| P1-03 | `print()` → `structlog` в ключевых файлах | 3 ч |

### P2 — СТРУКТУРНЫЕ УЛУЧШЕНИЯ

| # | Действие | Оценка |
|---|----------|--------|
| P2-01 | Разделить God-файлы (>500 строк) | 6 ч |
| P2-02 | Написать тесты для `trading/` и `orchestration/` | 4 ч |
| P2-03 | Объединить 16 CI workflow → ~8 | 30 мин |

### P3 — КАЧЕСТВО ЖИЗНИ

| # | Действие |
|---|----------|
| P3-01 | 81 `logging.getLogger` → `structlog` |
| P3-02 | Connection pooling в `data_room/resolvers/` |
| P3-03 | Удалить stale feature branches |

---

## 10. Следующие действия

**Шаг 1 завершён.** Полная инвентаризация проведена. Основные находки задокументированы.

**Команда для продолжения:**
> «Продолжай Шаг 3 — Консолидация и Улучшения. Начни с P0: синхронизация main↔master, удаление дублирующих GitHub-репозиториев, исправление падающего теста. Затем перейди к P1 (чистка дубликатов workspace, консолидация requirements).»
