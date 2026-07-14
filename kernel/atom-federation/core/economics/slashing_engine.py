"""slashing_engine.py — atom-federation-os v9.0+P8 Slashing Engine."""
from __future__ import annotations

import time
from enum import Enum

from core.economics.stake_registry import StakeTier


class SlashingReason(Enum):
    INVALID_PROOF = "invalid_proof"
    REPLAY_ATTACK = "replay_attack"
    FORK = "fork"
    RUNTIME_VIOLATION = "runtime_violation"
    DOUBLE_VOTE = "double_vote"
    TRIPLE_VOTE = "triple_vote"
    BYPASS_ATTEMPT = "bypass_attempt"
    VALIDATOR_MISS = "validator_miss"

FRACTIONS = {
    SlashingReason.INVALID_PROOF: 0.25,
    SlashingReason.REPLAY_ATTACK: 0.30,
    SlashingReason.FORK: 1.00,
    SlashingReason.RUNTIME_VIOLATION: 0.50,
    SlashingReason.DOUBLE_VOTE: 0.50,
    SlashingReason.TRIPLE_VOTE: 1.00,
    SlashingReason.BYPASS_ATTEMPT: 0.25,
    SlashingReason.VALIDATOR_MISS: 0.40,
}


class SlashingRecord:
    def __init__(self, record_id, node_id, reason, fraction, amount_slashed, timestamp, evidence):
        self.record_id = record_id
        self.node_id = node_id
        self.reason = reason
        self.fraction = fraction
        self.amount_slashed = amount_slashed
        self.timestamp = timestamp
        self.evidence = evidence


class EconomicSecurityViolation(Exception):
    pass


class ValidationSlashingError(EconomicSecurityViolation):
    pass


class SlashingEngine:
    def __init__(self, stake_registry):
        self._registry = stake_registry
        self._records = []
        self._vote_counts = {}

    def slash_for_reason(self, node_id, reason, evidence=None):
        fraction = FRACTIONS.get(reason, 0.25)
        amount = self._registry.slash(node_id, fraction)
        record = SlashingRecord(
            f"slash-{node_id}-{int(time.time()*1000)}",
            node_id, reason, fraction, amount, time.time(), evidence or {}
        )
        self._records.append(record)
        # Jail if fully slashed
        if self._registry.get_stake(node_id) <= 0:
            self._registry._stakes[node_id].tier = StakeTier.JAILED
        return amount

    def slash_invalid_proof(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.INVALID_PROOF, evidence)

    def slash_replay_attack(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.REPLAY_ATTACK, evidence)

    def slash_fork(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.FORK, evidence)

    def slash_runtime_violation(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.RUNTIME_VIOLATION, evidence)

    def slash_double_vote(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.DOUBLE_VOTE, evidence)

    def slash_triple_vote(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.TRIPLE_VOTE, evidence)

    def slash_bypass_attempt(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.BYPASS_ATTEMPT, evidence)

    def slash_validator_miss(self, node_id, evidence=None):
        return self.slash_for_reason(node_id, SlashingReason.VALIDATOR_MISS, evidence)

    def record_vote(self, node_id, proposal_hash):
        if node_id not in self._vote_counts:
            self._vote_counts[node_id] = set()
        self._vote_counts[node_id].add(proposal_hash)
        return len(self._vote_counts[node_id])

    def get_vote_count(self, node_id):
        return len(self._vote_counts.get(node_id, set()))

    def record_validator_miss(self, validator_node_id, violation_type, request_hash, detection_lag_ms):
        is_late = detection_lag_ms >= 5000
        if is_late:
            self.slash_validator_miss(validator_node_id, {
                "violation_type": violation_type,
                "request_hash": request_hash,
                "lag_ms": detection_lag_ms
            })
        return is_late

    def verify_and_slash_vote(self, node_id, proposal_hash, threshold=2):
        count = self.record_vote(node_id, proposal_hash)
        if count >= 3:
            self.slash_triple_vote(node_id, {"proposals": list(self._vote_counts[node_id])})
            return False
        if count == 2:
            self.slash_triple_vote(node_id, {"proposals": list(self._vote_counts[node_id])})
            return False
        return True

    def get_records(self, node_id=None):
        if node_id:
            return tuple(r for r in self._records if r.node_id == node_id)
        return tuple(self._records)

    def total_slashed(self):
        return sum(r.amount_slashed for r in self._records)

    def reverse_slashing(self, node_id):
        raise EconomicSecurityViolation(
            f"Slashing records are IMMUTABLE. Cannot reverse for {node_id}"
        )
