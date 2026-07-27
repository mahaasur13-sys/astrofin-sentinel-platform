# AstroFin Sentinel Platform — Глубокий Аудит (Шаг 2)

**Дата:** 2026-07-27  
**Аудитор:** Senior Architect & Code Auditor (Zo)  
**Проект:** `astrofin-sentinel-platform`  
**Ветка:** `release/v1.0.0`  
**Workspace:** `/home/workspace` (flat structure, Zo sandbox)

---

## Executive Summary

| Метрика | Значение | Оценка |
|---------|----------|--------|
| Python-файлов | 21,869 (активных ~400) | ⚠️ Много мусора |
| Активных агентов | 25 в `agents/_impl/` | ✅ |
| Тестов | 833 collected (848 total, 15 deselected) | ✅ |
| KI-125a skip | 53 тестов | 🔴 |
| Test failures | 1 (test_broker_overhead_acceptable) | 🟡 |
| Bandit HIGH | 0 | ✅ |
| Bandit MEDIUM | 1 (B108 /tmp в sec_edgar) | 🟡 |
| Pip-audit уязвимостей | 3 (chromadb, diskcache, ragas) | 🟡 |
| CI воркфлоу | 9 активных (+4 устаревших) | ✅ |
| PostgreSQL | Online, TimescaleDB 2.28.3, pgvector 0.8.0 | ✅ |
| Архитектурный линтер | 0 нарушений (проходит) | ✅ |
| Коммитов за неделю | 183 (35 merge) | 🔴 Слишком много |

**Общий вердикт:** Проект в хорошей форме для v1.0.0-beta, но требует хирургической чистки перед GA. Ключевые риски: 53 пропущенных теста, 1 реальный тестовый сбой, 3 уязвимости в зависимостях, высокая частота merge-коммитов (признак хаотичного CI).

---

## 1. Архитектура и Структура

### 1.1 Монорепо vs Микросервисы

**Текущий подход:** Монорепо с плоской структурой. 50+ top-level директорий. Все модули в одном Python-пакете.

**Оценка:** ✅ Выбрано правильно для текущей стадии (v1.0.0-beta). Микросервисы были бы преждевременны для команды из 1-2 разработчиков.

### 1.2 Границы модулей и Coupling/Cohesion

| Модуль | Файлов | Размер | Cohesion | Coupling |
|--------|--------|--------|----------|----------|
| `agents/` | 60 | 1.1M | 🟡 Средняя (25 агентов, 6,292 строк) | 🔴 Высокий — многие агенты импортируют ядро напрямую |
| `core/` | 66 | 1.7M | 🟡 Средняя — смесь эфемерид, auth, RAG, rate_limit, security | 🔴 Высокий — `core/` разросся до God-module |
| `meta_rl/` | 45 | 529K | ✅ Хорошая — чёткая зона ответственности (Meta-RL pipeline) | 🟡 Средний |
| `data_room/` | 11 | 91K | ✅ Отличная — единая точка входа для внешних API | ✅ Низкий |
| `orchestration/` | 14 | 176K | ✅ Хорошая — оркестрация Sentinel | 🟡 Средний |
| `deploy/` | 168 | 1.7M | 🔴 Низкая — смесь IAC, мониторинга, Docker, systemd, Ansible | 🟡 Средний |

**Критические находки:**

1. **`core/` — God-module (66 файлов, 1.7MB):** Смешивает эфемериды, аутентификацию, RAG-клиент, rate-limiting, security middleware, FastAPI/Flask адаптеры. Рекомендуется split на `core/domain/` (ephemeris, aspects, beliefs) и `core/infra/` (auth, rate_limit, middleware).

2. **`deploy/iac/` — монстр на 168 файлов:** Содержит Ansible, Terraform, k8s, systemd, собственный `pyproject.toml`, тесты и даже копию `acos`. Это отдельный продукт, который не должен жить внутри монорепо.

3. **`agents/_impl/amre/` — 14 модулей внутри `_impl/`:** AMRE заслуживает собственной директории верхнего уровня (`amre/`) или как минимум `agents/amre/`. Сейчас это 14 модулей внутри `_impl/`, что нарушает иерархию (AMRE не является агентом).

4. **R-01 (data_room) — чисто:** Ни один активный агент не импортирует `requests` напрямую. Все HTTP через `data_room/`. ✅

5. **Flask/FastAPI дуализм:** Проект использует и Flask (web/, core/auth.py) и FastAPI (api/main.py). Flask-часть — legacy (тесты на Flask-специфичные фичи игнорируются в pytest). Нужен план миграции Flask → FastAPI для v1.1.0.

### 1.3 Соответствие Clean Architecture

| Слой | Реализация | Оценка |
|------|-----------|--------|
| Domain | `core/ephemeris.py`, `core/aspects.py`, `agents/_impl/types.py` | ✅ |
| Application | `orchestration/sentinel_v5.py`, `meta_rl/` | ✅ |
| Infrastructure | `data_room/`, `core/rag_client.py`, `db/` | 🟡 (Flask/FastAPI дуализм) |
| Presentation | `web/`, `api/`, `web-react/` | 🟡 (два фреймворка) |

---

## 2. Код и Качество

### 2.1 Размеры файлов — Top-10 рисков

| Файл | Строк | Проблема |
|------|-------|----------|
| `agents/_impl/amre/audit.py` | 671 | Крупнейший файл — кандидат №1 на split |
| `agents/_impl/synthesis_agent.py` | 659 | Sprint B должен был распилить callbacks — проверка: файл не разбит |
| `core/rag_client.py` | 643 | Разросся — смешивает RAG, FAISS, BM25 |
| `agents/gitagent_exporter.py` | 627 | GitAgent интеграция — должен быть в `integrations/gitagent/` |
| `backtest/engine.py` | 611 | Бэктест-движок — допустимо для научного кода |
| `api/main.py` | 576 | FastAPI main — допустимо для монолитного API |
| `agents/gitagent_registry.py` | 561 | Дублирует gitagent_exporter — объединить |
| `core/belief.py` | 521 | Bayesian belief tracking — допустимо |
| `meta_rl/evolution.py` | 519 | Evolution engine — допустимо |
| `meta_rl/strategy_pool.py` | 504 | Strategy pool — допустимо |

**Правило:** Файлы >500 строк — candidate for decomposition. Исключение: научные/ML-модули где целостность важнее размера.

### 2.2 Дублирование кода

| Пара | Diff-строк | Вердикт |
|------|-----------|---------|
| `bull_researcher.py` ↔ `bear_researcher.py` | 268 строк разницы | ✅ By design — симметричные агенты |
| `gitagent_exporter.py` ↔ `gitagent_registry.py` | 627/561 строк | 🔴 Кандидаты на слияние в `integrations/gitagent/` |

### 2.3 SOLID / DRY / KISS

- **Single Responsibility:** Нарушается в `synthesis_agent.py` (659 строк, должен быть coordinator, а не God-agent) и `core/rag_client.py` (смесь RAG + FAISS + BM25 + observability).
- **Open/Closed:** ✅ Хорошо — `BaseAgent` и `AgentResponse` позволяют добавлять агентов без изменения ядра.
- **Liskov Substitution:** ✅ Все агенты реализуют `async def run(self, state: dict) -> AgentResponse` (19 из 22 используют идентичную сигнатуру).
- **Interface Segregation:** 🟡 Частично. `BaseAgent` имеет 5 строк — хорошо. Но `AgentResponse` содержит поля для всех возможных агентов (раздутый интерфейс).
- **Dependency Inversion:** 🟡 `data_room/` — отличный пример. Но `core/` напрямую зависит от Flask, httpx, и других конкретных реализаций.

### 2.4 Устаревшие паттерны

- **Flask (legacy):** 10 импортов `flask` в core/ и web/. FastAPI — современная замена, уже используется в api/. Flask-роуты должны быть мигрированы.
- **Deprecated typing (Dict, List, Optional):** 0 использований ✅ — проект перешёл на `dict`, `list`, `X | None`.
- **Root-дубли агентов:** 7 файлов архивированы в `agents/_archived/` ✅.

### 2.5 Неиспользуемые импорты

```
F401 orchestration/council_orchestrator.py: unused os, TradingMode
F401 orchestration/karl_cli.py: unused rich.table.Table
```

Мелкие проблемы, 3 исправления.

---

## 3. Безопасность и Надёжность

### 3.1 Bandit Scan

| Severity | Count | Детали |
|----------|-------|--------|
| HIGH | 0 | ✅ |
| MEDIUM | 1 | B108: `/tmp/sec_edgar_cache` — предсказуемый путь |
| LOW | 195 | B101 (assert в тестах) — допустимо |

**B108 Fix:** `_CACHE_DIR = Path(os.getenv("SEC_CACHE_DIR", "/tmp/sec_edgar_cache"))` → использовать `tempfile.gettempdir()` или выделенный `XDG_CACHE_HOME`.

### 3.2 Pip-audit (Уязвимости)

| Пакет | Версия | Уязвимость |
|-------|--------|------------|
| `chromadb` | 1.5.5 | PYSEC-2026-311 |
| `diskcache` | 5.6.3 | PYSEC-2026-2447 |
| `ragas` | 0.4.3 | PYSEC-2026-3046 |

Все три — non-critical (не RCE), но требуют обновления до безопасных версий.

### 3.3 Secrets

✅ `.env` в `.gitignore`, `.env.example` — чист. Bandit 0 findings по хардкод-секретам. Gitleaks в CI активен.

### 3.4 Error Handling & Logging

- **Стандартизация ошибок:** KI-127 внедрил `core/error_schema.format_error` с полем `error`. ✅
- **Логирование:** `structlog` используется. 🟡 Не все модули логируют структурно — проверка выборочная.
- **API-ключи:** `API_KEY_AUTH_DISABLED` (inverted semantics) с DeprecationWarning. 🟡 Нужно убрать shim после v1.0.0.

### 3.5 Тестирование

| Метрика | Значение |
|---------|----------|
| Всего тестов | 848 collected (15 deselected) |
| Активных (running) | ~780 |
| KI-125a skipped | 53 |
| Реальных failures | 1 |
| Категории skip | architecture (3), calibration (8), dual_mode/logging/meta_rl (3), strategy_pool (1), imports (1), observability (7), RAG (7), rate_limit (4), compromise (6), backtest_real (9) |

**Критический сбой:** `test_broker_overhead_acceptable` — падает при полном прогоне, но проходит изолированно. Причина: race condition / resource contention (возможно, httpx event loop после другого теста). Требуется investigation.

### 3.6 ADR (Architecture Decision Records)

`docs/adr/` и `docs/decisions/` — присутствуют. ADR-0010 (Legacy Test Exemptions) принят 2026-08-11. ✅

---

## 4. Производительность и Scalability

### 4.1 Узкие места

| Компонент | Риск | Причина |
|-----------|------|---------|
| `core/rag_client.py` (643 строк) | 🟡 | Синхронный FAISS поиск в асинхронном агенте |
| `data_room/resolvers/` | 🟡 | Нет circuit breaker для внешних API (добавлен только blueprint-level) |
| `meta_rl/live_data.py` (477 строк) | 🟡 | Потоковая обработка — потенциально memory-heavy |

### 4.2 База данных

- **PostgreSQL 15.18** + TimescaleDB 2.28.3 + pgvector 0.8.0 — production-ready. ✅
- **15 таблиц** включая hypertables, audit_log, karl_trajectories. ✅
- **WAL-G** бэкапы настроены. ✅
- **Redis** — заявлен в docker-compose, но не проверен в sandbox.

### 4.3 Docker / Контейнеризация

Docker недоступен в Zo sandbox (gVisor). Docker Compose-файл содержит 12 сервисов. Multi-stage Dockerfile (2.5K) для production. ✅

---

## 5. Зависимости и Инфраструктура

### 5.1 Python-зависимости

- `pyproject.toml` — единый источник зависимостей с `[dev]` и `[rag]` extras. ✅
- `uv.lock` — синхронизирован. ✅
- 8 internal-пакетов не найдены на PyPI (ожидаемо для монорепо).
- 3 уязвимости (см. §3.2).

### 5.2 CI/CD

| Workflow | Триггер | Статус |
|----------|---------|--------|
| `ci.yml` | PR/push | ✅ Lint + unit tests + arch linter |
| `quality-gate.yml` | PR | ✅ Quality gate (coverage, per-agent validation) |
| `security.yml` | PR/push + cron | ✅ Bandit + pip-audit + gitleaks |
| `release.yml` | workflow_dispatch | ✅ Build + sign + changelog |
| `deploy.yml` | workflow_dispatch | ✅ Multi-arch build + SBOM + cosign |
| `nightly.yml` | schedule | ✅ DORA + full test suite + dependabot |
| `load-test.yml` | workflow_dispatch | ✅ Locust staging soak |
| `auto-label.yml` | PR | ✅ Auto-label |
| `coderabbit-pr-review.yml` | PR | ✅ Code review |

4 устаревших workflow в `disabled-workflows/` — дубликаты, безопасны для удаления.

### 5.3 Pre-commit hooks

- Ruff (lint + format)
- Bandit (security)
- Architecture linter
- Validate agent
- Detect secrets

Все активны. ✅

### 5.4 K8s готовность

3 манифеста в `k8s/manifests/` (ray-serve, gpu-job, pvc). Деплой-конфиги в `deploy/k8s/` (deployment, hpa, ingress, service). Базовая готовность есть, но не production-grade (нет NetworkPolicy, PodDisruptionBudget, resource limits).

---

## 6. Лучшие Артефакты

### 6.1 Код-паттерны для переиспользования

| Артефакт | Путь | Почему лучший |
|----------|------|---------------|
| `@require_ephemeris` декоратор | `agents/_impl/ephemeris_decorator.py` (54 строки) | Чистый, переиспользуемый AOP-паттерн |
| `data_room/blueprint.py` | 175 строк | Единый gateway для внешних API с circuit breaker |
| `TradingSignal.from_agents()` | `agents/_impl/types.py` | Паттерн агрегации с весами |
| `BaseAgent` | `agents/base_agent.py` (5 строк) | Минималистичный абстрактный класс |
| `DecisionRecord` | `agents/_impl/amre/audit.py` | Полный audit trail с сериализацией |
| `KPIControlState` | `agents/_impl/amre/backtest_loop.py` | Adaptive control loop |
| `VolatilityRegime` | `core/volatility.py` | Динамический risk management |
| `AspectsEngine` | `core/aspects.py` | Конфигурируемый движок аспектов с orbs |
| `postgresql_manager.py` | `db/` | Dual-write (PG + SQLite fallback) |
| `middleware/__init__.py` | `web/middleware/` | Переиспользуемый `@require_auth` |

### 6.2 Documentation gems

| Документ | Путь | Ценность |
|----------|------|----------|
| AGENTS.md | root | Исчерпывающая карта проекта |
| SOUL.md | root | Философия и принципы (R-01…R-12) |
| ARCHITECTURE.md | root | Архитектурная документация |
| ADR-0010 | docs/adr/ | Legacy test exemptions policy |
| CODE_REVIEW.md | docs/ | CodeRabbit контракт |
| DEPLOYMENT.md | docs/ | Полный деплой-гайд |
| RUNBOOKS | docs/runbooks/ | Операционные инструкции |

---

## 7. Сводка всех находок

### Критические (P0)

| # | Находка | Действие |
|---|---------|----------|
| C1 | 53 пропущенных теста (KI-125a) | Sprint 5: batch-fix по 10/спринт |
| C2 | `core/` — God-module (66 файлов, 1.7MB) | Split на domain/infra в v1.1.0 |
| C3 | Flask/FastAPI дуализм | Миграция Flask→FastAPI в v1.1.0 |

### Высокие (P1)

| # | Находка | Действие |
|---|---------|----------|
| H1 | `deploy/iac/` — 168 файлов, отдельный продукт | Вынести в `infrastructure/` или отдельный репо |
| H2 | `gitagent_exporter.py` + `gitagent_registry.py` — 1,188 строк дубля | Слить в `integrations/gitagent/` |
| H3 | `test_broker_overhead_acceptable` — flaky test | Investigation: race condition / resource contention |
| H4 | AMRE в `agents/_impl/amre/` — нарушение иерархии | Перенести в `amre/` или `agents/amre/` |
| H5 | 3 уязвимости в зависимостях (chromadb, diskcache, ragas) | Обновить пакеты |

### Средние (P2)

| # | Находка | Действие |
|---|---------|----------|
| M1 | `synthesis_agent.py` (659 строк) — не разбит после Sprint B | Разбить callbacks на модули |
| M2 | `core/rag_client.py` (643 строк) — смесь RAG+FAISS+BM25 | Декомпозировать |
| M3 | B108 /tmp в sec_edgar | Использовать `XDG_CACHE_HOME` |
| M4 | 4 отключённых workflow — дубликаты | Удалить |
| M5 | K8s манифесты без NetworkPolicy/PodDisruptionBudget | Добавить для GA |

### Низкие (P3)

| # | Находка | Действие |
|---|---------|----------|
| L1 | 3 F401 (неиспользуемые импорты) | Auto-fix ruff |
| L2 | `council_orchestrator.py` — неиспользуемые os, TradingMode | Удалить |
| L3 | `karl_cli.py` — неиспользуемый rich.table.Table | Удалить |

---

## 8. План действий на Шаг 3

### Sprint 5 (текущий, до 2026-08-11)

1. **H5:** Обновить chromadb, diskcache, ragas
2. **M3:** Fix B108 (sec_edgar /tmp)
3. **M4:** Удалить 4 disabled workflow
4. **L1-L3:** Auto-fix ruff F401
5. **H3:** Investigation flaky test

### v1.1.0 (2026-08-11 — 2026-09-01)

1. **C1:** Batch-fix 10 KI-125a тестов
2. **H2:** Слить gitagent exporter + registry
3. **H4:** Перенести AMRE из `agents/_impl/amre/`
4. **M1:** Разбить synthesis_agent.py callbacks
5. **M2:** Декомпозировать core/rag_client.py

### v1.2.0 (после GA)

1. **C2:** Split core/ на domain/infra
2. **C3:** Flask→FastAPI миграция
3. **H1:** Вынести deploy/iac/ в отдельный репо
4. **M5:** K8s hardening (NetworkPolicy, PDB, resource limits)

---

*Отчёт создан 2026-07-27 в рамках Шага 2 аудита. Готов к ревью перед Шагом 3.*
