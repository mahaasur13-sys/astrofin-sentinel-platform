# guard_policy.py — atom-federation-os v9.0+P0.3
# ExecutionGuardPolicy: Global Fail-Fast Guard (Singleton)
#
# HARD INVARIANT: Any mutation outside ExecutionGateway → SystemShutdown.
# This policy is UNDISABLEABLE. No fallback, no warning, no grace period.
#
# RULES:
#   1. Only ExecutionGateway.execute() can originate mutations
#   2. MutationExecutor is ONLY accessible inside mutation_context
#   3. All mutation points MUST be registered at startup
#   4. Any unregistered mutation → SystemShutdown (immediate)
#   5. Gateway context MUST be active for ALL mutation operations
#
# Thread-safe: fully lock-protected against race conditions.

from __future__ import annotations

import hashlib
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ViolationSeverity(Enum):
    BLOCKED = 1          # Gateway blocked, but caught
    CRITICAL = 2         # Direct bypass attempt
    FATAL = 3            # System integrity compromised → SHUTDOWN


@dataclass
class MutationPoint:
    module: str
    function: str
    file_path: str
    line_number: int
    registered_at: str
    caller_stack_hash: str  # hash of expected call stack


@dataclass
class GuardViolation:
    timestamp: str
    severity: ViolationSeverity
    message: str
    detected_at: str
    caller_module: str
    caller_function: str
    caller_file: str
    caller_line: int
    stack_snapshot: str
    attempted_operation: str
    policy_rule_violated: str
    context: dict = field(default_factory=dict)


class SystemShutdown(Exception):
    '''
    FATAL: System integrity compromised.
    
    Raised when ExecutionGuardPolicy detects a violation that cannot
    be recovered. This is UNRECOVERABLE — system must abort.
    
    NO warnings, NO graceful degradation, NO fallback.
    '''
    def __init__(self, message: str, violation: GuardViolation | None = None):
        self.violation = violation
        super().__init__(message)


class ExecutionGuardPolicy:
    '''
    Global singleton that enforces mutation policy at runtime.
    
    Registration: All mutation points must register at startup via self_audit.
    Enforcement: Any violation → immediate SystemShutdown.
    Auditability: Every mutation logged with full trace.
    
    Usage:
        policy = ExecutionGuardPolicy.instance()
        policy.assert_mutation_allowed(caller_module, caller_function)
    '''

    _instance: ExecutionGuardPolicy | None = None
    _lock = threading.Lock()

    # Registry of ALL allowed mutation points (populated by self_audit)
    _mutation_points: dict[str, MutationPoint] = {}
    _violations_log: list[GuardViolation] = []
    _initialized: bool = False
    _init_lock = threading.Lock()

    # Protection state
    _active_context_modules: set[str] = field(default_factory=set)
    _gateway_depth: int = 0

    # Allowed entry point (ONLY this can originate mutations)
    _ALLOWED_ENTRY = frozenset({
        'execute', '_execute_impl', 'mutation_context',
        '_act_stage', 'apply_mutation',
    })

    # Forbidden patterns — any match = FATAL
    _FORBIDDEN_PATTERNS = frozenset({
        'direct_mutation', 'bypass_gateway', 'unsafe_execute',
        'execute_mutation_direct', 'force_mutation',
    })

    def __new__(cls) -> ExecutionGuardPolicy:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    cls._instance = instance
        return cls._instance

    @classmethod
    def instance(cls) -> ExecutionGuardPolicy:
        if cls._instance is None:
            cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        '''Reset singleton (for testing only).'''
        with cls._lock:
            cls._instance = None
            cls._mutation_points = {}
            cls._violations_log = []
            cls._initialized = False

    def initialize(self, mutation_points: dict[str, MutationPoint] | None = None) -> None:
        '''
        Initialize guard policy with registered mutation points.
        
        Called by self_audit at system startup AFTER module scan.
        '''
        with self._init_lock:
            if self._initialized:
                return
            self._initialized = True

            if mutation_points:
                self._mutation_points = mutation_points.copy()

    def register_mutation_point(self, module: str, function: str,
                                 file_path: str, line_number: int) -> None:
        '''
        Register a mutation point during self_audit.
        
        Key: module:function
        '''
        key = f'{module}:{function}'
        self._mutation_points[key] = MutationPoint(
            module=module,
            function=function,
            file_path=file_path,
            line_number=line_number,
            registered_at=datetime.now(timezone.utc).isoformat(),
            caller_stack_hash='',
        )

    def assert_mutation_allowed(self, caller_module: str, caller_function: str,
                                 operation: str = 'unknown') -> None:
        '''
        HARD ASSERT: Verify mutation is allowed.
        
        Called by:
        - ExecutionGateway before any mutation operation
        - MutationExecutor.apply_mutation()
        - Any component with @requires_gateway
        
        Raises:
            SystemShutdown: if mutation not allowed
        '''
        # Compute call stack
        stack = self._capture_stack()
        stack_str = self._format_stack(stack)
        stack_hash = hashlib.sha256(stack_str.encode()).hexdigest()[:16]

        # Check if in gateway context
        in_gateway = self._is_in_gateway_context(stack)

        # CRITICAL CHECK 1: Must be in gateway context
        if not in_gateway:
            violation = self._create_violation(
                severity=ViolationSeverity.FATAL,
                message=f'Mutation OUTSIDE Gateway context: {caller_module}.{caller_function}',
                caller_module=caller_module,
                caller_function=caller_function,
                operation=operation,
                stack=stack,
                policy_rule='gateway_context_required',
            )
            self._log_violation(violation)
            self._trigger_shutdown(violation)

        # CRITICAL CHECK 2: Caller must be registered mutation point OR gateway internals
        key = f'{caller_module}:{caller_function}'
        is_gateway_internal = any(x in caller_module.lower() for x in (
            'executiongateway', 'execution_gateway'))

        if not is_gateway_internal and key not in self._mutation_points:
            violation = self._create_violation(
                severity=ViolationSeverity.CRITICAL,
                message=f'Unregistered mutation point: {caller_module}.{caller_function}',
                caller_module=caller_module,
                caller_function=caller_function,
                operation=operation,
                stack=stack,
                policy_rule='registered_mutation_point_required',
            )
            self._log_violation(violation)
            self._trigger_shutdown(violation)

        # CRITICAL CHECK 3: No forbidden patterns in function name
        for forbidden in self._FORBIDDEN_PATTERNS:
            if forbidden.lower() in caller_function.lower():
                violation = self._create_violation(
                    severity=ViolationSeverity.FATAL,
                    message=f'Forbidden mutation pattern detected: {caller_function}',
                    caller_module=caller_module,
                    caller_function=caller_function,
                    operation=operation,
                    stack=stack,
                    policy_rule='forbidden_pattern_detected',
                )
                self._log_violation(violation)
                self._trigger_shutdown(violation)

    def assert_gateway_active(self, operation: str = 'unknown') -> None:
        '''
        Verify Gateway context is active.
        
        Called at the START of every gateway operation.
        '''
        stack = self._capture_stack()

        if not self._is_in_gateway_context(stack):
            violation = self._create_violation(
                severity=ViolationSeverity.FATAL,
                message='Gateway context NOT active during gateway operation',
                caller_module='unknown',
                caller_function='unknown',
                operation=operation,
                stack=stack,
                policy_rule='gateway_context_must_be_active',
            )
            self._log_violation(violation)
            self._trigger_shutdown(violation)

    def assert_entry_point(self, function_name: str) -> None:
        '''
        Verify function is an allowed entry point.
        '''
        if function_name not in self._ALLOWED_ENTRY:
            stack = self._capture_stack()
            violation = self._create_violation(
                severity=ViolationSeverity.CRITICAL,
                message=f'Not an allowed entry point: {function_name}',
                caller_module='unknown',
                caller_function=function_name,
                operation='entry_point_check',
                stack=stack,
                policy_rule='allowed_entry_point_required',
            )
            self._log_violation(violation)
            self._trigger_shutdown(violation)

    def push_gateway_context(self, module: str) -> None:
        '''Track gateway context entry (for nested calls).'''
        with self._lock:
            self._active_context_modules.add(module)
            self._gateway_depth += 1

    def pop_gateway_context(self, module: str) -> None:
        '''Track gateway context exit.'''
        with self._lock:
            self._active_context_modules.discard(module)
            self._gateway_depth = max(0, self._gateway_depth - 1)

    def is_gateway_context_active(self) -> bool:
        '''Check if gateway context is currently active.'''
        with self._lock:
            return self._gateway_depth > 0

    def get_violations(self) -> list[GuardViolation]:
        '''Return all logged violations.'''
        return list(self._violations_log)

    def get_stats(self) -> dict:
        '''Return guard statistics.'''
        with self._lock:
            return {
                'registered_mutation_points': len(self._mutation_points),
                'total_violations': len(self._violations_log),
                'fatal_violations': sum(1 for v in self._violations_log if v.severity == ViolationSeverity.FATAL),
                'gateway_depth': self._gateway_depth,
                'initialized': self._initialized,
            }

    def get_registered_points(self) -> dict[str, MutationPoint]:
        '''Return all registered mutation points.'''
        return dict(self._mutation_points)

    # ── Internal helpers ────────────────────────────────────────────────────

    def _is_in_gateway_context(self, stack: list[dict]) -> bool:
        '''Check if call stack contains ExecutionGateway.'''
        for frame in stack:
            filename = frame.get('filename', '').lower()
            if 'execution_gateway' in filename or 'executiongateway' in filename:
                return True
        return False

    def _capture_stack(self) -> list[dict]:
        '''Capture current call stack.'''
        frames = []
        for frame_info in traceback.extract_stack():
            frames.append({
                'filename': frame_info.filename,
                'lineno': frame_info.lineno,
                'function': frame_info.name,
            })
        return frames

    def _format_stack(self, stack: list[dict]) -> str:
        '''Format stack as readable string.'''
        lines = []
        for f in stack[-10:]:
            fname = f.get('filename', '?')
            lineno = f.get('lineno', '?')
            func = f.get('function', '?')
            lines.append(f'  {fname}:{lineno} in {func}')
        return '\n'.join(lines)

    def _create_violation(self, severity: ViolationSeverity, message: str,
                          caller_module: str, caller_function: str,
                          operation: str, stack: list[dict],
                          policy_rule: str) -> GuardViolation:
        '''Create a violation record.'''
        top_frame = stack[-1] if stack else {}
        top_fname = top_frame.get('filename', '?')
        top_lineno = top_frame.get('lineno', '?')

        return GuardViolation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity,
            message=message,
            detected_at=f'{top_fname}:{top_lineno}',
            caller_module=caller_module,
            caller_function=caller_function,
            caller_file=top_frame.get('filename', ''),
            caller_line=top_frame.get('lineno', 0),
            stack_snapshot=self._format_stack(stack),
            attempted_operation=operation,
            policy_rule_violated=policy_rule,
        )

    def _log_violation(self, violation: GuardViolation) -> None:
        '''Log violation to internal log.'''
        with self._lock:
            self._violations_log.append(violation)

        # Also print to stderr for visibility
        import sys as _sys
        print(
            f'\n[ExecutionGuardPolicy] VIOLATION ({violation.severity.name}):\n'
            f'  {violation.message}\n'
            f'  File: {violation.caller_file}:{violation.caller_line}\n'
            f'  Rule: {violation.policy_rule_violated}\n'
            f'  Stack:\n{violation.stack_snapshot}\n',
            file=_sys.stderr
        )

    def _trigger_shutdown(self, violation: GuardViolation) -> None:
        '''
        Trigger immediate system shutdown.
        
        This is UNRECOVERABLE. No exceptions, no fallbacks.
        '''
        raise SystemShutdown(
            f'\n'
            f'========================================\n'
            f'  ATOMFEDERATION-OS SYSTEM SHUTDOWN\n'
            f'  Violation: {violation.message}\n'
            f'  Severity: {violation.severity.name}\n'
            f'  Rule: {violation.policy_rule_violated}\n'
            f'========================================\n'
            f'\n'
            f'The system has detected a CRITICAL safety violation that cannot\n'
            f'be recovered. All mutations MUST flow exclusively through\n'
            f'ExecutionGateway.execute(). Any bypass attempt leads to\n'
            f'immediate system termination.\n'
            f'\n'
            f'Detected at: {violation.detected_at}\n'
            f'Operation: {violation.attempted_operation}\n'
            f'\n'
            f'Full stack trace:\n{violation.stack_snapshot}\n',
            violation=violation
        )
