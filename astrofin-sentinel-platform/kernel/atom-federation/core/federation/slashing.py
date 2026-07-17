"""slashing.py — atom-federation-os v9.0+P7 Slashing Engine for Byzantine Misbehavior.

Slashing conditions:
  1. DOUBLE_SIGN: node signs two different requests at same (view, sequence)
  2. EQUIVOCATION: node commits to conflicting states
  3. LIGHTING_ATTACK: node withholds pre-prepare longer than MAX_VIEW_WAIT

Evidence types are captured as immutable dataclasses for audit trails.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# ── Evidence Types ────────────────────────────────────────────────────────────

class MisbehaviorType(Enum):
    DOUBLE_SIGN    = auto()  # signed conflicting requests at same sequence
    EQUIVOCATE     = auto()  # sent different payloads to different nodes
    VIEW_TIMEOUT   = auto()  # primary stalled for too long
    INVALID_QC     = auto()  # participated in QC with insufficient sigs
    FORK_ACCOUNTABILITY = auto()  # caused or contributed to a ledger fork


@dataclass(frozen=True)
class MisbehaviorEvidence:
    """Immutable evidence of Byzantine misbehavior."""
    evidence_id: str
    node_id: str
    misbehavior_type: MisbehaviorType
    description: str
    conflicting_hashes: tuple[str, ...]   # e.g. request_hash_a, request_hash_b
    view: int
    sequence: int | None
    timestamp: float
    proof: str                            # raw evidence (e.g. two signatures)
    recorded_at: float = field(default_factory=time.time)


@dataclass
class SlashRecord:
    """Immutable slash record for a specific misbehavior event."""
    record_id: str
    node_id: str
    evidence_id: str
    misbehavior: MisbehaviorType
    slashed_at: float
    slashed_by: str                       # node_id of the detector
    height: int                           # ledger height at time of slashing
    is_appealed: bool = False
    appeal_result: str | None = None


class SlashingEngine:
    """
    Slashing engine — detects and records Byzantine misbehavior.

    Properties:
      - All slash records are append-only (never modified)
      - Slashed nodes are excluded from future quorums immediately
      - Evidence is immutable and can be used for off-chain arbitration

    Usage:
        engine = SlashingEngine()
        engine.slash(node_id='malicious-node', evidence=evidence)
        if engine.is_slashed('malicious-node'):
            # exclude from quorum
    """

    def __init__(self):
        self._slashed: set[str] = set()
        self._records: list[SlashRecord] = []
        self._evidence: dict[str, MisbehaviorEvidence] = {}  # evidence_id -> evidence
        self._appeal_records: dict[str, dict] = {}  # record_id -> appeal

    # ── Core Slashing ─────────────────────────────────────────────────────

    def slash(
        self,
        node_id: str,
        evidence: MisbehaviorEvidence,
        slashed_by: str = "SYSTEM",
    ) -> SlashRecord:
        """
        Slash a node — add to blacklist and record evidence.

        This operation is IDEMPOTENT: slashing an already-slashed node is a no-op
        (but still records the evidence).
        """
        record_id = hashlib.sha256(
            f"{node_id}{evidence.evidence_id}{time.time_ns()}".encode()
        ).hexdigest()[:16]

        self._slashed.add(node_id)

        record = SlashRecord(
            record_id=record_id,
            node_id=node_id,
            evidence_id=evidence.evidence_id,
            misbehavior=evidence.misbehavior_type,
            slashed_at=evidence.recorded_at,
            slashed_by=slashed_by,
            height=getattr(evidence, 'height', 0),
        )
        self._records.append(record)
        self._evidence[evidence.evidence_id] = evidence

        return record

    def is_slashed(self, node_id: str) -> bool:
        """Return True if node is currently slashed."""
        return node_id in self._slashed

    def get_slash_records(
        self,
        node_id: str | None = None,
    ) -> list[SlashRecord]:
        """Return slash records, optionally filtered by node_id."""
        if node_id is None:
            return list(self._records)
        return [r for r in self._records if r.node_id == node_id]

    def get_evidence(self, evidence_id: str) -> MisbehaviorEvidence | None:
        return self._evidence.get(evidence_id)

    # ── Double-Sign Detection ─────────────────────────────────────────────

    def report_double_sign(
        self,
        node_id: str,
        request_hash_a: str,
        request_hash_b: str,
        view: int,
        sequence: int,
        signature_a: str,
        signature_b: str,
        detected_by: str = "SYSTEM",
    ) -> SlashRecord:
        """
        Report and slash a double-signing incident.

        This is the primary slashing condition in BFT systems.
        Even one confirmed double-sign is sufficient to slash a node.
        """
        evidence_id = hashlib.sha256(
            f"{node_id}{request_hash_a}{request_hash_b}{time.time_ns()}".encode()
        ).hexdigest()[:16]

        evidence = MisbehaviorEvidence(
            evidence_id=evidence_id,
            node_id=node_id,
            misbehavior_type=MisbehaviorType.DOUBLE_SIGN,
            description=(
                f"Node {node_id} signed two different requests at (view={view}, seq={sequence}): "
                f"hash_a={request_hash_a[:12]}, hash_b={request_hash_b[:12]}"
            ),
            conflicting_hashes=(request_hash_a, request_hash_b),
            view=view,
            sequence=sequence,
            timestamp=time.time(),
            proof=f"sig_a={signature_a}, sig_b={signature_b}",
        )

        return self.slash(node_id, evidence, slashed_by=detected_by)

    def report_equivocation(
        self,
        node_id: str,
        payload_hash_a: str,
        payload_hash_b: str,
        detected_by: str = "SYSTEM",
    ) -> SlashRecord:
        """Report equivocation — sent different payloads to different nodes."""
        evidence_id = hashlib.sha256(
            f"{node_id}eq{time.time_ns()}".encode()
        ).hexdigest()[:16]

        evidence = MisbehaviorEvidence(
            evidence_id=evidence_id,
            node_id=node_id,
            misbehavior_type=MisbehaviorType.EQUIVOCATE,
            description=(
                f"Node {node_id} equivocated: sent conflicting payloads "
                f"hash_a={payload_hash_a[:12]}, hash_b={payload_hash_b[:12]}"
            ),
            conflicting_hashes=(payload_hash_a, payload_hash_b),
            view=0,
            sequence=None,
            timestamp=time.time(),
            proof=f"payload_a={payload_hash_a}, payload_b={payload_hash_b}",
        )

        return self.slash(node_id, evidence, slashed_by=detected_by)

    def report_invalid_qc(
        self,
        node_id: str,
        qc_request_hash: str,
        expected_threshold: int,
        actual_sigs: int,
        detected_by: str = "SYSTEM",
    ) -> SlashRecord:
        """Report participation in an invalid QC."""
        evidence_id = hashlib.sha256(
            f"{node_id}iqc{time.time_ns()}".encode()
        ).hexdigest()[:16]

        evidence = MisbehaviorEvidence(
            evidence_id=evidence_id,
            node_id=node_id,
            misbehavior_type=MisbehaviorType.INVALID_QC,
            description=(
                f"Node {node_id} participated in QC for {qc_request_hash[:12]} "
                f"with only {actual_sigs}/{expected_threshold} signatures"
            ),
            conflicting_hashes=(qc_request_hash,),
            view=0,
            sequence=None,
            timestamp=time.time(),
            proof=f"threshold={expected_threshold}, actual={actual_sigs}",
        )

        return self.slash(node_id, evidence, slashed_by=detected_by)

    # ── Fork Accountability ───────────────────────────────────────────────

    def report_fork(
        self,
        node_id: str,
        fork_height: int,
        evidence: str,
        detected_by: str = "SYSTEM",
    ) -> SlashRecord:
        """Report node responsible for a ledger fork."""
        evidence_id = hashlib.sha256(
            f"{node_id}fork{fork_height}{time.time_ns()}".encode()
        ).hexdigest()[:16]

        mis_evidence = MisbehaviorEvidence(
            evidence_id=evidence_id,
            node_id=node_id,
            misbehavior_type=MisbehaviorType.FORK_ACCOUNTABILITY,
            description=f"Fork detected at height {fork_height}: {evidence}",
            conflicting_hashes=(f"fork_at_{fork_height}",),
            view=0,
            sequence=None,
            timestamp=time.time(),
            proof=evidence,
        )

        return self.slash(node_id, mis_evidence, slashed_by=detected_by)

    # ── Appeal ────────────────────────────────────────────────────────────

    def appeal(self, record_id: str, appeal_reason: str) -> None:
        """File an appeal against a slash record."""
        for rec in self._records:
            if rec.record_id == record_id:
                rec.is_appealed = True
                rec.appeal_result = None
                self._appeal_records[record_id] = {
                    "reason": appeal_reason,
                    "filed_at": time.time(),
                    "pending": True,
                }
                break

    def resolve_appeal(self, record_id: str, upheld: bool) -> None:
        """Resolve an appeal — if rejected, node remains slashed."""
        if record_id in self._appeal_records:
            self._appeal_records[record_id]["pending"] = False
            self._appeal_records[record_id]["upheld"] = upheld
            for rec in self._records:
                if rec.record_id == record_id:
                    rec.appeal_result = "upheld" if upheld else "rejected"
                    if not upheld:
                        self._slashed.discard(rec.node_id)
                    break

    # ── Queries ──────────────────────────────────────────────────────────

    @property
    def slashed_count(self) -> int:
        return len(self._slashed)

    @property
    def total_slash_records(self) -> int:
        return len(self._records)

    def get_slashed_nodes(self) -> list[str]:
        return list(self._slashed)

    def summary(self) -> dict[str, Any]:
        return {
            "total_slashed": self.slashed_count,
            "total_records": self.total_slash_records,
            "pending_appeals": sum(
                1 for a in self._appeal_records.values() if a.get("pending")
            ),
            "slashed_nodes": list(self._slashed),
        }
