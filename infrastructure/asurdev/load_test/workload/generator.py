#!/usr/bin/env python3
"""
Workload Generator — generates job streams from profiles.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import random
import math
from .types import WorkloadProfile, WorkloadProfile as WProfile


@dataclass
class Job:
    """Single synthetic job."""
    job_id: str
    submitted_at: datetime
    runtime_sec: float
    gpu_required: bool
    priority: int
    adversarial: bool
    target_node: Optional[str] = None
    failure_injected: bool = False


@dataclass
class WorkloadStream:
    """Generated job stream for one injection cycle."""
    scenario_name: str
    jobs: list[Job] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    total_burst_events: int = 0
    total_adversarial: int = 0
    total_failure_injected: int = 0


class WorkloadGenerator:
    """
    Generates realistic job streams from WorkloadProfile.
    Supports burst, adversarial, and skewed patterns.
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def generate(
        self,
        profile: WorkloadProfile,
        duration_sec: int,
        target_nodes: list[str],
        scenario_name: str = "unnamed",
        start_time: Optional[datetime] = None,
    ) -> WorkloadStream:
        """Generate full job stream for given profile and duration."""
        rng = self._rng
        stream = WorkloadStream(scenario_name=scenario_name)
        t = start_time or datetime.utcnow()
        end_time = t + timedelta(seconds=duration_sec)

        # Poisson arrival process
        jobs_per_second = profile.jobs_per_minute / 60.0

        current_time = t
        job_counter = 0

        while current_time < end_time:
            # Inter-arrival time (exponential / Poisson)
            inter_arrival = rng.expovariate(jobs_per_second)
            current_time += timedelta(seconds=inter_arrival)
            if current_time >= end_time:
                break

            # Burst multiplier
            in_burst = rng.random() < profile.burst_probability
            multiplier = profile.burst_multiplier if in_burst else 1.0
            if in_burst:
                stream.total_burst_events += 1

            # Runtime (log-normal for heavy tail)
            runtime = rng.lognormvariate(
                mean=math.log(profile.avg_runtime_sec),
                sigma=0.5,
            )

            # GPU requirement
            gpu_required = rng.random() < profile.gpu_fraction

            # Adversarial flag
            adversarial = rng.random() < profile.adversarial_probability
            if adversarial:
                stream.total_adversarial += 1

            # Failure injection
            failure_injected = rng.random() < profile.failure_injection_rate
            if failure_injected:
                stream.total_failure_injected += 1

            # Target node (skewed or uniform)
            if target_nodes and profile.skew_factor > 0:
                if rng.random() < profile.skew_factor:
                    # All skew hits first node (worst-case hotspot)
                    target = target_nodes[0]
                else:
                    target = rng.choice(target_nodes)
            elif target_nodes:
                target = rng.choice(target_nodes)
            else:
                target = None

            job_counter += 1
            job = Job(
                job_id=f"{scenario_name}-{job_counter:06d}",
                submitted_at=current_time,
                runtime_sec=min(runtime * multiplier, 600.0),  # cap at 10min
                gpu_required=gpu_required,
                priority=rng.randint(1, 10),
                adversarial=adversarial,
                target_node=target,
                failure_injected=failure_injected,
            )
            stream.jobs.append(job)

        return stream

    def generate_scenario(self, scenario_name: str, duration_sec: int,
                          target_nodes: list[str]) -> WorkloadStream:
        """Convenience: generate from predefined SCENARIOS."""
        from .types import SCENARIOS
        if scenario_name not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        scenario = SCENARIOS[scenario_name]
        return self.generate(
            profile=scenario.profile,
            duration_sec=duration_sec,
            target_nodes=target_nodes,
            scenario_name=scenario_name,
        )
