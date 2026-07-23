"""
ledger_normalizer.py — P7.2 Ledger Equivalence

Canonical representation for ledger entries:
  NormalizedLedgerEntry = {payload_hash, proof_hash, prev_hash, nonce}

Excludes (non-deterministic / federation-specific noise):
  - timestamp
  - node_id
  - quorum certificates
  - vote records
  - federation metadata
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

# ─── Canonical entry ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NormalizedLedgerEntry:
    """Deterministic ledger entry without noise fields."""
    payload_hash: str
    proof_hash: str
    prev_hash: str
    nonce: str


# ─── Normalization ─────────────────────────────────────────────────────────────


def normalize_entry(entry: dict | Any) -> NormalizedLedgerEntry:
    """
    Convert any ledger entry to NormalizedLedgerEntry.

    Accepts dict with flexible field names (from various ledger formats).
    Raises ValueError if required fields are missing.
    """
    if isinstance(entry, NormalizedLedgerEntry):
        return entry

    if isinstance(entry, dict):
        # Flexible field extraction — handle multiple naming conventions
        payload = (
            entry.get("payload_hash")
            or entry.get("request_payload_hash")
            or entry.get("data_hash")
        )
        proof = (
            entry.get("proof_hash")
            or entry.get("signature_hash")
            or entry.get("proof_signature")
        )
        prev = (
            entry.get("prev_hash")
            or entry.get("previous_hash")
            or entry.get("ledger_prev_hash")
        )
        nonce = (
            entry.get("nonce")
            or entry.get("request_nonce")
        )
        if payload is None or proof is None or prev is None or nonce is None:
            missing = [n for n, v in [
                ("payload_hash", payload), ("proof_hash", proof),
                ("prev_hash", prev), ("nonce", nonce)
            ] if v is None]
            raise ValueError(f"Ledger entry missing required fields: {missing}")
        return NormalizedLedgerEntry(
            payload_hash=str(payload),
            proof_hash=str(proof),
            prev_hash=str(prev),
            nonce=str(nonce),
        )

    raise ValueError(f"Unsupported ledger entry type: {type(entry)}")


def normalize_ledger(ledger: list) -> list[NormalizedLedgerEntry]:
    """
    Convert full ledger to canonical form.

    Preserves order (ledger is an append-only chain).
    """
    return [normalize_entry(e) for e in ledger]


# ─── Federated projection ────────────────────────────────────────────────────────


def project_federated_ledger(feg_ledger: list) -> list[NormalizedLedgerEntry]:
    """
    Remove federation-specific entries from federated ledger.

    Removes:
      - vote records (type == "vote")
      - quorum certificates (type == "qc" or "quorum_cert")
      - federation metadata (type == "federation" or "meta")
      - pending entries (status != "committed")

    Keeps only: entries that represent actual state mutations.
    """
    result = []
    for entry in feg_ledger:
        if isinstance(entry, dict):
            etype = str(entry.get("type", "")).lower()
            status = str(entry.get("status", "committed")).lower()

            # Skip non-committed entries
            if status not in ("committed", "final"):
                continue

            # Skip federation-layer metadata
            if etype in ("vote", "quorum_cert", "qc", "federation", "meta",
                        "pre_prepare", "prepare", "commit_vote"):
                continue

        # Accept: normalize and include
        try:
            result.append(normalize_entry(entry))
        except ValueError:
            # Silently skip malformed federated entries
            continue

    return result


# ─── Comparator ─────────────────────────────────────────────────────────────────


def compare_ledgers(
    eg_ledger: list,
    feg_ledger: list,
) -> tuple[bool, dict]:
    """
    Check ledger equivalence between EG and FEG.

    Returns:
        (True, {})  — ledgers are equivalent
        (False, {"reason": str, "eg_entry": ..., "feg_entry": ...})
    """
    try:
        norm_eg = normalize_ledger(eg_ledger)
    except ValueError as e:
        return False, {"reason": f"EG normalization failed: {e}"}

    try:
        norm_feg = project_federated_ledger(feg_ledger)
    except Exception as e:
        return False, {"reason": f"FEG projection failed: {e}"}

    if len(norm_eg) != len(norm_feg):
        return False, {
            "reason": f"length mismatch: EG={len(norm_eg)} vs FEG={len(norm_feg)}",
            "eg_len": len(norm_eg),
            "feg_len": len(norm_feg),
        }

    for i, (e, f) in enumerate(zip(norm_eg, norm_feg)):
        if e != f:
            return False, {
                "reason": f"entry {i} mismatch",
                "eg_entry": str(e),
                "feg_entry": str(f),
            }

    return True, {}


# ─── Ledger hash ─────────────────────────────────────────────────────────────────


def ledger_hash(ledger: list) -> str:
    """Deterministic SHA256 hash of normalized ledger."""
    normalized = normalize_ledger(ledger)
    serialized = json.dumps(
        [(e.payload_hash, e.proof_hash, e.prev_hash, e.nonce)
         for e in normalized],
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


def ledger_hash_from_normalized(normalized: list[NormalizedLedgerEntry]) -> str:
    """Hash from already-normalized entries (avoids double normalization)."""
    serialized = json.dumps(
        [(e.payload_hash, e.proof_hash, e.prev_hash, e.nonce)
         for e in normalized],
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


# ─── Invariant check ─────────────────────────────────────────────────────────────


def check_invariant(eg_ledger: list, feg_ledger: list) -> dict:
    """
    Full P7.2 invariant check: ledger_hash(EG) == ledger_hash(FEG)

    Returns dict with:
        - passed: bool
        - eg_hash: str
        - feg_hash: str
        - equivalence: bool
        - details: dict
    """
    eg_norm = normalize_ledger(eg_ledger)
    feg_norm = project_federated_ledger(feg_ledger)

    eg_h = ledger_hash_from_normalized(eg_norm)
    feg_h = ledger_hash_from_normalized(feg_norm)

    eq, details = compare_ledgers(eg_ledger, feg_ledger)

    return {
        "passed": eg_h == feg_h,
        "eg_hash": eg_h,
        "feg_hash": feg_h,
        "equivalence": eq,
        "eg_entries": len(eg_norm),
        "feg_entries": len(feg_norm),
        "details": details,
    }
