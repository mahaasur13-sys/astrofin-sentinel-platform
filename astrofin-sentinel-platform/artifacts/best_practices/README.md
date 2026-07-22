# AstroFin Sentinel — Best Practices Catalog

Извлечено в ходе аудита 2026-07-21. Каждый артефакт — эталонный образец паттерна, применимого в других частях проекта.

---

## `patterns/` — Архитектурные паттерны

### `circuit_breaker.py` — Circuit Breaker (ADR-001)
- **Что:** 3-phase Circuit Breaker (CLOSED → OPEN → HALF_OPEN) с per-provider изоляцией
- **Паттерн:** Resilience (Martin Fowler)
- **Особенности:**
  - `CBConfig` dataclass с настройками по умолчанию
  - `CBFailureReason` enum для категоризации ошибок
  - Half-open state с `success_threshold` для безопасного восстановления
  - In-flight request tracking во избежание thundering herd
- **Где применять:** Все внешние HTTP-запросы, WebSocket-подключения, вызовы LLM API

### `ephemeris_decorator.py` — Graceful Degradation Decorator
- **Что:** `@require_ephemeris` — блокирует работу агента при отсутствии Swiss Ephemeris
- **Паттерн:** Decorator + Graceful Degradation
- **Особенности:**
  - Type-safe: `ParamSpec` + `TypeVar` для сохранения сигнатуры
  - `functools.wraps` для корректного `__name__` и `__doc__`
  - `EphemerisUnavailableError` — typed exception
  - `try/except ImportError` для опциональной зависимости
- **Где применять:** Любой опциональный компонент (GPU, LLM, внешняя API)

---

## `agents/` — Агентные паттерны

### `types.py` — Unified Agent Types
- **Что:** `AgentResponse`, `TradingSignal`, `Signal` — единый интерфейс для всех агентов
- **Паттерн:** Data Transfer Object (DTO) + Composite
- **Особенности:**
  - `Signal.score` property — numeric mapping для weighted calculation
  - `TradingSignal.from_agents()` — композитный сигнал из нескольких агентов
  - `AgentResponse` включает `confidence`, `reasoning`, `metadata`
  - `datetime.now().isoformat()` как default_factory
- **Где применять:** Все агенты должны возвращать `AgentResponse`

### `metrics.py` — Prometheus Metrics Factory
- **Что:** `@track_agent_metrics` декоратор + factory для Counter/Histogram
- **Паттерн:** Decorator + Factory + Prometheus naming convention
- **Особенности:**
  - Имена метрик: `sentinel_{agent_snake}_runs_total`, `sentinel_{agent_snake}_latency_seconds`
  - Lazy registration (создаются при первом вызове)
  - Labelled by `signal` для анализа по сигналам
  - Документированы два паттерна использования (A и B)
- **Где применять:** Каждый новый агент, любой измеримый метод

---

## `core/` — Core-утилиты и инфраструктура

### `cache.py` — Async Cache с Fallback
- **Что:** `RedisCache` — асинхронный кэш с in-memory fallback
- **Паттерн:** Repository + Fallback
- **Особенности:**
  - `redis.asyncio` для асинхронных операций
  - In-memory dict при недоступности Redis
  - Prometheus метрики: `CACHE_HITS`, `CACHE_MISSES`
  - TTL для fallback-записей
- **Где применять:** RAG retrieval, API-запросы, конфигурации

### `reward.py` — Bayesian Reward Calibration
- **Что:** `RewardCalibrator` — платформ-скейлинг + ECE tracking + drawdown penalty
- **Паттерн:** Bayesian Calibration + EMA Smoothing
- **Особенности:**
  - `CalibrationMetrics` dataclass — ECE, reliability_diagram
  - EMA smoothing: `alpha * current + (1-alpha) * previous`
  - `FalseCorrelationDetector` — выявляет переобучение на шум
  - `DrawdownTracker` — penalty за просадки
- **Где применять:** Meta-RL, оценка моделей, A/B тестирование

### `settings.py` — Secret-безопасные Settings
- **Что:** Pydantic Settings с `SecretStr` и `repr()`-маскированием
- **Паттерн:** Secure Configuration
- **Особенности:**
  - `SecretStr` для всех чувствительных полей
  - `repr()` маскирует поля `*_key`, `*_secret`, `*_password`
  - `validate_startup()` — проверка всех secrets при старте
  - `env-aware`: development vs production validation
- **Где применять:** Любой модуль с API-ключами

### `logging_utils.py` — Structured Logging с Redaction
- **Что:** Regex-based redaction API-ключей, JWT, email в логах
- **Паттерн:** Secure Logging
- **Особенности:**
  - `_API_KEY_RE`, `_JWT_RE`, `_EMAIL_RE`, `_HEX_SECRET_RE` — компилированные regex
  - `redact_secrets()` и `redact_structured()` для структурированных логов
  - Интеграция с `structlog`
- **Где применять:** Все модули, где пишутся логи с потенциально чувствительными данными
