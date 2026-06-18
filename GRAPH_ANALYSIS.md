# AstroFin Sentinel V5 — Архитектурный анализ Graphify

**Дата:** 2026-06-17  
**Источник:** `graphify-out/graph.json` (38 682 узла, 62 196 рёбер)  
**Активный исходный код:** `push/` (253 .py, 50 074 LOC)  
**Метод:** AST-фаза graphify (Pass 1), zero-token, EXTRACTED-рёбра ~85%.

> **Критическая находка №0 (контекст рабочей директории):**  
> `AstroFinSentinelV5/` содержит **17 .py** — это runtime/data слой (БД, agent instructions, web-dashboard, archived-агенты).  
> Исходный код, по которому реально идёт разработка, живёт в зеркале `push/` (253 active .py).  
> Полные зеркала: `astrofin-sentinel-v5/`, `audit_repo/`, `push/`, `agents/`, `_pr_logs/`, `hived/`.  
> Документация в `AstroFinSentinelV5/AGENTS.md` ссылается на папки (`agents/`, `core/`, `orchestration/`, `meta_rl/`), которые **пусты** в самой `AstroFinSentinelV5/` и реально находятся в `push/`.  
> Это означает, что в workspace существует **несколько конкурирующих «корней проекта»**, и без явного `cd push/ <команды>` ни одна инструкция в `AstroFinSentinelV5/AGENTS.md` не сработает.

---

## 1. God Nodes (модули с наибольшей входящей связностью)

`core/base_agent.py` — **абсолютный лидер** по связности:

| Ранг | In-deg | Импортёров | Файл | Роль |
|---|---|---|---|---|
| **1** | **902** | **143** | `push/core/base_agent.py` | Базовый класс агента (`AgentResponse`, `_degraded()`, константы `EPHEMERIS_UNAVAILABLE`, `UNKNOWN`) |
| 2 | 256 | 16 | `push/mas_factory/topology.py` | Топологии multi-agent совета |
| 3 | 207 | 86 | `push/agents/_impl/ephemeris_decorator.py` | Декоратор `@track_agent_metrics`, исключение `EphemerisUnavailableError` |
| 4 | 176 | 9 | `push/core/kepler.py` | Астрономические вычисления |
| 5 | 164 | 24 | `push/agents/_impl/amre/trajectory.py` | AMRE-траектории |
| 6 | 134 | 21 | `push/meta_rl/strategy_pool.py` | Пул стратегий |
| 7 | 131 | 23 | `push/meta_rl/strategy_evaluator.py` | Оценка стратегий |
| 8 | 108 | 19 | `push/meta_rl/meta_agent.py` | Meta-RL агент |
| 9 | 88 | 8 | `push/db/models.py` | ORM-модели |
| 10 | 76 | 11 | `push/core/volatility.py` | Волатильность |

### Риски

- **`push/core/base_agent.py`** — single point of failure: 143 модуля импортируют его. Любое изменение `AgentResponse`-сигнатуры, исключения или констант ломает **больше половины кодовой базы**.  
- **Fan-out** у `base_agent.py` тоже высок: через него проходят практически все агенты, meta_rl, mas_factory, web. Это не «утилита», а **шина типов домена**.
- **`ephemeris_decorator.py`** — вторая точка риска (86 импортёров, декоратор критичен для всех агентов).  
- **Тестов God Node не существует** в `tests/` — это здоровый сигнал: тесты не доминируют.

---

## 2. Циклы и нежелательные зависимости

**Tarjan SCC по 367 модулям → найден ровно 1 цикл:**

| Цикл | Связь |
|---|---|
| `push/meta_rl/basket.py` ↔ `push/meta_rl/strategy_evaluator.py` | Взаимный import/call |

**Степень критичности: НИЗКАЯ.**  
`meta_rl/basket.py` — расчёт весов корзины, `meta_rl/strategy_evaluator.py` — оценка стратегий. Логически эти компоненты независимы (basket оперирует на уровне портфеля, evaluator — на уровне отдельной стратегии). Цикл, вероятно, исторический: изначально evaluator был утилитой basket, потом basket стал использовать evaluator, и наоборот для типов/метрик. Рекомендация: выделить общий интерфейс в `meta_rl/_types.py` (без импортов обратно) и убрать цикл.

**Других циклов между модулями нет** — это сильный показатель зрелости архитектуры.

### Скрытые кросс-пакетные «потоки»

| Откуда | Куда | Вес | Комментарий |
|---|---|---|---|
| `agents` | `core` | 555 | **Доминирующий поток.** Все агенты → core. Здоровый паттерн. |
| `agents` | `agents` | 488 | Внутри-agent вызовы (соседние агенты, council, etc.). |
| `mas_factory` | `mas_factory` | 210 | Самодостаточный конструктор топологий. |
| `meta_rl` | `meta_rl` | 170 | Внутренние зависимости meta_rl. |
| `core` | `core` | 120 | core-в-core (composition). |
| `backtest` | `agents` | 110 | Backtester дёргает агентов — здоровый паттерн. |
| `web` | `meta_rl` | 20 | Web-dashboard → meta_rl. |
| `trading` | `broker` | 42 | Trading → broker-адаптер. |

**Поток `meta_rl → core → agents → meta_rl`** явно отсутствует на уровне пакетов. Это значит, что meta_rl **не ходит обратно** в агенты напрямую — он общается через `core` и `backtest`. Хороший знак разделения слоёв.

---

## 3. AMBIGUOUS-связи

**В отчёте: 0% AMBIGUOUS, 85% EXTRACTED, 15% INFERRED** (средняя confidence INFERRED = 0.52).

INFERRED-связи возникли только на doc-нодах (LLM-фаза не запускалась, у нас 100% AST). Это означает:
- Все 9 601 INFERRED-рёбер — это **предположения, извлечённые из комментариев/docstring**, не из кода.  
- INFERRED density = 9601 / 62196 = **15.4%**. Это высокий процент «мягких» знаний: архитектурные намерения, упомянутые в коде, но не выраженные в импортах.

> **Недостаточно данных** для перечисления конкретных AMBIGUOUS-связей — в текущей выгрузке их формально 0 (только EXTRACTED и INFERRED). Для разбора AMBIGUOUS нужно запустить `graphify extract .` с LLM-ключом (см. блок «Что потребуется для полного отчёта»).

---

## 4. Модульность и сообщества (Leiden)

**2 702 сообщества** на весь workspace. Для активного `push/` (253 модуля) — **319 сообществ** (т.е. почти каждый модуль = своё сообщество). Это **over-clustering**, типичный для AST-only фазы: алгоритм не находит перемычек через символьные вызовы, потому что фокус — на корневых нодах.

### Здоровые «кластеры» (community size ≥ 3):

| Community | Файлов | Состав | Оценка |
|---|---|---|---|
| **0** | 13 | `astro_council/agent.py`, `bull_researcher.py`, `bear_researcher.py`, … | ✅ Агентский совет выделен в один кластер. |
| **12** | 5 | `bradley_agent`, `cycle_agent`, `electoral_agent` | ✅ Электоральные агенты сгруппированы. |
| **1** | 3 | `karl_synthesis.py`, `core/thompson.py`, `knowledge/rag_retriever.py` | ⚠️ Подозрительное объединение: KARL-синтез + Thompson sampling + RAG. Логически эти три модуля из разных слоёв (orchestration, ml, knowledge). Скорее всего граф увидел общий паттерн вызовов, но архитектурно это разные ответственности. |
| **18** | 2 | `ephemeris_decorator.py`, `technical_agent.py` | ❓ Decorator + конкретный агент в одном кластере — натянуто. |
| **2** | 2 | `synthesis_agent.py`, `core/volatility.py` | ❓ Агент и доменная утилита вместе. |
| **100** | 2 | `core/council/agents.py`, `core/council/types.py` | ✅ Здоровый. |

### Вердикт по модульности

- **Границы пакетов (top-level) чёткие** — `agents/`, `core/`, `meta_rl/`, `trading/`, `backtest/`, `web/`, `db/`, `mas_factory/`, `knowledge/`, `strategies/`, `tools/`, `observability/` — все изолированы в своём большинстве.
- **`agents/_impl/`** — внутри-импортная плотность высокая (488 рёбер внутри `agents`). Это ожидаемо (агенты общаются между собой через council).
- **Нарушение, которое надо чинить:** `push/core/coordination/`, `push/core/council/`, `push/core/reward/` — это «оркестрация в core» вместо отдельного пакета. По названию они в `core`, по сути — координация. Архитектурный долг.
- **AMRE-подпакет** (`agents/_impl/amre/`) — изолирован от основной массы `agents/_impl/` ровно одним уровнем вложенности. Рекомендуется вынести в `amre/` верхнего уровня (как самостоятельный пакет).

---

## 5. Сравнение с идеальной архитектурой

### Что соответствует идеалу

| Критерий | Состояние | Вердикт |
|---|---|---|
| Базовый класс агента (`base_agent.py`) | Существует, импортируется 143 модулями | ✅ Канонический контракт |
| `@track_agent_metrics` декоратор | 86 импортёров | ✅ Сквозная метрика на месте |
| `_degraded()` / `EPHEMERIS_UNAVAILABLE` / `UNKNOWN` | Используются | ✅ Safety-контракт |
| Cyclic deps | 0 (1 малый цикл basket↔evaluator) | ✅ Чисто |
| Package boundaries | Чёткие (agents/core/meta_rl/...) | ✅ |
| Backtester отдельно от trading | `backtest/` импортирует agents, не наоборот | ✅ |
| Trading → broker adapter | Изолирован | ✅ |
| web → meta_rl | Только чтение | ✅ |

### Что нарушено

| Паттерн | Реальность | Идеал |
|---|---|---|
| **Один канонический корень проекта** | 4+ зеркала: `AstroFinSentinelV5/`, `astrofin-sentinel-v5/`, `push/`, `audit_repo/`, `agents/`, `_pr_logs/`, `hived/` | Один `src/` или `app/` |
| **Tests mirror source layout** | `push/tests/test_X.py` дублируется в 4+ копиях | `tests/` верхнего уровня |
| **Документация в `AGENTS.md` отражает реальность** | Документирует `AstroFinSentinelV5/agents/`, которого нет в `AstroFinSentinelV5/` | Документация = зеркало кода |
| **Слой оркестрации отдельно** | Координация размазана: `core/coordination/`, `core/council/`, `core/reward/`, `mas_factory/`, `orchestration/` (пустая) | Один пакет `orchestration/` |
| **AMRE как самостоятельная подсистема** | Спрятан в `agents/_impl/amre/` | `amre/` верхнего уровня |
| **Meta-RL ↔ Trading ↔ Execution изолированы** | Цикл basket↔evaluator внутри `meta_rl/` | Чистый DAG |

### Риск-зоны

- **`_archived/` папки** разбросаны по workspace (`AstroFinSentinelV5/agents/_archived/`, `agents/_archived/`). В активном `push/` их нет — это значит, архивирование **на уровне workspace**, а не на уровне проекта. Риск: устаревший код читается новыми разработчиками.
- **Test-зеркала** (`test_meta_rl.py` встречается в 5+ копиях): pytest запускает все копии или только одну? Если все — то тесты **умножают runtime-стоимость** в 5 раз.
- **`agents/gitagent_registry.py`** + `agents/gitagent_exporter.py` — отдельная «GitAgent»-подсистема, импортируемая 5 файлами, нигде не в community. Подозрение на «забытый» модуль.

---

## 6. Приоритизированные рекомендации (TOP 5)

### 🔴 P0. Консолидация зеркал (cleanup, ~1 день)

**Что:** Оставить один канонический корень (`AstroFinSentinelV5/` или `push/`), остальные зеркала перенести в `Trash/` или в `archive/`.  
**Почему:** `AstroFinSentinelV5/AGENTS.md` указывает на структуру, которой нет в самой `AstroFinSentinelV5/`. Любой новый разработчик или AI-agent выполнит инструкции в `AstroFinSentinelV5/AGENTS.md` и получит `ModuleNotFoundError`.  
**Эффект:** AGENTS.md становится исполняемым; pytest перестаёт запускать 5 копий одного теста; устраняются race-conditions при push в git.

### 🟠 P1. Изоляция god-node `core/base_agent.py` (≈2–3 дня)

**Что:** Провести аудит всех 143 импортёров, разделить `base_agent.py` на:
- `core/base_agent/protocol.py` (протокол, без зависимостей)
- `core/base_agent/implementation.py` (конкретика)
- `core/base_agent/degraded.py` (`_degraded`, константы)
**Почему:** Сегодня любое изменение `base_agent.py` = каскад правок в 143 файлах. Это самый частый источник merge-конфликтов.  
**Эффект:** Изменение контракта больше не = изменение реализации; 143 файла продолжают работать без правок.

### 🟠 P1. Устранить цикл `meta_rl/basket.py ↔ meta_rl/strategy_evaluator.py` (≈1 день)

**Что:** Выделить общие типы в `meta_rl/_types.py` (без импортов обратно), убрать прямой import basket↔evaluator.  
**Почему:** Цикл нарушает инвариант «meta_rl — чистый слой».  
**Эффект:** Возможность тестировать basket и evaluator изолированно.

### 🟡 P2. Выделить оркестрацию из `core/` (≈3–5 дней)

**Что:** Перенести `core/coordination/`, `core/council/`, `core/reward/` в `orchestration/`. Сейчас `orchestration/` пуста в `push/` (файлы есть только в зеркалах).  
**Почему:** Координация — это не «core domain», это runtime-инфраструктура. Разделение ответственности.  
**Эффект:** `core/` остаётся чисто доменным (`base_agent`, `kepler`, `volatility`, `thompson`), `orchestration/` — runtime.

### 🟡 P2. Поднять AMRE до top-level (≈2 дня)

**Что:** `agents/_impl/amre/` → `amre/`. Это 8+ модулей (trajectory, replay_buffer, ensemble_selection, audit, astro_reward, counterfactual, grounding, meta_questioning, backtest_loop, lag_windowing).  
**Почему:** AMRE — это самостоятельный RL-стек, спрятанный в `_impl/`. Из-за этого AMRE-специфичные тесты, конфиги и зависимости зашиты внутрь `agents/`.  
**Эффект:** AMRE можно релизить отдельно, тестировать отдельно, масштабировать отдельно.

---

## Что потребуется для полного отчёта (P1 для следующего захода)

1. **LLM-ключ** (`ANTHROPIC_API_KEY` или `GEMINI_API_KEY`) → запуск `graphify extract .` с семантической фазой → AMBIGUOUS-рёбра + LLM-разметка сообществ (Leiden с именами).
2. **Расширить `.graphifyignore`** — добавить `astrofin-sentinel-v5/`, `audit_repo/`, `push/`, `_pr_logs/`, `hived/`, `hived-asur/`, `_sbs_old/`, `tests/`-без-префикса, `agents/`-в-корне, `trading/`/`core/`/`meta_rl/`/`backtest/`-в-корне. Тогда граф будет **только по активному коду**.
3. **Прогон `graphify cluster-only`** после extract → получение читаемых community-имён (сейчас 2 702 безымянных «Community N»).
4. **Сгенерировать `graph.html`** с `GRAPHIFY_VIZ_NODE_LIMIT=50000` (сейчас 38 682 > 5 000, граф пропущен) — визуальная проверка god-нодов глазами.

---

## Сводка цифр

| Метрика | Значение |
|---|---|
| Всего узлов в графе | 38 682 |
| Всего рёбер | 62 196 |
| Active .py (`push/`, no tests, no archive) | 253 |
| Active LOC | 50 074 |
| Кросс-модульных рёбер (active) | 3 305 |
| Уникальных модулей в графе зависимостей | 367 |
| EXTRACTED рёбра | 85% (≈52 866) |
| INFERRED рёбра | 15% (9 601, avg conf 0.52) |
| AMBIGUOUS рёбра | 0% (LLM-фаза не запускалась) |
| Циклы (SCC size > 1) | 1 (`meta_rl/basket ↔ strategy_evaluator`) |
| God nodes (in-deg ≥ 100) | 4 (`base_agent`, `topology`, `ephemeris_decorator`, `kepler`) |
| Active сообществ | 319 (over-clustered) |
| Зеркала проекта | 6+ (`AstroFinSentinelV5`, `astrofin-sentinel-v5`, `push`, `audit_repo`, `agents`, `_pr_logs`, `hived`, `_sbs_old`) |
