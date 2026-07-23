"""
StabilityProver — measures stability of reasoning across ticks.
Not just action stable, but the reasoning process itself is stable.
"""
from __future__ import annotations

from dataclasses import dataclass

from proof.causal_proof_graph import CausalProofGraph
from proof.proof_chain import ChainLink, ProofChain


@dataclass
class StabilityMetrics:
    """Metrics for reasoning stability over a time window."""
    tick_range: tuple[int, int]
    action_stability: float      # 0..1 how consistent actions are
    reasoning_stability: float    # 0..1 how consistent the reasoning process is
    causal_coherence: float      # 0..1 causal links strong and consistent
    proof_continuity: float       # 0..1 proof chain is continuous
    overall_stability: float     # weighted composite
    is_stable: bool              # threshold-based boolean

    def to_dict(self) -> dict:
        return {
            "tick_range": self.tick_range,
            "action_stability": round(self.action_stability, 4),
            "reasoning_stability": round(self.reasoning_stability, 4),
            "causal_coherence": round(self.causal_coherence, 4),
            "proof_continuity": round(self.proof_continuity, 4),
            "overall_stability": round(self.overall_stability, 4),
            "is_stable": self.is_stable,
        }


class StabilityProver:
    """
    Determines if the reasoning chain is stable over time.
    Uses ProofChain + CausalProofGraph.
    """

    def __init__(self, stability_threshold: float = 0.75):
        self.stability_threshold = stability_threshold

    def compute(self, chain: ProofChain,
                graph: CausalProofGraph | None = None,
                window: tuple[int, int] | None = None) -> StabilityMetrics:
        """
        Compute stability metrics over a chain (optionally within a window).
        """
        if chain.length == 0:
            return StabilityMetrics(
                tick_range=(0, 0),
                action_stability=0.0,
                reasoning_stability=0.0,
                causal_coherence=0.0,
                proof_continuity=0.0,
                overall_stability=0.0,
                is_stable=False,
            )

        start_tick = window[0] if window else chain.genesis_tick
        end_tick = window[1] if window else chain.latest_tick
        links = chain.window(start_tick, end_tick)

        if len(links) < 2:
            # Only one tick — check against chain_validity
            return StabilityMetrics(
                tick_range=(start_tick, end_tick),
                action_stability=1.0,
                reasoning_stability=1.0,
                causal_coherence=1.0,
                proof_continuity=chain.chain_validity(),
                overall_stability=chain.chain_validity(),
                is_stable=chain.chain_validity() >= self.stability_threshold,
            )

        # Action stability: variance in winner sources
        action_stability = self._action_stability(links)

        # Reasoning stability: continuity scores across links
        reasoning_stability = self._reasoning_stability(links)

        # Causal coherence: graph-based
        causal_coherence = self._causal_coherence(chain, graph, start_tick, end_tick)

        # Proof continuity: chain-level metric
        proof_continuity = self._proof_continuity(links)

        # Weighted composite
        overall = (
            action_stability * 0.2 +
            reasoning_stability * 0.3 +
            causal_coherence * 0.25 +
            proof_continuity * 0.25
        )

        return StabilityMetrics(
            tick_range=(start_tick, end_tick),
            action_stability=action_stability,
            reasoning_stability=reasoning_stability,
            causal_coherence=causal_coherence,
            proof_continuity=proof_continuity,
            overall_stability=overall,
            is_stable=overall >= self.stability_threshold,
        )

    def _action_stability(self, links: list[ChainLink]) -> float:
        """How consistent the winner sources are."""
        sources = []
        for link in links:
            action = link.record.selected_action
            if action:
                src = action.label.split(":")[1] if ":" in action.label else "unknown"
                sources.append(src)

        if len(sources) < 2:
            return 1.0

        # Count transitions
        transitions = sum(1 for i in range(1, len(sources)) if sources[i] != sources[i - 1])
        max_transitions = len(sources) - 1
        return 1.0 - (transitions / max_transitions)

    def _reasoning_stability(self, links: list[ChainLink]) -> float:
        """How consistent the reasoning quality is (continuity scores)."""
        if not links:
            return 0.0
        avg_continuity = sum(l.continuity_score for l in links) / len(links)

        # Bonus if causal_depth grows steadily (not chaotic)
        depth_gaps = []
        for i in range(1, len(links)):
            gap = links[i].causal_depth - links[i - 1].causal_depth
            depth_gaps.append(gap)

        if depth_gaps:
            # Stable = depth grows by 1 each tick (steady reasoning chain)
            stable_count = sum(1 for g in depth_gaps if g == 1)
            depth_stability = stable_count / len(depth_gaps)
            # Blend continuity + depth stability
            return avg_continuity * 0.7 + depth_stability * 0.3
        return avg_continuity

    def _causal_coherence(self, chain, graph, start_tick, end_tick) -> float:
        """Check that causal graph is coherent across window."""
        if graph is None or graph.vertex_count < 2:
            # No graph — use chain continuity as proxy
            links = chain.window(start_tick, end_tick)
            return sum(l.continuity_score for l in links) / len(links) if links else 0.0

        # Check propagation strength between adjacent ticks
        weights = []
        for t in range(start_tick, end_tick):
            # Find edges from t to t+1
            out = graph.out_edges(t)
            for edge in out:
                if edge.to_tick == t + 1:
                    weights.append(edge.weight)
                    break

        if not weights:
            return 0.5  # neutral if no edges found
        return sum(weights) / len(weights)

    def _proof_continuity(self, links: list[ChainLink]) -> float:
        """Proof chain continuity (no gaps)."""
        if len(links) < 2:
            return 1.0

        # Check that tick numbers are consecutive
        ticks = [l.tick for l in links]
        expected_consecutive = all(
            ticks[i + 1] == ticks[i] + 1 for i in range(len(ticks) - 1)
        )
        return 1.0 if expected_consecutive else 0.3
