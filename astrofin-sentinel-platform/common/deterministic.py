"""
Local determinism primitives (formerly acos_contracts.deterministic).
Self-contained — no external package dependency.
"""
from __future__ import annotations

import random
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone

# --- ContextVar for per-thread determinism ---
_current_context: ContextVar = ContextVar("_deterministic_ctx", default=None)


@dataclass
class DeterministicContext:
    seed: int = 42
    clock_speed: float = 1.0
    start_time: float = field(default_factory=time.time)

    def now(self) -> float:
        elapsed = (time.time() - self.start_time) * self.clock_speed
        return self.start_time + elapsed


def set_current_context(ctx: DeterministicContext | None) -> None:
    _current_context.set(ctx)


def reset_current_context() -> None:
    _current_context.set(None)


def _get_context() -> DeterministicContext | None:
    return _current_context.get()


# --- Clock ---
class DeterministicClockImpl:
    def utc_now(self) -> datetime:
        ctx = _get_context()
        if ctx is not None:
            return datetime.fromtimestamp(ctx.now(), tz=timezone.utc)
        return datetime.now(timezone.utc)


def utc_now_deterministic() -> datetime:
    return DeterministicClockImpl().utc_now()


# --- RNG ---
class DeterministicRNG:
    def __init__(self, seed: int | None = None):
        ctx = _get_context()
        self._rng = random.Random(seed if seed is not None else (ctx.seed if ctx else 42))

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self._rng.uniform(a, b)


# --- UUID ---
def uuid4_deterministic() -> uuid.UUID:
    ctx = _get_context()
    rng = random.Random(ctx.seed if ctx else 42)
    return uuid.UUID(int=rng.getrandbits(128), version=4)


def deterministic_uuid(seed: int = 42) -> uuid.UUID:
    return uuid.UUID(int=random.Random(seed).getrandbits(128), version=4)


# --- Entropy ---
def require_entropy_source() -> None:
    """
    No-op in local mode — entopy is always available via os.urandom.
    """
    pass


__all__ = [
    "DeterministicClockImpl",
    "DeterministicContext",
    "DeterministicRNG",
    "deterministic_uuid",
    "require_entropy_source",
    "reset_current_context",
    "set_current_context",
    "utc_now_deterministic",
    "uuid4_deterministic",
]
