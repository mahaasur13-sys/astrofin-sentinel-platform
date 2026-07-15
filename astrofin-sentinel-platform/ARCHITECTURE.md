# Architecture - AstroFin Sentinel V5

> **Canonical repo.** Single source of truth.

## Layered Structure

```
orchestration/        - Entry points (sentinel_v5.py)
  ├── agent_layer/        - Agent implementations (active: agents/_impl/)
  ├── reasoning/         - Routing, synthesis, multi-agent coordination
agents/_impl/        - Active agent classes (FundamentalAgent, etc.)
agents/_archived/    - Deprecated duplicates (do
```

graph TD
  U[User Query] --> R[Router]
  R -->|parallel| A1[FundamentalAgent 20%]
  R -->|parallel| A2[MacroAgent 15%]
  R -->|parallel| A3[QuantAgent 20%]
  R -->|parallel| A4[OptionsFlowAgent 15%]
  R -->|parallel| A5[Sent
  A9[SynthesisAgent 100%] --> R[TradingSignal]
  R --> OUT[Order / Decision]
```

## Key Subsystems

### KOCA-AMRE (agents/_impl/amre/)
Atom-KARL continuous-backtest loop.

### Observability
- `core/logging.py` - structured logging
- `core/tracing.py` - OpenTelemetry trace context
- `deploy/monitoring/` - health, metrics, alerts

### Risk & State
- `core/volatility.py` - regime-aware risk sizing
- `core/history_db.py` - session history persistence
- `core/checkpoint.py` - state checkpointing

### Main Entry Points
- `orchestration/sentinel_v5.py`
- `web/app.py`
- `deploy.monitoring.health_endpoints`