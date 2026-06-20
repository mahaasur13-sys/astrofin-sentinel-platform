"""Determinism primitives for acos-contracts.

This is a **verbatim copy** of `common/deterministic.py` from
astrofin-sentinel-platform. The split is intentional: in S2 we want
`acos-contracts` to be importable by *any* consumer without a
`common/` on their path.

Long-term, all consumers will depend on `acos-contracts` only.
Until then, `common/deterministic.py` re-exports the same names from
`acos_contracts.deterministic` for backward compatibility.
"""
from __future__ import annotations

import hashlib
import os
import random
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

import uuid as _uuid

# Stable namespace for deterministic UUID5 derivation
_NS = _uuid.UUID("12345678-1234-5678-1234-567812345678")

# --- Module-level thread-safe helpers -------------------------------------
_ctx = ContextVar("astrofin_deterministic_ctx", default=None)


def set_current_context(ctx: "DeterministicContext | None") -> object:
    return _ctx.set(ctx)


def reset_current_context(token: object) -> None:
    _ctx.reset(token)  # type: ignore[arg-type]


def _current_or_default() -> "DeterministicContext":
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
    """UUIDv5-style deterministic identifier (replay-stable)."""
    payload = f"{namespace}:{clock_ns}:{salt}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


class DeterministicContext:
    """Bundle of deterministic primitives passed through call stacks."""

    clock: "DeterministicClockImpl"
    rng: "DeterministicRNG"
    seed: int
    started_at_ns: int = field(default_factory=time.monotonic_ns)

    def __init__(
        self,
        clock: "DeterministicClock | None" = None,
        rng: "DeterministicRNG | None" = None,
        seed: int | None = None,
    ) -> None:
        self.clock = clock or DeterministicClockImpl()
        if rng is None:
            derived_seed = 0 if seed is None else int(seed)
            self.rng = DeterministicRNG(seed=derived_seed)
        else:
            self.rng = rng
        self.seed = 0 if seed is None else int(seed)
        self.started_at_ns = time.monotonic_ns()

    @classmethod
    def with_seed(
        cls,
        seed: int | str | bytes,
        *,
        frozen_at: datetime | str | None = None,
        rng: "DeterministicRNG | None" = None,
        clock: "DeterministicClock | None" = None,
    ) -> "DeterministicContext":
        derived_seed = (
            seed if isinstance(seed, int)
            else DeterministicRNG.from_seed(seed).seed
        )
        return cls(
            clock=clock or DeterministicClockImpl(frozen_at=frozen_at),
            rng=rng or DeterministicRNG.from_seed(seed),
            seed=derived_seed,
        )

    @classmethod
    def frozen(cls, *, at: datetime, seed: int = 0) -> "DeterministicContext":
        clock = DeterministicClockImpl(frozen_at=at)
        rng = DeterministicRNG(seed=seed)
        return cls(clock=clock, rng=rng, seed=seed)

    def uuid4(self) -> str:
        return self.rng.uuid4()

    def utcnow(self) -> datetime:
        return self.clock.utcnow()


@dataclass
class DeterministicClockImpl:
    """Concrete clock with optional freeze for replay / tests."""

    frozen_at: datetime | None = None
    _offset_ns: int = 0

    def __post_init__(self) -> None:
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
        self._offset_ns += int(seconds * 1_000_000_000) + nanoseconds

    def utcnow(self) -> datetime:
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
        return cls(seed)

    def uuid4(self) -> str:
        seed_bytes = b"".join(
            self._state.randbytes(4) if hasattr(self._state, "randbytes")
            else self._state.getrandbits(32).to_bytes(4, "big")
            for _ in range(4)
        )
        digest = hashlib.sha1(seed_bytes).hexdigest()
        return str(_uuid.UUID(digest[:32]))


# Protocol name (matches the original in common/interfaces.py)
# DeterministicClock Protocol lives in interfaces.py


def require_entropy_source() -> bytes:
    """Return 32 cryptographically-secure random bytes, or raise."""
    return os.urandom(32)
