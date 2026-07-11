# Текущее состояние проекта

## ✅ Стабильные компоненты
- **Агенты:** 18 из 20 полностью реализованы.
- **RAG-ретривер:** FAISS-индексы для астрологии, технического анализа, трейдинга.
- **Мета-RL движок:** EvolutionEngine + walk-forward валидация.
- **KARL синтез:** 13-шаговый пайплайн с Q-обучением.
- **Risk Engine V2:** kill-switch, контроль экспозиции, корреляций.
- **Safety Gate:** композиция ModeEnforcer → RiskEngineV2 → SanityChecker.
- **CI/CD:** тесты, линтинг, покрытие (основа заложена).
- **Мониторинг:** Prometheus + Grafana + алерты.

## 🔨 В разработке (заглушки)
- `agents/_impl/macro_agent.py` — MacroAgent (возвращает NEUTRAL).
- `agents/_impl/astro_council/agent.py` — AstroCouncilAgent (заглушка).

## ⚠️ Ограничения
- `data/market_adapter.py` использует только синтетические OHLCV-данные.
- Астро-агенты зависят от эфемерид (требуется `pyswisseph`).

## 📊 Тестирование
- **241 тест** в 47 файлах.
- Покрытие: >80% для core (meta_rl, trading, agents).
- CI прогоняет юнит-тесты, но пока без PostgreSQL.

## 🔜 Ближайшие шаги
- Завершить MacroAgent и AstroCouncilAgent.
- Подключить живые рыночные данные (Binance).
- Добавить PostgreSQL в CI.
- Усилить безопасность и документирование.

---

## Updates from Phase 1 (architecture overhaul)

# Status — AstroFin Sentinel V5

> **Last updated:** 2026-06-02
> **Source of truth:** This file. When in doubt, `docs/STATUS.md` wins.
> **Symbols:** ✅ Ready · 🟡 In Progress · 🛠 Planned · ❌ Deprecated

---

## 1. Agents

| Agent | Domain | Status | Path | Notes |
|-------|--------|:------:|------|-------|
| AstroCouncil | astro | ✅ | `agents/_impl/astro_council/agent.py` | Coordinator of astro sub-agents |
| BradleyAgent | astro | ✅ | `agents/_impl/bradley_agent.py` | Bradley S&P seasonality |
| GannAgent | astro | ✅ | `agents/_impl/gann_agent.py` | Gann angles & time/price |
| CycleAgent | astro | ✅ | `agents/_impl/cycle_agent.py` | Dominant cycle detection |
| ElectoralAgent | astro | ✅ | `agents/_impl/electoral_agent.py` | Muhurta / Choghadiya |
| TimeWindowAgent | astro | ✅ | `agents/_impl/time_window_agent.py` | Multi-TF entry windows |
| FundamentalAgent | fundamental | ✅ | `agents/_impl/fundamental_agent.py` | P/E, MVRV, valuation |
| MacroAgent | macro | ✅ | `agents/_impl/macro_agent.py` | VIX, DXY, Fed rates |
| QuantAgent | quant | ✅ | `agents/_impl/quant_agent.py` | ML, vol forecasting |
| OptionsFlowAgent | options | ✅ | `agents/_impl/options_flow_agent.py` | Unusual activity |
| SentimentAgent | sentiment | ✅ | `agents/_impl/sentiment_agent.py` | News, social |
| TechnicalAgent | technical | ✅ | `agents/technical_agent.py` | RSI, MACD, BB |
| BullResearcher | research | ✅ | `agents/_impl/bull_researcher.py` | Bullish narrative |
| BearResearcher | research | ✅ | `agents/_impl/bear_researcher.py` | Bearish narrative |
| MLPredictorAgent | quant | ✅ | `agents/_impl/ml_predictor_agent.py` | ML price prediction |
| MarketAnalyst | technical | ✅ | `agents/_impl/market_analyst.py` | Market structure |
| InsiderAgent | fundamental | ✅ | `agents/_impl/insider_agent.py` | Insider activity |
| ElliotAgent | technical | ✅ | `agents/_impl/elliot_agent.py` | Elliot Wave |
| RiskAgent | risk | ✅ | `agents/_impl/risk_agent.py` | Position sizing |
| SynthesisAgent | synthesis | ✅ | `agents/_impl/synthesis_agent.py` | Conflict resolver |

> **All 20 agents Ready.** Archived duplicates in `agents/_archived/` (not active).

---

## 2. Core infrastructure

| Component | Status | Path | Notes |
|-----------|:------:|------|-------|
| `BaseAgent` contract | ✅ | `core/base_agent.py` | `AgentResponse`, `SignalDirection` |
| `require_ephemeris` decorator | ✅ | `agents/_impl/ephemeris_decorator.py` | Fails fast if `pyswisseph` missing |
| `RAGRetriever` | ✅ | `knowledge/rag_retriever.py` | FAISS-backed |
| Metrics single source of truth | ✅ | `meta_rl/metrics.py` | Re-exported by `tools/metrics_server.py` |
| History DB (SQLite) | ✅ | `core/history_db.py` | R-08 |
| Dynamic risk engine (R-07) | ✅ | `core/volatility.py` | Volatility-regime position sizing |
| Auth (`@require_auth`) | ✅ | `core/auth.py` | Bearer token |
| Rate limiting | ✅ | `core/rate_limit.py` | Token bucket |
| Tracing (OpenTelemetry) | ✅ | `core/tracing.py` | |
| Caching | ✅ | `core/cache.py` | |
| Safe JSON | ✅ | `core/safe_json.py` | |
| Checkpointing | ✅ | `core/checkpoint.py` | |
| AMRE framework | ✅ | `agents/_impl/amre/` | ATOM-KARL-009..015 |
| KARL post-processing | ✅ | `karl_synthesis.py` | |
| Decision Audit Trail | ✅ | `agents/_impl/amre/audit.py` | `DecisionRecord`, `AuditLog` |
| Continuous backtest | ✅ | `agents/_impl/amre/backtest_loop.py` | ATOM-KARL-010 |
| **Data Room** | 🟡 | `data_room/` | Phase 1 of this plan |
| Event bus (planned) | 🛠 | — | Q4 2026 |
| PostgreSQL + pgvector | 🛠 | — | See `knowledge/DB_ARCHITECTURE_PROMPT.md` |

---

## 3. Orchestration

| Component | Status | Path | Notes |
|-----------|:------:|------|-------|
| `asyncio.gather` fan-out | ✅ | `orchestration/sentinel_v5.py` | Current production path |
| `langgraph_schema.py` StateGraph | 🟡 | `langgraph_schema.py` | Experimental, conditional flows |
| Event-driven orchestrator | 🛠 | — | Q4 2026 |
| KARL-integrated synthesis | ✅ | `karl_synthesis.py` | ATOM-013 |

---

## 4. Web / API

| Endpoint | Status | Path | Notes |
|----------|:------:|------|-------|
| `/api/health` | ✅ | `web/app.py` | |
| `/api/live/*` | ✅ | `web/app.py` | Live trading controls |
| `/metrics` (Prometheus) | ✅ | `tools/metrics_server.py` | Port 9100 |
| Data Room endpoints | 🟡 | `data_room/blueprint.py` | Phase 1 of this plan |
| Public landing page | ✅ | `web/app.py` | |

---

## 5. Tooling

| Tool | Status | Path | Notes |
|------|:------:|------|-------|
| `pre-commit` | ✅ | `.pre-commit-config.yaml` | ruff, bandit, hooks |
| `scripts/validate_agent.py` | 🟡 | `scripts/validate_agent.py` | Phase 2 of this plan |
| `scripts/architecture_linter.py` | 🛠 | `scripts/architecture_linter.py` | Phase 2 of this plan |
| `tools/healthcheck.py` | ✅ | `tools/healthcheck.py` | Pre-flight checks |
| `tools/db_monitor.py` | ✅ | `tools/db_monitor.py` | |
| `tools/nightly_export.py` | ✅ | `tools/nightly_export.py` | Top-strategy export |
| `tools/thompson_cli.py` | ✅ | `tools/thompson_cli.py` | Bandit tuning CLI |
| `tools/metrics_server.py` | ✅ | `tools/metrics_server.py` | |

---

## 6. CI / CD

| Workflow | Status | Path | Notes |
|----------|:------:|------|-------|
| `ci.yml` | ✅ | `.github/workflows/ci.yml` | tests + lint |
| `quality-gate.yml` | 🛠 | `.github/workflows/quality-gate.yml` | Phase 2 of this plan |
| Architecture lint in CI | 🛠 | — | Phase 2 of this plan |
| Coverage ≥ 85% gate | 🛠 | — | Phase 2 of this plan |
| Doc-change warning | 🛠 | — | Phase 2 of this plan |

---

## 7. Documentation

| Doc | Status | Path | Notes |
|-----|:------:|------|-------|
| `docs/ARCHITECTURE.md` | ✅ | `docs/ARCHITECTURE.md` | **This plan, Phase 1** |
| `docs/CONTRIBUTING.md` | ✅ | `docs/CONTRIBUTING.md` | **This plan, Phase 1** |
| `docs/STATUS.md` | ✅ | `docs/STATUS.md` | **This plan, Phase 1** |
| `docs/KNOWN_ISSUES.md` | ✅ | `docs/KNOWN_ISSUES.md` | **This plan, Phase 1** |
| `docs/BLOG.md` | ✅ | `docs/BLOG.md` | **This plan, Phase 1** |
| `docs/ARCHITECTURE_OVERVIEW.md` | ✅ | legacy | Keep for now |
| `docs/MIGRATION_GUIDE.md` | ✅ | legacy | |
| `docs/architecture/` (D2 sources) | 🛠 | — | Q3 2026 |
| `docs/monitoring/` (dashboards) | ✅ | `docs/monitoring/` | Grafana JSONs |

---

## 8. Roadmap (next 90 days)

1. **Q3 2026** — Data Room phase 2: real-time conflict resolution via Kafka.
2. **Q3 2026** — Agent hot-reload via entry points (no more manual registry edit).
3. **Q3 2026** — Full TypeScript dashboard rewrite (drop Plotly Dash).
4. **Q4 2026** — Event bus migration; `asyncio.gather` deprecated.
5. **Q4 2026** — PostgreSQL + TimescaleDB + pgvector cutover.

---

## 9. Health snapshot

- **Tests:** _see `pytest -q` output in CI_
- **Coverage:** _see `coverage report` in CI_
- **Last green commit:** _see `git log -1 --oneline`_
- **Lighthouse / dashboards:** _see `docs/monitoring/`_