"""
amre/grounding.py — ATOM-KARL-015 Phase 5: Soft Degrade Grounding

Заменяет жёсткий additive штраф на мягкий multiplicative factor.
Backward-compatible: при GROUNDING_DEGRADE_ENABLED=false — прежнее поведение.

Формула:
    grounding_factor = max(GROUNDING_MIN_FACTOR, 1.0 - failed_checks * 0.13)
    new_confidence  = max(30, round(confidence * grounding_factor))

Примеры:
    0 failed → factor=1.00 → confidence не меняется
    1 failed → factor=0.87 → confidence 80 → 70
    2 failed → factor=0.74 → confidence 80 → 59
    3 failed → factor=0.65 (capped)

Env vars:
    GROUNDING_DEGRADE_ENABLED (default: "true")
    GROUNDING_MIN_FACTOR      (default: "0.65")
    GROUNDING_PENALTY_STEP    (default: "0.13")
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ─── Config from env ─────────────────────────────────────────────────────────────
_DEGRADE_ENABLED = os.getenv("GROUNDING_DEGRADE_ENABLED", "true").lower() == "true"
_MIN_FACTOR = float(os.getenv("GROUNDING_MIN_FACTOR", "0.65"))
_PENALTY_STEP = float(os.getenv("GROUNDING_PENALTY_STEP", "0.13"))


def validate_with_grounding(
    state: Any,
    signals: list[Any],
    current_confidence: int = 50,
) -> dict[str, Any]:
    """
    Domain grounding validation с мягким multiplicative degrade.

    Parameters
    ----------
    state : Any
        Current market state (for future extensibility).
    signals : List[Any]
        List of agent signals (AgentResponse or dict).
    current_confidence : int
        Confidence before grounding adjustment. Used only in soft-degrade mode.

    Returns
    -------
    Dict[str, Any]
        passed               : bool  — True if < 2 issues
        confidence_adjustment: int   — delta to apply to confidence
        grounding_factor      : float — multiplicative factor (new in Phase 5)
        issues               : List[str] — up to 3 detected problems
    """
    if not signals:
        return {
            "passed": True,
            "confidence_adjustment": 0,
            "grounding_factor": 1.0,
            "issues": [],
        }

    def _get(s, key, default=None):
        if hasattr(s, key):
            return getattr(s, key)
        if isinstance(s, dict):
            return s.get(key, default)
        return default

    issues: list[str] = []
    for s in signals:
        sig = _get(s, "signal", "")
        conf = _get(s, "confidence", 50)

        # Rule 1: High confidence + NEUTRAL → suspicious
        if conf > 85 and sig in ("NEUTRAL", "neutral"):
            issues.append(f"High confidence ({conf}) but NEUTRAL signal")

        # Rule 2: Low confidence + directional → inconsistent
        if conf < 25 and sig not in ("NEUTRAL", "neutral", "AVOID", "avoid"):
            issues.append(f"Low confidence ({conf}) but directional signal: {sig}")

    # Count failed checks (issues with "but" + "signal" = internal consistency failure)
    failed_count = sum(1 for i in issues if "but" in i and "signal" in i)
    passed = len(issues) < 2

    # ── Soft Degrade (Phase 5) ───────────────────────────────────────────────
    if _DEGRADE_ENABLED:
        grounding_factor = max(_MIN_FACTOR, 1.0 - failed_count * _PENALTY_STEP)
        raw_confidence = current_confidence
        adjusted_confidence = max(30, round(raw_confidence * grounding_factor))
        confidence_adjustment = adjusted_confidence - raw_confidence  # e.g. -10

        logger.debug(f"[Grounding] failed={failed_count} factor={grounding_factor:.3f} conf {raw_confidence} → {adjusted_confidence} (Δ={confidence_adjustment:+d})")
    else:
        # Backward-compatible additive degrade (old behaviour)
        confidence_adjustment = -failed_count * 5 if failed_count > 0 else 0
        grounding_factor = 1.0

    return {
        "passed": passed,
        "confidence_adjustment": confidence_adjustment,
        "grounding_factor": round(grounding_factor, 4),
        "issues": issues[:3],
    }
