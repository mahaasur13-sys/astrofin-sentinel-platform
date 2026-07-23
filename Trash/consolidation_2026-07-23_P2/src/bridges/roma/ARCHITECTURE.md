# ROMA — Economic-Aware Distributed Execution Control Plane
# Architecture Specification v1.0 (2026-04-17)

## Status: 🟢 TERMINAL ARCHITECTURAL COMPLETE

> All fundamental layers built. Further work = product maturity, not system design.

---

## System Identity

**ROMA** = Economic-Aware Distributed Execution Control Plane

A policy-driven compute broker where execution is conditioned on economic feasibility.
ExecutionAllowed ⇔ (Quota OK ∧ Cost OK ∧ Policy OK) — **hard system invariant**.

---

## Closed-Loop System Model

```
Intent
    ↓
Planning (DAG) — ROMA JSON
    ↓
Cost Prediction (pre-flight economics) ← unique innovation
    ↓
Decision Gate (APPROVED / REQUIRES_CONFIRMATION / REJECTED)
    ↓
Execution (K8s Jobs + GPU scheduling)
    ↓
Event Sourcing (deterministic replay log)
    ↓
Billing (Metering → Ledger → Stripe → Invoicing)
    ↓
Economic feedback loop → next planning cycle
```

---

## Four Coupled State Systems

| System | Technology | Purpose |
|--------|-----------|---------|
| Execution State | K8s Jobs + GPU scheduler | Runtime truth |
| Financial State | Billing ledger + Stripe | Revenue truth |
| Event State | Deterministic event log + Raft | Audit truth |
| Economic State | Cost prediction + Decision Gate | Pre-execution control |

---

## Layer Inventory

| Layer | Status | Key Files |
|-------|--------|-----------|
| Control Plane (CLI, Planner) | ✅ | `roma_cli.py`, `compiler/json_to_k8s.py` |
| Queue Manager | ✅ | `queue/queue_manager.py` |
| GPU Policy Engine v2 | ✅ | `scheduler/gpu_policy_engine_v2.py` |
| Event Sourcing | ✅ | `durability/event_sourcing.py` |
| Raft Consensus | ✅ | `ha/raft_consensus.py` |
| K8s CRD + Controller | ✅ | `k8s/roma_crd.yaml`, `k8s/roma_controller.py` |
| Plugin Ecosystem | ✅ | `plugins/plugin_api.py`, `plugins/plugin_runtime.py` |
| Operator SDK | ✅ | `operator_sdk/operator_base.py`, `operator_sdk/converter.py` |
| Multi-Tenant | ✅ | `tenancy/manager.py` |
| Auth + API Gateway | ✅ | `auth/engine.py`, `auth/api_gateway.py` |
| Billing (Metering + Ledger + Stripe) | ✅ | `billing/metering.py`, `billing/ledger.py`, `billing/stripe_client.py` |
| Cost Prediction + Decision Gate | ✅ | `cost/predictor.py`, `cost/gate.py` |

---

## Core Innovation: Decision Gate

```python
APPROVED                 # within budget + policy
REQUIRES_CONFIRMATION   # above budget threshold, user confirm
REJECTED                 # exceeds limits or policy violation
```

Policy-driven compute broker. Execution is conditioned on economic feasibility.
Not available in: Kubernetes, Argo, Ray, Nomad, AWS Lambda (no pre-execution economic gating).

---

## Comparison with Existing Systems

| Property | K8s | Argo | Ray | Nomad | ROMA |
|----------|-----|------|-----|-------|------|
| GPU scheduling | ✅ | ✅ | ✅ | ✅ | ✅ |
| Event sourcing | ❌ | Partial | ❌ | ❌ | ✅ |
| Pre-execution cost gate | ❌ | ❌ | ❌ | ❌ | ✅ |
| Plugin ecosystem | ✅ Operators | ✅ | ✅ | ✅ | ✅ |
| Multi-tenant | Namespace | Teams | ✅ | Namespaces | ✅ |
| Stripe billing | External | External | External | External | ✅ Built-in |
| Raft consensus | etcd | ❌ | ❌ | ❌ | ✅ |

---

## Next Phase: Product Maturity (Not Architecture)

| Option | Focus | What It Means |
|--------|-------|---------------|
| **A** | Developer Platform UX | CLI polish, interactive approvals, cost previews |
| **B** | Enterprise Control Plane | SSO/SCIM, audit logs, compliance layer |
| **C** | Global Scaling Layer | Multi-region routing, cost-aware cross-cluster routing |
| **D** | FinOps Intelligence | Budget forecasting, anomaly detection, spend optimization |

---

## Execution Commands

```bash
cd /home/workspace/roma-execution-bridge

# CLI
python3 roma_cli.py --help

# Verify core systems
python3 ha/raft_consensus.py
python3 cost/gate.py
python3 billing/stripe_client.py
python3 ecosystem/marketplace.py

# K8s installation
kubectl apply -f k8s/roma_crd.yaml
kubectl apply -f k8s/rbac-roma-executor.yaml
bash k8s/install_roma_crd.sh
```
