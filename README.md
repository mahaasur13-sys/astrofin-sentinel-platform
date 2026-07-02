# AstroFin Sentinel Platform — Monorepo

[![CI](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml)
[![Nightly](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/nightly.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/nightly.yml)
[![Release](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/release.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/release.yml)
[![Security](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/security.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/security.yml)
[![PR Checks](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/pr-checks.yml)

Unified monorepo aggregating three production-grade projects under one CI/CD:

| Path | Origin | Purpose |
| --- | --- | --- |
| `/` (root) | `push/` | KARL / AMRE / Astro Council — orchestration, meta-RL, web dashboard |
| `infrastructure/asurdev/` | `AsurDev/` | Home-cluster IaC, ACOS admission controllers, monitoring stack |
| `kernel/atom-federation/` | `atom-federation-os/` | Deterministic alignment kernel, formal verification, K8s operator |
| `bridge/roma/` | `roma-execution-bridge/` | GPU execution bridge, SaaS billing, Stripe webhooks |

## Quickstart

```bash
pip install -r requirements.txt
pip install -r requirements.all.txt
pytest -q
```

## Layout

```
astrofin-monorepo/
├── infrastructure/asurdev/      # cluster IaC + side-car controllers
├── kernel/atom-federation/      # alignment + verification kernel
├── bridge/roma/                 # execution bridge & SaaS
├── scripts/                     # monorepo-level automation (DORA, audits)
├── docs/                        # architecture & contribution docs
├── audit_reports/               # CI artifacts and audit snapshots
└── .github/workflows/           # CI/CD pipelines
```

See `docs/ARCHITECTURE.md` for deeper context.
