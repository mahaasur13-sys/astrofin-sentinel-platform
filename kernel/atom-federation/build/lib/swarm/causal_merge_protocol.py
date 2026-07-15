# ATOMFEDERATION-OS - CausalMergeProtocol
# Swarm layer — deterministic merge with ExecutionGateway enforcement
# =========================================================

import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime

from orchestration.execution_gateway import ExecutionGateway


@dataclass
class TickSnapshot:
    tick: int
    agent_id: str
    state_hash: str
    state: bytes
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MergeResult:
    success: bool
    merged_tick: int
    conflicting_agents: list[str] = field(default_factory=list)
    resolved_state: bytes | None = None
    error: str | None = None


@dataclass
class ConsensusSignal:
    tick: int
    action: str  # 'proceed', 'stall', 'rollback'
    reason: str


class CausalMergeProtocol:
    # =========================================================
    # CAUSAL MERGE PROTOCOL — Deterministic Swarm Merge
    # All state mutations go through ExecutionGateway
    # =========================================================

    def __init__(self, gateway: ExecutionGateway):
        self._gateway = gateway
        self._snapshots: dict[int, dict[str, TickSnapshot]] = {}
        self._merge_history: list[MergeResult] = []
        self._lock = threading.RLock()

        # Deterministic merge config
        self._tick_stability_threshold = 3  # ticks before commit
        self._max_divergence = 0.15  # 15% max divergence before stall

    @ExecutionGateway.requires_gateway
    def propose_merge(
        self,
        tick: int,
        agent_id: str,
        state: bytes
    ) -> MergeResult:
        with self._lock:
            state_hash = hashlib.sha256(state).hexdigest()

            snapshot = TickSnapshot(
                tick=tick,
                agent_id=agent_id,
                state_hash=state_hash,
                state=state
            )

            if tick not in self._snapshots:
                self._snapshots[tick] = {}

            self._snapshots[tick][agent_id] = snapshot

            return self._execute_merge(tick)

    @ExecutionGateway.requires_gateway
    def execute_merge(self, tick: int) -> MergeResult:
        with self._lock:
            return self._execute_merge(tick)

    def _execute_merge(self, tick: int) -> MergeResult:
        if tick not in self._snapshots:
            return MergeResult(
                success=False,
                merged_tick=tick,
                error=f'No snapshots for tick {tick}'
            )

        agents = self._snapshots[tick]
        if len(agents) == 1:
            return MergeResult(
                success=True,
                merged_tick=tick,
                resolved_state=next(iter(agents.values())).state
            )

        # Detect divergence
        hashes = [s.state_hash for s in agents.values()]
        unique_hashes = set(hashes)

        if len(unique_hashes) > 1:
            divergence = 1 - (len(unique_hashes) / len(hashes))
            if divergence > self._max_divergence:
                return MergeResult(
                    success=False,
                    merged_tick=tick,
                    conflicting_agents=list(agents.keys()),
                    error=f'Divergence {divergence:.2%} exceeds threshold {self._max_divergence:.2%}'
                )

        # Deterministic merge: pick by lowest agent_id (stable ordering)
        sorted_agents = sorted(agents.keys())
        winner = sorted_agents[0]
        merged_state = agents[winner].state

        result = MergeResult(
            success=True,
            merged_tick=tick,
            resolved_state=merged_state
        )
        self._merge_history.append(result)
        return result

    @ExecutionGateway.requires_gateway
    def resolve_divergence(self, tick: int) -> MergeResult:
        with self._lock:
            if tick not in self._snapshots:
                return MergeResult(
                    success=False,
                    merged_tick=tick,
                    error=f'No snapshots for tick {tick}'
                )

            agents = self._snapshots[tick]

            # Deterministic resolution: median tick convergence
            best_snapshot = None
            for agent_id, snapshot in agents.items():
                convergence_score = self._calculate_convergence(tick, agent_id)
                if best_snapshot is None or convergence_score > best_snapshot[1]:
                    best_snapshot = (snapshot, convergence_score)

            result = MergeResult(
                success=True,
                merged_tick=tick,
                resolved_state=best_snapshot[0].state
            )
            self._merge_history.append(result)
            return result

    def _calculate_convergence(self, tick: int, agent_id: str) -> float:
        # Deterministic: based on tick and agent_id, no randomness
        if tick < self._tick_stability_threshold:
            return 0.0

        agent_num = int(hashlib.md5(agent_id.encode()).hexdigest()[:8], 16)
        return (tick - self._tick_stability_threshold) / (agent_num % 100 + 1)

    def get_pending_ticks(self) -> list[int]:
        with self._lock:
            return sorted(self._snapshots.keys())

    def get_merge_history(self) -> list[MergeResult]:
        return list(self._merge_history)
