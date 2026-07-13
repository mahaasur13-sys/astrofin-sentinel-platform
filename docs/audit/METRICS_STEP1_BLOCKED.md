# Metrics Step 1 — BLOCKED: предпосылки ADD-2026-07-13 неверны

> **Date:** 2026-07-13
> **Author:** Zo (агент)
> **Status:** STOP — ожидаю решения Felix
> **Branch:** `chore/metrics-consolidation-step1` (создана, без изменений)

## TL;DR

ADD-2026-07-13 основан на трёх фактических ошибках аудита. Безопасное исполнение **невозможно** в текущей формулировке. Бэкап сделан в `/tmp/metrics-backup-2026-07-13/`. Дерево чистое, никаких коммитов нет.

## Расхождение 1: `observability/metrics.py` не мёртв

| ADD-2026-07-13 | Реальность |
|---|---|
| "21 LOC, dead" | **53 LOC**, 4 уникальные функции |
| "нет production-импортов" | Верно для production, **но** `tests/observability/test_metrics.py:8` его активно импортирует |

4 функции, которые **нигде больше не реализованы**:
- `record_agent_run(agent, signal, duration, confidence)` — другая сигнатура, нежели `agents.metrics`
- `record_data_room_resolve(...)` — data-room specific
- `time_block(label) -> elapsed` — context manager
- `with_agent_timing(agent, signal_getter, confidence_getter)` — декоратор

## Расхождение 2: сигнатуры **не** совместимы

```python
# core/metrics.py: track_agent_duration(agent_name: str) -> decorator
#   Берёт имя, возвращает декоратор. Оборачивает AGENT_DURATION (Histogram).
#   Usage: @track_agent_duration("MarketAnalyst")

# agents/metrics.py: track_agent_metrics(func: Callable) -> Callable
#   Берёт функцию, возвращает обёрнутую. Оборачивает agent_counter + agent_latency.
#   Usage: @track_agent_metrics (без аргументов)
```

Простой `from agents.metrics import track_agent_metrics as track_agent_duration` **не сработает**:
- Первый — `@track_agent_duration("MarketAnalyst")` (decorator factory)
- Второй — `@track_agent_metrics` (decorator)

Семантика различна → `market_analyst.py:13` упадёт при импорте (нужны скобки, но их нет).

## Расхождение 3: `market_analyst.py` уже использует ОБА декоратора намеренно

Файл `agents/_impl/market_analyst.py`:
- **Line 13:** `from core.metrics import track_agent_duration` — импортирован
- **Line 39:** `@track_agent_metrics` — применён
- **Line ~50 (вероятно):** `@track_agent_duration` — нужно проверить, **используется ли**

Если line 13 — dead import, то **"мёртвый код" — это import в market_analyst.py, а не в core/metrics.py!**

## Что предлагаю — 3 безопасных альтернативы

### Option A: Минимальная зачистка (РЕКОМЕНДУЮ)
- **Удалить** неиспользуемый `import track_agent_duration` из `market_analyst.py:13` (если он действительно dead)
- **Удалить** `core/metrics.py` целиком
- **Оставить** `observability/metrics.py` нетронутым (он **живой** через тесты)
- **Docstring** в `tools/metrics_server.py`
- **Риск:** нулевой. Это просто чистка dead import.

### Option B: Двухфазный консолидейшн
- **Фаза 1 (этот PR):** Добавить deprecation warnings в `core/metrics.py` и `observability/metrics.py`, **не удалять ничего**. Дать production-потребителям 1-2 спринта на миграцию.
- **Фаза 2 (следующий PR):** Удалить устаревшие модули.
- **Риск:** низкий, но **время × 2**.

### Option C: Отозвать ADD, пересмотреть аудит
- ADD отозвать, аудит переделать.
- Я составлю обновлённый `METRICS_AUDIT_REPORT.md` с **реальной** картой: какие функции кто использует, какие из них действительно дубликаты, какие — нет.
- **Риск:** нулевой, но потеря 1 итерации.

## Текущее состояние

- Ветка `chore/metrics-consolidation-step1` создана из master
- Бэкап: `/tmp/metrics-backup-2026-07-13/{core_metrics.py, observability_metrics.py, tools_metrics_server.py}.bak`
- Никаких изменений в файлах, никаких коммитов
- `git status` — clean (только неотслеживаемый `docs/audit/METRICS_AUDIT_REPORT.md`)

## Моя рекомендация

**Option A.** Идти строго по ADD опасно — сломаем `market_analyst.py`. Если ты подтверждаешь что `track_agent_duration` в market_analyst.py действительно dead — это 1 безопасный коммит: убрать dead import + удалить dead `core/metrics.py`. `observability/metrics.py` оставляем как есть.

Жду твоё решение (A / B / C / свой вариант).
