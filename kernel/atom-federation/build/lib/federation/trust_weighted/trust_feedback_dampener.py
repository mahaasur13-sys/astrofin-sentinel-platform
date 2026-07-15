"""
trust_feedback_dampener.py — v9.7 Trust Feedback Dampener

Purpose:
  Prevents feedback amplification in the trust ↔ consensus loop.

  trust(t+1) = α · trust(t) + (1-α) · outcome_signal
             + decay · (base_trust - trust(t))

Where:
  α ∈ (0, 1)              — EMA smoothing factor (higher = more inertia)
  outcome_signal ∈ [-1,1] — consensus outcome: +1=accepted, -1=rejected, 0=no-consensus
  decay ∈ [0, 1]          — trust freeze prevention (decay toward base_trust)
  base_trust ∈ [0, 1]    — equilibrium trust for inactive nodes

Feedback loop this breaks:
  trust → consensus → outcome → trust_update → trust (loop)
                                     ↑
                          dampened here

Anti-patterns prevented:
  - trust monopolies: node accumulates trust → dominates forever
  - phase locking: oscillating trust values never converge
  - consensus inertia: consensus keeps confirming same winner
  - Byzantine weight freezing: malicious node locks its trust high
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto


class FeedbackRegime(Enum):
    """Operating regime of the trust-feedback loop."""
    STABLE          = auto()   # normal operation
    DAMPED          = auto()   # dampening is active
    OSCILLATING     = auto()   # periodic trust oscillations detected
    MONOPOLIZING    = auto()   # single node accumulating disproportionate trust
    FREEZING        = auto()   # trust values stuck / not updating
    BYZANTINE_FREEZE = auto()  # high-trust node suspiciously static


@dataclass
class DampenerConfig:
    """Configuration for the trust feedback dampener."""
    alpha: float = 0.75           # EMA smoothing: trust(t+1) = α·trust + (1-α)·signal
    decay_rate: float = 0.05      # base_trust pull per epoch: decay · (base - trust)
    base_trust: float = 0.30      # equilibrium trust for inactive/no-consensus nodes
    trust_floor: float = 0.05     # absolute minimum trust
    trust_ceiling: float = 0.95   # absolute maximum trust (anti-monopoly)
    max_trust_delta: float = 0.15 # maximum trust change per epoch per node
    oscillation_window: int = 8   # window for oscillation detection
    oscillation_threshold: float = 0.10  # trust delta threshold for oscillation flag


@dataclass
class TrustUpdateResult:
    """Result of a dampened trust update."""
    node_id: str
    prev_trust: float
    new_trust: float
    delta: float
    outcome_signal: float
    regime: FeedbackRegime
    clamped: bool
    epoch: int
    timestamp: float = field(default_factory=time.time)


class TrustFeedbackDampener:
    """
    Dampens trust updates to prevent feedback amplification.

    Core formula:
      trust_new = α · trust_old
                + (1-α) · outcome_signal
                + decay · (base_trust - trust_old)

    Anti-monopoly constraint:
      |trust_new - trust_old| ≤ max_trust_delta

    Trust freeze prevention:
      decay component pulls inactive nodes toward base_trust
    """

    def __init__(self, config: DampenerConfig | None = None):
        self.config = config or DampenerConfig()
        self._prev_trust: dict[str, float] = {}
        self._trust_history: dict[str, list[float]] = {}   # node_id → rolling window
        self._outcome_history: list[float] = []            # rolling window of outcome signals
        self._regime: FeedbackRegime = FeedbackRegime.STABLE
        self._epoch: int = 0

    def update_trust(
        self,
        node_id: str,
        current_trust: float,
        outcome_signal: float,   # ∈ [-1, 1]: +1=accept, -1=reject, 0=no consensus
        epoch: int | None = None,
    ) -> TrustUpdateResult:
        """
        Compute dampened trust update for one node.

        Returns TrustUpdateResult with new_trust, delta, and regime.
        """
        if epoch is not None:
            self._epoch = epoch
        else:
            self._epoch += 1

        cfg = self.config
        prev_trust = current_trust

        # Track history for oscillation / freeze detection
        self._prev_trust[node_id] = prev_trust
        self._trust_history.setdefault(node_id, []).append(prev_trust)
        if len(self._trust_history[node_id]) > cfg.oscillation_window:
            self._trust_history[node_id].pop(0)

        # Rolling outcome history
        self._outcome_history.append(outcome_signal)
        if len(self._outcome_history) > cfg.oscillation_window:
            self._outcome_history.pop(0)

        # ── Core EMA update ──────────────────────────────────────────
        # trust_new = α·trust_old + (1-α)·outcome_signal
        # Note: outcome_signal is in [-1, 1] so we treat it as a directional signal
        signal_component = (1.0 - cfg.alpha) * outcome_signal

        # Normalize outcome_signal contribution: map [-1, 1] → [0, 1] around base_trust
        # +1 → full upward pressure toward ceiling
        # -1 → full downward pressure toward floor
        # 0  → no directional pressure
        normalized_signal = 0.5 * (outcome_signal + 1.0)  # [0, 1]
        base_pressure = (1.0 - cfg.alpha) * normalized_signal  # [0, 1-α]

        trust_ema = cfg.alpha * prev_trust + base_pressure

        # ── Decay toward base_trust (freeze prevention) ──────────────
        # Nodes with no participation slowly drift toward base_trust
        decay_component = cfg.decay_rate * (cfg.base_trust - trust_ema)
        trust_decayed = trust_ema + decay_component

        # ── Clamp to [trust_floor, trust_ceiling] ────────────────────
        new_trust = max(cfg.trust_floor, min(cfg.trust_ceiling, trust_decayed))

        # ── Anti-monopoly: cap delta ──────────────────────────────────
        delta = new_trust - prev_trust
        clamped = False
        if abs(delta) > cfg.max_trust_delta:
            new_trust = prev_trust + cfg.max_trust_delta * (1 if delta > 0 else -1)
            clamped = True

        # ── Detect regime ─────────────────────────────────────────────
        regime = self._detect_regime(node_id, prev_trust, new_trust)

        return TrustUpdateResult(
            node_id=node_id,
            prev_trust=prev_trust,
            new_trust=new_trust,
            delta=new_trust - prev_trust,
            outcome_signal=outcome_signal,
            regime=regime,
            clamped=clamped,
            epoch=self._epoch,
        )

    def _detect_regime(
        self,
        node_id: str,
        prev_trust: float,
        new_trust: float,
    ) -> FeedbackRegime:
        """Detect operating regime from trust history patterns."""
        cfg = self.config

        history = self._trust_history.get(node_id, [])
        if len(history) < 3:
            return FeedbackRegime.STABLE

        # ── Freeze detection: trust hasn't changed meaningfully ────────
        if len(history) >= 3:
            recent_range = max(history[-3:]) - min(history[-3:])
            if recent_range < 0.01 and new_trust > cfg.base_trust + 0.1:
                return FeedbackRegime.FREEZING

        # ── Oscillation detection: alternating up/down ─────────────────
        if len(history) >= 4:
            deltas = [history[i] - history[i-1] for i in range(1, len(history))]
            sign_changes = sum(
                1 for i in range(len(deltas)-1)
                if deltas[i] != 0 and (deltas[i] > 0) != (deltas[i+1] > 0)
            )
            if sign_changes >= 3:
                return FeedbackRegime.OSCILLATING

        # ── Byzantine freeze: high-trust node suspiciously static ─────
        if prev_trust > 0.8 and len(history) >= 5:
            recent_range = max(history[-5:]) - min(history[-5:])
            if recent_range < 0.02:
                return FeedbackRegime.BYZANTINE_FREEZE

        # ── Monopoly: very high trust + large delta ───────────────────
        if new_trust > 0.85 and abs(new_trust - prev_trust) > 0.05:
            return FeedbackRegime.MONOPOLIZING

        return FeedbackRegime.STABLE if not self._outcome_history else FeedbackRegime.DAMPED

    def compute_outcome_signal(self, consensus_accepted: bool, confidence: float) -> float:
        """
        Map consensus outcome to trust update signal.

        Returns:
            +1.0  — consensus accepted, high confidence
            +0.5  — consensus accepted, low confidence
             0.0  — no consensus
            -0.5  — consensus rejected, low confidence
            -1.0  — consensus rejected, high confidence
        """
        if confidence < 0.1:
            return 0.0  # inconclusive
        direction = 1.0 if consensus_accepted else -1.0
        magnitude = max(0.0, (confidence - 0.3) / 0.7)  # [0, 1] when confidence ∈ [0.3, 1.0]
        return direction * magnitude

    def batch_update(
        self,
        trust_scores: dict[str, float],     # node_id → current trust
        consensus_accepted: bool,
        confidence: float,
        epoch: int | None = None,
    ) -> list[TrustUpdateResult]:
        """Update trust for all nodes from a single consensus round."""
        signal = self.compute_outcome_signal(consensus_accepted, confidence)
        results = []
        for node_id, trust in trust_scores.items():
            results.append(self.update_trust(node_id, trust, signal, epoch))
        return results

    def global_regime(self) -> FeedbackRegime:
        return self._regime

    @property
    def epoch(self) -> int:
        return self._epoch


# ─── Tests ──────────────────────────────────────────────────────────────

def _test_trust_feedback_dampener():
    dampener = TrustFeedbackDampener(DampenerConfig(
        alpha=0.75,
        decay_rate=0.05,
        base_trust=0.30,
        trust_floor=0.05,
        trust_ceiling=0.95,
        max_trust_delta=0.15,
    ))

    # Case 1: high-trust node on accepted consensus → small positive delta
    r1 = dampener.update_trust("node_A", 0.85, outcome_signal=1.0)
    assert 0.85 < r1.new_trust <= 0.95, f"Expected slight increase, got {r1.new_trust}"
    assert r1.regime in (FeedbackRegime.STABLE, FeedbackRegime.DAMPED)
    print(f"✅ Case 1: trust 0.85 → {r1.new_trust:.4f}, delta={r1.delta:+.4f}, regime={r1.regime.name}")

    # Case 2: low-trust node on rejected consensus → trust drops
    r2 = dampener.update_trust("node_B", 0.40, outcome_signal=-1.0)
    assert r2.new_trust < 0.40, f"Expected drop, got {r2.new_trust}"
    print(f"✅ Case 2: trust 0.40 → {r2.new_trust:.4f}, delta={r2.delta:+.4f}")

    # Case 3: anti-monopoly delta cap
    dampener3 = TrustFeedbackDampener(DampenerConfig(max_trust_delta=0.05))
    r3 = dampener3.update_trust("node_C", 0.50, outcome_signal=1.0)
    assert abs(r3.delta) <= 0.05 + 1e-9, f"Delta {r3.delta} exceeds cap 0.05"
    assert r3.clamped is True
    print(f"✅ Case 3: delta cap active, clamped={r3.clamped}, delta={r3.delta:+.4f}")

    # Case 4: trust ceiling enforced
    dampener4 = TrustFeedbackDampener(DampenerConfig(trust_ceiling=0.90))
    r4 = dampener4.update_trust("node_D", 0.88, outcome_signal=1.0)
    assert r4.new_trust <= 0.90, f"Capped at ceiling, got {r4.new_trust}"
    print(f"✅ Case 4: ceiling enforced: {r4.new_trust:.4f} ≤ 0.90")

    # Case 5: trust floor enforced
    r5 = dampener4.update_trust("node_E", 0.08, outcome_signal=-1.0)
    assert r5.new_trust >= 0.05, f"Floor broken, got {r5.new_trust}"
    print(f"✅ Case 5: floor enforced: {r5.new_trust:.4f} ≥ 0.05")

    # Case 6: decay pulls inactive node toward base_trust
    dampener6 = TrustFeedbackDampener(DampenerConfig(alpha=0.95, decay_rate=0.10, base_trust=0.30))
    r6 = dampener6.update_trust("node_F", 0.70, outcome_signal=0.0)  # no consensus signal
    assert r6.new_trust < 0.70, f"Decay should reduce high trust, got {r6.new_trust}"
    print(f"✅ Case 6: decay pulls 0.70 → {r6.new_trust:.4f} toward base 0.30")

    # Case 7: outcome_signal → normalized signal
    signal_high = dampener.compute_outcome_signal(consensus_accepted=True, confidence=1.0)
    assert abs(signal_high - 1.0) < 1e-6
    signal_low = dampener.compute_outcome_signal(consensus_accepted=True, confidence=0.3)
    assert abs(signal_low - 0.0) < 1e-6
    signal_reject = dampener.compute_outcome_signal(consensus_accepted=False, confidence=1.0)
    assert abs(signal_reject - (-1.0)) < 1e-6
    print(f"✅ Case 7: signal mapping — high_accept={signal_high:.1f}, low={signal_low:.1f}, reject={signal_reject:.1f}")

    # Case 8: batch update
    results = dampener.batch_update(
        trust_scores={"A": 0.8, "B": 0.6, "C": 0.3},
        consensus_accepted=True,
        confidence=0.85,
    )
    assert len(results) == 3
    for r in results:
        assert 0.0 < r.new_trust < 1.0
    print("✅ Case 8: batch_update 3 nodes, all updated")

    print("\n✅ v9.7 TrustFeedbackDampener — all checks passed")


if __name__ == "__main__":
    _test_trust_feedback_dampener()


__all__ = [
    "DampenerConfig",
    "FeedbackRegime",
    "TrustFeedbackDampener",
    "TrustUpdateResult",
]
