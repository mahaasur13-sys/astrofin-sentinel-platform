"""
Execution DAG Recorder — v3 core component.

Captures: task → step graph → span tree → persisted trace.
Enables: replay, deterministic reconstruction, latency analysis.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum

import redis.asyncio as aioredis


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepSpan:
    step_id: str
    step_name: str
    tool: str
    parent_id: str | None       # parent step_id (None = root)
    status: StepStatus = StepStatus.PENDING
    started_at: float | None = None
    finished_at: float | None = None
    latency_ms: float | None = None
    error: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: dict = field(default_factory=dict)
    # children tracked via parent_id linkage
    child_ids: list[str] = field(default_factory=list)

    def duration_ms(self) -> float:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return 0.0


@dataclass
class ExecutionDAG:
    dag_id: str
    task_id: str
    epoch: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    status: StepStatus = StepStatus.PENDING
    steps: dict[str, StepSpan] = field(default_factory=dict)
    root_ids: list[str] = field(default_factory=list)
    # aggregated metrics
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    tool_usage: dict[str, int] = field(default_factory=dict)   # tool → count

    def to_dict(self) -> dict:
        return {
            "dag_id": self.dag_id,
            "task_id": self.task_id,
            "epoch": self.epoch,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status.value,
            "steps": {k: {**asdict(v), "child_ids": v.child_ids} for k, v in self.steps.items()},
            "root_ids": self.root_ids,
            "total_latency_ms": self.total_latency_ms,
            "total_tokens": self.total_tokens,
            "tool_usage": self.tool_usage,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ExecutionDAG:
        d = dict(d)
        d["status"] = StepStatus(d["status"])
        steps_raw = d.pop("steps", {})
        steps = {}
        for k, v in steps_raw.items():
            v["status"] = StepStatus(v["status"])
            steps[k] = StepSpan(**v)
        d["steps"] = steps
        return cls(**d)


class DAGRecorder:
    """
    Thread-safe, async-native execution trace recorder.
    
    Usage:
        recorder = DAGRecorder()
        dag_id = await recorder.create(task_id)
        step_id = await recorder.add_step(dag_id, name="search", tool="web", parent_id=None)
        await recorder.start_step(step_id)
        await recorder.finish_step(step_id, output_tokens=120)
        dag = await recorder.finalize(dag_id)
    """

    REDIS_PREFIX = "dag:"
    TTL_SECONDS = 86400 * 7  # 7 days retention

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis: aioredis.Redis | None = None
        self._redis_url = redis_url
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_lock = asyncio.Lock()

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def _get_lock(self, key: str) -> asyncio.Lock:
        async with self._locks_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    # ── DAG lifecycle ─────────────────────────────────────────────────────────

    async def create(self, task_id: str, epoch: int = 0) -> str:
        """Create a new DAG for task_id + epoch. Returns dag_id."""
        dag_id = str(uuid.uuid4())
        dag = ExecutionDAG(dag_id=dag_id, task_id=task_id, epoch=epoch)
        r = await self._get_redis()
        key = f"{self.REDIS_PREFIX}{task_id}:{epoch}:{dag_id}"
        await r.setex(key, self.TTL_SECONDS, json.dumps(dag.to_dict(), default=str))
        # reverse index so load() can find it
        await r.setex(f"dag:meta:{dag_id}", self.TTL_SECONDS, f"{task_id}:{epoch}")
        return dag_id

    async def load(self, dag_id: str) -> ExecutionDAG | None:
        """Load DAG by dag_id. Uses meta index for epoch-aware keys."""
        r = await self._get_redis()
        # try legacy simple key first
        raw = await r.get(f"{self.REDIS_PREFIX}{dag_id}")
        if raw:
            return ExecutionDAG.from_dict(json.loads(raw))
        # look up meta index
        meta = await r.get(f"dag:meta:{dag_id}")
        if not meta:
            return None
        task_id, epoch = meta.split(":")
        epoch = int(epoch)
        raw = await r.get(f"{self.REDIS_PREFIX}{task_id}:{epoch}:{dag_id}")
        if not raw:
            return None
        return ExecutionDAG.from_dict(json.loads(raw))

    async def save(self, dag: ExecutionDAG) -> None:
        """Persist DAG to Redis with meta index for loadability."""
        r = await self._get_redis()
        key = f"{self.REDIS_PREFIX}{dag.task_id}:{dag.epoch}:{dag.dag_id}"
        await r.setex(key, self.TTL_SECONDS, json.dumps(dag.to_dict(), default=str))
        await r.setex(f"dag:meta:{dag.dag_id}", self.TTL_SECONDS, f"{dag.task_id}:{dag.epoch}")

    async def finalize(self, dag_id: str) -> ExecutionDAG | None:
        """Mark DAG complete, compute aggregations, persist."""
        dag = await self.load(dag_id)
        if not dag:
            return None

        dag.finished_at = time.time()

        # aggregate total latency
        total = 0.0
        tokens = 0
        tool_counts: dict[str, int] = {}
        for step in dag.steps.values():
            total += step.duration_ms()
            tokens += step.input_tokens + step.output_tokens
            tool_counts[step.tool] = tool_counts.get(step.tool, 0) + 1

        dag.total_latency_ms = total
        dag.total_tokens = tokens
        dag.tool_usage = tool_counts

        # finalize status
        if all(s.status == StepStatus.COMPLETED for s in dag.steps.values()):
            dag.status = StepStatus.COMPLETED
        elif any(s.status == StepStatus.FAILED for s in dag.steps.values()):
            dag.status = StepStatus.FAILED
        elif any(s.status == StepStatus.CANCELLED for s in dag.steps.values()):
            dag.status = StepStatus.CANCELLED

        await self.save(dag)
        return dag

    # ── step lifecycle ──────────────────────────────────────────────────────

    async def add_step(
        self,
        dag_id: str,
        step_name: str,
        tool: str,
        parent_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Add a step to DAG. Returns step_id."""
        lock = await self._get_lock(dag_id)
        async with lock:
            dag = await self.load(dag_id)
            if not dag:
                raise ValueError(f"DAG {dag_id} not found")

            step_id = str(uuid.uuid4())
            span = StepSpan(
                step_id=step_id,
                step_name=step_name,
                tool=tool,
                parent_id=parent_id,
                metadata=metadata or {},
            )

            dag.steps[step_id] = span

            # link to parent
            if parent_id:
                if parent_id in dag.steps:
                    dag.steps[parent_id].child_ids.append(step_id)
                else:
                    # parent not yet registered — will link later via relink()
                    pass
            else:
                dag.root_ids.append(step_id)

            await self.save(dag)
            return step_id

    async def start_step(self, dag_id: str, step_id: str) -> None:
        """Mark step as RUNNING with timestamp."""
        lock = await self._get_lock(dag_id)
        async with lock:
            dag = await self.load(dag_id)
            if not dag or step_id not in dag.steps:
                return
            step = dag.steps[step_id]
            step.status = StepStatus.RUNNING
            step.started_at = time.time()
            if dag.started_at is None:
                dag.started_at = step.started_at
            await self.save(dag)

    async def finish_step(
        self,
        dag_id: str,
        step_id: str,
        status: StepStatus = StepStatus.COMPLETED,
        error: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: dict | None = None,
    ) -> None:
        """Mark step as completed/failed/cancelled."""
        lock = await self._get_lock(dag_id)
        async with lock:
            dag = await self.load(dag_id)
            if not dag or step_id not in dag.steps:
                return
            step = dag.steps[step_id]
            step.status = status
            step.finished_at = time.time()
            step.error = error
            step.input_tokens = input_tokens
            step.output_tokens = output_tokens
            step.latency_ms = step.duration_ms()
            if metadata:
                step.metadata.update(metadata)
            await self.save(dag)

    # ── traversal helpers ────────────────────────────────────────────────────

    async def get_step_tree(self, dag_id: str) -> dict:
        """Return hierarchical view: {step_id: {children: [...]}}."""
        dag = await self.load(dag_id)
        if not dag:
            return {}
        tree = {}
        for step in dag.steps.values():
            tree[step.step_id] = {
                "name": step.step_name,
                "tool": step.tool,
                "status": step.status.value,
                "latency_ms": step.latency_ms or 0,
                "children": step.child_ids,
                "parent": step.parent_id,
            }
        return tree

    async def get_observability_report(self, dag_id: str) -> dict:
        """Latency per step, tool heatmap, failure clustering."""
        dag = await self.load(dag_id)
        if not dag:
            return {}

        # latency per step
        step_latencies = [
            {
                "step_id": s.step_id,
                "name": s.step_name,
                "tool": s.tool,
                "latency_ms": s.latency_ms or 0,
                "status": s.status.value,
            }
            for s in dag.steps.values()
        ]
        step_latencies.sort(key=lambda x: -(x["latency_ms"] or 0))

        # tool usage heatmap
        tool_latencies: dict[str, list[float]] = {}
        for s in dag.steps.values():
            if s.tool not in tool_latencies:
                tool_latencies[s.tool] = []
            if s.latency_ms:
                tool_latencies[s.tool].append(s.latency_ms)

        tool_heatmap = {
            tool: {
                "count": len(lats),
                "total_ms": sum(lats),
                "avg_ms": sum(lats) / len(lats) if lats else 0,
            }
            for tool, lats in tool_latencies.items()
        }

        # failure clustering
        failures = [
            {
                "step_id": s.step_id,
                "name": s.step_name,
                "tool": s.tool,
                "error": s.error,
            }
            for s in dag.steps.values()
            if s.status == StepStatus.FAILED
        ]

        return {
            "dag_id": dag_id,
            "task_id": dag.task_id,
            "status": dag.status.value,
            "total_latency_ms": dag.total_latency_ms,
            "total_tokens": dag.total_tokens,
            "step_count": len(dag.steps),
            "top_latencies": step_latencies[:10],
            "tool_heatmap": tool_heatmap,
            "failures": failures,
            "epoch": dag.epoch,
        }

    # ── replay support ─────────────────────────────────────────────────────

    async def export_dag(self, dag_id: str) -> str | None:
        """Export DAG as JSON string for replay."""
        dag = await self.load(dag_id)
        if not dag:
            return None
        return json.dumps(dag.to_dict(), default=str)

    async def import_dag(self, dag_json: str) -> str | None:
        """Import DAG from JSON. Returns new dag_id."""
        dag = ExecutionDAG.from_dict(json.loads(dag_json))
        # assign new IDs to avoid collisions
        old_to_new: dict[str, str] = {}
        new_dag = ExecutionDAG(
            dag_id=str(uuid.uuid4()),
            task_id=dag.task_id + "_replay",
        )
        for old_id, step in dag.steps.items():
            new_id = str(uuid.uuid4())
            old_to_new[old_id] = new_id
            new_step = StepSpan(
                step_id=new_id,
                step_name=step.step_name,
                tool=step.tool,
                parent_id=old_to_new.get(step.parent_id) if step.parent_id else None,
                metadata=step.metadata,
            )
            new_dag.steps[new_id] = new_step

        # relink children
        for old_id, new_id in old_to_new.items():
            step = new_dag.steps[new_id]
            if step.parent_id:
                parent = new_dag.steps.get(step.parent_id)
                if parent and step.step_id not in parent.child_ids:
                    parent.child_ids.append(step.step_id)
            else:
                new_dag.root_ids.append(step.step_id)

        await self.save(new_dag)
        return new_dag.dag_id
