"""
AdaptiveRouter v6.4 — DRL++: loss-aware, latency-aware routing.

Routes around degraded paths based on real-time DRL metrics:
  - Per-peer latency EMA (exponential moving average)
  - Per-peer loss rate EMA
  - Per-peer weight for weighted random routing
  - SLO-gated routing (skip peers that violate SLO)

Usage:
    router = AdaptiveRouter(node_id="node-a", peers=["b","c","d"])
    router.update_peer_metrics("node-b", latency_ms=45.0, loss_rate=0.02)
    route = router.route(command="forward")  # returns best peer
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

__all__ = ["AdaptiveRouter", "PeerRouteState", "RouteMetrics"]


# ── SLO thresholds ────────────────────────────────────────────────────────────

DEFAULT_LATENCY_SLO_MS = 100.0
DEFAULT_LOSS_SLO = 0.05        # 5% packet loss
DEFAULT_CLOCK_SKEW_SLO_MS = 5000.0  # 5 seconds clock drift


# ── Peer route state ──────────────────────────────────────────────────────────

@dataclass
class PeerRouteState:
    node_id: str
    latency_ema: float = 0.0
    loss_rate_ema: float = 0.0
    clock_skew_ema: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    weight: float = 1.0
    last_seen: float = field(default_factory=time.monotonic)
    in_rotation: bool = True
    violating_slo: bool = False

    def update(
        self,
        latency_ms: float | None = None,
        loss_rate: float | None = None,
        clock_skew_ms: float | None = None,
        success: bool = True,
        latency_slo: float = DEFAULT_LATENCY_SLO_MS,
        loss_slo: float = DEFAULT_LOSS_SLO,
        skew_slo: float = DEFAULT_CLOCK_SKEW_SLO_MS,
    ) -> None:
        """Update EMA metrics after an RPC attempt."""
        alpha = 0.3  # EMA smoothing factor

        if latency_ms is not None:
            if self.latency_ema == 0:
                self.latency_ema = latency_ms
            else:
                self.latency_ema = alpha * latency_ms + (1 - alpha) * self.latency_ema

        if loss_rate is not None:
            if self.loss_rate_ema == 0:
                self.loss_rate_ema = loss_rate
            else:
                self.loss_rate_ema = alpha * loss_rate + (1 - alpha) * self.loss_rate_ema

        if clock_skew_ms is not None:
            if self.clock_skew_ema == 0:
                self.clock_skew_ema = clock_skew_ms
            else:
                self.clock_skew_ema = alpha * clock_skew_ms + (1 - alpha) * self.clock_skew_ema

        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0

        self.last_seen = time.monotonic()

        # Recalculate weight: inverse of latency * inverse of loss
        self._recompute_weight(latency_slo, loss_slo, skew_slo)

        # Check SLO violations
        self.violating_slo = (
            self.latency_ema > latency_slo
            or self.loss_rate_ema > loss_slo
            or abs(self.clock_skew_ema) > skew_slo
            or self.consecutive_failures >= 3
        )

        # Auto-return to rotation after recovery
        if not self.violating_slo and not self.in_rotation:
            self.in_rotation = True

    def _recompute_weight(
        self,
        latency_slo: float,
        loss_slo: float,
        skew_slo: float,
    ) -> None:
        """
        Weight = 1 / (1 + normalized_latency * normalized_loss)
        Normalized = value / SLO (capped at 1.0 so overweighted bad peers don't go to 0)
        """
        norm_lat = min(self.latency_ema / max(latency_slo, 1), 2.0)
        norm_loss = min(self.loss_rate_ema / max(loss_slo, 0.001), 2.0)
        norm_skew = min(abs(self.clock_skew_ema) / max(skew_slo, 1), 2.0)
        combined = max(norm_lat * norm_loss * (1 + norm_skew * 0.1), 0.01)
        self.weight = 1.0 / combined

    def mark_removed_from_rotation(self) -> None:
        self.in_rotation = False
        self.weight = 0.0

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "latency_ema_ms": round(self.latency_ema, 2),
            "loss_rate_ema": round(self.loss_rate_ema, 4),
            "clock_skew_ema_ms": round(self.clock_skew_ema, 2),
            "consecutive_failures": self.consecutive_failures,
            "weight": round(self.weight, 4),
            "in_rotation": self.in_rotation,
            "violating_slo": self.violating_slo,
        }


# ── Route decision ─────────────────────────────────────────────────────────────

@dataclass
class RouteMetrics:
    chosen_peer: str | None
    all_peers: list[str]
    weights: dict[str, float]
    skipped: list[str]  # peers skipped due to SLO violation
    reason: str


# ── AdaptiveRouter ─────────────────────────────────────────────────────────────

class AdaptiveRouter:
    """
    DRL++ layer: loss-aware and latency-aware routing.

    Wraps the raw DRL transport with a routing intelligence layer.
    Tracks per-peer EMA metrics and selects the best peer for each RPC.

    Key behaviors:
      - SLO-gated: peers violating latency/loss SLO are removed from rotation
              (but NOT evicted from cluster — that's the healer's job)
      - Weighted random: among healthy peers, route proportionally to weight
              (lower latency + lower loss = higher weight)
      - Probe mode: if ALL peers are degraded, use the least-bad one
      - Thread-safe: all state protected by lock
    """

    def __init__(
        self,
        node_id: str,
        peers: list[str],
        latency_slo_ms: float = DEFAULT_LATENCY_SLO_MS,
        loss_slo: float = DEFAULT_LOSS_SLO,
        skew_slo_ms: float = DEFAULT_CLOCK_SKEW_SLO_MS,
    ) -> None:
        self.node_id = node_id
        self.peers = list(peers)
        self._latency_slo = latency_slo_ms
        self._loss_slo = loss_slo
        self._skew_slo = skew_slo_ms

        self._state: dict[str, PeerRouteState] = {}
        self._lock = threading.RLock()
        self._route_count = 0
        self._skipped_count = 0

        for p in peers:
            self._state[p] = PeerRouteState(node_id=p)

    # ── Metric updates ────────────────────────────────────────────────────

    def update_peer_metrics(
        self,
        peer: str,
        latency_ms: float | None = None,
        loss_rate: float | None = None,
        clock_skew_ms: float | None = None,
        success: bool = True,
    ) -> None:
        """Called after each RPC attempt to update peer state."""
        with self._lock:
            if peer not in self._state:
                self._state[peer] = PeerRouteState(node_id=peer)
            self._state[peer].update(
                latency_ms=latency_ms,
                loss_rate=loss_rate,
                clock_skew_ms=clock_skew_ms,
                success=success,
                latency_slo=self._latency_slo,
                loss_slo=self._loss_slo,
                skew_slo=self._skew_slo,
            )

    def remove_peer_from_rotation(self, peer: str) -> None:
        """Manually remove peer from routing rotation (e.g., during healing)."""
        with self._lock:
            if peer in self._state:
                self._state[peer].mark_removed_from_rotation()

    def restore_peer_to_rotation(self, peer: str) -> None:
        """Restore peer to routing rotation after it recovers."""
        with self._lock:
            if peer in self._state:
                self._state[peer].in_rotation = True
                self._state[peer]._recompute_weight(
                    self._latency_slo, self._loss_slo, self._skew_slo
                )

    # ── Routing decision ──────────────────────────────────────────────────

    def route(self, command: str | None = None, tick: int = 0) -> RouteMetrics:
        """
        Choose the best peer for routing.

        Strategy:
          1. Filter to in-rotation peers
          2. Filter out SLO-violating peers
          3. If any remain: deterministic index from tick among healthy peers
          4. If none: probe mode — use least-bad peer (SLO violators allowed)
          5. If no peers at all: return None
        """
        with self._lock:
            self._route_count += 1

            healthy = [
                p for p, s in self._state.items()
                if s.in_rotation and not s.violating_slo
            ]
            skipped = [
                p for p, s in self._state.items()
                if s.violating_slo
            ]
            self._skipped_count += len(skipped)

            if healthy:
                # FIX-4: Deterministic peer selection — same tick → same peer
                # Sort for deterministic order, then pick by tick index
                healthy_sorted = sorted(healthy)
                idx = tick % len(healthy_sorted)
                chosen = healthy_sorted[idx]
                return RouteMetrics(
                    chosen_peer=chosen,
                    all_peers=list(self._state.keys()),
                    weights={},
                    skipped=skipped,
                    reason="deterministic_tick_index",
                )
            elif self._state:
                # Probe mode: least-bad peer (lowest combined penalty)
                all_states = list(self._state.values())
                best = min(
                    all_states,
                    key=lambda s: (
                        s.latency_ema / max(self._latency_slo, 1)
                        + s.loss_rate_ema / max(self._loss_slo, 0.001)
                    ),
                )
                return RouteMetrics(
                    chosen_peer=best.node_id,
                    all_peers=list(self._state.keys()),
                    weights={},
                    skipped=skipped,
                    reason="probe_mode_all_degraded",
                )
            else:
                return RouteMetrics(
                    chosen_peer=None,
                    all_peers=[],
                    weights={},
                    skipped=[],
                    reason="no_peers",
                )

    def get_best_peer(self) -> str | None:
        """Return the single best peer (no randomness)."""
        return self.route().chosen_peer

    # ── SLO status ────────────────────────────────────────────────────────

    def get_slo_status(self) -> dict:
        """Return per-peer SLO status summary."""
        with self._lock:
            return {
                peer: state.to_dict()
                for peer, state in self._state.items()
            }

    def get_violating_peers(self) -> list[str]:
        with self._lock:
            return [p for p, s in self._state.items() if s.violating_slo]

    def is_quorate(self) -> bool:
        """Cluster can achieve quorum if at least 2F+1 healthy peers exist."""
        with self._lock:
            healthy = sum(
                1 for s in self._state.values()
                if s.in_rotation and not s.violating_slo
            )
            # F2 quorum: need majority of cluster
            total = len(self._state) + 1  # +1 for self
            return healthy >= (total // 2 + 1)

    # ── Metrics ───────────────────────────────────────────────────────────

    def route_count(self) -> int:
        return self._route_count

    def skipped_count(self) -> int:
        return self._skipped_count

    def dump(self) -> dict:
        with self._lock:
            return {
                "node_id": self.node_id,
                "route_count": self._route_count,
                "skipped_count": self._skipped_count,
                "peers": {p: s.to_dict() for p, s in self._state.items()},
                "slo": {
                    "latency_slo_ms": self._latency_slo,
                    "loss_slo": self._loss_slo,
                    "skew_slo_ms": self._skew_slo,
                },
            }
