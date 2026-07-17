# ADD-2026-07-12-B1 — Findings при перемещении root-файлов

**Дата:** 2026-07-12
**Ветка:** `chore/phase-b1-docs-paths-orphans`
**Commits на текущий момент:** c19aeb9 (README), b5273d5 (AGENTS)

---

## ✅ Завершённые шаги

### Шаг 2 — README.md (commit c19aeb9)
Заменено 7 вхождений: 3 в таблице origins, 3 в дереве каталогов, 1 в quickstart (`cd bridge/roma` → `cd src/bridges/roma`). Diff чистый.

### Шаг 3 — AGENTS.md (commit b5273d5)
Одно вхождение: `cd /home/workspace/AstroFinSentinelV5` → `cd /home/workspace/Projects/asp-canonical-real`.

### Шаг 4 — shell-скрипты
**F-11 закрыт без действий.** `scripts/bootstrap.sh` и `scripts/deploy-roma.sh` отсутствуют. Широкий grep `infrastructure/asurdev\|kernel/atom-federation\|bridge/roma` по `scripts/` дал 0 совпадений — старых путей в shell-скриптах нет.

---

## ⚠️ Шаг 5 — БЛОКИРУЮЩАЯ ПРОБЛЕМА: F-13 содержит ошибки в маппинге

Прежде чем перемещать файлы, **прошу подтверждения** — F-13 в задании некорректен для **3 из 6 файлов**.

### Аудит root-файлов (что есть на самом деле)

| Файл | Размер | Это тест? | Импортируется? | Назначение |
|---|---|---|---|---|
| `test_aspects.py` | 321 B | ✅ да (smoke) | нет | Top-level скрипт, использует `core.aspects/ephemeris` |
| `health_endpoints.py` | 8.2 KB | ❌ **НЕТ** | нет (но упоминается в README как `python -m monitoring.health_endpoints`) | **Production FastAPI app** (10+ эндпоинтов, lifespan, middleware, prometheus exporter) |
| `langgraph_schema.py` | 15.6 KB | ❌ нет | нет | LangGraph state graph + Thompson Sampling, runtime module |
| `muhurtha.py` | 4.7 KB | ❌ нет | нет | Астрологический модуль (Panchanga/Ascendant), runtime-библиотека |
| `FINAL_INTEGRATION_TEST.py` | 12.9 KB | ⚠️ **полу-тест** | нет | Standalone CLI: `asyncio.run(main())`, 10 функций `test_*` через `print_test`/цветной вывод. **Не pytest.** |
| `data_provider.py` | 15.0 KB | ❌ нет | **никем не импортируется** | Unified OHLCV fetcher — действительно orphan по факту |

### Почему маппинг F-13 опасен

**1. `health_endpoints.py` → `tests/unit/health_endpoints.py`** ❌ ОПАСНО
- Файл **не является тестом** — это runtime FastAPI app (`@app.get("/health")`, `@app.get("/metrics")`, `@app.on_event("startup")`).
- В README сказано: `python -m monitoring.health_endpoints` (хотя текущий путь другой — это и есть F-11/маршрутизация, но факт: это прод-сервис, не тест).
- Перенос в `tests/unit/`:
  - сломает любой скрипт/докер, который импортирует его из корня;
  - pytest может попытаться его собрать как test module;
  - **исчезнет runtime-сервис из прод-зоны**.

**Правильное место:** `monitoring/health_endpoints.py` (папка `monitoring/` отсутствует — нужно создать, см. README: `monitoring/                       # Prometheus exporter, OpenTelemetry, health endpoints`).

**2. `FINAL_INTEGRATION_TEST.py` → `tests/e2e/test_aspects.py`** ❌ ОПАСНО
- Это **не `test_aspects`**, а комплексный integration скрипт для всех подсистем (sentinel_v5, A/B testing, и т.д.).
- Имя `test_aspects.py` уже занято в `tests/`? Проверю — в `tests/e2e/` есть `test_api_endpoints.py`, но не `test_aspects`. Тем не менее **переименование теряет смысл**: разработчик будет искать `aspects` в e2e, а найдёт integration.
- Файл **не pytest-стиль** (`asyncio.run(main())`, `print_test` с цветами) — pytest его не подхватит как тест.
- **Семантически правильнее:** `tests/integration/test_final_integration.py` (папка существует, см. `tests/integration/`).

**3. `muhurtha.py` → `orchestration/muhurtha.py`** ⚠️ спорно
- `muhurtha.py` — астрологический модуль, не orchestration. По смыслу ближе к `core/` (где живут `aspects.py`, `ephemeris.py`).
- Не критично, но **нелогично** — `muhurtha` ничего не оркеструет, а вычисляет.

**4. `langgraph_schema.py` → `tools/langgraph_schema.py`** ⚠️ спорно
- `langgraph_schema` — runtime state graph для `sentinel_v5`, а не "tool".
- Логичнее: `orchestration/langgraph_schema.py` (рядом с `sentinel_v5.py`).

### Что реально безопасно переносить (без дополнительных уточнений)

- `test_aspects.py` → `tests/unit/test_aspects.py` ✅ (реальный smoke-тест, без импортов извне)
- `data_provider.py` → `tools/data_provider.py` ✅ (никем не импортируется, делаем по алгоритму с временным re-export — но в данном случае re-export не нужен, т.к. импортов нет)

---

## 🛑 Запрос подтверждения

Прежде чем продолжить, нужны указания по **F-13**:

**Вариант A (безопасный — только то, что в задании буквально):**
- Перенести как написано, приняв риск поломки импортов прод-сервиса `health_endpoints.py`.
- **Не рекомендую.**

**Вариант B (исправленный маппинг по фактическому назначению):**
| Файл | Куда |
|---|---|
| `test_aspects.py` | `tests/unit/test_aspects.py` |
| `data_provider.py` | `tools/data_provider.py` (с re-export) |
| `health_endpoints.py` | `monitoring/health_endpoints.py` (создать `monitoring/__init__.py`) |
| `FINAL_INTEGRATION_TEST.py` | `tests/integration/test_final_integration.py` |
| `muhurtha.py` | `core/muhurtha.py` (рядом с `core/aspects.py`, `core/ephemeris.py`) |
| `langgraph_schema.py` | `orchestration/langgraph_schema.py` |

**Вариант C (минимальный — только 100% безопасные):**
- `test_aspects.py` → `tests/unit/test_aspects.py`
- `data_provider.py` → `tools/data_provider.py`
- Остальные 4 файла — оставить в корне до следующего ADD, требующего отдельного решения.

---

## Текущий статус репо

```
Branch: chore/phase-b1-docs-paths-orphans
On top of: 36bb943 (master)
Commits ahead: 2 (c19aeb9 README, b5273d5 AGENTS)
Modified: 0 (всё закоммичено)
Untracked: docs/audit/ (отчёт, не коммитим)
```

Жду решения по F-13, прежде чем продолжить.
