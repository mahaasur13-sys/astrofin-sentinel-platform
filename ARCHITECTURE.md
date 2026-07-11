# AstroFin Sentinel V5 — Architecture Reference

> **Version:** 5.0.0
> **Last updated:** 2026-06-02
> **Audience:** Every engineer contributing to AstroFin Sentinel V5
> **Inspired by:** BlackRock Aladdin engineering principles — One BlackRock Rule, Data Room culture, federated ownership, and explicit architectural decision records.

---

## Table of Contents

1. [Mission & non-goals](#1-mission--non-goals)
2. [Top-level architecture](#2-top-level-architecture)
3. [DDD bounded contexts](#3-ddd-bounded-contexts)
4. [Data Room — the One BlackRock Rule](#4-data-room--the-one-blackrock-rule)
5. [Plugin architecture: `BaseAgent` & `AgentResponse`](#5-plugin-architecture-baseagent--agentresponse)
6. [Orchestration: asyncio.gather vs LangGraph vs event bus](#6-orchestration)
7. [Conflict resolution policy](#7-conflict-resolution-policy)
8. [Key architectural decisions (ADRs)](#8-key-architectural-decisions-adrs)
9. [Observability & metrics](#9-observability--metrics)
10. [Security & secrets](#10-security--secrets)
11. [Graceful degradation contract](#11-graceful-degradation-contract)
12. [Roadmap](#12-roadmap)

---

## 1. Mission & non-goals

### Mission

Build a **modular, federated, multi-agent** algorithmic trading platform where each agent owns a clearly bounded **domain**, communicates through a shared `AgentResponse` contract, and reads all external data through a single **Data Room**. The system must:

- Be **decomposable** — adding an agent is one PR, not a refactor.
- Be **observable** — every agent emits metrics, every decision is auditable.
- Be **degradable** — if any source is down, the system produces a *lower-confidence* signal, not a crash.
- Be **backtestable** — every component has a deterministic in-memory path so a year of OHLCV can be replayed in minutes.

### Non-goals

- A general-purpose ML framework. We use Meta-RL selectively (`meta_rl/`); we are not PyTorch.
- A separate service per agent. We chose **in-process federation** for latency and atomic deployment. See [ADR-004](#adr-004-in-process-federation-over-microservices).
- HFT-grade microsecond latency. Our P99 budget is **5 ms** end-to-end. Below that, we'd need C++.

---

## 2. Top-level architecture

```
                         ┌────────────────────────────────────────┐
                         │  External Sources (CoinGecko, Binance, │
                         │  SEC EDGAR, Swiss Ephemeris, ...)      │
                         └────────────────────┬───────────────────┘
                                              │ (outbound only)
                                              ▼
        ╔═══════════════════════════════════════════════════════════╗
        ║                   DATA ROOM (One Rule)                    ║
        ║   data_room/blueprint.py  → Flask Blueprint               ║
        ║   data_room/inventory/    → sources / conflicts / gaps     ║
        ╚═══════════════════════════════════════════════════════════╝
                                              │ (in-process API)
                                              ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                       AGENT COUNCIL                              │
   │                                                                  │
   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐  │
   │  │ Fundamental │  │   Macro     │  │   Quant     │  │ ...    │  │
   │  │   (20%)     │  │   (15%)     │  │   (20%)     │  │        │  │
   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘  │
   │                                                                  │
   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐  │
   │  │  Astro      │  │ Sentiment   │  │ Options     │  │ Bull/  │  │
   │  │  Council    │  │   (10%)     │  │   (15%)     │  │ Bear   │  │
   │  │  (16%)      │  │             │  │             │  │ (10%)  │  │
   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘  │
   │                                                                  │
   │            ▲                  ▲                                  │
   │            │ shared RAG       │ @require_ephemeris               │
   │  ┌─────────┴──────┐  ┌────────┴────────┐  ┌────────────────┐    │
   │  │ RAG Retriever  │  │ core/ephemeris  │  │ metrics.py     │    │
   │  └────────────────┘  └─────────────────┘  └────────────────┘    │
   │                                                                  │
   │                          ▼  AgentResponse[]                     │
   │                  ┌──────────────────────────┐                    │
   │                  │   SynthesisAgent (100%)  │                    │
   │                  │   (orchestration/sentinel_v5.py)            │
   │                  └──────────────────────────┘                    │
   │                          ▼                                      │
   │                  TradingSignal (TradingSignal)                  │
   └──────────────────────────────────────────────────────────────────┘
                                              │
                          ┌───────────────────┴───────────────────┐
                          ▼                                       ▼
                 ┌──────────────────┐                  ┌──────────────────┐
                 │  Audit / KARL    │                  │  Dashboard (web) │
                 │  (audit.py,      │                  │  (Dash + React)  │
                 │   backtest_loop) │                  │                  │
                 └──────────────────┘                  └──────────────────┘
```

---

## 3. DDD bounded contexts

We partition the codebase into **6 bounded contexts** (DDD). Each context has a single owner, a public API, and is forbidden from importing across boundaries except through well-typed interfaces.

| # | Domain | Owner | Key modules | Public API | Notes |
|---|--------|-------|-------------|------------|-------|
| 1 | **Astro** | `agents/_impl/astro*` | `astro_council/`, `bradley_agent.py`, `gann_agent.py`, `cycle_agent.py`, `electoral_agent.py`, `time_window_agent.py`, `core/ephemeris.py`, `core/aspects.py` | `run_<agent>()` async function | **Hard rule:** every astro-touching agent must use `@require_ephemeris`. |
| 2 | **Fundamental** | `agents/_impl/fundamental_agent.py`, `agents/_impl/insider_agent.py` | `core/belief.py` | `run_fundamental_agent()`, `run_insider_agent()` | Reads from Data Room only. |
| 3 | **Macro** | `agents/_impl/macro_agent.py` | — | `run_macro_agent()` | Fed data, no scraping. |
| 4 | **Quant** | `agents/_impl/quant_agent.py`, `agents/_impl/ml_predictor_agent.py`, `meta_rl/` | `meta_rl/persistence.py`, `meta_rl/strategy_evaluator.py` | `run_quant_agent()`, `run_ml_predictor_agent()` | Backtest loop, OAP control. |
| 5 | **Risk & Trading** | `agents/_impl/risk_agent.py`, `trading/` | `core/volatility.py` | `run_risk_agent()` | **Hard rule:** risk is the only domain that may refuse a signal. |
| 6 | **Synthesis & Observability** | `agents/_impl/synthesis_agent.py`, `orchestration/`, `tools/metrics_server.py`, `web/` | `orchestration/sentinel_v5.py`, `langgraph_schema.py`, `meta_rl/metrics.py` | `run_sentinel_v5()` | The conductor. The only domain that knows about *all* others. |

### Bounded context rules

1. **Astro** code may not import from **Quant** code. (Astro is the slowest-changing domain; it should not be coupled to ML internals.)
2. **Risk** may import from anyone. Everyone else may import from Risk only via `run_risk_agent()`.
3. **Synthesis** may import from everyone. No one may import from Synthesis except `orchestration/sentinel_v5.py`.
4. The **Data Room** may not import from any agent. (One-way dependency.)

These rules are enforced by `scripts/architecture_linter.py`.

---

## 4. Data Room — the One BlackRock Rule

> **Origin:** BlackRock's "One BlackRock Rule" — no desk may have its own data version. There is exactly one canonical price for a security at a timestamp, period.
>
> **Our translation:** No agent may import `requests` and call an external API. The Data Room is the only path.

### 4.1. Why a Data Room?

Three operational failures, all in 2025, forced this:

1. **Drift:** `MacroAgent` was reading VIX from Yahoo. `SentimentAgent` was reading it from CNN. They disagreed by 4% on a high-volatility day and the resulting composite signal was uninterpretable.
2. **Rate limits:** A backtest in March 2025 hit CoinGecko's free tier mid-run. The run produced 30% missing data. We had no fall-back.
3. **Auditability:** Compliance asked "where did this price come from?" The answer was "whichever agent you ask." Unacceptable.

### 4.2. Data Room structure

```
data_room/
├── __init__.py
├── blueprint.py                 # Flask Blueprint; only place with `requests`
├── resolvers/
│   ├── __init__.py
│   ├── price_resolver.py        # CoinGecko + Binance → unified PriceTick
│   ├── macro_resolver.py        # Yahoo + Fed
│   ├── ephemeris_resolver.py    # Swiss Ephemeris + JPL fallback
│   └── fundamentals_resolver.py # SEC EDGAR + CoinGecko
├── inventory/
│   ├── sources_inventory.json   # every source, owner, rate limit, SLA
│   ├── conflict_journal.json    # who wins when they disagree (signed)
│   └── missing_context.json     # honest list of "we don't have X yet"
├── schemas/
│   ├── price_tick.json
│   ├── macro_indicator.json
│   └── ephemeris_position.json
└── tests/
    └── test_resolvers.py
```

### 4.3. The conflict journal

`inventory/conflict_journal.json` is the most important file in the system. Every time the Data Room sees two sources disagree, it writes an entry. The `ConflictResolver` reads the latest entry on every call.

```json
{
  "version": 5,
  "entries": [
    {
      "id": "CJ-2026-05-14-001",
      "symbol": "BTCUSDT",
      "field": "price",
      "sources": {
        "coingecko": 67231.00,
        "binance":   67229.50
      },
      "decision": "binance",
      "reason": "Binance is the primary venue; CoinGecko indexer lags by ~90s.",
      "decided_by": "price_resolver.py@2026-04-02",
      "ttl_days": 30
    }
  ]
}
```

The journal is append-only, signed, and reviewed weekly by the data team.

### 4.4. TopNotch-style quality control

"TopNotch" in Aladdin terminology means: every data point has a **provenance** and a **quality score**. We adopt this as:

- **Provenance** — every `PriceTick` carries `source`, `fetched_at`, `resolver_version`.
- **Quality score** — `0.0` to `1.0`; `1.0` = direct exchange feed, `0.5` = derived/index, `0.1` = last-known-good on outage.
- **Circuit breaker** — if a source's error rate > 50% over 5 minutes, it is marked `degraded` and the resolver falls back. The `degraded` flag is propagated to agents via `metadata["data_quality"]`.
    - Specifically: if a source fails 3 times in 60s, quality drops to 0.1 and the next resolver is tried.

### 4.5. Public API of the Data Room

Agents must consume data through `data_room.blueprint.get_price(symbol, asof=None)`, never via `requests.get`. The function returns a `PriceTick` and a `quality` score; the agent must propagate `quality` into its `AgentResponse.metadata["data_quality"]` so the SynthesisAgent can down-weight low-quality signals.

### 4.6. Anti-patterns

- ❌ `import requests` in any file under `agents/`.
- ❌ Hard-coding a URL or API key in an agent.
- ❌ An agent having its own SQLite cache that bypasses the inventory.
- ❌ Logging a `current_price` to `logs/` directly — the data room is the only thing that may see the raw value.

These are enforced by `scripts/architecture_linter.py::check_data_room_compliance`.

---

## 5. Plugin architecture: BaseAgent & AgentResponse

### 5.1. The contract

Every agent **must** subclass `core.base_agent.BaseAgent` and return a `core.base_agent.AgentResponse`. This is non-negotiable; it is the protocol that the SynthesisAgent can compose.

```python
class BaseAgent(ABC, Generic[T]):
    def __init__(
        self,
        name: str,
        instructions_path: str | None = None,
        domain: str | None = None,
        weight: float = 0.0,
    ): ...
    @abstractmethod
    async def run(self, state: dict) -> AgentResponse: ...
    def retrieve(self, query, domain=None, top_k=5) -> list[dict]: ...    # RAG
```

The contract deliberately exposes **less**, not more: no I/O outside of `data_room/`, no global state, no mutable defaults. This is what makes the agents composable.

### 5.2. Automatic discovery: `_discover_agents()`

A new agent is shipped in three steps:

1. Drop a file in `agents/_impl/`.
2. Register it in `agents/gitagent_registry.py:AGENT_AGENTS` with name, domain, weight, module path, and runner function name.
3. Add a row to `docs/STATUS.md`.

There is **no central `__init__.py` to edit**. The orchestrator calls `discover_agents()` which:

- Walks `agents/_impl/`,
- Imports any module with a `run_*` function,
- Validates the runner returns an `AgentResponse` instance,
- Injects it into the SynthesisAgent's domain-weighted pool.

This is the federated model. Compare to Aladdin Copilot, which uses a similar plugin model: a small registration manifest (`AGENT_AGENTS`) acts as the service catalog, while the agent code itself is a separate, independently testable unit.

### 5.3. Why federation beats a single agent

A monolithic "GPT-eats-the-world" agent is tempting. We reject it because:

- **Specialization is cheaper than generality** — `GannAgent` is 300 lines; the same logic in a prompt would be 10,000 tokens and unreliable.
- **Failure isolation** — if `SentimentAgent`'s Ollama is down, the composite signal still works with 6 of 7 agents; the missing one's weight is redistributed.
- **Testability** — a 300-line agent has a finite test surface; a prompt-driven agent is a regression test against a moving LLM target.
- **Auditability** — for compliance, we need to know *which* component said *what*, not a single opaque "the LLM said so".

---

## 6. Orchestration

### 6.1. Current: `asyncio.gather` in `sentinel_v5.py`

The current production path is intentionally simple: a fan-out `asyncio.gather` over `AGENT_AGENTS`, followed by `SynthesisAgent` collapsing the responses.

```python
async def run_sentinel_v5(query, symbol, timeframe):
    state = build_state(query, symbol, timeframe)
    responses = await asyncio.gather(*[
        run_agent(name, state) for name in registry.list()
    ])
    return SynthesisAgent().synthesize(responses, state)
```

This is **fine** for our P99 budget (5 ms × 7 agents = 35 ms parallel; we measure 22 ms in production). The reason we are looking at alternatives is **observability and back-pressure**, not latency.

### 6.2. Alternative: LangGraph `StateGraph`

`langgraph_schema.py` already exists as a parallel implementation:

```python
graph = StateGraph(SentinelState)
graph.add_node("fundamental", run_fundamental_agent)
graph.add_node("macro",       run_macro_agent)
graph.add_node("quant",       run_quant_agent)
graph.add_edge("fundamental", "synthesis")
...
```

The advantage: LangGraph gives us **conditional edges** ("if risk says AVOID, abort synthesis"), **persisted state** (so we can replay a session from a checkpoint), and **typed state schemas** (replacing our free-form `dict`).

The disadvantage: a third-party dependency, an additional abstraction layer, and worse cold-start time.

### 6.3. Roadmap: event-bus orchestration

The longer-term target is an event-bus (NATS or Redis Streams) where each agent is a worker subscribing to a `MarketState` topic. This unlocks:

- **Multi-process** agents (CPU-bound ML can run in a separate process pool).
- **Replay** — a historical `MarketState` stream drives the backtest loop without code changes.
- **Cross-language** — the `SentimentAgent` in Rust, the `QuantAgent` in Python.

We are not there yet. See [ADR-005](#adr-005-in-process-federation-over-microservices).

---

## 7. Conflict resolution policy

When two agents disagree, **never silently average**. The rules below are encoded in `agents/_impl/synthesis_agent.py`.

| Conflict | Rule |
|----------|------|
| Astro vs Fundamental+Quant | Astro weight **−30%**, Fundamental **+18%**, Quant **+12%** (rebalance to 100%). |
| Bull vs Bear | Take the one with higher `confidence`; if within 5 points, fall back to Quant. |
| Risk says AVOID | **Override** — return AVOID regardless of other signals. |
| Data quality < 0.4 for an agent's primary input | Drop that agent; redistribute its weight across the domain. |

The conflict journal (`data_room/inventory/conflict_journal.json`) is the auditable trail.

---

## 8. Key architectural decisions (ADRs)

### ADR-001 — Asynchronous-first I/O

**Context.** Trading workloads are I/O-bound (RAG, OHLCV fetches, ephemeris).
**Decision.** All agents and orchestrators use `async def`. The Flask Blueprint in `data_room/blueprint.py` is a thin sync façade over `asyncio.run`.
**Alternatives considered.** Thread pool, gevent. Rejected for debuggability.
**Trade-off.** Slightly more verbose code (`async`/`await`); in exchange, 7× higher concurrency on the same GIL.

### ADR-002 — SQLite for development, Postgres for production

**Context.** Local DX must be zero-friction; production needs concurrency.
**Decision.** Default storage is SQLite (`core/history.db`, `core/belief.db`). The `data/connections.py` layer is the single place that swaps the driver; production uses the same SQL with a Postgres URL.
**Trade-off.** Some Postgres-only features (TSDB, `pgvector`) require re-implementation in SQLite for dev. We accept the duplication for the first three milestones.

### ADR-003 — Swiss Ephemeris is hard-required, not soft

**Context.** Astro agents contribute ~16% of the composite. We could mock the ephemeris and ship "good enough" signals.
**Decision.** `@require_ephemeris` raises an `EphemerisUnavailableError` if `pyswisseph` is not importable. The SynthesisAgent catches this and down-weights Astro by 100% (i.e., effectively disables Astro agents) rather than failing the whole run.
**Trade-off.** Astro fails loud in dev if the lib is missing. This is intentional — silent degradation masked three bugs in 2025.

### ADR-004 — In-process federation over microservices

**Context.** Many-agent systems classically go to microservices (one agent per process, REST).
**Decision.** We stay in-process. `AGENT_AGENTS` is a Python dict; `run_*` is a Python function.
**Trade-off.** A bug in one agent can crash the orchestrator. Mitigation: every `run_*` is wrapped in a timeout (`asyncio.wait_for(run_*, timeout=5.0)`) and the orchestrator catches and continues.

### ADR-005 — Meta-RL only on Quant, not on Astro

**Context.** Meta-RL would in principle let agents learn their own weights.
**Decision.** Meta-RL is scoped to the **Quant** domain (`meta_rl/`). Other domains use static weights from `docs/STATUS.md`. Reason: the Astro domain is a slow-moving, low-N signal; an RL weight schedule on top of it produces overfitting, not alpha.
**Trade-off.** Static weights look less "smart". They are also more auditable and less prone to regime collapse.

### ADR-006 — Observability is a deployment gate, not a feature

**Context.** A metric added "later" is a metric that doesn't exist during the first outage.
**Decision.** Every new agent **must** export at least one Prometheus metric (`agents/.../{agent_name}_runs_total`, `..._confidence_avg`). `scripts/architecture_linter.py` enforces this. The CI fails the PR if the metric is missing.

---

## 9. Observability & metrics

### 9.1. Metrics server

`tools/metrics_server.py` (and `meta_rl/metrics.py` as the canonical source) exposes Prometheus on `:9100/metrics`.

Key metric families:

| Metric | Type | Source |
|--------|------|--------|
| `sentinel_agent_runs_total{agent, signal}` | Counter | every agent |
| `sentinel_agent_confidence_avg{agent}` | Gauge | per minute |
| `sentinel_data_room_quality{symbol, source}` | Gauge | data room |
| `sentinel_synthesis_p99_seconds` | Gauge | orchestrator |
| `sentinel_risk_overrides_total` | Counter | risk agent |

### 9.2. Structured logging

All agents log to `logs/<date>/<agent>.log` with the schema:

```json
{"ts": "2026-06-02T01:23:45Z", "level": "INFO", "agent": "QuantAgent",
 "session_id": "abc12345", "event": "run_start", "symbol": "BTCUSDT"}
```

`core/logging.py` is the single point of configuration; do not configure logging inside agents.

### 9.3. Tracing

`core/tracing.py` provides a no-op-friendly OpenTelemetry context. In dev it's a no-op; in production it ships spans to Loki.

---

## 10. Security & secrets

- All secrets live in `Secrets` (Settings → Advanced) or in `.env` for local dev.
- No secret in a Python file. `scripts/architecture_linter.py::check_secrets` will fail the CI.
- The web UI enforces `Authorization: Bearer <token>` for write endpoints (`/api/live/*`).
- Ephemeris license file is `core/ephemeris_license/` and is **never** committed (see `.gitignore`).
- The Meta-RL replay buffer (`meta_rl/replay_buffer/`) is append-only and immutable once written.

---

## 11. Graceful degradation contract

Every agent is **required** to implement the following contract:

1. If a hard dependency (ephemeris, RAG, data room) is unavailable, return `AgentResponse(signal=NEUTRAL, confidence=0, reasoning="<hard reason>")` with `metadata["degraded"]=True`.
2. The SynthesisAgent never crashes on a degraded response. It redistributes weight (see §7).
3. The orchestrator never crashes on an exception inside `run_*`. It is wrapped in `asyncio.wait_for(..., timeout=5.0)`.
4. A degraded response **must** carry `metadata["degradation_reason"]` as a machine-readable string (one of: `EPHEMERIS_UNAVAILABLE`, `DATA_ROOM_TIMEOUT`, `RAG_OFFLINE`, `ML_MODEL_NOT_LOADED`, `UNKNOWN`).

This contract is verified by `scripts/validate_agent.py`.

---

## 12. Roadmap

| Quarter | Theme | Status |
|---------|-------|--------|
| 2026 Q1 | Federated plugin architecture, Meta-RL foundation | ✅ |
| 2026 Q2 | Data Room (this document), architecture linter, agent templates | 🟡 |
| 2026 Q3 | Event-bus orchestration (NATS), Postgres + pgvector migration | 🛠 |
| 2026 Q4 | Multi-language agents (Rust for Quant), real-time compliance | 🛠 |

---

*This document is a living artifact. When you change the architecture, change this file in the same PR.*
