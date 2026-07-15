# ATOMFEDERATION-OS - ConsensusResolver
# Federation layer — deterministic consensus with ExecutionGateway
# =========================================================

import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime

from orchestration.execution_gateway import ExecutionGateway


@dataclass
class ConsensusVote:
    node_id: str
    tick: int
    vote: str  # 'approve', 'reject', 'abstain'
    weight: float
    signature: str | None = None


@dataclass
class ConsensusDecision:
    tick: int
    decision: str  # 'proceed', 'stall', 'rollback'
    votes_approve: int
    votes_reject: int
    votes_abstain: int
    quorum_reached: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConsensusResult:
    success: bool
    decision: ConsensusDecision | None = None
    error: str | None = None


class ConsensusResolver:
    # =========================================================
    # CONSENSUS RESOLVER — Deterministic Federation Consensus
    # All consensus operations go through ExecutionGateway
    # =========================================================

    def __init__(self, gateway: ExecutionGateway, quorum_threshold: float = 0.51):
        self._gateway = gateway
        self._quorum_threshold = quorum_threshold
        self._votes: dict[int, list[ConsensusVote]] = {}
        self._decisions: dict[int, ConsensusDecision] = {}
        self._lock = threading.RLock()
        self._node_weights: dict[str, float] = {}

    def register_node(self, node_id: str, weight: float = 1.0) -> None:
        with self._gateway.mutation_context(can_mutate=True):
            self._node_weights[node_id] = weight

    @ExecutionGateway.requires_gateway
    def submit_vote(
        self,
        node_id: str,
        tick: int,
        vote: str
    ) -> ConsensusResult:
        with self._lock:
            if not self._gateway.is_safe():
                return ConsensusResult(
                    success=False,
                    error='Gateway safety check failed'
                )

            if tick not in self._votes:
                self._votes[tick] = []

            weight = self._node_weights.get(node_id, 1.0)
            signature = self._compute_signature(node_id, tick, vote)

            consensus_vote = ConsensusVote(
                node_id=node_id,
                tick=tick,
                vote=vote,
                weight=weight,
                signature=signature
            )

            self._votes[tick].append(consensus_vote)

            return self._resolve_consensus(tick)

    def _compute_signature(self, node_id: str, tick: int, vote: str) -> str:
        data = f'{node_id}:{tick}:{vote}'.encode()
        return hashlib.sha256(data).hexdigest()

    def _resolve_consensus(self, tick: int) -> ConsensusResult:
        if tick not in self._votes:
            return ConsensusResult(success=False, error=f'No votes for tick {tick}')

        votes = self._votes[tick]
        approve_weight = sum(v.weight for v in votes if v.vote == 'approve')
        reject_weight = sum(v.weight for v in votes if v.vote == 'reject')
        total_weight = sum(v.weight for v in votes)
        abstain_weight = sum(v.weight for v in votes if v.vote == 'abstain')

        if total_weight == 0:
            return ConsensusResult(success=False, error='No voting weight')

        approve_ratio = approve_weight / total_weight
        reject_ratio = reject_weight / total_weight

        quorum_reached = (approve_ratio + reject_ratio) >= self._quorum_threshold

        if approve_ratio > reject_ratio and approve_ratio > 0.5:
            decision_str = 'proceed'
        elif reject_ratio > approve_ratio and reject_ratio > 0.5:
            decision_str = 'rollback'
        else:
            decision_str = 'stall'

        decision = ConsensusDecision(
            tick=tick,
            decision=decision_str,
            votes_approve=int(approve_weight),
            votes_reject=int(reject_weight),
            votes_abstain=int(abstain_weight),
            quorum_reached=quorum_reached
        )

        self._decisions[tick] = decision
        return ConsensusResult(success=True, decision=decision)

    @ExecutionGateway.requires_gateway
    def force_decision(self, tick: int, decision: str) -> ConsensusResult:
        with self._lock:
            if decision not in ('proceed', 'stall', 'rollback'):
                return ConsensusResult(
                    success=False,
                    error=f'Invalid decision: {decision}'
                )

            total_weight = sum(self._node_weights.values())
            approve = total_weight if decision == 'proceed' else 0
            reject = total_weight if decision == 'rollback' else 0

            consensus_decision = ConsensusDecision(
                tick=tick,
                decision=decision,
                votes_approve=approve,
                votes_reject=reject,
                votes_abstain=0,
                quorum_reached=True
            )

            self._decisions[tick] = consensus_decision
            return ConsensusResult(success=True, decision=consensus_decision)

    def get_decision(self, tick: int) -> ConsensusDecision | None:
        with self._lock:
            return self._decisions.get(tick)

    def get_votes(self, tick: int) -> list[ConsensusVote]:
        with self._lock:
            return list(self._votes.get(tick, []))
