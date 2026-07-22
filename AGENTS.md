# AstroFin Sentinel — Workspace Index

> **Status:** GA-ready | **v1.0.0-ga** tagged 2026-07-22 | **Branch:** `main`
> **Tests:** 664 passed | **Security:** 0 HIGH bandit | **Architecture:** Clean + Hub-and-Spoke

## Canonical paths

| Path | Purpose |
|------|---------|
| `astrofin-sentinel-platform/` | **Main codebase** — all production code |
| `astrofin-sentinel-platform/agents/_impl/` | Active agent implementations (18 agents) |
| `astrofin-sentinel-platform/orchestration/` | Orchestrator + broker + KARL pipeline |
| `astrofin-sentinel-platform/trading/` | Broker abstraction (PaperBroker, BinanceBroker, factory) |
| `astrofin-sentinel-platform/core/` | Domain layer (BaseAgent, belief, cache, auth) |
| `astrofin-sentinel-platform/data_room/` | External HTTP gateway (R-01) |
| `astrofin-sentinel-platform/knowledge/` | RAG index (FAISS+BM25+RRF) |
| `astrofin-sentinel-platform/tests/` | Test suite (125 files) |
| `astrofin-sentinel-platform/docs/` | Architecture docs, ADRs, reports |
| `astrofin-sentinel-platform/artifacts/best_practices/` | Extracted reusable patterns |

## Key documents

- `astrofin-sentinel-platform/AGENTS.md` — Project memory (agent weights, architecture diagrams)
- `astrofin-sentinel-platform/SOUL.md` — Philosophy, principles (R-01…R-12), anti-patterns
- `astrofin-sentinel-platform/AUDIT_REPORT.md` — Full Step 1+2 audit (661 lines)
- `astrofin-sentinel-platform/CONSOLIDATION_PLAN.md` — Roadmap to GA
- `astrofin-sentinel-platform/CONFIG.md` — Configuration reference
- `astrofin-sentinel-platform/README.md` — Getting started

## Architecture rules (non-negotiable)

1. All external HTTP → `data_room/` only (R-01)
2. No `print()` in production → use `structlog`
3. No `try/except: pass` → `log.warning(exc_info=True)`
4. Secrets → `.env` / GitHub Secrets only (R-10)
5. Submodules forbidden → all inlined (R-12)

## Related repositories (archived)

- `AstroFinSentinelV5` — archived
- `astrofin-sentinel-v5` — archived
- `ATOMFederationOS` — archived
- `astrofin-federation-stack` — active (federation layer)
- `pop-os-setup` — workstation setup scripts
