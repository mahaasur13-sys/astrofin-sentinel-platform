"""
CausalProofGraph — inter-tick dependency graph.
Tracks how proof(t) influences proof(t+1) through causal links.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class CausalLinkType(Enum):
    """Type of causal influence between ticks."""
    PRIORITY_PROPAGATION = auto()   # winner priority → next decision
    GAIN_CARRY = auto()            # gain value propagates forward
    INVARIANT_STABILITY = auto()   # invariant status carries over
    REASONING_SWITCH = auto()      # source switched (low continuity)


@dataclass
class CausalLink:
    """Directed edge in the causal graph: from_tick → to_tick."""
    from_tick: int
    to_tick: int
    link_type: CausalLinkType
    weight: float = 1.0  # strength of causal influence
    metadata: dict = field(default_factory=dict)


@dataclass
class CausalProofGraph:
    """
    Graph of causal dependencies between proof ticks.
    Vertices = ticks, Edges = causal influence.
    """
    vertices: list[int] = field(default_factory=list)  # tick indices
    edges: list[CausalLink] = field(default_factory=list)
    _out_edges: dict[int, list[CausalLink]] = field(default_factory=dict)
    _in_edges: dict[int, list[CausalLink]] = field(default_factory=dict)

    def add_vertex(self, tick: int) -> None:
        if tick not in self.vertices:
            self.vertices.append(tick)
            self.vertices.sort()

    def add_edge(self, from_tick: int, to_tick: int,
                 link_type: CausalLinkType, weight: float = 1.0,
                 metadata: dict | None = None) -> None:
        self.add_vertex(from_tick)
        self.add_vertex(to_tick)

        edge = CausalLink(
            from_tick=from_tick,
            to_tick=to_tick,
            link_type=link_type,
            weight=weight,
            metadata=metadata or {},
        )
        self.edges.append(edge)

        if from_tick not in self._out_edges:
            self._out_edges[from_tick] = []
        self._out_edges[from_tick].append(edge)

        if to_tick not in self._in_edges:
            self._in_edges[to_tick] = []
        self._in_edges[to_tick].append(edge)

    def out_edges(self, tick: int) -> list[CausalLink]:
        return self._out_edges.get(tick, [])

    def in_edges(self, tick: int) -> list[CausalLink]:
        return self._in_edges.get(tick, [])

    def predecessors(self, tick: int) -> list[int]:
        return [e.from_tick for e in self.in_edges(tick)]

    def successors(self, tick: int) -> list[int]:
        return [e.to_tick for e in self.out_edges(tick)]

    def causal_path(self, from_tick: int, to_tick: int) -> list[int]:
        """Find causal path from from_tick to to_tick (BFS)."""
        if from_tick == to_tick:
            return [from_tick]

        visited = {from_tick}
        queue = [(from_tick, [from_tick])]

        while queue:
            current, path = queue.pop(0)
            for edge in self.out_edges(current):
                next_tick = edge.to_tick
                if next_tick == to_tick:
                    return path + [next_tick]
                if next_tick not in visited:
                    visited.add(next_tick)
                    queue.append((next_tick, path + [next_tick]))
        return []

    def propagation_strength(self, from_tick: int, to_tick: int) -> float:
        """Compute aggregate causal strength from from_tick to to_tick."""
        path = self.causal_path(from_tick, to_tick)
        if not path or len(path) < 2:
            return 0.0

        total_weight = 1.0
        for i in range(len(path) - 1):
            for edge in self.out_edges(path[i]):
                if edge.to_tick == path[i + 1]:
                    total_weight *= edge.weight
                    break
        return total_weight

    def build_from_chain(self, chain) -> None:
        """
        Build causal graph from a ProofChain.
        Infers causal links based on tick adjacency and metadata.
        """
        from proof.proof_chain import ProofChain
        if not isinstance(chain, ProofChain) or chain.length < 2:
            return

        for i in range(chain.length - 1):
            curr_link = chain.links[i]
            next_link = chain.links[i + 1]

            # PRIORITY_PROPAGATION: winner source carries forward
            if (curr_link.record.selected_action is not None and
                    next_link.record.selected_action is not None):
                curr_src = curr_link.record.selected_action.label.split(":")[1]
                next_src = next_link.record.selected_action.label.split(":")[1]

                if curr_src == next_src:
                    # Same winner → strong priority propagation
                    self.add_edge(
                        curr_link.tick, next_link.tick,
                        CausalLinkType.PRIORITY_PROPAGATION,
                        weight=0.95,
                        metadata={"source": curr_src, "continuity": "same"}
                    )
                else:
                    # Reasoning switch
                    self.add_edge(
                        curr_link.tick, next_link.tick,
                        CausalLinkType.REASONING_SWITCH,
                        weight=0.4,
                        metadata={"from": curr_src, "to": next_src}
                    )

            # GAIN_CARRY: gain node propagates normalization
            if curr_link.record.gain_node and next_link.record.gain_node:
                self.add_edge(
                    curr_link.tick, next_link.tick,
                    CausalLinkType.GAIN_CARRY,
                    weight=0.8,
                    metadata={"gain_normalization": "propagates"}
                )

            # INVARIANT_STABILITY: proof status carries over
            if curr_link.record.proof_status == next_link.record.proof_status == "PASS":
                self.add_edge(
                    curr_link.tick, next_link.tick,
                    CausalLinkType.INVARIANT_STABILITY,
                    weight=0.9,
                    metadata={"proof_status": "PASS"}
                )

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def edge_count(self) -> int:
        return len(self.edges)
