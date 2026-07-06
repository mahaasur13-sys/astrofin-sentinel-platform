# AstroFin Sentinel Platform — Monorepo

[![CI](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml)
[![Nightly](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/nightly.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/nightly.yml)
[![Release](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/release.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/release.yml)
[![Security](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/security.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/security.yml)
[![PR Checks](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/pr-checks.yml)
[![License: All Rights Reserved](https://img.shields.io/badge/license-All%20Rights%20Reserved-red.svg)](LICENSE)

Unified monorepo aggregating the AstroFin Sentinel V5 platform, formal verification kernel, and execution bridge under a single CI/CD and dependency surface.

## Components

| Path | Origin | Status | Purpose |
| --- | --- | --- | --- |
| `agents/`, `core/`, `orchestration/`, `meta_rl/`, `trading/`, `web/`, `monitoring/`, `knowledge/` | AstroFin Sentinel V5 | **native** | KARL/AMRE agent pool, Sentinel V5 orchestrator, meta-RL pipeline, FastAPI dashboard, RAG index, execution adapters |
| `src/bridges/roma/` | `roma-execution-bridge` (inlined from `main`) | **inlined in v1.0.0** | GPU execution bridge, SaaS billing, Stripe webhooks, scheduler, deploy manifests |
| `src/formal_verification/` | `atom-federation-os` (inlined from `main`) | **inlined in v1.0.0** | Deterministic alignment kernel, formal verification, K8s operator, cluster/agent runtime, SBS |
| `AsurDev/` | `AsurDev` | **submodule (pending inline)** | Home-cluster IaC, ACOS admission controllers, monitoring stack — to be inlined in v1.1 |
| `home-cluster-iac/` | `home-cluster-iac` | **submodule (pending inline)** | Ansible roles, Terraform, K8s manifests — to be inlined in v1.1 |
| `astrofin-sentinel-v5/` | `astrofin-sentinel-v5` | **submodule (pending inline)** | Legacy v5 snapshot — to be archived/inlined in v1.1 |
| `integrations/gitagent/` | `integrations/gitagent` | **submodule (pending inline)** | GitAgent MCP / agent validator — to be inlined in v1.1 |

## Quickstart

```bash
git clone https://github.com/mahaasur13-sys/astrofin-sentinel-platform.git
cd astrofin-sentinel-platform
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

The editable install exposes both the root packages (`agents`, `core`, `orchestration`, `meta_rl`, `trading`, `web`, `data_provider`) and the inlined Tier A packages (`src.bridges.roma`, `src.formal_verification`).

## Layout

```
astrofin-sentinel-platform/
├── agents/                       # KARL/AMRE agent implementations (active: agents/_impl/)
├── orchestration/                # Sentinel V5 orchestrator + meta-RL pipeline
├── core/                         # Cross-cutting primitives: logging, ephemeris, cache, aspects
├── web/                          # FastAPI dashboard (Dash/Plotly) + WebSocket
├── tests/                        # Pytest suite (see CONTRIBUTING.md)
├── knowledge/                    # RAG index, FAISS, daily-digest pipeline
├── trading/                      # Execution adapters, broker integrations
├── meta_rl/                      # Meta-reinforcement learning, A/B testing
├── monitoring/                   # Prometheus exporter, OpenTelemetry, health endpoints
├── src/
│   ├── bridges/roma/              # ← inlined from roma-execution-bridge (main)
│   │   ├── roma_execution_bridge/
│   │   ├── deploy/               # (unique to roma, not in upstream)
│   │   ├── saas/                 # (unique to roma, not in upstream)
│   │   ├── charts/               # Helm charts
│   │   └── pyproject.toml
│   └── formal_verification/      # ← inlined from atom-federation-os (main)
│       ├── alignment/            # ADLR, BCIL, MCPC, DRL, Orchestration
│       ├── sbs/                  # State-Based Scheduler + Runtime Enforcer
│       ├── cluster/, federation/, proof/, chaos/, ...
│       └── pyproject.toml
├── scripts/                      # Monorepo-level automation (DORA, audits, validate_agent.py)
├── docs/                         # Architecture, contribution, runbooks
├── audit_reports/                # CI artifacts, audit snapshots
├── .github/workflows/            # CI/CD pipelines (ci/nightly/release/security/pr-checks/...)
├── AsurDev/                      # git submodule (pending inline)
├── home-cluster-iac/             # git submodule (pending inline)
├── astrofin-sentinel-v5/         # git submodule (pending inline)
├── integrations/gitagent/        # git submodule (pending inline)
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

# ROMA execution bridge (inlined package, local dev)
cd src/bridges/roma && uvicorn roma_execution_bridge.main:app --reload

# Atom-Federation SBS CLI (inlined package)
cd src/formal_verification && sbs --help
```

## Tier A Merge (v1.0.0)

Two submodules were inlined into `src/` and removed from `.gitmodules` in the v1.0.0 unification branch:

- **`roma-execution-bridge`** → `src/bridges/roma/` (272 source files + 218 unique artifacts from `astrofin-fed/` orphan: `deploy/`, `saas/`, `charts/`, `gpu_worker/`, `k8s/`, etc.)
- **`atom-federation-os`** → `src/formal_verification/` (494 files: `alignment/`, `sbs/`, `cluster/`, `federation/`, `proof/`, `chaos/`, `drl/`, `orchestration/`, etc.)

Hard-coded `sys.path.insert(0, '/home/workspace/atom-federation-os')` references in test files were rewritten to relative `Path(__file__).resolve().parent / '...'` paths so the package works from any checkout location.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — full architecture overview
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — dev workflow (or see [`CONTRIBUTING.md`](CONTRIBUTING.md))
- [`LICENSE`](LICENSE) — usage terms
- [`docs/AGENT_REGISTRY.md`](docs/AGENT_REGISTRY.md) — agent roster & weights (KARL/AMRE)

## License

All Rights Reserved. See [LICENSE](LICENSE) for full terms.

See `docs/ARCHITECTURE.md` for deeper context.
