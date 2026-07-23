# AstroFin Sentinel V5 — Architecture Refactor Brief

> **Status:** Draft · 2026-06-20
> **Source:** Graphify audit (`graphify-out/GRAPH_REPORT.md`, 2026-06-17)
> **Owner:** Architecture / Lead
> **Scope:** `AstroFinSentinelV5/` + cross-repo contracts (AsurDev, home-cluster-iac, roma-execution-bridge)

---

## 1. Context

Архитектурный аудит проекта AstroFin Sentinel V5 проведён инструментом Graphify.
Получен граф зависимостей: **38 682 узла, 62 196 рёбер, 2 702 сообщества**.

### 1.1 Выявленные проблемы

| # | Проблема | Данные Graphify |
|---|---|---|
| 1 | **God Nodes** — чрезмерная связанность | `AgentResponse` (348), `SignalDirection` (321), `BaseAgent` (254), `EphemerisUnavailableError` (210), `RiskEngineV2` (151), `DeterministicClock` (134) |
| 2 | **Кросс-репозиторные зависимости** | `AsurDev` → `home-cluster-iac` (`WindowEngine`), `AsurDev` → `roma-execution-bridge` (`StateStore`) и др. (INFERRED) |
| 3 | **Однофайловые циклы импорта** | 20+ файлов: `schema.py`, `backfill.py`, `exporter.py`, `window_engine.py`, `load_test/.../generator.py`, `ml_engine/dataset/builder.py`, `agents/_impl/technical_agent.py`, `agents/astro_council_agent.py`, `astrofin-sentinel-v5/agents/_impl/technical_agent.py`, `astrofin-sentinel-v5/agents/astro_council_agent.py`, `astrofin-sentinel-v5/astrology/vedic.py`, `astrofin-sentinel-v5/backtest/engine.py`, `astrofin-sentinel-v5/core/ephemeris.py`, `astrofin-sentinel-v5/core/houses.py`, `astrofin-sentinel-v5/core/online_trainer.py`, `astrofin-sentinel-v5/core/panchanga.py`, `astrofin-sentinel-v5/integrations/__init__.py`, `astrofin-sentinel-v5/mas_factory/visualizer.py`, `astrofin-sentinel-v5/meta_rl/calibration.py`, `astrofin-sentinel-v5/muhurtha.py` |
| 4 | **Низкая когезия сообществ** | Top-50: cohesion < 0.05 (например, Community 0: 0.01, Community 1: 0.01) |
| 5 | **Фрагментация** | 2 702 сообщества (2 285 показаны) — отсутствие чётких доменных границ |
| 6 | **Смешение слоёв** | Агенты ↔ риск ↔ исполнение ↔ инфраструктура переплетены |

### 1.2 Зачем

Довести систему до production-уровня: уменьшить связанность, устранить циклы, разделить домены, повысить детерминизм и воспроизводимость.

---

## 2. Goal (SMART)

| Критерий | Целевое значение | Проверка |
|---|---|---|
| Связанность God Nodes | **−30…40 %** | перезапуск Graphify, отчёт `graphify-out/GRAPH_REPORT.md` |
| Циклы импорта | **0** (1-file и multi-file) | Graphify + `import-linter` |
| Домены | **≤ 50 сообществ**, средняя cohesion **≥ 0.30** | Graphify |
| Cross-repo INFERRED | **0** | Graphify |
| Тесты | **100 % pass**, coverage ≥ **80 %** | pytest + coverage |
| Детерминизм | одинаковый вход → одинаковый выход | replay-тесты |
| Документация | ≥ **5 ADR** в `docs/adr/` | ревью |

---

## 3. Technical Requirements

### 3.1 P0 — Устранение однофайловых циклов

**Задача:** разбить каждый «циклящий» файл на модули: интерфейс / реализация / утилиты.

**Файлы под разбор (по отчёту Graphify):**
- `AsurDev/acos/storage/schema.py`
- `AsurDev/feature_pipeline/backfill.py`
- `AsurDev/feature_pipeline/exporter.py`
- `AsurDev/feature_pipeline/window_engine.py`
- `AsurDev/load_test/workload/generator.py`
- `AsurDev/ml_engine/dataset/builder.py`
- `agents/_impl/technical_agent.py`
- `agents/astro_council_agent.py`
- `astrofin-sentinel-v5/agents/_impl/technical_agent.py`
- `astrofin-sentinel-v5/agents/astro_council_agent.py`
- `astrofin-sentinel-v5/astrology/vedic.py`
- `astrofin-sentinel-v5/backtest/engine.py`
- `astrofin-sentinel-v5/core/ephemeris.py`
- `astrofin-sentinel-v5/core/houses.py`
- `astrofin-sentinel-v5/core/online_trainer.py`
- `astrofin-sentinel-v5/core/panchanga.py`
- `astrofin-sentinel-v5/integrations/__init__.py`
- `astrofin-sentinel-v5/mas_factory/visualizer.py`
- `astrofin-sentinel-v5/meta_rl/calibration.py`
- `astrofin-sentinel-v5/muhurtha.py`

**Acceptance:**
- Graphify: 0 single-file cycles.
- `python -c "import <module>"` — без ошибок.
- Существующие тесты проходят без изменения функциональности (могут потребоваться обновления путей импорта).

### 3.2 P0 — Абстракции для God Nodes

**Действия:**
1. Создать `AstroFinSentinelV5/common/interfaces.py` с `typing.Protocol`:
   - `AgentResponseProtocol` — поля и методы `AgentResponse`.
   - `SignalDirectionProtocol` — направления и их свойства.
   - `BaseAgentProtocol` — `analyze()`, `run()`, …
2. Перевести все агенты на протоколы (DI через конструктор).
3. Заменить статические ссылки на динамические (factory / registry).

**Acceptance:**
- Степень центральности `AgentResponse`, `SignalDirection`, `BaseAgent` **−30…40 %** в новом отчёте Graphify.
- Подмена реализации агента без правки остального кода (smoke-тест).

### 3.3 P1 — `common-contracts` пакет

**Задача:** выделить общие интерфейсы и типы в отдельный пакет (репозиторий или подпакет), чтобы устранить прямые зависимости `AsurDev` ↔ `home-cluster-iac` ↔ `roma-execution-bridge`.

**Содержимое `common-contracts`:**
- `events/types.py` — `EventType`, …
- `contracts/trace_contract.py` — `TraceContract`, `ExecutionResult`
- `durability/state_store.py` — `StateStore` (интерфейс)

**Acceptance:**
- Graphify: 0 INFERRED-связей между разными репозиториями.
- Каждый репозиторий собирается и тестируется независимо.

### 3.4 P1 — Доменная реорганизация

| Домен | Содержание | Примеры модулей |
|---|---|---|
| `trading_agents` | Торговые агенты (technical, fundamental, astro, synthesis) | `agents/`, `astrofin-sentinel-v5/agents/` |
| `risk_management` | Риск, позиционирование, лимиты | `RiskEngineV2`, `RiskConfigV2`, `mode.py`, `risk_v2.py` |
| `execution` | Ордера, брокеры, шлюзы | `ExecutionGateway`, `broker/`, `execution/` |
| `data_storage` | Хранилища, репозитории, event log | `StateStore`, `EventStore`, `repository/` |
| `core_determinism` | Время, UUID, replay | `DeterministicClock`, `DeterministicUUIDFactory`, `replay/` |
| `astrology` | Эфемериды, дома, муртхи | `ephemeris.py`, `houses.py`, `muhurtha.py` |
| `observability` | Логи, метрики, трассировка | `metrics.py`, `tracing.py`, `logging/` |

**Действия:**
1. Создать физические пакеты.
2. Перенести файлы с сохранением git-истории (`git mv`).
3. Обновить импорты (через `ruff --fix` / `pyupgrade` + ручной контроль).
4. Зависимости между доменами — только через интерфейсы.

**Acceptance:**
- Количество сообществ **≤ 50**.
- Средняя cohesion **≥ 0.30**.

### 3.5 P1 — Архитектурный линтер в CI

- Инструмент: `import-linter` (Python) или `pydeps`.
- Правила:
  - `infrastructure` не импортирует `domain`.
  - `domain` не импортирует `infrastructure` напрямую (только через интерфейсы).
  - Запрет циклов между доменами.
- Файл `.importlinter` в корне репозитория.

**Acceptance:**
- CI падает при нарушении.
- `.importlinter` задокументирован в `README.md`.

### 3.6 P2 — Детерминизм

**Аудит:** `random.*`, `uuid.uuid4()`, `datetime.now()`, `time.time()`.

**Замена:** `DeterministicRNG`, `DeterministicUUIDFactory`, `DeterministicClock`.

**CLI-флаг:** `--deterministic` для режима воспроизведения (фиксирует seed).

**Acceptance:**
- Replay-тесты: один вход → один выход (бит-в-бит).

### 3.7 P2 — ADR

Формат ADR (Michael Nygard):
- **Status:** proposed / accepted / deprecated / superseded
- **Context**
- **Decision**
- **Consequences**

**Acceptance:** ≥ 5 ADR в `docs/adr/`, минимум:
1. ADR-001: Domain reorganization
2. ADR-002: Protocol-based agent abstraction
3. ADR-003: common-contracts package
4. ADR-004: import-linter as CI gate
5. ADR-005: Determinism-first architecture

---

## 4. Implementation Plan (по спринтам)

| Sprint | Длительность | Задачи | Exit Criteria |
|---|---|---|---|
| **S1** | 1 неделя | (3.1) Устранение 1-file cycles. (3.2) Протоколы для God Nodes. | 0 циклов; центральность −20 % |
| **S2** | 1 неделя | (3.3) `common-contracts` пакет. (3.3) Рефакторинг межрепозиторных импортов. | 0 INFERRED cross-repo |
| **S3** | 2 недели | (3.4) Доменная реорганизация. (3.5) Начальная настройка `import-linter`. | Сообщества ≤ 50; cohesion ≥ 0.30 |
| **S4** | 1 неделя | (3.5) import-linter в CI. (3.7) 5 ADR. | CI блокирует нарушения; ADR оформлены |
| **S5** | 1 неделя | (3.6) Determinism audit. Replay-тесты. | Все replay-сценарии pass |

---

## 5. General Acceptance Criteria

1. **Graphify отчёт** в репозитории фиксируется после каждого спринта:
   - 0 циклов
   - God Nodes centrality снижена
   - Cohesion ≥ 0.30
   - 0 INFERRED cross-repo
2. **Тесты:** unit + integration + replay, coverage ≥ 80 %.
3. **CI:** lint + mypy + import-linter + pytest + coverage.
4. **Production-deploy:** smoke-test + нагрузочный тест ≥ N RPS.
5. **Документация:** README, ARCHITECTURE.md, ADR/, runbook.

---

## 6. Non-functional

- **Покрытие тестами:** ≥ 80 % для изменённых модулей.
- **Code review:** ≥ 1 архитектор + 1 доменный эксперт.
- **Метрики:** Graphify-отчёт + CI-артефакты (coverage, mypy, linter).
- **Коммуникации:** weekly status, ритуал демо в конце спринта.

---

## 7. Risks & Mitigations

| Риск | Митигация |
|---|---|
| Поломка обратной совместимости | feature-flag `LEGACY_AGENTS_ENABLED`, deprecation period 2 спринта |
| Скрытые зависимости, невидимые Graphify | ручной `pydeps` + code review |
| Регрессия в trade-логике | shadow-run нового pipeline параллельно со старым |
| Перенос файлов ломает git blame | `git log --follow` + CHANGELOG.md + ADR |

---

## 8. Resources

- **Инструменты:** Graphify, `import-linter`, `pytest`, `mypy`, `ruff`, `pydeps`.
- **Документы:** `graphify-out/GRAPH_REPORT.md` (актуальный), `docs/ARCHITECTURE.md`, KNOWN_ISSUES.md.
- **Команда:** разработчики Python + архитектор + тимлид.

---

## 9. Open Questions — **Resolved 2026-06-20**

| # | Вопрос | Решение | Обоснование |
|---|---|---|---|
| Q1 | `common-contracts`: отдельный репо **или** подпакет? | **Подпакет** `astrofin/common/` в рабочем корне | Избегаем 5-го репозитория; упрощает release-flow. Экспорт через `pyproject.toml` (PEP 621) при необходимости |
| Q2 | `import-linter` конфиг: в каждом репо **или** только в корневом? | **Только в рабочем корне** (`.importlinter`) | Один источник истины; проверяем только то, что собирается. Дочерние репо получают pre-commit-линтер |
| Q3 | Seed-формат для `--deterministic`? | **`--seed=YYYY-MM-DD` (UTC date)** | Читаемо в логах; воспроизводимо из `git log`; совпадает с форматом `core.history_db` |
| Q4 | Где хранить `GRAPH_REPORT.md`? | **`docs/audit/graphify/<date>.md`** (симлинк на актуальный — `docs/audit/graphify/latest.md`) | Версионируется в git; `latest.md` для быстрого доступа |
| Q5 | Версионирование `common-contracts`? | **SemVer** (`MAJOR.MINOR.PATCH`) | Стандарт; совместимо с tag-triggered release |

---

## 10. Repository Discovery & Working Root Decision (2026-06-20)

### 10.1 Реальный ландшафт воркспейса

При инвентаризации `/home/workspace/` обнаружено **4 git-репозитория**, содержащих код AstroFin, плюс 1 копия без `.git`:

| Корень | Branch | HEAD | Origin | Статус |
|---|---|---|---|---|
| `/home/workspace/` | `master` | `d48d5a5` | `mahaasur13-sys/astrofin-sentinel-platform` | **Основной код** (12/13 файлов S1-пилота) |
| `/home/workspace/astrofin-sentinel-v5/` | `phase4-observability-ab-cd-backtest-paper` | `5affa98` | `mahaasur13-sys/astrofin-sentinel-v5` | Экспериментальная ветка (наблюдаемость, A/B) |
| `/home/workspace/AstroFinSentinelV5/` | `main` | `13cfec7` | `mahaasur13-sys/AstroFinSentinelV5` | «Initial import» — почти пустая оболочка |
| `/home/workspace/AsurDev/` | — | — | `mahaasur13-sys/AsurDev` | ACOS (storage/contracts/events) — отдельный домен |
| `/home/workspace/[ARCHIVED] audit_repo/` | — | — | — | [ARCHIVED] Копия для офлайн-аудита (на диске, не в git) |
| `/home/workspace/push/` | `main` | `71d6e1d` | `mahaasur13-sys/push` | Независимый сервис-publisher |

### 10.2 Решение по рабочему корню

**Рабочий репозиторий для S1 и всего рефакторинга: `/home/workspace/`** (= `astrofin-sentinel-platform`, branch `master`, HEAD `d48d5a5`).

**Причины:**
- Реальный production-код (`agents/`, `acos/`, `core/`, `orchestration/`) живёт здесь.
- 12 из 13 файлов S1-пилота физически существуют только в этом корне.
- `AstroFinSentinelV5/` сейчас — пустая оболочка («Initial import»), синхронизация с ней не имеет смысла до окончания рефакторинга.

**Стратегия для `AstroFinSentinelV5/`:**
- После завершения **S1–S2** (или в конце **S3**) делаем однонаправленный перенос изменений в `AstroFinSentinelV5/` через merge или rebase.
- `AstroFinSentinelV5/` остаётся **каноническим** репозиторием для долгосрочного сопровождения.

**Что делаем с `astrofin-sentinel-v5/` (экспериментальная ветка):**
- Помечаем `phase4-observability-ab-cd-backtest-paper` как **frozen** до окончания S3.
- После стабилизации рабочего корня — cherry-pick ценные куски (observability, A/B) в S5.

**Что делаем с `AsurDev/`:**
- На S1 — выделяем `AsurDev/acos/storage/schema.py` как пилотный файл.
- На S2 — формализуем границу: ACOS становится отдельным доменом с собственным `pyproject.toml` и публикацией в `common-contracts` или собственный пакет.

### 10.3 Топология S1-пилота (актуальные пути)

```
/home/workspace/
├── agents/
│   ├── _impl/
│   │   ├── technical_agent.py    ← PILOT 1 (294 строки, god node)
│   │   ├── ephemeris_decorator.py
│   │   └── ...
│   ├── base_agent.py             ← god node (AgentResponse, BaseAgent)
│   └── ...
├── core/
│   ├── ephemeris.py              ← PILOT 2 (252 строки, 0-cycles target)
│   ├── base_agent.py
│   └── ...
├── AsurDev/
│   └── acos/
│       └── storage/
│           └── schema.py         ← PILOT 3 (44 строки, 1-file cycle)
└── ...
```

### 10.4 Связанные документы

- `docs/refactor/S1_pilot_proposal.md` — детальный план S1 + пример рефакторинга `technical_agent.py`.
- `common/interfaces.py` — черновик протоколов (после утверждения Q1).

---

## 11. S2 Completion Report — 2026-06-20

S2 (Cross-repo contract unification) завершён. Ниже — зафиксированные
артефакты, миграции и итоговые метрики.

### 11.1 Что создано

| Артефакт | Расположение | Описание |
|---|---|---|
| Пакет `acos-contracts` v0.1.0 | `/home/workspace/acos-contracts/` | 10 модулей, `pyproject.toml` (PEP 621), editable install |
| ADR-0002 | `docs/adr/ADR-0002-common-contracts.md` | Решение о выделении `acos-contracts` как единого источника истины |

**Модули `acos_contracts/` (v0.1.0):**

| Модуль | Содержимое | Назначение |
|---|---|---|
| `interfaces` | `AgentResponseProtocol`, `SignalDirectionProtocol`, `BaseAgentProtocol` | Покрытие God Node #1–#3 |
| `contracts` | `TraceRecorderContract`, `StorageBackendContract` | Persistence / trace контракты |
| `deterministic` | `DeterministicClock`, `DeterministicUUIDFactory` | Покрытие God Node #6 |
| `deterministic_factory` | factory-функции | Конструкторы для вышестоящих |
| `events` | `EventType`, `Decision`, `ExecutionResult` | DTO для разрыва Surprising Connection #3 |
| `feature_pipeline` | `WindowEngineProtocol` | Разрыв Surprising Connection #1 |
| `state` | `StateStoreProtocol` | Разрыв Surprising Connection #2 |
| `trading` | `RiskEngineProtocol`, `StrategyEvaluatorProtocol`, `MarketStateProtocol` | Покрытие God Node #5, #8, #9, #10 |
| `errors` | `AcosContractError` и иерархия | Общий словарь ошибок |
| root `acos_contracts` | re-exports | Удобный namespace для частых символов |

### 11.2 Мигрированные репозитории

| Репозиторий | Коммит S2 | Дельта |
|---|---|---|
| `astrofin-sentinel-platform` (`/home/workspace/`) | `a664f74` | `common.*` → `acos_contracts.*`; старые пути в `common/` оставлены как re-export шимы |
| `AsurDev` (`/home/workspace/AsurDev/`) | `7f50ea6` | Локальные дубликаты `EventType` / `Decision` / `ExecutionResult` заменены на реэкспорты; более богатые реализации оставлены локально |
| `acos-contracts` | `860ab03` | v0.1.0 baseline — сам пакет |

**Не требовали миграции (прямых кросс-импортов нет):**

- `home-cluster-iac` — чистый потребитель контрактов, не импортировал старые пути.
- `roma-execution-bridge` — аналогично; Surprising Connection #4 устранена на уровне контракта, без правок в самом репо.

### 11.3 Итоговые метрики S2

| Метрика | До S2 | После S2 |
|---|---|---|
| God Nodes, покрытые протоколами | 6 / 10 (только S1) | **10 / 10** |
| Surprising Connections (кросс-репо INFERRED) | 5 | **0** (устранены на уровне контрактов) |
| Прямые кросс-репозиторные импорты | 5 | **0** |
| Репозиториев с дубликатами `EventType` | 2 | **0** |
| Репозиториев, зависящих от `acos-contracts` | 0 | **2** (`astrofin-sentinel-platform`, `AsurDev`) |

### 11.4 Статус публикации

Пакет `acos-contracts` опубликован **локально** через `pip install -e
/home/workspace/acos-contracts/` (editable install). Это позволяет любому
проекту в `/home/workspace/` подключить контракты одной командой и
получать изменения без пересборки пакета — достаточно `git pull` в
каталоге `acos-contracts/`.

Публикация в PyPI **не выполняется** для версий v0.x: все потребители —
внутренние проекты экосистемы `astrofin-sentinel-platform`. Переход на
PyPI будет рассматриваться при достижении v1.0.0 (стабилизация API).

### 11.5 Что осталось на S3+

- Доменная реорганизация (§3.4) — физическое разделение пакетов
  по доменам `trading_agents`, `risk_management`, `execution`,
  `data_storage`, `core_determinism`, `astrology`, `observability`.
- Подключение `import-linter` (§3.5) как CI-gate.
- Переоценка центральности God Nodes через повторный Graphify-аудит
  после S3: целевое снижение −30…40 %.

---

*Документ будет обновляться после каждого спринта. История решений — в ADR.*
