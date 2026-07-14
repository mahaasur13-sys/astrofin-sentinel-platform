"""gcst.py — v11.2 Global Consensus Stability Theorem.

GCST: If GAST converges to an attractor and BCIL detects no Byzantine fault,
      then GSCT is CONVERGENT (terminal regime = STABLE attractor).
      |A| = 1 ∧ ∀ i : ByzantineDetector(node_i) = NOMINAL
        ⇒ ∃! attractor_class ∈ {STABLE_CENTRALISED, STABLE_DISTRIBUTED}
"""
from dataclasses import dataclass
from enum import Enum, auto

from alignment.bcil import BCIL
from alignment.gast import GAST, AttractorState, AttractorType


class Regime(Enum):
    STABLE_CENTRALISED = auto()
    STABLE_DISTRIBUTED = auto()
    DEGRADED = auto()
    UNSTABLE = auto()
    UNKNOWN = auto()


@dataclass
class ConsensusState:
    gast_state: AttractorState
    byzantine_count: int
    byzantine_nodes: list[str]
    regime: Regime = Regime.UNKNOWN
    uniqueness_theorem: bool = False
    byzantine_theorem: bool = False
    convergent: bool = False


class GSCT:
    def __init__(self):
        self.gast = GAST()
        self.bcil = BCIL()

    def evaluate(
        self,
        gast_state: AttractorState,
        byzantine_count: int,
        byzantine_nodes: list[str],
    ) -> ConsensusState:
        result = ConsensusState(
            gast_state=gast_state,
            byzantine_count=byzantine_count,
            byzantine_nodes=byzantine_nodes,
        )
        result.uniqueness_theorem = gast_state.attractor_type == AttractorType.STABLE_CENTRALISED or gast_state.attractor_type == AttractorType.STABLE_DISTRIBUTED
        result.byzantine_theorem = byzantine_count == 0
        if result.uniqueness_theorem and result.byzantine_theorem:
            result.regime = gast_state.attractor_type.name.replace("STABLE_", "STABLE_")
            result.regime = Regime.STABLE_CENTRALISED if gast_state.attractor_type == AttractorType.STABLE_CENTRALISED else Regime.STABLE_DISTRIBUTED
            result.convergent = True
        elif result.byzantine_theorem and not result.uniqueness_theorem:
            result.regime = Regime.UNSTABLE
            result.convergent = False
        elif not result.byzantine_theorem and result.uniqueness_theorem:
            result.regime = Regime.DEGRADED
            result.convergent = False
        else:
            result.regime = Regime.UNKNOWN
            result.convergent = False
        return result

    def summary(self, r: ConsensusState) -> str:
        return f"Regime={r.regime.name} unique={r.uniqueness_theorem} byz={r.byzantine_theorem} conv={r.convergent}"
