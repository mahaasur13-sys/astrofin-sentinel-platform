# AstroFin Sentinel Platform — Architecture

> Monorepo-level architecture for the unified `astrofin-sentinel-platform` repository.

## Repository Layout

```
astrofin-sentinel-platform/
├── (root)                     ← AstroFinSentinelV5 — multi-agent trading
│   ├── agents/                ← Agent registry (KARL, AMRE, Astro Council)
│   ├── core/                  ← Core kernels (ephemeris, aspects, volatility)
│   ├── orchestration/         ← Sentinel v5 orchestrator + router
│   ├── meta_rl/               ← Meta-reinforcement learning subsystem
│   ├── web/                   ← Dash dashboard
│   ├── trading/               ← Broker integration + execution
│   └── tests/                 ← Pytest suite (50+ files)
│
├── infrastructure/asurdev/    ← Home-cluster IaC + monitoring
│   ├── acos/                  ← ACOS controller
│   ├── k8s/                   ← Kubernetes manifests
│   ├── terraform/             ← IaC
│   ├── monitoring/            ← Observability stack
│   └── l9_ebl/ l10_self_healing/ l11_verifier/   ← Self-healing layers
│
├── kernel/atom-federation/    ← ATOM alignment kernel
│   ├── alignment/             ← Alignment contracts & verification
│   ├── formal_model/          ← Formal verification artifacts
│   ├── kubernetes/            ← atom-operator CRDs
│   └── core/                  ← Federation primitives
│
├── bridge/roma/               ← ROMA execution bridge
│   ├── billing/               ← Stripe integration
│   ├── saas/                  ← Multi-tenant SaaS endpoints
│   ├── gpu_worker/            ← GPU execution layer
│   └── control_plane/         ← Reconciler
│
├── scripts/                   ← Operational scripts (dora, linters, …)
├── docs/                      ← Architecture & design docs
└── audit_reports/             ← Static-analysis & compliance reports
```

## Logical Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│  Presentation: web/ (Dash), SaaS endpoints, Grafana dashboards      │
├─────────────────────────────────────────────────────────────────────┤
│  Orchestration: orchestration/sentinel_v5.py + router + meta_rl    │
├─────────────────────────────────────────────────────────────────────┤
│  Agent Layer: agents/* — KARL/AMRE/Astro Council/Quant/Macro/...   │
├─────────────────────────────────────────────────────────────────────┤
│  Core Kernels: core/ephemeris.py · core/aspects.py · core/tracing   │
├─────────────────────────────────────────────────────────────────────┤
│  Alignment Kernel (kernel/atom-federation): formal verification     │
├─────────────────────────────────────────────────────────────────────┤
│  Execution Bridge (bridge/roma): SaaS · GPU · Billing · RBAC        │
├─────────────────────────────────────────────────────────────────────┤
│  Infrastructure (infrastructure/asurdev): IaC · observability       │
└─────────────────────────────────────────────────────────────────────┘
```

## Cross-Component Contracts

| Producer | Contract | Consumer |
|---|---|---|
| `orchestration/sentinel_v5.py` | `TradingSignal` (action, confidence, regime) | Dashboard, KARL integration |
| `agents/_impl/*` | `AgentResponse` (direction, weight, evidence) | `SynthesisAgent` |
| `kernel/atom-federation` | `AlignmentReport` (score, violations) | `bridge/roma` RBAC |
| `bridge/roma/billing` | `StripeEvent` (webhook payload) | `bridge/roma/saas` |

## Data Flow

1. User query → `orchestration/sentinel_v5.py` (router)
2. Router → parallel agents (`agents/_impl/*`)
3. Each agent → `AgentResponse` with `SignalDirection`
4. `SynthesisAgent` (100% weight) aggregates via `TradingSignal.from_agents()`
5. `core/volatility.py` computes dynamic `risk_pct`
6. `meta_rl/` updates ensemble weights (off-policy)
7. `core/history_db.py` persists session to SQLite
8. Dashboard renders signal via `web/`

## Subsystem Dependencies

- `kernel/atom-federation` is **independent** of trading layer — only consumes contracts.
- `bridge/roma` **consumes** signals via event bus; never imports from `agents/`.
- `infrastructure/asurdev` is **deploy-only** — no runtime imports.
- `orchestration/` is the **only** entry point that imports from multiple subsystems.

## Versioning

- Repo version follows SemVer on tags (`vMAJOR.MINOR.PATCH`).
- Subprojects may pin via path: `pip install -e infrastructure/asurdev`.
- API-breaking changes require an ADR in `docs/` before merge.

## CI/CD

- **CI** runs on every push & PR to `main`.
- **CD** uses Dependabot for weekly updates; releases via git tags.
- **Required checks**: pytest, flake8, bandit (high severity), radon (cyclomatic complexity).

## Observability

- Structured logging via `core/logging.py` (`structlog`).
- Tracing via `core/tracing.py` (OpenTelemetry).
- Metrics via `observability/metrics.py` (Prometheus).
- DORA metrics via `scripts/dora_metrics.py` (deployment frequency + lead time).