# Dashboard Evaluation: LangGraph + n8n

## Decision

Use **LangGraph as the primary orchestration and state-management layer** and introduce **n8n only as an integration boundary**. AstroFin already has a Python multi-agent council, conditional routing, KARL arbitration, volatility-aware risk, audit records, and checkpoint/history requirements. These are graph-state concerns: the workflow must preserve typed state, run specialist agents in parallel, expose conflicts, apply one synthesis/arbitration step, and resume safely after interruption. LangGraph fits that execution model; a dashboard should observe and control the graph rather than become a second orchestrator.

n8n is useful for the surrounding data plane, not for the trading decision graph. Use it for scheduled market/news/calendar ingestion, provider webhooks, normalization, persistence, and Telegram/email/Slack notifications. Keep external HTTP behind AstroFin's `data_room/` boundary, validate n8n payloads before persistence, attach source timestamps and provenance, and never allow an n8n workflow to bypass KARL, risk limits, or the audit trail. This hybrid minimizes coupling: Python owns decisions; n8n owns transport and event plumbing; the dashboard reads durable state and streams graph progress.

## Suggested Architecture

```mermaid
graph LR
    subgraph Ingestion["n8n integration boundary"]
        Schedules[Schedules and webhooks]
        Providers[Market data, news, SEC, calendars]
        Normalize[Validate, normalize, provenance]
        Schedules --> Providers --> Normalize
    end

    Store[(PostgreSQL / SQLite fallback\nmarket data + checkpoints + audit JSONL)]
    Normalize --> Store

    subgraph Decision["LangGraph decision graph"]
        Router[Query and symbol router]
        Council[AstroCouncil supervisor]
        Parallel[Fundamental | Quant | Macro | Technical | Sentiment | Bull/Bear]
        Synthesis[Synthesis + KARL arbitration]
        Risk[Risk engine and position sizing]
        Audit[Decision audit + checkpoint]
        Router --> Council --> Parallel --> Synthesis --> Risk --> Audit
    end

    Store --> Router
    Audit --> Store
    Audit --> Dashboard
    Risk --> Dashboard
    Dashboard[Dashboard: state, conflicts, signals, risk, history]
    Dashboard -->|human approval / replay| Router
```

## Integration Points

1. **State schema:** extend the existing sentinel state with `data_provenance`, `agent_responses`, `conflicts`, `risk_decision`, and `decision_id`.
2. **Parallel council:** invoke specialist agents concurrently and retain every response; do not silently average away disagreement.
3. **Arbitration:** route all conflicts through Synthesis/KARL, then apply the volatility risk engine before displaying an actionable signal.
4. **Persistence:** checkpoint LangGraph state and write the final `DecisionRecord`; n8n writes only validated input events and delivery status.
5. **Dashboard:** show graph run status, per-agent evidence/confidence, conflict resolution, risk regime, stop levels, and replayable historical decisions.

## Rollout

- **Now:** consolidate the agent graph and checkpointing around the existing Python orchestration; expose read-only run state to the dashboard.
- **Next:** add one n8n workflow for market/news/calendar ingestion and one notification workflow. Treat n8n as replaceable and keep provider adapters out of agents.
- **Before production execution:** add idempotency keys, source freshness checks, secret isolation, failure/retry policies, and an explicit human-approval gate for any order-producing path.

**Recommendation:** LangGraph-first, n8n-at-the-edge. Do not move agent arbitration or risk governance into n8n.
