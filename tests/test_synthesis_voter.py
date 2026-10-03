"""Unit tests for synthesis/voter.py no_data abstain.

Covers the is_no_data() semantic ported from wip/local-workspace-sync@7d7e294:
signals marked no_data / degraded / confidence==0 must abstain and not enter
the weighted-vote denominator.
"""

from __future__ import annotations

from agents._impl.synthesis.formatting import get_signal_attr
from agents._impl.synthesis.voter import vote
from core.base_agent import SignalDirection


def _sig(signal: str, confidence: int, metadata: dict | None = None) -> dict:
    d: dict = {"signal": signal, "confidence": confidence}
    if metadata is not None:
        d["metadata"] = metadata
    return d


def _vote(signals: list[dict]) -> tuple[SignalDirection, int, str]:
    return vote({"cat": signals}, get_signal_attr, eff={"cat": 1.0})


def test_no_data_metadata_abstains_from_denominator():
    # 2 live LONG + 1 no_data SHORT => counted as 2/2 (100% LONG), not 2/3.
    signals = [
        _sig("LONG", 80),
        _sig("LONG", 80),
        _sig("SHORT", 60, metadata={"no_data": True}),
    ]
    direction, confidence, _ = _vote(signals)
    assert direction == SignalDirection.LONG
    assert confidence == 90  # 100% long -> 50 + 40, capped at MAX_CONFIDENCE=90

    # no_data is a no-op: identical result without the abstaining ballot
    direction2, confidence2, _ = _vote([_sig("LONG", 80), _sig("LONG", 80)])
    assert (direction2, confidence2) == (direction, confidence)


def test_confidence_zero_abstains():
    signals = [_sig("LONG", 100), _sig("SHORT", 0)]
    direction, confidence, _ = _vote(signals)
    assert direction == SignalDirection.LONG
    assert confidence == 90


def test_degraded_metadata_abstains():
    signals = [_sig("LONG", 100), _sig("SHORT", 100, metadata={"degraded": True})]
    direction, confidence, _ = _vote(signals)
    assert direction == SignalDirection.LONG
    assert confidence == 90


def test_live_votes_keep_55_percent_threshold():
    # balanced 2 vs 2 -> NEUTRAL (no 55% majority)
    direction, confidence, _ = _vote(
        [
            _sig("LONG", 100),
            _sig("LONG", 100),
            _sig("SHORT", 100),
            _sig("SHORT", 100),
        ]
    )
    assert direction == SignalDirection.NEUTRAL
    assert confidence == 50

    # 3 vs 1 -> LONG (0.75 > 0.55)
    direction2, _confidence2, _ = _vote(
        [
            _sig("LONG", 100),
            _sig("LONG", 100),
            _sig("LONG", 100),
            _sig("SHORT", 100),
        ]
    )
    assert direction2 == SignalDirection.LONG
