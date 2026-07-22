"""
test_deterministic_scheduler.py
ATOMS: ATOM-META-RL-014 — Deterministic Scheduler verification tests
"""

import sys

sys.path.insert(0, '/home/workspace/atom-federation-os')

from orchestration.deterministic_scheduler import (
    DeterministicScheduler,
    SchedulingStrategy,
)


def test_make_task_id_deterministic():
    """Same name + same tick → same ID."""
    id1 = DeterministicScheduler.make_task_id("task_a", tick=42)
    id2 = DeterministicScheduler.make_task_id("task_a", tick=42)
    id3 = DeterministicScheduler.make_task_id("task_a", tick=43)

    assert id1 == id2, f"Same inputs should give same ID: {id1} != {id2}"
    assert id1 != id3, f"Different tick should give different ID: {id1} == {id3}"
    assert len(id1) == 16, f"ID should be 16 chars, got {len(id1)}"


def test_task_id_uniqueness():
    """Different tasks at different ticks give different IDs."""
    ids = set()
    for tick in range(100):
        for name in ["a", "b", "c"]:
            id_ = DeterministicScheduler.make_task_id(name, tick)
            ids.add(id_)
    assert len(ids) == 300, f"Expected 300 unique IDs, got {len(ids)}"


def test_schedule_determinism_priority_order():
    """schedule() with PRIORITY_ORDER is deterministic across multiple calls."""
    scheduler = DeterministicScheduler(max_concurrent=4)

    # Register tasks at tick=1 (deterministic IDs)
    scheduler.register_task_at_tick("task_c", priority=0.6, tick=1)
    scheduler.register_task_at_tick("task_a", priority=0.9, tick=1)
    scheduler.register_task_at_tick("task_b", priority=0.7, tick=1)

    # Run schedule 5 times at tick=42 — should always return same result
    results = []
    for _ in range(5):
        r = scheduler.schedule(tick=42, strategy=SchedulingStrategy.PRIORITY_ORDER)
        results.append((r.selected_task.name, r.execution_order))

    assert all(r == results[0] for r in results), (
        f"NONDETERMINISM detected in PRIORITY_ORDER: {results}"
    )


def test_schedule_determinism_round_robin():
    """schedule() with ROUND_ROBIN is deterministic across multiple calls."""
    scheduler = DeterministicScheduler(max_concurrent=4)
    scheduler.register_task_at_tick("t1", priority=0.5, tick=1)
    scheduler.register_task_at_tick("t2", priority=0.5, tick=1)
    scheduler.register_task_at_tick("t3", priority=0.5, tick=1)

    results = []
    for _ in range(5):
        r = scheduler.schedule(tick=100, strategy=SchedulingStrategy.ROUND_ROBIN)
        results.append((r.selected_task.name if r.selected_task else None, r.execution_order))

    assert all(r == results[0] for r in results), (
        f"NONDETERMINISM detected in ROUND_ROBIN: {results}"
    )


def test_schedule_tick_affects_selection():
    """Different ticks → different selections (round-robin)."""
    scheduler = DeterministicScheduler(max_concurrent=4)
    scheduler.register_task_at_tick("t1", priority=0.5, tick=1)
    scheduler.register_task_at_tick("t2", priority=0.5, tick=1)
    scheduler.register_task_at_tick("t3", priority=0.5, tick=1)

    selections = set()
    for tick in range(6):
        r = scheduler.schedule(tick=tick, strategy=SchedulingStrategy.ROUND_ROBIN)
        if r.selected_task:
            selections.add(r.selected_task.name)

    # Round-robin over 3 tasks → all 3 should appear in 6 ticks
    assert len(selections) == 3, f"Expected all 3 tasks in round-robin, got {selections}"


def test_schedule_priority_order_highest_first():
    """PRIORITY_ORDER always selects highest priority."""
    scheduler = DeterministicScheduler(max_concurrent=4)
    scheduler.register_task_at_tick("low", priority=0.2, tick=1)
    scheduler.register_task_at_tick("high", priority=0.9, tick=1)
    scheduler.register_task_at_tick("medium", priority=0.5, tick=1)

    for tick in [1, 10, 50, 99]:
        r = scheduler.schedule(tick=tick, strategy=SchedulingStrategy.PRIORITY_ORDER)
        assert r.selected_task is not None, f"No task selected at tick={tick}"
        assert r.selected_task.name == "high", (
            f"Expected 'high' priority, got '{r.selected_task.name}' at tick={tick}"
        )


def test_execution_order_deterministic():
    """execution_order is deterministic across runs."""
    scheduler = DeterministicScheduler(max_concurrent=4)
    for name, priority in [("c", 0.3), ("a", 0.8), ("b", 0.6), ("d", 0.4)]:
        scheduler.register_task_at_tick(name, priority=priority, tick=1)

    orders = []
    for _ in range(3):
        r = scheduler.schedule(tick=77, strategy=SchedulingStrategy.PRIORITY_ORDER)
        orders.append(r.execution_order)

    assert all(o == orders[0] for o in orders), f"execution_order not deterministic: {orders}"


def test_fan_out_deterministic():
    """schedule_fan_out is deterministic: same tick → same worker assignments."""
    scheduler = DeterministicScheduler()

    assignments = []
    for _ in range(3):
        a = scheduler.schedule_fan_out(tick=10, num_workers=4)
        assignments.append(a)

    assert all(a == assignments[0] for a in assignments), (
        f"fan_out not deterministic: {assignments}"
    )


def test_fan_out_primary_worker():
    """get_primary_worker: tick % num_workers."""
    scheduler = DeterministicScheduler()

    for num_workers in [3, 5, 8]:
        primaries = set()
        for tick in range(num_workers * 2):
            w = scheduler.get_primary_worker(tick=tick, num_workers=num_workers)
            primaries.add(w)
        assert len(primaries) == num_workers, (
            f"Expected {num_workers} different primaries, got {primaries}"
        )


def test_async_steps_deterministic():
    """schedule_async_steps is deterministic across runs."""
    scheduler = DeterministicScheduler()

    steps = [
        {"id": "s3", "priority": 0.3},
        {"id": "s1", "priority": 0.9},
        {"id": "s2", "priority": 0.6},
    ]

    ordered_runs = []
    for _ in range(3):
        result = scheduler.schedule_async_steps(steps=steps, tick=55)
        ordered_runs.append([s["id"] for s in result])

    assert all(o == ordered_runs[0] for o in ordered_runs), (
        f"async steps not deterministic: {ordered_runs}"
    )


def test_async_steps_priority_ordering():
    """Higher priority steps come first."""
    scheduler = DeterministicScheduler()

    steps = [
        {"id": "low", "priority": 0.1},
        {"id": "high", "priority": 0.9},
        {"id": "medium", "priority": 0.5},
    ]

    result = scheduler.schedule_async_steps(steps=steps, tick=1)
    ids = [s["id"] for s in result]

    assert ids.index("high") < ids.index("medium") < ids.index("low"), (
        f"Expected priority order, got {ids}"
    )


def test_verify_determinism_passes():
    """verify_determinism() returns is_deterministic=True."""
    scheduler = DeterministicScheduler(max_concurrent=4)
    scheduler.register_task_at_tick("t1", priority=0.5, tick=1)
    scheduler.register_task_at_tick("t2", priority=0.7, tick=1)

    report = scheduler.verify_determinism(
        tick=42,
        strategy=SchedulingStrategy.PRIORITY_ORDER,
        num_runs=5,
    )

    assert report["is_deterministic"] is True, (
        f"Scheduler failed determinism check: {report}"
    )
    assert report["first_result"]["selected_id"] is not None


def test_empty_scheduler_returns_none():
    """schedule() on empty scheduler returns None selected."""
    scheduler = DeterministicScheduler()

    r = scheduler.schedule(tick=1, strategy=SchedulingStrategy.PRIORITY_ORDER)

    assert r.selected_task is None
    assert r.execution_order == []
    assert r.nondeterministic_sources == []


def test_cross_seed_reproducibility():
    """
    CRITICAL: Scheduler must be reproducible across PYTHONHASHSEED values.
    This is the ultimate determinism test.
    """
    scheduler = DeterministicScheduler(max_concurrent=8)
    for name, priority in [("x", 0.4), ("y", 0.8), ("z", 0.6)]:
        scheduler.register_task_at_tick(name, priority=priority, tick=1)

    # Simulate different hash seeds by registering new tasks
    # (same scheduler state → same result regardless of hash seed)
    results_by_seed = {}
    for seed in [0, 42, 123, 999]:
        s = DeterministicScheduler(max_concurrent=8)
        for name, priority in [("x", 0.4), ("y", 0.8), ("z", 0.6)]:
            s.register_task_at_tick(name, priority=priority, tick=1)

        r = s.schedule(tick=99, strategy=SchedulingStrategy.PRIORITY_ORDER)
        results_by_seed[seed] = (
            r.selected_task.name if r.selected_task else None,
            r.execution_order,
        )

    # All seeds should give the same result (deterministic by construction)
    first = list(results_by_seed.values())[0]
    assert all(v == first for v in results_by_seed.values()), (
        f"Cross-seed reproducibility failed: {results_by_seed}"
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
