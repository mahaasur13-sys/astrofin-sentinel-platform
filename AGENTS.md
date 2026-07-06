# AstroFin Sentinel V5 — Project Memory

**Status:** ✅ Production-Beta (2026-03-26)
**Architecture:** RAG-First + LangGraph + Multi-Agent + Hybrid Signal
**Pattern:** Internal Board of Directors (Совет Директоров)

---

## 2026 Hybrid Signal Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║            ASTROFIN SENTINEL v5 — HYBRID SIGNAL ARCHITECTURE         ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   User Query ──► Router ──► Parallel Agent Council ──► Synthesis        ║
║                                   │                    │             ║
║         ┌──────────┬──────────────┬┴──────┬───────────┐  │             ║
║         ▼          ▼              ▼       ▼           ▼             ║
║    ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐      ║
║    │FUNDAMENT│ │  MACRO   │ │ QUANT   │ │OPTIONS │ │SENTIMENT │      ║
║    │ 20%    │ │   15%    │ │  20%    │ │  15%   │ │   10%    │      ║
║    └─────────┘ └──────────┘ └─────────┘ └────────┘ └──────────┘      ║
║                           │                    │                        ║
║                           ▼                    ▼                        ║
║                    ┌──────────────────────────────┐                   ║
║                    │     SYNTHESIS AGENT (100%)    │                   ║
║                    │     AstroCouncil = Coordinator │                   ║
║                    └──────────────────────────────┘                   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Agent Board — Final Weights

| Агент | Вес | Ответственность | Реализация |
|-------|-----|----------------|------------|
| **FundamentalAgent** | **20%** | Фундаментальный анализ (P/E, MVRV, revenue growth, valuation) | `agents/_impl/fundamental_agent.py` |
| **QuantAgent** | **20%** | ML-модели, бэктестирование, предсказание волатильности | `agents/_impl/quant_agent.py` |
| **MacroAgent** | **15%** | Макроэкономика (VIX, DXY, Fed rates, геополитика) | `agents/_impl/macro_agent.py` |
| **OptionsFlowAgent** | **15%** | Анализ опционного потока, unusual activity, gamma exposure | `agents/_impl/options_flow_agent.py` |
| **SentimentAgent** | **10%** | Анализ новостей, Reddit, X, StockTwits | `agents/_impl/sentiment_agent.py` |
| **TechnicalAgent** | **10%** | Технический анализ (RSI, MACD, Bollinger) — как фильтр | `agents/technical_agent.py` |
| **BullResearcher** | **5%** | Бычий нарратив + сильные астрологические факторы | `agents/_impl/bull_researcher.py` |
| **BearResearcher** | **5%** | Медвежий нарратив + рисковые факторы | `agents/_impl/bear_researcher.py` |
| **ElectoralAgent** | **3%** | Muhurta timing — сканирование окон входа по Choghadiya/Nakshatra | `agents/electoral_agent.py` |
| **BradleyAgent** | **3%** | Модель Брэдли — сезонность S&P 500 + планетарные аспекты | `agents/_impl/bradley_agent.py` |
| **TimeWindowAgent** | **2%** | Мульти-таймфрейм окна (4H/1D/1W) + астро тайминг | `agents/_impl/time_window_agent.py` |
| **GannAgent** | **3%** | Углы Ганна (1×1, 1×2), квадрат цены и времени, временные кластеры | `agents/_impl/gann_agent.py` |
| **CycleAgent** | **5%** | Доминантные циклы (20/40/80 дней), фазы, поворотные точки + астроциклы | `agents/_impl/cycle_agent.py` |
| **ИТОГО** | **100%** | | |

> **Примечание 1:** 7 корневых `agents/*.py` дублей архивированы в `agents/_archived/`. Активные реализации — только в `agents/_impl/`.

> **Примечание 2:** `AstroCouncil` — координатор, а не голосующий агент. Собирает данные от Astro-суб-агентов (BradleyAgent, ElectoralAgent, TimeWindowAgent, GannAgent, CycleAgent) и объединяет их через `TradingSignal.from_agents()`. Astro-блок суммарно получает ~16% (3+3+2+3+5).

---

## Astro-Sub-Agents Detail (AstroCouncil sub-ecosystem)

```
agents/_impl/astro_council/
└── agent.py        ← AstroCouncilAgent (координатор астро-блока)
                       Вызывает Swiss Ephemeris, затем параллельно
                       запускает все Astro-суб-агенты и объединяет
                       результат через TradingSignal.from_agents()
```

**AstroCouncil** (`agents/_impl/astro_council/agent.py`, 228 строк) отличается от `agents/astro_council_agent.py` тем, что:

| | `agents/astro_council_agent.py` | `agents/_impl/astro_council/agent.py` |
|---|---|---|
| **Роль** | Stub-обёртка, регистрирует суб-агентов через `_register_sub_agents()` | Полная реализация — `AstroCouncilAgent` с `run()` и `_call_ephemeris()` |
| **Импорты суб-агентов** | Из `agents.*` (дубли) | Из `agents._impl.*` (активные) |
| **Astro-расчёт** | Делегирует | Напрямую вызывает `core.ephemeris` |
| **`run_astro_council()`** | Нет | Есть — convenience runner для оркестратора |

AstroCouncil использует веса:

```python
HYBRID_WEIGHTS = {
    "Fundamental": 0.20, "Macro": 0.15, "Quant": 0.20,
    "OptionsFlow": 0.15, "Sentiment": 0.10, "Technical": 0.10,
    "BullResearcher": 0.05, "BearResearcher": 0.05,
}
```

При этом Astro-суб-агенты (Bradley, Electoral, TimeWindow, Gann, Cycle) **взвешиваются отдельно** внутри `TradingSignal.from_agents()` через свой `astro_weights` dict.

---

## Conflict Resolution

**Никогда не игнорировать ни один источник.**

| Конфликт | Правило |
|----------|---------|
| Astro ↔ Fundamental+Quant | Astro вес −30%, Fundamental +18%, Quant +12% |

Если астрология противоречит фундаменталу и quant — снижаем вес астрологии.

---

## Астрологический фактор в каждом агенте

Каждый агент использует `@require_ephemeris` декоратор и включает 15–30% астрологический бонус:

| Агент | Astro Weight |
|-------|-------------|
| FundamentalAgent | ~30% (Jupiter, Venus) |
| MacroAgent | ~20% (Saturn, Jupiter) |
| QuantAgent | ~20% (ephemeris-based) |
| OptionsFlowAgent | ~20% (Mercury, Venus, Jupiter) |
| SentimentAgent | ~20% (Moon, Venus) |
| TechnicalAgent | ~15% (Mars, Moon) |
| BradleyAgent | ~50% (планетарные аспекты) |
| GannAgent | ~40% (астро временные даты) |
| CycleAgent | ~40% (астроциклы Jupiter/Saturn) |

---

## Agent Implementation Files

```
agents/
├── base_agent.py              ← BaseAgent (AgentResponse, SignalDirection)
├── synthesis_agent.py          ← SynthesisAgent (100% coordinator)
├── astro_council_agent.py      ← AstroCoordinator stub (registers sub-agents)
├── electoral_agent.py          ← 3% — Muhurta / electional timing
├── fundamental_agent.py        ← ARCHIVED (duplicate)
├── macro_agent.py              ← ARCHIVED (duplicate)
├── quant_agent.py              ← ARCHIVED (duplicate)
├── options_flow_agent.py       ← ARCHIVED (duplicate)
├── sentiment_agent.py           ← ARCHIVED (duplicate)
├── technical_agent.py           ← 10% — Technical analysis
├── market_analyst.py           ← Market structure
├── bull_researcher.py          ← ARCHIVED (duplicate)
├── bear_researcher.py          ← ARCHIVED (duplicate)
├── directional_agents.py       ← Direction helpers
├── _archived/                  ← 7 архивных дублей
│   ├── fundamental_agent_root.py
│   ├── macro_agent_root.py
│   ├── quant_agent_root.py
│   ├── options_flow_agent_root.py
│   ├── sentiment_agent_root.py
│   ├── bull_researcher_root.py
│   └── bear_researcher_root.py
└── _impl/                     ← ЕДИНСТВЕННЫЕ активные реализации
    ├── fundamental_agent.py    ← 20%
    ├── macro_agent.py          ← 15%
    ├── quant_agent.py          ← 20%
    ├── options_flow_agent.py   ← 15%
    ├── sentiment_agent.py      ← 10%
    ├── bull_researcher.py      ← 5%
    ├── bear_researcher.py      ← 5%
    ├── bradley_agent.py         ← 3% — Bradley seasonality model
    ├── gann_agent.py            ← 3% — Gann angles & time/price
    ├── cycle_agent.py          ← 5% — Market cycle analysis
    ├── time_window_agent.py    ← 2% — Multi-TF entry windows
    ├── astro_council/agent.py  ← AstroCouncilAgent (full impl)
    ├── ml_predictor_agent.py    ← ML price prediction
    ├── risk_agent.py           ← Risk management
    ├── insider_agent.py        ← Insider activity
    ├── elliot_agent.py         ← Elliot Wave analysis
    ├── types.py                ← AgentResponse, TradingSignal, SignalDirection
    └── ephemeris_decorator.py  ← @require_ephemeris decorator
```

---

## Core Modules

```
core/
├── ephemeris.py          ← Swiss Ephemeris wrapper (PlanetPosition, NatalChart)
├── aspects.py           ← Aspects engine (conjunction, sextile, square, trine, opposition)
├── history_db.py        ← SQLite session persistence
├── volatility.py         ← Volatility regime engine (dynamic risk)
└── checkpoint.py        ← State checkpointing
```

### `core/aspects.py` (2026-03-26)

Calculates angular relationships between planets. Works with `core/ephemeris.py` output.

```python
from core.ephemeris import get_planetary_positions
from core.aspects import calculate_aspects, AspectsEngine

# One-shot
report = calculate_aspects(positions)

# Configurable
engine = AspectsEngine(orbs={AspectType.SQUARE: 10.0}, include_minor=True)
report = engine.compute(positions)
```

**Aspect types:** Conjunction (0°), Sextile (60°), Square (90°), Trine (120°), Opposition (180°), plus optional minor aspects.

---

## Data Sources

| Source | Purpose | API |
|--------|---------|-----|
| CoinGecko | Crypto metadata, prices | Free |
| Binance | OHLCV data | Free |
| Swiss Ephemeris | Planetary positions | License (sweph) |
| SEC EDGAR | 13F filings | Free |
| Fear & Greed Index | Sentiment | Free |
| Yahoo Finance | VIX, DXY, Gold | Free |
| Polygon.io | Options flow (future) | Paid |

---

## AMRE Modules (ATOM-KARL Framework)

```
agents/_impl/amre/
├── audit.py          ← ATOM-KARL-009: DecisionRecord + AuditLog
├── backtest_loop.py  ← ATOM-KARL-010: ContinuousBacktest
├── counterfactual.py
├── ensemble_selection.py
├── grounding.py
├── hierarchical_policy.py
├── karl_integration.py ← ATOM-012: AMRE post-processing + delisted fallback
├── oap_optimizer.py  ← ATOM-KARL-010: KPI Control Loop
├── replay_buffer.py
├── reward.py         ← ATOM-012: RewardCalibrator, FalseCorrelationDetector, DrawdownTracker
├── self_question.py
├── similarity.py
├── trajectory.py
└── uncertainty.py
```

### ATOM-KARL-009: Decision Audit Trail

**Full `DecisionRecord` schema:**
```python
DecisionRecord {
    decision_id, timestamp, session_id
    symbol, price, timeframe, regime, state_hash
    top_trajectories: [TrajectorySnapshot]
    selected_ensemble: [EnsembleMember]
    q_values, q_star, advantage
    uncertainty_aleatoric, epistemic, total
    confidence_raw, confidence_final
    confidence_adjustments: [str]
    final_action: LONG/SHORT/NEUTRAL
    position_pct
    kpi_snapshot: KPISnapshot
}
```

**AuditLog features:**
- `record()` — добавить DecisionRecord
- `find_by_state_hash()` — воспроизвести конкретное решение
- `analyze_drift()` — анализ OAP drift (деградирует ли система)
- `export_json()` / `import_json()` — сериализация

### ATOM-KARL-010: Backtest-as-a-Service

**ContinuousBacktest loop:**
```python
for t in historical_data:
    state = build_state(t)
    decision = agent.run(state)
    reward = evaluate_future(t, horizon=H)
    buffer.add(decision, reward)
```

**Features:**
- Walk-forward validation
- Rolling window continuous backtest
- OOS evaluation на каждом шаге
- Q* evolution tracking
- KPI Control Loop:
  - `if kpi["uncertainty"] > 0.6: increase_ttc_depth()`
  - `if kpi["entropy"] < 0.3: boost_exploration()`
  - `if kpi["oos_fail_rate"] > 0.4: tighten_grounding()`

### KPI Control State

```python
KPIControlState {
    current_ttc_depth: int
    current_exploration_rate: float
    current_grounding_strength: float
    uncertainty_avg, entropy_avg, oos_fail_rate
    control_history: [actions applied]
}
```

---

## Session History (R-08)

Every `run_sentinel_v5()` call is automatically persisted to `core/history.db` (SQLite).

```python
from core.history_db import save_session, get_session, list_sessions, session_stats
```

---

## R-07: Dynamic Risk Engine (Volatility-Adjusted Position Sizing)

Every call computes dynamic `risk_pct` based on market volatility regime.

| Regime | ATR% | risk_pct | Kelly mult | Conf drop |
|--------|------|----------|-----------|-----------|
| LOW | <1.5% | 3.0% | 1.0× | 0 |
| NORMAL | 1.5–3% | 2.0% | 0.75× | 0 |
| HIGH | 3–5% | 1.0% | 0.50× | −10 |
| EXTREME | ≥5% | 0.5% | 0.20× | −25 + AVOID |

---

## Backtest & Metrics

Module: `backtest/metrics_agent.py`

```python
from backtest.metrics_agent import MetricsAgent, BacktestRun

agent = MetricsAgent()
agent.record_run(BacktestRun(...))
runs = agent.list()
summary = agent.summary()
```

Tests: `backtest/test_metrics_agent.py` — 10/10 passing ✅

---

## Usage

```bash
cd /home/workspace/AstroFinSentinelV5
python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING
```

---

## TODO

- [x] Implement all agents with proper weights
- [x] Update SynthesisAgent with 2026 hybrid weights
- [x] Add FundamentalAgent, MacroAgent, QuantAgent, OptionsFlowAgent
- [x] Add SentimentAgent, TechnicalAgent, Bull/Bear Researchers
- [x] Add conflict resolution (Astro vs Fundamental+Quant)
- [x] **R-07: Dynamic risk_pct based on volatility regime**
- [x] **R-08: Persistent session history (SQLite)**
- [x] **R-09: AgentResponse — unified interface**
- [x] **core/aspects.py — AspectsEngine (2026-03-26)**
- [x] **Deduplicate agents — archive 7 root duplicates (2026-03-26)**
- [x] **Add weights for ElectoralAgent, BradleyAgent, TimeWindowAgent, GannAgent, CycleAgent (2026-03-26)**
- [x] **ATOM-KARL-009: Decision Audit Trail**
- [x] **ATOM-KARL-010: Backtest-as-a-Service + KPI Control Loop**
- [x] **ATOM-012: Enhanced KARL — reward calibration, delisted fallback, grounding integration**
- [x] **ATOM-013: Full KARL integration in sentinel_v5.py (KARLSynthesisAgent)**
- [x] **ATOM-015: KARL CLI integration, dashboard, JSONL persistence, HTML reports, continuous backtest command**
- [ ] Connect real data APIs (Polygon, Unusual Whales, SEC EDGAR)
- [ ] Add Telegram bot for alerts
- [ ] Build RAG index (FAISS/Chroma)
- [ ] Add visualizations
- [x] **ATOM-017: Full agent pools (MACRO + ASTRO + TECHNICAL)** — 8 agents running
- [ ] DB Migration: SQLite → PostgreSQL + TimescaleDB + pgvector (see `knowledge/DB_ARCHITECTURE_PROMPT.md`)

---

## Monorepo Migration v1.0.0 (2026-07-06)

Unified 12+ repos into single master (commit `b6574c2`).

### Tier A Integration (inline)

| Path | Source | Status |
|------|--------|--------|
| `src/bridges/roma/` | `main:bridge/roma` (roma-execution-bridge inline) | ✅ done (commit 7d1bb60) |
| `src/formal_verification/` | `main:kernel/atom-federation` (atom-federation-os inline) | ✅ done (commit e23b072) |

Install both as editable packages:
```bash
cd src/bridges/roma && pip install -e .[dev]
cd src/formal_verification && pip install -e .[dev]
```

### Imports

```python
# Tier A imports (after pip install -e . in both src/ subdirs)
from roma_execution_bridge.bridge import StripeBridge
from alignment.adlr import ADLRecoveryOrchestrator
from sbs.schema_validator import validate_state
```

### Remaining Submodules (4)

- `AsurDev` (kebab-case kept) - inlined in v1.0.1
- `home-cluster-iac` - inlined in v1.0.1
- `integrations/gitagent` - inlined in v1.0.1
- `astrofin-sentinel-v5` - inlined in v1.0.1

### Path Fixes (commit da3ef41)

Replaced 5 hard-coded `/home/workspace/atom-federation-os` paths with `Path(__file__).resolve().parent` relative paths in:
- `src/formal_verification/alignment/test_adlr.py`
- `src/formal_verification/alignment/test_bcil.py`
- `src/formal_verification/sbs/tests/test_sbs_contract.py`
- `src/formal_verification/sbs/tests/test_sbs_runtime.py`
- `src/formal_verification/cluster/node/node.py`

Test results after fix: 18 + 5 + 19 = 42 passed.

### Tier B/C Cleanup

Not migrated: `AstroFinSentinelV5/`, `AsurDev/`, `home-cluster-iac/`, `astrofin-sentinel-v5/`, `data_provider/`, `knowledge/`, `observability/`, `training/`. These remain in `main` branch only and will be archived in v1.0.1.

### Backups

- `backup/master-pre-migration` (39c15c4) - master before migration
- `backup/main-pre-deprecation` (994fcd7) - main snapshot
- `backup/atomos-after-merge` (b6574c2) - after Tier A + path fixes
- `/home/workspace/snapshots/2026-07-06-pre-migration/` - tar.bz2 + bundle backups


---

## 🤖 AI Agent Rules

1. **Virtual Environment**: All commands and scripts must be executed inside the project's venv (`source venv/bin/activate`).
2. **Active Modules**: Only use agent implementations from `agents/_impl/`. Do not import from `agents/_archived/`.
3. **Pre-Flight Healthcheck**: Before making changes or running the system, execute `python tools/healthcheck.py` and ensure it passes (exit code 0). If critical checks fail, notify the user and halt.
4. **Port Conflict Resolution**: Before starting the dashboard, check port 8050 (`ss -tlnp | grep 8050`). Kill any stale process occupying it.
5. **Dependency Management**: New third-party packages must be added to `requirements.txt` and recorded in `progress.md`.
6. **PostgreSQL Fallback**: If PostgreSQL is unavailable, the system may fallback to SQLite. The healthcheck will attempt `docker-compose up -d postgres redis` if Docker is present.

### CodeRabbit Review Contract

7. **CodeRabbit Review Contract**: PRs trigger CodeRabbit via `.coderabbit.yaml` (Russian, assertive). CodeRabbit checks **architectural reasoning** (R1–R9 alignment, KNOWN_ISSUES.md P1 blockers); pre-commit handles **syntactic** checks (Ruff, Bandit, detect-secrets, architecture_linter.py). Never duplicate pre-commit logic in CodeRabbit instructions. See `docs/CODE_REVIEW.md`.
8. **Architecture linter is the source of truth**: For new agents, run `python scripts/validate_agent.py agents/_impl/new_agent.py` before requesting a PR review. All 9 checks must pass.
9. **Quarterly review cycle**: The `.coderabbit.yaml` rule set is reviewed quarterly (next: 2026-09-02) to align with ADR review cadence in `docs/ARCHITECTURE.md`.

---

## CI Checks