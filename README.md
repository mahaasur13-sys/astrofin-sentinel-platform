# AstroFin Sentinel Platform — Monorepo

[![CI](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml)
[![Nightly](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/nightly.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/nightly.yml)
[![Release](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/release.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/release.yml)
[![Security](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/security.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/security.yml)
[![PR Checks](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/pr-checks.yml)
[![License: All Rights Reserved](https://img.shields.io/badge/license-All%20Rights%20Reserved-red.svg)](LICENSE)

Unified monorepo aggregating three production-grade projects under one CI/CD:

| Path | Origin | Purpose |
| --- | --- | --- |
| `/` (root) | `push/` | KARL / AMRE / Astro Council — orchestration, meta-RL, web dashboard |
| `infrastructure/asurdev/` | `AsurDev/` | Home-cluster IaC, ACOS admission controllers, monitoring stack |
| `kernel/atom-federation/` | `atom-federation-os/` | Deterministic alignment kernel, formal verification, K8s operator (re-integration in progress, see [Roadmap](#roadmap--known-issues)) |
| `bridge/roma/` | `roma-execution-bridge/` | GPU execution bridge, SaaS billing, Stripe webhooks |

> **Repository structure note (2026-07):** A nested duplicate copy of the entire tree
> (`astrofin-sentinel-platform/astrofin-sentinel-platform/`) was consolidated into this single
> source of truth. Overlapping files were reverse-merged from the newer nested copy, root-only
> modules (`v6/`, `v7/`, `v8/`, `src/`, `utils/`, `settings/`) were preserved, and the `api/`,
> `web-react/`, and `telegram_bot/` directories now live at the repository root. See
> [`CONSOLIDATION_REPORT.md`](CONSOLIDATION_REPORT.md) for the full audit trail.

## Quickstart

```bash
git clone https://github.com/mahaasur13-sys/astrofin-sentinel-platform.git
cd astrofin-sentinel-platform

# Recommended (uses uv.lock)
uv sync --all-extras

# Alternative (pip + pyproject)
# pip install -e ".[dev,web]"

pytest -q
```

## Layout

```
astrofin-sentinel-platform/
├── agents/                       # KARL/AMRE agent implementations (active: agents/_impl/)
├── orchestration/                # Sentinel V5 orchestrator + meta-RL pipeline
├── core/                         # Cross-cutting primitives: logging, ephemeris, cache
├── api/                          # FastAPI REST layer (sessions list, schemas — see docs/API_SETUP.md)
├── web/                          # FastAPI dashboard (Dash/Plotly) + WebSocket
├── web-react/                    # React + TypeScript dashboard SPA (Vite, Redux)
├── telegram_bot/                 # Telegram alerts bot + notification bridge
├── tests/                        # Pytest suite (see CONTRIBUTING.md)
├── knowledge/                    # RAG index, FAISS, daily-digest pipeline
├── trading/                      # Execution adapters, broker integrations
├── meta_rl/                      # Meta-reinforcement learning, A/B testing
├── monitoring/                   # Prometheus exporter, OpenTelemetry, health endpoints
├── infrastructure/asurdev/       # Cluster IaC, ACOS admission controllers
├── kernel/atom-federation/       # Alignment + verification kernel, K8s operator
├── bridge/roma/                  # GPU execution bridge, SaaS billing
├── scripts/                      # Monorepo-level automation (DORA, audits)
├── docs/                         # Architecture, contribution, runbooks
├── audit_reports/                # CI artifacts, audit snapshots
├── .github/workflows/            # CI/CD pipelines (ci/nightly/release/security/pr-checks)
├── requirements.txt              # Core runtime deps
├── requirements.all.txt          # Dev + test + lint deps
├── pyproject.toml                # Package metadata (astrofin-sentinel-v5 5.0.0)
├── LICENSE                       # All Rights Reserved
├── CONTRIBUTING.md               # Development setup, lint, test workflow
└── README.md                     # This file
```

## CLI Examples

```bash
# KARL/AMRE Sentinel V5 — single-symbol analysis
python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING

# Run targeted agent pool
python -m orchestration.sentinel_v5_mas --symbol ETHUSDT --timeframe INTRADAY

# Web dashboard (FastAPI + Dash)
python -m web.app

# Meta-RL backtest loop
python -m meta_rl.backtest_loop --symbol BTCUSDT --horizon 24h

# Observability smoke-test
python -m monitoring.health_endpoints

# Atom-Federation kernel verification
python -m kernel.atom_federation.verification.runner

# ROMA execution bridge (local)
cd bridge/roma && uvicorn roma_execution_bridge.main:app --reload
```

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — full architecture overview
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — dev workflow (or see [`CONTRIBUTING.md`](CONTRIBUTING.md))
- [`LICENSE`](LICENSE) — usage terms
- [`docs/AGENT_REGISTRY.md`](docs/AGENT_REGISTRY.md) — agent roster & weights (KARL/AMRE)

## License

All Rights Reserved. See [LICENSE](LICENSE) for full terms.

See `docs/ARCHITECTURE.md` for deeper context.
