# test_execution_context_isolation.py — per-caller isolation of EnhancedExecutionContext
#
# Pins the contract that mutation_context()/internal_context() keep their state
# on the CALLER (thread / asyncio task), not on the singleton:
#   - nesting restores the outer state
#   - an exception in the block still restores it
#   - asyncio tasks and threads never observe each other's context

import asyncio
import threading

import pytest

from core.runtime.execution_context import ContextMode, EnhancedExecutionContext


@pytest.fixture(autouse=True)
def reset_context():
    EnhancedExecutionContext.reset()
    yield
    EnhancedExecutionContext.reset()


def test_nested_context_restores_outer_state():
    ctx = EnhancedExecutionContext.instance()
    assert ctx.is_safe is False

    with ctx.mutation_context(can_mutate=True):
        assert ctx.is_safe is True
        assert ctx.context_depth == 1

        with ctx.mutation_context(can_mutate=False):
            assert ctx.is_safe is False
            assert ctx.context_depth == 2

        assert ctx.is_safe is True
        assert ctx.context_depth == 1
        assert ctx.current_mode is ContextMode.MUTATION_ALLOWED

    assert ctx.is_safe is False
    assert ctx.context_depth == 0


def test_state_restored_after_exception():
    ctx = EnhancedExecutionContext.instance()

    with pytest.raises(RuntimeError):
        with ctx.mutation_context(can_mutate=True):
            assert ctx.is_safe is True
            raise RuntimeError('boom')

    assert ctx.is_safe is False
    assert ctx.context_depth == 0


def test_asyncio_tasks_do_not_share_context_state():
    ctx = EnhancedExecutionContext.instance()

    async def worker(can_mutate: bool):
        with ctx.mutation_context(can_mutate=can_mutate):
            await asyncio.sleep(0.01)
            first = ctx.is_safe
            await asyncio.sleep(0.01)
            return first, ctx.is_safe

    async def main():
        return await asyncio.gather(worker(True), worker(False))

    (ro_first, ro_after), (rw_first, rw_after) = asyncio.run(main())

    assert ro_first is True
    assert ro_after is True
    assert rw_first is False
    assert rw_after is False
    assert ctx.is_safe is False


def test_threads_do_not_share_context_state():
    ctx = EnhancedExecutionContext.instance()
    barrier = threading.Barrier(2, timeout=5)
    seen: dict[str, bool] = {}

    def read_only_worker():
        with ctx.mutation_context(can_mutate=False):
            barrier.wait()
            seen['read_only'] = ctx.is_safe
            barrier.wait()

    def mutation_worker():
        with ctx.mutation_context(can_mutate=True):
            barrier.wait()
            barrier.wait()
            seen['mutation'] = ctx.is_safe

    threads = [
        threading.Thread(target=read_only_worker),
        threading.Thread(target=mutation_worker),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert seen == {'read_only': False, 'mutation': True}
