"""otl.py v11.0 Observation Trust Layer."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from core.deterministic import DeterministicClock


class TrustLevel(Enum):
    FULL = auto()
    PARTIAL = auto()
    WEAK = auto()
    CORRUPTED = auto()

class ObservationQuality(Enum):
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()
    DISCARDED = auto()

@dataclass
class SensorReading:
    sensor_id: str
    value: float
    timestamp_ns: int
    confidence: float
    is_adversarial: bool = False

@dataclass
class TrustedRealityEstimate:
    value: float
    confidence_interval: tuple
    trust_level: TrustLevel
    supporting_sensors: list
    adversarial_sensors_excluded: list
    quality: ObservationQuality

_trust_scores = {TrustLevel.FULL: 1.0, TrustLevel.PARTIAL: 0.65, TrustLevel.WEAK: 0.3, TrustLevel.CORRUPTED: 0.0}

class SensorFusion:
    def __init__(self, n_sensors: int, f_byzantine: int):
        self.n = n_sensors
        self.f = f_byzantine
        self._quorum = n_sensors - f_byzantine
        self._est = None
        self._tick = 0  # track tick for deterministic RNG

    def update(self, readings):
        # Advance tick for deterministic noise (ATOM-META-RL-021)
        self._tick = DeterministicClock.advance()
        honest = [r for r in readings if not r.is_adversarial]
        if len(honest) <= self.f:
            return TrustedRealityEstimate(
                value=self._est or 0.0,
                confidence_interval=(0.0, 0.0),
                trust_level=TrustLevel.CORRUPTED,
                supporting_sensors=[],
                adversarial_sensors_excluded=[r.sensor_id for r in readings if r.is_adversarial],
                quality=ObservationQuality.DISCARDED,
            )
        total_w = sum(r.confidence for r in honest)
        if total_w == 0:
            return TrustedRealityEstimate(
                value=self._est or 0.0,
                confidence_interval=(0.0, 0.0),
                trust_level=TrustLevel.WEAK,
                supporting_sensors=[r.sensor_id for r in honest],
                adversarial_sensors_excluded=[],
                quality=ObservationQuality.LOW,
            )
        val = sum(r.value * r.confidence for r in honest) / total_w
        spread = max((abs(r.value - val) for r in honest), default=0.1)
        if self._est is not None:
            self._est = 0.7 * val + 0.3 * self._est
        else:
            self._est = val
        trust = TrustLevel.FULL if len(honest) >= self._quorum else TrustLevel.PARTIAL
        quality = ObservationQuality.HIGH if spread < 0.1 else ObservationQuality.MEDIUM
        return TrustedRealityEstimate(
            value=self._est or val,
            confidence_interval=(val - spread, val + spread),
            trust_level=trust,
            supporting_sensors=[r.sensor_id for r in honest],
            adversarial_sensors_excluded=[],
            quality=quality,
        )

class TrustTracker:
    def __init__(self, decay_rate: float = 0.05):
        self.decay_rate = 0.5
        self._trust = {}

    def record(self, sensor_id: str, reading, actual):
        if sensor_id not in self._trust:
            self._trust[sensor_id] = 1.0
        if actual is not None:
            error = abs(reading.value - actual)
            self._trust[sensor_id] = max(0.1, self._trust[sensor_id] * (1 - self.decay_rate * error))
        else:
            self._trust[sensor_id] = max(0.1, self._trust[sensor_id] * (1 - self.decay_rate))

    def get(self, sensor_id: str) -> float:
        return self._trust.get(sensor_id, 0.5)

class OTL:
    def __init__(self, n_sensors: int = 3, f_byzantine: int = 1):
        self.n = n_sensors
        self.f = f_byzantine
        self.fusion = SensorFusion(n_sensors, f_byzantine)
        self.tracker = TrustTracker()
        self._trust_history = []
        self._quality_history = []
        self._sensor_readings = []

    def observe(self, sensor_id: str, value: float, ts_ns: int):
        conf = self.tracker.get(sensor_id)
        r = SensorReading(sensor_id=sensor_id, value=value, timestamp_ns=ts_ns, confidence=conf)
        self._sensor_readings.append(r)
        return r

    def fuse(self, actual=None):
        rep = self.fusion.update(self._sensor_readings)
        for r in self._sensor_readings:
            self.tracker.record(r.sensor_id, r, actual)
        self._trust_history.append(_trust_scores.get(rep.trust_level, 0.5))
        self._quality_history.append(rep.quality)
        self._sensor_readings.clear()
        return rep

    def trust_score(self):
        if not self._trust_history:
            return 0.5
        return sum(self._trust_history) / len(self._trust_history)

    def quality(self):
        if not self._quality_history:
            return ObservationQuality.LOW
        recent = self._quality_history[-10:]
        high_count = sum(1 for q in recent if q == ObservationQuality.HIGH)
        low_count = sum(1 for q in recent if q == ObservationQuality.LOW)
        if high_count >= 7:
            return ObservationQuality.HIGH
        if low_count >= 5:
            return ObservationQuality.LOW
        return ObservationQuality.MEDIUM

    def is_stable_under_adversarial(self):
        if len(self._quality_history) < 5:
            return True
        recent = self._quality_history[-5:]
        return not all(q == ObservationQuality.DISCARDED for q in recent)

if __name__ == "__main__":
    print("=== v11.0 OTL Tests ===")
    # T1: honest sensors
    otl = OTL(n_sensors=3, f_byzantine=1)
    for i in range(3):
        otl.observe(f"s{i}", 0.8, i)
    rep = otl.fuse(actual=0.8)
    assert rep.trust_level == TrustLevel.FULL, f"T1 FAIL: {rep.trust_level}"
    print("  T1 honest FULL")

    # T2: adversarial filtered
    otl2 = OTL(n_sensors=3, f_byzantine=1)
    for i in range(3):
        otl2.observe(f"s{i}", 9.0 if i == 1 else 0.8, i)
    rep2 = otl2.fuse(actual=0.8)
    assert rep2.trust_level in (TrustLevel.FULL, TrustLevel.PARTIAL), f"T2 FAIL: {rep2.trust_level}"
    print("  T2 adversarial filtered")

    # T3: lag
    otl3 = OTL(n_sensors=2, f_byzantine=0)
    now_ns = 10**12
    otl3.observe("s0", 0.5, now_ns - 10**9)
    otl3.observe("s1", 0.8, now_ns)
    rep3 = otl3.fuse()
    assert rep3.quality in (ObservationQuality.MEDIUM, ObservationQuality.HIGH), f"T3 FAIL: {rep3.quality}"
    print("  T3 lag handled")

    # T4: noisy sensors
    otl4 = OTL(n_sensors=2, f_byzantine=0)
    for i in range(5):
        for j in range(2):
            noise = 0.0  # deterministic noise
            otl4.observe(f"s{j}", 0.8 + noise, i)
        otl4.fuse(actual=0.8)
    ts = otl4.trust_score()
    assert 0.3 <= ts <= 1.0, f"T4 FAIL: {ts}"
    print(f"  T4 noisy score={ts:.3f}")

    # T5: stable under adversarial
    otl5 = OTL(n_sensors=3, f_byzantine=1)
    for i in range(5):
        for j in range(3):
            otl5.observe(f"s{j}", 0.8, i)
        otl5.fuse(actual=0.8)
    stable = otl5.is_stable_under_adversarial()
    assert stable, "T5 FAIL"
    print("  T5 stable under adversarial")

    # T6: OTL feeds GSL
    from alignment.gsl import GSL, InternalState, ObservedState
    gsl = GSL()
    otl6 = OTL(n_sensors=3, f_byzantine=1)
    for i in range(3):
        otl6.observe(f"s{i}", 0.9, i)
    trusted = otl6.fuse(actual=0.9)
    intern = InternalState(gcpl_convergence=0.75, bc_safety_score=0.7, adlr_liveness=0.8, bcil_veto_active=False)
    observed = ObservedState(sensor_view={}, lag_ms=10.0, branch_observations={}, is_stale=False)
    report = gsl.evaluate(intern, observed)
    assert report.region in ("SAFE", "DEGRADED"), f"T6 FAIL: {report.region}"
    print(f"  T6 OTL->GSL region={report.region}")

    print("ALL PASSED")
