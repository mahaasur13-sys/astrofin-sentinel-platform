# AstroFin Sentinel V5 — DAG Architecture

**Sprint G (2026-08-08)** — DAG Multi-Agent Transition  
**Коммиты:** `3bcd3e2` → `c353d0b` → `98b6af3` → `7f5191c`  
**Файлы:** `core/dag/`, `core/cache/`, `orchestration/dag_nodes.py`, `orchestration/sentinel_v5_dag.py`

---

## Архитектурный обзор

DAG-оркестратор — надстройка над существующей архитектурой агентов. Все 12 DAG-узлов — тонкие обёртки, вызывающие существующие функции без изменения их API (`run_macro_flow()`, `SynthesisAgent.run()`, etc.).

```
Level 0                 Level 1                  Level 2      Level 3           Level 4
┌──────────┐      ┌──────────────────┐
│RouterNode│──────►│TechnicalFlowNode │──┐
└──────────┘      └──────────────────┘  │
                                         │         ┌──────────────┐   ┌──────────────────┐   ┌──────────┐
┌──────────┐      ┌──────────────────┐  ├────────►│SynthesisNode │──►│KARLPostProcess  │──►│PersistNode│
│PriceNode │──────►│MacroFlowNode     │──┤         └──────────────┘   │       Node       │   └──────────┘
└──────────┘      └──────────────────┘  │                             └──────────────────┘        │
                                         │                                                         ▼
┌──────────┐      ┌──────────────────┐  │                                                  ┌──────────┐
│ RAGNode  │──────►│AstroFlowNode     │──┤                                                  │AlertNode │
└──────────┘      └──────────────────┘  │                                                  └──────────┘
                                         │
                  ┌──────────────────┐  │
                  │ElectoralFlowNode │──┘
                  └──────────────────┘
```

---

## DAG Engine (`core/dag/`)

### `DAGNode` — базовый узел (`core/dag/node.py`)

```python
from core.dag import DAGNode, DAGContext

class MyNode(DAGNode):
    timeout_ms: float = 30_000      # таймаут на узел
    max_retries: int = 2            # количество ретраев
    backoff_base_s: float = 1.0     # база exponential backoff
    fallback_node_id: str | None = None  # альтернативный узел при ошибке

    async def run(self, ctx: DAGContext) -> dict:
        # Чтение результатов зависимых узлов
        router = ctx.get("RouterNode")
        price = ctx.get("PriceNode")

        # Бизнес-логика
        return {"result": "value"}
```

**Политика ретраев:**
- До `max_retries` попыток
- Exponential backoff: `backoff_base_s × 2^attempt`
- При исчерпании ретраев — fallback на `fallback_node_id` (если задан)
- Узел логирует `NodeResult` с флагом `ok=True/False`

**Таймауты (asyncio.wait_for):** узел прерывается через `timeout_ms` миллисекунд, бросает `asyncio.TimeoutError`.

**Важно:** дочерние классы реализуют только `run()`. Метод `execute()` вызывается `DAGPipeline`'ом и управляет retry-логикой.

### `DAGPipeline` — движок исполнения (`core/dag/pipeline.py`)

```python
from core.dag import DAGPipeline

pipeline = DAGPipeline("my_analysis")
pipeline.add_node(MyNode())
pipeline.add_node(AnotherNode(), depends_on=["MyNode"])

ctx = await pipeline.run(user_query="Analyze BTC")
```

**Алгоритм:**
1. **Регистрация узлов:** `add_node(node, depends_on=[])` — fluent API
2. **Topological sort:** вычисление уровней — `level = max(dep.level) + 1`, детекция циклов
3. **Параллельное исполнение по уровням:** каждый уровень — `asyncio.gather(*tasks)`
4. **Сбор результатов:** `DAGContext.results: dict[str, NodeResult]`

**Методы интроспекции:**
- `pipeline.describe()` — человекочитаемая топология
- `pipeline.execution_plan` — словарь `{level_N: [node_ids]}`
- `pipeline.node_ids()` — список всех id узлов
- `pipeline.get_node(node_id)` — доступ к экземпляру узла

### `DAGContext` — контекст исполнения (`core/dag/context.py`)

```python
@dataclass
class DAGContext:
    run_id: str          # UUID12
    state: dict          # Начальное состояние (user_query, symbol, timeframe, ...)
    results: dict[str, NodeResult]  # Результаты узлов по node_id
    start_time: float

    def get(node_id) -> NodeResult | None
    def set(node_id, result) -> None
    elapsed_ms: float    # Время с начала прогона
```

### `NodeResult` — выход узла

```python
@dataclass
class NodeResult:
    node_id: str
    output: Any          # Результат run()
    duration_ms: float
    error: str | None    # None = OK
    retry_count: int
    ok: bool             # error is None
```

### `DAGRunSummary` — метрики прогона (`core/dag/metrics.py`)

```python
@dataclass
class DAGRunSummary:
    run_id, name, total_ms: float
    node_results: dict[str, NodeResult]
    ok_count, fail_count: int
    bottleneck_node: tuple[str, float]    # (node_id, duration_ms)
    as_dict() -> dict                     # Сериализация для JSON/логов
```

`summarize_run(ctx, name)` — построить summary из контекста после завершения пайплайна.

---

## Кэширование (`core/cache/`)

Два уровня кэша в DAG-прогоне:

### Prompt Cache (`core/cache/prompt_cache.py`)

**Глобальный LRU-кэш промптов (500 записей):**

| Тип совпадения | Механизм | TTL |
|---------------|----------|-----|
| Exact match | MD5(prompt + model) | 15 мин (trading/fundamental), 24ч (astro) |
| Semantic match | Sentence-transformers embedding, cosine similarity > 0.95 | 15 мин |

```python
from core.cache.prompt_cache import get_prompt_cache

pc = get_prompt_cache()
cached = pc.get_exact(prompt, model="openrouter/auto")
if not cached:
    cached = pc.get_semantic(prompt)
if not cached:
    response = await call_llm(prompt)
    pc.set_exact(prompt, response, model="openrouter/auto")
    pc.set_semantic(prompt, response)

# Метрики
print(pc.stats)  # {enabled, entries, hits, misses, hit_rate, ...}

# Инвалидация
pc.invalidate(prompt)       # удалить конкретный
pc.invalidate()             # очистить всё
```

**Интеграция:** встроен в `core/llm_router.route(prompt, use_prompt_cache=True)`.

**Env vars:**
- `PROMPT_CACHE_MAX_ENTRIES` (default: 500)
- `PROMPT_CACHE_DEFAULT_TTL` (default: 300)
- `PROMPT_CACHE_ASTRO_TTL` (default: 86400)
- `PROMPT_CACHE_SEMANTIC_THRESHOLD` (default: 0.95)
- `PROMPT_CACHE_ENABLED` (default: true)

### Session RAG Cache (`core/cache/session_rag_cache.py`)

**Per-run кэш результатов FAISS-поиска:**

```python
from core.cache.session_rag_cache import get_session_rag_cache

cache = get_session_rag_cache(session_id="abc123")
cached = cache.get("Bitcoin fundamentals")
if not cached:
    result = rag.retrieve_context("Bitcoin fundamentals")
    cached = cache.set("Bitcoin fundamentals", result)
```

**Характеристики:**
- TTL: 5 минут (одна DAG-сессия)
- Max записей: 50 на сессию
- Потокобезопасный (`threading.Lock`)
- Интегрирован в `RAGNode.run()` — проверка перед каждым FAISS-запросом

---

## 12 DAG-узлов (`orchestration/dag_nodes.py`)

### Level 0 — Pre-Flow (независимые, параллельные)

| Узел | Назначение | Timeout | Retries | Вызывает |
|------|-----------|---------|---------|----------|
| `RouterNode` | Классификация запроса (rule-based) | 5s | 1 | `orchestration.router.route_query()` |
| `PriceNode` | Цена через CoinGecko | 15s | 2 | `data_room.resolvers.coingecko` |
| `RAGNode` | FAISS retrieval + session cache | 20s | 1 | `knowledge.rag_index`, `SessionRAGCache` |

**RouterNode output:**
```python
{
    "query_type": "ANALYSIS", "symbols": ["BTCUSDT"],
    "timeframe": "SWING", "include_technical": True,
    "include_astro": True, "include_electional": True,
    "birth_data": None, "confidence_threshold": 60
}
```

**PriceNode output:**
```python
{"price": 65000.0, "source": "coingecko", "symbol": "BTCUSDT"}
```

**RAGNode output:**
```python
{"context": "... retrieved text ...", "chunks": 5, "source": "cache"}
```

### Level 1 — Agent Flows (параллельные, зависят от Level 0)

| Узел | Агенты | Вызывает |
|------|--------|----------|
| `TechnicalFlowNode` | 3 технических агента | `run_technical_flow()` |
| `MacroFlowNode` | 5 макро-агентов | `run_macro_flow()` |
| `AstroFlowNode` | 5 астро-агентов (Bradley, Electoral, TimeWindow, Gann, Cycle) | `run_astro_flow()` |
| `ElectoralFlowNode` | ElectoralAgent | `run_electoral_flow()` |

Все Flow-узлы наследуют `BaseFlowNode` — общий `run()` с параллельным вызовом `asyncio.gather()` внутри flow-функций.

### Level 2 — Синтез

| Узел | Назначение | Timeout | Retries |
|------|-----------|---------|---------|
| `SynthesisNode` | Агрегация сигналов всех flow-ов | 60s | 2 |

Вызывает `SynthesisAgent.run()` с консолидацией сигналов через взвешенное голосование (Hybrid Weights: Fundamental 20%, Quant 20%, Macro 15%, Options 15%, Sentiment 10%, Technical 10%, Bull 5%, Bear 5%).

### Level 3 — KARL Post-Process

| Узел | Назначение | Timeout | Fallback |
|------|-----------|---------|----------|
| `KARLPostProcessNode` | AMRE калибровка (OAP, grounding, reward) | 60s | `SynthesisNode` |

При ошибке автоматически делегирует результат `SynthesisNode` (через `fallback_node_id`).

### Level 4 — Выходные узлы (параллельные)

| Узел | Назначение | Timeout | Примечание |
|------|-----------|---------|------------|
| `PersistNode` | Сохранение в БД | 10s | PG → fallback SQLite |
| `AlertNode` | Telegram-алерт | 10s | Только при confidence > 60% |

**PersistNode:** вызывает `core.history_db.save_session(final_data)`, возвращает `session_id`.

**AlertNode:** при `confidence >= 60` отправляет `utils.telegram_notifier.send_telegram_message()`. При отсутствии данных PersistNode молча пропускается.

---

## DAG-пайплайны (`orchestration/sentinel_v5_dag.py`)

### `build_analysis_dag()` — полный анализ

```
11 узлов, 5 уровней (на практике — 6 из-за зависимости Alert → Persist)
Level 0: RouterNode, PriceNode, RAGNode               (3 параллельно)
Level 1: TechnicalFlow, MacroFlow, AstroFlow,          (4 параллельно)
         ElectoralFlow — зависят от Level 0
Level 2: SynthesisNode — зависит от всех Flow-ов
Level 3: KARLPostProcessNode — зависит от SynthesisNode
Level 4: PersistNode — зависит от KARLPostProcessNode
Level 5: AlertNode — зависит от PersistNode
```

### `build_light_dag()` — облегчённый анализ

```
6 узлов, 4 уровня (~5-8 сек)
Level 0: RouterNode, PriceNode, RAGNode               (3 параллельно)
Level 1: MacroFlowNode — зависит от Level 0
Level 2: SynthesisNode — зависит от MacroFlowNode
Level 3: PersistNode — зависит от SynthesisNode
```

### CLI

```bash
# Полный анализ
python -m orchestration.sentinel_v5_dag "Analyze BTC" BTCUSDT SWING

# Лёгкий режим
python -m orchestration.sentinel_v5_dag "Analyze BTC" BTCUSDT SWING --light
```

### Программный вызов

```python
from orchestration.sentinel_v5_dag import run_dag_analysis

result = await run_dag_analysis(
    user_query="Analyze BTC",
    symbol="BTCUSDT",
    timeframe="SWING",
    light=False,
)
# result: {direction, confidence, risk_pct, session_id, karl_applied, elapsed_s, dag_summary}
```

---

## Как добавить новый DAG-узел

1. **Создать класс в `orchestration/dag_nodes.py`:**

```python
class NewAnalysisNode(DAGNode):
    timeout_ms: float = 30_000
    max_retries: int = 2

    async def run(self, ctx: DAGContext) -> dict:
        # Читаем данные зависимых узлов
        synthesis = ctx.get("SynthesisNode")
        if not synthesis or not synthesis.ok:
            raise ValueError("Synthesis node failed")

        data = synthesis.output
        # Бизнес-логика...
        return {"new_metric": 42}
```

2. **Зарегистрировать в пайплайне (`orchestration/sentinel_v5_dag.py`):**

```python
from orchestration.dag_nodes import NewAnalysisNode

def build_analysis_dag(name="BTCUSDT_analysis"):
    pipeline = DAGPipeline(name)
    # ... existing nodes ...
    pipeline.add_node(NewAnalysisNode(), depends_on=["SynthesisNode"])
    return pipeline
```

3. **Проверить компиляцию:**

```bash
python3 -m py_compile orchestration/dag_nodes.py
python3 -m py_compile orchestration/sentinel_v5_dag.py
```

4. **Запустить лёгкий тест:**

```bash
PYTHONPATH=/home/workspace python -m orchestration.sentinel_v5_dag "Analyze BTC" BTCUSDT SWING --light
```

---

## Метрики и наблюдаемость

### Per-node метрики (внутренние)

Каждый `NodeResult` содержит:
- `duration_ms` — время исполнения
- `error` — текст ошибки (None = OK)
- `retry_count` — количество ретраев

`DAGRunSummary` добавляет:
- `bottleneck_node` — самый медленный узел
- `ok_count` / `fail_count` — агрегированные счётчики

### Prompt Cache метрики

```python
from core.cache.prompt_cache import get_prompt_cache
pc = get_prompt_cache()
stats = pc.stats
# {enabled, entries, semantic_entries, hits, misses, hit_rate, ...}
```

### Session RAG Cache метрики

```python
from core.cache.session_rag_cache import get_session_rag_cache
cache = get_session_rag_cache(session_id)
cache.stats  # {session_id, entries, ttl_s}
```

### Grafana Dashboard

Дашборд `deploy/monitoring/grafana-cloud/dag_performance_dashboard.json` содержит 5 секций:
1. **Overview** — количество прогонов, success rate, среднее время
2. **Per-Node Latency** — длительность каждого узла (bar chart)
3. **Errors** — ошибки по узлам, retry counts
4. **Cache** — prompt cache hit rate, session RAG cache entries
5. **Bottlenecks** — самый медленный узел за прогон, тренд bottleneck-а

---

## Интеграция с Zo

Автоматизация `Scheduled BTCUSDT Analysis` (каждые 20 минут):

```bash
cd /home/workspace && PYTHONPATH=/home/workspace python -m orchestration.sentinel_v5_dag "Analyze BTC" BTCUSDT SWING
```

---

## Известные ограничения

| Ограничение | Детали | Workaround |
|------------|--------|------------|
| PostgreSQL не поднят в Zo-sandbox | PersistNode падает на PG | Автоматический fallback на SQLite (warning, не fatal) |
| FAISS ленивая инициализация | Первый RAG-запрос 5-7 сек | Прогрев при старте сервиса |
| CoinGecko rate limit | 429 при частых запросах | Retry с backoff в PriceNode |
| `sentinel_v5.py` не затронут | Старый путь работает как раньше | DAG — опциональная надстройка |

---

## Что дальше (следующий спринт)

- **P1 — OpenTelemetry:** spans на каждый DAG-узел, trace ID от RouterNode до PersistNode
- **P1 — Prometheus метрики:** `dag_node_duration_seconds`, `dag_node_errors_total`, `dag_cache_hits_total`
- **P2 — Динамическое связывание:** relevance-based routing, нефиксированные рёбра
- **P2 — Shared embedding space:** векторная память между агентами
- **P3 — Circuit Breaker:** интеграция в data_room-вызовы, альтернативные маршруты

---

## Быстрый старт

```bash
# Проверить состояние репозитория
cd /home/workspace
git log --oneline -6

# Проверить компиляцию DAG-модулей
python3 -m py_compile core/dag/__init__.py
python3 -m py_compile core/dag/node.py
python3 -m py_compile core/dag/pipeline.py
python3 -m py_compile core/cache/prompt_cache.py
python3 -m py_compile core/cache/session_rag_cache.py
python3 -m py_compile orchestration/dag_nodes.py
python3 -m py_compile orchestration/sentinel_v5_dag.py

# Запустить лёгкий DAG-тест
PYTHONPATH=/home/workspace python -m orchestration.sentinel_v5_dag "Analyze BTC" BTCUSDT SWING --light

# Инспектировать топологию
python3 -c "
from orchestration.sentinel_v5_dag import build_analysis_dag
dag = build_analysis_dag()
print(dag.describe())
print(dag.execution_plan)
"
```
