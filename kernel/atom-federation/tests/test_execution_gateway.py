# ATOM-META-RL-016 Verification Tests
# ================================
# Tests for bug fixes:
# 1. @ExecutionGateway.requires_gateway — static method, no instance on decoration
# 2. mutation_context() — thread-safe with _ctx_lock
# 3. SQLite WAL + deferred isolation — no deadlock

import random
import sqlite3
import threading
import time

import pytest

from orchestration.execution_gateway import ExecutionGateway, SafetyViolationError


class TestExecutionGatewaySingleton:
    def test_singleton_returns_same_instance(self):
        g1 = ExecutionGateway()
        g2 = ExecutionGateway()
        assert g1 is g2

    def test_instance_classmethod(self):
        g1 = ExecutionGateway.instance()
        g2 = ExecutionGateway.instance()
        assert g1 is g2


class TestMutationContextThreadSafety:
    def test_concurrent_context_entry_no_race(self):
        gateway = ExecutionGateway()
        results = []

        def worker(can_mutate: bool, results: list):
            try:
                with gateway.mutation_context(can_mutate=can_mutate):
                    time.sleep(0.01)
                    results.append(('entered', can_mutate, gateway._active_context, gateway._can_mutate))
            except Exception as e:
                results.append(('error', str(e)))

        threads = [
            threading.Thread(target=worker, args=(True, results)),
            threading.Thread(target=worker, args=(True, results)),
            threading.Thread(target=worker, args=(False, results)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        errors = [r for r in results if r[0] == 'error']
        assert len(errors) == 0, f'Race condition: {errors}'

    def test_nested_context_preserves_state(self):
        gateway = ExecutionGateway()
        outer_state = []

        with gateway.mutation_context(can_mutate=True):
            outer_state.append((gateway._active_context, gateway._can_mutate))

            with gateway.mutation_context(can_mutate=False):
                outer_state.append((gateway._active_context, gateway._can_mutate))

            outer_state.append((gateway._active_context, gateway._can_mutate))

        assert outer_state == [(True, True), (True, False), (True, True)]


class TestRequiresGatewayDecorator:
    def test_decorator_blocks_without_context(self):
        ExecutionGateway()

        class TestExecutor:
            @ExecutionGateway.requires_gateway
            def mutate(self):
                return 'mutated'

        executor = TestExecutor()

        with pytest.raises(SafetyViolationError) as exc_info:
            executor.mutate()

        assert 'Mutation blocked' in str(exc_info.value)

    def test_decorator_allows_inside_context(self):
        gateway = ExecutionGateway()

        class TestExecutor:
            @ExecutionGateway.requires_gateway
            def mutate(self):
                return 'success'

        executor = TestExecutor()
        result = None

        # Use same gateway instance that decorator checks
        with gateway.mutation_context():
            result = executor.mutate()

        assert result == 'success'

    def test_different_classes_share_same_guard(self):
        gateway = ExecutionGateway()

        class Executor1:
            @ExecutionGateway.requires_gateway
            def mutate(self):
                return 'executor1'

        class Executor2:
            @ExecutionGateway.requires_gateway
            def mutate(self):
                return 'executor2'

        ex1 = Executor1()
        ex2 = Executor2()

        # Both blocked outside context
        for ex in [ex1, ex2]:
            with pytest.raises(SafetyViolationError):
                ex.mutate()

        # Both work inside same context (using gateway singleton)
        with gateway.mutation_context():
            assert ex1.mutate() == 'executor1'
            assert ex2.mutate() == 'executor2'


class TestSQLiteWALIsolation:
    def test_wal_mode_enabled(self, tmp_path):
        from meta_control.persistence.state_window_store import StateWindowStore

        db_path = tmp_path / 'test_wal.db'
        store = StateWindowStore(db_path=str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.execute('PRAGMA journal_mode')
        mode = cursor.fetchone()[0]
        conn.close()
        store.close()

        assert mode.upper() == 'WAL', f'Expected WAL, got {mode}'

    def test_concurrent_writes_no_deadlock(self, tmp_path):
        from meta_control.persistence.state_window_store import StateWindowStore

        db_path = tmp_path / 'test_concurrent.db'
        gateway = ExecutionGateway()
        store = StateWindowStore(db_path=str(db_path), gateway=gateway)

        errors = []
        successes = []

        def writer(thread_id: int):
            try:
                for i in range(5):
                    payload = MutationPayload(
                        tick=thread_id * 100 + i,
                        agent_id=f'agent_{thread_id}',
                        operation='test',
                        state_delta={'v': thread_id * 10 + i}
                    )
                    executor.execute(payload)
                    successes.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Protected module: both import and instantiation are legal only inside
        # the Gateway context (GUARD enforces it at import time and in __call__).
        # The context flag is process-wide, so one context covers all writers —
        # the concurrency under test is the SQLite writes, not the context.
        with gateway.mutation_context():
            from orchestration.mutation_executor import MutationExecutor, MutationPayload
            executor = MutationExecutor(gateway)

            threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        assert len(errors) == 0, f'Concurrent errors: {errors}'
        assert len(successes) == 15

        store.close()


class TestBypassImpossible:
    def test_direct_import_bypass_blocked(self):
        gateway = ExecutionGateway()

        class BypassAttempt:
            @ExecutionGateway.requires_gateway
            def unsafe_mutation(self):
                return 'bypassed!'

        bypasser = BypassAttempt()

        with pytest.raises(SafetyViolationError):
            bypasser.unsafe_mutation()

        with gateway.mutation_context():
            assert bypasser.unsafe_mutation() == 'bypassed!'


class TestNestedContextDepth:
    def test_nested_contexts_never_clear_flags_while_a_thread_is_inside(self):
        """Restoring a snapshot on exit lets one thread switch off another's context.

        Every thread is inside its own (nested) mutation_context when the first
        one leaves; the remaining threads must still see is_safe() == True.
        """
        gateway = ExecutionGateway()
        n_threads = 8
        all_inside = threading.Barrier(n_threads, timeout=10)
        first_exited = threading.Event()
        seen_unsafe = []

        def worker(index: int) -> None:
            with gateway.mutation_context():
                all_inside.wait()
                with gateway.mutation_context():
                    time.sleep(random.uniform(0, 0.01))
                    if index != 0:
                        first_exited.wait(timeout=10)
                        time.sleep(random.uniform(0, 0.01))
                        if not gateway.is_safe():
                            seen_unsafe.append(index)
            if index == 0:
                first_exited.set()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert seen_unsafe == [], f'context switched off under threads: {seen_unsafe}'
        assert gateway.is_safe() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
