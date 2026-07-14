from dataclasses import dataclass
from typing import Any


@dataclass
class ControlSignal:
    source: str
    priority: float
    payload: dict[str, Any]


class ControlArbitrator:
    """
    Resolves competing actuator signals across control layers:
    DRL / SBS / Coherence / Actuator feedback loops.
    Deterministic: highest priority wins; ties broken by stable source name order.
    """

    def __init__(self) -> None:
        self._signals: list[ControlSignal] = []

    def submit(self, signal: ControlSignal) -> None:
        self._signals.append(signal)

    def resolve(self) -> ControlSignal:
        if not self._signals:
            raise RuntimeError("No control signals submitted")
        ordered = sorted(
            self._signals,
            key=lambda s: (-s.priority, s.source),
        )
        winner = ordered[0]
        self._signals.clear()
        return winner

    def resolve_many(self) -> list[ControlSignal]:
        """Return all signals sorted by priority (highest first), no clear."""
        if not self._signals:
            return []
        return sorted(
            self._signals,
            key=lambda s: (-s.priority, s.source),
        )

    @property
    def pending_count(self) -> int:
        return len(self._signals)
