"""amre/reward.py — Enhanced Reward Functions (ATOM-012)
- Penalty for false correlations (overfitting to noise)
- Bayesian calibration (Platt scaling)
- Regime-aware reward with drawdown penalty
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .trajectory import MarketState, Trajectory

# ATOM-KARL-015 Phase 3: EMA Reward Smoothing
EMA_ALPHA = 0.3


class RewardState:
    """EMA state for reward smoothing — ATOM-KARL-015 Phase 3."""

    __slots__ = ("ema_reward", "raw_reward", "count")

    def __init__(self):
        self.ema_reward: float = 0.0
        self.raw_reward: float = 0.0
        self.count: int = 0


def update_reward_ema(
    previous: float, current: float, alpha: float = EMA_ALPHA
) -> float:
    """
    EMA smoothing: new = alpha * current + (1 - alpha) * previous.
    α = 0.3 → responsive but not noisy.
    """
    return alpha * current + (1 - alpha) * previous


# ─── Calibrated Reward ──────────────────────────────────────────────────────────


@dataclass
class CalibrationMetrics:
    """Tracks calibration quality of reward predictions."""

    predictions: list[float]  # predicted rewards
    actuals: list[float]  # actual outcomes
    n_samples: int
    calibration_error: float  # ECE (Expected Calibration Error)
    reliability_diagram: list[tuple[float, float]]  # (bin_center, accuracy)


class RewardCalibrator:
    """
    Bayesian reward calibration using Platt scaling.
    Keeps predictions honest — if system claims 90% confidence but wins 50%,
    this will show it.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        self.metrics = CalibrationMetrics(
            predictions=[],
            actuals=[],
            n_samples=0,
            calibration_error=0.0,
            reliability_diagram=[],
        )
        # Platt scaling params (initialized to identity)
        self.slope = 1.0
        self.intercept = 0.0
        self.fitted = False

    def add_sample(self, predicted_reward: float, actual_outcome: float):
        """Add a (predicted, actual) sample pair."""
        self.metrics.predictions.append(predicted_reward)
        self.metrics.actuals.append(actual_outcome)
        self.metrics.n_samples += 1

        if self.metrics.n_samples >= 30 and not self.fitted:
            self._fit_platt()

    def _fit_platt(self):
        """Fit Platt scaling: p_calibrated = sigmoid(slope * p_raw + intercept)."""
        preds = self.metrics.predictions
        acts = self.metrics.actuals

        # Simple linear Platt on binned data
        bins = [[] for _ in range(self.n_bins)]
        for p, a in zip(preds, acts, strict=False):
            bin_idx = min(int(p * self.n_bins), self.n_bins - 1)
            bins[bin_idx].append((p, a))

        bin_centers, bin_accs = [], []
        for bin_data in bins:
            if bin_data:
                center = sum(x[0] for x in bin_data) / len(bin_data)
                acc = sum(1 for x in bin_data if x[1] > 0) / len(bin_data)
                bin_centers.append(center)
                bin_accs.append(acc)
            else:
                bin_centers.append(0)
                bin_accs.append(0)

        if len(bin_centers) >= 2:
            # Linear regression for Platt params
            n = len(bin_centers)
            sum_x = sum(bin_centers)
            sum_y = sum(bin_accs)
            sum_xy = sum(c * a for c, a in zip(bin_centers, bin_accs, strict=False))
            sum_xx = sum(c * c for c in bin_centers)
            denom = n * sum_xx - sum_x * sum_x
            if abs(denom) > 1e-9:
                self.slope = (n * sum_xy - sum_x * sum_y) / denom
                self.intercept = (sum_y - self.slope * sum_x) / n
                self.fitted = True

        self._compute_ece(bin_centers, bin_accs)

    def _compute_ece(self, bin_centers: list[float], bin_accs: list[float]):
        """Compute Expected Calibration Error."""
        total = sum(
            abs(c - a) for c, a in zip(bin_centers, bin_accs, strict=False) if c > 0
        )
        count = sum(1 for c in bin_centers if c > 0)
        self.metrics.calibration_error = total / count if count > 0 else 1.0
        self.metrics.reliability_diagram = list(
            zip(bin_centers, bin_accs, strict=False)
        )

    def calibrate(self, raw_reward: float) -> float:
        """Apply Platt scaling to raw reward prediction."""
        if not self.fitted:
            return raw_reward  # No calibration yet
        # Clamp to avoid overflow
        z = self.slope * raw_reward + self.intercept
        try:
            return 1.0 / (1.0 + math.exp(-z))
        except OverflowError:
            return 0.0 if z < 0 else 1.0

    def get_calibration_report(self) -> dict[str, Any]:
        """Return calibration diagnostics."""
        if self.metrics.n_samples < 10:
            return {"status": "insufficient_data", "n": self.metrics.n_samples}

        return {
            "status": "calibrated" if self.fitted else "uncalibrated",
            "n": self.metrics.n_samples,
            "ece": round(self.metrics.calibration_error, 4),
            "slope": round(self.slope, 4),
            "intercept": round(self.intercept, 4),
            "reliability_diagram": [
                {"bin": round(c, 3), "accuracy": round(a, 3)}
                for c, a in self.metrics.reliability_diagram
                if c > 0
            ],
        }


# ─── False Correlation Detector ────────────────────────────────────────────────


@dataclass
class CorrelationPenalty:
    """Penalty applied when reward is likely from false correlation."""

    raw_reward: float
    penalty: float
    reason: str
    is_spurious: bool


class FalseCorrelationDetector:
    """
    Detects when reward is likely from spurious correlation (overfitting to noise).

    Signs of spurious correlation:
    - Very high reward on very few samples (lucky streak)
    - Reward doesn't generalize across regimes
    - Reward inversely correlated with sample size (more data → lower reward)
    """

    def __init__(self, min_samples_for_trust: int = 20):
        self.min_samples = min_samples_for_trust
        self.sample_history: list[tuple[int, float]] = []  # (n_samples, reward)

    def assess(
        self, n_samples: int, raw_reward: float, regime: str
    ) -> CorrelationPenalty:
        """Assess whether reward is spurious and apply penalty."""
        self.sample_history.append((n_samples, raw_reward))

        penalty = 0.0
        reasons = []

        # Rule 1: Lucky streak — high reward on tiny sample
        if n_samples < self.min_samples and raw_reward > 0.7:
            lucky_factor = raw_reward * (1 - n_samples / self.min_samples)
            penalty += lucky_factor * 0.4
            reasons.append(
                f"lucky_streak: n={n_samples}<{self.min_samples}, reward={raw_reward:.3f}"
            )

        # Rule 2: Regime instability — reward swings wildly across recent samples
        if len(self.sample_history) >= 5:
            recent = self.sample_history[-5:]
            values = [r for _, r in recent]
            if values:
                mean_r = sum(values) / len(values)
                variance = sum((r - mean_r) ** 2 for r in values) / len(values)
                if variance > 0.15 and raw_reward > mean_r + 0.2:
                    penalty += 0.2
                    reasons.append(f"regime_unstable: var={variance:.3f}>0.15")

        # Rule 3: Inverse sample size correlation (dangerous sign)
        if len(self.sample_history) >= 10:
            early = [r for n, r in self.sample_history[-10:-5]]
            late = [r for n, r in self.sample_history[-5:]]
            if early and late:
                early_avg = sum(early) / len(early)
                late_avg = sum(late) / len(late)
                # If more data → lower reward, suspicious
                if late_avg < early_avg - 0.1 and raw_reward > 0.5:
                    penalty += 0.25
                    reasons.append(
                        f"sample_inverse: early={early_avg:.3f} > late={late_avg:.3f}"
                    )

        is_spurious = penalty > 0.3
        max(0.0, raw_reward - penalty)

        return CorrelationPenalty(
            raw_reward=raw_reward,
            penalty=round(penalty, 4),
            reason="; ".join(reasons) if reasons else "clean",
            is_spurious=is_spurious,
        )


# ─── Drawdown Penalty ──────────────────────────────────────────────────────────


@dataclass
class DrawdownState:
    peak: float
    current: float
    drawdown: float
    in_drawdown: bool


class DrawdownTracker:
    """Track drawdown and penalize sustained losses."""

    def __init__(self, dd_threshold: float = 0.15):
        self.dd_threshold = dd_threshold  # 15% drawdown triggers penalty
        self.peak = 0.0
        self.current = 0.0
        self.trades: list[float] = []

    def add_trade(self, pnl_pct: float) -> DrawdownState:
        """Record a trade and compute drawdown state."""
        self.trades.append(pnl_pct)
        self.current = sum(self.trades)
        self.peak = max(self.peak, self.current)
        dd = (self.peak - self.current) / max(self.peak, 1e-9)
        in_dd = dd >= self.dd_threshold
        return DrawdownState(
            peak=round(self.peak, 4),
            current=round(self.current, 4),
            drawdown=round(dd, 4),
            in_drawdown=in_dd,
        )

    def apply_penalty(self, reward: float) -> tuple[float, str | None]:
        """Apply drawdown penalty to reward if in drawdown."""
        if not self.trades:
            return reward, None
        state = self.add_trade(0)  # just compute current state
        if state.in_drawdown:
            penalty = reward * 0.3
            return reward - penalty, f"dd_penalty: {state.drawdown:.1%}"
        return reward, None


# ─── Main Enhanced Reward Functions ─────────────────────────────────────────────

# Global instances (shared across sessions for persistent calibration)
_CALIBRATOR: RewardCalibrator | None = None
_CORRELATION_DETECTOR: FalseCorrelationDetector | None = None
_DD_TRACKER: DrawdownTracker | None = None


def get_calibrator() -> RewardCalibrator:
    global _CALIBRATOR
    if _CALIBRATOR is None:
        _CALIBRATOR = RewardCalibrator()
    return _CALIBRATOR


def get_correlation_detector() -> FalseCorrelationDetector:
    global _CORRELATION_DETECTOR
    if _CORRELATION_DETECTOR is None:
        _CORRELATION_DETECTOR = FalseCorrelationDetector()
    return _CORRELATION_DETECTOR


def get_dd_tracker() -> DrawdownTracker:
    global _DD_TRACKER
    if _DD_TRACKER is None:
        _DD_TRACKER = DrawdownTracker()
    return _DD_TRACKER


def compute_trajectory_reward(
    state: MarketState,
    signals: list[Any],
    use_calibration: bool = True,
) -> float:
    """
    Enhanced reward computation with:
    - Regime-aware multipliers
    - False correlation penalty
    - Bayesian calibration
    """
    if not signals:
        return 0.0

    def _get(s, key, default=None):
        if hasattr(s, key):
            return getattr(s, key)
        if isinstance(s, dict):
            return s.get(key, default)
        return default

    # Base signal score
    signal_score = sum(
        (
            1.0
            if _get(s, "signal", "NEUTRAL") in ("LONG", "BUY")
            else -0.5 if _get(s, "signal") in ("SHORT", "SELL") else 0
        )
        * _get(s, "confidence", 50)
        / 100
        for s in signals
    ) / len(signals)

    # Regime multiplier
    regime_multiplier = {"LOW": 1.2, "NORMAL": 1.0, "HIGH": 0.7, "EXTREME": 0.3}.get(
        getattr(state, "regime", "NORMAL"), 1.0
    )

    raw_reward = signal_score * regime_multiplier

    # False correlation penalty
    n_samples = getattr(state, "n_samples", 0)
    corr_detector = get_correlation_detector()
    corr_result = corr_detector.assess(
        n_samples=n_samples,
        raw_reward=raw_reward,
        regime=getattr(state, "regime", "NORMAL"),
    )

    if corr_result.is_spurious:
        raw_reward = max(0.0, raw_reward - corr_result.penalty)

    # Bayesian calibration
    if use_calibration:
        calibrator = get_calibrator()
        calibrated_reward = calibrator.calibrate(raw_reward)
    else:
        calibrated_reward = raw_reward

    return round(calibrated_reward, 4)


def compute_reward_from_outcome(
    trade: dict[str, Any],
    apply_drawdown_penalty: bool = True,
) -> float:
    """
    Enhanced reward from trade outcome with drawdown penalty.
    """
    pnl = trade.get("pnl_pct", 0.0)
    conf = trade.get("confidence", 50) / 100
    direction_correct = trade.get("direction_correct", False)

    if pnl > 0 and direction_correct:
        reward = pnl * conf
    elif pnl < 0:
        reward = pnl * 0.5
    else:
        reward = 0.0

    # Drawdown penalty
    if apply_drawdown_penalty:
        dd_tracker = get_dd_tracker()
        # Record trade
        dd_tracker.add_trade(pnl)
        reward, penalty_msg = dd_tracker.apply_penalty(reward)

    return round(reward, 4)


def get_reward_diagnostics() -> dict[str, Any]:
    """Get full reward system diagnostics for audit."""
    return {
        "calibration": get_calibrator().get_calibration_report(),
        "correlation": {
            "n_history": len(get_correlation_detector().sample_history),
        },
        "drawdown": {
            "peak": get_dd_tracker().peak,
            "current": get_dd_tracker().current,
            "trades": len(get_dd_tracker().trades),
        },
    }


# ─── Backward Compatibility ─────────────────────────────────────────────────────


def get_default_buffer() -> list[Trajectory]:
    return []


_DEFAULT_BUFFER: list[Trajectory] | None = None


def get_global_buffer() -> list[Trajectory] | None:
    global _DEFAULT_BUFFER
    return _DEFAULT_BUFFER


def set_global_buffer(buffer: list[Trajectory] | None):
    global _DEFAULT_BUFFER
    _DEFAULT_BUFFER = buffer
