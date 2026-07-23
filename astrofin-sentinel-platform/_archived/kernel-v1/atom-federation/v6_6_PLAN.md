# ATOMFederationOS v6.6 — Self-Modeling + Predictive Control + Decision Lattice

## Status

**v6.5 DONE** (commit 649 insertions) — GlobalControlArbiter + SystemOptimizer + ContinuousStabilityEngine + InvariantsEngine (8/8 tests passing)
**v6.6 PLANNED** — Self-Model + Predictive Controller + Formal Decision Lattice

---

## v6.5 Architectural Assessment

v6.5 is a **closed-loop autonomous cybernetic regulator (ADCR)**:

```
ContinuousStabilityEngine (1Hz tick)
       ↓
InvariantsEngine (formal verification)
       ↓
GlobalControlArbiter (conflict resolution)
       ↓
SystemOptimizer (J() objective)
       ↓
ClosedLoopResilienceController (execute actions)
```

**Gaps remaining (v6.6):**

---

## v6.6 — Four Critical Gaps

### 🔴 GAP 1: Self-Model (CRITICAL — missing entirely)

**Problem:** The system does NOT model itself as an object. It reacts to events but has no internal representation of its own state, dynamics, or possible futures.

**Solution:** `SelfModel`

```python
class SelfModel:
    """
    Internal representation of the ATOMFederationOS cluster.
    
    Builds a causal graph of:
      - Node states
      - RPC dependencies
      - Invariant relationships
      - Failure propagation paths
    
    Enables:
      - What-if analysis (simulate failure before it happens)
      - State prediction (forecast stability score 30s ahead)
      - Root cause inference (which node caused the cascade)
    """

    def build_model(self, snapshot: StabilitySnapshot) -> None:
        """Reconstruct internal model from current snapshot."""

    def predict_next_state(self, action: PolicyAction) -> StabilitySnapshot:
        """Simulate what happens if we take this action."""

    def forecast_stability(self, horizon_s: float = 30.0) -> float:
        """Forecast stability score N seconds ahead."""

    def get_cascade_path(self, failure_node: str) -> list[str]:
        """Which nodes would fail if this node fails?"""
```

---

### 🔴 GAP 2: Predictive Control Loop

**Problem:** v6.5 is **reactive** — it heals after failure. Need **predictive** — heal before failure.

**Solution:** `PredictiveController`

```python
class PredictiveController:
    """
    Extends ClosedLoopResilienceController with predictive capabilities.
    
    Forecasts degradation T seconds ahead using SelfModel.
    If degradation predicted → trigger pre-emptive healing.
    
    Key insight:
      v6.5: score=0.3 → heal        (reactive, RTO-dependent)
      v6.6: score=0.7 but falling   → heal NOW  (predictive, RTO→0)
    """

    def __init__(self, ctrl: ClosedLoopResilienceController):
        self.ctrl = ctrl
        self.self_model = SelfModel()
        self.forecast_horizon_s = 30.0
        self.degradation_threshold = 0.15  # If score drops >0.15 in 30s → pre-heal

    def tick(self) -> TickResult:
        # 1. Update self-model from current snapshot
        snap = self.ctrl.get_snapshot()
        self.self_model.build_model(snap)

        # 2. Forecast stability
        predicted_score = self.self_model.forecast_stability(self.forecast_horizon_s)
        
        # 3. If degradation exceeds threshold → pre-emptive heal
        if snap.stability_score - predicted_score > self.degradation_threshold:
            self.ctrl.heal_async(HealingAction.RECONFIGURE_QUORUM)
        
        # 4. Return tick result with prediction
        return tick_result_with_prediction(snap, predicted_score)
```

---

### 🔴 GAP 3: Formal Decision Lattice

**Problem:** `GlobalControlArbiter` has a priority cascade, but:

- No formal proof of correctness
- No deterministic algebra for conflict resolution
- No verification that lattice is total/consistent

**Solution:** `DecisionLattice`

```python
class DecisionLattice:
    """
    Formal deterministic decision algebra.
    
    Given a system state S and a set of desired actions A = {a1, a2, ...},
    produces a totally-ordered, conflict-free action sequence.
    
    Properties (PROVED):
      - Determinism: same S → same decision (idempotent)
      - Completeness: every S produces a decision (no undefined states)
      - Conflict-freedom: no two actions in the output conflict
      - Priority soundness: higher-priority action always wins
    """

    def decide(self, state: SystemState) -> LatticeDecision:
        """
        Returns:
          - primary_action: PolicyAction
          - secondary_actions: list[PolicyAction]  
          - lattice_path: list[str]  (proof trace)
          - conflicts_resolved: list[ConflictRecord]
        """
    
    # Formal priority lattice (totally ordered):
    # BYZANTINE(1000) > QUORUM_LOST(900) > SBS_CRITICAL(850) > ...
    # Every priority level has a PROOF of correctness.
```

---

### 🔴 GAP 4: Global Objective Integration

**Problem:** `SystemOptimizer.compute_J()` exists but is NOT integrated into the control loop.

**Solution:** `AdaptiveObjectiveController`

```python
class AdaptiveObjectiveController:
    """
    Integrates J() into the real control loop.
    
    J = w_stability * stability_score
      - w_cost * operation_cost
      - w_latency * normalized_latency
      - w_violations * violation_penalty
      - w_conflicts * conflict_penalty
    
    Every action is evaluated by J() BEFORE execution.
    If J would decrease → action is deferred or rejected.
    
    v6.6: REACTIVE → PREDICTIVE + GOAL-DIRECTED
    """

    def should_execute(self, action: PolicyAction, snapshot: StabilitySnapshot) -> bool:
        """
        Returns True if executing action would increase (or not decrease) J.
        """
        current_J = self.optimizer.compute_J(snapshot)
        predicted_snap = self.self_model.predict_next_state(action)
        predicted_J = self.optimizer.compute_J(predicted_snap)
        return predicted_J >= current_J - 0.05  # 0.05 tolerance
```

---

## v6.6 Module Map

```
atom-federation-os/
├── resilience/
│   ├── self_model.py              [NEW] SelfModel
│   ├── predictive_controller.py   [NEW] PredictiveController
│   ├── decision_lattice.py        [NEW] DecisionLattice + Formal proofs
│   ├── adaptive_objective.py      [NEW] AdaptiveObjectiveController
│   ├── __init__.py                [UPDATE] export new modules
│   └── tests/
│       └── test_resilience_v66.py  [NEW]
│
└── cluster/node/node.py            [UPDATE] wire PredictiveController
```

---

## Implementation Sequence

### Step 1: SelfModel

- Build causal graph from StabilitySnapshot
- `predict_next_state(action)` — what-if simulation
- `forecast_stability(horizon_s)` — time-series projection
- `get_cascade_path(node)` — failure propagation

### Step 2: DecisionLattice

- Formal priority ordering with proof annotations
- `decide(state) → LatticeDecision` — total order, no conflicts
- `verify_lattice()` — sanity check that lattice is total/consistent
- Conflict resolution algebra (commutative, associative, idempotent)

### Step 3: PredictiveController

- Wrap ClosedLoopResilienceController
- SelfModel tick integration
- Forecast-based pre-healing trigger
- Return `PredictiveTickResult` with `predicted_score`

### Step 4: AdaptiveObjectiveController

- Integrate SystemOptimizer J() into decision gate
- Pre-execution J evaluation
- J-based action deferral/rejection
- Weight adaptation from action history

### Step 5: Tests (all new)

- SelfModel: build, predict, forecast, cascade
- DecisionLattice: determinism, completeness, conflict-freedom
- PredictiveController: degradation detected before threshold breach
- AdaptiveObjectiveController: J-gated action execution

---

## v6.6 → v6.7 Roadmap

| Version | Focus | Key Deliverable |
|---------|-------|-----------------|
| **v6.6** | Self-Model + Predictive + Lattice | Predictive pre-healing; formal decision algebra |
| **v6.7** | Live cluster test | docker-compose 3-node; inject partition; verify self-heal |
| **v6.8** | Jepsen linearizability | 100 concurrent ops under partition; verify serializability |
| **v6.9** | DRL self-tuning | Auto-tune weights based on observed J trajectories |

---

## Changelog

| Version | Commit | Delta |
|---------|--------|-------|
| v6.0 | 32f91a4 | Initial commit |
| v6.4 | 50ca554 | Closed-loop resilience (34/34 tests) |
| v6.5 | 649+ | GlobalArbiter + Optimizer + Continuous + Invariants (8/8 tests) |
| v6.6 | planned | SelfModel + PredictiveController + DecisionLattice + AdaptiveObjective |
