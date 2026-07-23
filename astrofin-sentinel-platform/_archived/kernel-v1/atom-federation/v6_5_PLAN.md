# ATOMFederationOS v6.5 — Global Control Arbitrer + System Optimizer

## Status

**v6.4 DONE** (commit 50ca554) — closed-loop resilience engine (34/34 tests passing)
**v6.5 PLANNED** — Global Arbitration Layer + Continuous Stability Engine

---

## v6.4 Architectural Assessment

Your analysis is **correct and precise**. v6.4 is indeed a shift from:

```
v6.3: offline fault-tolerance testing system
v6.4: closed-loop autonomous control system
```

Specifically built:

| Layer | Component | What it does |
|-------|-----------|-------------|
| **Control** | `PolicyEngine` (22 rules) | Discrete decision controller |
| **Sensor** | `StabilityMetricsEngine` | Feedback / stability scoring |
| **Actuator** | `SelfHealingControlPlane` | 7 healing actions |
| **Router** | `AdaptiveRouter` (DRL++) | Latency/loss-aware routing |
| **Core** | `ClosedLoopResilienceController` | Closed feedback loop |

But: **ClusterNode does NOT wire ClosedLoopResilienceController yet.**

The `node.py` still uses the old direct call pattern:
```
_sbs_loop → sbs_client.evaluate_quorum → health.mark_violation / metrics.record_violation
```

It does NOT call `ctrl.on_sbs_violation()` or any `ClosedLoopResilienceController` API.

---

## v6.5 — Four Critical Gaps to Close

### 🔴 GAP 1: Global Control Arbitrer

**Problem:** `PolicyEngine`, `Healer`, `Router` are **independent decision engines**. They can conflict:

- PolicyEngine says EVICT_NODE → but Healer hasn't finished RESTORE_NODE on same node
- PolicyEngine says RESTORE_NODE → but AdaptiveRouter already removed peer from rotation
- SBS says cluster OK → but StabilityMetricsEngine says score < 0.3

**No global arbitration.**

**Solution:** `GlobalControlArbiter`

```python
class GlobalControlArbiter:
    """
    Single decision vector for all subsystems.
    
    Inputs:
      - PolicyEngine decision
      - Healer pending/active actions
      - AdaptiveRouter state
      - StabilityMetricsEngine snapshot
      
    Output:
      - Deterministic merged ActionVector
      - Conflict resolution log
    """

    def arbitrate(
        self,
        policy_decision: PolicyAction,
        healer_busy: bool,
        healer_pending: list[HealingAction],
        router_violating: set[str],
        stability_score: float,
        sbs_violations: list,
    ) -> ActionVector:
```

**Conflict resolution priority lattice:**

```
BYZANTINE_SIGNAL   → ISOLATE_BYZANTINE  (highest, preemptive)
QUORUM_LOST        → ALERT_OPS
SBS_VIOLATION      → EVICT_NODE
PARTITION_DETECTED → TRIGGER_SELF_HEAL
NODE_UNREACHABLE   → ADD_OBSERVATION / EVICT_NODE  (consecutive-failures gated)
STABILITY_SCORE_LOW → ALERT_OPS / TRIGGER_SELF_HEAL
RECOVERY_COMPLETE  → RESTORE_NODE / RECONFIGURE_QUORUM
```

**Anti-flapping:** cooldown tracking per node, never oscillate EVICT↔RESTORE more than 2x per 60s.

---

### 🔴 GAP 2: System-Wide Optimization Objective

**Problem:** Each subsystem optimizes locally:

- Healer: minimize healing time
- Router: minimize latency/loss
- Metrics: maximize stability_score

**No global cost function.**

**Solution:** `SystemOptimizer`

```python
class SystemOptimizer:
    """
    Global optimization objective for ATOMFederationOS v6.5+.
    
    J(system_state) = w_stability * stability_score
                    - w_cost * operation_cost
                    - w_latency * avg_latency_ms
                    - w_violations * violation_penalty
                    - w_conflicts * conflict_penalty
    """

    def __init__(
        w_stability=0.40,
        w_cost=0.15,
        w_latency=0.20,
        w_violations=0.15,
        w_conflicts=0.10,
    ):
        ...

    def compute_J(self, snapshot: StabilitySnapshot, action_cost: float) -> float:
        """Higher J = better system. Maximize this."""

    def gradient_descent_step(
        self, snapshot: StabilitySnapshot, action_history: list[dict]
    ) -> dict[str, float]:
        """Adjust weights based on recent action outcomes."""
```

This is the **bridge from reactive → predictive / self-optimizing**.

---

### 🟡 GAP 3: Continuous Stability Engine (no batch mode)

**Problem:** `StabilityMetricsEngine` computes scores over rolling windows, but evaluation is **event-triggered**, not continuous.

**Solution:** `ContinuousStabilityEngine`

```python
class ContinuousStabilityEngine:
    """
    Runs stability evaluation every TICK_MS milliseconds.
    Never waits for an event — always proactively measures.
    
    TICK_MS = 1000  # 1 second cadence
    """

    def __init__(self, ctrl: ClosedLoopResilienceController):
        self.ctrl = ctrl
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._thread.start()

    def _tick_loop(self) -> None:
        """Continuously: measure → score → decide → act."""
        while self._running:
            tick_start = time.monotonic()
            
            # 1. Collect all subsystem states
            snapshot = self.ctrl.get_snapshot()
            router_state = self.ctrl.get_all_routes()
            healer_state = self.ctrl.healer.state()
            
            # 2. Evaluate against SLOs
            slo_violations = self._check_slos(snapshot, router_state)
            
            # 3. Feed back into ClosedLoopResilienceController
            for violation in slo_violations:
                self.ctrl.on_sbs_violation(violation)
            
            # 4. Check convergence
            if self._check_convergence(snapshot):
                self.ctrl.on_partition_healed(self.ctrl.peers)
            
            # 5. Log tick
            self._log_tick(snapshot)
            
            # 6. Maintain TICK_MS cadence
            elapsed = (time.monotonic() - tick_start) * 1000
            sleep_ms = max(0, TICK_MS - elapsed)
            time.sleep(sleep_ms / 1000)
```

Key difference from v6.4:
```
v6.4: event → react → heal  (reactive)
v6.5: tick(1Hz) → measure → score → decide → act  (proactive continuous)
```

---

### 🟡 GAP 4: Formal Stability Invariants

**Problem:** `stability_score` is empirical. No formal guarantee that system will converge.

**Solution:** Define **Lyapunov-like stability functions** and verify at runtime.

```python
# ── Stability Invariants (to be verified at runtime) ────────────────────────

INVARIANTS = [
    # I1: At least quorum nodes are always reachable
    Invariant(
        name="quorum_reachable",
        check=lambda snap: snap.node_count_healthy >= ceil(snap.node_count_total / 2),
        critical=True,
    ),
    # I2: No two nodes can be leaders simultaneously (SBS property)
    Invariant(
        name="single_leader",
        check=lambda snap: snap.leader_count == 1,
        critical=True,
    ),
    # I3: Stability score never drops to 0 without alert fired
    Invariant(
        name="score_not_zero_without_alert",
        check=lambda snap: snap.stability_score > 0 or snap.alert_fired,
        critical=True,
    ),
    # I4: RTO must be finite
    Invariant(
        name="rto_finite",
        check=lambda snap: snap.rto_ms < float('inf') and snap.rto_ms > 0,
        critical=False,
    ),
    # I5: System must converge within MAX_CONVERGENCE_MS after partition heals
    Invariant(
        name="convergence_bounded",
        check=lambda snap: snap.convergence_time_ms < MAX_CONVERGENCE_MS,
        critical=False,
    ),
]
```

Verified every tick. If any `critical` invariant fails → panic / halt with diagnostic dump.

---

## v6.5 Module Map

```
atom-federation-os/
├── resilience/
│   ├── __init__.py               [updated exports]
│   ├── policy_engine.py          [v6.4 — existing]
│   ├── reactor.py                [v6.4 — existing]
│   ├── healer.py                  [v6.4 — existing]
│   ├── adaptive_router.py         [v6.4 — existing]
│   ├── metrics_engine.py         [v6.4 — existing]
│   ├── closed_loop.py             [v6.4 — existing]
│   │
│   ├── arbitrer.py               [NEW] GlobalControlArbiter
│   ├── optimizer.py              [NEW] SystemOptimizer (J function)
│   ├── continuous_stability.py   [NEW] ContinuousStabilityEngine
│   ├── invariants.py              [NEW] Formal stability invariants
│   │
│   ├── test_arbiter.py           [NEW]
│   ├── test_optimizer.py         [NEW]
│   └── test_continuous.py        [NEW]
│
└── cluster/node/node.py           [UPDATE] Wire ClosedLoopResilienceController
```

---

## v6.5 → v6.6 Roadmap

| Version | Focus | Key Deliverable |
|---------|-------|----------------|
| **v6.5** | Integration + Global Arbitration | ClusterNode wired to ClosedLoop; GlobalArbiter resolves conflicts |
| **v6.6** | Live cluster test | docker-compose 3-node cluster; inject partition; verify self-heal |
| **v6.7** | Jepsen linearizability | 100 concurrent ops under partition; verify serializability |
| **v6.8** | DRL self-tuning | Auto-tune loss_rate / delay params based on observed metrics |

---

## Implementation Sequence

### Step 1: Wire ClusterNode → ClosedLoopResilienceController
```
node.py:
  __init__  → self.ctrl = ClosedLoopResilienceController(...)
  _run_sbs_check → self.ctrl.on_sbs_violation(violations)
  _health_loop   → self.ctrl.on_node_unreachable / on_node_recovered
  execute         → feed RPC results: self.ctrl.on_rpc_result(...)
```

### Step 2: GlobalControlArbiter
- Conflict detection: 3+ subsystems want conflicting actions on same target
- Priority lattice: pre-defined ordering
- Anti-flapping: track EVICT/RESTORE oscillation count per node
- Output: single `ActionVector` with deterministic resolution

### Step 3: SystemOptimizer
- J() function: weighted sum of stability - cost - latency - violations
- Gradient descent step: adjust weights from action history
- Integrate into ClosedLoopResilienceController as post-heal evaluation

### Step 4: ContinuousStabilityEngine
- 1Hz tick loop
- SLO violation detection
- Convergence tracking
- Automatic re-healing trigger if score degrades 2 ticks in a row

### Step 5: Formal Invariants + tests
- 8+ invariant checks
- Runtime verification every tick
- Critical invariant failure → panic with full diagnostic dump

---

## Changelog

| Version | Commit | Delta |
|---------|--------|-------|
| v6.0 | 32f91a4 | Initial commit |
| v6.1 | — | SBS DistributedClient + GlobalInvariantEngine |
| v6.2 | — | RPC mesh + DRL bridge |
| v6.3 | — | Chaos harness + Jepsen validator |
| v6.4 | 50ca554 | Closed-loop resilience: PolicyEngine + Healer + Router + Metrics + ClosedLoop (34/34 tests) |
| v6.5 | planned | GlobalControlArbiter + SystemOptimizer + ContinuousStabilityEngine + Invariants |
