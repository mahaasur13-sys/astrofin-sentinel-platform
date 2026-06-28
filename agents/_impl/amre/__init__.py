"""amre/__init__.py - ATOM-KARL AMRE Control Loop"""

from __future__ import annotations  # noqa: F401


from .audit import (  # noqa: F401
    AuditLog,
    DecisionRecord,
    build_decision_record,
    get_audit_log,
    record_decision,  # noqa: F401  # noqa: F401
)
from .backtest_loop import (  # noqa: F401
    BacktestRegime,
    ContinuousBacktest,
    create_backtest_runner,
    run_backtest_on_bars,  # noqa: F401  # noqa: F401
)
from .counterfactual import CounterfactualEngine  # noqa: F401
from .ensemble_selection import (  # noqa: F401
    ensemble_diversity_score,
    select_ensemble,
    select_ensemble_by_confidence,  # noqa: F401  # noqa: F401
)
from .grounding import validate_with_grounding  # noqa: F401
from .hierarchical_policy import HierarchicalPolicy  # noqa: F401
from .karl_integration import (  # noqa: F401
    AMREOutput,
    DelistFallback,
    apply_fallback,
    check_delisted_fallback,
    get_karl_diagnostics,
    process_amre,  # noqa: F401  # noqa: F401
)
from .oap_optimizer import (  # noqa: F401
    OAPConfig,
    OAPOptimizer,
    OptimizationStatus,
    ValidationState,
    get_oap_optimizer,  # noqa: F401  # noqa: F401
)
from .replay_buffer import (  # noqa: F401
    BufferEntry,
    ReplayBuffer,
    _select_best_trajectory,
    get_default_buffer,  # noqa: F401  # noqa: F401
)
from .reward import (  # noqa: F401
    EMA_ALPHA,
    CalibrationMetrics,
    CorrelationPenalty,
    DrawdownState,
    DrawdownTracker,
    FalseCorrelationDetector,
    RewardCalibrator,
    # ATOM-KARL-015 Phase 3
    RewardState,
    compute_reward_from_outcome,
    compute_trajectory_reward,
    get_calibrator,
    get_dd_tracker,
    get_global_buffer,
    get_reward_diagnostics,
    set_global_buffer,
    update_reward_ema,  # noqa: F401  # noqa: F401
)
from .self_question import (  # noqa: F401
    SelfQuestioningEngine,
    SQResult,
    should_trigger_self_questioning,  # noqa: F401  # noqa: F401
)
from .similarity import (  # noqa: F401
    estimate_q_star,
    is_similar_trajectory,
    jensen_shannon_divergence,
    knn_q_star,
    select_top_k_trajectories,
    trajectory_distance,  # noqa: F401  # noqa: F401
)
from .trajectory import (  # noqa: F401
    MarketState,
    Trajectory,
    TrajectoryMetrics,
    TrajectoryStep,
    compute_trajectory_metrics,
    market_state_hash,
    trajectory_from_dict,
    trajectory_from_state,
    trajectory_to_dict,  # noqa: F401  # noqa: F401
)
from .uncertainty import estimate_uncertainty  # noqa: F401

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
from .astro_reward import (  # noqa: E402  # noqa: F401
    LUNAR_PHASES,  # noqa: F401  # noqa: F401
    NAKSHATRA_SCORES,  # noqa: F401  # noqa: F401
    PLANETARY_ASPECTS,  # noqa: F401  # noqa: F401
    ZODIAC_ARC,  # noqa: F401  # noqa: F401
    compute_astro_reward,  # noqa: F401  # noqa: F401
    get_astro_market_phase,  # noqa: F401  # noqa: F401
    get_lunar_phase_score,  # noqa: F401  # noqa: F401
    get_nakshatra_score,  # noqa: F401  # noqa: F401
    get_planetary_aspect_score,  # noqa: F401  # noqa: F401
)
from .karl_diagnostics import (  # noqa: E402  # noqa: F401
    KARLHealthMetrics,  # noqa: F401  # noqa: F401
    compute_karl_health,  # noqa: F401  # noqa: F401
    format_diagnostics_rich,  # noqa: F401  # noqa: F401
    get_recommendations,  # noqa: F401  # noqa: F401
    get_system_status,  # noqa: F401  # noqa: F401
)
from .karl_optimizer import (  # noqa: E402  # noqa: F401
    AsyncPipeline,  # noqa: F401  # noqa: F401
    KARLOptimizer,  # noqa: F401  # noqa: F401
    KARLPerfProfile,  # noqa: F401  # noqa: F401
    get_karl_optimizer,  # noqa: F401  # noqa: F401
)
from .meta_questioning import MetaQuestion, MetaQuestioningEngine, get_meta_engine  # noqa: E402  # noqa: F401

__all__ += ["MetaQuestioningEngine", "MetaQuestion", "get_meta_engine"]
__all__ += ["RewardState", "EMA_ALPHA", "update_reward_ema"]
__all__ += ["should_trigger_self_questioning"]
