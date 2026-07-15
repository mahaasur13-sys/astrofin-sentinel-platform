"""
DAG-Aware Retry Engine — Layer B.

Provides:
- DagNode / RetryStrategy model
- PartialRecomputeStore (Redis hash per task_id)
- DagRetryEngine with upstream rollback + memoised recompute
- DAG state persistence (nodes stored in Redis)
"""

from __future__ import annotations

import enum
import json
import os
import time
from dataclasses import dataclass, field

import redis.asyncio as aioredis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# ── async redis singleton ─────────────────────────────────────────────────────

_async_r: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _async_r
    if _async_r is None:
        _async_r = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _async_r


# ── enums ──────────────────────────────────────────────────────────────────────

class RetryStrategy(str, enum.Enum):
    NONE = "none"                 # simple retry of the node
    UPSTREAM = "upstream"          # retry node + recursively retry all dependencies
    PARTIAL_RECOMPUTE = "partial_recompute"  # reuse cached ancestors, recompute only failed branch


class NodeStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ── model ──────────────────────────────────────────────────────────────────────

@dataclass
class DagNode:
    id: str
    task_id: str
    deps: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    result: dict | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "deps": self.deps,
            "status": self.status.value,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DagNode:
        return cls(
            id=d["id"],
            task_id=d["task_id"],
            deps=d.get("deps", []),
            status=NodeStatus(d.get("status", "PENDING")),
            retries=int(d.get("retries", 0)),
            max_retries=int(d.get("max_retries", 3)),
            result=d.get("result"),
            error=d.get("error"),
            created_at=float(d.get("created_at", time.time())),
            updated_at=float(d.get("updated_at", time.time())),
        )


# ── Partial Recompute Store ─────────────────────────────────────────────────────

class PartialRecomputeStore:
    """
    Redis hash store: task:{task_id}:nodes → {node_id: json(result), ...}
    Persists computed node results across retries so we only recompute
    the failed branch, not the entire DAG.
    """

    def __init__(self, ttl_seconds: int = 86400):
        self.ttl = ttl_seconds

    def _hash_key(self, task_id: str) -> str:
        return f"prs:{task_id}"

    async def save(self, task_id: str, node_id: str, result: dict) -> None:
        r = await _get_redis()
        key = self._hash_key(task_id)
        await r.hset(key, node_id, json.dumps(result))
        await r.expire(key, self.ttl)

    async def load_node(self, task_id: str, node_id: str) -> dict | None:
        r = await _get_redis()
        raw = await r.hget(self._hash_key(task_id), node_id)
        if raw is None:
            return None
        return json.loads(raw)

    async def load_all(self, task_id: str) -> dict[str, dict]:
        r = await _get_redis()
        raw = await r.hgetall(self._hash_key(task_id))
        return {k: json.loads(v) for k, v in raw.items()}

    async def has(self, task_id: str, node_id: str) -> bool:
        r = await _get_redis()
        return await r.hexists(self._hash_key(task_id), node_id)

    async def evict(self, task_id: str, node_id: str) -> None:
        r = await _get_redis()
        await r.hdel(self._hash_key(task_id), node_id)

    async def evict_subtree(self, task_id: str, node_ids: list[str]) -> None:
        r = await _get_redis()
        if node_ids:
            await r.hdel(self._hash_key(task_id), *node_ids)

    async def get_cached_ancestors(self, task_id: str, node_ids: list[str]) -> dict[str, dict]:
        """Return only those node_ids that are already cached."""
        result = {}
        for nid in node_ids:
            cached = await self.load_node(task_id, nid)
            if cached is not None:
                result[nid] = cached
        return result


# ── DAG State Store ─────────────────────────────────────────────────────────────

class DagStateStore:
    """
    Redis hash per task: dag:{task_id} → {node_id: json(node_dict)}
    """

    def _key(self, task_id: str) -> str:
        return f"dag:{task_id}"

    async def save_node(self, node: DagNode) -> None:
        r = await _get_redis()
        await r.hset(self._key(node.task_id), node.id, json.dumps(node.to_dict()))

    async def load_node(self, task_id: str, node_id: str) -> DagNode | None:
        r = await _get_redis()
        raw = await r.hget(self._key(task_id), node_id)
        if raw is None:
            return None
        return DagNode.from_dict(json.loads(raw))

    async def load_all(self, task_id: str) -> dict[str, DagNode]:
        r = await _get_redis()
        raw = await r.hgetall(self._key(task_id))
        return {k: DagNode.from_dict(json.loads(v)) for k, v in raw.items()}

    async def update_status(self, task_id: str, node_id: str, status: NodeStatus,
                            error: str | None = None,
                            result: dict | None = None) -> None:
        node = await self.load_node(task_id, node_id)
        if node is None:
            return
        node.status = status
        node.updated_at = time.time()
        node.error = error
        if result is not None:
            node.result = result
        await self.save_node(node)

    async def delete_task(self, task_id: str) -> None:
        r = await _get_redis()
        await r.delete(self._key(task_id))


# ── DAG Retry Engine ────────────────────────────────────────────────────────────

class DagRetryEngine:
    """
    Dag-aware retry with two strategies:

    1. UPSTREAM — when a node fails, recursively retry all its dependencies
       first, then the node itself. Used when deps may have produced stale data.

    2. PARTIAL_RECOMPUTE — load cached results for already-computed ancestors
       from PartialRecomputeStore; only run the failed branch.
       Used when we know upstream results are still valid.
    """

    def __init__(self,
                 state_store: DagStateStore | None = None,
                 recompute_store: PartialRecomputeStore | None = None,
                 default_max_retries: int = 3):
        self.state = state_store or DagStateStore()
        self.recompute = recompute_store or PartialRecomputeStore()
        self.default_max_retries = default_max_retries

    # ── DAG construction ───────────────────────────────────────────────────────

    async def create_dag(self, task_id: str, node_specs: list[dict]) -> list[DagNode]:
        """
        node_specs: [{"id": str, "deps": [str]}, ...]
        Returns list of created DagNode objects.
        """
        nodes = {}
        for spec in node_specs:
            node = DagNode(
                id=spec["id"],
                task_id=task_id,
                deps=spec.get("deps", []),
                max_retries=spec.get("max_retries", self.default_max_retries),
            )
            nodes[node.id] = node
            await self.state.save_node(node)
        return list(nodes.values())

    # ── retry operations ────────────────────────────────────────────────────────

    async def retry_node(self,
                         task_id: str,
                         node_id: str,
                         strategy: RetryStrategy = RetryStrategy.NONE,
                         executor=None) -> DagNode:
        """
        Retry a specific node with the given strategy.

        executor: callable(node: DagNode) -> dict
                 Called to recompute a node when needed.
        """
        node = await self.state.load_node(task_id, node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found in task {task_id}")

        if node.retries >= node.max_retries:
            await self.state.update_status(task_id, node_id, NodeStatus.FAILED,
                                           error="max_retries_exceeded")
            return node

        if strategy == RetryStrategy.NONE:
            return await self._retry_none(node, executor)
        elif strategy == RetryStrategy.UPSTREAM:
            return await self._retry_upstream(node, executor)
        elif strategy == RetryStrategy.PARTIAL_RECOMPUTE:
            return await self._retry_partial(node, executor)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    async def _retry_none(self, node: DagNode, executor) -> DagNode:
        node.retries += 1
        node.status = NodeStatus.PENDING
        node.updated_at = time.time()
        await self.state.save_node(node)
        if executor:
            result = await executor(node)
            node.result = result
            node.status = NodeStatus.DONE
        await self.state.save_node(node)
        return node

    async def _retry_upstream(self, node: DagNode, executor) -> DagNode:
        """
        Retry dependencies first (depth-first), then the node itself.
        Used when a dependency failure may have tainted downstream results.
        """
        # Recursively retry all deps first
        for dep_id in node.deps:
            dep_node = await self.state.load_node(node.task_id, dep_id)
            if dep_node and dep_node.status == NodeStatus.FAILED:
                await self._retry_upstream(dep_node, executor)

        # Evict cached results for this node and its downstream
        await self.recompute.evict(node.task_id, node.id)
        downstream = await self._get_downstream_nodes(node.task_id, node.id)
        if downstream:
            await self.recompute.evict_subtree(node.task_id, downstream)

        # Re-run this node
        return await self._retry_none(node, executor)

    async def _retry_partial(self, node: DagNode, executor) -> DagNode:
        """
        Load cached ancestors from PartialRecomputeStore.
        Only recompute the failed node (ancestors are assumed valid).
        """
        cached_ancestors = await self.recompute.get_cached_ancestors(
            node.task_id, node.deps
        )
        node.retries += 1
        node.updated_at = time.time()

        if executor:
            # Inject cached deps as inputs
            computed_inputs = {dep_id: cached_ancestors.get(dep_id)
                                for dep_id in node.deps}
            node_obj_with_inputs = _NodeWithInputs(node, computed_inputs)
            result = await executor(node_obj_with_inputs)
            node.result = result
            node.status = NodeStatus.DONE
            # Cache this node's result for its downstream
            await self.recompute.save(node.task_id, node.id, result)
        else:
            node.status = NodeStatus.PENDING

        await self.state.save_node(node)
        return node

    # ── helpers ────────────────────────────────────────────────────────────────

    async def _get_downstream_nodes(self, task_id: str, node_id: str) -> list[str]:
        """Return all nodes that depend on node_id (direct downstream)."""
        all_nodes = await self.state.load_all(task_id)
        downstream = []
        for nid, n in all_nodes.items():
            if node_id in n.deps:
                downstream.append(nid)
        return downstream

    async def dag_status(self, task_id: str) -> dict:
        """Return a summary of all node statuses for a task DAG."""
        nodes = await self.state.load_all(task_id)
        if not nodes:
            return {"task_id": task_id, "nodes": {}, "summary": "not_found"}

        by_status = {}
        for nid, node in nodes.items():
            by_status.setdefault(node.status.value, []).append(nid)

        return {
            "task_id": task_id,
            "total": len(nodes),
            "by_status": by_status,
            "nodes": {nid: n.to_dict() for nid, n in nodes.items()},
        }

    async def mark_running(self, task_id: str, node_id: str) -> None:
        await self.state.update_status(task_id, node_id, NodeStatus.RUNNING)

    async def mark_done(self, task_id: str, node_id: str,
                        result: dict) -> None:
        await self.state.update_status(task_id, node_id, NodeStatus.DONE, result=result)
        await self.recompute.save(task_id, node_id, result)

    async def mark_failed(self, task_id: str, node_id: str,
                          error: str) -> None:
        await self.state.update_status(task_id, node_id, NodeStatus.FAILED, error=error)

    async def reset_node(self, task_id: str, node_id: str) -> None:
        """Reset a node to PENDING so it can be retried."""
        node = await self.state.load_node(task_id, node_id)
        if node:
            node.status = NodeStatus.PENDING
            node.updated_at = time.time()
            await self.state.save_node(node)


# ── helper class ───────────────────────────────────────────────────────────────

class _NodeWithInputs:
    """Wrapper that carries cached ancestor results into the executor."""
    def __init__(self, node: DagNode, computed_inputs: dict):
        self.id = node.id
        self.task_id = node.task_id
        self.deps = node.deps
        self.retries = node.retries
        self.max_retries = node.max_retries
        self.computed_inputs = computed_inputs  # {dep_id: result_dict}
