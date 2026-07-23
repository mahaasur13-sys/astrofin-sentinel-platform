"""
ProofChain — links DecisionRecords across time ticks.
Maintains a verifiable chain of proofs where proof(t) → proof(t+1).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from proof.proof_trace import DecisionRecord


@dataclass
class ChainLink:
    """Single tick in the proof chain."""
    tick: int
    record: DecisionRecord
    parent_tick: int | None = None  # None for genesis tick
    causal_depth: int = 0  # distance from genesis
    continuity_score: float = 1.0  # how continuous this link is


@dataclass
class ProofChain:
    """
    Immutable chain of DecisionRecords across time.
    proof(t) → proof(t+1) with causal traceability.
    """
    links: list[ChainLink] = field(default_factory=list)
    genesis_tick: int = 0

    def append(self, record: DecisionRecord) -> ChainLink:
        """Append a new DecisionRecord to the chain."""
        tick = len(self.links) + self.genesis_tick
        parent_tick = None if tick == self.genesis_tick else tick - 1
        causal_depth = 0 if parent_tick is None else self.links[-1].causal_depth + 1

        # Compute continuity: check if reasoning pattern matches parent
        continuity_score = 1.0
        if parent_tick is not None:
            prev = self.links[-1]
            # Same winner source → higher continuity
            if (prev.record.selected_action is not None and
                    record.selected_action is not None):
                prev_src = prev.record.selected_action.label.split(":")[1]
                curr_src = record.selected_action.label.split(":")[1]
                if prev_src == curr_src:
                    continuity_score = 0.95
                else:
                    continuity_score = 0.6  # source switch → lower continuity

        link = ChainLink(
            tick=tick,
            record=record,
            parent_tick=parent_tick,
            causal_depth=causal_depth,
            continuity_score=continuity_score,
        )
        self.links.append(link)
        return link

    def get_link(self, tick: int) -> ChainLink | None:
        idx = tick - self.genesis_tick
        if 0 <= idx < len(self.links):
            return self.links[idx]
        return None

    def window(self, start_tick: int, end_tick: int) -> list[ChainLink]:
        """Get chain links in a time window."""
        return [l for l in self.links if start_tick <= l.tick <= end_tick]

    def all_ticks(self) -> list[int]:
        return [l.tick for l in self.links]

    @property
    def length(self) -> int:
        return len(self.links)

    @property
    def latest_tick(self) -> int | None:
        return self.links[-1].tick if self.links else None

    def causal_path(self, tick: int) -> list[int]:
        """Return list of ticks from genesis to given tick (causal lineage)."""
        path = []
        idx = tick - self.genesis_tick
        while idx >= 0:
            path.append(self.links[idx].tick)
            idx -= 1
        return list(reversed(path))

    def proof_at(self, tick: int) -> DecisionRecord | None:
        link = self.get_link(tick)
        return link.record if link else None

    def chain_validity(self) -> float:
        """Compute overall chain validity: average continuity across all links."""
        if not self.links:
            return 0.0
        return sum(l.continuity_score for l in self.links) / len(self.links)
