# execution_context.py — atom-federation-os v9.0+P1.4
# Enhanced ExecutionContext: Thread-safe + Async-aware + Audit Trail
#
# Thread-safety: Uses threading.RLock (reentrant, safe for async)
# Async-safety: Works with asyncio (no event-loop assumptions)
# Audit: Every mutation logged with full context for traceability

from __future__ import annotations

import asyncio
import threading
import traceback
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

# ── Deterministic primitives (ATOM-META-RL-019) ───────────────────────────────
try:
    from core.deterministic import DeterministicClock, DeterministicUUIDFactory
except ImportError:
    DeterministicUUIDFactory = None
    DeterministicClock = None


class ContextMode(Enum):
    READ_ONLY = 'read_only'      # No mutations allowed
    MUTATION_ALLOWED = 'mutation_allowed'  # Mutations permitted
    INTERNAL = 'internal'        # Internal gateway operations


@dataclass(frozen=True)
class _ContextState:
    '''Per-call context state. Stored in a ContextVar — one copy per thread / asyncio task.'''
    can_mutate: bool = False
    active: bool = False
    mode: ContextMode = ContextMode.READ_ONLY
    depth: int = 0
    context_id: str = ''


@dataclass
class MutationAuditEntry:
    '''Single mutation audit record.'''
    entry_id: str
    timestamp: str
    mode: ContextMode
    caller_module: str
    caller_function: str
    caller_file: str
    caller_line: int
    operation: str
    payload_summary: str
    stack_snapshot: str
    allowed: bool
    denied_reason: str = ''

    def to_dict(self) -> dict:
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp,
            'mode': self.mode.value,
            'caller': f'{self.caller_module}.{self.caller_function}',
            'file': f'{self.caller_file}:{self.caller_line}',
            'operation': self.operation,
            'allowed': self.allowed,
            'denied_reason': self.denied_reason,
        }


class EnhancedExecutionContext:
    '''
    Thread-safe + Async-aware execution context for mutations.

    Features:
        - Caller-isolated state (ContextVar): per thread and per asyncio task
        - Full audit trail of all mutation attempts
        - Nested context support (inner context restores outer on exit)
        - Deterministic tick propagation

    Usage:
        ctx = EnhancedExecutionContext()

        # Mutation allowed
        with ctx.mutation_context(can_mutate=True):
            # ... perform mutations ...

        # Read-only
        with ctx.mutation_context(can_mutate=False):
            # ... read state, no mutations allowed ...
    '''

    _instance: EnhancedExecutionContext | None = None
    _lock = threading.Lock()

    def __new__(cls) -> EnhancedExecutionContext:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._ctx_lock = threading.RLock()  # Reentrant — same thread can re-enter
        self._async_lock = None  # Lazy init for async support

        # Context state — per thread / asyncio task, never shared between callers
        self._ctx_state: ContextVar[_ContextState] = ContextVar(
            f'execution_context_state_{id(self)}', default=_ContextState()
        )

        # Audit trail
        self._audit_log: list[MutationAuditEntry] = []
        self._audit_lock = threading.Lock()

        # Tick tracking
        self._tick: int = 0

    @classmethod
    def instance(cls) -> EnhancedExecutionContext:
        if cls._instance is None:
            cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        '''Reset singleton (for testing only).'''
        with cls._lock:
            if cls._instance is not None:
                cls._instance._ctx_state.set(_ContextState())
            cls._instance = None

    @property
    def is_safe(self) -> bool:
        '''Check if mutation is currently allowed — in the CALLER's own context.'''
        state = self._ctx_state.get()
        return state.active and state.can_mutate

    @property
    def current_mode(self) -> ContextMode:
        '''Get current context mode.'''
        return self._ctx_state.get().mode

    @property
    def context_depth(self) -> int:
        '''Get current context nesting depth.'''
        return self._ctx_state.get().depth

    # ── Read-only views over the per-call state (kept for internal readers) ──
    @property
    def _can_mutate(self) -> bool:
        return self._ctx_state.get().can_mutate

    @property
    def _active_context(self) -> bool:
        return self._ctx_state.get().active

    @property
    def _context_mode(self) -> ContextMode:
        return self._ctx_state.get().mode

    @property
    def _context_depth(self) -> int:
        return self._ctx_state.get().depth

    @property
    def _context_id(self) -> str:
        return self._ctx_state.get().context_id

    @property
    def current_tick(self) -> int:
        '''Get current tick.'''
        with self._ctx_lock:
            return self._tick

    def advance_tick(self) -> int:
        '''Advance tick counter. Returns new tick.'''
        with self._ctx_lock:
            self._tick += 1
            return self._tick

    @contextmanager
    def mutation_context(self, can_mutate: bool = True,
                         mode: ContextMode = ContextMode.MUTATION_ALLOWED):
        '''
        Context manager for mutations, scoped to the calling thread / asyncio task.

        Args:
            can_mutate: If True, mutations are allowed inside this context.
                       If False, only read-only operations permitted.
            mode: Context mode (READ_ONLY or MUTATION_ALLOWED)

        Usage:
            # Allow mutations
            with ctx.mutation_context(can_mutate=True):
                executor.execute(payload)

            # Read-only (no mutations)
            with ctx.mutation_context(can_mutate=False):
                state = read_state()

        Isolation:
            - State lives in a ContextVar: one copy per thread and per asyncio task.
            - Concurrent callers never observe each other's context.
            - Nested entry restores the outer state via ContextVar token reset.
        '''
        # Capture current stack for audit
        stack = self._capture_stack()

        prev = self._ctx_state.get()
        depth = prev.depth + 1
        state = _ContextState(
            can_mutate=can_mutate,
            active=True,
            mode=mode if can_mutate else ContextMode.READ_ONLY,
            depth=depth,
            context_id=DeterministicUUIDFactory.make_context_id(
                agent_id=self.__class__.__name__,
                tick=self._tick,
                depth=depth
            ),
        )
        token = self._ctx_state.set(state)

        # Log context entry
        if can_mutate:
            self._log_audit_entry(
                mode=state.mode,
                caller_module=self._get_caller_module(stack),
                caller_function=self._get_caller_function(stack),
                caller_file=self._get_caller_file(stack),
                caller_line=self._get_caller_line(stack),
                operation='context_enter',
                payload_summary=f'can_mutate={can_mutate}, depth={depth}',
                allowed=True,
            )

        try:
            yield self
        except Exception as e:
            # Log error
            stack = self._capture_stack()
            self._log_audit_entry(
                mode=state.mode,
                caller_module=self._get_caller_module(stack),
                caller_function=self._get_caller_function(stack),
                caller_file=self._get_caller_file(stack),
                caller_line=self._get_caller_line(stack),
                operation='context_error',
                payload_summary=f'error={type(e).__name__}: {e}',
                allowed=False,
                denied_reason='exception_during_context',
            )
            raise
        finally:
            # Restore the caller's outer state (nested contexts included)
            self._ctx_state.reset(token)

            # Log context exit
            if prev.can_mutate:
                self._log_audit_entry(
                    mode=prev.mode,
                    caller_module=self._get_caller_module(stack),
                    caller_function=self._get_caller_function(stack),
                    caller_file=self._get_caller_file(stack),
                    caller_line=self._get_caller_line(stack),
                    operation='context_exit',
                    payload_summary=f'depth={depth}->nested',
                    allowed=True,
                )

    @contextmanager
    def internal_context(self):
        '''
        Internal gateway context (highest priority).

        Used for gateway-internal operations that bypass normal checks.
        Scoped to the calling thread / asyncio task, like mutation_context.
        '''
        prev = self._ctx_state.get()
        depth = prev.depth + 1
        state = _ContextState(
            can_mutate=True,
            active=True,
            mode=ContextMode.INTERNAL,
            depth=depth,
            context_id=DeterministicUUIDFactory.make_context_id(
                agent_id=self.__class__.__name__,
                tick=self._tick,
                depth=depth
            ),
        )
        token = self._ctx_state.set(state)

        try:
            yield self
        finally:
            self._ctx_state.reset(token)

    def assert_mutation_allowed(self, operation: str = 'unknown',
                                 payload_summary: str = '') -> None:
        '''
        HARD ASSERT: Verify mutation is allowed in current context.

        Raises:
            SafetyViolationError: if mutation not allowed
            SystemShutdown: if bypass attempt detected

        Called by @requires_gateway decorator and MutationExecutor.
        '''
        from core.runtime.guard_policy import ExecutionGuardPolicy, SystemShutdown
        from orchestration.execution_gateway import SafetyViolationError

        stack = self._capture_stack()

        with self._ctx_lock:
            if not self._active_context:
                # No context at all — check if this is a bypass
                policy = ExecutionGuardPolicy.instance()

                self._log_audit_entry(
                    mode=ContextMode.READ_ONLY,
                    caller_module=self._get_caller_module(stack),
                    caller_function=self._get_caller_function(stack),
                    caller_file=self._get_caller_file(stack),
                    caller_line=self._get_caller_line(stack),
                    operation=operation,
                    payload_summary=payload_summary,
                    allowed=False,
                    denied_reason='no_active_context',
                )

                # Try guard policy — this may trigger SystemShutdown
                try:
                    policy.assert_mutation_allowed(
                        self._get_caller_module(stack),
                        self._get_caller_function(stack),
                        operation
                    )
                except SystemShutdown:
                    raise

                # If guard policy allows (gateway context detected via stack), proceed
                if policy.is_gateway_context_active():
                    return

                raise SafetyViolationError(
                    f'Mutation blocked: no active ExecutionGateway context. '
                    f'Operation: {operation}, Caller: {self._get_caller_module(stack)}.{self._get_caller_function(stack)}'
                )

            if not self._can_mutate:
                self._log_audit_entry(
                    mode=self._context_mode,
                    caller_module=self._get_caller_module(stack),
                    caller_function=self._get_caller_function(stack),
                    caller_file=self._get_caller_file(stack),
                    caller_line=self._get_caller_line(stack),
                    operation=operation,
                    payload_summary=payload_summary,
                    allowed=False,
                    denied_reason='can_mutate=False',
                )

                raise SafetyViolationError(
                    f'Mutation blocked: context is READ-ONLY. '
                    f'Operation: {operation}, Mode: {self._context_mode.value}'
                )

    def log_mutation(self, operation: str, payload_summary: str = '',
                     allowed: bool = True, denied_reason: str = '') -> None:
        '''Log a mutation attempt.'''
        stack = self._capture_stack()
        self._log_audit_entry(
            mode=self._context_mode,
            caller_module=self._get_caller_module(stack),
            caller_function=self._get_caller_function(stack),
            caller_file=self._get_caller_file(stack),
            caller_line=self._get_caller_line(stack),
            operation=operation,
            payload_summary=payload_summary,
            allowed=allowed,
            denied_reason=denied_reason,
        )

    def get_audit_log(self, limit: int = 100) -> list[MutationAuditEntry]:
        '''Return recent audit entries.'''
        with self._audit_lock:
            return list(self._audit_log[-limit:])

    def get_audit_summary(self) -> dict:
        '''Return audit statistics.'''
        with self._audit_lock:
            total = len(self._audit_log)
            allowed = sum(1 for e in self._audit_log if e.allowed)
            denied = total - allowed
            return {
                'total_entries': total,
                'allowed': allowed,
                'denied': denied,
                'current_depth': self._context_depth,
                'current_mode': self._context_mode.value,
                'tick': self._tick,
            }

    def clear_audit_log(self) -> None:
        '''Clear audit log (for testing only).'''
        with self._audit_lock:
            self._audit_log.clear()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _log_audit_entry(self, mode: ContextMode,
                         caller_module: str, caller_function: str,
                         caller_file: str, caller_line: int,
                         operation: str, payload_summary: str,
                         allowed: bool, denied_reason: str = '') -> MutationAuditEntry:
        '''Add entry to audit log.'''
        entry = MutationAuditEntry(
            entry_id=DeterministicUUIDFactory.make_entry_id(
                operation=operation,
                tick=self._tick,
                seq=len(self._audit_log)
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode=mode,
            caller_module=caller_module,
            caller_function=caller_function,
            caller_file=caller_file,
            caller_line=caller_line,
            operation=operation,
            payload_summary=payload_summary,
            stack_snapshot=self._format_stack(self._capture_stack()),
            allowed=allowed,
            denied_reason=denied_reason,
        )

        with self._audit_lock:
            self._audit_log.append(entry)

        return entry

    def _capture_stack(self) -> list:
        return traceback.extract_stack()[:-1]  # Exclude this function

    def _get_caller_module(self, stack: list) -> str:
        if not stack:
            return 'unknown'
        frame = stack[-1]
        filename = frame.filename
        # Extract module from filename
        if 'atom-federation-os' in filename:
            parts = filename.split('atom-federation-os')
            if len(parts) > 1:
                rel = parts[1].lstrip('/')
                mod = rel.replace('/', '.').replace('.py', '')
                if mod.endswith('.__init__'):
                    mod = mod[:-9]
                return mod
        return frame.filename

    def _get_caller_function(self, stack: list) -> str:
        if not stack:
            return 'unknown'
        return stack[-1].name

    def _get_caller_file(self, stack: list) -> str:
        if not stack:
            return 'unknown'
        return stack[-1].filename

    def _get_caller_line(self, stack: list) -> int:
        if not stack:
            return 0
        return stack[-1].lineno

    def _format_stack(self, stack: list) -> str:
        return '\n'.join(
            f'  {frame.filename}:{frame.lineno} in {frame.name}'
            for frame in stack[-8:]
        )

    # ── Async support ──────────────────────────────────────────────────────

    async def async_mutation_context(self, can_mutate: bool = True,
                                      mode: ContextMode = ContextMode.MUTATION_ALLOWED):
        '''
        Async-compatible context manager.

        Usage:
            async with ctx.async_mutation_context(can_mutate=True):
                await do_async_work()
        '''
        return self.mutation_context(can_mutate=can_mutate, mode=mode)


# ── Async-aware context manager ────────────────────────────────────────────────

class AsyncExecutionContext:
    '''
    Async-aware execution context wrapper.

    For use with asyncio-based code:
        async with ctx.async_mutation_context():
            await executor.execute_async(payload)
    '''

    def __init__(self, context: EnhancedExecutionContext | None = None):
        self._ctx = context or EnhancedExecutionContext.instance()
        self._async_lock = None

    async def __aenter__(self):
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        await self._async_lock.acquire()
        return self

    async def __aexit__(self, *args):
        if self._async_lock:
            self._async_lock.release()
        return False

    @property
    def is_safe(self) -> bool:
        return self._ctx.is_safe

    async def mutation_context(self, can_mutate: bool = True):
        '''Async context manager.'''
        return self._ctx.mutation_context(can_mutate=can_mutate)
