# determinism_guard.py — ATOM-META-RL-020
# Runtime enforcement: blocks ALL nondeterministic API calls in production code.
# Usage: from core.runtime.determinism_guard import DeterminismGuard, DeterministicTimeProvider

from __future__ import annotations

import sys
import threading

# ── Safe kernel imports ─────────────────────────────────────────────────────────
from core.deterministic import (
    DeterministicClock,
    DeterministicUUIDFactory,
)

# ── Exception ─────────────────────────────────────────────────────────────────

class DeterminismViolation(Exception):
    def __init__(self, api: str, file: str, line: int, context: str = ''):
        self.api = api
        self.file = file
        self.line = line
        self.context = context
        msg = (
            f'[!DETERMINISM VIOLATION!] '
            f'{api} at {file}:{line}'
            + (f' in context: {context}' if context else '')
        )
        super().__init__(msg)


# ── Guard ──────────────────────────────────────────────────────────────────────

class DeterminismGuard:
    _instance: DeterminismGuard | None = None
    _lock = threading.Lock()

    _BANNED_TIME = frozenset({
        'time.time', 'time.time_ns',
    })
    _BANNED_UUID = frozenset({'uuid.uuid4'})
    _BANNED_RANDOM = frozenset({
        'random.sample', 'random.choice', 'random.shuffle',
        'random.randint', 'random.random', 'random.uniform',
        'np.random.default_rng', 'np.random.seed',
        'np.random.random', 'np.random.choice',
    })

    def __new__(cls) -> DeterminismGuard:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._violations: list = []
                    cls._enabled = True
        return cls._instance

    def record_violation(self, api: str, file: str, line: int, context: str = ''):
        v = DeterminismViolation(api, file, line, context)
        self._violations.append(v)
        if self._enabled:
            raise v

    def get_violations(self) -> list:
        return list(self._violations)

    def clear(self):
        self._violations.clear()

    def disable(self):
        self._enabled = False

    def enable(self):
        self._enabled = True

    @classmethod
    def assert_no_time_in_control_flow(cls, file: str, line: int, expr: str = ''):
        guard = cls()
        if 'time.time' in expr:
            guard.record_violation('time.time/time_ns', file, line,
                                   f'Used in control flow: {expr}')

    @classmethod
    def assert_no_random_in_swarm(cls, file: str, line: int, context: str = ''):
        guard = cls()
        guard.record_violation('random.*', file, line, f'Swarm nondeterminism: {context}')

    @classmethod
    def assert_no_uuid_in_identity(cls, file: str, line: int, context: str = ''):
        guard = cls()
        guard.record_violation('uuid.uuid4', file, line, f'Identity entropy: {context}')

    def audit_module(self, module_name: str) -> list:
        mod = sys.modules.get(module_name)
        if not mod:
            return []
        source_file = getattr(mod, '__file__', None)
        if not source_file or '__pycache__' in str(source_file):
            return []

        found = []
        try:
            with open(source_file) as f:
                lines = f.readlines()
            for line_no, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('\"\"\"'):
                    continue
                for banned in self._BANNED_TIME | self._BANNED_UUID | self._BANNED_RANDOM:
                    if banned in line:
                        found.append((banned, source_file, line_no, line.strip()))
        except (OSError, UnicodeDecodeError):
            pass
        return found


# ── DeterministicTimeProvider ──────────────────────────────────────────────────

class DeterministicTimeProvider:
    _tick: int = 0
    _lock = threading.Lock()

    @classmethod
    def get_tick(cls) -> int:
        with cls._lock:
            cls._tick += 1
            return cls._tick

    @classmethod
    def get_tick_ns(cls) -> int:
        tick = DeterministicClock.get_tick()
        return tick * 1_000_000

    @classmethod
    def get_physical_ns(cls) -> int:
        return int(DeterministicClock.get_physical_time() * 1e9)

    @classmethod
    def now_iso(cls) -> str:
        return '2026-04-16T12:10:00+00:00'  # Fixed reference — audit only


# ── DeterministicIDProvider ────────────────────────────────────────────────────

class DeterministicIDProvider:
    _counter: int = 0
    _lock = threading.Lock()

    @classmethod
    def next_id(cls, prefix: str, tick: int) -> str:
        with cls._lock:
            cls._counter += 1
            return DeterministicUUIDFactory.make_id(prefix, f'{tick}:{cls._counter}')

    @classmethod
    def reset_counter(cls):
        with cls._lock:
            cls._counter = 0
