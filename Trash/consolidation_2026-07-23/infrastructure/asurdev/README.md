# ACOS — Autonomous Constrained Optimization System

**Production-Grade Distributed Compute Platform** | L0-L8 |

---

## Architecture

```
L8: Governance Layer (Safety Kernel)
    ├── safety_kernel/engine.py     — hard constraints (no override)
    ├── policy_verifier/pipeline.py — pre-execution validation
    ├── rollback/engine.py          — state snapshots + rollback
    └── incident/model.py           — 5-tier severity taxonomy

L7: Adaptive Policy Evolution (v7)
    ├── policy_governor/governor.py       — policy parameter governance
    ├── drift_alignment/triple_align.py  — concept/distribution/hardware drift
    ├── budget_controller/ebc.py         — Energy-Budget Controller
    ├── adversarial_sim/stress_tester.py  — stress test policies
    ├── meta_learner/meta_learner.py     — meta-learning on run history
    └── objective_reweight/reweighter.py  — objective reweighting

L6: Optimization Engine (v6)
    ├── constraint_engine/ — validation G = (V, E)
    ├── solver/optimizer_api.py — hybrid: beam search → ILP → selector
    ├── policy_eval/evaluator.py — Thompson sampling + UCB
    └── digital_twin/simulator.py — state propagation

L5: ML Prediction Layer (v5)
    ├── ml_engine/dataset/  — DatasetBuilder → TimescaleDB → train/val/test
    ├── ml_engine/models/    — FailureXGBoost, LoadModel, ModelRegistry
    ├── ml_engine/training/  — Trainer, Evaluator, DriftDetector
    ├── ml_engine/inference/ — FastAPI /predict (<10ms), Predictor
    └── ml_engine/feedback/  — FeedbackCollector, Retrainer

L4: Control Plane State (v4.1)
    ├── state_store/sql/schema.sql         — PostgreSQL schema
    ├── state_store/client.py             — StateStore client
    ├── admission_controller/             — Probabilistic + deterministic
    ├── feature_pipeline/                 — Time-series feature extraction
    └── tsdb/                             — TimescaleDB ingestion

L3-L0: Infrastructure (Ansible + Scripts)
    ├── ansible/roles/slurm_ha/  — Slurm HA (3 controllers)
    ├── ansible/roles/ceph/      — Ceph quorum (3 MON)
    ├── ansible/roles/wireguard/ — WireGuard mesh
    ├── ansible/roles/monitoring/ — Prometheus + Grafana
    ├── scripts/day{1-7}/         — Day-by-day bootstrap
    └── self_healing/             — Watchdog + diagnostics

K8s: manifests/ — Ray Serve, K8s ValidatingWebhook
Load Test: load_test/scenarios/ — 7 failure scenarios
```

---

## Layer Maturity

| Layer | Component | Status |
|-------|-----------|--------|
| L0-L3 | Hardware + Network | ✅ Production |
| L4 | PostgreSQL + Slurm HA | ✅ Production |
| L5 | K8s + Ray + Slurm federation | ✅ |
| L6 | AI Scheduler (data-driven) | ✅ |
| L7 | ML Engine | ✅ v5 |
| L8 | Adaptive Policy (EBC + Drift) | ✅ v6 |
| L9 | Governance (Safety Kernel) | ✅ v7 |
| L10 | Self-healing watchdog | ✅ v8 |

---

## Quick Start

```bash
# Bootstrap cluster (Day 1-7)
make infra

# Deploy management layer
make tsdb        # TimescaleDB
make monitor     # Prometheus + Grafana
make self-healing

# Run ML pipeline
make ml-train    # Train models
make ml-api      # Start inference API :8081
make ml-backfill # Backfill features

# Load test
make loadtest

# System correction
make correction
```

---

## Data Flow

```
TimescaleDB (metrics_1m/5m/15m/1h)
  ↓
feature_pipeline → FeatureVector
  ↓
ml_engine/training → XGBoost models (FailureXGBoost, LoadModel)
  ↓
ml_engine/inference → /predict (risk_score, recommendations)
  ↓
scheduler_v3 → final_score = base_score - risk_penalty
  ↓
Slurm / Ray execution
  ↓
Job outcomes → feedback loop → Retrainer (every 500 jobs OR drift)
```

---

## Git History

```
fb44fde feat: ACOS Correction Prompt + RCA Engine
f7c0158 feat: ACOS load test framework — 7 failure scenarios
e641435 fix: L4 CRITICAL — ceph.py all fixes
d5f38fe feat: v8 — Governance Layer (Safety Kernel)
6c6977e feat: v7 — Adaptive Policy Evolution Layer
93d09c6 feat: v6 CORRECTED — all critical fixes
746977b feat: load_test — self-correcting feedback loop
02f3fd9 feat: v4.3 — TimescaleDB integration
b8de319 feat: v4.1 — Control Plane State Layer
97d4119 feat: v2 — Slurm HA + monitoring
8d707d3 feat: full production-grade home cluster IaC
```

---

## Repo

https://github.com/mahaasur13-sys/AsurDev
