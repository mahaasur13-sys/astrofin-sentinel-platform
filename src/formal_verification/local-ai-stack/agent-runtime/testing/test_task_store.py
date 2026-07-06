"""
Tests for TaskStore — единый source of truth.

Covers:
- claim_task: only PENDING tasks
- complete_task: only owner + RUNNING
- fail_task: attempts check, retry vs FAILED
- retry_task: new epoch, worker_id reset
- cancel_task: owner check
- recover_stale_tasks: stale RUNNING → recovered
- concurrent claim: only one winner
- epoch increments on retry
"""

import asyncio
import time

import pytest
from agent_runtime.task_store import (
    STATE_PREFIX,
    TaskState,
    TaskStore,
    _state_key,
)


@pytest.fixture
async def store():
    """Fresh store pointing to test DB."""
    s = TaskStore("redis://localhost:6379")
    r = await s._redis()
    # flush test keys
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match=f"{STATE_PREFIX}*", count=200)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break
    yield s
    # cleanup
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match=f"{STATE_PREFIX}*", count=200)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break
    await r.aclose()


# ── basic lifecycle ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task(store):
    rec = await store.create_task("t1", {"task": "hello"}, max_attempts=3)
    assert rec.state == TaskState.PENDING
    assert rec.task_id == "t1"
    assert rec.worker_id == ""
    assert rec.epoch == 0
    assert rec.attempt == 0
    assert rec.max_attempts == 3


@pytest.mark.asyncio
async def test_create_task_idempotent(store):
    await store.create_task("t1", {"task": "a"})
    rec2 = await store.create_task("t1", {"task": "b"})
    assert rec2.state == TaskState.PENDING  # original state preserved
    result = await store.get_result("t1")
    assert result is None  # no result yet


@pytest.mark.asyncio
async def test_claim_task_success(store):
    await store.create_task("t1", {"task": "hello"})
    rec = await store.claim_task("t1", "worker_A")
    assert rec is not None
    assert rec.state == TaskState.RUNNING
    assert rec.worker_id == "worker_A"
    assert rec.epoch == 1  # epoch incremented on claim
    assert rec.attempt == 0


@pytest.mark.asyncio
async def test_claim_task_not_pending(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    rec2 = await store.claim_task("t1", "worker_B")
    assert rec2 is None  # already RUNNING


@pytest.mark.asyncio
async def test_claim_task_not_found(store):
    rec = await store.claim_task("nonexistent", "worker_A")
    assert rec is None


@pytest.mark.asyncio
async def test_complete_task_success(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    ok = await store.complete_task("t1", "worker_A", {"result": "done"})
    assert ok is True
    rec = await store.get_task("t1")
    assert rec.state == TaskState.DONE
    result = await store.get_result("t1")
    assert result == {"result": "done"}


@pytest.mark.asyncio
async def test_complete_task_wrong_worker(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    ok = await store.complete_task("t1", "worker_B", {"result": "x"})
    assert ok is False
    rec = await store.get_task("t1")
    assert rec.state == TaskState.RUNNING  # unchanged


@pytest.mark.asyncio
async def test_complete_task_not_running(store):
    await store.create_task("t1", {"task": "hello"})
    ok = await store.complete_task("t1", "worker_A", {"result": "x"})
    assert ok is False


# ── fail + retry ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fail_triggers_retry(store):
    await store.create_task("t1", {"task": "hello"}, max_attempts=3)
    await store.claim_task("t1", "worker_A")
    ok = await store.fail_task("t1", "worker_A", "transient error")
    assert ok is True
    rec = await store.get_task("t1")
    assert rec.state == TaskState.PENDING  # retry
    assert rec.attempt == 1
    assert rec.worker_id == ""  # reset for next claim


@pytest.mark.asyncio
async def test_fail_exhausted_max_attempts(store):
    await store.create_task("t1", {"task": "hello"}, max_attempts=2)
    await store.claim_task("t1", "worker_A")
    await store.fail_task("t1", "worker_A", "error 1")
    # now PENDING, claim again
    await store.claim_task("t1", "worker_B")
    await store.fail_task("t1", "worker_B", "error 2")
    rec = await store.get_task("t1")
    assert rec.state == TaskState.FAILED
    assert rec.error == "error 2"


@pytest.mark.asyncio
async def test_epoch_increments_on_retry(store):
    await store.create_task("t1", {"task": "hello"}, max_attempts=3)
    await store.claim_task("t1", "worker_A")
    epoch_before = (await store.get_task("t1")).epoch
    await store.fail_task("t1", "worker_A", "err")
    epoch_after = (await store.get_task("t1")).epoch
    assert epoch_after == epoch_before + 1


@pytest.mark.asyncio
async def test_retry_task(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    ok = await store.retry_task("t1", "worker_A")
    assert ok is True
    rec = await store.get_task("t1")
    assert rec.state == TaskState.PENDING
    assert rec.epoch > 1
    assert rec.worker_id == ""


@pytest.mark.asyncio
async def test_retry_task_wrong_worker(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    ok = await store.retry_task("t1", "worker_B")
    assert ok is False


# ── cancel ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cancel_running_task(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    ok = await store.cancel_task("t1", "worker_A")
    assert ok is True
    rec = await store.get_task("t1")
    assert rec.state == TaskState.CANCELLED


@pytest.mark.asyncio
async def test_cancel_pending_task(store):
    await store.create_task("t1", {"task": "hello"})
    ok = await store.cancel_task("t1", "worker_A")
    assert ok is True
    rec = await store.get_task("t1")
    assert rec.state == TaskState.CANCELLED


@pytest.mark.asyncio
async def test_cancel_done_fails(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    await store.complete_task("t1", "worker_A", {"result": "x"})
    ok = await store.cancel_task("t1", "worker_A")
    assert ok is False


# ── stale recovery ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recover_stale_tasks(store):
    await store.create_task("t1", {"task": "hello"})
    await store.claim_task("t1", "worker_A")
    # simulate stale by directly setting started_at to far past
    r = await store._redis()
    await r.hset(_state_key("t1"), "started_at", str(time.time() - 1000))
    recovered = await store.recover_stale_tasks("worker_B", stale_timeout=300)
    assert recovered == 1
    rec = await store.get_task("t1")
    assert rec.state == TaskState.RUNNING
    assert rec.worker_id == "worker_B"
    assert rec.epoch == 2  # incremented on reclaim


# ── concurrent claim ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_concurrent_claim_only_one_wins(store):
    await store.create_task("t1", {"task": "hello"})

    async def claim(name):
        return await store.claim_task("t1", name)

    results = await asyncio.gather(
        claim("worker_A"),
        claim("worker_B"),
        claim("worker_C"),
    )
    winners = [r for r in results if r is not None]
    assert len(winners) == 1
    assert winners[0].worker_id in ("worker_A", "worker_B", "worker_C")


# ── get_all_by_state ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_all_by_state(store):
    for i in range(5):
        await store.create_task(f"t{i}", {"n": i})
    await store.claim_task("t0", "w")
    await store.claim_task("t1", "w")
    pending = await store.get_all_by_state(TaskState.PENDING)
    assert len(pending) == 3
    running = await store.get_all_by_state(TaskState.RUNNING)
    assert len(running) == 2


# ── critical edge-case tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_zombie_worker_recovery(store):
    """
    Zombie worker A (epoch=1) is stuck. Worker B recovers the task (epoch=2),
    completes it. A wakes up → complete_task must be rejected (epoch mismatch).
    """
    await store.create_task("t1", {"task": "hello"}, max_attempts=2)

    # Worker A claims — epoch=1
    rec_a = await store.claim_task("t1", "worker_A")
    assert rec_a is not None
    assert rec_a.epoch == 1
    assert rec_a.state == TaskState.RUNNING

    # Simulate hang: fail_task exhausts attempts → worker_A's epoch now locked in at 1
    # But fail triggers retry and increments to epoch=2
    ok_fail = await store.fail_task("t1", "worker_A", "transient")
    assert ok_fail is True

    # Now PENDING with epoch=2, worker_id=""
    rec_after_fail = await store.get_task("t1")
    assert rec_after_fail.state == TaskState.PENDING
    assert rec_after_fail.epoch == 2

    # Worker B claims — epoch=2 (new attempt)
    rec_b = await store.claim_task("t1", "worker_B")
    assert rec_b is not None
    assert rec_b.epoch == 2
    assert rec_b.worker_id == "worker_B"

    # Worker B completes
    ok_complete = await store.complete_task("t1", "worker_B", {"result": "done"})
    assert ok_complete is True
    assert (await store.get_task("t1")).state == TaskState.DONE

    # Worker A wakes up, tries to complete its stale epoch=1 → must reject
    ok_stale = await store.complete_task("t1", "worker_A", {"result": "stale"})
    assert ok_stale is False  # epoch mismatch, wrong worker_id
    assert (await store.get_task("t1")).state == TaskState.DONE  # still DONE


@pytest.mark.asyncio
async def test_double_claim_storm(store):
    """
    10 workers racing to claim the same PENDING task.
    Exactly 1 must win — all others must get None.
    """
    await store.create_task("t1", {"task": "storm"})

    async def try_claim(worker_name: str):
        return await store.claim_task("t1", worker_name)

    results = await asyncio.gather(
        try_claim("w0"), try_claim("w1"), try_claim("w2"),
        try_claim("w3"), try_claim("w4"), try_claim("w5"),
        try_claim("w6"), try_claim("w7"), try_claim("w8"),
        try_claim("w9"),
    )

    winners = [r for r in results if r is not None]
    losers = [r for r in results if r is None]
    assert len(winners) == 1, f"Expected 1 winner, got {len(winners)}"
    assert len(losers) == 9, f"Expected 9 losers, got {len(losers)}"
    assert winners[0].state == TaskState.RUNNING


@pytest.mark.asyncio
async def test_pel_recovery_with_epoch_change(store):
    """
    PEL message for epoch=1 arrives after epoch has already changed to 2.
    complete_task must reject the stale write.
    """
    await store.create_task("t1", {"task": "pel_test"}, max_attempts=3)

    # Worker A claims at epoch=1
    rec_a = await store.claim_task("t1", "worker_A")
    assert rec_a.epoch == 1

    # Worker A fails → retry → epoch=2, PENDING
    await store.fail_task("t1", "worker_A", "error")
    rec_after_fail = await store.get_task("t1")
    assert rec_after_fail.epoch == 2
    assert rec_after_fail.state == TaskState.PENDING

    # Worker B claims at epoch=2
    rec_b = await store.claim_task("t1", "worker_B")
    assert rec_b.epoch == 2
    assert rec_b.worker_id == "worker_B"

    # Now Worker A's old PEL message arrives and tries to complete(epoch=1)
    # This should fail because worker_id="worker_A" !== current owner=""
    # Actually since state is RUNNING, it checks: current_worker (worker_B) != worker_A → 0
    ok_stale = await store.complete_task("t1", "worker_A", {"result": "stale"})
    assert ok_stale is False

    # Task remains RUNNING with worker_B
    final = await store.get_task("t1")
    assert final.state == TaskState.RUNNING
    assert final.worker_id == "worker_B"


@pytest.mark.asyncio
async def test_idempotency_key_format(store):
    """Idempotency key follows expected format: idem:{task_id}:{epoch}:{step_id}"""
    key = TaskStore.make_idempotency_key("task_abc", 7, "step_x")
    assert key == "idem:task_abc:7:step_x"


@pytest.mark.asyncio
async def test_check_and_set_idempotency_first_call(store):
    """First call returns True (key set), second call returns False (already exists)"""
    task_id = "idem_test"
    epoch = 1
    step_id = "step_1"

    # First execution
    ok1 = await store.check_and_set_idempotency(task_id, epoch, step_id)
    assert ok1 is True

    # Duplicate execution
    ok2 = await store.check_and_set_idempotency(task_id, epoch, step_id)
    assert ok2 is False

    # Different step_id is fine
    ok3 = await store.check_and_set_idempotency(task_id, epoch, "step_2")
    assert ok3 is True

    # Different epoch is fine
    ok4 = await store.check_and_set_idempotency(task_id, epoch + 1, step_id)
    assert ok4 is True
