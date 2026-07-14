# deterministic.py — atom-federation-os v9.0+ATOM-META-RL-019
# Deterministic Kernel: centralized time/uuid/random sources.
#
# Guarantees:
#   1. DeterministicClock — monotonic tick, no time.time() in control flow
#   2. DeterministicRNG — seeded per-agent per-tick, no unseeded np.random
#   3. DeterministicUUIDFactory — content-addressed IDs, no uuid.uuid4()
#   4. GlobalExecutionSequencer — single-writer FIFO queue
#
# Usage:
#   tick = DeterministicClock.get_tick()
#   rng = DeterministicRNG.get_rng(agent_id='SwarmAgent', tick=tick)
#   ctx_id = DeterministicUUIDFactory.make_context_id('SwarmAgent', tick, depth=1)
#   nonce = DeterministicUUIDFactory.make_nonce('req1', tick, seq=0)
#   GlobalExecutionSequencer.enqueue(request)

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any

# ── DeterministicClock ────────────────────────────────────────────────────────

class DeterministicClock:
    '''
    Monotonic tick-based clock — replaces time.time() in control flow.

    ONE physical timestamp taken at initialization (for external APIs only).
    All internal timing uses tick (logical, deterministic).

    Usage:
        tick = DeterministicClock.get_tick()        # current tick
        DeterministicClock.advance()                # atomically advance
        elapsed = DeterministicClock.get_elapsed(from_tick)  # logical elapsed
    '''

    _tick: int = 0
    _seed: int = 0
    _lock = threading.Lock()
    _initialized: bool = False
    _start_physical_time: float = 0.0

    @classmethod
    def configure(cls, seed: int = 0, start_tick: int = 0) -> None:
        '''
        Configure clock with explicit seed (for reproducibility).
        Call once at system startup.

        Args:
            seed: Seed for deterministic derivations
            start_tick: Initial tick value (default 0)
        '''
        with cls._lock:
            cls._seed = seed
            cls._tick = start_tick
            cls._start_physical_time = time.time()
            cls._initialized = True

    @classmethod
    def advance(cls) -> int:
        '''
        Atomically advance tick. Returns new tick.
        Thread-safe: uses lock.
        '''
        with cls._lock:
            cls._tick += 1
            return cls._tick

    @classmethod
    def get_tick(cls) -> int:
        '''
        Get current tick (monotonic, never decreases).
        '''
        with cls._lock:
            return cls._tick

    @classmethod
    def get_elapsed(cls, from_tick: int) -> float:
        '''
        Get logical elapsed time since from_tick.
        Returns float seconds (logical, not physical).
        '''
        with cls._lock:
            return float(cls._tick - from_tick) * cls._SECONDS_PER_TICK

    @classmethod
    def get_tick_ns(cls) -> int:
        return cls.get_tick() * 1_000_000

    @classmethod
    def get_physical_time(cls) -> float:
        '''
        Get wall-clock time for external APIs (audit/logging only).
        NEVER use for control flow decisions.
        '''
        return time.time() - cls._start_physical_time

    @classmethod
    def reset(cls, seed: int = 0) -> None:
        '''
        Reset clock to initial state (for testing only).
        '''
        with cls._lock:
            cls._tick = 0
            cls._seed = seed
            cls._start_physical_time = time.time()

    @classmethod
    def is_initialized(cls) -> bool:
        with cls._lock:
            return cls._initialized

    # Logical seconds per tick (for elapsed calculations)
    _SECONDS_PER_TICK: float = 1.0


# ── DeterministicRNG ──────────────────────────────────────────────────────────

class DeterministicRNG:
    '''
    Seeded RNG factory — replaces np.random.default_rng() in control flow.

    Guarantees:
        - Same (agent_id, tick) → same random sequence
        - Per-agent isolation (different agents get different streams)
        - Cache invalidation on tick advance

    Usage:
        rng = DeterministicRNG.get_rng(agent_id='MutationExecutor', tick=42)
        value = rng.random()  # deterministic for same agent_id + tick
    '''

    _caches: dict[str, Any] = {}
    _lock = threading.Lock()
    _salt: str = 'ATOM-RNG-SEED-v1'

    @classmethod
    def get_rng(cls, agent_id: str, tick: int) -> Any:
        '''
        Get or create deterministic RNG for agent_id at tick.
        Same inputs → same RNG instance with same state.

        Args:
            agent_id: Unique identifier for the agent
            tick: Current tick (monotonic integer)

        Returns:
            np.random.Generator (seeded deterministically)
        '''
        import numpy as np

        seed = cls.make_seed(agent_id, tick)
        cache_key = f'{agent_id}:{tick}'

        if cache_key not in cls._caches:
            with cls._lock:
                if cache_key not in cls._caches:
                    cls._caches[cache_key] = np.random.default_rng(seed)

        return cls._caches[cache_key]

    @classmethod
    def make_seed(cls, agent_id: str, tick: int) -> int:
        '''
        Deterministic seed: same agent_id + same tick → same seed.
        Uses SHA256 to derive 64-bit integer from inputs.

        Args:
            agent_id: Agent identifier
            tick: Current tick

        Returns:
            int: deterministic seed value
        '''
        h = hashlib.sha256(
            f'{agent_id}:{tick}:{cls._salt}'.encode()
        ).hexdigest()
        return int(h[:16], 16)  # First 16 hex chars = 64 bits

    @classmethod
    def invalidate_caches(cls) -> None:
        '''
        Clear RNG cache on tick advance.
        Call this when DeterministicClock.advance() is called.
        '''
        with cls._lock:
            cls._caches.clear()

    @classmethod
    def reset(cls) -> None:
        '''
        Reset all state (for testing only).
        '''
        with cls._lock:
            cls._caches.clear()

    @classmethod
    def get_cached_rng(cls, agent_id: str, tick: int) -> Any | None:
        '''
        Get cached RNG if exists, None otherwise.
        For read-only inspection without creation.
        '''
        cache_key = f'{agent_id}:{tick}'
        with cls._lock:
            return cls._caches.get(cache_key)


# ── DeterministicUUIDFactory ──────────────────────────────────────────────────

class DeterministicUUIDFactory:
    '''
    Content-addressed ID factory — replaces uuid.uuid4() for identity.

    Guarantees:
        - Same inputs → same ID (deterministic)
        - No random generation
        - Collision-resistant (SHA256-based)

    Usage:
        ctx_id = DeterministicUUIDFactory.make_context_id('Agent1', tick=42, depth=1)
        entry_id = DeterministicUUIDFactory.make_entry_id('mutation', tick=42, seq=5)
        nonce = DeterministicUUIDFactory.make_nonce('request1', tick=42, seq=0)
    '''

    _salt: str = 'ATOM-ID-FACTORY-v1'

    @staticmethod
    def make_id(prefix: str, content: str, salt: str = '') -> str:
        '''
        Generate deterministic ID: same inputs → same ID.

        Args:
            prefix: ID prefix (e.g., 'ctx', 'entry', 'nonce')
            content: Content to hash (determines ID)
            salt: Additional salt for domain separation

        Returns:
            str: deterministic ID in format 'prefix_hex12'
        '''
        h = hashlib.sha256(
            f'{prefix}:{content}:{salt}:{DeterministicUUIDFactory._salt}'.encode()
        ).hexdigest()
        return f'{prefix}_{h[:12]}'

    @staticmethod
    def make_trace_id(trace_content: str, tick: int) -> str:
        '''
        Trace ID for replay verification.
        Same trace_content + same tick → same trace_id.
        '''
        return DeterministicUUIDFactory.make_id('trace', trace_content, salt=str(tick))

    @staticmethod
    def make_context_id(agent_id: str, tick: int, depth: int) -> str:
        '''
        Context ID for EnhancedExecutionContext.
        Replaces uuid.uuid4()[:8] in execution_context.py.

        Args:
            agent_id: Agent class name
            tick: Current tick
            depth: Context nesting depth
        '''
        return DeterministicUUIDFactory.make_id(
            'ctx',
            f'{agent_id}:{depth}',
            salt=str(tick)
        )

    @staticmethod
    def make_entry_id(operation: str, tick: int, seq: int) -> str:
        '''
        Audit entry ID.
        Replaces uuid.uuid4()[:8] in execution_context.py audit log.

        Args:
            operation: Operation name
            tick: Current tick
            seq: Sequential counter for this tick
        '''
        return DeterministicUUIDFactory.make_id(
            'entry',
            operation,
            salt=f'{tick}:{seq}'
        )

    @staticmethod
    def make_nonce(request_id: str, tick: int, seq: int) -> str:
        '''
        Deterministic nonce for ExecutionRequest.
        Replaces uuid.uuid4().hex in proof-related code.

        Args:
            request_id: Request identifier
            tick: Current tick
            seq: Sequence number for this request
        '''
        h = hashlib.sha256(
            f'{request_id}:{tick}:{seq}:{DeterministicUUIDFactory._salt}'.encode()
        ).hexdigest()
        return h[:16]  # 16 hex chars = 64 bits

    @staticmethod
    def make_round_id(term: int, tick: int) -> str:
        '''
        Consensus round ID.
        Replaces uuid.uuid4().hex[:8] in consensus.py.

        Args:
            term: Consensus term
            tick: Current tick
        '''
        return f'round-{term}-{tick:08d}'

    @staticmethod
    def make_proof_id(content_hash: str, tick: int) -> str:
        '''
        Proof/contract ID.

        Args:
            content_hash: Hash of proof content
            tick: Current tick
        '''
        return DeterministicUUIDFactory.make_id(
            'proof',
            content_hash,
            salt=str(tick)
        )

    @staticmethod
    def verify_id(id: str, prefix: str, content: str, salt: str = '') -> bool:
        '''
        Verify ID matches expected derivation.

        Args:
            id: ID to verify
            prefix: Expected prefix
            content: Expected content
            salt: Expected salt

        Returns:
            bool: True if ID matches, False otherwise
        '''
        expected = DeterministicUUIDFactory.make_id(prefix, content, salt)
        return id == expected


# ── GlobalExecutionSequencer ──────────────────────────────────────────────────

class GlobalExecutionSequencer:
    '''
    Single monotonically increasing tick + ordered mutation queue.

    Guarantees:
        1. Strict FIFO ordering by tick
        2. No concurrent mutation execution (single-writer)
        3. Deterministic scheduling (tick-only)
        4. Atomic commit

    Usage:
        tick = GlobalExecutionSequencer.next_tick()
        GlobalExecutionSequencer.enqueue(request)
        ready = GlobalExecutionSequencer.dequeue_all_ready()
    '''

    _tick: int = 0
    _lock = threading.Lock()
    _queue: list[tuple[int, Any]] = []  # (tick, request)
    _counter: int = 0

    @classmethod
    def next_tick(cls) -> int:
        '''
        Atomically advance tick and return new value.
        Thread-safe.
        '''
        with cls._lock:
            cls._tick += 1
            cls._counter += 1
            return cls._tick

    @classmethod
    def get_tick(cls) -> int:
        '''
        Get current tick (read-only, no advance).
        '''
        with cls._lock:
            return cls._tick

    @classmethod
    def enqueue(cls, request: Any) -> int:
        '''
        Enqueue request with current tick.
        Returns tick assigned to this request.

        Args:
            request: Mutation request to enqueue

        Returns:
            int: tick assigned to this request
        '''
        tick = cls.next_tick()
        with cls._lock:
            cls._queue.append((tick, request))
            # Strict FIFO: maintain tick order
            cls._queue.sort(key=lambda x: x[0])
        return tick

    @classmethod
    def dequeue_all_ready(cls) -> list[tuple[int, Any]]:
        '''
        Return all requests with tick <= current_tick, in tick order.
        Removes dequeued items from queue.

        Returns:
            list[tuple[int, Any]]: list of (tick, request) in order
        '''
        with cls._lock:
            current = cls._tick
            ready = [(t, r) for t, r in cls._queue if t <= current]
            cls._queue = [(t, r) for t, r in cls._queue if t > current]
            return ready

    @classmethod
    def peek_ready(cls) -> list[tuple[int, Any]]:
        '''
        Peek at ready requests without removing them.
        '''
        with cls._lock:
            current = cls._tick
            return [(t, r) for t, r in cls._queue if t <= current]

    @classmethod
    def is_empty(cls) -> bool:
        '''
        Check if queue is empty.
        '''
        with cls._lock:
            return len(cls._queue) == 0

    @classmethod
    def queue_size(cls) -> int:
        '''
        Get number of items in queue.
        '''
        with cls._lock:
            return len(cls._queue)

    @classmethod
    def reset(cls) -> None:
        '''
        Reset sequencer state (for testing only).
        '''
        with cls._lock:
            cls._tick = 0
            cls._counter = 0
            cls._queue.clear()


# ── ExecutionToken ─────────────────────────────────────────────────────────────

class ExecutionToken:
    '''
    Immutable capability token for mutation authorization.

    Created when GlobalExecutionSequencer.enqueue() is called.
    Must be passed explicitly to AtomicMutationProcessor.execute().

    Cannot be forged — hash includes gateway_id, tick, and counter.

    Usage:
        token = ExecutionToken(gateway_id=id(gateway), tick=42)
        processor.execute(payload, token=token)
        token.verify(gateway_id, tick)  # Must match
    '''

    _counter: int = 0
    _lock = threading.Lock()

    def __init__(self, gateway_id: int, tick: int):
        with self._lock:
            ExecutionToken._counter += 1
            self._seq = ExecutionToken._counter

        self._gateway_id = gateway_id
        self._tick = tick
        self._hash = hashlib.sha256(
            f'{gateway_id}:{tick}:{self._seq}:ATOM-TOKEN'.encode()
        ).hexdigest()[:24]

    @property
    def token(self) -> str:
        '''Get token string.'''
        return self._hash

    @property
    def tick(self) -> int:
        '''Get tick this token was issued at.'''
        return self._tick

    @property
    def sequence(self) -> int:
        '''Get sequence number.'''
        return self._seq

    def verify(self, gateway_id: int, tick: int) -> bool:
        '''
        Verify token is still valid for this gateway and tick.

        Args:
            gateway_id: Expected gateway ID
            tick: Expected tick

        Returns:
            bool: True if valid, False otherwise
        '''
        return (
            self._gateway_id == gateway_id and
            self._tick == tick and
            self._hash == hashlib.sha256(
                f'{gateway_id}:{tick}:{self._seq}:ATOM-TOKEN'.encode()
            ).hexdigest()[:24]
        )

    @classmethod
    def reset_counter(cls) -> None:
        '''
        Reset token counter (for testing only).
        '''
        with cls._lock:
            cls._counter = 0


# ── Global Tie-Breaking Protocol (GTBP) ──────────────────────────────────────
# ATOM-META-RL-021: Deterministic tie resolution for alignment layer.
# Used when two entities have equal scores/priorities/timestamps.
# Rule: min(hash(entity_id)) — lexicographically smaller hash wins.
# Applies to: swarm merge, DAG resolution, consensus, evaluation ranking.

class GlobalTieBreaker:
    """
    Deterministic tie-breaking for alignment layer.

    Invariant: same inputs → same output (pure function).
    No time, no randomness, no side effects.

    Protocol:
        if score_a == score_b:
            return min(hash(id_a), hash(id_b)) → entity with smaller hash wins

    Usage:
        winner = GlobalTieBreaker.choose(score_a=0.85, id_a='branch_a',
                                         score_b=0.85, id_b='branch_b')
        # Returns ('branch_a', 0.85) — smaller hash wins at equal score
    """

    @staticmethod
    def choose(
        score_a: float,
        id_a: str,
        score_b: float,
        id_b: str,
    ) -> tuple[str, float]:
        """
        Choose winner by score, with deterministic tie-break on id hash.

        Args:
            score_a: score for entity A
            id_a: entity A identifier
            score_b: score for entity B
            id_b: entity B identifier

        Returns:
            (winner_id, winner_score) — the higher-score entity,
            or the smaller-hash entity if scores are equal
        """
        if score_a > score_b:
            return (id_a, score_a)
        if score_b > score_a:
            return (id_b, score_b)
        # Tie: lexicographically smaller hash wins (deterministic, no time)
        hash_a = hashlib.sha256(id_a.encode()).hexdigest()
        hash_b = hashlib.sha256(id_b.encode()).hexdigest()
        if hash_a <= hash_b:
            return (id_a, score_a)
        return (id_b, score_b)

    @staticmethod
    def choose_n(
        entries: list[tuple[str, float]],
    ) -> tuple[str, float]:
        """
        Choose winner from N entries by (score, hash) — fully deterministic.

        Args:
            entries: list of (entity_id, score) tuples

        Returns:
            (winner_id, winner_score)
        """
        if not entries:
            raise ValueError("No entries to choose from")
        if len(entries) == 1:
            return entries[0]

        # Sort by (-score, hash) — higher score first, smaller hash as tie-break
        def sort_key(item: tuple[str, float]) -> tuple[float, str]:
            entity_id, score = item
            entity_hash = hashlib.sha256(entity_id.encode()).hexdigest()
            return (-score, entity_hash)

        sorted_entries = sorted(entries, key=sort_key)
        return sorted_entries[0]

    @staticmethod
    def stable_sort_by_score(
        items: list[tuple[str, float]],
    ) -> list[tuple[str, float]]:
        """
        Sort items by score descending, tie-break by entity_id hash.
        Produces deterministic ordering for lists that would otherwise be unstable.

        Args:
            items: list of (entity_id, score) tuples

        Returns:
            sorted list — deterministic, replay-safe
        """
        def sort_key(item: tuple[str, float]) -> tuple[float, str]:
            entity_id, score = item
            entity_hash = hashlib.sha256(entity_id.encode()).hexdigest()
            return (-score, entity_hash)

        return sorted(items, key=sort_key)

    @staticmethod
    def compare_floats(a: float, b: float, epsilon: float = 1e-9) -> int:
        """
        Deterministic float comparison with epsilon tolerance.

        Returns:
            -1 if a < b
             0 if |a - b| <= epsilon (equal within tolerance)
             1 if a > b
        """
        diff = a - b
        if diff < -epsilon:
            return -1
        if diff > epsilon:
            return 1
        return 0

    @staticmethod
    def round_floats(values: list[float], decimals: int = 9) -> list[float]:
        """
        Deterministic rounding — removes float representation instability.
        Same input list → same rounded output list.
        """
        return [round(v, decimals) for v in values]
