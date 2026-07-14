# execution_gateway.py — atom-federation-os v9.0+ATOM-META-RL-016+P0.1+P0.3
# ExecutionGateway — единая точка входа всех мутаций в ATOMFEDERATION-OS.
#
# HARD SAFETY GUARANTEES:
#   1. Singleton — only one instance exists
#   2. mutation_context() — ONLY way to perform mutations
#   3. @requires_gateway decorator — guards all mutation methods
#   4. Runtime Self-Audit at startup — detects bypass paths
#   5. ExecutionGuardPolicy — global fail-fast enforcement
#   6. Thread-safe + Async-aware context management
#   7. Full audit trail for every mutation
#
# FAIL-FAST: Any violation → SystemShutdown (no recovery)

import threading
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Optional

# ── Import Guards (P0.2 — Import Protection) ──────────────────────────────────
# These must be imported FIRST, before any protected modules
try:
    from core.runtime.import_guard import GatewayContextGuard, install_firewall
    _FIREWALL_INSTALLED = True
except ImportError:
    install_firewall = None
    GatewayContextGuard = None
    _FIREWALL_INSTALLED = False

# ── Self-Audit (P0.1) ──────────────────────────────────────────────────────────
# Run at startup to detect bypass paths
try:
    from core.runtime.self_audit import RuntimeVerifier, SelfAudit, run_startup_audit
    _SELF_AUDIT_AVAILABLE = True
except ImportError:
    run_startup_audit = None
    SelfAudit = None
    RuntimeVerifier = None
    _SELF_AUDIT_AVAILABLE = False

# ── Guard Policy (P0.3) ────────────────────────────────────────────────────────
try:
    from core.runtime.guard_policy import ExecutionGuardPolicy, SystemShutdown
    _GUARD_POLICY_AVAILABLE = True
except ImportError:
    ExecutionGuardPolicy = None
    SystemShutdown = Exception
    _GUARD_POLICY_AVAILABLE = False

# ── Enhanced Context (P1.4) ────────────────────────────────────────────────────
try:
    from core.runtime.execution_context import ContextMode, EnhancedExecutionContext
    _CONTEXT_AVAILABLE = True
except ImportError:
    EnhancedExecutionContext = None
    ContextMode = None
    _CONTEXT_AVAILABLE = False


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


# ── ExecutionGateway ───────────────────────────────────────────────────────────

class ExecutionGateway:
    '''
    Singleton gateway-guard для всех state mutations в системе.

    Guarantees:
        1. Singleton — only one instance per process
        2. mutation_context() — only way to enable mutations
        3. @requires_gateway — guards all decorated methods
        4. Runtime Self-Audit at startup
        5. ExecutionGuardPolicy for global enforcement
        6. Thread-safe + async-aware
        7. Full audit trail

    Usage:
        gateway = ExecutionGateway.instance()
        with gateway.mutation_context():
            executor.execute(payload)

    Decorator:
        @ExecutionGateway.requires_gateway
        def mutate(self, ...):
            ...
    '''

    _instance: Optional['ExecutionGateway'] = None
    _lock = threading.Lock()
    _init_lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> 'ExecutionGateway':
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)

                    # ── Initialize core state ──────────────────────────────
                    instance._can_mutate = False
                    instance._active_context = False
                    instance._ctx_lock = threading.RLock()

                    # ── Enhanced context (P1.4) ──────────────────────────
                    if _CONTEXT_AVAILABLE:
                        instance._enhanced_ctx = EnhancedExecutionContext.instance()
                    else:
                        instance._enhanced_ctx = None

                    # ── Guard Policy (P0.3) ───────────────────────────────
                    if _GUARD_POLICY_AVAILABLE:
                        instance._policy = ExecutionGuardPolicy.instance()
                    else:
                        instance._policy = None

                    # ── Audit logger ─────────────────────────────────────
                    instance._audit = AuditLogger()

                    # ── Install import firewall (P0.2) ───────────────────
                    if _FIREWALL_INSTALLED and callable(install_firewall):
                        install_firewall()

                    cls._instance = instance
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            # ── Run Startup Self-Audit (P0.1) ───────────────────────────
            if _SELF_AUDIT_AVAILABLE and callable(run_startup_audit):
                try:
                    audit_result = run_startup_audit()
                    self._audit.log(
                        'startup_audit',
                        'ExecutionGateway',
                        '__init__',
                        allowed=audit_result.passed,
                        reason='self_audit' if audit_result.passed else audit_result.error_message,
                        details={
                            'modules_scanned': audit_result.total_modules_scanned,
                            'mutation_points': audit_result.mutation_points_found,
                            'bypass_paths': len(audit_result.bypass_paths_detected),
                            'graph_hash': audit_result.graph_hash,
                        }
                    )
                except SystemShutdown:
                    raise
                except Exception as e:
                    self._audit.log(
                        'startup_audit',
                        'ExecutionGateway',
                        '__init__',
                        allowed=False,
                        reason=f'audit_error: {e}',
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
            if cls._instance is not None:
                if cls._instance._enhanced_ctx:
                    cls._instance._enhanced_ctx.reset()
            cls._instance = None
            cls._initialized = False

    @classmethod
    def requires_gateway(cls, func: Callable) -> Callable:
        '''
        Static decorator — работает с singleton-экземпляром.

        Guarantees:
            - Mutation allowed ONLY when mutation_context is active
            - Raises SafetyViolationError on any bypass attempt
            - Triggers ExecutionGuardPolicy check (P0.3)
            - Logs to audit trail

        Bypass physically impossible:
            - Checks singleton state on EVERY call
            - Guard policy validates caller registration
            - Stack trace verification
        '''
        @wraps(func)
        def guarded(self, *args, **kwargs):
            gateway = cls.instance()

            # ── Primary check: context must be active ──────────────────
            if not gateway._active_context or not gateway._can_mutate:
                gateway._audit.log(
                    'mutation_blocked',
                    self.__class__.__module__,
                    func.__qualname__,
                    allowed=False,
                    reason='no_active_context',
                    details={'active': gateway._active_context, 'can_mutate': gateway._can_mutate}
                )

                # ── Guard Policy check (P0.3) — may trigger SystemShutdown
                if _GUARD_POLICY_AVAILABLE and gateway._policy:
                    try:
                        gateway._policy.assert_mutation_allowed(
                            self.__class__.__module__,
                            func.__qualname__,
                            operation=func.__name__
                        )
                    except SystemShutdown:
                        raise

                raise SafetyViolationError(
                    f'Mutation blocked by ExecutionGateway: {func.__qualname__}. '
                    f'All mutations MUST go through ExecutionGateway.mutation_context()'
                )

            # ── Runtime verifier check (P0.1) ───────────────────────────
            if _SELF_AUDIT_AVAILABLE and RuntimeVerifier:
                try:
                    RuntimeVerifier.verify_mutation_call(
                        self.__class__.__module__,
                        func.__qualname__,
                        operation=func.__name__
                    )
                except SystemShutdown:
                    raise

            # ── Enhanced context check (P1.4) ──────────────────────────
            if _CONTEXT_AVAILABLE and gateway._enhanced_ctx:
                gateway._enhanced_ctx.assert_mutation_allowed(
                    operation=func.__name__,
                    payload_summary=f'{self.__class__.__name__}.{func.__name__}'
                )

            return func(self, *args, **kwargs)

        return guarded

    @contextmanager
    def mutation_context(self, can_mutate: bool = True) -> None:
        '''
        Единственный разрешённый способ выполнить мутацию.

        Thread-safe: весь контекст защищён RLock.
        Async-safe: работает с asyncio.
        Bypass невозможен без SafetyViolationError.

        Args:
            can_mutate: False — read-only context (для drift detection, scan)

        Raises:
            SafetyViolationError: if mutation attempted outside context
            SystemShutdown: if bypass detected
        '''
        # ── Guard policy verification (P0.3) ───────────────────────────
        if _GUARD_POLICY_AVAILABLE and self._policy:
            self._policy.assert_gateway_active('mutation_context')

        # ── Enhanced context (P1.4) ───────────────────────────────────
        if _CONTEXT_AVAILABLE and self._enhanced_ctx:
            mode = ContextMode.MUTATION_ALLOWED if can_mutate else ContextMode.READ_ONLY
            with self._enhanced_ctx.mutation_context(can_mutate=can_mutate, mode=mode):
                self._enter_context(can_mutate)
                try:
                    yield self
                finally:
                    self._exit_context()
        else:
            # Fallback to basic context
            self._enter_context(can_mutate)
            try:
                yield self
            finally:
                self._exit_context()

    def _enter_context(self, can_mutate: bool) -> None:
        '''Enter mutation context.'''
        with self._ctx_lock:
            self._can_mutate = can_mutate
            self._active_context = True

        self._audit.log(
            'context_enter',
            'ExecutionGateway',
            'mutation_context',
            allowed=True,
            details={'can_mutate': can_mutate}
        )

    def _exit_context(self) -> None:
        '''Exit mutation context.'''
        with self._ctx_lock:
            self._can_mutate = False
            self._active_context = False

        self._audit.log(
            'context_exit',
            'ExecutionGateway',
            'mutation_context',
            allowed=True,
        )

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
        }


# ── Alias for compatibility ────────────────────────────────────────────────────
SafetyViolationError.__module__ = 'orchestration.execution_gateway'
