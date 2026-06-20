"""Feature-pipeline protocols.

The `WindowEngine` god-node shows up in `home-cluster-iac/feature_pipeline/
window_engine.py` and `AsurDev/feature_pipeline/window_engine.py`. They are
*identical* line-for-line. This module lifts the protocol so any other repo
can depend on the contract without copying the implementation.

The cross-repo Surprising Connection
`Backend → WindowEngine` (AsurDev/feature_pipeline ↔ home-cluster-iac)
closes once both sides depend on this contract.

See ADR-0002 for the full rationale.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SlidingWindowProtocol(Protocol):
    """Time-bounded buffer of `(timestamp, value)` samples.

    Subset of `home-cluster-iac/feature_pipeline/window_engine.py:SlidingWindow`.
    """

    node_id: str
    metric: str
    window_seconds: int

    def push(self, value: float, timestamp: datetime | None = None) -> None: ...

    def get_window(self, cutoff: datetime) -> list[float]: ...

    def get_values(self) -> list[float]: ...

    def get_timestamps(self) -> list[datetime]: ...

    def aggregate(self, agg: str) -> float: ...

    def clear(self) -> None: ...


@runtime_checkable
class WindowEngineProtocol(Protocol):
    """Central window manager — `{(node_id, metric, ws): SlidingWindow}`."""

    def push(
        self,
        node_id: str,
        metric: str,
        value: float,
        timestamp: datetime | None = None,
    ) -> None: ...

    def get_window_data(
        self,
        node_id: str,
        metric: str,
        window_seconds: int,
    ) -> list[float]: ...

    def get_aggregated(
        self,
        node_id: str,
        metric: str,
        window_seconds: int,
        agg: str,
    ) -> float: ...

    def get_all_windows_for_node(self, node_id: str) -> dict[str, dict[str, float]]: ...

    def clear_node(self, node_id: str) -> None: ...


__all__ = [
    "SlidingWindowProtocol",
    "WindowEngineProtocol",
]


# Legacy alias.
WindowEngine = WindowEngineProtocol     # type: ignore[misc, assignment]
