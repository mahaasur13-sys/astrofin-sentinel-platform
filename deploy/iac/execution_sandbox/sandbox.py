#!/usr/bin/env python3
"""
ExecutionSandbox — Node-level isolation
Block: fs writes outside scope, network calls, env mutation, memory overflow
"""

from __future__ import annotations
import tempfile

import os
import resource
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ViolationType(Enum):
    FS_WRITE = "FS_WRITE"
    NETWORK_CALL = "NETWORK_CALL"
    ENV_MUTATE = "ENV_MUTATE"
    MEMORY_EXCEED = "MEMORY_EXCEED"
    EXTERNAL_API = "EXTERNAL_API"


@dataclass
class SandboxViolation:
    type: ViolationType
    node_id: str
    details: str


@dataclass
class SandboxResult:
    allowed: bool
    node_id: str
    output: Any = None
    violations: list[SandboxViolation] = field(default_factory=list)
    memory_bytes: int = 0


class ExecutionSandbox:
    def __init__(
        self,
        allowed_dirs: list[str] | None = None,
        max_memory_bytes: int = 8 * 1024**3,
        allow_network: bool = False,
        allow_env_write: bool = False,
    ):
        self.allowed_dirs = allowed_dirs or []
        self.max_memory = max_memory_bytes
        self.allow_network = allow_network
        self.allow_env_write = allow_env_write

    def validate_fs_write(self, path: str) -> bool:
        if not self.allowed_dirs:
            return True
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(d) for d in self.allowed_dirs)

    def execute(self, node: dict[str, Any]) -> SandboxResult:
        node_id = node.get("id", "?")
        # Check memory limit
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        if mem > self.max_memory:
            return SandboxResult(
                False,
                node_id,
                violations=[
                    SandboxViolation(
                        ViolationType.MEMORY_EXCEED,
                        node_id,
                        f"Memory {mem} > {self.max_memory}",
                    )
                ],
            )
        # Check fs write scope
        if "write_path" in node and not self.validate_fs_write(node["write_path"]):
            return SandboxResult(
                False,
                node_id,
                violations=[
                    SandboxViolation(
                        ViolationType.FS_WRITE,
                        node_id,
                        f"Write to '{node['write_path']}' outside allowed scope",
                    )
                ],
            )
        # Check network
        if node.get("network_required") and not self.allow_network:
            return SandboxResult(
                False,
                node_id,
                violations=[
                    SandboxViolation(
                        ViolationType.NETWORK_CALL, node_id, "Network call blocked"
                    )
                ],
            )
        # Check env mutation
        if node.get("env_mutate") and not self.allow_env_write:
            return SandboxResult(
                False,
                node_id,
                violations=[
                    SandboxViolation(
                        ViolationType.ENV_MUTATE, node_id, "Env mutation blocked"
                    )
                ],
            )
        return SandboxResult(True, node_id, output=node.get("output"))

    def execute_batch(self, nodes: list[dict[str, Any]]) -> list[SandboxResult]:
        return [self.execute(n) for n in nodes]


if __name__ == "__main__":
    sandbox = ExecutionSandbox(
        allowed_dirs=[os.path.join(tempfile.gettempdir(), "scope")],
        max_memory_bytes=1_000_000_000,
    )
    result = sandbox.execute({"id": "test", "output": 42})
    print(f"Allowed: {result.allowed}, Output: {result.output}")
    result2 = sandbox.execute({"id": "bad", "write_path": "/etc/passwd"})
    print(
        f"Blocked: {result2.violations[0].type.value if result2.violations else 'none'}"
    )
