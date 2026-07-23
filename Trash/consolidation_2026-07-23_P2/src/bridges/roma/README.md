# ROMA — Distributed Execution Platform

> **ROMA = Closed-Loop Compute Economy OS**
> Autonomous GPU workload orchestration with cost-aware scheduling, event sourcing, and multi-tenant SaaS control plane.

[![CI](https://github.com/mahaasur13-sys/roma-execution-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaasur13-sys/roma-execution-bridge/actions)

---

## 🚀 Quick Start

```bash
pip install typer rich requests pyyaml plotly dash
python roma_cli.py run "train YOLOv8"
python roma_cli.py explain "train YOLOv8"
```

---

## ⚡ Commands

```bash
roma run "train YOLOv8"    # Execute job
roma explain "train model"  # Cost preview  
roma logs --job-id <id>     # View logs
roma status                 # System status
```

---

## 🏗️ Architecture

```
CLI → Input Contract → ROMA Planner → Event Sourcing
    → Decision Gate (cost + quota) → Raft Consensus
    → Plugin Executor → GPU Scheduler → K8s/Ray
    → Billing → Dashboard
```

---

## 📦 Core Modules

| Module | Purpose |
|--------|---------|
| `auth/` | API keys + OAuth2 + RBAC + audit |
| `cost/` | Cost prediction + decision gate |
| `plugins/` | Plugin API + ML training plugin |
| `scheduler/` | GPU-aware job scheduler |
| `durability/` | Event store + event sourcing |
| `ha/` | Raft consensus + leader election |
| `k8s/` | K8s CRD + operator SDK |
| `billing/` | Metering + Stripe + invoicing |
| `tenancy/` | Multi-tenant isolation |
| `dashboard/` | Plotly Dash UI |

---

## 🔑 Features

- **GPU-aware scheduling** — automatic CUDA node selection
- **Cost prediction** — estimated cost before execution
- **Event-sourced execution** — full audit trail, deterministic replay
- **Raft consensus** — fault-tolerant multi-node coordination
- **Plugin ecosystem** — extensible via `IPlugin` interface
- **Multi-tenant SaaS** — org/project hierarchy with quota isolation
- **Billing engine** — metering, Stripe, invoice ledger
- **Enterprise RBAC** — role-based access with org scopes
- **CLI + Dashboard** — human CLI and visual UI

---

## 📐 System Classes

| Class | Description |
|-------|-------------|
| **Class A** | Deterministic execution kernel (strict contract) |
| **Class B** | Observable OS with full audit trail |
| **Class C** | Closed-loop compute economy (cost → billing) |

---

## 📄 Version

**v1.0.0** — First stable release (2026-04-17)  
See [CHANGELOG.md](./CHANGELOG.md) for release history.
