"""Chronological Development / Validation / Final-OOS split and walk-forward windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .errors import ChronologyError
from .leakage import Bar, assert_chronological


@dataclass(frozen=True)
class Segment:
    name: str
    start: int  # inclusive bar index
    end: int  # exclusive bar index

    def __post_init__(self) -> None:
        if not (0 <= self.start < self.end):
            raise ChronologyError(f"segment {self.name}: empty or negative range [{self.start},{self.end})")

    def __len__(self) -> int:
        return self.end - self.start

    def boundaries(self, bars: Sequence[Bar]) -> dict:
        return {"name": self.name, "start_index": self.start, "end_index": self.end,
                "first_ts": bars[self.start].ts.isoformat(), "last_ts": bars[self.end - 1].ts.isoformat()}


@dataclass(frozen=True)
class Split:
    development: Segment
    validation: Segment
    final_oos: Segment
    embargo_bars: int

    def segments(self) -> tuple[Segment, Segment, Segment]:
        return (self.development, self.validation, self.final_oos)

    def boundaries(self, bars: Sequence[Bar]) -> dict:
        return {"embargo_bars": self.embargo_bars, "n_bars": len(bars),
                "segments": [s.boundaries(bars) for s in self.segments()]}


def assert_ordered(segments: Sequence[Segment], embargo_bars: int, n_bars: int | None = None) -> None:
    """Refuse overlap, reordering or a gap smaller than the embargo (lookahead in the split)."""
    for a, b in zip(segments, segments[1:]):
        if b.start < a.end:
            raise ChronologyError(f"segments overlap: {a.name}[{a.start},{a.end}) / {b.name}[{b.start},{b.end})")
        if b.start - a.end < embargo_bars:
            raise ChronologyError(
                f"embargo violated between {a.name} and {b.name}: gap {b.start - a.end} < {embargo_bars} bars"
            )
    if n_bars is not None and segments and segments[-1].end > n_bars:
        raise ChronologyError(f"segment {segments[-1].name} ends beyond data ({segments[-1].end} > {n_bars})")


def chronological_split(
    bars: Sequence[Bar], *, dev_fraction: float, validation_fraction: float, embargo_bars: int
) -> Split:
    """Split bars by time: [Dev] gap [Validation] gap [Final OOS]; gaps of ``embargo_bars`` are purged."""
    assert_chronological(bars)
    if embargo_bars < 0:
        raise ChronologyError("embargo_bars must be >= 0")
    if not (0 < dev_fraction < 1 and 0 < validation_fraction < 1 and dev_fraction + validation_fraction < 1):
        raise ChronologyError("fractions must be in (0,1) and leave room for final OOS")
    usable = len(bars) - 2 * embargo_bars
    n_dev = int(usable * dev_fraction)
    n_val = int(usable * validation_fraction)
    n_oos = usable - n_dev - n_val
    if min(n_dev, n_val, n_oos) < 1:
        raise ChronologyError(f"not enough bars ({len(bars)}) for split with embargo {embargo_bars}")
    dev = Segment("development", 0, n_dev)
    val = Segment("validation", n_dev + embargo_bars, n_dev + embargo_bars + n_val)
    oos = Segment("final_oos", val.end + embargo_bars, len(bars))
    split = Split(dev, val, oos, embargo_bars)
    assert_ordered(split.segments(), embargo_bars, len(bars))
    return split


def walk_forward_windows(
    region: Segment, *, train_bars: int, test_bars: int, embargo_bars: int, anchored: bool = False
) -> list[tuple[Segment, Segment]]:
    """(train, test) windows inside ``region`` only. Test follows train after the embargo; step = test_bars."""
    if train_bars < 1 or test_bars < 1:
        raise ChronologyError("train_bars and test_bars must be >= 1")
    out: list[tuple[Segment, Segment]] = []
    k = 0
    while True:
        train_end = region.start + train_bars + k * test_bars
        test_start = train_end + embargo_bars
        test_end = test_start + test_bars
        if test_end > region.end:
            break
        train_start = region.start if anchored else train_end - train_bars
        tr = Segment(f"wf{k}_train", train_start, train_end)
        te = Segment(f"wf{k}_test", test_start, test_end)
        assert_ordered((tr, te), embargo_bars)
        out.append((tr, te))
        k += 1
    if not out:
        raise ChronologyError(f"region {region.name} too short for one walk-forward window")
    return out
