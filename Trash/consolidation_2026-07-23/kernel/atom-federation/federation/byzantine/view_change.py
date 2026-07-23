"""
view_change.py — Cooperative view-change mechanism for PBFT-lite v9.8
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto


class ViewChangeReason(Enum):
    ENTROPY_FREEZE = auto()
    TRUST_COLLAPSE = auto()
    STALLED_ROUND = auto()
    BYZANTINE_SIGNAL = auto()
    TIMEOUT = auto()
    EXPLICIT_ROTATION = auto()


@dataclass
class ViewChangeEvent:
    view: int
    reason: ViewChangeReason
    leader_id: str
    new_leader_id: str
    timestamp: float
    triggered_by: str


class ViewChangeManager:
    """Cooperative leader rotation. Lightweight (not full PBFT view-change)."""

    def __init__(self, node_id: str, n_nodes: int):
        self.node_id = node_id
        self.n_nodes = n_nodes
        self._current_view: int = 0
        self._current_leader: str = ""
        self._round_start_tick: int = 0
        self._stall_threshold_ticks: int = 3
        self._pending_vc: list[ViewChangeEvent] = []

    def current_leader(self) -> str:
        return self._current_leader

    def current_view(self) -> int:
        return self._current_view

    def select_leader(self, view: int, peer_ids: list[str]) -> str:
        if not peer_ids:
            return self.node_id
        return peer_ids[view % len(peer_ids)]

    def should_trigger_view_change(
        self,
        reason: ViewChangeReason,
        current_tick: int,
    ) -> bool:
        if reason == ViewChangeReason.TIMEOUT:
            return (current_tick - self._round_start_tick) >= self._stall_threshold_ticks
        return reason in (
            ViewChangeReason.ENTROPY_FREEZE,
            ViewChangeReason.TRUST_COLLAPSE,
            ViewChangeReason.BYZANTINE_SIGNAL,
        )

    def trigger_view_change(
        self,
        reason: ViewChangeReason,
        peer_ids: list[str],
        triggered_by: str,
    ) -> ViewChangeEvent:
        self._current_view += 1
        old_leader = self._current_leader
        new_leader = self.select_leader(self._current_view, peer_ids)
        self._current_leader = new_leader
        event = ViewChangeEvent(
            view=self._current_view,
            reason=reason,
            leader_id=old_leader,
            new_leader_id=new_leader,
            timestamp=time.time(),
            triggered_by=triggered_by,
        )
        self._pending_vc.append(event)
        self._round_start_tick = 0
        return event

    def on_round_start(self, tick: int) -> None:
        self._round_start_tick = tick

    def pending_view_changes(self) -> list[ViewChangeEvent]:
        return list(self._pending_vc)

    def clear_pending(self) -> None:
        self._pending_vc.clear()

    def set_stall_threshold(self, ticks: int) -> None:
        self._stall_threshold_ticks = ticks


__all__ = [
    "ViewChangeEvent",
    "ViewChangeManager",
    "ViewChangeReason",
]
