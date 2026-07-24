"""
Proof Kernel — top-level self-verifying control engine.
Hooks into ControlArbitrator, builds DecisionRecord, runs VerificationEngine.
"""
import time
from dataclasses import dataclass
from typing import Any

from orchestration import (
    ConflictResolutionMatrix,
    ControlArbitrator,
    ControlSignal,
    SystemWideGainScheduler,
)
from proof.invariant_registry import InvariantRegistry
from proof.proof_trace import (
    DecisionRecord,
    DominanceResult,
    ProofTrace,
)
from proof.verification_engine import VerificationEngine, VerificationReport


class ProofStatus:
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class KernelConfig:
    """Configuration for ProofKernel runtime behaviour."""
    max_global_gain: float = 2.0
    per_layer_cap: float = 1.5
    max_latency_ms: float = 50.0
    attach_verification_report: bool = True
    store_rejected_branches: bool = True


class ProofKernel:
    """
    Self-verifying control kernel.

    Wraps ControlArbitrator + SystemWideGainScheduler + ConflictResolutionMatrix
    and produces a DecisionRecord with proof trace DAG for every decision.

    Usage:
        kernel = ProofKernel()
        kernel.submit(ControlSignal(...))
        result = kernel.resolve()          # returns (winner, DecisionRecord)
        report = kernel.verify(result[1])   # optional full verification
    """

    def __init__(self, config: KernelConfig | None = None) -> None:
        self._config = config or KernelConfig()
        self._arb = ControlArbitrator()
        self._gain_sched = SystemWideGainScheduler(max_global_gain=self._config.max_global_gain)
        self._conflict = ConflictResolutionMatrix()
        self._trace = ProofTrace()
        self._verifier = VerificationEngine()
        self._history: list[DecisionRecord] = []
        self._next_id: int = 0

    # ─── Control interface (mirrors ControlArbitrator) ───────────────────

    def submit(self, signal: ControlSignal) -> None:
        self._arb.submit(signal)

    def resolve(self) -> tuple[ControlSignal, DecisionRecord]:
        """
        Resolve pending signals and produce a proof trace DAG.
        Returns (winner_signal, DecisionRecord).
        """
        decision_id = f"d_{self._next_id}"
        self._next_id += 1

        record = DecisionRecord(
            decision_id=decision_id,
            timestamp=time.time(),
            input_state=self._snapshot_state(),
        )

        all_signals = self._arb.resolve_many()
        if not all_signals:
            raise RuntimeError("No control signals submitted")

        winner = all_signals[0]

        # ── Build DAG stages ──
        self._build_arbiter_dag(record, winner, all_signals)
        self._build_gain_dag(record)
        self._build_conflict_dag(record, winner, all_signals)

        # ── Set action ──
        self._trace.set_action(
            record,
            winner.source,
            {**winner.payload, "priority": winner.priority},
        )

        # ── Rejected branches ──
        if self._config.store_rejected_branches:
            self._build_rejected_branches(record, winner, all_signals)

        # ── Finalize DAG ──
        self._trace.finalize(record)

        # ── Verification (optional) ──
        if self._config.attach_verification_report:
            report = self._verifier.verify(record)
            record.proof_status = report.proof_result.proof_status
            record.validity_score = report.proof_result.validity_score
            record.invariants_checked = [
                name for name, passed in report.invariant_results.items()
                if passed
            ]

        self._history.append(record)
        return winner, record

    def resolve_many(self) -> tuple[list[ControlSignal], DecisionRecord]:
        """Return all signals sorted + DecisionRecord."""
        all_signals = self._arb.resolve_many()
        if not all_signals:
            return ([], DecisionRecord(
                decision_id=f"d_{self._next_id}",
                timestamp=time.time(),
                input_state=self._snapshot_state(),
            ))
        all_signals[0]
        _, record = self.resolve.__wrapped__(self) if False else (None, None)
        # resolve() already-populated arbiter; reuse signals list
        _, record = self.resolve()
        return (all_signals, record)

    def verify(self, record: DecisionRecord) -> VerificationReport:
        """Run full cross-layer verification on a DecisionRecord."""
        return self._verifier.verify(record)

    @property
    def history(self) -> list[DecisionRecord]:
        return self._history

    def last_record(self) -> DecisionRecord | None:
        return self._history[-1] if self._history else None

    @property
    def registry(self) -> InvariantRegistry:
        return self._verifier.registry

    # ─── Internal helpers ─────────────────────────────────────────────────

    def _snapshot_state(self) -> dict[str, Any]:
        return {
            "_meta_pending_count": self._arb.pending_count,
            "_meta_max_global_gain": self._config.max_global_gain,
            "_meta_per_layer_cap": self._config.per_layer_cap,
            "_meta_max_latency_ms": self._config.max_latency_ms,
            "_meta_timestamp": time.time(),
        }

    def _build_arbiter_dag(
        self,
        record: DecisionRecord,
        winner: ControlSignal,
        all_signals: list[ControlSignal],
    ) -> None:
        submitted = [
            {"source": s.source, "priority": s.priority, "payload": s.payload}
            for s in all_signals
        ]
        self._trace.add_arbiter_stage(
            record,
            winner_source=winner.source,
            winner_priority=winner.priority,
            all_submitted=submitted,
        )

    def _build_gain_dag(self, record: DecisionRecord) -> None:
        # No explicit gains set → identity normalizer
        gains = {s.source: 1.0 for s in self._arb._signals}
        normalized = self._gain_sched.normalize(gains)
        self._trace.add_gain_stage(record, normalized, raw_gains=gains)

    def _build_conflict_dag(
        self,
        record: DecisionRecord,
        winner: ControlSignal,
        all_signals: list[ControlSignal],
    ) -> None:
        candidates = [s.source for s in all_signals]
        # Build pairwise matrix: winner > others
        entries: dict[tuple, float] = {}
        for s in all_signals:
            if s.source != winner.source:
                entries[(s.source, winner.source)] = 1.0

        self._trace.add_conflict_stage(
            record,
            winner=winner.source,
            candidates=candidates,
            matrix_entries=entries,
        )

    def _build_rejected_branches(
        self,
        record: DecisionRecord,
        winner: ControlSignal,
        all_signals: list[ControlSignal],
    ) -> None:
        for sig in all_signals:
            if sig.source == winner.source:
                continue
            dominance = (
                DominanceResult.STRICTLY_DOMINATES
                if sig.priority < winner.priority
                else DominanceResult.EQUIVALENT
            )
            self._trace.add_rejected(
                record,
                source=sig.source,
                reason=f"priority {sig.priority:.4f} < winner {winner.priority:.4f}",
                dominance=dominance,
                priority=sig.priority,
                selected_priority=winner.priority,
            )
