# Best Practices Artifacts — AstroFin Sentinel V5

Извлечено в ходе Step 2 аудита (2026-07-27). Рекомендуется для переиспользования в смежных проектах.

| # | Артефакт | Источник | Назначение |
|---|----------|----------|------------|
| `01` | `require_ephemeris_decorator.py` | `agents/_impl/ephemeris_decorator.py` | Декоратор для астро-агентов: проверяет доступность Swiss Ephemeris, graceful fallback если офлайн |
| `02` | `minimal_base_agent.py` | `agents/base_agent.py` | Минимальная реализация BaseAgent с AgentResponse — шаблон для новых агентов |
| `03` | `trading_signal_aggregation.py` | `agents/_impl/types.py` | `TradingSignal.from_agents()` — агрегация мультиагентных сигналов с весами и conflict resolution |
| `04` | `data_room_blueprint.py` | `data_room/blueprint.py` | Паттерн RAG-first сетевого шлюза: единая точка HTTP-вызовов, circuit breaker, resolver chain |
| `05` | `circuit_breaker.py` | `data_room/circuit_breaker.py` | Production-grade Circuit Breaker для внешних API с half-open recovery |
| `06` | `require_auth_decorator.py` | `web/middleware/__init__.py` | Декоратор `@require_auth` для Flask/FastAPI роутов с audit trail |
| `07` | `volatility_regime.py` | `core/volatility.py` | Динамический risk engine: 4 режима волатильности → адаптивный position sizing |
| `08` | `decision_audit_trail.py` | `agents/_impl/amre/audit.py` | DecisionRecord + AuditLog: полный audit trail мультиагентных решений (JSONL) |

## Паттерны для переиспользования

- **RAG-first шлюз** (#04, #05): все внешние HTTP-вызовы через единый resolver chain
- **Unified Agent Interface** (#02, #03): `AgentResponse` + `TradingSignal` — контракт между агентами
- **Decorator-based cross-cutting** (#01, #06): аспекты (auth, ephemeris) через декораторы, не наследование
- **Audit trail** (#08): каждое решение мультиагентного совета записывается в JSONL для последующего обучения
