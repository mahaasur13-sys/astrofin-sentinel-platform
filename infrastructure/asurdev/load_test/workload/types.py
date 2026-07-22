#!/usr/bin/env python3
"""
Workload Types — parameterizable load profiles.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
import random


@dataclass
class WorkloadProfile:
    """Single workload specification."""
    name: str
    jobs_per_minute: float          # arrival rate lambda
    avg_runtime_sec: float           # job duration
    gpu_fraction: float             # 0..1 — fraction requiring GPU
    burst_probability: float         # P(burst arrival)
    burst_multiplier: float          # load multiplier during burst
    adversarial_probability: float   # P(adversarial pattern)
    failure_injection_rate: float    # P(job failure)
    skew_factor: float               # 0=uniform, 1=hotspot


@dataclass
class StressScenario:
    """Named stress scenario = profile + duration + targets."""
    name: str
    profile: WorkloadProfile
    duration_sec: int
    target_nodes: list[str] = field(default_factory=list)
    injected_failures: list[str] = field(default_factory=list)
    seed: int = 42


# =============================================================================
# Predefined Profiles
# =============================================================================

def burst_load() -> WorkloadProfile:
    """Sudden spike: 10x baseline, short duration."""
    return WorkloadProfile(
        name="burst",
        jobs_per_minute=120.0,
        avg_runtime_sec=45.0,
        gpu_fraction=0.4,
        burst_probability=0.7,
        burst_multiplier=10.0,
        adversarial_probability=0.1,
        failure_injection_rate=0.05,
        skew_factor=0.3,
    )


def sustained_overload() -> WorkloadProfile:
    """Continuous 3x baseline load."""
    return WorkloadProfile(
        name="sustained_overload",
        jobs_per_minute=60.0,
        avg_runtime_sec=90.0,
        gpu_fraction=0.6,
        burst_probability=0.1,
        burst_multiplier=3.0,
        adversarial_probability=0.2,
        failure_injection_rate=0.08,
        skew_factor=0.5,
    )


def adversarial_scheduling() -> WorkloadProfile:
    """Hostile patterns designed to expose scheduling weaknesses."""
    return WorkloadProfile(
        name="adversarial",
        jobs_per_minute=40.0,
        avg_runtime_sec=120.0,
        gpu_fraction=0.9,
        burst_probability=0.3,
        burst_multiplier=5.0,
        adversarial_probability=0.8,
        failure_injection_rate=0.20,
        skew_factor=0.9,
    )


def skewed_hotspot() -> WorkloadProfile:
    """All jobs target single node to create artificial hotspot."""
    return WorkloadProfile(
        name="skewed_hotspot",
        jobs_per_minute=30.0,
        avg_runtime_sec=60.0,
        gpu_fraction=0.5,
        burst_probability=0.0,
        burst_multiplier=1.0,
        adversarial_probability=0.0,
        failure_injection_rate=0.02,
        skew_factor=0.95,
    )


def cascading_failure() -> WorkloadProfile:
    """Frequent failure injection to test rollback and recovery."""
    return WorkloadProfile(
        name="cascading_failure",
        jobs_per_minute=20.0,
        avg_runtime_sec=30.0,
        gpu_fraction=0.3,
        burst_probability=0.2,
        burst_multiplier=2.0,
        adversarial_probability=0.3,
        failure_injection_rate=0.40,
        skew_factor=0.4,
    )


def normal_baseline() -> WorkloadProfile:
    """Typical production load."""
    return WorkloadProfile(
        name="baseline",
        jobs_per_minute=12.0,
        avg_runtime_sec=60.0,
        gpu_fraction=0.25,
        burst_probability=0.05,
        burst_multiplier=2.0,
        adversarial_probability=0.0,
        failure_injection_rate=0.01,
        skew_factor=0.1,
    )


SCENARIOS: dict[str, StressScenario] = {
    "burst": StressScenario(name="burst", profile=burst_load(), duration_sec=300),
    "sustained": StressScenario(name="sustained", profile=sustained_overload(), duration_sec=1800),
    "adversarial": StressScenario(name="adversarial", profile=adversarial_scheduling(), duration_sec=600),
    "hotspot": StressScenario(name="hotspot", profile=skewed_hotspot(), duration_sec=300),
    "failure": StressScenario(name="failure", profile=cascading_failure(), duration_sec=300),
    "baseline": StressScenario(name="baseline", profile=normal_baseline(), duration_sec=600),
}
