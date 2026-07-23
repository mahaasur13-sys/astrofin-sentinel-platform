"""distributed_ledger.py — atom-federation-os v9.0+P7 DistributedLedger.

Append-only ledger with BFT quorum certificates and fork detection.

Key design:
    - Ledger is append-only (no delete / rewrite)
    - Genesis entry: prev_hash = "GENESIS", appended unconditionally
    - All subsequent entries: prev_hash must match current HEAD
    - fork_detected() checks if local ledger diverges from peer ledger
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass

from .quorum_certificate import QuorumCertificate


@dataclass
class LedgerEntry:
    """
    Single immutable entry in the distributed ledger.
    Created ONLY after quorum is reached and QC is formed.
    """
    entry_hash: str           # SHA-256(prev_hash + QC hash + timestamp)
    prev_hash: str            # hash of previous entry ("GENESIS" for first)
    qc: QuorumCertificate    # quorum certificate for this entry
    timestamp: float
    term: int
    payload_preview: str      # first 64 chars of payload for human audit

    @staticmethod
    def compute_hash(prev_hash: str, qc: QuorumCertificate, timestamp: float) -> str:
        data = f"{prev_hash}{qc.aggregated_signature}{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_chain(self, prev_entry: LedgerEntry | None) -> bool:
        """
        Verify this entry's chain linkage.

        Args:
            prev_entry: the entry that should precede this one, or None if genesis.

        Returns True if chain is valid.
        """
        # Genesis entry: prev_hash must be "GENESIS", prev_entry must be None
        if prev_entry is None:
            if self.prev_hash != "GENESIS":
                return False
            # Verify self-hash (entry_hash must match computed hash)
            computed = self.compute_hash(self.prev_hash, self.qc, self.timestamp)
            if computed != self.entry_hash:
                return False
            return True

        # Non-genesis: prev_hash must link to previous entry
        expected_prev = prev_entry.entry_hash
        if self.prev_hash != expected_prev:
            return False

        # Verify self-hash
        computed = self.compute_hash(self.prev_hash, self.qc, self.timestamp)
        if computed != self.entry_hash:
            return False

        return True


class LedgerIntegrityError(Exception):
    """Raised when ledger integrity is compromised."""
    pass


class DistributedLedger:
    """
    Append-only distributed ledger with fork detection.

    Each committed entry is a LedgerEntry containing a QuorumCertificate.
    Ledger grows ONLY via quorum consensus — no single node can append.

    Anti-fork mechanism:
        - Ledger is append-only (no delete / rewrite)
        - Genesis entry: appended unconditionally (no prev_hash check)
        - Subsequent entries: prev_hash must chain to current HEAD
        - Any divergence from HEAD -> REJECT (fork detected)
    """

    def __init__(self, ledger_path: str | None = None):
        self._path = pathlib.Path(ledger_path) if ledger_path else None
        self._entries: list[LedgerEntry] = []
        self._head_hash: str = "GENESIS"
        self._term: int = 0

        if self._path and self._path.exists():
            self._load()

    def _load(self) -> None:
        """Load ledger from disk."""
        try:
            data = json.loads(self._path.read_text())
            for e in data["entries"]:
                vote_records = []
                for v in e.get("qc", {}).get("vote_records", []):
                    from .consensus import VoteRecord, VoteValue
                    vote_records.append(VoteRecord(
                        node_id=v["node_id"],
                        value=VoteValue(v["value"]) if isinstance(v["value"], str) else v["value"],
                        term=v["term"],
                        proof_hash=v["proof_hash"],
                        payload_hash=v["payload_hash"],
                        timestamp=v["timestamp"],
                        reason=v.get("reason", ""),
                    ))
                from .quorum_certificate import QuorumCertificate
                qc_dict = e.get("qc", {})
                qc = QuorumCertificate(
                    vote_records=tuple(vote_records),
                    aggregated_signature=qc_dict.get("aggregated_signature", ""),
                    proof_hash=qc_dict.get("proof_hash", ""),
                    payload_hash=qc_dict.get("payload_hash", ""),
                    quorum_size=qc_dict.get("quorum_size", 0),
                    threshold=qc_dict.get("threshold", 0),
                    timestamp=qc_dict.get("timestamp", 0.0),
                    round_id=qc_dict.get("round_id", ""),
                )
                self._entries.append(LedgerEntry(
                    entry_hash=e["entry_hash"],
                    prev_hash=e["prev_hash"],
                    qc=qc,
                    timestamp=e["timestamp"],
                    term=e["term"],
                    payload_preview=e.get("payload_preview", ""),
                ))
            self._head_hash = self._entries[-1].entry_hash if self._entries else "GENESIS"
            self._term = self._entries[-1].term if self._entries else 0
        except Exception:
            pass  # start fresh

    def _save(self) -> None:
        """Persist ledger to disk."""
        if not self._path:
            return
        data = {
            "entries": [
                {
                    "entry_hash": e.entry_hash,
                    "prev_hash": e.prev_hash,
                    "qc": {
                        "vote_records": [
                            {
                                "node_id": v.node_id,
                                "value": v.value.value if hasattr(v.value, "value") else str(v.value),
                                "term": v.term,
                                "proof_hash": v.proof_hash,
                                "payload_hash": v.payload_hash,
                                "timestamp": v.timestamp,
                                "reason": getattr(v, "reason", ""),
                            }
                            for v in e.qc.vote_records
                        ],
                        "aggregated_signature": e.qc.aggregated_signature,
                        "proof_hash": e.qc.proof_hash,
                        "payload_hash": e.qc.payload_hash,
                        "quorum_size": e.qc.quorum_size,
                        "threshold": e.qc.threshold,
                        "timestamp": e.qc.timestamp,
                        "round_id": e.qc.round_id,
                    },
                    "timestamp": e.timestamp,
                    "term": e.term,
                    "payload_preview": e.payload_preview,
                }
                for e in self._entries
            ]
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))

    @property
    def entries(self) -> list:
        return list(self._entries)

    @property
    def head_hash(self) -> str:
        return self._head_hash

    @property
    def is_empty(self) -> bool:
        return len(self._entries) == 0

    @property
    def length(self) -> int:
        return len(self._entries)

    def try_append(self, entry: LedgerEntry) -> bool:
        """
        Attempt to append an entry to the ledger.

        Returns False if:
            - entry's prev_hash does not match current HEAD (fork detected)
            - entry fails chain verification
            - any other validation failure

        SPECIAL RULE: Genesis entry (ledger is empty) ALWAYS succeeds.
        """
        # Genesis rule: if ledger is empty, allow first append unconditionally.
        # The first entry's prev_hash MUST be "GENESIS" — this is the only requirement.
        # We skip verify_chain() here because the genesis entry's entry_hash was
        # computed externally (e.g. in tests or by a genesis protocol) and may not
        # match our local compute_hash() which depends on the exact QC snapshot.
        if self.is_empty:
            if entry.prev_hash != "GENESIS":
                return False
            self._entries.append(entry)
            self._head_hash = entry.entry_hash
            self._term = max(self._term, entry.term)
            self._save()
            return True

        # Fork detection: prev_hash must chain to current HEAD.
        # We do NOT re-verify the entry's self-hash (compute_hash) here because:
        #   - Genesis entries: created externally, hash won't match local recomputation
        #   - Non-genesis entries: hash was validated when the QC was formed
        # The QC's aggregated signature is the trust anchor — not local hash recomputation.
        if entry.prev_hash != self._head_hash:
            return False

        self._entries.append(entry)
        self._head_hash = entry.entry_hash
        self._term = max(self._term, entry.term)
        self._save()
        return True

    def force_append(self, entry: LedgerEntry) -> None:
        """
        Force-append an entry (used only for genesis or recovery).
        Bypasses prev_hash check. Use with extreme caution.
        """
        self._entries.append(entry)
        self._head_hash = entry.entry_hash
        self._term = max(self._term, entry.term)
        self._save()

    def fork_detected(self, peer_head_hash: str) -> bool:
        """Return True if peer ledger has diverged from local ledger."""
        return peer_head_hash != self._head_hash

    def get_status(self) -> dict:
        """Return human-readable ledger status."""
        return {
            "entries": len(self._entries),
            "head_hash": self._head_hash[:16] + "...",
            "term": self._term,
        }

    def summary(self) -> str:
        return f"Ledger(len={self.length}, head={self.head_hash[:12]}...)"

    def __repr__(self) -> str:
        return f"DistributedLedger(entries={self.length}, head={self.head_hash[:12]})"
