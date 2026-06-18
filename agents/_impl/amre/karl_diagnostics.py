"""amre/karl_diagnostics.py - ATOM-021: Enhanced KARL Diagnostics"""
from __future__ import annotations


"""Extended diagnostics for KARL self-improvement loop."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class KARLHealthMetrics:
    """Comprehensive health metrics for KARL system."""

    # Decision quality
    decision_count: int = 0
    avg_confidence: float = 0.0
    confidence_trend: float = 0.0  # positive = improving
    high_confidence_ratio: float = 0.0

    # Reward metrics
    avg_reward: float = 0.0
    reward_volatility: float = 0.0
    positive_reward_ratio: float = 0.0

    # Astro alignment
    avg_astro_score: float = 0.0
    astro_alignment_ratio: float = 0.0  # % of decisions with good astro

    # Meta-questioning effectiveness
    meta_question_count: int = 0
    meta_adjustment_avg: float = 0.0
    meta_prevented_wrong: int = 0

    # System health
    oos_fail_rate: float = 0.0
    entropy: float = 0.0
    regime_stability: float = 0.0

    # Performance
    ttc_depth: int = 0
    exploration_rate: float = 0.0

    # Timing
    avg_decision_time_ms: float = 0.0
    overhead_pct: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def compute_karl_health(
    decision_records: list[dict[str, Any]],
    reward_history: list[float],
    astro_scores: list[float],
    meta_questions: list[dict[str, Any]],
    time_ms: float,
) -> KARLHealthMetrics:
    """Compute comprehensive health metrics from history."""
    m = KARLHealthMetrics()

    if not decision_records:
        return m

    m.decision_count = len(decision_records)

    # Confidence metrics
    confidences = [r.get("confidence_final", 50) for r in decision_records]
    m.avg_confidence = sum(confidences) / len(confidences)
    m.high_confidence_ratio = sum(1 for c in confidences if c >= 70) / len(confidences)

    # Confidence trend (simple linear)
    if len(confidences) >= 10:
        first_half = sum(confidences[: len(confidences) // 2]) / (len(confidences) // 2)
        second_half = sum(confidences[len(confidences) // 2 :]) / (len(confidences) - len(confidences) // 2)
        m.confidence_trend = second_half - first_half

    # Reward metrics
    if reward_history:
        m.avg_reward = sum(reward_history) / len(reward_history)
        m.positive_reward_ratio = sum(1 for r in reward_history if r > 0) / len(reward_history)
        if len(reward_history) > 1:
            mean = m.avg_reward
            variance = sum((r - mean) ** 2 for r in reward_history) / len(reward_history)
            m.reward_volatility = variance**0.5

    # Astro metrics
    if astro_scores:
        m.avg_astro_score = sum(astro_scores) / len(astro_scores)
        m.astro_alignment_ratio = sum(1 for s in astro_scores if s >= 1.0) / len(astro_scores)

    # Meta-questioning
    if meta_questions:
        m.meta_question_count = len(meta_questions)
        adjustments = [q.get("confidence_adjustment", 0) for q in meta_questions]
        m.meta_adjustment_avg = sum(adjustments) / len(adjustments)
        m.meta_prevented_wrong = sum(1 for a in adjustments if a < 0)

    # Performance
    m.avg_decision_time_ms = time_ms / max(m.decision_count, 1)

    return m


def get_system_status(health: KARLHealthMetrics) -> dict[str, Any]:
    """Determine overall system status from health metrics."""
    score = 0
    issues = []

    # Check confidence trend
    if health.confidence_trend < -5:
        score -= 2
        issues.append("Confidence degrading")
    elif health.confidence_trend > 5:
        score += 2

    # Check reward quality
    if health.avg_reward < 0:
        score -= 3
        issues.append("Negative average reward")
    elif health.avg_reward > 0.1:
        score += 2

    # Check astro alignment
    if health.astro_alignment_ratio < 0.3:
        score -= 1
        issues.append("Low astro alignment")

    # Check meta-questioning
    if health.meta_prevented_wrong > health.decision_count * 0.1:
        score += 1  # Meta-questioning is helping

    # Check OOS fail rate
    if health.oos_fail_rate > 0.4:
        score -= 2
        issues.append("High OOS failure rate")

    # Determine status
    if score >= 3:
        status = "HEALTHY"
        color = "green"
    elif score >= 0:
        status = "STABLE"
        color = "yellow"
    else:
        status = "DEGRADING"
        color = "red"

    return {
        "status": status,
        "color": color,
        "score": score,
        "issues": issues,
        "recommendations": get_recommendations(health, issues),
    }


def get_recommendations(health: KARLHealthMetrics, issues: list[str]) -> list[str]:
    """Generate actionable recommendations based on health metrics."""
    recs = []

    if "Confidence degrading" in issues:
        recs.append("Consider increasing exploration rate to break pattern")
        recs.append("Review recent high-confidence decisions for hubris")

    if "Negative average reward" in issues:
        recs.append("Reduce position sizes until reward stabilizes")
        recs.append("Increase weight of QuantAgent in synthesis")

    if "Low astro alignment" in issues:
        recs.append("Review planetary aspect scoring weights")
        recs.append("Consider reducing astro weight in conflict resolution")

    if "High OOS failure rate" in issues:
        recs.append("Calibrate reward function using backtest data")
        recs.append("Reduce overfitting to recent patterns")

    if health.exploration_rate < 0.05:
        recs.append("Exploration rate too low - risk of local minimum")

    if health.entropy < 0.3:
        recs.append("Decision entropy low - agents making similar choices")

    if not recs:
        recs.append("System operating within normal parameters")

    return recs


def format_diagnostics_rich(health: KARLHealthMetrics) -> str:
    """Format diagnostics for rich console output."""
    status_info = get_system_status(health)
    lines = []

    status_icon = {"HEALTHY": "✓", "STABLE": "~", "DEGRADING": "✗"}.get(status_info["status"], "?")

    lines.append(f"{status_icon} Status: {status_info['status']}")
    lines.append(f"  Decisions: {health.decision_count}")
    lines.append(f"  Avg Confidence: {health.avg_confidence:.1f} (trend: {health.confidence_trend:+.1f})")
    lines.append(f"  Avg Reward: {health.avg_reward:.4f} (vol: {health.reward_volatility:.4f})")
    lines.append(f"  Astro Score: {health.avg_astro_score:.3f} (aligned: {health.astro_alignment_ratio:.1%})")
    lines.append(f"  Meta Q's: {health.meta_question_count} (avg adj: {health.meta_adjustment_avg:+.1f})")
    lines.append(f"  OOS Fail Rate: {health.oos_fail_rate:.1%}")
    lines.append(f"  Decision Time: {health.avg_decision_time_ms:.1f}ms")

    if issues := status_info.get("issues"):
        lines.append(f"  Issues: {', '.join(issues)}")

    return "\n".join(lines)
