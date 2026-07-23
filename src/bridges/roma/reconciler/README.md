# ROMA Reconciliation Engine — Architecture

## Purpose

Kubernetes is the source of truth. Redis is a cache. When they drift, the reconciler fixes it.

## How It Works

### 3-Way Reconciliation

```
┌──────────────────────────────────────────────────────────────┐
│                      RECONCILER LOOP (every 30s)              │
├──────────────────────────────────────────────────────────────┤
│  1. LIST jobs in Redis  (pending + running sets)             │
│  2. GET job status from K8s (kubectl get jobs -n roma-system│
│  3. DIFF and REPAIR:                                        │
│     ├─ Redis=pending, K8s=running → update Redis to running │
│     ├─ Redis=running, K8s=done      → mark Redis succeeded   │
│     ├─ Redis=running, K8s=missing   → orphan detected       │
│     ├─ Redis=pending, K8s=missing  → orphan pending        │
│     └─ K8s has job, Redis missing   → ingest into Redis      │
└──────────────────────────────────────────────────────────────┘
```

### Orphan Job Recovery

When a job is in Redis but not in Kubernetes:
1. Mark Redis as `failed`
2. Release GPU lock
3. Log orphan event
4. Emit `orphan_job_detected` metric

### Self-Healing Loop

Background thread (daemonize or run inside bridge):
- Runs every 30 seconds
- Repairs drift automatically
- Logs all repair actions
- Emits health metrics

## Usage

```python
from reconciler.reconciliation_engine import ReconciliationEngine

engine = ReconciliationEngine(
    redis_client=redis_client,
    kubeconfig_path="~/.kube/config",
    namespace="roma-system",
)

# Run once (sync reconciliation)
report = engine.reconcile()
print(report)

# Or start background daemon
engine.start_daemon(interval_seconds=30)
```

## Integration

Add to `main.py`:

```python
from reconciler.self_healing_loop import SelfHealingLoop

reconciler = ReconciliationEngine(redis_client, kubeconfig_path, namespace)
healer = SelfHealingLoop(reconciler, interval=30)

@app.on_event("startup")
def start_healer():
    healer.start()

@app.on_event("shutdown")
def stop_healer():
    healer.stop()
```

## Metrics Exposed

| Metric | Type | Description |
|--------|------|-------------|
| `roma_reconcile_runs_total` | Counter | Number of reconciliation runs |
| `roma_reconcile_repairs_total` | Counter | Total repairs made |
| `roma_orphan_jobs_detected` | Gauge | Current orphan jobs |
| `roma_gpu_locks_held` | Gauge | GPU locks in Redis |
| `roma_redis_k8s_drift` | Gauge | 1 if drift detected |
| `roma_job_status_mismatch` | Counter | Status mismatch events |

## Failure Modes

| Scenario | Action |
|----------|--------|
| Redis down | Skip reconcile, log error, continue |
| K8s unreachable | Skip K8s checks, log error, continue |
| Orphan job | Mark failed, release GPU lock |
| Zombie GPU lock | Detect via job completion, force release after 5 min |
| Redis flush (kill all) | On reconnect, reconcile against K8s |
