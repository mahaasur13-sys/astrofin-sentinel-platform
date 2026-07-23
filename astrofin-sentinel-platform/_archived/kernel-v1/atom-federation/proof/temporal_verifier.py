"""
TemporalVerifier — global verification over a time window.
Wraps StabilityProver + ProofDriftDetector + CausalProofGraph.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from proof.causal_proof_graph import CausalProofGraph
from proof.proof_chain import ProofChain
from proof.proof_drift_detector import DriftEvent, DriftReport, ProofDriftDetector
from proof.stability_prover import StabilityMetrics, StabilityProver


@dataclass
class TemporalVerificationReport:
    """Complete temporal verification result."""
    chain_length: int
    window: tuple[int, int]
    stability: StabilityMetrics
    drift_report: DriftReport
    causal_graph_stats: dict = field(default_factory=dict)
    overall_passed: bool = False
    recommendations: list[str] = field(default_factory=list)
    proof_chain: ProofChain | None = None
    verified_sources: list[str] = field(default_factory=list)

    # Convenience aliases for cleaner access
    @property
    def is_stable(self) -> bool:
        return self.stability.is_stable

    @property
    def overall_stability(self) -> float:
        return self.stability.overall_stability

    @property
    def causal_coherence(self) -> float:
        return self.stability.causal_coherence

    @property
    def drift_events(self) -> list[DriftEvent]:
        return self.drift_report.events

    def to_dict(self) -> dict:
        return {
            "chain_length": self.chain_length,
            "window": self.window,
            "stability": self.stability.to_dict(),
            "drift": self.drift_report.to_dict(),
            "causal_graph_stats": self.causal_graph_stats,
            "overall_passed": self.overall_passed,
            "recommendations": self.recommendations,
        }


class TemporalVerifier:
    """
    Global verification over time windows.
    Combines stability analysis + drift detection + causal coherence.
    """

    def __init__(self,
                 stability_threshold: float = 0.75,
                 drift_threshold: float = 0.6):
        self.stability_prover = StabilityProver(stability_threshold=stability_threshold)
        self.drift_detector = ProofDriftDetector(severity_threshold=drift_threshold)
        self._graph: CausalProofGraph | None = None

    def build_graph(self, chain: ProofChain) -> CausalProofGraph:
        """Build or rebuild causal graph from chain."""
        graph = CausalProofGraph()
        graph.build_from_chain(chain)
        self._graph = graph
        return graph

    def verify(self, chain: ProofChain,
               window: tuple[int, int] | None = None) -> TemporalVerificationReport:
        """
        Full temporal verification of a ProofChain.
        """
        if chain.length == 0:
            return TemporalVerificationReport(
                chain_length=0,
                window=(0, 0),
                stability=StabilityMetrics(
                    tick_range=(0, 0),
                    action_stability=0.0,
                    reasoning_stability=0.0,
                    causal_coherence=0.0,
                    proof_continuity=0.0,
                    overall_stability=0.0,
                    is_stable=False,
                ),
                drift_report=DriftReport(
                    tick_range=(0, 0),
                    events=[],
                    drift_score=0.0,
                    is_drifted=False,
                ),
                overall_passed=False,
                recommendations=["Chain is empty — no verification possible"],
            )

        start_tick = window[0] if window else chain.genesis_tick
        end_tick = window[1] if window else chain.latest_tick

        # Build graph if not already built
        if self._graph is None:
            self.build_graph(chain)

        # Compute stability
        stability = self.stability_prover.compute(chain, self._graph, window)

        # Detect drift
        drift_report = self.drift_detector.detect(chain, window)

        # Causal graph stats
        graph_stats = {
            "vertices": self._graph.vertex_count,
            "edges": self._graph.edge_count,
            "avg_propagation_strength": self._compute_avg_propagation(),
        }

        # Overall pass/fail
        overall_passed = (
            stability.is_stable
            and not drift_report.is_drifted
            and stability.overall_stability >= self.stability_prover.stability_threshold
        )

        # Recommendations
        recs = []
        if not stability.is_stable:
            recs.append(f"Reasoning stability below threshold ({stability.overall_stability:.2f} < {self.stability_prover.stability_threshold})")
        if drift_report.is_drifted:
            recs.append(f"Drift detected ({len(drift_report.events)} events, score={drift_report.drift_score:.2f})")
        if stability.action_stability < 0.5:
            recs.append("Action source switches frequently — review arbitration policy")
        if stability.causal_coherence < 0.5:
            recs.append("Causal coherence weak — verify causal graph integrity")

        return TemporalVerificationReport(
            chain_length=chain.length,
            window=(start_tick, end_tick),
            stability=stability,
            drift_report=drift_report,
            causal_graph_stats=graph_stats,
            overall_passed=overall_passed,
            recommendations=recs,
        )

    def _compute_avg_propagation(self) -> float:
        if self._graph is None or self._graph.edge_count == 0:
            return 0.0
        return sum(e.weight for e in self._graph.edges) / len(self._graph.edges)

    def verify_batch(self, chains: list[ProofChain],
                    window: tuple[int, int] | None = None) -> list[TemporalVerificationReport]:
        """Verify multiple chains."""
        return [self.verify(c, window) for c in chains]
