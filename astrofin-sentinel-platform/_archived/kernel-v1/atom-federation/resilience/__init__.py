"""
ATOMFederationOS Resilience Layer — v6.7

Modules:
  v6.4 (base closed-loop):
    - PolicyEngine       — 22 rules, trigger → action mapping
    - ResilienceReactor  — event-driven dispatcher
    - SelfHealingControlPlane — 7 healing actions (EVICT/RESTORE/...)
    - AdaptiveRouter     — DRL++: latency/loss-aware routing
    - StabilityMetricsEngine — rolling-window stability scoring
    - ClosedLoopResilienceController — wires all v6.4 components

  v6.5 (global control layer):
    - GlobalControlArbiter   — conflict resolution across subsystems
    - SystemOptimizer       — J() global objective + gradient descent
    - ContinuousStabilityEngine — 1Hz proactive tick loop
    - InvariantsEngine      — formal stability invariant verification

  v6.6 (self-modeling + predictive + goal-directed):
    - SelfModel             — internal causal graph + what-if simulation
    - PredictiveController  — forecast-based pre-emptive healing
    - DecisionLattice       — formal deterministic decision algebra
    - AdaptiveObjectiveController — J-gated autonomous control

  v6.7 (meta-coherence layer — model ↔ reality ↔ objective closure):
    - ModelRealityAligner          — self_model vs real cluster drift detection
    - EigenstateDetector           — stable attractor detection + transition prediction
    - ObjectiveStabilityGovernor   — J-gate oscillation prevention
    - ComputeBudgetController      — compute overhead bounding per tick
    - MetaCoherenceController      — master controller wiring all v6.7 subsystems
"""

from resilience.adaptive_objective import (
    AdaptiveObjectiveController,
    AdaptiveTickResult,
)
from resilience.adaptive_router import (
    AdaptiveRouter,
    PeerRouteState,
    RouteMetrics,
)

# v6.5
from resilience.arbitrer import (
    ArbitrationDecision,
    ConflictType,
    GlobalControlArbiter,
)
from resilience.closed_loop import (
    ClosedLoopResilienceController,
)
from resilience.compute_budget_controller import (
    BudgetAllocation,
    BudgetDecision,
    ComputeBudgetController,
    ComputeBudgetSnapshot,
    CostEntry,
    Subsystem,
)
from resilience.continuous_stability import (
    ContinuousStabilityEngine,
    TickResult,
)
from resilience.decision_lattice import (
    DecisionLattice,
    LatticeDecision,
)
from resilience.eigenstate_detector import (
    Eigenstate,
    EigenstateDetector,
    EigenstateSnapshot,
    EigenstateType,
    TransitionEvent,
)
from resilience.healer import (
    HealingAction,
    HealingResult,
    SelfHealingControlPlane,
)
from resilience.invariants import (
    Invariant,
    InvariantResult,
    InvariantsEngine,
    InvariantSet,
    InvariantSeverity,
)
from resilience.invariants import (
    StabilitySnapshot as InvariantSnapshot,
)
from resilience.meta_coherence_controller import (
    CoherenceMetrics,
    MetaCoherenceController,
    MetaCoherenceSnapshot,
)
from resilience.metrics_engine import (
    StabilityMetricsEngine,
    StabilitySnapshot,
)

# v6.7
from resilience.model_reality_aligner import (
    AlignmentSnapshot,
    DriftEvent,
    DriftStatus,
    ModelRealityAligner,
)
from resilience.objective_stability_governor import (
    GovernorDecision,
    GovernorMode,
    JWindow,
    ObjectiveStabilityGovernor,
    OscillationReport,
)
from resilience.optimizer import (
    OptimizationResult,
    OptimizerWeights,
    SystemOptimizer,
)
from resilience.policy_engine import (
    PolicyAction,
    PolicyEngine,
    PolicyRule,
    ReactionTrigger,
    TriggerMatch,
)
from resilience.predictive_controller import (
    PredictiveController,
    PredictiveTickResult,
)
from resilience.reactor import (
    ReactionAction,
    ResilienceReactor,
)

# v6.6
from resilience.self_model import (
    NodeRole,
    SystemState,
)

__all__ = [
    # v6.4 core
    "PolicyEngine",
    "PolicyRule",
    "PolicyAction",
    "ReactionTrigger",
    "TriggerMatch",
    "ResilienceReactor",
    "ReactionAction",
    "SelfHealingControlPlane",
    "HealingAction",
    "HealingResult",
    "AdaptiveRouter",
    "PeerRouteState",
    "RouteMetrics",
    "StabilityMetricsEngine",
    "StabilitySnapshot",
    "ClosedLoopResilienceController",
    # v6.5
    "GlobalControlArbiter",
    "ArbitrationDecision",
    "ConflictType",
    "SystemOptimizer",
    "OptimizationResult",
    "OptimizerWeights",
    "ContinuousStabilityEngine",
    "TickResult",
    "InvariantsEngine",
    "Invariant",
    "InvariantResult",
    "InvariantSet",
    "InvariantSeverity",
    "InvariantSnapshot",
    # v6.6
    "SystemState",
    "NodeRole",
    "PredictiveController",
    "PredictiveTickResult",
    "DecisionLattice",
    "LatticeDecision",
    "AdaptiveObjectiveController",
    "AdaptiveTickResult",
    # v6.7
    "ModelRealityAligner",
    "AlignmentSnapshot",
    "DriftStatus",
    "DriftEvent",
    "EigenstateDetector",
    "EigenstateSnapshot",
    "Eigenstate",
    "EigenstateType",
    "TransitionEvent",
    "ObjectiveStabilityGovernor",
    "GovernorMode",
    "JWindow",
    "OscillationReport",
    "GovernorDecision",
    "ComputeBudgetController",
    "Subsystem",
    "BudgetAllocation",
    "CostEntry",
    "BudgetDecision",
    "ComputeBudgetSnapshot",
    "MetaCoherenceController",
    "CoherenceMetrics",
    "MetaCoherenceSnapshot",
]
