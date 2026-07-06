# ATOM-META-RL-016 Verification Tests
# ================================
# Tests for bug fixes:
# 1. @ExecutionGateway.requires_gateway — static method, no instance on decoration
# 2. mutation_context() — thread-safe with _ctx_lock
# 3. SQLite WAL + deferred isolation — no deadlock

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
        gateway = ExecutionGateway()

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
        from orchestration.mutation_executor import MutationExecutor, MutationPayload

        db_path = tmp_path / 'test_concurrent.db'
        gateway = ExecutionGateway()
        store = StateWindowStore(db_path=str(db_path), gateway=gateway)
        executor = MutationExecutor(gateway)

        errors = []
        successes = []

        def writer(thread_id: int):
            try:
                with gateway.mutation_context():
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
