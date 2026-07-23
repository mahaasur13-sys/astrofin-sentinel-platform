# ROMA Changelog

## v1.0.0 (2026-04-17) — First Stable Release

**ROMA = Closed-Loop Compute Economy OS** — First production-ready version.

### Core Platform
- Execution Kernel (Class A, strict input contract)
- Plugin System (IPlugin, auto-discovery, 3 built-in plugins)
- GPU Scheduler (VRAM tracking, backpressure)
- Event Sourcing (append-only log, deterministic replay)
- Raft Consensus (leader election, log replication)
- K8s Integration (CRD, operator SDK, RayJob)
- Billing Engine (metering, Stripe, invoicing, ledger)

### Enterprise
- API Keys (scoped, HMAC, rotation)
- OAuth2 / SSO (SAML assertion)
- RBAC (org/project scopes)
- Audit Log (CSV + JSON, SIEM-ready)
- Multi-Tenant (org→project→tenant hierarchy)
- SOC2-ready controls

### Product
- CLI (run, explain, logs, status)
- Dashboard (Plotly Dash)
- Cost Explainability (alternatives, optimization hints)
- Developer Onboarding (0-to-job in 30 seconds)

### Architecture Freeze
Core kernel (Layers 1-4) frozen as of v1.0.0.
