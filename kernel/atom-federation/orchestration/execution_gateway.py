# execution_gateway.py — facade over the canonical ExecutionGateway.
#
# The gate chain (G1..G10 -> ACT) and the sole entry point live in
# orchestration/ExecutionGateway/execution_gateway.py. This module only keeps
# the API the rest of the tree imports (singleton, requires_gateway,
# mutation_context) and wires the canonical gateway to the local executor
# protocol. No gate logic is duplicated here.
#
#   1. Singleton — one instance per process
#   2. mutation_context() — activates GatewayContext + guard policy context
#   3. @requires_gateway — guards all mutation methods
#
# FAIL-FAST: Any violation → SystemShutdown (no recovery)

from __future__ import annotations

import threading
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any, Optional

from core.runtime.execution_context import ContextMode, EnhancedExecutionContext
from core.runtime.guard_policy import ExecutionGuardPolicy
from core.runtime.import_guard import GatewayContext
from orchestration.ExecutionGateway.execution_gateway import (
    ExecutionGateway as _CanonGateway,
)
from orchestration.ExecutionGateway.execution_gateway import (
    GateResult,
    GateStatus,
    GatewayResult,
    GatewayState,
)

__all__ = [
    'AuditLogger',
    'ExecutionGateway',
    'GateResult',
    'GateStatus',
    'GatewayResult',
    'GatewayState',
    'SafetyViolationError',
]


# ── Layers ─────────────────────────────────────────────────────────────────────
# guard_policy, import_guard and execution_context are imported unconditionally
# above, so every layer below is present whenever this module imports at all.

_SELF_AUDIT_AVAILABLE = True
_GUARD_POLICY_AVAILABLE = True
_CONTEXT_AVAILABLE = True


# ── Exception Types ────────────────────────────────────────────────────────────

class SafetyViolationError(Exception):
    '''Любая попытка мутации вне ExecutionGateway.'''
    pass


# ── Audit Logger ───────────────────────────────────────────────────────────────

class AuditLogger:
    '''Thread-safe audit logger for all mutation operations.'''

    _instance: Optional['AuditLogger'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._entries = []
        return cls._instance

    def log(self, event_type: str, module: str, function: str,
            allowed: bool, reason: str = '', details: dict = None) -> None:
        from datetime import datetime, timezone
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'module': module,
            'function': function,
            'allowed': allowed,
            'reason': reason,
            'details': details or {},
        }
        with self._lock:
            self._entries.append(entry)
            # Keep last 1000 entries
            if len(self._entries) > 1000:
                self._entries = self._entries[-1000:]

    def get_recent(self, count: int = 50) -> list:
        with self._lock:
            return list(self._entries[-count:])


# ── Executor adapter ───────────────────────────────────────────────────────────

class _PayloadExecutorAdapter:
    '''
    Adapts the payload-style executor (MutationExecutor.execute(payload)) to
    the apply_mutation(...) call the canonical ACT stage makes.
    '''

    def __init__(self, executor: Any) -> None:
        self._executor = executor

    def apply_mutation(self, drift_score: float, health_score: float,
                       mutation_density: float, coherence_drop: float,
                       oscillation_detected: bool, tick: int = 0) -> Any:
        from orchestration.mutation_executor import MutationPayload

        payload = MutationPayload(
            tick=tick,
            agent_id='execution_gateway',
            operation='apply_mutation',
            state_delta={
                'drift_score': drift_score,
                'health_score': health_score,
                'mutation_density': mutation_density,
                'coherence_drop': coherence_drop,
                'oscillation_detected': oscillation_detected,
            },
        )
        return self._executor.execute(payload)


def _as_mutation_executor(executor: Any) -> Any:
    '''Allow both executor protocols: apply_mutation(...) and execute(payload).'''
    if executor is None or hasattr(executor, 'apply_mutation'):
        return executor
    if hasattr(executor, 'execute'):
        return _PayloadExecutorAdapter(executor)
    return executor


# ── ExecutionGateway ───────────────────────────────────────────────────────────

class ExecutionGateway(_CanonGateway):
    '''
    Singleton gateway-guard for all state mutations.

    Guarantees:
        1. Singleton — one instance per process
        2. mutation_context() — only way to enable mutations
        3. @requires_gateway — guards all decorated methods
        4. Canonical gate chain G1..G10 -> ACT for every execute()

    Usage:
        gateway = ExecutionGateway.instance()
        with gateway.mutation_context():
            executor.execute(payload)
    '''

    _instance: Optional['ExecutionGateway'] = None
    _lock = threading.Lock()
    _init_lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> 'ExecutionGateway':
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, mutation_executor: Any = None,
                 proof_verifier: Any = None) -> None:
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            super().__init__(
                mutation_executor=_as_mutation_executor(mutation_executor),
                proof_verifier=proof_verifier,
            )

            self._ctx_lock = threading.RLock()
            self._ctx_local = threading.local()
            self._context_depth = 0
            self._policy = ExecutionGuardPolicy.instance()
            self._enhanced_ctx = EnhancedExecutionContext.instance()
            self._audit = AuditLogger()

            self._audit.log(
                'startup',
                'ExecutionGateway',
                '__init__',
                allowed=True,
                reason='canonical_gate_chain',
                details={'mutation_executor': type(mutation_executor).__name__},
            )

            self._initialized = True

    @classmethod
    def instance(cls) -> 'ExecutionGateway':
        '''Return singleton instance.'''
        if cls._instance is None:
            cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        '''Reset singleton (for testing only).'''
        with cls._lock:
            cls._instance = None
            cls._initialized = False

    @classmethod
    def requires_gateway(cls, func: Callable) -> Callable:
        '''
        Static decorator — works with the singleton instance.

        Raises SafetyViolationError on any call outside mutation_context();
        the guard policy may escalate it to SystemShutdown.
        '''
        @wraps(func)
        def guarded(self, *args, **kwargs):
            gateway = cls.instance()

            # ── Primary check: context must be active ──────────────────
            if not gateway._latch_open():
                gateway._audit.log(
                    'mutation_blocked',
                    self.__class__.__module__,
                    func.__qualname__,
                    allowed=False,
                    reason='no_active_context',
                    details={'depth': gateway._context_depth}
                )

                # ── Guard Policy check — may trigger SystemShutdown ────
                gateway._policy.assert_mutation_allowed(
                    self.__class__.__module__,
                    func.__qualname__,
                    operation=func.__name__,
                )

                raise SafetyViolationError(
                    f'Mutation blocked by ExecutionGateway: {func.__qualname__}. '
                    f'All mutations MUST go through ExecutionGateway.mutation_context()'
                )

            # ── Runtime verifier check (P0.1) ───────────────────────────
            from core.runtime.self_audit import RuntimeVerifier
            RuntimeVerifier.verify_mutation_call(
                self.__class__.__module__,
                func.__qualname__,
                operation=func.__name__,
            )

            # ── Enhanced context check (P1.4) ──────────────────────────
            gateway._enhanced_ctx.assert_mutation_allowed(
                operation=func.__name__,
                payload_summary=f'{self.__class__.__name__}.{func.__name__}',
            )

            return func(self, *args, **kwargs)

        return guarded

    def _latch_open(self) -> bool:
        '''Process-wide latch: any open mutation_context() authorises mutations.

        Deliberately not thread-local: a context opened by a parent thread covers
        its worker threads (see test_concurrent_writes_no_deadlock). is_safe()
        stays thread-local: it reports what this thread may do right now.
        '''
        with self._ctx_lock:
            return self._context_depth > 0

    def _ctx_stack(self) -> list:
        '''Per-thread nesting stack (thread-local; never shared across threads).'''
        stack = getattr(self._ctx_local, 'stack', None)
        if stack is None:
            stack = []
            self._ctx_local.stack = stack
        return stack

    @property
    def _active_context(self) -> bool:
        return getattr(self._ctx_local, 'active', False)

    @_active_context.setter
    def _active_context(self, value: bool) -> None:
        self._ctx_local.active = value

    @property
    def _can_mutate(self) -> bool:
        return getattr(self._ctx_local, 'can_mutate', False)

    @_can_mutate.setter
    def _can_mutate(self, value: bool) -> None:
        self._ctx_local.can_mutate = value

    @contextmanager
    def mutation_context(self, can_mutate: bool = True) -> None:
        '''
        Единственный разрешённый способ выполнить мутацию.

        Activates both the import-time GatewayContext and the guard policy
        context, and restores the previous state on exit (nesting-safe).

        Raises:
            SafetyViolationError: if mutation attempted outside context
            SystemShutdown: if bypass detected
        '''
        self._policy.assert_gateway_active('mutation_context')
        mode = ContextMode.MUTATION_ALLOWED if can_mutate else ContextMode.READ_ONLY

        with self._ctx_lock:
            # Per-thread stack + shared depth: a snapshot restored on exit lets one
            # thread switch the context off while another thread is still inside.
            self._ctx_stack().append((self._active_context, self._can_mutate))
            self._active_context = True
            self._can_mutate = can_mutate
            self._context_depth += 1

        GatewayContext.activate('mutation_context')
        self._policy.push_gateway_context('orchestration.execution_gateway')
        self._audit.log(
            'context_enter',
            'ExecutionGateway',
            'mutation_context',
            allowed=True,
            details={'can_mutate': can_mutate},
        )

        try:
            with self._enhanced_ctx.mutation_context(can_mutate=can_mutate, mode=mode):
                yield self
        finally:
            self._policy.pop_gateway_context('orchestration.execution_gateway')
            GatewayContext.deactivate()

            with self._ctx_lock:
                stack = self._ctx_stack()
                active, can_mutate_prev = stack.pop() if stack else (False, False)
                self._active_context = active
                self._can_mutate = can_mutate_prev
                self._context_depth = max(0, self._context_depth - 1)

            self._audit.log(
                'context_exit',
                'ExecutionGateway',
                'mutation_context',
                allowed=True,
            )

    def execute(self, input_data: Any, intent: str = '') -> GatewayResult:
        '''Run the canonical G1..G10 -> ACT chain with the mutation context open.'''
        with self.mutation_context():
            return super().execute(input_data, intent)

    def is_safe(self) -> bool:
        '''Check if mutation is currently allowed.'''
        with self._ctx_lock:
            return self._active_context and self._can_mutate

    def assert_safe(self) -> None:
        '''Raise if mutation attempted outside context.'''
        if not self.is_safe():
            raise SafetyViolationError(
                'Mutation attempted outside ExecutionGateway.mutation_context()'
            )

    def get_audit_log(self, limit: int = 50) -> list:
        '''Return recent audit entries.'''
        return self._audit.get_recent(limit)

    def get_stats(self) -> dict:
        '''Return gateway statistics.'''
        return {
            'initialized': self._initialized,
            'active_context': self._active_context,
            'can_mutate': self._can_mutate,
            'guard_policy_available': _GUARD_POLICY_AVAILABLE,
            'self_audit_available': _SELF_AUDIT_AVAILABLE,
            'enhanced_context_available': _CONTEXT_AVAILABLE,
            'audit_entries': len(self._audit.get_recent(10000)),
            'gate': self.stats,
        }


# ── Alias for compatibility ────────────────────────────────────────────────────
SafetyViolationError.__module__ = 'orchestration.execution_gateway'
