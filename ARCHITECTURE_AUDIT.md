# Architecture Audit — master @ 900ebdd

**Дата:** 2026-07-13
**HEAD:** `900ebdd` (PR #206 merged, coverage threshold 10%)
**Скоуп:** аудит архитектуры и границ модулей текущего состояния `master`.

## 1. Структура верхнего уровня

Корень репозитория — монолитный Python-проект с выраженными доменными слоями. Соседство legacy- и продуктовых каталогов (см. п. 4).

| Слой / домен | Каталог | Назначение |
| --- | --- | --- |
| Агенты | `agents/`, `agents/_impl/` | Базовые классы и активные агенты (AstroCouncil, Electoral, Synthesis). |
| Оркестрация | `orchestration/`, `mas_factory/` | Графы и фабрики multi-agent систем. |
| Meta-RL | `meta_rl/` | Meta-обучение с подкреплением, A/B testing, persistence. |
| Core | `core/` | Базовые абстракции (tracing, logging, доменные сервисы). |
| Trading | `trading/`, `strategies/`, `backtest/`, `execution/` | Торговые пайплайны, стратегии, бэктесты. |
| Web | `web/` | FastAPI/Dash-дашборд. |
| Knowledge / RAG | `knowledge/`, `Knowledge/`, `data_room/` | RAG-retriever, data room. |
| Observability | `observability/`, `monitoring/`, `health_endpoints.py` | Метрики, health-checks, health-endpoints. |
| ML | `ml_engine/`, `models/`, `training/`, `gpu_worker/` | ML-pipeline. |
| Contracts | `acos-contracts/`, `atom-core/` | Контракты и shared core ATOM. |
| Инфра | `deploy/`, `docker-compose*.yml`, `Dockerfile`, `Makefile` | Развертывание. |
| Тесты | `tests/`, `bench/` | Unit/integration/benchmarks. |
| Решения | `docs/decisions/` | ADRs (ADD-YYYY-MM-DD-*.md). |

## 2. Границы модулей и coupling/cohesion

**Сильные стороны:**
- Чёткое разделение `agents/_impl/` (активные) vs `_archived/` (legacy) — enforced через `AGENTS.md` rule #2.
- `core/` изолирует базовые сервисы (tracing, logging) — остальные слои зависят от него, а не наоборот.
- `meta_rl/persistence.py` отделён от `meta_rl/meta_agent.py` — data-access отдельно от логики.
- `trading/execution/` (TWAP и пр.) живёт отдельно от `trading/strategies/` — исполнение ≠ стратегия.
- `acos-contracts/` и `atom-core/` — явные shared-kernel для cross-component контрактов.

**Слабые места / риски:**
- В корне — большое количество «верхнеуровневых» файлов, не привязанных к слоям: `muhurtha.py`, `data_provider.py`, `langgraph_schema.py`, `test_aspects.py`, `FINAL_INTEGRATION_TEST.py`. Снижают cohesion корня, требуют placement-политики.
- Каталог `src/` присутствует наряду с пакетной раскладкой (модули на верхнем уровне). Возможны два параллельных layout-а.
- `knowledge/` (lowercase) и `Knowledge/` (capitalized) — два каталога в одной кодовой базе: либо legacy, либо разделение зон ответственности, но сейчас это выглядит как naming drift.
- `Projects/`, `Documents/`, `Downloads/` в корне репозитория — это **артефакты окружения**, не код; должны быть в `.gitignore`.
- `nano/`, `ralph_audit.log`, `ci-cleanup.patch`, `artifacts/`, `graphify-out/` — смесь временных/archived артефактов и потенциально активного кода. Нужна явная политика retention.

## 3. Соответствие подходам

| Подход | Соблюдение | Комментарий |
| --- | --- | --- |
| Clean Architecture | ⚠️ частично | `core/` + `agents/_impl/` дают чистое ядро, но `web/` напрямую импортирует `trading/`, `meta_rl/`, минуя application-слой. |
| DDD | ⚠️ частично | Домены выделены (trading, meta_rl, agents, observability), но bounded contexts не зафиксированы явно (нет `domain/` namespace, нет общих value objects вне `core/`). |
| Feature-Sliced Design | ❌ нет | Раскладка по слоям, а не по фичам. Для multi-agent платформы это допустимо, но требует явной feature-folder policy. |

## 4. Технический долг верхнего уровня (по слоям)

- **`orchestration/`**: требует аудита графа фаз (ранее фиксировались проблемы с `phase2/plan_graph.py`).
- **`meta_rl/`**: persistence-слой и ab_testing — точки роста, требуют покрытия тестами.
- **`web/`**: middleware/ и components/ разрослись; проверить циклы импорта.
- **`tests/`**: coverage-gate теперь 10% (см. PR #206). Довести до целевого 40%+ по приоритетам из `MOSCOW_PRIORITIZATION.md`.
- **Корень**: провести `gitignore` hygiene для `Projects/`, `Documents/`, `Downloads/`, `artifacts/`, `graphify-out/`, `nano/`, `*.patch`.

## 5. Рекомендации (приоритизировано)

| # | Действие | Приоритет | Ссылка |
| --- | --- | --- | --- |
| 1 | Расчистить корень: вынести legacy-скрипты в `scripts/` или удалить, добавить правила `.gitignore`. | MUST | `MOSCOW_PRIORITIZATION` |
| 2 | Унифицировать `knowledge/` vs `Knowledge/` — выбрать один стиль, второй перенести или удалить. | SHOULD | Phase B2d |
| 3 | Провести аудит циклов импорта в `web/` → `trading/`, `meta_rl/`. | SHOULD | `SPRINT_2` |
| 4 | Ввести явный `domain/` namespace (DDD) при следующем major-рефакторе. | COULD | Backlog |
| 5 | Покрыть `meta_rl/persistence.py` и `ab_testing.py` тестами до повышения coverage-gate. | MUST | Sprint 1 |
| 6 | Документировать архитектурные границы (mermaid/plantuml) в `docs/architecture/`. | COULD | Backlog |

## 6. Сводка

- **Архитектурный базис** — рабочий, слои разделены, есть явные ADRs.
- **Главные риски** — разрастание корня, дубли naming (`knowledge/`/`Knowledge/`), отсутствие явных bounded contexts, остаточный технический долг по тестам.
- **Следующая фаза** — Phase B2d (см. `STATUS.md`).
