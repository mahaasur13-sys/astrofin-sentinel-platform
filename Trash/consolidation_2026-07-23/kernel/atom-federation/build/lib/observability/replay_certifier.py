# observability/replay_certifier.py — NEW
# ATOM-META-RL-022 P2 — Replay Certification Mode

import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional


class CertificationStatus(Enum):
    PENDING = auto()   # not yet certified
    CERTIFIED = auto() # runtime == replay
    FAILED = auto()    # runtime != replay


@dataclass
class CertificationResult:
    tick: int
    status: CertificationStatus
    runtime_output: Any = None
    replay_output: Any = None
    divergence: list[dict] = field(default_factory=list)


@dataclass
class DivergencePoint:
    path: str
    runtime_value: Any
    replay_value: Any

    def to_dict(self) -> dict:
        return {
            'path': self.path,
            'runtime_value': self.runtime_value,
            'replay_value': self.replay_value,
        }


@dataclass
class CertificationReport:
    total: int
    certified: int
    failed: int
    pending: int
    results: list[CertificationResult]

    def is_full_certification(self) -> bool:
        return self.failed == 0 and self.pending == 0 and self.certified == self.total

    def to_dict(self) -> dict:
        return {
            'total': self.total,
            'certified': self.certified,
            'failed': self.failed,
            'pending': self.pending,
            'full_certification': self.is_full_certification(),
            'results': [
                {
                    'tick': r.tick,
                    'status': r.status.name,
                    'divergence': r.divergence,
                }
                for r in self.results
            ],
        }


# Global flag — disabled by default, enable for certification testing
REPLAY_CERTIFICATION_MODE: bool = False


class ReplayCertificationMode:
    r'''
    Verifies that runtime execution and replay produce identical output.

    Usage:
        # Enable certification mode
        ReplayCertificationMode.set_enabled(True)

        # During runtime:
        certifier = ReplayCertificationMode()
        certifier.record_runtime(tick=42, output={"result": "value"})

        # During replay:
        certifier.record_replay(tick=42, output={"result": "value"})

        # After both complete:
        result = certifier.certify_tick(42)
        report = certifier.certify_all()

    Theorem:
        REPLAY_CERTIFICATION_MODE = True
          -> for all ticks: Runtime(tick) == Replay(tick)
          -> system is replay-certifiable
          -> deterministic under distributed execution verified
    '''

    _instance: Optional['ReplayCertificationMode'] = None
    _enabled: bool = False
    _lock = threading.RLock()

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        '''Enable or disable replay certification mode.'''
        with cls._lock:
            cls._enabled = enabled

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._enabled

    @classmethod
    def get_instance(cls) -> 'ReplayCertificationMode':
        '''Get singleton instance.'''
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ReplayCertificationMode()
        return cls._instance

    def __init__(self):
        self._runtime_output: dict[int, Any] = {}
        self._replay_output: dict[int, Any] = {}
        self._certified_ticks: set[int] = set()
        self._results: list[CertificationResult] = []
        self._lock = threading.RLock()

    def record_runtime(self, tick: int, output: Any) -> None:
        '''Record runtime output at tick.'''
        if not self._enabled:
            return
        with self._lock:
            self._runtime_output[tick] = output

    def record_replay(self, tick: int, output: Any) -> None:
        '''Record replay output at tick.'''
        if not self._enabled:
            return
        with self._lock:
            self._replay_output[tick] = output

    def certify_tick(self, tick: int) -> CertificationResult:
        '''Certify a single tick.'''
        with self._lock:
            if tick not in self._runtime_output or tick not in self._replay_output:
                result = CertificationResult(tick=tick, status=CertificationStatus.PENDING)
                self._results.append(result)
                return result

            runtime = self._runtime_output[tick]
            replay = self._replay_output[tick]

            if self._deep_equal(runtime, replay):
                self._certified_ticks.add(tick)
                result = CertificationResult(
                    tick=tick,
                    status=CertificationStatus.CERTIFIED,
                    runtime_output=runtime,
                    replay_output=replay
                )
            else:
                divergence = self._find_divergence(runtime, replay)
                result = CertificationResult(
                    tick=tick,
                    status=CertificationStatus.FAILED,
                    runtime_output=runtime,
                    replay_output=replay,
                    divergence=[d.to_dict() for d in divergence]
                )

            self._results.append(result)
            return result

    def certify_all(self) -> CertificationReport:
        '''Certify all ticks that have both runtime and replay outputs.'''
        with self._lock:
            ticks = set(self._runtime_output.keys()) & set(self._replay_output.keys())
            results = []
            for tick in sorted(ticks):
                results.append(self.certify_tick(tick))

            certified = sum(1 for r in results if r.status == CertificationStatus.CERTIFIED)
            failed = sum(1 for r in results if r.status == CertificationStatus.FAILED)
            pending = sum(1 for r in results if r.status == CertificationStatus.PENDING)

            return CertificationReport(
                total=len(results),
                certified=certified,
                failed=failed,
                pending=pending,
                results=results
            )

    def get_certified_ticks(self) -> list[int]:
        with self._lock:
            return sorted(self._certified_ticks)

    def is_tick_certified(self, tick: int) -> bool:
        return tick in self._certified_ticks

    def reset(self) -> None:
        '''Reset all certification state. For testing.'''
        with self._lock:
            self._runtime_output.clear()
            self._replay_output.clear()
            self._certified_ticks.clear()
            self._results.clear()

    # ── Deep equality and divergence detection ───────────────────────────

    @staticmethod
    def _deep_equal(a: Any, b: Any) -> bool:
        '''
        Deterministic deep equality.
        No id(), no memory addresses, no time in comparison.
        '''
        if type(a) != type(b):
            return False

        if isinstance(a, dict):
            if set(a.keys()) != set(b.keys()):
                return False
            return all(ReplayCertificationMode._deep_equal(a[k], b[k]) for k in a)

        if isinstance(a, list):
            if len(a) != len(b):
                return False
            return all(ReplayCertificationMode._deep_equal(a[i], b[i]) for i in range(len(a)))

        if isinstance(a, float):
            # Float comparison with tolerance
            return abs(a - b) < 1e-9

        return a == b

    @staticmethod
    def _find_divergence(a: Any, b: Any, path: str = '') -> list[DivergencePoint]:
        '''
        Find all divergence points between two structures.
        Traverses both structures recursively to find exact mismatch locations.
        '''
        divergences = []

        if type(a) != type(b):
            divergences.append(DivergencePoint(
                path=path or '<root>',
                runtime_value=a,
                replay_value=b
            ))
            return divergences

        if isinstance(a, dict):
            all_keys = set(a.keys()) | set(b.keys())
            for k in sorted(all_keys):
                sub_a = a.get(k)
                sub_b = b.get(k)
                sub_path = f'{path}.{k}' if path else k
                if not ReplayCertificationMode._deep_equal(sub_a, sub_b):
                    divergences.extend(
                        ReplayCertificationMode._find_divergence(sub_a, sub_b, sub_path)
                    )
            return divergences

        if isinstance(a, list):
            max_len = max(len(a), len(b))
            for i in range(max_len):
                sub_a = a[i] if i < len(a) else None
                sub_b = b[i] if i < len(b) else None
                sub_path = f'{path}[{i}]'
                if not ReplayCertificationMode._deep_equal(sub_a, sub_b):
                    divergences.extend(
                        ReplayCertificationMode._find_divergence(sub_a, sub_b, sub_path)
                    )
            return divergences

        if a != b:
            divergences.append(DivergencePoint(
                path=path or '<root>',
                runtime_value=a,
                replay_value=b
            ))

        return divergences


# ── CertificationContext ──────────────────────────────────────────────────────

class CertificationContext:
    r'''
    Scoped certification context for a single execution/replay cycle.

    Usage:
        with CertificationContext('node-1', tick=42) as ctx:
            ctx.record(output)
        result = ctx.get_result()
    '''

    def __init__(self, node_id: str, tick: int):
        self.node_id = node_id
        self.tick = tick
        self._output: Any | None = None
        self._certifier = ReplayCertificationMode.get_instance()

    def __enter__(self) -> 'CertificationContext':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass  # Output recorded separately via record()

    def record_output(self, output: Any) -> None:
        self._output = output

    def is_runtime(self) -> bool:
        '''Override in subclasses or pass context flag.'''
        return True


def certify_runtime_output(tick: int, output: Any) -> None:
    '''Convenience function to record runtime output.'''
    if REPLAY_CERTIFICATION_MODE:
        certifier = ReplayCertificationMode.get_instance()
        certifier.record_runtime(tick, output)


def certify_replay_output(tick: int, output: Any) -> None:
    '''Convenience function to record replay output.'''
    if REPLAY_CERTIFICATION_MODE:
        certifier = ReplayCertificationMode.get_instance()
        certifier.record_replay(tick, output)
