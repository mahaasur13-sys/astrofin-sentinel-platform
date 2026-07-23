"""
load_simulator.py — Synthetic workload + chaos injection harness
─────────────────────────────────────────────────────────────────
Generates realistic DAG workloads with controlled:
  - burst patterns (ramp, spike, plateau, sawtooth, silence)
  - node failure injection (random, cascading, stuck-in-progress)
  - Redis latency jitter (spike, drift, salt)
  - Ollama slowdown simulation (token throttle, hang)
"""

from __future__ import annotations

import asyncio
import math
import random
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ──────────────────────────────────────────────────────────────
# Enums & Dataclasses
# ──────────────────────────────────────────────────────────────

class BurstPattern(str, Enum):
    RAMP     = "ramp"
    SPIKE    = "spike"
    PLATEAU  = "plateau"
    SAWTOOTH = "sawtooth"
    SILENCE  = "silence"


@dataclass
class ChaosConfig:
    node_failure_rate: float = 0.05
    cascade_failure_prob: float = 0.25
    stuck_in_progress_prob: float = 0.02

    redis_latency_jitter: int = 50
    redis_latency_spike_prob: float = 0.01
    redis_latency_spike_duration: float = 2.0

    ollama_slowdown_prob: float = 0.05
    ollama_slowdown_factor: float = 5.0
    ollama_hang_prob: float = 0.01

    tick_interval: float = 0.5


@dataclass
class LoadProfile:
    pattern: BurstPattern = BurstPattern.RAMP
    duration_s: float = 10.0
    tasks_per_tick: int = 5
    dag_depth_min: int = 2
    dag_depth_max: int = 5
    dag_width_min: int = 1
    dag_width_max: int = 4
    node_exec_time_min: float = 0.1
    node_exec_time_max: float = 1.5
    priority_weights: tuple[float, float, float, float] = (0.4, 0.3, 0.2, 0.1)


@dataclass
class SyntheticTask:
    task_id: str
    priority: int
    dag_spec: dict
    fail_nodes: set[str] = field(default_factory=set)
    hang_nodes: set[str] = field(default_factory=set)
    slowdown_factor: float = 1.0
    created_at: float = field(default_factory=time.time)


# ──────────────────────────────────────────────────────────────
# DAG Generator
# ──────────────────────────────────────────────────────────────

def generate_synthetic_dag(
    rng: random.Random,
    task_id: str,
    depth: int,
    width: int,
    exec_time_min: float = 0.1,
    exec_time_max: float = 1.5,
) -> tuple[list[dict], set[str], set[str]]:
    nodes = []
    node_ids = []

    root_id = f"{task_id}_n0"
    nodes.append({"id": root_id, "deps": [], "exec_time": rng.uniform(exec_time_min, exec_time_max)})
    node_ids.append(root_id)

    for d in range(1, depth):
        prev_ids = node_ids[-width:] if d > 1 else [root_id]
        for w in range(width):
            nid = f"{task_id}_n{d}_{w}"
            parent = rng.choice(prev_ids)
            if rng.random() < 0.3 and len(prev_ids) > 1:
                p2 = rng.choice([p for p in prev_ids if p != parent])
                deps = [parent, p2]
            else:
                deps = [parent]
            nodes.append({
                "id": nid,
                "deps": deps,
                "exec_time": rng.uniform(exec_time_min, exec_time_max),
            })
            node_ids.append(nid)

    fail_nodes: set[str] = set()
    hang_nodes: set[str] = set()

    for n in nodes:
        if n["id"] != root_id:
            if rng.random() < 0.08:
                fail_nodes.add(n["id"])
            if rng.random() < 0.02:
                hang_nodes.add(n["id"])

    return nodes, fail_nodes, hang_nodes


# ──────────────────────────────────────────────────────────────
# Redis Latency Injector
# ──────────────────────────────────────────────────────────────

class RedisLatencyInjector:
    def __init__(self, config: ChaosConfig):
        self._cfg = config
        self._spike_active = False
        self._spike_until = 0.0
        self._lock = threading.Lock()

    def _jitter(self) -> float:
        if self._cfg.redis_latency_jitter <= 0:
            return 0.0
        with self._lock:
            if self._spike_active or random.random() < self._cfg.redis_latency_spike_prob:
                self._spike_active = True
                self._spike_until = time.time() + self._cfg.redis_latency_spike_duration
                return 0.5
        base = random.uniform(
            -self._cfg.redis_latency_jitter, self._cfg.redis_latency_jitter
        ) / 1000.0
        return max(0.0, base)

    async def patch_redis(self, redis_client) -> None:
        original_execute = redis_client.execute

        async def _exec_with_jitter(*args, **kwargs):
            delay = self._jitter()
            if delay > 0:
                await asyncio.sleep(delay)
            return await original_execute(*args, **kwargs)

        redis_client.execute = _exec_with_jitter

    def trigger_spike(self, duration_s: float = 2.0) -> None:
        with self._lock:
            self._spike_active = True
            self._spike_until = time.time() + duration_s


# ──────────────────────────────────────────────────────────────
# Ollama Slowdown Simulator
# ──────────────────────────────────────────────────────────────

class OllamaSimulator:
    def __init__(self, config: ChaosConfig):
        self._cfg = config

    async def call_with_chaos(
        self,
        real_call: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:
        hang = random.random() < self._cfg.ollama_hang_prob
        slowdown = random.random() < self._cfg.ollama_slowdown_prob

        if hang:
            await asyncio.sleep(999999)
            return None

        if slowdown:
            await asyncio.sleep(30)
            return None

        return await real_call(*args, **kwargs)


# ──────────────────────────────────────────────────────────────
# Load Simulator Orchestrator
# ──────────────────────────────────────────────────────────────

class LoadSimulator:
    def __init__(
        self,
        redis: Any,
        chaos: ChaosConfig | None = None,
        seed: int = 42,
    ):
        self._redis = redis
        self._chaos = chaos or ChaosConfig()
        self._seed = seed
        self._rng = random.Random(seed)
        self._running = False
        self._tasks_generated = 0
        self._lock = asyncio.Lock()

        self.latency_injector = RedisLatencyInjector(self._chaos)
        self.ollama_sim = OllamaSimulator(self._chaos)

        self._burst_queue: asyncio.Queue[SyntheticTask] = asyncio.Queue()
        self.stats = {
            "tasks_generated": 0,
            "tasks_by_priority": {0: 0, 1: 0, 2: 0, 3: 0},
            "fail_nodes_injected": 0,
            "hang_nodes_injected": 0,
            "latency_spikes_triggered": 0,
            "ollama_slowdowns_injected": 0,
            "ollama_hangs_injected": 0,
        }

    @property
    def chaos(self) -> ChaosConfig:
        return self._chaos

    def generate_task(self, profile: LoadProfile) -> SyntheticTask:
        self._rng.seed(self._seed + self._tasks_generated)

        depth = self._rng.randint(profile.dag_depth_min, profile.dag_depth_max)
        width = self._rng.randint(profile.dag_width_min, profile.dag_width_max)
        task_id = f"syn_{uuid.uuid4().hex[:8]}"

        nodes, fail_nodes, hang_nodes = generate_synthetic_dag(
            rng=self._rng,
            task_id=task_id,
            depth=depth,
            width=width,
            exec_time_min=profile.node_exec_time_min,
            exec_time_max=profile.node_exec_time_max,
        )

        priority = self._rng.choices(
            [0, 1, 2, 3], weights=profile.priority_weights, k=1,
        )[0]

        if self._rng.random() < self._chaos.node_failure_rate:
            if len(nodes) > 1:
                victim = self._rng.choice(nodes[1:])["id"]
                fail_nodes.add(victim)
                self.stats["fail_nodes_injected"] += 1

        if self._rng.random() < self._chaos.stuck_in_progress_prob:
            if len(nodes) > 1:
                victim = self._rng.choice(nodes[1:])["id"]
                hang_nodes.add(victim)
                self.stats["hang_nodes_injected"] += 1

        if self._rng.random() < self._chaos.ollama_slowdown_prob:
            self.stats["ollama_slowdowns_injected"] += 1

        dag_spec = {
            "task_id": task_id,
            "nodes": nodes,
            "metadata": {"profile": profile.pattern.value},
        }

        task = SyntheticTask(
            task_id=task_id,
            priority=priority,
            dag_spec=dag_spec,
            fail_nodes=fail_nodes,
            hang_nodes=hang_nodes,
            slowdown_factor=1.0,
        )

        self._tasks_generated += 1
        self.stats["tasks_generated"] = self._tasks_generated
        self.stats["tasks_by_priority"][priority] += 1
        return task

    async def run_schedule(self, *profiles: LoadProfile) -> list[SyntheticTask]:
        self._running = True
        all_tasks: list[SyntheticTask] = []
        for profile in profiles:
            if not self._running:
                break
            tasks = await self._run_profile(profile)
            all_tasks.extend(tasks)
        return all_tasks

    async def _run_profile(self, profile: LoadProfile) -> list[SyntheticTask]:
        tasks: list[SyntheticTask] = []
        ticks = int(profile.duration_s / self._chaos.tick_interval)

        for tick in range(ticks):
            if not self._running:
                break
            count = self._tasks_per_tick_for_tick(profile, tick, ticks)
            for _ in range(count):
                task = self.generate_task(profile)
                await self._burst_queue.put(task)
                tasks.append(task)
            await asyncio.sleep(self._chaos.tick_interval)

        return tasks

    def _tasks_per_tick_for_tick(
        self, profile: LoadProfile, tick: int, total_ticks: int,
    ) -> int:
        progress = tick / total_ticks
        p = profile.pattern

        if p == BurstPattern.RAMP:
            peak, sigma = 0.4, 0.2
            weight = math.exp(-0.5 * ((progress - peak) / sigma) ** 2)
            return max(1, int(profile.tasks_per_tick * weight * 1.5))
        elif p == BurstPattern.SPIKE:
            if progress < 0.1:
                return int(profile.tasks_per_tick * 3)
            return max(1, int(profile.tasks_per_tick * 0.3 ** (progress * 5)))
        elif p == BurstPattern.PLATEAU:
            return profile.tasks_per_tick
        elif p == BurstPattern.SAWTOOTH:
            cycle = 5
            local_progress = tick % cycle / cycle
            return max(1, int(profile.tasks_per_tick * local_progress * 3))
        else:
            return 0

    async def get_task(self, timeout: float = 1.0) -> SyntheticTask | None:
        try:
            return await asyncio.wait_for(self._burst_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def stop(self):
        self._running = False

    def get_stats(self) -> dict:
        return {
            **self.stats,
            "queue_depth": self._burst_queue.qsize(),
        }


# ──────────────────────────────────────────────────────────────
# Preset scenarios
# ──────────────────────────────────────────────────────────────

def make_overload_scenario() -> tuple[list[LoadProfile], ChaosConfig]:
    chaos = ChaosConfig(
        node_failure_rate=0.1,
        redis_latency_jitter=30,
        redis_latency_spike_prob=0.05,
        ollama_slowdown_prob=0.1,
        stuck_in_progress_prob=0.03,
    )
    profiles = [
        LoadProfile(BurstPattern.RAMP,    duration_s=10, tasks_per_tick=20),
        LoadProfile(BurstPattern.PLATEAU, duration_s=30, tasks_per_tick=50),
        LoadProfile(BurstPattern.RAMP,    duration_s=10, tasks_per_tick=20),
        LoadProfile(BurstPattern.SILENCE, duration_s=10, tasks_per_tick=0),
    ]
    return profiles, chaos


def make_cascade_failure_scenario() -> tuple[list[LoadProfile], ChaosConfig]:
    chaos = ChaosConfig(
        node_failure_rate=0.3,
        cascade_failure_prob=0.5,
        redis_latency_spike_prob=0.1,
        ollama_hang_prob=0.05,
        stuck_in_progress_prob=0.05,
    )
    profiles = [
        LoadProfile(BurstPattern.SPIKE, duration_s=5, tasks_per_tick=10),
        LoadProfile(BurstPattern.PLATEAU, duration_s=15, tasks_per_tick=30),
        LoadProfile(BurstPattern.SPIKE, duration_s=5, tasks_per_tick=10),
    ]
    return profiles, chaos


def make_quiescent_scenario() -> tuple[list[LoadProfile], ChaosConfig]:
    chaos = ChaosConfig(
        node_failure_rate=0.01,
        redis_latency_jitter=5,
    )
    profiles = [
        LoadProfile(BurstPattern.RAMP,   duration_s=5, tasks_per_tick=5),
        LoadProfile(BurstPattern.PLATEAU, duration_s=10, tasks_per_tick=5),
        LoadProfile(BurstPattern.RAMP,   duration_s=5, tasks_per_tick=5),
    ]
    return profiles, chaos
