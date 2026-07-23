"""
planning_observability — v8.0 Phase A
Introspection layer for the temporal planning system.

Modules:
  plan_trace_logger  — full execution trace (events, scores, cycles, replans)
  evaluation_metrics — planning health metrics (stability, entropy, DAG complexity)
  drift_profiler     — degradation detection (oscillation, goal drift, weight drift, DAG drift)

Invariant (v8.0 Phase A):
  planning_health = f(stability, evaluation_entropy, replanning_rate, DAG_drift)

Public exports:
  PlanTraceLogger, TraceEventType, TraceEvent, ScoreEvolutionPoint
  EvaluationMetrics, EvaluationMetricsCollector, MetricsConfig
  DriftProfiler, DriftType, DriftEpisode
"""
from orchestration.planning_observability.drift_profiler import (
    DAGDriftProfile,
    DriftEpisode,
    DriftProfiler,
    DriftType,
    GoalDriftProfile,
    OscillationProfile,
    WeightDriftProfile,
)
from orchestration.planning_observability.evaluation_metrics import (
    EvaluationMetrics,
    EvaluationMetricsCollector,
    MetricsConfig,
)
from orchestration.planning_observability.plan_trace_logger import (
    CycleRecord,
    PlanTraceLogger,
    ReplanRecord,
    ScoreEvolutionPoint,
    TraceEvent,
    TraceEventType,
)

__all__ = [
    # trace logger
    "PlanTraceLogger",
    "TraceEventType",
    "TraceEvent",
    "ScoreEvolutionPoint",
    "CycleRecord",
    "ReplanRecord",
    # evaluation metrics
    "EvaluationMetrics",
    "EvaluationMetricsCollector",
    "MetricsConfig",
    # drift profiler
    "DriftProfiler",
    "DriftType",
    "DriftEpisode",
    "OscillationProfile",
    "GoalDriftProfile",
    "WeightDriftProfile",
    "DAGDriftProfile",
]
