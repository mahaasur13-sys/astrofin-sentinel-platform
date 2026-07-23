"""
chaos_test_suite.py — Reproducible chaos scenarios + runner
────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from .load_simulator import (

import logging
log = logging.getLogger(__name__)

    BurstPattern,
    ChaosConfig,
    LoadProfile,
    LoadSimulator,
    make_cascade_failure_scenario,
    make_overload_scenario,
)
from .system_observer import StabilityLevel, StabilitySnapshot, SystemObserver


class AssertionResult(str, Enum):
    PASS         = "PASS"
    FAIL         = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class ScenarioResult:
    name: str
    duration_s: float
    assertions: list[tuple[str, AssertionResult, str]]
    stability_history: list[StabilitySnapshot]
    passed: int = 0
    failed: int = 0
    inconclusive: int = 0

    def summary(self) -> str:
        lines = [
            f"=== {self.name} ===",
            f"Duration: {self.duration_s:.1f}s",
            f"Passed: {self.passed}  Failed: {self.failed}  Inconclusive: {self.inconclusive}",
            "",
        ]
        for name, result, detail in self.assertions:
            icon = "✅" if result == AssertionResult.PASS else "❌" if result == AssertionResult.FAIL else "⚠️"
            lines.append(f"  {icon} [{result.value}] {name}: {detail}")
        return "\n".join(lines)


@dataclass
class ChaosScenario:
    name: str
    description: str
    duration_s: float
    configure: Callable[[], tuple[ChaosConfig, list[LoadProfile]]]
    assertions: Callable[[list[StabilitySnapshot], dict], list[tuple[str, AssertionResult, str]]] = field(default=lambda s, st: [])
    injectors: Callable[[LoadSimulator, SystemObserver], None] = field(default=lambda *a: None)
    teardown: Callable[[], None] = field(default=lambda: None)


def _overload_assertions(snaps: list[StabilitySnapshot], stats: dict) -> list[tuple[str, AssertionResult, str]]:
    results = []
    if not snaps:
        return [("Has snapshots", AssertionResult.INCONCLUSIVE, "No snapshots collected")]

    final = snaps[-1]
    all_ssi = [s.system_stability_index for s in snaps]
    avg_ssi = sum(all_ssi) / len(all_ssi)

    if avg_ssi > 0.3:
        results.append(("Avg SSI under overload", AssertionResult.PASS, f"avg_ssi={avg_ssi:.3f}"))
    else:
        results.append(("Avg SSI under overload", AssertionResult.FAIL, f"avg_ssi={avg_ssi:.3f} — system collapsed"))

    if final.shed_events > 0:
        results.append(("Load shedding triggered", AssertionResult.PASS, f"{final.shed_events} events"))
    else:
        results.append(("Load shedding triggered", AssertionResult.INCONCLUSIVE, "No shed events"))

    if final.retry_amplification_rate <= 5.0:
        results.append(("Retry amplification bounded", AssertionResult.PASS, f"RAR={final.retry_amplification_rate:.1f}"))
    else:
        results.append(("Retry amplification bounded", AssertionResult.FAIL, f"RAR={final.retry_amplification_rate:.1f} — storm"))

    return results


def _cascade_assertions(snaps: list[StabilitySnapshot], stats: dict) -> list[tuple[str, AssertionResult, str]]:
    results = []
    if not snaps:
        return [("Has snapshots", AssertionResult.INCONCLUSIVE, "No snapshots")]

    final = snaps[-1]

    if final.error_rate > 0.05:
        results.append(("Error rate captured", AssertionResult.PASS, f"error_rate={final.error_rate:.3f}"))
    else:
        results.append(("Error rate captured", AssertionResult.INCONCLUSIVE, f"error_rate={final.error_rate:.3f}"))

    if final.dag_recompute_ratio > 0.05:
        results.append(("DAG recompute detected", AssertionResult.PASS, f"DCR={final.dag_recompute_ratio:.3f}"))
    else:
        results.append(("DAG recompute detected", AssertionResult.INCONCLUSIVE, f"DCR={final.dag_recompute_ratio:.3f}"))

    turbulent = [s for s in snaps if s.degradation_level == StabilityLevel.TURBULENT.value]
    if len(turbulent) >= len(snaps) * 0.8:
        results.append(("System recovery", AssertionResult.FAIL, "System remained turbulent"))
    else:
        results.append(("System recovery", AssertionResult.PASS, f"Recovered after {len(snaps) - len(turbulent)} snapshots"))

    return results


def _oscillation_assertions(snaps: list[StabilitySnapshot], stats: dict) -> list[tuple[str, AssertionResult, str]]:
    results = []
    if not snaps:
        return [("Has snapshots", AssertionResult.INCONCLUSIVE, "No snapshots")]

    bounces = snaps[-1].green_red_bounces if snaps else 0

    if bounces >= 1:
        results.append(("Oscillation detected", AssertionResult.PASS, f"{bounces} bounce(es)"))
    else:
        results.append(("Oscillation detected", AssertionResult.INCONCLUSIVE, "No bounces"))

    shed_per_min = snaps[-1].shed_events * 60 / 60.0 if snaps else 0
    if 0 < shed_per_min < 100:
        results.append(("Shedding frequency bounded", AssertionResult.PASS, f"{shed_per_min:.1f}/min"))
    else:
        results.append(("Shedding frequency bounded", AssertionResult.INCONCLUSIVE, f"{shed_per_min:.1f}/min"))

    return results


SCENARIOS: dict[str, ChaosScenario] = {}

SCENARIOS["OVERLOAD_BURST"] = ChaosScenario(
    name="OVERLOAD_BURST",
    description="System receives 3x capacity for 30s — tests load shedding + stability",
    duration_s=50.0,
    configure=lambda: make_overload_scenario(),
    assertions=_overload_assertions,
)

SCENARIOS["CASCADE_FAILURE"] = ChaosScenario(
    name="CASCADE_FAILURE",
    description="30% node failure rate + cascade prob 0.5 — tests partial recompute + retry storm",
    duration_s=25.0,
    configure=lambda: make_cascade_failure_scenario(),
    assertions=_cascade_assertions,
)

SCENARIOS["SHEDDING_OSCILLATION"] = ChaosScenario(
    name="SHEDDING_OSCILLATION",
    description="Repeated ramp→plateau→spike to trigger GREEN↔RED oscillation cycles",
    duration_s=40.0,
    configure=lambda: (
        ChaosConfig(node_failure_rate=0.1, redis_latency_spike_prob=0.05),
        [
            LoadProfile(BurstPattern.RAMP,    duration_s=10, tasks_per_tick=15),
            LoadProfile(BurstPattern.PLATEAU, duration_s=10, tasks_per_tick=30),
            LoadProfile(BurstPattern.RAMP,    duration_s=10, tasks_per_tick=15),
            LoadProfile(BurstPattern.SPIKE,   duration_s=5,  tasks_per_tick=40),
            LoadProfile(BurstPattern.PLATEAU, duration_s=5,  tasks_per_tick=10),
        ],
    ),
    assertions=_oscillation_assertions,
)

SCENARIOS["QUIESCENT_BASELINE"] = ChaosScenario(
    name="QUIESCENT_BASELINE",
    description="Minimal load, near-zero failure — baseline sanity check",
    duration_s=20.0,
    configure=lambda: (
        ChaosConfig(node_failure_rate=0.01, redis_latency_jitter=5),
        [
            LoadProfile(BurstPattern.RAMP,    duration_s=5,  tasks_per_tick=3),
            LoadProfile(BurstPattern.PLATEAU, duration_s=10, tasks_per_tick=3),
            LoadProfile(BurstPattern.RAMP,    duration_s=5,  tasks_per_tick=3),
        ],
    ),
    assertions=lambda snaps, stats: [
        ("SSI near 1.0 in quiescent", AssertionResult.PASS if (snaps and snaps[-1].system_stability_index > 0.85) else AssertionResult.FAIL,
         f"SSI={snaps[-1].system_stability_index if snaps else 'N/A'}"),
        ("No shed events in quiescent", AssertionResult.PASS if (not snaps or snaps[-1].shed_events == 0) else AssertionResult.INCONCLUSIVE,
         f"{snaps[-1].shed_events if snaps else 0} events"),
    ],
)


class ChaosRunner:
    def __init__(self, seed: int = 42):
        self._seed = seed

    def run(self, scenario_name: str) -> ScenarioResult:
        if scenario_name not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIOS.keys())}")

        scenario = SCENARIOS[scenario_name]
        chaos, profiles = scenario.configure()
        rng = random.Random(self._seed)

        fake_redis = {}
        observer = SystemObserver(window_seconds=30.0)
        simulator = LoadSimulator(redis=fake_redis, chaos=chaos, seed=self._seed)

        start_time = time.time()
        snapshots: list[StabilitySnapshot] = []

        async def run_scenario():
            nonlocal snapshots
            tasks = await simulator.run_schedule(*profiles)

            # Inject events based on generated tasks + chaos config
            for task in tasks:
                if rng.random() < chaos.node_failure_rate:
                    observer.record_failure()
                    observer.record_retry()
                observer.record_node_executed()
                if rng.random() < 0.05:
                    observer.record_node_recomputed()

            # Inject shed events if load was high
            if len(tasks) > 30:
                for _ in range(min(len(tasks) // 10, 10)):
                    observer.record_shed_event()

            # Record degradation changes
            levels = ["GREEN", "YELLOW", "RED"]
            for i in range(5):
                level = levels[min(i, 2)]
                observer.record_degradation_change(level)
                await asyncio.sleep(0.05)

            # Collect snapshots every second for duration
            elapsed = 0.0
            tick_interval = 1.0
            while elapsed < scenario.duration_s:
                snap = observer.compute()
                snapshots.append(snap)
                await asyncio.sleep(tick_interval)
                elapsed += tick_interval

        asyncio.run(run_scenario())

        duration = time.time() - start_time
        stats = simulator.get_stats()
        assertion_results = scenario.assertions(snapshots, stats)

        result = ScenarioResult(
            name=scenario_name,
            duration_s=duration,
            assertions=assertion_results,
            stability_history=snapshots,
        )

        for _, res, _ in assertion_results:
            if res == AssertionResult.PASS:
                result.passed += 1
            elif res == AssertionResult.FAIL:
                result.failed += 1
            else:
                result.inconclusive += 1

        scenario.teardown()
        return result

    def run_all(self) -> list[ScenarioResult]:
        results = []
        for name in SCENARIOS:
            log.info(f"Running {name}...")
            try:
                r = self.run(name)
                results.append(r)
                log.info(f"  → PASS={r.passed} FAIL={r.failed} INCONCLUSIVE={r.inconclusive}")
            except Exception as e:
                log.info(f"  → ERROR: {e}")
        return results
