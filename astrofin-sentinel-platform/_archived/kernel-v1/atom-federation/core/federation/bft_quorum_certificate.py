"""bft_quorum_certificate.py — atom-federation-os v9.0+P7 BFT Quorum Certificate."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BFTThreshold:
    n: int
    f: int
    prepare_threshold: int
    commit_threshold: int

    @classmethod
    def from_n(cls, n: int) -> BFTThreshold:
        f = (n - 1) // 3
        return cls(n=n, f=f, prepare_threshold=2*f+1, commit_threshold=2*f+1)

    @property
    def honest_minimum(self) -> int:
        return self.f + 1


@dataclass(frozen=True)
class BFTQC:
    request_hash: str
    view: int
    sequence: int
    signatures: tuple[str, ...]
    nodes_signed: tuple[str, ...]
    threshold: int
    f: int
    aggregated_sig: str
    timestamp: float
    quorum_type: str

    def is_valid(self, slashed: frozenset[str]) -> bool:
        if len(self.signatures) < self.threshold:
            return False
        for node_id in self.nodes_signed:
            if node_id in slashed:
                return False
        return True

    @property
    def quorum_strength(self) -> float:
        return len(self.signatures) / self.threshold

    @property
    def description(self) -> str:
        n_sig = len(self.signatures)
        return (
            f"BFTQC(view={self.view},seq={self.sequence},"
            f"sigs={n_sig}/{self.threshold},f={self.f},type={self.quorum_type})"
        )


@dataclass
class BFTQCBuilder:
    request_hash: str
    view: int
    sequence: int
    threshold: int
    f: int
    quorum_type: str
    _signatures: list[str] = field(default_factory=list)
    _nodes: list[str] = field(default_factory=list)
    _sig_map: dict[str, str] = field(default_factory=dict)

    def add_signature(self, node_id: str, signature: str) -> bool:
        if node_id in self._sig_map:
            return len(self._signatures) >= self.threshold
        self._sig_map[node_id] = signature
        self._signatures.append(signature)
        self._nodes.append(node_id)
        return len(self._signatures) >= self.threshold

    @property
    def count(self) -> int:
        return len(self._signatures)

    def can_build(self) -> bool:
        return len(self._signatures) >= self.threshold

    def build(self) -> BFTQC:
        if not self.can_build():
            raise RuntimeError(
                f"Cannot build BFTQC: {len(self._signatures)}/{self.threshold} signatures"
            )
        agg = hashlib.sha256("".join(self._signatures).encode()).hexdigest()
        return BFTQC(
            request_hash=self.request_hash,
            view=self.view,
            sequence=self.sequence,
            signatures=tuple(self._signatures),
            nodes_signed=tuple(self._nodes),
            threshold=self.threshold,
            f=self.f,
            aggregated_sig=agg,
            timestamp=time.time(),
            quorum_type=self.quorum_type,
        )

    def merge(self, other: BFTQCBuilder) -> None:
        if other.request_hash != self.request_hash:
            raise ValueError("Cannot merge QC builders for different requests")
        if other.view != self.view or other.sequence != self.sequence:
            raise ValueError("Cannot merge QC builders for different view/sequence")
        for node_id, sig in zip(other._nodes, other._signatures):
            if node_id not in self._sig_map:
                self.add_signature(node_id, sig)


@dataclass
class QCValidationResult:
    valid: bool
    reason: str
    signatures_count: int
    threshold: int
    slashed_detected: list[str] = field(default_factory=list)
    quorum_strength: float = 0.0


def validate_bft_qc(qc: BFTQC, slashed: frozenset[str]) -> QCValidationResult:
    if len(qc.signatures) < qc.threshold:
        return QCValidationResult(
            valid=False,
            reason=f"insufficient signatures: {len(qc.signatures)} < {qc.threshold}",
            signatures_count=len(qc.signatures),
            threshold=qc.threshold,
        )
    slashed_found = [n for n in qc.nodes_signed if n in slashed]
    if slashed_found:
        return QCValidationResult(
            valid=False,
            reason=f"slashed nodes participated: {slashed_found}",
            signatures_count=len(qc.signatures),
            threshold=qc.threshold,
            slashed_detected=slashed_found,
        )
    strength = len(qc.signatures) / qc.threshold
    return QCValidationResult(
        valid=True,
        reason="ok",
        signatures_count=len(qc.signatures),
        threshold=qc.threshold,
        quorum_strength=strength,
    )
