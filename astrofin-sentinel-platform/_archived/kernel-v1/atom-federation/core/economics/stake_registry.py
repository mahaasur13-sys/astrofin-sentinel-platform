"""stake_registry.py — atom-federation-os v9.0+P8 Stake Registry."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum


class StakeTier(Enum):
    FOUNDING = "founding"
    ACTIVE = "active"
    PROBATION = "probation"
    JAILED = "jailed"

@dataclass
class NodeStake:
    node_id: str
    amount: float
    tier: StakeTier = StakeTier.ACTIVE
    last_update: float = field(default=0.0)
    weight: float = 1.0

    def __post_init__(self):
        self.weight = self.amount

class StakeRegistry:
    def __init__(self, initial_total_stake: float = 0.0):
        self._total = initial_total_stake
        self._stakes: dict = {}
        self._lock = threading.Lock()
        self._deposits: dict = {}
        self._withdrawals: dict = {}

    def deposit(self, node_id: str, amount: float) -> None:
        with self._lock:
            existing = self._stakes.get(node_id)
            if existing:
                existing.amount += amount
            else:
                self._stakes[node_id] = NodeStake(node_id=node_id, amount=amount)
            self._total += amount
            self._deposits[node_id] = self._deposits.get(node_id, 0.0) + amount

    def withdraw(self, node_id: str, amount: float) -> None:
        with self._lock:
            stake = self._stakes.get(node_id)
            if not stake:
                return
            actual = min(amount, stake.amount)
            stake.amount = max(0.0, stake.amount - actual)
            self._total = max(0.0, self._total - actual)
            self._withdrawals[node_id] = self._withdrawals.get(node_id, 0.0) + actual

    def slash(self, node_id: str, fraction: float) -> float:
        with self._lock:
            stake = self._stakes.get(node_id)
            if not stake or stake.amount <= 0:
                return 0.0
            slashed_amt = stake.amount * fraction
            stake.amount = max(0.0, stake.amount - slashed_amt)
            self._total = max(0.0, self._total - slashed_amt)
            return slashed_amt

    def get_stake(self, node_id: str) -> float:
        return self._stakes.get(node_id, NodeStake(node_id=node_id, amount=0.0)).amount

    def get_weight(self, node_id: str) -> float:
        return self.get_stake(node_id)

    def total_stake(self) -> float:
        return self._total

    def snapshot(self) -> dict:
        return {n: s.amount for n, s in self._stakes.items()}

    def get_tier(self, node_id: str) -> StakeTier:
        return self._stakes.get(node_id, NodeStake(node_id=node_id, amount=0.0)).tier

    def is_jailed(self, node_id: str) -> bool:
        return self.get_tier(node_id) == StakeTier.JAILED
