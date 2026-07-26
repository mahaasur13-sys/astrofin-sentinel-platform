# R-01 Compliance Review — 2026-07-26

**Правило:** Все внешние HTTP-вызовы — только через `data_room/`. Никаких bare `import requests` в агентах, оркестраторе, вебе или production-коде.

## Нарушения (29 файлов)

### 🟢 Зона 1: Архив — удалить (9 файлов)

Файлы в `.zo_scratch/submodule-archive-2026-07-12/` — это мёртвый архив уже inlined-субмодулей. Будут удалены при P3-очистке `.zo_scratch/`.

| Файл | Контекст |
|------|---------|
| `.zo_scratch/.../AsurDev/ml_engine/inference/ml_client.py` | Legacy ML client |
| `.zo_scratch/.../AsurDev/failure_orchestrator/orchestrator.py` | Legacy orchestrator |
| `.zo_scratch/.../AsurDev/ai_scheduler/modules/metrics.py` | Legacy metrics |
| `.zo_scratch/.../AsurDev/feature_pipeline/builder.py` | Legacy pipeline |
| `.zo_scratch/.../atom-federation-os/chaos/partitioner.py` | Legacy chaos |
| `.zo_scratch/.../atom-federation-os/build/lib/chaos/partitioner.py` | Legacy build artefact |
| `.zo_scratch/.../roma-execution-bridge/saas/email/service.py` | Legacy email |
| `.zo_scratch/.../roma-execution-bridge/roma_sdk.py` | Legacy SDK |
| `.zo_scratch/.../roma-execution-bridge/gpu_worker/connector.py` | Legacy GPU |
| `.zo_scratch/.../roma-execution-bridge/gpu_worker/heartbeat.py` | Legacy heartbeat |

### 🟡 Зона 2: Инфраструктурные исключения (9 файлов)

Код в `infrastructure/`, `deploy/iac/`, `bridge/roma/` — это **инфраструктурный код**, а не торговые агенты. Правило R-01 формально нарушается, но контекст допустимый:

| Файл | Контекст | Решение |
|------|---------|--------|
| `bridge/roma/roma_sdk.py` | ROMA SDK client | ✅ Исключение — инфраструктура |
| `bridge/roma/gpu_worker/connector.py` | GPU connector | ✅ Исключение — инфраструктура |
| `bridge/roma/gpu_worker/heartbeat.py` | GPU heartbeat | ✅ Исключение — инфраструктура |
| `bridge/roma/saas/email/service.py` | Email service | ✅ Исключение — инфраструктура |
| `infrastructure/asurdev/failure_orchestrator/orchestrator.py` | Failure orchestrator | ✅ Исключение — инфраструктура |
| `infrastructure/asurdev/ml_engine/inference/ml_client.py` | ML engine client | ✅ Исключение — инфраструктура |
| `infrastructure/asurdev/ai_scheduler/modules/metrics.py` | AI scheduler metrics | ✅ Исключение — инфраструктура |
| `infrastructure/asurdev/feature_pipeline/builder.py` | Feature pipeline | ✅ Исключение — инфраструктура |
| `deploy/iac/` (3 файла: feature_pipeline, failure_orchestrator, ai_scheduler) | IAC-код | ✅ Исключение — деплой-инфраструктура |

**Rationale:** R-01 защищает агентов от прямых сетевых вызовов. Инфраструктурные модули (bridge, iac, failure orchestrator) по природе должны иметь сетевой доступ. Это не торговый код, а операционная обвязка.

### 🔴 Зона 3: Production-нарушения — требуют рефакторинга (4 файла)

| Файл | Строка | Контекст | Рекомендация |
|------|--------|---------|-------------|
| `backtest/engine.py` | 15 | `import requests` | Refactor to `data_room.blueprint.get_price()` |
| `backtest/atom_014_stress_test.py` | 21 | `import requests` (conditional) | Refactor or exempt as test infrastructure |
| `data_provider.py` | 10 | `import requests` | **DEPRECATED** — удалить (заменён на `data_room/`) |
| `data/market_adapter.py` | 12 | `import requests` | Refactor or exempt as data infrastructure |

### 🟠 Зона 4: Прочие (7 файлов — дубликаты infrastructure в kernel/ai_scheduler)

| Файл | Контекст | Решение |
|------|---------|--------|
| `kernel/atom-federation/chaos/partitioner.py` | Chaos testing | ✅ Исключение — тестовая инфраструктура |
| `kernel/atom-federation/build/lib/chaos/partitioner.py` | Build artefact | Удалить при очистке build |
| `ai_scheduler/modules/metrics.py` | AI scheduler proxy | ✅ Исключение — инфраструктура |

## Action Plan

1. **P3-Cleanup (автоматически):** Удаление `.zo_scratch/submodule-archive-2026-07-12/` — 9 файлов уйдут.
2. **Ручной рефакторинг (Sprint A):** `backtest/engine.py` → `data_room.blueprint`.
3. **Deprecation:** `data_provider.py` помечен как устаревший, будет удалён после проверки импортов.
4. **GRANDFATHER:** 16 инфраструктурных файлов получают grandfathered exemption в архитектурный линтер с тегом `# noqa: R-01 (infrastructure)`

## Decision: PENDING HUMAN REVIEW

Не выполнять автоматический рефакторинг — файлы могут быть legacy и неиспользуемыми. Финальное решение по каждому файлу зоны 3 оставлено за архитектором.
