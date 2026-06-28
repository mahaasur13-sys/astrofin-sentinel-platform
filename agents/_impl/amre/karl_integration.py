"""amre/karl_integration.py — KARL-010 Integration Layer
Встраивает AMRE-контур (uncertainty, grounding, decision record)
в SynthesisAgent и sentinel_v5.
"""

from __future__ import annotations


import hashlib
from dataclasses import dataclass
from typing import Any

from .audit import (  # noqa: F401
    build_decision_record,
    get_audit_log,
)
from .grounding import validate_with_grounding
from .oap_optimizer import get_oap_optimizer
from .reward import (  # noqa: F401
    compute_trajectory_reward,
    get_reward_diagnostics,
)
from .uncertainty import estimate_uncertainty

# ─── Delisted Ticker Fallback ──────────────────────────────────────────────────

DELISTED_TICKERS = {
    "NICKEL",
    "NCL",  # Nickel
    "FAANG",  # FAANG basket (split into individual tickers)
}


@dataclass
class DelistFallback:
    """Fallback configuration for delisted/unsupported tickers."""

    original_symbol: str
    fallback_symbol: str
    reason: str
    regime: str = "NORMAL"
    confidence_floor: int = 35


def check_delisted_fallback(symbol: str) -> DelistFallback | None:
    """Check if ticker is delisted or unsupported, return fallback config."""
    symbol_upper = symbol.upper()

    if symbol_upper in DELISTED_TICKERS:
        # Map to equivalent or proxy ticker
        fallbacks = {
            "NICKEL": DelistFallback(
                original_symbol=symbol_upper,
                fallback_symbol="MCP",  # MCP token (proxy for metals)
                reason="Nickel delisted — using MCP as proxy",
            ),
            "NCL": DelistFallback(
                original_symbol=symbol_upper,
                fallback_symbol="MCP",
                reason="Nickel delisted — using MCP as proxy",
            ),
            "FAANG": DelistFallback(
                original_symbol=symbol_upper,
                fallback_symbol="QQQ",  # Tech index as proxy
                reason="FAANG basket deprecated — using QQQ as proxy",
            ),
        }
        return fallbacks.get(symbol_upper)

    # Check for unsupported patterns
    if any(c in symbol_upper for c in ["@", "#", "$", "^"]):
        return DelistFallback(
            original_symbol=symbol_upper,
            fallback_symbol="BTC",  # Default to BTC for crypto-style queries
            reason="Unsupported character in ticker — defaulting to BTC",
        )

    return None


def apply_fallback(state: dict, fallback: DelistFallback) -> dict:
    """Apply delisted ticker fallback to state."""
    state = {**state}
    state["symbol"] = fallback.fallback_symbol
    state["original_symbol"] = fallback.original_symbol
    state["fallback_applied"] = True
    state["fallback_reason"] = fallback.reason
    state["regime"] = fallback.regime
    return state


# ─── AMRE Post-Processing ──────────────────────────────────────────────────────


@dataclass
class AMREOutput:
    """Output from AMRE processing."""

    uncertainty: dict[str, float]
    grounding: dict[str, Any]
    confidence_adjustment: int
    final_confidence: int
    reward_estimate: float
    decision_record: dict[str, Any] | None
    passed: bool
    issues: list[str]
    delist_fallback: DelistFallback | None


def process_amre(
    state: dict,
    signals: list[Any],
    all_signals: list[Any],
) -> AMREOutput:
    """
    Run full AMRE post-processing on agent signals:
    1. Delisted ticker check
    2. Uncertainty estimation
    3. Grounding validation
    4. Reward estimation
    5. Decision recording
    6. OAP validation
    """
    symbol = state.get("symbol", "BTCUSDT")
    confidence = state.get("confidence", 50)

    # ── Step 1: Delisted ticker fallback ────────────────────────────────────
    delist_fallback = check_delisted_fallback(symbol)
    if delist_fallback:
        state = apply_fallback(state, delist_fallback)

    # ── Step 2: Uncertainty estimation ───────────────────────────────────────
    uncertainty = estimate_uncertainty(signals)

    # ── Step 3: Grounding validation ────────────────────────────────────────
    grounding = validate_with_grounding(state, signals)

    # ── Step 4: Reward estimation ────────────────────────────────────────────
    reward = compute_trajectory_reward(state, signals, use_calibration=True)

    # ── Step 5: Confidence adjustment via grounding ───────────────────────────
    conf_adjust = grounding.get("confidence_adjustment", 0)
    # Also apply uncertainty penalty
    if uncertainty.get("total", 0) > 0.55:
        conf_adjust -= 10
    final_conf = max(30, min(92, confidence + conf_adjust))

    # ── Step 6: OAP validation ───────────────────────────────────────────────
    amre_data = {
        "uncertainty": uncertainty,
        "q_star": reward,
        "regime": state.get("regime", "NORMAL"),
        "timestamp": state.get("timestamp", ""),
    }
    oap = get_oap_optimizer()
    oap_state = oap.validate_and_adjust(
        amre_data=amre_data,
        base_confidence=final_conf,
        base_position=state.get("position_size", 0.02),
    )

    # ── Step 7.5: Determine pass/fail BEFORE building record ─────────────────
    passed = (
        grounding.get("passed", True)
        and not oap_state.issues  # OAP has no critical issues
        and not delist_fallback  # Don't pass if fallback was needed
    )

    # ── Step 8: Build DecisionRecord for audit trail ─────────────────────────
    from .audit import EnsembleSelection as _ES
    from .audit import MarketSnapshot as _MS

    top_trajectories_dicts = [
        {
            "id": f"traj_{i}",
            "depth": i,
            "action": signals[i].get("signal", "NEUTRAL") if i < len(signals) else "UNKNOWN",
            "q_value": reward,
            "advantage": reward - 0.5,
            "uncertainty": uncertainty.get("total", 0.5),
            "confidence": signals[i].get("confidence", 50) if i < len(signals) else 50,
            "policy": "karluar",
        }
        for i in range(min(3, len(signals)))
    ]

    ensemble_dicts = [
        {
            "name": signals[i].get("agent_name", f"agent_{i}") if i < len(signals) else f"agent_{i}",
            "signal": signals[i].get("signal", "NEUTRAL") if i < len(signals) else "NEUTRAL",
            "confidence": signals[i].get("confidence", 50) if i < len(signals) else 50,
            "weight": signals[i].get("confidence", 50) / 100 if i < len(signals) else 0,
            "q_value": reward,
        }
        for i in range(min(5, len(signals)))
    ]

    _MS(
        symbol=symbol,
        price=state.get("current_price", 0),
        regime=state.get("regime", "NORMAL"),
        volatility_score=uncertainty.get("aleatoric", 0.5),
    )

    [
        _ES(
            agent_name=signals[i].get("agent_name", f"agent_{i}") if i < len(signals) else f"agent_{i}",
            weight=signals[i].get("confidence", 50) / 100 if i < len(signals) else 0,
            q_value=reward,
        )
        for i in range(min(5, len(signals)))
    ]

    import uuid

    decision_record = build_decision_record(
        decision_id=f"DR-{uuid.uuid4().hex[:8].upper()}",
        session_id=state.get("session_id", "unknown"),
        symbol=symbol,
        price=state.get("current_price", 0),
        timeframe=state.get("timeframe_requested", "SWING"),
        regime=state.get("regime", "NORMAL"),
        state_hash=hashlib.md5(
            f"{symbol}:{state.get('current_price', 0)}:{state.get('regime', 'NORMAL')}".encode()
        ).hexdigest()[:12]
        if "hashlib" in dir()
        else "0" * 12,
        top_trajectories=top_trajectories_dicts,
        selected_ensemble=ensemble_dicts,
        q_values=[reward],
        q_star=reward,
        uncertainty=uncertainty,
        confidence_raw=confidence,
        confidence_final=oap_state.confidence,
        confidence_adjustments=[
            f"grounding:{conf_adjust}",
            f"oap:{oap_state.confidence_boost}",
        ],
        final_action=state.get("signal", "NEUTRAL"),
        position_pct=oap_state.position_pct,
        kpi_snapshot={
            "oos_fail_rate": 0.0,
            "entropy": uncertainty.get("total", 0.5),
            "uncertainty": uncertainty.get("total", 0.5),
            "avg_confidence": float(oap_state.confidence),
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "regime_stability": 1.0,
            "exploration_rate": 0.1,
            "ttc_depth": oap_state.confidence_boost,
            "grounding_strength": 0.8 if grounding.get("passed", True) else 0.5,
        },
        metadata={
            "amre_passed": passed,
            "issues": oap_state.issues + grounding.get("issues", []),
            "delist_fallback_applied": delist_fallback is not None,
        },
    )

    # ── Step 9: Return AMREOutput ────────────────────────────────────────────
    return AMREOutput(
        uncertainty=uncertainty,
        grounding=grounding,
        confidence_adjustment=conf_adjust + oap_state.confidence_boost,
        final_confidence=oap_state.confidence,
        reward_estimate=reward,
        decision_record=decision_record,
        passed=passed,
        issues=oap_state.issues + grounding.get("issues", []),
        delist_fallback=delist_fallback,
    )


def get_karl_diagnostics() -> dict[str, Any]:
    """Get full KARL system diagnostics."""
    oap = get_oap_optimizer()
    return {
        "amre_diagnostics": get_reward_diagnostics(),
        "oap_kpi": {
            "current_ttc_depth": oap.kpi_state.current_ttc_depth,
            "oos_fail_rate": round(oap.kpi_state.oos_fail_rate, 4),
            "entropy_avg": round(oap.kpi_state.entropy_avg, 4),
        },
        "audit_summary": get_audit_log().summary(),
    }
