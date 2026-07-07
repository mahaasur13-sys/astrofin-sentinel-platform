from __future__ import annotations
from .audit import (
    AuditLog,
    DecisionRecord,
    get_audit_log,
    build_decision_record,
    record_decision,
)
from .backtest_loop import (
    BacktestRegime,
    ContinuousBacktest,
    create_backtest_runner,
    run_backtest_on_bars,
)
from .counterfactual import CounterfactualEngine
from .ensemble_selection import (
    ensemble_diversity_score,
    select_ensemble,
    select_ensemble_by_confidence,
)
from .grounding import validate_with_grounding
from .hierarchical_policy import HierarchicalPolicy
from .karl_integration import (
    AMREOutput,
    DelistFallback,
    apply_fallback,
    check_delisted_fallback,
    get_karl_diagnostics,
    process_amre,
)
from .oap_optimizer import (
    get_oap_optimizer,
    OAPConfig,
    OAPOptimizer,
    OptimizationStatus,
    ValidationState,
)
from .replay_buffer import (
    BufferEntry,
    ReplayBuffer,
    _select_best_trajectory,
    get_default_buffer,
)
from .reward import (
    get_reward_diagnostics,
    EMA_ALPHA,
    RewardState,
    compute_reward_from_outcome,
    compute_trajectory_reward,
    get_global_buffer,
    get_calibrator,
    get_dd_tracker,
    
    
    set_global_buffer,
    update_reward_ema,
)
from .self_question import (
    SelfQuestioningEngine,
    SQResult,
    should_trigger_self_questioning,
)
from .similarity import (
    estimate_q_star,
    is_similar_trajectory,
    jensen_shannon_divergence,
    knn_q_star,
    select_top_k_trajectories,
    trajectory_distance,
)
from .trajectory import (
    MarketState,
    Trajectory,
    TrajectoryMetrics,
    TrajectoryStep,
    compute_trajectory_metrics,
    market_state_hash,
    trajectory_from_dict,
    trajectory_from_state,
    trajectory_to_dict,
)
from .uncertainty import estimate_uncertainty

"""amre/__init__.py - ATOM-KARL AMRE Control Loop"""


AMRE_ENABLED = True
__all__ = [
    "AMRE_ENABLED",
    "MarketState",
    "Trajectory",
    "TrajectoryStep",
    "TrajectoryMetrics",
    "market_state_hash",
    "trajectory_from_state",
    "compute_trajectory_metrics",
    "trajectory_to_dict",
    "trajectory_from_dict",
    "trajectory_distance",
    "is_similar_trajectory",
    "jensen_shannon_divergence",
    "estimate_q_star",
    "select_top_k_trajectories",
    "knn_q_star",
    "compute_trajectory_reward",
    "compute_reward_from_outcome",
    "get_default_buffer",
    "get_global_buffer",
    "get_calibrator",
    "get_dd_tracker",
    "get_oap_optimizer",
    "get_reward_diagnostics",
    "set_global_buffer",
    "validate_with_grounding",
    "estimate_uncertainty",
    "SelfQuestioningEngine",
    "SQResult",
    "HierarchicalPolicy",
    "CounterfactualEngine",
    "select_ensemble",
    "ensemble_diversity_score",
    "select_ensemble_by_confidence",
    "OAPOptimizer",
    "OAPConfig",
    "OptimizationStatus",
    "ValidationState",
    "ReplayBuffer",
    "BufferEntry",
    "_select_best_trajectory",
    "AuditLog",
    "DecisionRecord",
    "get_audit_log",
    "record_decision",
    "build_decision_record",
    "ContinuousBacktest",
    "BacktestRegime",
    "create_backtest_runner",
    "run_backtest_on_bars",
    # KARL-010 Integration
    "process_amre",
    "check_delisted_fallback",
    "apply_fallback",
    "get_karl_diagnostics",
    "DelistFallback",
    "AMREOutput",
]


__all__ += ["RewardState", "EMA_ALPHA", "update_reward_ema"]
__all__ += ["should_trigger_self_questioning"]
