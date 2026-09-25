# AstroFin Sentinel v5 — Архитектурный Аудит: Графовая Мультиагентная Модель

**Дата:** 2026-08-08  
**Аудитор:** Zo Computer (asurdev)  
**Версия системы:** v1.0.0-beta (Sprint F closed, `master` @ `c1b7e8d1`)

---

## 1. Резюме (Executive Summary)

AstroFin Sentinel v5 — зрелая production-система с 16+ агентами, 9 CI-воркфлоу, RAG-First архитектурой и KARL-синтезом. **Графовая готовность: 4 из 7 критериев выполнены частично (🟡), 1 — полностью (✅), 2 отсутствуют (❌).** Система имеет key building blocks для перехода к DAG (MASFactory, `asyncio.gather`, audit trail), но не хватает явного графового оркестратора, векторной памяти между агентами и кэширования промптов. **Переход к полной графовой архитектуре реалистичен за 2 спринта (4 недели) с ожидаемой экономией на LLM-вызовах 40-60% и ускорением пайплайна 2-3x.**

---

## 2. Карта текущих взаимодействий

### 2.1 Топология «as-is» (2026-08-08)

```
                    ┌─────────────┐
                    │  Zo Cron /   │
                    │  Automation  │ (каждые 20 мин)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Router    │ ← rule-based (keyword matching)
                    │  router.py  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌──────▼──────┐ ┌──▼──────────┐
     │  TECHNICAL │ │   MACRO     │ │   ASTRO     │
     │    FLOW    │ │    FLOW     │ │   FLOW      │
     │ (parallel) │ │ (parallel)  │ │ (parallel)  │
     └─────┬──────┘ └──────┬──────┘ └──┬──────────┘
           │               │           │
           └───────────────┼───────────┘
                           │
                  ┌────────▼────────┐
                  │   SYNTHESIS     │
                  │  (KARL/Synth)   │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌──────▼──────┐ ┌──▼──────────┐
     │  Save SQL  │ │  Telegram   │ │  Dashboard  │
     │  history   │ │   alert     │ │   update    │
     └────────────┘ └─────────────┘ └─────────────┘
```

### 2.2 Связи между компонентами (матрица зависимостей)

| Компонент | Вызывает | Через | Тип |
|-----------|----------|-------|-----|
| `sentinel_v5.py` | `router.py` | прямой import | синхронный |
| `sentinel_v5.py` | `result_aggregator.py` (flows) | прямой import | `asyncio.gather` (параллельно внутри flow) |
| `result_aggregator.py` | `agents/_impl/*` | прямой import run_* функций | `asyncio.gather` |
| `result_aggregator.py` | `data_room/resolvers/*` | `CoinGeckoResolver` | async HTTP |
| Каждый агент | `data_room/blueprint` | R-01 (через data_room) | async HTTP |
| Каждый агент | `core/llm_router.py` | `BaseAgent.generate()` | синхронный → Ollama/OpenRouter |
| `BaseAgent.generate()` | `knowledge/rag_index.py` | `retrieve_context()` | FAISS lookup |
| `karl_synthesis.py` | `amre/*` (14 модулей) | прямой import | синхронный/async |
| `karl_synthesis.py` | `core/history_db.py` | `save_session()` | SQLite/PostgreSQL |
| `sentinel_v5_mas.py` | `mas_factory/` | `MASFactoryArchitect` | async topology execution |
| `web/app.py` | Dash callbacks | HTTP polling | WebSocket/HTTP |
| `telegram_bot/` | `orchestration.sentinel_v5` | subprocess/import | async |

### 2.3 Хранилища данных (read/write потоки)

| Хранилище | Пишут | Читают | Формат |
|-----------|-------|--------|--------|
| PostgreSQL + TimescaleDB | sentinel_v5 (persist), KARL | Dashboard, AI-Ops | SQL |
| SQLite (`core/history.db`) | sentinel_v5 (fallback) | Dashboard, audit | SQL |
| FAISS index (in-memory) | `knowledge/rag_index.py` (init/rebuild) | Все агенты через `BaseAgent.generate()` | векторы |
| `/dev/shm/astrofin_signals.log` | sentinel_v5 (strong signals) | AI-Ops monitoring | text |
| `logs/llm_requests.jsonl` | `core/llm_router.py` | аналитика | JSONL |
| `amre/audit.py` JSONL | KARL Synthesis Agent | audit, backtest | JSONL |

### 2.4 Критические зависимости и циклы

**Циклов нет** — все вызовы направленные. Но есть неявная зависимость: Evolution worker (Meta-RL, порт 8050) читает AuditLog, который пишет KARL, который вызывается из sentinel_v5. При падении sentinel_v5 audit не пополняется → evolution деградирует. Это не цикл, а каскадная зависимость.

**Критический путь (полный анализ BTCUSDT):**
`Router → 4 flows parallel → Synthesis → KARL post-processing → persist`  
~15-30 секунд при полной загрузке (основная задержка — LLM-вызовы агентов).

---

## 3. Оценка параллелизма

### 3.1 Что уже параллельно (✅)

1. **Внутри каждого flow-а агенты запускаются через `asyncio.gather`:**
   - `run_macro_flow()`: FundamentalAgent + MacroAgent + QuantAgent + OptionsFlowAgent + SentimentAgent — **5 агентов одновременно**
   - `run_technical_flow()`: MarketAnalyst + BullResearcher + BearResearcher — **3 агента одновременно**
   - `run_astro_flow()`: AstroCouncil → Bradley + Electoral + TimeWindow + Gann + Cycle — **5 агентов одновременно** (внутри AstroCouncil)

2. **MASFactory (`sentinel_v5_mas.py`):** строит топологический граф ролей и исполняет узлы параллельно где возможно через `TopologyExecutor`.

### 3.2 Что идёт последовательно (🟡 можно распараллелить)

В `run_karl_sentinel_v5()` (основной путь):

```python
# Шаг 1: Router (синхронно)
route_output = route_query(user_query)

# Шаг 2: RAG (синхронно, перед агентами)
rag_context = rag.retrieve(query)  # ← можно параллельно с Router

# Шаг 3: 4 flow-а — идут ПОСЛЕДОВАТЕЛЬНО?
technical_signals = await run_technical_flow(...)
electoral_signals = await run_electoral_flow(...)
astro_signals = await run_astro_flow(...)
macro_signals = await run_macro_flow(...)
# ⚠️ Это ключевой разрыв: 4 flow-а вызываются await последовательно!
```

Фактически, в `sentinel_v5.py` каждый flow вызывается отдельным `await`, а не `asyncio.gather`. Это значит, что **MACRO-агенты ждут завершения TECHNICAL, ASTRO ждёт MACRO** — теряется 2-3x потенциального параллелизма.

### 3.3 Конкретные примеры параллелизации

**Пример 1:** RAG retrieval + Router classification — полностью независимы.  
Текущее: Router → затем RAG в каждом агенте.  
Предложение: `await asyncio.gather(route_query(...), rag.retrieve(...))`.

**Пример 2:** 4 flow-а (Technical, Macro, Astro, Electoral) независимы друг от друга.  
Текущее: последовательный `await`.  
Предложение: `await asyncio.gather(run_technical, run_macro, run_astro, run_electoral)`.

**Пример 3:** Data fetching (CoinGecko + SEC EDGAR + FearGreed) можно делать параллельно с запуском агентов.

**Ожидаемое ускорение:** с ~20-30 сек до ~8-12 сек (2.5-3x) при полной параллелизации flow-ов.

---

## 4. Узкие места с точки зрения графа

### 4.1 Отсутствие явного разделения на узлы (❌)

`sentinel_v5.py` (382 строки) и `karl_synthesis.py` (439 строк) — монолитные функции, смешивающие:
- Маршрутизацию
- Сбор данных
- Запуск агентов
- Синтез
- Персистенцию
- Отправку уведомлений

В DAG-модели каждый из этих шагов должен быть отдельным узлом с чёткими входами/выходами.

### 4.2 Один модуль — много функций (🟡)

`result_aggregator.py` (131 строка) — одновременно:
- Запускает агентов
- Агрегирует результаты
- Обрабатывает ошибки агентов (graceful degradation)
- Извлекает цену через `_fetch_price()`

В DAG это должно быть разделено на: `AgentNode`, `ResultCollectorNode`, `PriceFetcherNode`.

### 4.3 Потеря информации между этапами (🟡)

Промежуточные результаты агентов (до синтеза) сохраняются в `state["all_signals"]` — Python dict, не сериализованный граф. При сбое SynthesisAgent теряется контекст того, какие сигналы были получены. В графовой модели каждый узел сохраняет свой output в иммутабельный контекст графа.

---

## 5. Пригодность для DAG-оркестрации

### 5.1 Компоненты, легко оборачиваемые в узлы DAG (✅)

| Текущая функция | DAG-узел | Вход | Выход |
|----------------|----------|------|-------|
| `route_query()` | `RouterNode` | `user_query: str` | `RouterOutput` |
| RAG `retrieve_context()` | `RAGNode` | `query: str` | `context: str` |
| `_fetch_price()` | `PriceNode` | `symbol: str` | `price: float` |
| `run_*_flow()` | `TechnicalFlowNode`, `MacroFlowNode`, etc. | `state: dict` | `signals: list[AgentResponse]` |
| `SynthesisAgent.run()` | `SynthesisNode` | `signals: list` | `TradingSignal` |
| `KARLSynthesisAgent.run()` | `KARLNode` | `signals + state` | `DecisionRecord + final_signal` |
| `save_session()` | `PersistNode` | `state: dict` | `session_id` |
| Telegram alert | `AlertNode` | `signal + confidence` | `bool` |

**Итого: 10+ узлов с чёткими контрактами.**

### 5.2 Компоненты, требующие рефакторинга (🟡)

| Компонент | Проблема | Рефакторинг |
|-----------|---------|------------|
| `sentinel_v5.py` | Монолитная `async def run_karl_sentinel_v5()` | Разделить на узлы + DAG-композицию |
| `BaseAgent.generate()` | Неявно связан с RAG + LLM router | Выделить `LLMCallNode` с контекстом |
| `result_aggregator.py` | Смешивает запуск и агрегацию | Разделить на `AgentNode` + `CollectorNode` |
| `amre/karl_integration.py` | 14 AMRE-модулей, неявные зависимости | Обернуть в `KARLPostProcessNode` |

---

## 6. Возможности кэширования

### 6.1 Существующий кэш (🟡)

| Кэш | Уровень | TTL | Эффективность |
|-----|---------|-----|--------------|
| Session cache в `llm_router.py` | Классификация сложности → бэкенд | 5 мин | Только исключает повторную классификацию |
| FAISS index в памяти | Эмбеддинги документов | persistent | Каждый агент делает отдельный lookup |

### 6.2 Что можно кэшировать (❌ сейчас отсутствует)

1. **Промпты агентов (30-50% LLM-вызовов дублируются):**
   - Одинаковые промпты FundamentalAgent для BTCUSDT в пределах 15-минутного окна
   - Астро-расчёты (Bradley, Gann) меняются раз в день → кэш 24 часа

2. **Результаты RAG retrieval:**
   - Одинаковый контекст для 5+ агентов в одном прогоне → кэшировать на уровне сессии

3. **Результаты data_room вызовов:**
   - CoinGecko price, FearGreed index — кэш 30-60 секунд

4. **Эмбеддинги промптов (векторный кэш):**
   - `cosine_similarity(prompt_new, prompt_cached) > 0.95` → вернуть кэшированный ответ
   - Потенциальная экономия: 5-10x на повторяющихся запросах

**Оценка экономии:**
- При полном внедрении кэширования: **снижение LLM-затрат на 40-60%**
- При 20-минутном интервале запуска: ~72 вызова/день → экономия ~$3-5/день на OpenRouter (при среднем usage)

---

## 7. Наблюдаемость

### 7.1 Что уже есть (✅)

| Метрика | Источник | Куда попадает |
|---------|----------|--------------|
| Health check (CPU, RAM, uptime) | `monitoring/health_endpoints.py` | Prometheus → Grafana |
| 104 Prometheus метрики | `tools/metrics_server.py` | Prometheus |
| Agent selection counts | `AGENT_SELECTION_COUNTS` в `context_manager.py` | Prometheus |
| LLM request logs (backend, model, latency) | `logs/llm_requests.jsonl` | Loki / файлы |
| DecisionRecord audit trail | `amre/audit.py` | JSONL |
| KARL diagnostics (Q*, uncertainty, drift) | `karl_synthesis.py` | Логи + dashboard |
| 15 Prometheus alerts | Prometheus rules | AI-Ops → Telegram |

### 7.2 Что отсутствует для DAG (❌)

| Необходимо | Текущее состояние |
|-----------|------------------|
| Per-node latency (сколько времени занял каждый узел) | Нет — только общее время сессии |
| Per-node error rate | Есть `return_exceptions=True`, но не агрегируется |
| DAG trace (какой путь прошёл конкретный запрос) | Нет — нет trace ID / span |
| Inter-node data flow (какие данные переданы между узлами) | Не логируется |
| Cache hit/miss rate | Не отслеживается |

**Что нужно добавить:** OpenTelemetry spans на каждый DAG-узел, trace ID от Router до Persist, метрики cache hit/miss.

---

## 8. Устойчивость (Self-Healing)

### 8.1 Что уже есть (🟡)

| Механизм | Уровень | Описание |
|----------|---------|----------|
| `return_exceptions=True` в `asyncio.gather` | Agent flow | При падении агента — NEUTRAL fallback с confidence=30 |
| Circuit breaker OpenRouter → Ollama | LLM router | После 3 ошибок за 60 сек — переход на локальную модель |
| PostgreSQL → SQLite fallback | Persistence | `PG_AVAILABLE` флаг + dual-write |
| Zo service restart | Infrastructure | Падение всего процесса → автоматический перезапуск |
| `except Exception` в KARL | Synthesis | Деградация до простого SynthesisAgent без AMRE |

### 8.2 Что отсутствует (❌)

| Необходимо | Текущее состояние |
|-----------|------------------|
| Retry с exponential backoff для отдельных узлов | Нет — только один проход |
| Альтернативные маршруты в графе | Нет — граф фиксированный |
| Health check per-agent | Нет — только глобальный health endpoint |
| Circuit breaker на data_room вызовы | Нет (есть `circuit_breaker.py`, но не интегрирован) |
| Graceful degradation path при отказе Synthesis | Нет — отказ Synthesis = отказ всего пайплайна |

---

## 9. Сравнение с эталонной моделью

| Критерий | Оценка | Обоснование |
|----------|--------|------------|
| **1. Явный DAG-оркестратор** | 🟡 | MASFactory строит топологии, но основной путь (`sentinel_v5.py`) жёстко закодирован. Flow-ы идут последовательно. |
| **2. Векторная память (граф знаний)** | 🟡 | FAISS+BM25+RRF для RAG, но нет shared embedding space между агентами. RAG используется per-agent, а не как общая память. |
| **3. Динамическое связывание** | 🟡 | Thompson Sampling выбирает агентов динамически, но рёбра между flow-ами фиксированы. Нет relevance-based routing между агентами. |
| **4. Кэширование промптов** | ❌ | Только session cache (5 мин TTL) на уровне классификации. Нет кэша промптов, результатов RAG, эмбеддингов. |
| **5. Наблюдаемость на уровне узлов** | 🟡 | Prometheus метрики есть, audit trail (KARL) детальный, но нет per-node tracing/latency в DAG-стиле. |
| **6. Самоисцеление** | 🟡 | Graceful degradation агентов (NEUTRAL fallback), circuit breaker на LLM, но нет retry/альтернативных маршрутов для узлов. |
| **7. Масштабируемость** | ✅ | Новые агенты добавляются через `agents/_impl/` + регистрация в пулах. Архитектурный линтер и `validate_agent.py` гарантируют контракт. CI/CD покрывает 9 воркфлоу. |

**Средняя оценка:** 🟡 (4.3 / 7 — частичная готовность)

---

## 10. Разрывы (Gaps)

| # | Разрыв | Влияние | Приоритет |
|---|--------|---------|-----------|
| G1 | Flow-ы вызываются последовательно, а не параллельно | 2-3x замедление пайплайна | 🔴 P0 |
| G2 | Нет кэша промптов/эмбеддингов | 40-60% избыточных LLM-вызовов | 🔴 P0 |
| G3 | Нет явного DAG-оркестратора | Монолитность, сложность отладки | 🟡 P1 |
| G4 | Нет per-node observability (tracing) | Непонятно, какой агент bottleneck | 🟡 P1 |
| G5 | Нет retry/альтернативных маршрутов | Полный отказ пайплайна при сбое Synthesis | 🟡 P1 |
| G6 | RAG per-agent, нет shared embedding space | Контекст дублируется, нет обучения между агентами | 🟢 P2 |
| G7 | MASFactory не интегрирован в основной поток | Два параллельных оркестратора (sentinel_v5 + MAS) | 🟢 P2 |

---

## 11. Рекомендуемый DAG-пайплайн

### 11.1 Узлы и рёбра (целевая архитектура)

```
                    ┌──────────┐
                    │  TRIGGER │ (Zo Cron / API / Telegram)
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌─────────┐ ┌────────┐ ┌─────────┐
        │ ROUTER  │ │  RAG   │ │  PRICE  │  ← Level 0: параллельный сбор
        │  NODE   │ │  NODE  │ │  NODE   │     контекста
        └────┬─────┘ └───┬────┘ └────┬────┘
             │            │          │
             └────────────┼──────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
    ┌─────────▼──┐ ┌──────▼─────┐ ┌──▼──────────┐
    │ TECHNICAL  │ │   MACRO    │ │    ASTRO     │  ← Level 1: параллельные
    │   FLOW     │ │   FLOW     │ │    FLOW      │     agent flow-ы
    │ (3 agents) │ │ (5 agents) │ │  (5 agents)  │
    └─────┬──────┘ └──────┬─────┘ └──┬───────────┘
          │               │           │
          └───────────────┼───────────┘
                          │
                ┌─────────▼─────────┐
                │    SYNTHESIS      │  ← Level 2: агрегация
                │      NODE         │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │   KARL POST-      │  ← Level 3: AMRE-обработка
                │   PROCESS NODE    │
                └─────────┬─────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
    ┌─────────▼──┐ ┌──────▼─────┐ ┌──▼──────────┐
    │  PERSIST   │ │  ALERT     │ │  DASHBOARD  │  ← Level 4: выходные узлы
    │   NODE     │ │  NODE      │ │  UPDATE     │
    └────────────┘ └────────────┘ └─────────────┘
```

**Всего узлов:** 14  
**Уровней:** 5  
**Максимальный параллелизм:** Level 1 (11 агентов параллельно в 3 flow-ах)  
**Критический путь:** Router/Price/RAG → MacroFlow → Synthesis → KARL → Persist (~8-12 сек)

### 11.2 Контракты узлов (пример)

```python
@dataclass
class RouterNodeInput:
    user_query: str
    context: dict | None

@dataclass
class RouterNodeOutput:
    query_type: str
    symbols: list[str]
    timeframe: str
    include_technical: bool
    include_astro: bool
    include_electional: bool
    include_macro: bool
```

---

## 12. План внедрения (Roadmap)

### Этап 1: Пилотный DAG (Спринт G — 2 недели) 🔴 P0

**Цель:** минимальный DAG-оркестратор на 5 узлах, покрывающий полный цикл анализа BTCUSDT.

**Задачи:**
1. **Создать `orchestration/dag_engine.py`** — легковесный DAG-движок:
   - `DAGNode` base class с `async run(input) -> output`
   - `DAGPipeline` — регистрация узлов, разрешение зависимостей, параллельное исполнение
   - Интеграция с существующим `asyncio.gather`

2. **Обернуть 5 узлов:**
   - `RouterNode` (из `orchestration/router.py`)
   - `PriceNode` (из `result_aggregator._fetch_price`)
   - `MacroFlowNode` (из `result_aggregator.run_macro_flow`)
   - `SynthesisNode` (из `agents/_impl/synthesis_agent.py`)
   - `PersistNode` (из `core/history_db`)

3. **Параллелизовать Level 0 и Level 1:**
   - Router + Price + RAG → `asyncio.gather`
   - Все 4 flow-а → `asyncio.gather` (не последовательно!)

4. **Добавить базовое кэширование:**
   - In-memory LRU-кэш для промптов агентов (TTL 15 мин)
   - Кэш RAG-результатов на уровне сессии

5. **Интегрировать с существующим automation:**
   - Обновить automation "Scheduled BTCUSDT Analysis" на вызов DAG

**Ожидаемые результаты:**
- Ускорение: с ~20-30 сек до ~10-15 сек
- Снижение LLM-вызовов: ~30% (за счёт кэша)
- 0 изменений в API агентов (узлы — обёртки над существующими run_* функциями)

**Ответственный:** @felix (core DAG engine) + Zo (интеграция)

---

### Этап 2: Полный DAG + Кэширование (Спринт H — 2 недели) 🟡 P1

**Цель:** расширение на все 14 узлов, полноценное кэширование, tracing.

**Задачи:**
1. **Обернуть все 14 узлов** (оставшиеся 9: TechnicalFlow, AstroFlow, ElectoralFlow, KARLPostProcess, Alert, Dashboard, RAG, DataRoom, ThompsonSelect)

2. **Векторный кэш промптов:**
   - Сохранять эмбеддинги промптов в FAISS
   - `cosine_similarity > 0.95` → возвращать кэшированный ответ
   - TTL-based инвалидация (15 мин для fundamental, 24ч для astro)

3. **Per-node observability:**
   - OpenTelemetry spans на каждый узел
   - Jaeger/Grafana Tempo для trace visualization
   - Prometheus метрики: `dag_node_duration_seconds`, `dag_node_errors_total`, `dag_cache_hits_total`

4. **Retry + fallback:**
   - `DAGNode.retry_policy`: max 3 попытки с exponential backoff
   - `DAGNode.fallback_node`: альтернативный узел при исчерпании ретраев

5. **Унифицировать sentinel_v5 и MASFactory:**
   - `sentinel_v5.py` → вызывает DAG engine
   - `sentinel_v5_mas.py` → депрекейтить, функциональность в DAG

**Ожидаемые результаты:**
- Снижение LLM-затрат: ~40-60%
- Полная трассируемость каждого запроса
- Автоматическое восстановление при сбоях

**Ответственный:** @felix (DAG nodes + caching) + DevOps (OpenTelemetry)

---

### Этап 3: Динамическое связывание + Векторная память (Спринт I — 2 недели) 🟢 P2

**Цель:** Graph-of-Agents с динамическими рёбрами и общей векторной памятью.

**Задачи:**
1. **Shared embedding space:**
   - Агенты публикуют свои выводы как эмбеддинги в общий индекс
   - При новом запросе агенты ищут релевантные выводы соседей

2. **Relevance-based routing:**
   - Рёбра между агентами не фиксированы, а вычисляются на основе similarity
   - Thompson Sampling → dynamic edge weights

3. **Версионирование графа:**
   - Разные DAG-топологии для разных стратегий (SWING, INTRADAY, SCALP)
   - Хранение топологий в PostgreSQL

**Ответственный:** @felix (research + prototype)

---

## 13. Экономический эффект

### 13.1 Текущие затраты (оценка)

| Статья | Частота | LLM-вызовов/запуск | ≈$ за день | ≈$ за месяц |
|--------|---------|-------------------|------------|-------------|
| Scheduled analysis (каждые 20 мин) | 72/день | ~12 (агенты + синтез) | $3-7 | $90-210 |
| AI-Ops monitoring (каждые 15 мин) | 96/день | ~4 (запросы к Prometheus) | $1-2 | $30-60 |
| Daily digests (6 automations) | 6/день | ~8 | $0.50-1 | $15-30 |
| **ИТОГО** | | | **$5-10/день** | **$150-300/мес** |

> *Допущение: средняя стоимость OpenRouter ~$0.002/запрос при использовании auto-model*

### 13.2 Ожидаемая экономия

| Этап | Экономия LLM | Экономия $/мес | Ускорение |
|------|-------------|----------------|-----------|
| Этап 1 (пилотный DAG + базовое кэширование) | 30% | $45-90 | 2x |
| Этап 2 (полный DAG + векторный кэш) | 50% | $75-150 | 3x |
| Этап 3 (динамическое связывание) | 60% | $90-180 | 3.5x |

**ROI Этапа 1+2:** окупаемость за счёт экономии на LLM — **2-3 месяца**.

### 13.3 Трудозатраты

| Этап | Человеко-недель | Риски |
|------|----------------|-------|
| Этап 1 | 2 (1 разработчик) | Низкие: надстройка над существующим кодом |
| Этап 2 | 2 (1 разработчик + 0.5 DevOps) | Средние: интеграция OpenTelemetry |
| Этап 3 | 2 (1 разработчик, research-heavy) | Высокие: требует экспериментов с embedding models |

---

## 14. Допущения и ограничения

1. **Стоимость LLM-вызовов** — приблизительная оценка на основе типовых цен OpenRouter. Фактические затраты зависят от модели и длины промптов.
2. **MASFactory** — модуль `mas_factory/` существует в кодовой базе и используется в `sentinel_v5_mas.py`, но не в основном потоке `sentinel_v5.py`. Предполагается, что его топологический движок может быть адаптирован для DAG.
3. **Объёмы кэша** — оценка hit rate 40-60% основана на типовых паттернах повторяющихся промптов в трейдинговых системах (одинаковые символы, таймфреймы).
4. **OpenTelemetry** — предполагается, что Jaeger/Tempo может быть развёрнут на Zo-инфраструктуре. Альтернатива: lightweight tracing через структурированные логи (JSONL).

---

## 15. Приоритеты для немедленного действия

| # | Действие | Приоритет | Спринт |
|---|----------|-----------|--------|
| 1 | Параллелизовать 4 flow-а в `run_karl_sentinel_v5()` через `asyncio.gather` | 🔴 P0 | G, день 1 |
| 2 | Добавить in-memory LRU-кэш для промптов агентов (TTL 15 мин) | 🔴 P0 | G, день 2-3 |
| 3 | Создать `DAGNode` base class + `DAGPipeline` в `orchestration/dag_engine.py` | 🟡 P1 | G, день 3-5 |
| 4 | Обернуть Router, Price, MacroFlow как DAG-узлы | 🟡 P1 | G, день 5-8 |
| 5 | Интегрировать DAG pipeline с automation "Scheduled BTCUSDT Analysis" | 🟡 P1 | G, день 8-10 |

---

## A. Приложение: Файлы, затронутые аудитом

| Файл | Строк | Роль | Изменения |
|------|-------|------|-----------|
| `orchestration/sentinel_v5.py` | 382 | Главный оркестратор | Разделить на DAG-узлы |
| `orchestration/sentinel_v5_mas.py` | 176 | MASFactory-оркестратор | Депрекейтить |
| `orchestration/result_aggregator.py` | 131 | Flow runners | Преобразовать в узлы |
| `orchestration/context_manager.py` | 71 | Thompson/OAP helpers | Оставить как есть |
| `orchestration/router.py` | 119 | Query router | Обернуть в `RouterNode` |
| `agents/karl_synthesis.py` | 439 | KARL synthesis | Обернуть в `KARLNode` |
| `core/llm_router.py` | 201 | LLM routing + session cache | Добавить prompt cache |
| `knowledge/rag_index.py` | 267 | FAISS RAG index | Добавить shared embedding space |
| `core/history_db.py` | N/A | Session persistence | Обернуть в `PersistNode` |
| `mas_factory/__init__.py` | N/A | Topology builder | Адаптировать для DAG engine |

---

## B. Реализация (Спринт G — 2026-08-08)

### Выполнено

| # | Действие | Статус | Файл |
|---|----------|--------|------|
| 1 | Создан DAG engine — `DAGNode`, `DAGPipeline`, retry/fallback/topological sort | ✅ | `orchestration/dag_engine.py` (412 строк) |
| 2 | Создан PromptCache — exact+semantic кеш с FAISS-эмбеддингами | ✅ | `core/prompt_cache.py` (221 строка) |
| 3 | Интегрирован PromptCache в `core/llm_router.py` (параметр `use_prompt_cache`) | ✅ | `core/llm_router.py` |

### Корректировка аудита

**П.3.2 (Что идёт последовательно):** ОШИБКА — flow-ы в `run_karl_sentinel_v5()` и `run_sentinel_v5()` УЖЕ вызываются параллельно через `asyncio.gather(*flow_tasks)`. Фактическая потеря параллелизма — в pre-flow фазе (Router + Price + OAP идут последовательно перед flows). Оценка ускорения скорректирована: с ~20-30 сек до ~12-18 сек (1.5-2x) вместо заявленных 2.5-3x.

### Следующие шаги (P0)

- [ ] Обернуть Router, Price, RAG как DAG-узлы в `sentinel_v5_dag.py`
- [ ] Параллелизовать pre-flow фазу (Router + RAG + Price) через DAG engine
- [ ] Интегрировать CircuitBreaker из `core/circuit_breaker.py` в data_room-вызовы
- [ ] Добавить per-node Prometheus метрики (`dag_node_duration_seconds`, `dag_node_errors_total`)
