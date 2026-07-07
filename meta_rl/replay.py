"""meta_rl/replay.py — ATOM-META-RL-009: Cross-session Replay Engine"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

# Feature flag
CROSS_SESSION_REPLAY_ENABLED = True

# Drift thresholds
DRIFT_SCORE_MILD = 0.15
DRIFT_SCORE_MODERATE = 0.30
DRIFT_SCORE_SEVERE = 0.50


def load_session_records(session_id: str) -> list[dict[str, Any]]:
    """Load all decision records from a persisted session."""
    from meta_rl.persistence import get_persistence

    return get_persistence().load_scored_strategies(session_id)


def load_all_records() -> list[dict[str, Any]]:
    """Load decision records from all sessions."""
    from meta_rl.persistence import get_persistence

    persist = get_persistence()
    sessions = persist.list_sessions()
    all_records = []
    for sid in sessions:
        all_records.extend(persist.load_scored_strategies(sid))
    return all_records


def replay_session(
    session_id: str,
    callback: Callable[[dict[str, Any]], int],
    records: list[dict[str, Any]] | None = None,
) -> int:
    """Replay records from a session, calling callback for each.

    Returns the number of records processed.
    Fail-safe: returns 0 on any error.
    """
    if not CROSS_SESSION_REPLAY_ENABLED:
        return 0
    if records is None:
        records = load_session_records(session_id)
    if not records:
        return 0
    processed = 0
    for idx, record in enumerate(records):
        try:
            callback(record, idx)
            processed += 1
        except Exception:
            continue
    return processed


@dataclass
class OAPDriftReport:
    """Results of OAP drift analysis."""

    session_id: str
    total_records: int
    generations: list[int]
    mean_qstar: float
    std_qstar: float
    drift_score: float
    drift_severity: str
    generation_qstar_trend: list[float]
    is_overfitting: bool
    overfitting_evidence: list[str]
    recommendations: list[str]


def analyze_oap_drift(records: list[dict[str, Any]], session_id: str = "") -> OAPDriftReport:
    """Analyze OAP drift from historical decision records.

    Computes:
      - Q* mean and std across records
      - Drift score = std(Q*) / abs(mean(Q*) + ε)
      - Per-generation Q* trend
      - Overfitting detection (rising reward but falling unseen)

    Returns OAPDriftReport with severity, evidence, and recommendations.
    """
    if not records:
        return OAPDriftReport(
            session_id=session_id,
            total_records=0,
            generations=[],
            mean_qstar=0.0,
            std_qstar=0.0,
            drift_score=0.0,
            drift_severity="none",
            generation_qstar_trend=[],
            is_overfitting=False,
            overfitting_evidence=[],
            recommendations=[],
        )

    rewards = [float(r.get("reward", 0.0)) for r in records]
    gens = [int(r.get("generation", 0)) for r in records]

    mean_q = float(np.mean(rewards)) if rewards else 0.0
    std_q = float(np.std(rewards)) if rewards else 0.0
    drift_score = abs(std_q / (abs(mean_q) + 1e-6))

    if drift_score < DRIFT_SCORE_MILD:
        severity = "none"
    elif drift_score < DRIFT_SCORE_MODERATE:
        severity = "mild"
    elif drift_score < DRIFT_SCORE_SEVERE:
        severity = "moderate"
    else:
        severity = "severe"

    # Per-generation trend
    unique_gens = sorted(set(gens))
    gen_means = []
    for g in unique_gens:
        g_rewards = [r for r, g_ in zip(rewards, gens, strict=False) if g_ == g]
        if g_rewards:
            gen_means.append(float(np.mean(g_rewards)))
        else:
            gen_means.append(0.0)

    # Overfitting detection
    overfitting_evidence = []
    recommendations = []
    is_overfitting = False

    if len(gen_means) >= 2:
        early = np.mean(gen_means[: max(1, len(gen_means) // 3)])
        late = np.mean(gen_means[-max(1, len(gen_means) // 3) :])
        if late > early and std_q > DRIFT_SCORE_MODERATE:
            is_overfitting = True
            overfitting_evidence.append(f"Reward rising ({early:.3f} → {late:.3f}) with high variance (std={std_q:.3f})")
        if len(gen_means) >= 3:
            recent_deltas = [gen_means[i] - gen_means[i - 1] for i in range(1, len(gen_means))]
            if all(d > 0 for d in recent_deltas[-2:]) and std_q > DRIFT_SCORE_MILD:
                overfitting_evidence.append("Consecutive generation reward increases — possible memorization")

    if is_overfitting or severity in ("moderate", "severe"):
        recommendations.append("increase_mutation_rate")
        recommendations.append("decrease_crossover_rate")
    if severity in ("moderate", "severe"):
        recommendations.append("boost_exploration")
    if std_q > DRIFT_SCORE_SEVERE:
        recommendations.append("reset_population")

    return OAPDriftReport(
        session_id=session_id or "unknown",
        total_records=len(records),
        generations=unique_gens,
        mean_qstar=mean_q,
        std_qstar=std_q,
        drift_score=round(drift_score, 4),
        drift_severity=severity,
        generation_qstar_trend=[round(v, 4) for v in gen_means],
        is_overfitting=is_overfitting,
        overfitting_evidence=overfitting_evidence,
        recommendations=recommendations,
    )


def get_adaptive_params_from_drift(
    drift_report: OAPDriftReport,
    base_mutation: float = 0.15,
    base_crossover: float = 0.40,
) -> dict[str, float]:
    """ATOM-META-RL-009: Convert OAP drift report to adaptive GA params.

    When drift is high:
      - Increase mutation_rate (exploration)
      - Decrease crossover_rate (less exploitation of possibly overfitted genes)

    Returns dict with 'mutation_rate' and 'crossover_rate'.
    """
    if drift_report.drift_severity == "none":
        return {"mutation_rate": base_mutation, "crossover_rate": base_crossover}

    mult = 1.0 + 0.5 * (drift_report.drift_score / DRIFT_SCORE_SEVERE)
    adj_mutation = min(0.60, base_mutation * mult)
    adj_crossover = max(0.10, base_crossover / mult)

    if drift_report.is_overfitting:
        adj_mutation = min(0.60, adj_mutation * 1.5)
        adj_crossover = max(0.10, adj_crossover * 0.7)

    return {
        "mutation_rate": round(adj_mutation, 4),
        "crossover_rate": round(adj_crossover, 4),
    }
