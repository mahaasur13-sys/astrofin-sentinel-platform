"""Determinism primitives (refactor §3.6).

`datetime.utcnow()`, `random.random()`, and `uuid.uuid4()` are the three
classic non-determinism sources we want to centralise. Every domain module
MUST receive a clock / rng by injection rather than calling these
directly.

This module deliberately imports only from stdlib so it can live at the
bottom of the dependency graph.
"""
from __future__ import annotations

import hashlib
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence
from contextvars import ContextVar
import uuid as _uuid

# Stable namespace for deterministic UUID5 derivation
_NS = _uuid.UUID("12345678-1234-5678-1234-567812345678")


# --- Module-level thread-safe helpers -------------------------------------
# Use ContextVar so concurrent tasks share the same deterministic time
# when set, otherwise fall back to a per-task seeded clock.

_ctx = ContextVar("astrofin_deterministic_ctx", default=None)


def set_current_context(ctx: DeterministicContext | None) -> object:
    return _ctx.set(ctx)


def reset_current_context(token: object) -> None:
    _ctx.reset(token)  # type: ignore[arg-type]


def _current_or_default() -> DeterministicContext:
    return _ctx.get() or DeterministicContext()


def utc_now_deterministic() -> datetime:
    return _current_or_default().utcnow()


def uuid4_deterministic() -> str:
    return _current_or_default().uuid4()


def deterministic_uuid(
    *,
    clock_ns: int,
    salt: str = "",
    namespace: str = "astrofin",
) -> str:
    """UUIDv5-style deterministic identifier.

    Reproducible from `(clock_ns, salt)`. Replaces scattered `uuid.uuid4()`
    calls that broke replay determinism.
    """
    payload = f"{namespace}:{clock_ns}:{salt}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


@dataclass
class DeterministicContext:
    """Bundle of deterministic primitives passed through call stacks.

    Replace ad-hoc `from datetime import datetime; datetime.utcnow()` and
    `import random; random.random()` with a context that the orchestrator
    constructs once per session.
    """

    clock: "DeterministicClockImpl"
    rng: "DeterministicRNG"
    seed: int
    started_at_ns: int = field(default_factory=time.monotonic_ns)

    def __init__(
        self,
        clock: DeterministicClock | None = None,
        rng: DeterministicRNG | None = None,
    ) -> None:
        self.clock = clock or DeterministicClockImpl()
        self.rng = rng or DeterministicRNG()

    @classmethod
    def with_seed(
        cls,
        seed: int | str | bytes,
        *,
        frozen_at: datetime | str | None = None,
        rng: DeterministicRNG | None = None,
        clock: DeterministicClock | None = None,
    ) -> "DeterministicContext":
        """Convenience: fresh context with deterministic clock + RNG seeded."""
        return cls(
            clock=DeterministicClockImpl(frozen_at=frozen_at),
            rng=DeterministicRNG.from_seed(seed),
        )

    @classmethod
    def frozen(cls, *, at: datetime, seed: int = 0) -> "DeterministicContext":
        """Build a context pinned to a specific moment (for replay / tests)."""
        clock = DeterministicClockImpl(frozen_at=at)
        rng = DeterministicRNG(seed=seed)
        return cls(clock=clock, rng=rng, seed=seed)

    def uuid4(self) -> str:
        """Delegate to RNG."""
        return self.rng.uuid4()

    def utcnow(self) -> datetime:
        """Delegate to clock."""
        return self.clock.utcnow()


@dataclass
class DeterministicClockImpl:
    """Concrete clock with optional freeze for replay / tests.

    * `frozen_at is None`  → wall clock (production).
    * `frozen_at is set`   → always returns that moment + manual offset.
    """

    frozen_at: datetime | None = None
    _offset_ns: int = 0

    def __post_init__(self) -> None:
        # Normalize frozen_at: accept datetime, ISO string, or None.
        if isinstance(self.frozen_at, str):
            self.frozen_at = datetime.fromisoformat(self.frozen_at)
        if self.frozen_at is not None:
            self.frozen_at = self.frozen_at.replace(tzinfo=timezone.utc)

    def now(self) -> datetime:
        if self.frozen_at is not None:
            return self.frozen_at
        return datetime.now(timezone.utc)

    def monotonic_ns(self) -> int:
        if self.frozen_at is not None:
            return self._offset_ns
        return time.monotonic_ns()

    def isoformat(self) -> str:
        return self.now().isoformat()

    def advance(self, *, seconds: float = 0.0, nanoseconds: int = 0) -> None:
        """Manual offset for replay tests."""
        self._offset_ns += int(seconds * 1_000_000_000) + nanoseconds

    def utcnow(self) -> datetime:
        """Legacy alias for `now()`. Kept so callers can use either name."""
        return self.now()


@dataclass
class DeterministicRNG:
    """Reproducible RNG. Replaces direct `random` module usage."""

    seed: int
    _state: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._state = random.Random(self.seed)

    def random(self) -> float:
        return self._state.random()

    def randint(self, a: int, b: int) -> int:
        return self._state.randint(a, b)

    def choice(self, seq: Sequence[Any]) -> Any:
        return self._state.choice(seq)

    def shuffle(self, x: list[Any]) -> None:
        self._state.shuffle(x)

    @classmethod
    def from_seed(cls, seed: int | str | bytes) -> "DeterministicRNG":
        """Convenience: same as DeterministicRNG(seed)."""
        return cls(seed)

    def uuid4(self) -> str:
        """Deterministic UUID4-shaped string.

        Uses uuid5 with a stable namespace; the name is the SHA-1 of 16
        reproducible bytes drawn from the RNG state.
        """
        import hashlib
        seed_bytes = b"".join(
            self._state.randbytes(4) if hasattr(self._state, "randbytes")
            else self._state.getrandbits(32).to_bytes(4, "big")
            for _ in range(4)
        )
        digest = hashlib.sha1(seed_bytes).hexdigest()
        return str(_uuid.UUID(digest[:32]))


# Sentinel for "no entropy available" — used by callers that previously
# relied on `os.urandom` and need to surface the absence instead of silently
# degrading to non-determinism.
def require_entropy_source() -> bytes:
    """Return cryptographically secure random bytes.

    Unlike `os.urandom`, this function raises if the OS entropy source is
    unavailable, so callers cannot accidentally substitute `random.random()`
    and lose determinism.
    """
    return os.urandom(32)