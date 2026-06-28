# PRODUCTION PLAN — astrofin-sentinel-platform

> **Источник данных**: CI logs PR #28 (`fix/architecture-linter-zero-fail` → `master`), PR #28 issue comments (CodeRabbit, AstroFin CI bot), прямой анализ структуры репо через GitHub API.
> **Дата составления**: 2026-06-28
> **Статус CodeRabbit**: запуск инициирован (`Run ID 83da7f6b-…`, режим ASSERTIVE, Pro), финального `review body` ещё нет — рекомендации CodeRabbit будут добавлены позже. План уже сейчас основан на 5 параллельных CI-источниках, чтобы не зависеть от CodeRabbit.
> **Цель**: привести репозиторий к состоянию, в котором все 5 CI jobs зелёные, secrets не утёкают, есть мониторинг и наблюдаемость, а зависимости обновлены.

---

## TL;DR — Дорожная карта

| Фаза | Название | Часы | Блокирует релиз? |
|------|----------|------|------------------|
| **P0** | Разблокировать CI (submodules, local action, pip-audit) | 4–6 | ✅ Да |
| **P1** | Привести код к lint-нулю (R1–R9, Ruff, mypy) | 6–10 | ✅ Да |
| **P2** | Тестовое покрытие (unit + integration + contract) | 12–16 | ✅ Да |
| **P3** | Безопасность (secrets, bandit, supply-chain, Dockerfile) | 6–8 | ✅ Да |
| **P4** | Наблюдаемость (structured logging, OTel, health/metrics) | 8–10 | ⚠️ Желательно |
| **P5** | CI/CD (артефакты, кэши, деплой, зависимости между jobs) | 6–8 | ⚠️ Желательно |
| **P6** | Документация (README, ADR, OpenAPI, диаграммы) | 4–6 | ❌ Улучшение |
| **P7** | Код-стайл, рефакторинг, техдолг | 8–12 | ❌ Улучшение |
| **P8** | Производительность и масштабируемость | 8–12 | ❌ Улучшение |
| **Итого** | | **62–88 ч** | |

**Реалистичная оценка до релиза (MVP prod-ready)**: фазы **P0–P3** ≈ 28–40 часов. Остальное — полировка.

---

## P0 — Разблокировать CI ⚠️ HIGH (4–6 ч)

**Почему сейчас**: CI зелёный только у `CodeRabbit PR Review` и `pip-audit (strict)`. Всё остальное красное. Прод-релиз невозможен, пока CI не зелёный — это первый gate.

### P0.1 Submodules не клонируются — все 5 из 6 возвращают 404
- **Симптом** (`CI - Security and Quality`, `run 28312839545`):
  ```
  fatal: clone of 'https://github.com/mahaasur13-sys/AsurDev.git/' into submodule path ... failed
  remote: Repository not found.
  ```
  Затронуты: `AsurDev`, `atom-federation-os`, `home-cluster-iac`, `integrations/gitagent`, `roma-execution-bridge`. Клонируется только `astrofin-sentinel-v5`.
- **Гипотеза**: репозитории приватные / удалённые / переименованы.
- **Действия**:
  1. Выяснить реальный URL каждого сабмодуля (`gh repo list mahaasur13-sys --visibility all` или прямые запросы `gh api repos/<owner>/<name>`).
  2. Обновить `.gitmodules` (или удалить мёртвые сабмодули через `git rm --cached <path>`).
  3. В `.github/workflows/*.yml` заменить `https://` на `git@github.com:` + добавить `actions/checkout` с `submodules: recursive` и `token: ${{ secrets.GH_PAT }}`.
  4. Прогнать `git submodule update --init --recursive` локально, чтобы убедиться.
- **Приоритет**: высокий — блокирует все jobs, использующие код сабмодулей.
- **Время**: 1–2 ч.

### P0.2 `python-setup.yml` используется как local action — это сломано
- **Симптом** (`CI - Security and Quality`, `run 28312839545`):
  ```
  Can't find 'action.yml', 'action.yaml' or 'Dockerfile' under
  '/home/runner/work/.../astrofin-sentinel-platform/.github/workflows/python-setup.yml'.
  ```
  Затронуты jobs: **Security (Bandit + Docker)**, **Code Quality (Ruff + mypy)**, **Tests + Coverage** — все три полностью не работают.
- **Действия**:
  1. В `ci.security.yml` и `ci.yml` заменить `uses: ./.github/workflows/python-setup.yml` на корректную композицию шагов (или на `uses: actions/setup-python@v5` + bash-скрипты).
  2. Альтернатива: вынести общие шаги в `actions/setup-astrofin-python` composite action (создать `.github/actions/setup-astrofin-python/action.yml`).
- **Приоритет**: высокий.
- **Время**: 1–2 ч.

### P0.3 `pip-audit` падает из-за несовместимости флагов
- **Симптом** (`CI - Security and Quality`):
  ```
  ERROR:pip_audit._cli:the --disable-pip flag can only be used with a hashed requirements files
  or if the --no-deps flag has been provided
  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  ```
- **Действия**:
  1. В `ci.security.yml` заменить `pip-audit -r requirements.txt -f json --disable-pip` на `pip-audit -r requirements.txt --no-deps -f json` (или убрать `--disable-pip` совсем, если используется хэшированный `requirements.txt`).
  2. Добавить `--strict` только когда JSON отчёт непустой (не валить job на каждом CI).
- **Приоритет**: высокий.
- **Время**: 30 мин.

### P0.4 `compose-check` — статическая валидация `docker-compose.yml`
- **Симптом** (`Compose static check`, `run 28312839550`, conclusion=failure).
- **Действия**:
  1. Посмотреть конкретный лог `audit_reports/PR-28/compose-check.log`, найти первопричину.
  2. Исправить `docker-compose.yml` (скорее всего: несовместимая версия схемы, несуществующий `image`, неверный `volumes`-путь).
- **Приоритет**: высокий.
- **Время**: 30 мин – 1 ч.

### P0.5 `Quality Gate` — линт «изменённых» файлов выявляет ошибки и в не-изменённых
- **Симптом** (`Quality Gate`, `run 28312839559`): падает на **десятках** файлов, которые PR #28 не трогал (см. P1).
- **Действие**: фиксится вместе с P1.
- **Приоритет**: высокий.
- **Время**: см. P1.

---

## P1 — Линт-ноль (R1–R9, Ruff, mypy) ⚠️ HIGH (6–10 ч)

### P1.1 Architecture Lint (R1–R9) — 27 hard-rule violations

**Файлы с нарушением правила "FunctionDef/ClassDef без docstring"**:

| Файл | Строки | Кол-во |
|------|--------|--------|
| `scripts/architecture_linter.py` | 83, 87, 91, 488, 496 | 5 |
| `scripts/optimize_lag_blend.py` | 58, 406, 464 | 3 |
| `scripts/ralph_agent.py` | 20, 25, 30, 84 | 4 |
| `tools/nightly_export.py` | 47, 54 | 2 |
| `tools/thompson_cli.py` | 56, 81, 93, 141, 151, 201, 278 | 7 |
| `tools/healthcheck.py` | 76, 87 | 2 |
| `tools/metrics_server.py` | 33, 42, 46 | 3 |
| `tools/db_monitor.py` | 19, 81 | 2 |
| **Итого** | | **27** |

- **Действия**:
  1. Либо добавить docstring в каждый из этих def/class.
  2. Либо (если это legacy/CLI) — добавить в `architecture_linter.py` allow-list `# noqa: R-DOCSTRING` для файлов из `tools/`.
- **Приоритет**: высокий (блокирует CI).
- **Время**: 2–3 ч (1 час правок + 1 час ревью).

### P1.2 Ruff — ошибки в изменённых и не-изменённых файлах

| Категория | Файл | Строки | Ошибка | Что делать |
|-----------|------|--------|--------|------------|
| F401 unused import | `agents/_impl/macro_agent.py` | 15 | `numpy` | удалить импорт |
| F401 | `agents/_impl/synthesis_agent.py` | 16 | `require_ephemeris` | удалить |
| F841 unused var | `agents/_impl/synthesis_agent.py` | 298 | `amre_fallback` | удалить или использовать |
| F401 | `agents/astro_council_agent.py` | 21 | `SignalDirection` | удалить |
| F403 star-import | `agents/base_agent.py` | 4 | `from core.base_agent import *` | заменить на явные импорты |
| E401 multi-import | `agents/gitagent_exporter.py` | 223 | Multiple imports on one line | разнести по строкам |
| E402 late import | `agents/karl_synthesis.py` | 14, 15, 16, 17, 19, 41, 45, 46, 64, 65, 66 | module-level not at top | рефакторить или `# noqa: E402` |
| F401 | `agents/metrics.py` | 54 | `typing.Any` | удалить |
| E501 too long | `agents/_impl/market_analyst.py` | 114 | 124 > 120 | разбить |
| E501 | `core/astro_rl_engine.py` | 31 | 143 > 120 | разбить |
| F811 redef | `core/houses.py` | 315 | `normalize_degrees` | удалить второе определение |
| E501 | `core/kepler.py` | 318 | 127 > 120 | разбить |
| E741 ambig var | `core/safe_json.py` | 74 | `l` | переименовать |
| E402 | `core/thompson.py` | 16 | late import | вынести в шапку или `# noqa` |
| E731 lambda assign | `scripts/architecture_linter.py` | 54–59 | `GREEN/RED/YELLOW/CYAN/BOLD/DIM` | заменить на `def` |
| E731 | `scripts/validate_agent.py` | 47–52 | то же | заменить на `def` |

- **Действия**: внести правки точечно (`# noqa: …` где это legacy, либо рефакторинг). Запустить `ruff check .` локально до зелёного.
- **Приоритет**: высокий.
- **Время**: 2–4 ч.

### P1.3 mypy
- **Симптом**: `python-setup.yml` падает — mypy не выполняется (см. P0.2). После фикса P0.2 нужно прогнать mypy отдельно.
- **Действия**:
  1. Запустить `mypy --strict agents/ core/` локально.
  2. Добавить `mypy.ini`/`pyproject.toml [tool.mypy]` с `ignore_missing_imports = True` для сабмодулей.
  3. Включить в CI.
- **Приоритет**: средний (после разблокировки CI).
- **Время**: 2–3 ч.

---

## P2 — Тестовое покрытие ⚠️ HIGH (12–16 ч)

### P2.1 Что уже сделано в PR #28
- Добавлено 18 unit-тестов по агентам (`test_bear_researcher`, `test_bradley_agent`, `test_bull_researcher`, `test_compromise_agent`, `test_cycle_agent`, `test_electoral_agent`, `test_elliot_agent`, `test_ephemeris_decorator`, `test_fundamental_agent`, `test_gann_agent`, `test_insider_agent`, `test_macro_agent`, `test_market_analyst`, `test_ml_predictor_agent`, `test_options_flow_agent`, `test_quant_agent`, `test_risk_agent`, `test_sentiment_agent`, `test_synthesis_agent`, `test_technical_agent`, `test_time_window_agent`).
- Добавлен общий `tests/agent_test_base.py`.

### P2.2 Что отсутствует

| Тип | Примеры | Приоритет | Время |
|-----|---------|-----------|-------|
| **Unit-тесты CLI tools** | `tools/nightly_export.py`, `tools/thompson_cli.py`, `tools/healthcheck.py`, `tools/db_monitor.py`, `tools/metrics_server.py` | средний | 3 ч |
| **Integration-тесты** | оркестратор `sentinel_v5` с реальными данными, end-to-end web → API → DB | высокий | 4 ч |
| **Contract-тесты** | для API endpoints (FastAPI / web/app.py) — snapshot OpenAPI | средний | 2 ч |
| **Property-based tests** | `core/kepler.py`, `core/houses.py`, `core/safe_json.py` (math correctness) | низкий | 2 ч |
| **Chaos/failure tests** | timeouts, retry, circuit breaker — для `roma-execution-bridge` | низкий | 2 ч |
| **Coverage target** | ≥ 70% для `agents/`, `core/`, ≥ 50% для всего остального | средний | 2 ч настройка + 1 ч мониторинг |

### P2.3 Фикстуры и моки
- Текущие `tests/test_*_agent.py` используют `agent_test_base.py`. Нужно убедиться, что:
  - моки для внешних API (Yahoo Finance, OpenAI, Swiss Ephemeris) не превращаются в скрытые регрессии,
  - фикстуры для БД используют ephemeral (SQLite in-memory или testcontainers PostgreSQL),
  - есть snapshot-тесты на output агентов с `--snapshot-update` для разовых обновлений.

---

## P3 — Безопасность ⚠️ HIGH (6–8 ч)

### P3.1 Секреты и конфигурация
- Проверить `.secrets.baseline` (detekt-secrets) и `git secrets --scan-history` на всю историю.
- `.env.example` и `.env.db.example` — не содержат ли реальных значений (по diff с предыдущей версией).
- Проверить, что в `astrofin-sentinel-v5`/сабмодулях нет захардкоженных API-ключей.
- **Приоритет**: высокий. **Время**: 2 ч.

### P3.2 Bandit + Dockerfile
- В CI Bandit не выполняется (см. P0.2) — после разблокировки прогнать `bandit -r agents/ core/ scripts/ tools/ -ll` отдельно.
- **Dockerfile** — проверить:
  - `USER` (не root),
  - pinned versions (`pip install --no-cache-dir --require-hashes`),
  - `--read-only` root filesystem,
  - multi-stage build.
- **Приоритет**: высокий. **Время**: 2 ч.

### P3.3 Зависимости (supply-chain)
- `pip-audit strict` — заменить на правильный вызов (P0.3).
- Добавить `safety check` или `osv-scanner` для второго мнения.
- Включить Dependabot/Renovate для `requirements*.txt`, `Dockerfile`, `home-cluster-iac/`.
- **Приоритет**: средний. **Время**: 1–2 ч.

### P3.4 Workflow permissions
- Все `*.yml` — заменить `permissions: write-all` (если есть) на минимально нужные:
  ```yaml
  permissions:
    contents: read
    pull-requests: read
  ```
- Проверить, что `GH_PAT` (если создаётся) — fine-grained, read-only где возможно.
- **Приоритет**: высокий. **Время**: 1 ч.

### P3.5 Аутентификация
- В `web/app.py` (FastAPI) — проверить auth middleware (есть ли rate-limit, JWT validation, RBAC).
- API endpoints — все должны иметь `Authorization` gate (см. `web/app.py` routes).
- **Приоритет**: высокий. **Время**: 1–2 ч.

---

## P4 — Наблюдаемость 📊 MEDIUM (8–10 ч)

### P4.1 Structured logging
- Текущий логгер: проверить, что используется `structlog` или stdlib `logging` с JSON formatter.
- Все агенты должны логировать `event`, `agent`, `signal`, `confidence`, `latency_ms`.
- **Приоритет**: средний. **Время**: 3 ч.

### P4.2 OpenTelemetry traces
- `core/tracing.py` — проверить инициализацию (OTLP endpoint через env).
- Инструментировать key paths: `orchestration/sentinel_v5.py`, `web/app.py`, `roma-execution-bridge`.
- **Приоритет**: средний. **Время**: 3 ч.

### P4.3 Health / Metrics endpoints
- `health_endpoints.py` (FastAPI) — есть. Проверить `/healthz`, `/readyz`, `/metrics`.
- `/metrics` — Prometheus exposition format (`prometheus_client`).
- Добавить SLO-метрики: latency p50/p95/p99, error rate, queue depth.
- **Приоритет**: средний. **Время**: 2–3 ч.

### P4.4 Алерты
- В `deploy/monitoring/` — настроены `alertmanager.yml`, `blackbox.yml` (видим в git status ранее).
- Проверить, что есть правила на:
  - 5xx error rate > 1% за 5 мин,
  - p95 latency > 1s,
  - DB connection pool exhaustion,
  - Disk usage > 80%.
- **Приоритет**: средний. **Время**: 2 ч.

---

## P5 — CI/CD ⚙️ MEDIUM (6–8 ч)

### P5.1 Кэширование и артефакты
- `actions/setup-python@v5` + `cache: 'pip'` уже есть — ок.
- Добавить `actions/cache` для `.pytest_cache`, `.ruff_cache`, `.mypy_cache`.
- Артефакты: coverage report (`htmlcov/`) выгружать на каждый PR.
- **Приоритет**: средний. **Время**: 1–2 ч.

### P5.2 Параллелизация jobs
- Сейчас 5 jobs на PR — нормально. Добавить **матрицу** для тестов по Python 3.11/3.12.
- **Приоритет**: низкий. **Время**: 1 ч.

### P5.3 Deploy workflow (`deploy.yml`)
- Проверить: есть ли staging environment перед prod?
- Добавить manual approval gate (`environment: production`).
- Добавить `concurrency: production` для защиты от race.
- **Приоритет**: высокий (для prod). **Время**: 2 ч.

### P5.4 Load test workflow (`load-test.yml`)
- Проверить, что он не запускается на каждый PR — вынести в отдельный workflow_dispatch.
- **Приоритет**: средний. **Время**: 1 ч.

### P5.5 SBOM и подписи
- Уже был `fix(workflow): remove duplicate SBOM upload` (коммит `b3eabb2`). Хорошо.
- Добавить `cosign sign` артефактов Docker images.
- **Приоритет**: средний. **Время**: 2 ч.

---

## P6 — Документация 📚 LOW (4–6 ч)

### P6.1 README.md
- Сейчас README есть. Проверить секции: Quickstart, Architecture, Contributing, License.
- Добавить **архитектурную диаграмму** (D2 / Mermaid) — что в monorepo, как связаны сабмодули.
- **Время**: 1–2 ч.

### P6.2 ADR (Architecture Decision Records)
- Создать `docs/adr/` с шаблоном `0000-template.md`.
- Задокументировать ключевые решения:
  - ADR-001: почему monorepo + сабмодули,
  - ADR-002: стратегия multi-agent (meta-RL + orchestrator),
  - ADR-003: почему `astrofin-sentinel-v5` как отдельный submodule.
- **Время**: 2–3 ч.

### P6.3 API reference
- Для `web/app.py` — авто-генерация OpenAPI (FastAPI делает это из коробки).
- Экспорт в `docs/api/openapi.json` + статический `redoc` page.
- **Время**: 1 ч.

### P6.4 PRODUCTION_RESTORE.md / PRODUCTION_PLAN.md (этот файл)
- Документировать runbook для восстановления прод-сервиса.
- **Время**: 1 ч.

---

## P7 — Код-стайл и поддерживаемость 🧹 LOW (8–12 ч)

### P7.1 Техдолг
Известные «грязные» места из CI логов:
- `agents/karl_synthesis.py` — late imports, 10 штук → вынести в шапку или пересмотреть зависимость.
- `agents/base_agent.py:4` — `from core.base_agent import *` — заменить на явные импорты.
- `scripts/*.py` — повторяющиеся lambda для цветов (`E731`) — вынести в общий `core/console.py`.

### P7.2 Pre-commit hooks
- `.pre-commit-config.yaml` уже есть (видим в `git ls-files`).
- Добавить: `ruff`, `ruff-format`, `mypy`, `bandit`, `detect-secrets`.
- Включить в CI как `pre-commit run --all-files`.

### P7.3 Type hints
- Текущий код местами типизирован (`tests/test_types.py` есть). Проверить покрытие `mypy --strict` для `core/`.

### P7.4 Dead code / unused modules
- `python -m pyflakes` или `vulture .` — найти мёртвый код.
- Особенно в `tools/`, `_pr_logs/`, `_sbs_old/`.

---

## P8 — Производительность и масштабируемость ⚡ LOW (8–12 ч)

### P8.1 Profiling
- Снять cProfile / py-spy с `run_sentinel_v5.py` на 100 итераций.
- Выявить bottlenecks (Swiss Ephemeris calls? FAISS index?).

### P8.2 Concurrency
- Текущий `orchestration/sentinel_v5.py` — проверить, реально ли он async, или asyncio-обёртка над sync-кодом.
- При необходимости перевести CPU-heavy блоки (`core/kepler.py`) на `ProcessPoolExecutor`.

### P8.3 Caching
- Результаты эфемерид (`pyswisseph`) кэшировать в Redis/файлах.
- FAISS index — пересобирать только при обновлении эмбеддингов.

### P8.4 Database
- Индексы в миграциях `migrations/`.
- Connection pooling (`psycopg_pool` / `asyncpg.create_pool`).

### P8.5 Load test
- Использовать `load-test.yml` workflow (есть) для smoke-теста 100 RPS на staging.

---

## Критерии приёмки (Definition of Done для prod)

- [ ] Все 5 CI jobs зелёные на `master`.
- [ ] Submodules все клонируются в CI (или удалены/помечены как `optional`).
- [ ] `pip-audit` без известных уязвимостей в `requirements*.txt`.
- [ ] `bandit -ll` без HIGH issues.
- [ ] Покрытие тестами ≥ 70% для `agents/` и `core/`.
- [ ] `/healthz`, `/readyz`, `/metrics` работают в staging.
- [ ] SLO-алерты настроены в `alertmanager.yml`.
- [ ] `deploy.yml` имеет manual approval для `production`.
- [ ] `README.md` + `docs/adr/` + `PRODUCTION_RESTORE.md` актуальны.
- [ ] CodeRabbit финальное ревью PR #28 — либо `approved`, либо все замечания закрыты.

---

## Приложение A — CodeRabbit финальное ревью (заполняется)

> Будет добавлено, когда CodeRabbit завершит `Run ID 83da7f6b-…` и опубликует `review body` + inline comments.

Получено на 2026-06-28 05:48 UTC: CodeRabbit в режиме "in progress" (Pro, ASSERTIVE), обрабатывает 27 файлов. После выхода — дополнить план.

## Приложение B — Источники данных

- Логи CI runs сохранены в `audit_reports/PR-28/`:
  - `ci.log` (run 28312839546) — Architecture Lint 27 violations
  - `quality-gate.log` (run 28312839559) — Ruff ошибки
  - `compose-check.log` (run 28312839550) — compose static check
  - `security-quality.log` (run 28312839545) — submodules 404, pip-audit, local action
  - `coderabbit-comments.json` — все комментарии PR #28
- PR #28: https://github.com/mahaasur13-sys/astrofin-sentinel-platform/pull/28
- PR description: см. комментарий `gh pr view 28 --comments`