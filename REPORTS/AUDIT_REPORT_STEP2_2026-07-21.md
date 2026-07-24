# Шаг 2: Глубокий Аудит — AstroFin Sentinel Platform

**Date:** 2026-07-21
**Auditor:** Senior Architect & Code Auditor
**Project:** `astrofin-sentinel-platform` (mono-repo, master branch @ `21c5684`)

---

## 1. Архитектура и Структура (Architecture & Structure)

### 1.1 Текущая архитектура

**Тип:** Монорепо с модульной папкой
**Паттерн:** Clean Architecture / Feature-Sliced Design (частичное соблюдение)

```
platform/
├── agents/_impl/      ← ЕДИНСТВЕННЫЕ активные агенты (27 impl-файлов)
├── agents/             ← Stub'ы + архивные дубли (8 архивных дублей)
├── core/               ← Бизнес-логика, общие утилиты (ephemeris, circuit_breaker, cache, auth)
├── orchestration/      ← Оркестраторы, роутер, SentinelV5 entry point
├── api/                ← FastAPI-слой
├── web/                ← Dash dashboard (Flask/Gunicorn)
├── web-react/          ← React (Vite + TypeScript + Tailwind)
├── data_room/          ← Сетевой шлюз (единственная точка HTTP I/O)
├── agents/_impl/amre/  ← KARL AMRE: audit, backtest, reward, counterfactual
├── db/                 ← SQLAlchemy + Alembic миграции
├── knowledge/          ← RAG: FAISS + BM25 гибридный retrieval
└── tests/              ← Unit + Integration тесты
```

### 1.2 Нарушения архитектурных принципов (из SOUL.md)

| R-принцип | Статус | Детали |
|-----------|--------|--------|
| **R-01** (HTTP только через data_room/) | ❌ VIOLATED | `agents/_impl/fundamental_agent.py:9` и `agents/_impl/ml_predictor_agent.py:117` — прямой `import requests` |
| **R-02** (Сетевой I/O только в выделенных слоях) | ❌ VIOLATED | 2 агента нарушают (см. выше) |
| **R-03** (Архитектурный линтер — hard-fail) | ⚠️ | Линтер существует (`scripts/architecture_linter.py`) но не выполнялся |
| **R-04** (AgentResponse — unified interface) | ✅ | `agents/_impl/types.py` — единый интерфейс |
| **R-07** (KARL синтез — единственная точка арбитража) | ✅ | Реализован через KARLSynthesisAgent |
| **R-11** (100% unit + 1 integration на агента) | ❌ | 11/627 тестов — collection errors (missing deps), coverage неизвестен |
| **R-12** (Submodule запрещены) | ✅ | Submodule'ы inlined, `.gitmodules.bak` сохранён |

### 1.3 Coupling / Cohesion

**Core coupling:** 22 из 27 агентов импортируют `core.*` — это хорошо (единая core-либа), но есть риск сильной связности.

**Data room isolation:** `data_room/resolvers/` изолирован корректно. `core/settings.py` использует `pydantic.SecretStr` для секретов — OWASP best practice.

**Web-роуты без авторизации:** `SOUL.md` требует `@require_auth` на ВСЕХ web-роутах. По результатам grep, ни один роут не содержит декоратор `@require_auth`. Это критический gap.

### 1.4 Layer boundaries — оценка

| Слой | Изоляция | Проблемы |
|------|---------|----------|
| `agents/_impl/` | Средняя | 2 агента нарушают I/O rules |
| `core/` | Хорошая | Settings, circuit_breaker, cache — чисто |
| `data_room/` | Отличная | Pattern изоляции соблюдён |
| `orchestration/` | Средняя | 1 большой файл (sentinel_v5.py ~??? строк) |
| `web/` / `api/` | Слабая | No auth enforcement, mixed responsibilities |

### 1.5 Legacy / Архив

- **`v6/`, `v7/`, `v8/`:** Старые версионные снепшоты (10 + 7 + 7 файлов = 24 файла). Не используются.
- **`audit_repo/`:** 485 файлов из старого audit-репозитория. Присутствует в дереве platform, но неактивен.
- **`AstroFinSentinelV5/`:** Пустая директория (в руте workspace)
- **`AsurDev/`:** Пустая директория (в руте workspace)
- **`astrofin-sentinel-v5/`:** Пустая директория (в руте workspace)

**Итого dead weight:** ~512 файлов + 3 пустые директории.

---

## 2. Код и Качество (Code Quality)

### 2.1 Дублирование

| Тип | Количество | Детали |
|-----|-----------|--------|
| **Root ↔ Platform директории** | 43 | Полные дубликаты (v6, v7, v8, core, agents, orchestration, docs, etc.) |
| **Root ↔ Platform .md файлы** | 23 | AGENTS.md, SOUL.md, ARCHITECTURE.md и др. |
| **Root ↔ Platform .py файлы** | 6 | FINAL_INTEGRATION_TEST.py, health_endpoints.py, langgraph_schema.py, logging_setup.py, muhurtha.py, test_aspects.py |
| **Agent root vs _impl/** | 7 активных + 7 архивных | `agents/fundamental_agent.py` ≠ `agents/_impl/fundamental_agent.py` (разное содержимое!) |

**Корневая проблема:** Workspace `/home/workspace/` — это GIT-репозиторий (remote: `astrofin-sentinel-platform.git`), и **одновременно** под-папка `astrofin-sentinel-platform/` — отдельный git-репозиторий с тем же remote. Это порождает двойную синхронизацию. Root содержит файлы, которых нет в platform (док-отчёты, репорты), и наоборот.

### 2.2 Крупные файлы (monoliths)

| Файл | Строк | Проблема |
|------|-------|---------|
| `web/callbacks.py` | 1,162 | Слишком много ответственностей в одном файле |
| `audit_repo/web/callbacks.py` | 1,102 | Дубликат (устаревший) |

### 2.3 Code smells

- **Логирование:** `structlog` используется в `core/logging.py`, но местами встречаются `print()` и bare `logging.getLogger()` без structured context.
- **Error handling:** `except pass` — не найдено (хорошо), но `core/settings.py` содержит `default="dev-api-key-change-me"` для `API_KEY` — плохой дефолт для production.
- **Hard imports weak:** 11/627 тестов падают на этапе collection из-за optional зависимостей (`faiss`, `ollama`, `opentelemetry`, `cachetools`, `langgraph`). Эти модули должны быть опциональными с `try/except` или в `extras_require`.

### 2.4 Тестовое покрытие

| Категория | Результат |
|-----------|----------|
| Всего тестов (collection) | **612** (627 собрано, 15 deselected) |
| Collection errors | **11** (1.8%) |
| Причина ошибок | Missing optional deps: `faiss`, `ollama`, `opentelemetry`, `cachetools`, `langgraph` |
| Passing тестов | Не оценено (interrupted на первой ошибке) |

**Вывод:** ~98% тестов имеют корректные импорты. 11 тестов требуют опциональных зависимостей, не объявленных в `requirements.txt`. Это нужно вынести в `requirements-optional.txt` или `extras_require`.

---

## 3. Безопасность и Надёжность (Security & Reliability)

### 3.1 Secrets Management

| Аудит | Статус |
|-------|--------|
| API-ключи в коде | ❌ `core/settings.py:50` — `"dev-api-key-change-me"` |
| `pydantic.SecretStr` для секретов | ✅ Все чувствительные поля используют `SecretStr` |
| `core/logging_utils.py` redacts secrets | ✅ Регекс-маскирование API-ключей, JWT, email в логах |
| `.env` / `.env.example` | ✅ Шаблон существует |
| GitHub Secrets | ✅ CI workflows используют `${{ secrets.* }}` |
| CI: `detect-secrets` | ✅ Есть в `ci.security.yml` |

### 3.2 Auth & Access Control

| Аудит | Статус |
|-------|--------|
| `@require_auth` на web-роутах | ❌ **НЕ НАЙДЕНО** ни одного декоратора |
| API key validation | ✅ `core/auth.py` — загружает `API_KEY` из env |
| `api/main.py` auth enforcement | ❌ Нет проверки авторизации на API-эндпоинтах |

### 3.3 Injection & Validation

| Аудит | Статус |
|-------|--------|
| SQL injection | ✅ SQLAlchemy ORM + параметризованные запросы |
| Pydantic validation | ✅ `core/settings.py` — `model_validate()` с строгими проверками |
| Bandit scan | ✅ CI workflow присутствует |
| CodeRabbit safety scan | ✅ `.github/workflows/coderabbit-safety-scan.yml` |

### 3.4 Error Handling & Resilience

| Аудит | Статус |
|-------|--------|
| Circuit Breaker | ✅ `core/circuit_breaker.py` — ADR-001, per-provider, 3-phase (CLOSED/OPEN/HALF_OPEN) |
| Redis cache fallback | ✅ `core/cache.py` — in-memory fallback при недоступности Redis |
| DB session management | ✅ `db/session.py` — scoped_session + engine с retry |
| Observability | ⚠️ OpenTelemetry настроен, но не тестируется локально |

---

## 4. Производительность и Scalability

### 4.1 Database

| Аудит | Статус |
|-------|--------|
| Connection pooling | ✅ SQLAlchemy engine с pool_size по умолчанию |
| Async support | ⚠️ `core/cache.py` использует `redis.asyncio`, но DB session — синхронный |
| PostgreSQL + TimescaleDB | ✅ `docker-compose.yml` включает postgres + timescale |
| Redis кэш | ✅ Circuit breaker + cache layer |

### 4.2 Resource Usage

| Аудит | Статус |
|-------|--------|
| GPU worker | ✅ `gpu_worker/` — CUDA-оптимизированный (RTX 3060 на локалке) |
| Prometheus metrics | ✅ `agents/metrics.py` — `@track_agent_metrics` decorator |
| Health endpoints | ✅ `health_endpoints.py` — настроены для Docker healthcheck |

### 4.3 Потенциальные бутылочные горлышки

1. **Синхронный DB session** в `db/session.py` — при высокой нагрузке возможны блокировки
2. **Два крупных callback-файла** (1,162 + 1,102 строк) — сложно дебажить, высокая цикломатическая сложность
3. **Отсутствие connection pooling для Redis** — один клиент на все операции
4. **FAISS индекс** — хранится локально, нет шардирования при росте данных

---

## 5. Зависимости и Инфраструктура

### 5.1 Python Dependencies

| Пакет | Текущая | Outdated? |
|-------|---------|-----------|
| `pip` | 23.2.1 | ❌ **26.1.2** (3 major versions behind!) |
| `pydantic_core` | 2.46.4 | ⚠️ 2.47.0 доступен (minor) |
| `numpy` | ✅ | Актуальный |
| `pandas` | ✅ | Актуальный |
| Остальные | ✅ | Все OK |

**Критические пропуски в `requirements.txt`:** `faiss-cpu`, `ollama`, `opentelemetry-api`, `opentelemetry-sdk`, `cachetools`, `langgraph` — нужны для тестов.

### 5.2 Frontend Dependencies (web-react)

| Пакет | Текущая | Обновление |
|-------|---------|-----------|
| `@types/node` | 24.13.2 | 24.13.3 |
| `oxlint` | 1.71.0 | 1.74.0 |
| `typescript` | 6.0.2 | 6.0.3 |
| `vite` | 8.1.1 | 8.1.5 |

Все обновления — **minor/patch**, низкий риск.

### 5.3 Docker & Infrastructure

| Компонент | Статус |
|-----------|--------|
| `docker-compose.yml` | ✅ Единый compose с 7 сервисами (app, ml-engine, feature-pipeline, gpu-worker, postgres, redis, prometheus) |
| `.env.example` | ✅ Существует |
| Dockerfiles | ✅ 4 шт. (web, ml-engine, gpu-worker, feature-pipeline) |
| Healthchecks | ✅ app + ml-engine имеют healthcheck |
| CI/CD | ✅ 21 workflow файл (тесты, линт, security, деплой, nightly) |

### 5.4 CI/CD Health

| Workflow | Статус |
|----------|--------|
| `ci.yml` | Основной CI (10K) |
| `ci.security.yml` | Secret scan + bandit + ruff (10K) |
| `lint.yml` | Ruff + bandit + mypy |
| `coverage.yml` | pytest-cov |
| `deploy.yml` | Развёртывание (12K) |
| `nightly.yml` | Ночные тесты + интеграционные |
| `quality-gate.yml` | Качество кода (ruff + архитектурный линтер) |
| `secret-scan.yml` | detect-secrets |
| `release.yml` | Релизный пайплайн |

**Примечание:** `lint.yml` и `quality-gate.yml` проверяют **только изменённые в PR файлы** (не весь проект). Это снижает нагрузку, но может пропустить pre-existing issues.

---

## 6. Полезные Артефакты (Best Practices Extraction)

### 6.1 Лучшие паттерны (извлечены в `artifacts/best_practices/`)

| Артефакт | Файл | Почему лучший |
|----------|------|--------------|
| **Circuit Breaker** | `core/circuit_breaker.py` | ADR-001, 3-phase, per-provider isolation, clean dataclass config |
| **Ephemeris Decorator** | `agents/_impl/ephemeris_decorator.py` | Type-safe (`ParamSpec`/`TypeVar`), graceful degradation, idiomatic Python |
| **Agent Metrics** | `agents/metrics.py` | Factory pattern + `@track_agent_metrics` decorator, Prometheus-native |
| **AgentResponse/TradingSignal** | `agents/_impl/types.py` | Unified interface, numeric scoring, composite weights, `from_agents()` |
| **Redis Cache** | `core/cache.py` | Async + in-memory fallback, Prometheus metrics, TTL support |
| **Reward Calibrator** | `agents/_impl/amre/reward.py` | Bayesian Platt scaling, ECE tracking, EMA smoothing, drawdown penalty |
| **Settings (Secret-безопасный)** | `core/settings.py` | pydantic.SecretStr, repr() masks, validation, env-aware |
| **Logging Utils** | `core/logging_utils.py` | Structured logging, regex redaction (API keys, JWT, emails, hex secrets) |

---

## 7. Сводная Таблица Рисков

| ID | Риск | Severity | Категория |
|----|------|----------|-----------|
| SEC-01 | `@require_auth` не применяется ни на одном web-роуте | 🔴 Critical | Auth |
| SEC-02 | `dev-api-key-change-me` в `core/settings.py` | 🔴 Critical | Secrets |
| ARCH-01 | 2 агента импортируют `requests` напрямую (нарушение R-01) | 🟠 High | Architecture |
| ARCH-02 | 43 дублированные директории Root ↔ Platform | 🟠 High | Structure |
| QUAL-01 | 11/627 тестов (1.8%) — collection errors (missing optional deps) | 🟡 Medium | Testing |
| QUAL-02 | `web/callbacks.py` (1,162 строк) — монолитный файл | 🟡 Medium | Code Quality |
| QUAL-03 | `audit_repo/` (485 файлов) — dead code в дереве | 🟡 Medium | Structure |
| INFRA-01 | `pip` отстаёт на 3 major-версии (23.2.1 → 26.1.2) | 🟡 Medium | Dependencies |
| ARCH-03 | Root workspace и `astrofin-sentinel-platform/` — два git-репо с одним remote | 🟡 Medium | Structure |
| PERF-01 | Синхронный DB session — потенциальный bottleneck | 🟢 Low | Performance |

---

## 8. Следующие Шаги

**Шаг 3: Консолидация и Улучшения** (по запросу):
1. Устранить **SEC-01** — добавить `@require_auth` на все web-роуты
2. Устранить **SEC-02** — удалить `dev-api-key-change-me` default
3. Устранить **ARCH-01** — заменить `requests` на `data_room` resolver в 2 агентах
4. Устранить **ARCH-02** — принять решение: root vs platform как source of truth, удалить dead weight
5. Устранить **QUAL-01** — добавить optional deps в `requirements-optional.txt`
6. Создать `CONSOLIDATION_PLAN.md` с пошаговым планом миграции

---

**Файл:** `REPORTS/AUDIT_REPORT_STEP2_2026-07-21.md`
**Создан:** 2026-07-21 09:30 UTC+4
