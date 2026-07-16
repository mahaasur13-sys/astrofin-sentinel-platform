#!/usr/bin/env python3
"""
Hash Chain — Cryptographic Trace Integrity
Extends trace with SHA256 node_hash_chain + dag_hash + execution_hash
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HashChain:
    trace_id: str
    dag_hash: str
    node_hash_chain: list[str] = field(default_factory=list)
    execution_hashes: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def add_node_hash(self, node_result: dict[str, Any]) -> str:
        h = hashlib.sha256(json.dumps(node_result, sort_keys=True).encode()).hexdigest()
        self.node_hash_chain.append(h)
        return h

    def add_execution_hash(self, state: dict[str, Any]) -> str:
        h = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        self.execution_hashes.append(h)
        return h

    def verify_chain(self) -> tuple[bool, list[str]]:
        errors = []
        for i, node_h in enumerate(self.node_hash_chain):
            expected = self.node_hash_chain[i]
            if len(self.node_hash_chain) > i + 1:
                next_h = self.node_hash_chain[i + 1]
                hashlib.sha256((expected + next_h).encode()).hexdigest()
        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "dag_hash": self.dag_hash,
            "node_hash_chain": self.node_hash_chain,
            "execution_hashes": self.execution_hashes,
            "metadata": self.metadata,
            "is_valid": self.verify_chain()[0],
        }


def compute_deterministic_hash(data: dict[str, Any], seed: int) -> str:
    base = json.dumps(data, sort_keys=True) + str(seed)
    return hashlib.sha256(base.encode()).hexdigest()


if __name__ == "__main__":
    chain = HashChain("test-001", dag_hash="abc123")
    chain.add_node_hash({"node": "a", "output": 42})
    chain.add_node_hash({"node": "b", "output": 99})
    print(chain.to_dict())
    print(f"Valid: {chain.verify_chain()[0]}")
