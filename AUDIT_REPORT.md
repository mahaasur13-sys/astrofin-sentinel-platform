# AstroFin Sentinel V5 — Архитектурный Аудит (2026-07-22)

> **Аудитор:** Senior Architect & Code Auditor (Zo Computer)
> **Объём:** ~294 000 строк Python, 392 коммита, 15 веток, 27 GitHub-репозиториев
> **Этап:** Step 1 — Инвентаризация

---

## 1. Исполнительное резюме (Executive Summary)

**AstroFin Sentinel V5** — это зрелый, хорошо структурированный монорепо (~294K LOC), прошедший значительную архитектурную консолидацию (Phase B1 / 4.x / Step 4.8). Проект находится в состоянии **Production-Beta**, с 18 активными агентами, RAG-first архитектурой, KARL/AMRE self-improvement loop и PostgreSQL+pgvector бэкендом.

**Ключевые цифры:**
- 1 основной репозиторий + 26 смежных (из них ~14 — федеративные/ATOM-подсистемы)
- 125 тестовых файлов, ~358 коллекционируемых тестов, последний run: 93 passed / 15 skipped / 13 failed (2026-07-22)
- 1744 `.py` файлов в основном поддереве
- 3 CI ветки с расхождением (main — 67 коммитов впереди origin/master)
- 0 hard violations архитектурного линтера
- 61 leak finding (gitleaks) — все в venv/ (vendor-код)
- 3 High / 8 Medium / 130 Low bandit issues

**Главный риск:** дублирование workspace (корень репо ≈ копия `astrofin-sentinel-platform/`), дрейф между ветками `main`/`master`, 314 файлов dead-code в `audit_repo/`.

---

## 2. Инвентаризация репозиториев

### 2.1 Основной репозиторий

| Параметр | Значение |
|----------|----------|
| **Имя** | `mahaasur13-sys/astrofin-sentinel-platform` |
| **Default branch** | `master` |
| **Активная ветка** | `main` (67 коммитов впереди `origin/master`) |
| **Локальные ветки** | `main`, `feature/architecture-consolidation`, `feature/step-4.8-rag-linter-migration` |
| **Remote branches** | `master`, `main`, `feat/*`, `feature/*`, `dependabot/*` |
| **Размер** | ~294K LOC Python (без venv) |
| **Последний коммит (main)** | `6052d66` — SEC EDGAR resolver, Telegram bot, 8-panel dashboard, auth refactor |
| **Последний коммит (master)** | `6a3d777` — CI bump + consolidation fixes |

### 2.2 Смежные репозитории (всего 27 в GitHub-аккаунте `mahaasur13-sys`)

**Активные (федеративный стек):**

| Репо | Назначение | Статус |
|------|-----------|--------|
| `astrofin-federation-stack` | Federation: ATOM kernel + ROMA bridge + AsurDev infra | Public, последний push 2026-07-02 |
| `atom-federation-os` | ATOM Federation OS core | Private, последний push 2026-06-24 |
| `atom-federation-core` | Production K8s control plane | Private, 2026-04-25 |
| `atom-kernel` | Deterministic execution kernel | Public, 2026-04-25 |
| `atom-agent` | Deterministic agent executor | Public, 2026-04-25 |
| `atom-operator` | Kubernetes Operator (CRDs) | Public, 2026-04-25 |
| `atom-federation` | Federation messaging (BFT, consensus) | Public, 2026-04-25 |
| `atom-router` | REDEREF-style adaptive router | Private, 2026-05-18 |
| `roma-execution-bridge` | ROMA execution bridge | Private, 2026-06-18 |

**Архивные/дублирующие:**

| Репо | Проблема |
|------|----------|
| `AstroFinSentinelV5` | **Дубликат** основного репо (последний push: 2026-06-26) |
| `astrofin-sentinel-v5` | **Дубликат** основного репо (описание: "LangGraph, Thompson Sampling...") |
| `asurdev-workspace-backup-20260326` | Бэкап workspace от 2026-03-26 |
| `ATOMFederationOS` | **Дубликат** `atom-federation-os` (последний push: 2026-06-26) |
| `AsurDev` / `AsurDev1.1` | Infra/iac репо, статус неясен |
| `integrations-gitagent` | GitAgent MCP integration |

**Неактивные/экспериментальные:**
- `atom-runtime` (2026-04-25)
- `home-cluster-iac` (2026-06-18)
- `VIMANA_MAIN_PROJECT_SHANTI` (DDEV-проект, 2026-03-10)
- `ollama-transfer-template` / `ollama-transfer-templateRobot`
- `-my-obsidian-vault-` (2025-09-16)
- `_afs_token_probe_DO_NOT_USE` (токен-проб, 2026-07-02)

### 2.3 Inlined Submodules (Phase B1)

Согласно AGENTS.md, 6 подмодулей были inline-интегрированы в мастер:
- `AsurDev` → `infrastructure/asurdev/`
- `atom-federation-core` → `atom-core/`
- `atom-federation-os` → `kernel/atom-federation/`
- `ATOM-Consensus` → (внутри kernel)
- `Hermes Agent` → (не найден в workspace)
- `home-cluster-iac` → `k8s/` (частично)

**Но:** в workspace есть и отдельные директории (`kernel/atom-federation/`, `infrastructure/asurdev/`) и параллельный `astrofin-sentinel-platform/` с полной копией. Это создаёт путаницу.

---

## 3. Карта проекта

### 3.1 Структура верхнего уровня

```
/home/workspace/  (root = git repo astrofin-sentinel-platform)
├── astrofin-sentinel-platform/  ← ОСНОВНОЙ КОД (1744 .py, git clone)
│   ├── agents/           (58 .py)   — 18+ агентов + AMRE/KARL
│   ├── core/             (58 .py)   — ephemeris, history, volatility, llm_router
│   ├── meta_rl/          (43 .py)   — Meta-RL, HMM, Thompson Sampling, calibration
│   ├── orchestration/    (12 .py)   — sentinel_v5, council_orchestrator
│   ├── data_room/        (11 .py)   — сетевой шлюз (resolvers: SEC, CoinGecko, Binance, ...)
│   ├── knowledge/        (17 .py)   — RAG index (FAISS+BM25+RRF)
│   ├── trading/          (18 .py)   — execution (TWAP), order management
│   ├── web/              (21 .py)   — Dash dashboard (8 панелей)
│   ├── web-react/        (React)    — React+Redux фронтенд
│   ├── telegram_bot/     (6 .py)    — Telegram-бот (/start, /status, /analyze)
│   ├── api/              (4 .py)    — FastAPI бэкенд
│   ├── tests/            (125 .py)  — 358 тестов
│   ├── scripts/          (31 .py)   — архитектурный линтер, валидация агентов
│   ├── deploy/           (docker)   — Docker, k8s, мониторинг
│   ├── docs/             (49 .md)   — ADR, архитектура, спринты
│   ├── audit_repo/       (314 .py)  — ⚠️ DEAD CODE (должен быть удалён!)
│   ├── v6/, v7/, v8/     (23 .py)   — ⚠️ Устаревшие версии
│   └── venv/             (Python)   — виртуальное окружение
│
├── kernel/atom-federation/  (685 .py) — ATOM kernel (inline-субмодуль)
├── infrastructure/asurdev/  (178 .py) — AsurDev infra
├── pop-os-setup/            (shell)   — Pop!_OS Setup (отдельный проект)
│
├── [ДУБЛИКАТЫ КОРНЯ]: ← СОЗДАЮТ ПУТАНИЦУ
│   ├── config/   (3 files)  — vs astrofin-sentinel-platform/config/
│   ├── deploy/   (4 files)  — vs astrofin-sentinel-platform/deploy/
│   ├── scripts/  (20 .py)   — vs astrofin-sentinel-platform/scripts/
│   ├── tests/    (112 .py)  — vs astrofin-sentinel-platform/tests/
│   ├── docs/     (49 .md)   — vs astrofin-sentinel-platform/docs/
│   ├── ai_scheduler/        — дубликат
│   ├── astrology/           — дубликат
│   ├── atom-core/           — дубликат
│   ├── common/              — дубликат
│   ├── config/              — дубликат
│   ├── data/                — дубликат
│   ├── db/                  — дубликат
│   ├── examples/            — дубликат
│   ├── feature_pipeline/    — дубликат
│   ├── gpu_worker/          — дубликат
│   ├── l10_self_healing/    — дубликат
│   ├── l11_verifier/        — дубликат
│   └── ... (ещё ~20 директорий)
│
├── SOUL.md, ARCHITECTURE.md, CHANGELOG.md, ... ← ДУБЛИКАТЫ с astrofin-sentinel-platform/
└── requirements*.txt, pyproject.toml        ← РАСХОДЯТСЯ с поддиректорией
```

### 3.2 Ключевые технологии

| Слой | Технологии |
|------|-----------|
| **Язык** | Python 3.12 |
| **ML/RL** | numpy, pandas, scikit-learn, FAISS, sentence-transformers, HMM (hmmlearn) |
| **Астрология** | pyswisseph (Swiss Ephemeris) |
| **БД** | SQLite (primary), PostgreSQL + TimescaleDB + pgvector (dual-write) |
| **API** | FastAPI, Dash (Plotly), uvicorn |
| **Фронтенд** | React + Redux Toolkit (web-react/) |
| **Мониторинг** | Prometheus, Grafana, OpenTelemetry, structlog |
| **CI/CD** | GitHub Actions (17 workflows), CodeRabbit, pre-commit hooks |
| **Безопасность** | Bandit, Gitleaks, detect-secrets, `.sops.yaml` |
| **Инфра** | Docker, docker-compose, k8s (kind), systemd |
| **Сеть** | data_room/ (единый сетевой шлюз), httpx, aiohttp |

### 3.3 Модульная карта (Coupling/Cohesion)

```
orchestration/ ←── agents/_impl/ (28 импортов, высокий coupling — OK, это оркестратор)
core/           ←── agents/_impl/ (0 импортов — отличная изоляция!)
data_room/      ←── agents/_impl/ (0 импортов — отличная изоляция!)
agents/_impl/   ←── core/ (эталонный flow: агенты → ядро, не наоборот)
```

Архитектура близка к **Clean Architecture**: `data_room` (инфраструктура) → `core` (домен) → `agents` (бизнес-логика) → `orchestration` (application layer). Хорошая单向 зависимость.

---

## 4. Дубликаты и расхождения

### 4.1 Критические дубликаты

| Тип | Описание | Размер |
|-----|----------|--------|
| **Workspace vs Subdir** | `requirements.txt` (root) vs `astrofin-sentinel-platform/requirements.txt` | 5 отличий |
| **Workspace vs Subdir** | `pyproject.toml` (root: 1432B) vs sub (4892B) | Разные версии |
| **Workspace vs Subdir** | `CHANGELOG.md` (root: 1964B) vs sub (2972B) | Разное содержимое |
| **Workspace vs Subdir** | `SOUL.md`, `ARCHITECTURE.md`, `CLAUDE.md` — идентичны или почти идентичны |
| **Корневые модули** | `config/`, `deploy/`, `scripts/`, `tests/`, `docs/` — все продублированы | ~245 файлов |
| **Dead code** | `audit_repo/` — 314 .py файлов (SOUL.md явно говорит: "audit_repo/ удалён") | 314 файлов |
| **Legacy** | `v6/`, `v7/`, `v8/` — 23 устаревших файла | 23 файла |
| **GitHub forks** | `AstroFinSentinelV5`, `astrofin-sentinel-v5` — дубликаты основного репо | 2 репо |

### 4.2 Ветки с дрейфом

```
origin/master: CI bumps (6a3d777)
main (local):  SEC EDGAR, Telegram, dashboard (6052d66)
Расхождение:   67 коммитов
```

`main` опережает `origin/master` на 67 коммитов. `origin/master` имеет несколько CI-only коммитов, которых нет в `main`. Необходима синхронизация.

---

## 5. Быстрый аудит: Код и Качество

### 5.1 Антипаттерны (SOUL.md violations)

| Антипаттерн | Найдено | Детали |
|-------------|---------|--------|
| `import requests` в агентах | **0** ✅ | R-01 соблюдается |
| `print()` в production | **22** ⚠️ | `karl_synthesis.py` (7), `gitagent_exporter.py` (8), `gitagent_registry.py` (7) |
| `try/except: pass` | **2213** ❌ | Массовое количество (нуждается в аудите — много ложных срабатываний на легитимных `except: pass` в тестах и обработчиках) |
| Хардкод API-ключей | **0** (в коде) ✅ | gitleaks нашёл 61 в `venv/` (vendor-код transformers) — не наш код |
| `audit_repo/` | **314 файлов** ❌ | Должен быть удалён согласно SOUL.md |
| Submodule | **0** ✅ | R-12 соблюдается |

### 5.2 Безопасность (Bandit)

| Severity | Count | Примеры |
|----------|-------|---------|
| **High** | 3 | `subprocess` shell=True, `pickle` loads, `yaml.load` без SafeLoader |
| **Medium** | 8 | `0.0.0.0` bind (1 — помечен #nosec), hardcoded tmp paths |
| **Low** | 130 | assert в production, standard pseudo-random, try/except: pass |

### 5.3 Зависимости (pip outdated)

22 пакета устарели, включая:
- `certifi` 2026.6.17 → 2026.7.22
- `pydantic_core` 2.46.4 → 2.47.0
- `tokenizers` 0.22.2 → 0.23.1
- `websockets` 15.0.1 → 16.1.1

### 5.4 Тесты

```
Статус: 93 passed / 15 skipped / 13 failed (2026-07-22, из supermemory)
Ошибка коллекции: test_llm_router.py — ModuleNotFoundError: sentence_transformers
```

---

## 6. Смежные репозитории: статус интеграции

### 6.1 Федеративный стек (ATOM ecosystem)

Все ATOM-репозитории (`atom-kernel`, `atom-agent`, `atom-operator`, `atom-federation`, `atom-federation-core`, `atom-federation-os`, `atom-router`) находятся на архитектурном уровне v10.x и **не обновлялись с апреля-июня 2026**. Это либо стабильные, либо замороженные компоненты.

`astrofin-federation-stack` (последний push: 2026-07-02) — головной репо федеративного стека, объединяющий ATOM kernel + ROMA bridge + AsurDev. Вероятно, это основной источник для inline-интеграций.

### 6.2 Рекомендации по консолидации GitHub-репозиториев

| Действие | Репо |
|----------|------|
| **Удалить** | `AstroFinSentinelV5`, `astrofin-sentinel-v5` (дубликаты) |
| **Удалить** | `ATOMFederationOS` (дубликат `atom-federation-os`) |
| **Удалить** | `asurdev-workspace-backup-20260326` (устаревший бэкап) |
| **Удалить** | `_afs_token_probe_DO_NOT_USE` (токен-проб) |
| **Архивировать** | `ollama-transfer-template*`, `-my-obsidian-vault-`, `desktop-tutorial` |
| **Рассмотреть** | inline и архив `integrations-gitagent`, `AsurDev`, `AsurDev1.1` |

---

## 7. Следующие шаги

Шаг 1 завершён. Предлагаю вашему вниманию:

1. **APPROVE этот отчёт** перед переходом к Шагу 2 (Глубокий Аудит по категориям)
2. **Критические исправления (можно сразу):**
   - Удалить `audit_repo/` (314 dead-code файлов)
   - Удалить `v6/`, `v7/`, `v8/` (23 legacy файла)
   - Синхронизировать `main` ↔ `origin/master`
3. **Шаг 2 затронет:**
   - Детальный аудит кода (SOLID, DRY, дублирование)
   - Аудит безопасности (3 High bandit issues)
   - Аудит тестов (13 failures)
   - Аудит производительности
   - Извлечение best practices в `artifacts/best_practices/`
   - План консолидации GitHub-репозиториев

**Команда для продолжения:**
> «Продолжай Шаг 2 — глубокий аудит по категориям. Запиши findings в AUDIT_REPORT.md»


---

# Шаг 2: Глубокий Аудит (2026-07-22)

> **Методология:** Статический анализ (grep, bandit, gitleaks), архитектурный линтер, pytest, анализ импортов, ручная инспекция ключевых файлов.
> **Scope:** `agents/`, `core/`, `orchestration/`, `meta_rl/`, `data_room/`, `trading/`, `web/`, `knowledge/`, `tests/`
> **Исключено:** `venv/`, `audit_repo/`, `v6/`/`v7/`/`v8/`, `__pycache__`

---

## 3. Архитектура и Структура

### 3.1 Общая оценка: ⭐⭐⭐⭐☆ (4/5)

Проект следует **чистой многослойной архитектуре** с чётким разделением ответственности:

```
agents/_impl/          ← Application Layer (агенты, AMRE, AstroCouncil)
core/                  ← Domain Layer (BaseAgent, ephemeris, belief, cache, auth)
orchestration/         ← Orchestration Layer (sentinel_v5, broker, router)
data_room/             ← Infrastructure Layer (HTTP gateway, resolvers)
knowledge/             ← Knowledge Layer (RAG index, BM25, hybrid retriever)
meta_rl/               ← ML Layer (evolution, calibration, strategy pool)
trading/               ← Execution Layer (TWAP, order management)
web/                   ← Presentation Layer (Dash, WSGI)
api/                   ← FastAPI Layer (REST endpoints)
```

**Направление зависимостей** — строго однонаправленное:
- `data_room/` → `core/` → `agents/` → `orchestration/` ✅
- 0 обратных импортов `core/` → `agents/_impl/` ✅
- 28 прямых импортов `orchestration/` → `agents/_impl/` (допустимо для оркестратора) ✅

### 3.2 Coupling/Cohesion

| Метрика | Значение | Оценка |
|---------|----------|--------|
| Межмодульные импорты core → agents | **0** | ✅ Идеально |
| Межмодульные импорты orchestration → agents | **28** | ⚠️ Высокий coupling, но оправдан (оркестратор) |
| data_room → agents | **0** | ✅ Чистый gateway |
| R-01 violations (bare requests в агентах) | **0** | ✅ Полное соблюдение |

### 3.3 Структурные проблемы

| Проблема | Серьёзность | Детали |
|----------|------------|--------|
| **Дублирование workspace (root ↔ subdir)** | 🔴 CRITICAL | `config/`, `deploy/`, `scripts/`, `tests/`, `docs/`, `infrastructure/`, `kernel/` — дублируются в корне и `astrofin-sentinel-platform/`. 797+403+566 файлов в корне, 493+577+485 в поддереве. Это не git-worktree — это физические копии. |
| **`requirements.txt` drift** | 🔴 HIGH | Корневой `requirements.txt` ≠ `astrofin-sentinel-platform/requirements.txt` (разные версии `aiohttp`, отсутствует `asyncpg`, `python-telegram-bot`) |
| **Ветка `main` vs `origin/master`** | 🟡 MEDIUM | 67 коммитов расхождения. master содержит consolidation fixes (ruff, arch linter, CI improvements), main содержит Sprint 3-6 features |
| **Feature branches stale** | 🟡 MEDIUM | `feature/architecture-consolidation` (30 ahead, 16 behind main), `feature/step-4.8-rag-linter-migration` (5 ahead, 15 behind) |

---

## 4. Код и Качество

### 4.1 Общая оценка: ⭐⭐⭐☆☆ (3/5)

### 4.2 Антипаттерны

| Антипаттерн | Количество | Серьёзность | Примеры |
|-------------|-----------|------------|---------|
| `print()` в production-коде | **438** | 🟡 MEDIUM | `agents/karl_synthesis.py`, `agents/gitagent_exporter.py`, `agents/gitagent_registry.py` — основные нарушители. Замена на `structlog` охватывает только 12 файлов. |
| `logging.getLogger` (bare) | **81** | 🟡 MEDIUM | Большинство модулей используют `logging` вместо `structlog`. Нет единого standard. |
| `structlog` usage | **12** | — | Только 12 файлов используют правильное structured logging |
| `try/except: pass` | **2,213** | 🔴 HIGH | Массовое подавление исключений. Риск скрытых багов. |
| TODO/FIXME/HACK | ~0 в ядре | ✅ | Чисто |
| `import *` | **0** | ✅ | Отсутствует |

### 4.3 Дублирование кода

| Находка | Детали |
|---------|--------|
| **21 функция с именем `create`** | Разные классы/модули, но сигнатура конфликтует при чтении. Рекомендуется переименовать (например, `create_agent`, `create_buffer`, `create_session`) |
| **Идентичные импорты в 5 агентах** | `bradley_agent.py`, `cycle_agent.py`, `gann_agent.py`, `elliot_agent.py`, `time_window_agent.py` — все начинаются с одинаковых 5 строк импортов |
| **7 архивных дублей агентов** | `agents/_archived/` — уже изолированы ✅ |
| **Корневые файлы агентов** | `agents/fundamental_agent.py`, `agents/macro_agent.py` и др. — помечены ARCHIVED, но всё ещё присутствуют |

### 4.4 Размеры файлов (Top-10 монстров)

| Файл | Строк | Проблема |
|------|-------|----------|
| `agents/_impl/amre/audit.py` | **671** | God object — объединяет DecisionRecord, AuditLog, анализ дрифта, сериализацию |
| `agents/_impl/synthesis_agent.py` | **660** | Синтез-агент раздут |
| `core/rag_client.py` | **643** | RAG-клиент со всей логикой индексации и поиска |
| `agents/gitagent_exporter.py` | **623** | Экспортер с CLI-интерфейсом (print-heavy) |
| `agents/karl_synthesis.py` | **602** | KARL с print()-отладкой |
| `orchestration/sentinel_v5.py` | **550** | Оркестратор со всей логикой запуска |

**Рекомендация:** Файлы >500 строк — кандидаты на split по Single Responsibility.

### 4.5 Linter & CI

| Инструмент | Статус |
|-----------|--------|
| Architecture Linter (`scripts/architecture_linter.py`) | ✅ 0 hard violations |
| Ruff (`.ruff_cache/`) | ✅ Конфигурация присутствует |
| Bandit (security) | ⚠️ 3 High, 8 Medium, 130 Low |
| Gitleaks | ⚠️ 61 finding (все в `venv/`, vendor-код — **не критично**) |
| Pre-commit hooks | ✅ `.pre-commit-config.yaml` присутствует |
| CodeRabbit | ✅ `.coderabbit.yaml` настроен |

---

## 5. Безопасность и Надёжность

### 5.1 Общая оценка: ⭐⭐⭐☆☆ (3/5)

### 5.2 Критические находки

| ID | Находка | Серьёзность | Файлы |
|----|---------|------------|-------|
| **SEC-01** | Жёстко закодированные ключи/токены | 🟡 MEDIUM | 107 совпадений — большинство false-positive (имена переменных `token`, `secret`), но требуется ручная проверка |
| **SEC-02** | SQL-инъекция через f-строки | 🔴 **HIGH** | `tools/rag_admin.py:221` — `f"SELECT COUNT(*) FROM {pg_table}"` |
| **SEC-03** | `eval()` в production | 🔴 **HIGH** | `agents/_impl/amre/meta_questioning.py:112`, `mas_factory/topology.py:61` |
| **SEC-04** | `subprocess(..., shell=True)` | 🟡 MEDIUM | 10 вхождений: `scripts/ralph_agent.py`, `bridge/roma/gpu_worker/server.py`, `kernel/atom-federation/chaos/scenarios.py` |
| **SEC-05** | Слабые хеш-функции (MD5/SHA1) | 🔴 **HIGH** | `agents/_impl/amre/trajectory.py:59`, `agents/karl_synthesis.py:469`, `core/astro_rl_engine.py:33` — Bandit B324: использование `hashlib.md5()` / `hashlib.sha1()` |
| **SEC-06** | Bind на 0.0.0.0 | 🟡 MEDIUM | `web/wsgi.py:166` — `host="0.0.0.0"` (помечен `# nosec B104`, оправдано для dev) |

### 5.3 Аудит аутентификации

| Аспект | Статус |
|--------|--------|
| JWT middleware (`core/auth_jwt_middleware.py`) | ✅ Присутствует — `verify_token`, `require_auth`, `_extract_bearer` |
| API key auth (`web/middleware/`) | ✅ `@require_auth` декоратор |
| Secrets management | ✅ `.env` + GitHub Secrets (R-10 соблюдается) |
| `.gitleaks.toml` | ✅ Настроен |
| `.sops.yaml` | ✅ Настроен (шифрование secrets) |

### 5.4 Error Handling

| Аспект | Статус |
|--------|--------|
| Circuit Breaker | ✅ `core/circuit_breaker.py` |
| Retry logic | ✅ `data_room/resolvers/sec_edgar.py` (exponential backoff) |
| Graceful degradation | ⚠️ Частично — `try/except: pass` (2,213 случаев) маскирует ошибки |
| Structured error responses | ✅ `core/auth_jwt_middleware.py` — типизированные `_AuthFailure` |

---

## 6. Тестирование

### 6.1 Общая оценка: ⭐⭐⭐⭐☆ (4/5)

### 6.2 Результаты тестового прогона (2026-07-22)

| Метрика | Значение |
|---------|----------|
| Всего тестовых файлов | 125 |
| **Прошло** | **664** |
| Пропущено (skip) | **76** |
| Deselected (исключены из прогона) | 15 (5 файлов с known-issues) |
| Упало (в игнорируемых) | 8 (test_rag_index, test_rag_integration, test_api_auth, test_infer_edges, test_require_api_key_decorator) |
| Не импортируется | 1 (test_llm_router.py — отсутствует `sentence_transformers`) |
| Время прогона | ~34 секунды |

### 6.3 Проблемные тесты

| Тест | Причина падения |
|------|----------------|
| `tests/test_llm_router.py` | `ModuleNotFoundError: No module named 'sentence_transformers'` — отсутствует в requirements |
| `tests/test_api_auth.py` | Требует запущенный сервер |
| `tests/test_rag_index.py` | 3 теста падают при инициализации FAISS индекса |
| `tests/test_rag_integration.py` | `test_get_rag_returns_none_when_disabled` |
| `tests/architecture/test_infer_edges.py` | `test_tier_T1_for_high_confidence_valid` — graphify/infer_edges.py не найден |
| `tests/auth/test_require_api_key_decorator.py` | 3 теста падают (API key валидация) |

### 6.4 Coverage Gaps

| Модуль | .py файлов | Тестовых файлов | Покрытие |
|--------|-----------|----------------|----------|
| `trading/` | 14 | **0** | 🔴 0% |
| `core/` | 54 | **0** (прямых) | 🔴 ~0% (тестируется косвенно) |
| `orchestration/` | 11 | **0** | 🔴 0% |
| `meta_rl/` | 37 | 3 | 🟡 ~8% |
| `knowledge/` | 15 | 1 (плюс 3 knowledge-specific) | 🟡 ~25% |
| `data_room/` | 9 | 8 | 🟢 ~89% |
| `agents/` | 58 | ~50 (разбросаны) | 🟢 Высокое (unit-тесты на каждого агента) |

**Критический пробел:** `trading/` (исполнение ордеров) и `orchestration/` (ядро системы) — **ноль прямых тестов**. Это самые рискованные модули с точки зрения финансовых потерь.

---

## 7. Производительность и Scalability

### 7.1 Общая оценка: ⭐⭐⭐☆☆ (3/5)

### 7.2 Потенциальные узкие места

| Проблема | Локация | Риск |
|----------|---------|------|
| **Синхронные HTTP-вызовы в агентах** | `data_room/resolvers/*` | Под нагрузкой 13+ агентов — последовательные вызовы = latency × N |
| **Большие файлы без chunking** | `core/rag_client.py` (643 строки), `orchestration/sentinel_v5.py` (550 строк) | Затрудняет распараллеливание разработки |
| **Отсутствие connection pooling (явное)** | `data_room/resolvers/` | Нет явного httpx.AsyncClient с пулом соединений |
| **21 функция `create`** | Разные модули | Конфликт имён при рефакторинге |
| **1,055 функций в ядре** | `agents/`, `core/`, `orchestration/`, `meta_rl/` | Высокая когнитивная нагрузка |

### 7.3 Позитивные находки

| Аспект | Статус |
|--------|--------|
| PostgreSQL + pgvector (вместо SQLite) | ✅ Мигрировано (Sprint W3) |
| Асинхронный брокер | ✅ `orchestration/sentinel_v5_broker.py` |
| Кэширование | ✅ `core/cache.py`, `core/circuit_breaker.py` |
| RAG с гибридным поиском | ✅ FAISS + BM25 + RRF |
| Outbox pattern | ✅ `core/outbox.py` |

---

## 8. Зависимости и Инфраструктура

### 8.1 Общая оценка: ⭐⭐⭐☆☆ (3/5)

### 8.2 Outdated пакеты (критические)

| Пакет | Текущая | Latest | Gap |
|--------|---------|--------|-----|
| `boto3` | 1.40.61 | 1.43.53 | 3 minor |
| `aiobotocore` | 2.25.1 | 3.8.0 | **MAJOR** |
| `bandit` | 1.8.0 | 1.9.4 | 1 minor |
| `ansible` | 13.5.0 | 14.2.0 | **MAJOR** |
| `anthropic` | 0.117.0 | 0.117.1 | patch |
| `websockets` | 15.0.1 | 16.1.1 | **MAJOR** |

### 8.3 Requirements files — фрагментация

| Файл | Строк | Назначение |
|------|-------|-----------|
| `requirements.txt` | 35 | Основной (корень) |
| `requirements.all.txt` | 35 | Основной (поддерево) |
| `requirements-core.txt` | 36 | Core зависимости |
| `requirements-dev.txt` | 22 | Dev-инструменты |
| `requirements-test.txt` | 14 | Тестовые зависимости |
| `requirements-web.txt` | 16 | Web-зависимости |
| `requirements-optional.txt` | 23 | Опциональные |

**Проблема:** 7 файлов требований с пересекающимся содержимым. `requirements.all.txt` и `requirements.txt` дублируют друг друга с небольшими различиями.

### 8.4 CI/CD

| Workflow | Назначение |
|----------|-----------|
| `ci.yml` | Основной CI: 4 архитектурных джобы (lint, validate, registry, known-issues) |
| `lint.yml` | Ruff линтинг |
| `security.yml` / `ci.security.yml` | Bandit + Gitleaks |
| `secret-scan.yml` | Сканирование секретов |
| `pr-checks.yml` | PR проверки |
| `quality-gate.yml` | Quality gate |
| `coverage.yml` | Coverage (порог 10%) |
| `deploy.yml` / `release.yml` | Деплой и релиз |
| `nightly.yml` | Ночные прогоны |
| `load-test.yml` | Нагрузочное тестирование |
| `compose-check.yml` | Docker compose проверка |
| `graphify-healthcheck.yml` | Graphify healthcheck |
| `auto-label.yml` | Автоматические метки PR |
| `coderabbit-pr-review.yml` | CodeRabbit AI ревью |
| `coderabbit-safety-scan.yml` | CodeRabbit safety scan |

**Оценка:** 16 workflow-файлов — **over-engineered** для текущего состояния. Некоторые пересекаются (3 security-related workflow).

### 8.5 Docker

| Файл | Назначение |
|------|-----------|
| `Dockerfile` | Основной образ |
| `docker-compose.pgvector.yml` | PostgreSQL + pgvector |
| `ml_engine/Dockerfile` | ML-движок |
| `infrastructure/asurdev/perses/docker-compose.yml` | Perses мониторинг |
| `infrastructure/asurdev/docker-compose.monitoring.yml` | Общий мониторинг |

---

## 9. Полезные Артефакты (Best Practices)

### 9.1 Уже каталогизированы в `artifacts/best_practices/`

```
artifacts/best_practices/
├── README.md
├── agents/          ← Эталонные реализации агентов
├── auth/            ← JWT middleware, require_auth
├── contracts/       ← AgentResponse, TradingSignal, типы
├── core/            ← BaseAgent, cache, circuit_breaker
├── error_handling/  ← CircuitBreaker, RetryHandler
├── governance/      ← ACOS governance
├── infra/           ← Docker, CI шаблоны
├── llm_router_exemplar.py  ← Эталонный LLM Router
├── patterns/        ← Архитектурные паттерны
├── rtk_slice_exemplar.ts  ← Redux Toolkit эталон
├── settings/        ← Settings management
└── testing/         ← Тестовые утилиты
```

### 9.2 Выдающиеся компоненты (рекомендуются к сохранению)

| Компонент | Почему ценен |
|-----------|-------------|
| `core/circuit_breaker.py` | Правильный Circuit Breaker с half-open состоянием |
| `core/outbox.py` | Transactional Outbox pattern — гарантированная доставка событий |
| `data_room/resolvers/sec_edgar.py` | Production-grade HTTP клиент: rate limiting, exponential retry, disk cache, CIK lookup |
| `core/auth_jwt_middleware.py` | Типизированные ошибки с `_AuthFailure`, constant-time сравнение |
| `core/belief.py` | Bayesian belief tracking — хорошая математическая модель |
| `core/cache.py` | TTL-кэш с инвалидацией |
| `agents/_impl/ephemeris_decorator.py` | `@require_ephemeris` — чистый декоратор для astro-зависимых агентов |
| `scripts/architecture_linter.py` | Кастомный архитектурный линтер (редкая практика) |
| `scripts/validate_agent.py` | Валидатор агентов с 9 проверками |

### 9.3 Компоненты, требующие доработки

| Компонент | Проблема | Рекомендация |
|-----------|----------|-------------|
| `agents/karl_synthesis.py` | 602 строки + 22 `print()` | Разделить на `karl_core.py` + `karl_diagnostics.py`, перевести на structlog |
| `agents/gitagent_exporter.py` | 623 строки + CLI в production-коде | Выделить CLI в `scripts/gitagent_cli.py` |
| `orchestration/sentinel_v5.py` | 550 строк — God function | Разделить на `pipeline.py`, `runner.py`, `config.py` |
| `core/rag_client.py` | 643 строки — монолит | Разделить на `indexer.py`, `retriever.py`, `embedder.py` |

---

## 10. Сводная таблица оценок

| Категория | Оценка | Ключевой риск |
|-----------|--------|---------------|
| Архитектура и структура | ⭐⭐⭐⭐☆ (4/5) | Дублирование workspace, дрейф main↔master |
| Код и качество | ⭐⭐⭐☆☆ (3/5) | 438 `print()`, 2,213 `except: pass`, 81 bare `logging` |
| Безопасность | ⭐⭐⭐☆☆ (3/5) | SQL-инъекция (1), `eval()` (2), слабые хеши (3) |
| Тестирование | ⭐⭐⭐⭐☆ (4/5) | 664 passed, но `trading/` и `orchestration/` без тестов |
| Производительность | ⭐⭐⭐☆☆ (3/5) | Синхронные HTTP, нет connection pooling |
| Зависимости и инфраструктура | ⭐⭐⭐☆☆ (3/5) | 7 разрозненных requirements, 16 CI workflow |
| **Общая (средняя)** | **⭐⭐⭐½☆ (3.3/5)** | **Production-Beta: готов к GA после закрытия P0** |

---

## 11. Приоритизированный план исправлений (P0 → P3)

### P0 — CRITICAL (блокирует GA)

| # | Проблема | Действие | Оценка |
|---|----------|----------|--------|
| P0-01 | SQL-инъекция в `tools/rag_admin.py:221` | Заменить f-строку на параметризованный запрос | 5 мин |
| P0-02 | `eval()` в `meta_questioning.py:112` и `mas_factory/topology.py:61` | Заменить на `ast.literal_eval()` или безопасный парсер | 15 мин |
| P0-03 | Слабые хеши (MD5/SHA1) в 3 файлах | Заменить на `hashlib.sha256()` | 10 мин |
| P0-04 | `trading/` и `orchestration/` без тестов | Написать минимум smoke-тесты для execution pipeline | 4 ч |

### P1 — HIGH (блокирует Production)

| # | Проблема | Действие | Оценка |
|---|----------|----------|--------|
| P1-01 | `print()` → `structlog` в 438 местах | Массовая замена с сохранением отладочных в `logger.debug()` | 3 ч |
| P1-02 | 2,213 `except: pass` | Аудит и замена на `logger.exception()` или `raise` | 8 ч |
| P1-03 | Дрифт `main` ↔ `origin/master` (67 коммитов) | Синхронизация веток, ручное слияние | 2 ч |
| P1-04 | `sentence_transformers` missing → `test_llm_router.py` падает | Добавить в `requirements.txt` или `requirements-optional.txt` | 5 мин |

### P2 — MEDIUM (технический долг)

| # | Проблема | Действие | Оценка |
|---|----------|----------|--------|
| P2-01 | Дублирование workspace (root ↔ subdir) | Удалить дубликаты, оставить только `astrofin-sentinel-platform/` | 1 ч |
| P2-02 | Консолидация 7 requirements файлов | Объединить в 3: `requirements.txt`, `requirements-dev.txt`, `requirements-optional.txt` | 30 мин |
| P2-03 | 16 CI workflow → overhead | Объединить `security.yml` + `ci.security.yml` + `secret-scan.yml` в один | 30 мин |
| P2-04 | God-файлы >500 строк | Разделить `karl_synthesis.py`, `sentinel_v5.py`, `rag_client.py` | 6 ч |
| P2-05 | 21 функция `create` — конфликт имён | Переименовать на семантические: `create_decision_record`, `create_buffer` | 1 ч |

### P3 — LOW (качество жизни)

| # | Проблема | Действие | Оценка |
|---|----------|----------|--------|
| P3-01 | Удаление дублирующих GitHub-репозиториев | Архивировать `AstroFinSentinelV5`, `astrofin-sentinel-v5`, `ATOMFederationOS` | 10 мин |
| P3-02 | Stale feature branches | Смёрджить или удалить `feature/architecture-consolidation`, `feature/step-4.8-rag-linter-migration` | 15 мин |
| P3-03 | 81 `logging.getLogger` → `structlog` | Плановая миграция | 4 ч |
| P3-04 | Connection pooling в `data_room/resolvers/` | Добавить `httpx.AsyncClient` с пулом | 1 ч |

---

## 12. Следующие шаги (к Шагу 3)

**Ваш approve необходим для перехода к Шагу 3 (Консолидация), который включает:**

1. **P0 fixes** — немедленное исправление критических уязвимостей
2. **CONSOLIDATION_PLAN.md** — пошаговый план слияния workspace + веток + репозиториев
3. **Обновление `artifacts/best_practices/`** — дополнение каталога лучших компонентов
4. **Рефакторинг ключевых God-файлов** — split `karl_synthesis.py`, `sentinel_v5.py`, `rag_client.py`
5. **Унификация требований** — 7→3 requirements файла
6. **Чистка GitHub** — архивирование дублирующих репозиториев
