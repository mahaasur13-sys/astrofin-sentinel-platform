"""
skew_detector.py — v9.6 Trust Skew + Collapse Detector

Monitors weight distribution for dominance, skew, and trust collapse.

Integration:
  NodeWeightsSnapshot → TrustSkewDetector
  Provides alerts for CONSENSUS_SHIFT detection
"""

from __future__ import annotations

from dataclasses import dataclass
from .node_weights import NodeWeightsSnapshot


@dataclass
class TrustSkewReport:
    snapshot_epoch: int
    total_weight: float
    dom_fraction: float
    skew_ratio: float
    dominated: bool


@dataclass
class TrustCollapseAlert:
    snapshot_epoch: int
    node_id: str
    prev_weight: float
    curr_weight: float
    message: str


@dataclass
class ConsensusDominationAlert:
    snapshot_epoch: int
    node_id: str
    weight_fraction: float
    threshold: float
    message: str


class TrustSkewDetector:
    def __init__(self, dom_threshold: float = 0.5, collapse_threshold: float = 0.05):
        self.dom_threshold = dom_threshold
        self.collapse_threshold = collapse_threshold
        self._last_snapshot_weights: dict[str, float] = {}

    def analyze(self, epoch: int, snapshot: NodeWeightsSnapshot) -> TrustSkewReport:
        total_weight = snapshot.total_weight
        max_weight = snapshot.max_single_weight
        skew_ratio = max_weight / (total_weight + 1e-9)
        dominated = skew_ratio >= self.dom_threshold
        return TrustSkewReport(
            snapshot_epoch=epoch,
            total_weight=total_weight,
            dom_fraction=skew_ratio,
            skew_ratio=skew_ratio,
            dominated=dominated,
        )

    def detect_collapse(self, snapshot: NodeWeightsSnapshot) -> TrustCollapseAlert | None:
        for node_id, curr_weight in snapshot.weights.items():
            prev_weight = self._last_snapshot_weights.get(node_id, 0.0)
            if prev_weight > self.dom_threshold and curr_weight < self.collapse_threshold:
                return TrustCollapseAlert(
                    snapshot_epoch=snapshot.epoch,
                    node_id=node_id,
                    prev_weight=prev_weight,
                    curr_weight=curr_weight,
                    message=(
                        f"Trust collapse: {node_id} dropped from {prev_weight:.3f} to {curr_weight:.3f}"
                    ),
                )
        return None

    def detect_domination(self, snapshot: NodeWeightsSnapshot) -> ConsensusDominationAlert | None:
        for node_id, curr_weight in snapshot.weights.items():
            if curr_weight / (snapshot.total_weight + 1e-9) >= self.dom_threshold:
                return ConsensusDominationAlert(
                    snapshot_epoch=snapshot.epoch,
                    node_id=node_id,
                    weight_fraction=curr_weight / (snapshot.total_weight + 1e-9),
                    threshold=self.dom_threshold,
                    message=(
                        f"Dominating node: {node_id} controls {curr_weight:.3f} weight ({self.dom_threshold*100:.0f}% threshold)"
                    ),
                )
        return None

    def update_snapshot(self, snapshot: NodeWeightsSnapshot) -> None:
        self._last_snapshot_weights = dict(snapshot.weights)

__all__ = [
    "ConsensusDominationAlert",
    "TrustCollapseAlert",
    "TrustSkewDetector",
    "TrustSkewReport",
]
