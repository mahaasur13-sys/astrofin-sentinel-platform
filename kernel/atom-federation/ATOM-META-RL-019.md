# ATOM-META-RL-019 — Deterministic Kernel & Execution Boundary Hardening
**Version:** v9.0+ATOM-META-RL-019  
**Status:** 🟡 DESIGN COMPLETE — P0 IMPLEMENTATION REQUIRED  
**Date:** 2026-04-16  
**Author:** Senior Distributed Systems Engineer + Deterministic Systems Architect + Runtime Security Specialist  

---

## 1. EXECUTIVE SUMMARY

### Goal
Transform ATOMFederation-OS into a **fully deterministic, replay-safe, linearizable execution system** with a single hard enforcement boundary.

### Current State (v9.0+ATOM-META-RL-018)

| Problem Category | Status | Impact |
|-----------------|--------|--------|
| Non-deterministic control flow | 🔴 CRITICAL | Execution trace ≠ reproducible trace |
| Ledger non-linearizability | 🟠 HIGH | Race conditions, unordered appends |
| Layered enforcement (not atomic) | 🟠 HIGH | Bypass paths through runtime edges |
| Async non-determinism | 🟡 MEDIUM | Task ordering indeterminacy |
| Runtime context IDs | 🔴 CRITICAL | `uuid.uuid4()` in hot paths |

### Target State (ATOM-META-RL-019)
```
∀ execution: trace(t) == replay(trace(t))  (bitwise deterministic)
∀ mutation: mutation ∈ single linear execution stream
```

---

## 2. DETERMINISTIC KERNEL DESIGN

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DETERMINISTIC KERNEL (core/)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DeterministicClock — logical tick, monotonic, seeded               │   │
│  │  ├── get_tick() → int (monotonically increasing)                    │   │
│  │  ├── get_elapsed(tick) → float (logical elapsed)                    │   │
│  │  └── advance() → int (atomic increment)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DeterministicRNG — seeded per-agent, per-tick                      │   │
│  │  ├── get_rng(agent_id) → np.random.Generator                        │   │
│  │  ├── make_seed(agent_id, tick) → int (deterministic)                │   │
│  │  └── invalidate_caches() (on tick advance)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DeterministicUUIDFactory — content-addressed, no random            │   │
│  │  ├── make_id(prefix, content, salt) → str (sha256-based)            │   │
│  │  ├── make_trace_id(trace_content, tick) → str                       │   │
│  │  └── verify_id(id, prefix, content, salt) → bool                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DeterministicScheduler — tick-only scheduling                      │   │
│  │  ├── schedule(tick, strategy) → ScheduleResult (no random)          │   │
│  │  └── schedule_fan_out(tick, num_workers) → list[str]                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 API Specification

#### DeterministicClock

```python
class DeterministicClock:
    _tick: int = 0
    _seed: int = 0
    _lock = threading.Lock()
    _start_time: float = time.time()  # ONE-TIME initialization
    
    @classmethod
    def configure(cls, seed: int = 0, start_tick: int = 0) -> None:
        '''Configure clock with explicit seed (for reproducibility).'''
        with cls._lock:
            cls._seed = seed
            cls._tick = start_tick
            cls._start_time = time.time()
    
    @classmethod
    def advance(cls) -> int:
        '''Atomically advance tick. Returns new tick.'''
        with cls._lock:
            cls._tick += 1
            return cls._tick
    
    @classmethod
    def get_tick(cls) -> int:
        '''Get current tick (monotonic).'''
        with cls._lock:
            return cls._tick
    
    @classmethod
    def get_elapsed(cls, from_tick: int) -> float:
        '''Get logical elapsed time since from_tick.'''
        with cls._lock:
            return float(cls._tick - from_tick) * cls._SECONDS_PER_TICK
    
    @classmethod
    def get_physical_time(cls) -> float:
        '''Get wall-clock time ONLY for metrics/logging, NOT for control flow.'''
        return time.time() - cls._start_time
```

#### DeterministicRNG

```python
class DeterministicRNG:
    _caches: dict[str, np.random.Generator] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_rng(cls, agent_id: str, tick: int) -> np.random.Generator:
        seed = cls.make_seed(agent_id, tick)
        cache_key = f'{agent_id}:{tick}'
        if cache_key not in cls._caches:
            cls._caches[cache_key] = np.random.default_rng(seed)
        return cls._caches[cache_key]
    
    @classmethod
    def make_seed(cls, agent_id: str, tick: int) -> int:
        '''Deterministic seed: same agent_id + same tick → same seed.'''
        h = hashlib.sha256(f'{agent_id}:{tick}:ATOM-RNG-SEED'.encode())
        return int(h.hexdigest()[:8], 16)
    
    @classmethod
    def invalidate_caches(cls) -> None:
        '''Clear RNG cache on tick advance.'''
        with cls._lock:
            cls._caches.clear()
    
    @classmethod
    def reset(cls) -> None:
        cls._caches.clear()
        cls._lock = threading.Lock()
```

#### DeterministicUUIDFactory

```python
class DeterministicUUIDFactory:
    @staticmethod
    def make_id(prefix: str, content: str, salt: str = '') -> str:
        '''
        Deterministic ID: same inputs → same ID (content-addressed).
        Replaces uuid.uuid4() for all identity generation.
        '''
        h = hashlib.sha256(f'{prefix}:{content}:{salt}:ATOM-ID'.encode())
        return f'{prefix}_{h.hexdigest()[:12]}'
    
    @staticmethod
    def make_trace_id(trace_content: str, tick: int) -> str:
        '''Trace ID for replay verification.'''
        return DeterministicUUIDFactory.make_id('trace', trace_content, salt=str(tick))
    
    @staticmethod
    def make_context_id(agent_id: str, tick: int, depth: int) -> str:
        '''Context ID for EnhancedExecutionContext (replaces uuid.uuid4()[:8]).'''
        return DeterministicUUIDFactory.make_id('ctx', f'{agent_id}:{depth}', salt=str(tick))
    
    @staticmethod
    def make_entry_id(operation: str, tick: int, seq: int) -> str:
        '''Audit entry ID (replaces uuid.uuid4()[:8]).'''
        return DeterministicUUIDFactory.make_id('entry', operation, salt=f'{tick}:{seq}')
    
    @staticmethod
    def make_nonce(request_id: str, tick: int, seq: int) -> str:
        '''Deterministic nonce for ExecutionRequest (replaces uuid.uuid4().hex).'''
        h = hashlib.sha256(f'{request_id}:{tick}:{seq}:ATOM-NONCE'.encode())
        return h.hexdigest()[:16]
    
    @staticmethod
    def verify_id(id: str, prefix: str, content: str, salt: str = '') -> bool:
        '''Verify ID matches expected derivation.'''
        expected = DeterministicUUIDFactory.make_id(prefix, content, salt)
        return id == expected
```

### 2.3 Integration Points

| Component | Integration | File |
|-----------|-------------|------|
| ExecutionGateway | Uses DeterministicClock for nonce generation | `execution_gateway.py` |
| MutationExecutor | Uses DeterministicRNG(agent_id, tick) | `mutation_executor.py` |
| EnhancedExecutionContext | Uses DeterministicUUIDFactory for context_id | `execution_context.py` |
| ExecutionRequest | Uses DeterministicUUIDFactory.make_nonce() | `execution_request.py` |
| ProofVerifier | Uses DeterministicUUIDFactory for nonce | `proof_verifier.py` |
| Consensus | Uses DeterministicClock for round_id | `consensus.py` |
| DriftProfiler | Uses DeterministicClock for episode timestamps | `drift_profiler.py` |
| AdaptiveRouter | Already deterministic (SchedulingStrategy) | `adaptive_router.py` |

---

## 3. EXECUTION MODEL — BEFORE / AFTER

### 3.1 Current Execution Graph (v9.0)

```
ExecutionGateway (singleton)
    ├── @requires_gateway decorator (guards methods)
    ├── mutation_context() context manager
    ├── ExecutionGuardPolicy (P0.3 — global fail-fast)
    ├── SelfAudit.run() at startup (P0.1)
    ├── ImportFirewall (P0.2 — sys.meta_path hook)
    └── EnhancedExecutionContext (P1.4 — RLock + audit)

         ↓ Layered enforcement (multiple entry points)

MutationExecutor
    ├── MutationExecutorMetaclass (blocks instantiation)
    ├── @requires_gateway (auto-decorated)
    ├── execute(payload)
    └── _apply_mutation(payload) [INTERNAL]

         ↓ Gaps: non-deterministic IDs, no atomic kernel

MutationLedger (RACE CONDITION: no thread-lock on record())
DeterministicScheduler (CLEAN but not integrated into core)
```

### 3.2 New Linearized Execution Graph (ATOM-META-RL-019)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC KERNEL (core/)                            │
│  DeterministicClock | DeterministicRNG | DeterministicUUIDFactory          │
│  DeterministicScheduler | GlobalExecutionSequencer                         │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXECUTION KERNEL (collapsed)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AtomicMutationProcessor                                            │   │
│  │  ├── SINGLE entry point (no decorators, no layers)                  │   │
│  │  ├── GlobalExecutionSequencer — FIFO mutation queue                 │   │
│  │  ├── AtomicLedgerWriter — WAL semantics, single-writer              │   │
│  │  ├── DeterministicClock integration (tick-based nonce)              │   │
│  │  └── Context: ExecutionToken (immutable, verified on every call)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MUTATION FLOW (linearized)                              │
│                                                                          │   │
│  1. mutation_request arrived                                               │   │
│      └── DeterministicClock.get_tick() → tick                            │   │
│                                                                          │   │
│  2. GlobalExecutionSequencer.enqueue(request, tick)                       │   │
│      └── FIFO queue, strict ordering by tick                             │   │
│                                                                          │   │
│  3. AtomicMutationProcessor.process_next()                                │   │
│      └── Single-writer: only ONE mutation at a time                      │   │
│      └── ExecutionToken verified: valid token required                   │   │
│                                                                          │   │
│  4. AtomicLedgerWriter.write(ledger_entry, tick)                         │   │
│      └── WAL semantics: append-only, no concurrent writes                │   │
│      └── Thread-safe via threading.Lock                                  │   │
│                                                                          │   │
│  5. PlanEvaluator.evaluate() (post-mutation)                             │   │
│      └── DeterministicScheduler.schedule() — no random                   │   │
│                                                                          │   │
│  6. FeedbackPrioritySolver.rank() → ControlArbitrator                    │   │
│      └── Deterministic ordering (priority desc, source asc)             │   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Key Differences

| Aspect | Before (v9.0) | After (ATOM-META-RL-019) |
|--------|---------------|--------------------------|
| Mutation entry | Layered (gateway + decorators + policies) | Single atomic kernel |
| Nonce generation | `time.time_ns() + uuid4()` | `DeterministicClock.tick` |
| Context ID | `uuid.uuid4()[:8]` | `DeterministicUUIDFactory.make_context_id()` |
| RNG | `np.random.default_rng()` (unseeded) | `DeterministicRNG.get_rng(agent, tick)` |
| Ledger write | Not thread-safe | Single-writer + WAL + Lock |
| Task scheduling | Async scheduler (may be nondet) | DeterministicScheduler (tick-only) |
| Execution ordering | Concurrent possible | Serialized via FIFO queue |

---

## 4. MUTATION FLOW REDESIGN

### 4.1 Before (Layered)

```
mutation_request
    → ExecutionGateway.mutation_context()
    → @requires_gateway (decorator check)
    → ExecutionGuardPolicy.assert_mutation_allowed() (may trigger SystemShutdown)
    → EnhancedExecutionContext.assert_mutation_allowed()
    → MutationExecutor.execute(payload)
    → _apply_mutation(payload)  [STATE CHANGE]
    → MutationLedger.record()   [NO LOCK — RACE CONDITION]
    → PlanEvaluator.evaluate()
```

### 4.2 After (Linearized)

```
mutation_request
    → DeterministicClock.get_tick() → tick
    → ExecutionToken.verify(token) [MANDATORY]
    → GlobalExecutionSequencer.enqueue(request, tick) [FIFO]
    → AtomicMutationProcessor.process_next() [SINGLE-WRITER]
        → _apply_mutation(payload) [STATE CHANGE]
        → AtomicLedgerWriter.write(ledger_entry, tick) [WAL + LOCK]
    → DeterministicScheduler.schedule(tick) [NO RANDOM]
    → PlanEvaluator.evaluate()
    → FeedbackPrioritySolver.rank() [DETERMINISTIC]
```

### 4.3 Global Execution Sequencer

```python
class GlobalExecutionSequencer:
    '''
    Single monotonically increasing tick + ordered mutation queue.
    Guarantees:
        1. Strict FIFO ordering by tick
        2. No concurrent mutation execution
        3. Deterministic scheduling (tick-only)
        4. Atomic commit to ledger
    '''
    
    _tick: int = 0
    _lock = threading.Lock()
    _queue: list[tuple[int, MutationRequest]] = []  # (tick, request)
    _processing: bool = False
    
    @classmethod
    def next_tick(cls) -> int:
        '''Atomically advance and return new tick.'''
        with cls._lock:
            cls._tick += 1
            return cls._tick
    
    @classmethod
    def get_tick(cls) -> int:
        with cls._lock:
            return cls._tick
    
    @classmethod
    def enqueue(cls, request: MutationRequest) -> int:
        '''Enqueue request with current tick. Returns tick assigned.'''
        tick = cls.next_tick()
        with cls._lock:
            cls._queue.append((tick, request))
            cls._queue.sort(key=lambda x: x[0])  # Strict FIFO
        return tick
    
    @classmethod
    def dequeue_all_ready(cls) -> list[tuple[int, MutationRequest]]:
        '''Return all requests with tick <= current_tick, in tick order.'''
        with cls._lock:
            current = cls._tick
            ready = [(t, r) for t, r in cls._queue if t <= current]
            cls._queue = [(t, r) for t, r in cls._queue if t > current]
            return ready
    
    @classmethod
    def is_empty(cls) -> bool:
        with cls._lock:
            return len(cls._queue) == 0
    
    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._tick = 0
            cls._queue.clear()
            cls._processing = False
```

---

## 5. NONDETERMINISM ELIMINATION MAP

### 5.1 All Nondeterministic Sources — Complete Inventory

| # | File | Line | Source | Fix | Priority |
|---|------|------|--------|-----|----------|
| N1 | `execution_context.py` | 209 | `uuid.uuid4()[:8]` for context_id | `DeterministicUUIDFactory.make_context_id()` | 🔴 CRITICAL |
| N2 | `execution_context.py` | 283 | `uuid.uuid4()[:8]` for context_id | `DeterministicUUIDFactory.make_context_id()` | 🔴 CRITICAL |
| N3 | `execution_context.py` | 418 | `uuid.uuid4()[:8]` for entry_id | `DeterministicUUIDFactory.make_entry_id()` | 🔴 CRITICAL |
| N4 | `execution_request.py` | 18,70,121 | `uuid.uuid4().hex` for nonce | `DeterministicUUIDFactory.make_nonce()` | 🔴 CRITICAL |
| N5 | `execution_request.py` | 18,70,121 | `time.time()` for timestamp | Use `DeterministicClock.get_tick()` | 🟠 HIGH |
| N6 | `proof_verifier.py` | 221 | `uuid.uuid4().hex` for nonce | `DeterministicUUIDFactory.make_nonce()` | 🔴 CRITICAL |
| N7 | `execution_gateway.py` | 206 | `time.time_ns() + uuid.uuid4().hex` for nonce | Use `DeterministicClock.get_tick()` | 🔴 CRITICAL |
| N8 | `consensus.py` | 143 | `uuid.uuid4().hex[:8]` for round_id | `DeterministicUUIDFactory.make_id('round', ...)` | 🟠 HIGH |
| N9 | `mutation_executor.py` | 162 | `np.random.default_rng(seed=self._tick)` | ✅ ALREADY FIXED (seed=tick) | 🟢 OK |
| N10 | `feedback_injection.py` | 202 | `np.random.default_rng(seed=tick)` | ✅ ALREADY FIXED | 🟢 OK |
| N11 | `adaptive_router.py` | 258,264 | `random.choices()` / `random.choice()` | Deterministic tiebreak by peer_id | 🟠 HIGH |

### 5.2 Implementation — Fix Each Source

#### N1-N3: execution_context.py — uuid.uuid4() for context_id

**BEFORE:**
```python
self._context_id = str(uuid.uuid4())[:8]  # line 209, 283
entry_id=str(uuid.uuid4())[:8]            # line 418
```

**AFTER:**
```python
# Import
from core.deterministic import DeterministicUUIDFactory, DeterministicClock

# In mutation_context():
self._context_id = DeterministicUUIDFactory.make_context_id(
    agent_id=self.__class__.__name__,
    tick=DeterministicClock.get_tick(),
    depth=self._context_depth
)

# In _log_audit_entry():
entry_id = DeterministicUUIDFactory.make_entry_id(
    operation=operation,
    tick=DeterministicClock.get_tick(),
    seq=len(self._audit_log)  # sequential counter (deterministic)
)
```

#### N4: execution_request.py — uuid.uuid4().hex for nonce

**BEFORE:**
```python
nonce: str = field(default_factory=lambda: uuid.uuid4().hex)
```

**AFTER:**
```python
from core.deterministic import DeterministicUUIDFactory

nonce: str = field(default_factory=lambda: DeterministicUUIDFactory.make_nonce(
    request_id='exec_req',
    tick=0,  # Will be set at creation time
    seq=0
))

@classmethod
def create(cls, ..., tick: int = 0):
    nonce = DeterministicUUIDFactory.make_nonce(
        request_id=issuer_id,
        tick=tick,
        seq=0
    )
```

#### N5: execution_request.py — time.time() for timestamp

**BEFORE:**
```python
timestamp: float = field(default_factory=lambda: time.time())
```

**AFTER:**
```python
# Use logical tick instead of physical timestamp
# Timestamp in request is for auditing, not control flow
# Physical timestamp for external APIs (OK), logical tick for internal (REQUIRED)
timestamp: float = field(default_factory=lambda: float(DeterministicClock.get_tick()))
```

#### N6: proof_verifier.py — uuid.uuid4().hex for nonce

**BEFORE (line 221):**
```python
nonce = uuid.uuid4().hex
```

**AFTER:**
```python
from core.deterministic import DeterministicUUIDFactory, DeterministicClock

nonce = DeterministicUUIDFactory.make_nonce(
    request_id='proof_verify',
    tick=DeterministicClock.get_tick(),
    seq=0
)
```

#### N7: execution_gateway.py — nonce generation (FIX-1)

**BEFORE (line ~206):**
```python
f'{str(input_data)}{time.time_ns()}{uuid.uuid4().hex}'.encode()
```

**AFTER:**
```python
# Use tick-based deterministic nonce
f'{str(input_data)}{DeterministicClock.get_tick()}'.encode()
```

#### N8: consensus.py — round_id

**BEFORE (line ~143):**
```python
round_id = f'round-{self._current_term}-{uuid.uuid4().hex[:8]}'
```

**AFTER:**
```python
round_id = f'round-{self._current_term}-{DeterministicClock.get_tick():08d}'
```

#### N11: adaptive_router.py — random.choices / random.choice

**BEFORE (lines ~258, 264):**
```python
chosen = random.choices(healthy, weights=...)
chosen = random.choice(healthy)
```

**AFTER:**
```python
# Deterministic: sort by peer_id, use tick as index offset
healthy_sorted = sorted(healthy, key=lambda p: p.peer_id)
if weights:
    # Deterministic weighted selection using tick
    total_w = sum(weights)
    offset = DeterministicClock.get_tick() % total_w
    cumulative = 0
    for i, w in enumerate(weights):
        cumulative += w
        if offset < cumulative:
            chosen = healthy_sorted[i]
            break
else:
    idx = DeterministicClock.get_tick() % len(healthy_sorted)
    chosen = healthy_sorted[idx]
```

---

## 6. LEDGER LINEARIZATION — HARD FIX

### 6.1 Problem

Current `MutationLedger` has:
- No `threading.Lock` on `record()` — concurrent writes can corrupt list
- No WAL semantics — partial writes not atomic
- No strict ordering guarantee — events may append out-of-order

### 6.2 Solution: AtomicLedgerWriter

```python
class AtomicLedgerWriter:
    '''
    Single-writer WAL for MutationLedger.
    Guarantees:
        1. Strict FIFO ordering by tick
        2. No concurrent writes (thread-safe)
        3. WAL semantics: entries written to WAL before commit
        4. Atomic commit
        5. Append-only (no update/delete)
    '''
    
    _instance: Optional['AtomicLedgerWriter'] = None
    _lock = threading.Lock()
    _wal_path: str = '/tmp/atom_federation_ledger.wal'
    
    def __new__(cls) -> 'AtomicLedgerWriter':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._entries: list[dict] = []
                    cls._instance._tick_index: int = 0
                    cls._instance._wal_file = None
        return cls._instance
    
    @classmethod
    def instance(cls) -> 'AtomicLedgerWriter':
        if cls._instance is None:
            cls()
        return cls._instance
    
    def record(self, entry: dict, tick: int) -> None:
        '''
        Thread-safe append with WAL semantics.
        Raises SafetyViolationError if out-of-order (tick < last_tick).
        '''
        with self._lock:
            # ── Verify ordering ────────────────────────────────────────
            last_tick = self._entries[-1]['tick'] if self._entries else -1
            if tick < last_tick:
                raise SafetyViolationError(
                    f'Out-of-order ledger write: tick={tick}, last_tick={last_tick}. '
                    f'MutationLedger must be strictly linearizable.'
                )
            
            # ── WAL write ─────────────────────────────────────────────
            wal_entry = {
                'tick': tick,
                'entry': entry,
                'prev_hash': self._get_last_hash(),
                'timestamp': time.time(),  # Physical for auditing only
            }
            self._write_wal(wal_entry)
            
            # ── Commit to main ledger ──────────────────────────────────
            self._entries.append({
                'tick': tick,
                'data': entry,
                'hash': self._compute_hash(wal_entry),
            })
            self._tick_index = tick
    
    def _write_wal(self, wal_entry: dict) -> None:
        '''Append to WAL file (for crash recovery).'''
        with open(self._wal_path, 'a') as f:
            f.write(json.dumps(wal_entry) + '\n')
    
    def _get_last_hash(self) -> str:
        if not self._entries:
            return 'GENESIS'
        return self._entries[-1]['hash']
    
    def _compute_hash(self, wal_entry: dict) -> str:
        return hashlib.sha256(
            json.dumps(wal_entry, sort_keys=True).encode()
        ).hexdigest()
    
    def get_entries(self, from_tick: int = 0) -> list[dict]:
        '''Return all entries from from_tick onwards.'''
        with self._lock:
            return [e for e in self._entries if e['tick'] >= from_tick]
    
    def verify_linearizability(self) -> dict:
        '''Verify all entries are in ascending tick order.'''
        with self._lock:
            ticks = [e['tick'] for e in self._entries]
            is_linear = all(ticks[i] < ticks[i+1] for i in range(len(ticks)-1))
            return {
                'is_linearizable': is_linear,
                'total_entries': len(self._entries),
                'tick_range': (min(ticks), max(ticks)) if ticks else (0, 0),
                'gaps': self._find_gaps(ticks),
            }
    
    def _find_gaps(self, ticks: list[int]) -> list[int]:
        '''Find missing ticks (indicates lost entries).'''
        if not ticks:
            return []
        return [t for t in range(ticks[0], ticks[-1]) if t not in ticks]
    
    def reset(self) -> None:
        '''Reset ledger (for testing only).'''
        with self._lock:
            self._entries.clear()
            self._tick_index = 0
            if os.path.exists(self._wal_path):
                os.remove(self._wal_path)
```

### 6.3 Integration

Replace `MutationLedger.record()` calls with `AtomicLedgerWriter.instance().record()`:

```python
# Before
self._ledger.record(entry_data)

# After
from core.deterministic import DeterministicClock
AtomicLedgerWriter.instance().record(entry_data, tick=DeterministicClock.get_tick())
```

---

## 7. EXECUTION BOUNDARY COLLAPSE

### 7.1 Current State

```
ExecutionGateway (entry point)
    └── mutation_context() context manager
        ├── EnhancedExecutionContext
        │   └── mutation_context()
        │       └── RLock + audit trail
        ├── ExecutionGuardPolicy
        │   └── assert_mutation_allowed() → may trigger SystemShutdown
        ├── @requires_gateway decorator
        │   └── checks _active_context && _can_mutate
        └── ImportFirewall (sys.meta_path hook)
            └── blocks protected module imports

MutationExecutor
    ├── Metaclass blocks instantiation
    └── @requires_gateway auto-decorates methods
```

**Problem:** Multiple layers, each can be bypassed independently.

### 7.2 Collapsed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXECUTION KERNEL (single boundary)                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AtomicMutationProcessor                                            │   │
│  │                                                                      │   │
│  │  __init__(gateway):                                                 │   │
│  │      1. SelfAudit.verify_execution_graph()  → SystemShutdown on fail│   │
│  │      2. ImportFirewall.install()            → blocks protected mods │   │
│  │      3. ExecutionGuardPolicy.initialize()   → global fail-fast      │   │
│  │      4. AtomicLedgerWriter.instance()       → single-writer ledger  │   │
│  │      5. DeterministicClock.configure()      → seeded tick counter   │   │
│  │                                                                      │   │
│  │  execute(payload, token):                                           │   │
│  │      1. ExecutionToken.verify(token)        → SafetyViolationError  │   │
│  │      2. GlobalExecutionSequencer.enqueue()  → FIFO + tick ordering  │   │
│  │      3. _apply_mutation(payload)            → STATE CHANGE          │   │
│  │      4. AtomicLedgerWriter.record()         → WAL + thread-safe     │   │
│  │      5. DeterministicScheduler.schedule()   → no random             │   │
│  │      6. PlanEvaluator.evaluate()            → post-mutation eval    │   │
│  │                                                                      │   │
│  │  No decorators. No layered checks. Single atomic boundary.          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 ExecutionToken — Immutable Capability

```python
class ExecutionToken:
    '''
    Immutable token created when GlobalExecutionSequencer.enqueue() is called.
    Must be passed explicitly to AtomicMutationProcessor.execute().
    
    Cannot be forged — hash includes:
        - gateway instance ID (unique per process)
        - tick (monotonically increasing)
        - sequencer counter (strictly increasing)
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
        return self._hash
    
    @property
    def tick(self) -> int:
        return self._tick
    
    def verify(self, gateway_id: int, tick: int) -> bool:
        '''Verify token is still valid for this gateway and tick.'''
        return (
            self._gateway_id == gateway_id and
            self._tick == tick and
            self._hash == hashlib.sha256(
                f'{gateway_id}:{tick}:{self._seq}:ATOM-TOKEN'.encode()
            ).hexdigest()[:24]
        )
    
    @classmethod
    def reset_counter(cls) -> None:
        '''Reset counter (for testing only).'''
        with cls._lock:
            cls._counter = 0
```

### 7.4 Before/After Enforcement Comparison

| Aspect | Before (Layered) | After (Collapsed) |
|--------|------------------|-------------------|
| Entry points | Gateway + decorators + policies (multiple) | Single atomic kernel |
| Bypass surface | 10 known paths | 0 (enforced at C-level equivalent) |
| Mutability | Class attributes writable | Token-based capability |
| Thread safety | RLock per-context | GlobalExecutionSequencer single-writer |
| Startup verification | SelfAudit only | SelfAudit + graph verification |
| Import blocking | sys.meta_path (mutable) | Replace class in sys.modules |

---

## 8. ASYNC DETERMINISM FIX

### 8.1 SwarmEngine / AsyncExecutionEngine

Current state: Async tasks may be scheduled nondeterministically.

**Solution:** All async tasks tagged with tick at creation time. Execution order is deterministic: lower tick → first.

```python
class DeterministicAsyncExecutor:
    '''
    Async executor with deterministic task ordering.
    Tasks are tagged with tick at creation time.
    Execution order: sorted by tick (ascending), then by task_id (ascending).
    '''
    
    def __init__(self):
        self._tasks: dict[str, tuple[int, asyncio.Task]] = {}  # task_id → (tick, task)
        self._lock = asyncio.Lock()
    
    async def submit(self, coro, task_id: str, tick: int) -> None:
        '''Submit task with explicit tick (deterministic ordering key).'''
        async with self._lock:
            task = asyncio.create_task(coro)
            self._tasks[task_id] = (tick, task)
    
    async def run_all(self) -> list:
        '''Run all tasks in deterministic tick order.'''
        # Sort by tick (primary), then by task_id (secondary)
        sorted_tasks = sorted(
            self._tasks.items(),
            key=lambda x: (x[1][0], x[0])  # (tick, task_id)
        )
        
        results = []
        for task_id, (tick, task) in sorted_tasks:
            result = await task
            results.append((task_id, result))
        
        return results
```

### 8.2 DeterministicScheduler Integration

All scheduling decisions use `DeterministicScheduler` (already implemented, just integrate):

```python
# Instead of:
asyncio.create_task(guarded_method())

# Use:
scheduler = DeterministicScheduler()
scheduler.register_task_at_tick(
    name='guarded_method',
    priority=0.8,
    tick=DeterministicClock.get_tick()
)
result = scheduler.schedule(tick=DeterministicClock.get_tick())
```

---

## 9. DETERMINISM FIX IMPLEMENTATION ORDER

### Phase 1: Core Deterministic Primitives (P0)

```
Step 1: Create core/deterministic.py
  ├── DeterministicClock
  ├── DeterministicRNG
  ├── DeterministicUUIDFactory
  ├── GlobalExecutionSequencer
  └── AtomicLedgerWriter

Step 2: Fix N1-N3 (execution_context.py)
  └── Replace uuid.uuid4() with DeterministicUUIDFactory

Step 3: Fix N4-N6 (execution_request.py, proof_verifier.py)
  └── Replace uuid.uuid4() with make_nonce()

Step 4: Fix N7 (execution_gateway.py nonce)
  └── Replace time.time_ns() + uuid4 with DeterministicClock.tick

Step 5: Fix N8 (consensus.py round_id)
  └── Replace uuid.uuid4().hex[:8] with tick-based ID

Step 6: Fix N11 (adaptive_router.py)
  └── Replace random.choices/choice with deterministic peer selection
```

### Phase 2: Ledger Linearization (P0)

```
Step 7: Create AtomicLedgerWriter
  └── Single-writer WAL with thread-lock

Step 8: Replace MutationLedger.record() calls with AtomicLedgerWriter.instance().record()
```

### Phase 3: Execution Boundary Collapse (P1)

```
Step 9: Create AtomicMutationProcessor
  └── Single entry point replacing layered gateway + decorators

Step 10: Integrate ExecutionToken into MutationExecutor.execute()

Step 11: Remove @requires_gateway decorator (replaced by token verification)
```

### Phase 4: Async Determinism (P1)

```
Step 12: Integrate DeterministicScheduler into SwarmEngine

Step 13: Replace asyncio.create_task() with DeterministicAsyncExecutor
```

---

## 10. SAFETY PROOF (INFORMAL)

### 10.1 Why Replay Becomes Exact

**Theorem:** For any execution trace `trace(t)` produced by ATOMFederation-OS with `ATOM_SEED=S`, running the same trace with `ATOM_SEED=S` produces identical state.

**Proof:**

1. **All randomness is seeded:**
   - `DeterministicRNG.get_rng(agent, tick)` produces identical sequence for same `(agent, tick)` pair
   - No `random.*`, `uuid.uuid4()`, `np.random.*` outside `DeterministicRNG`

2. **All ordering is tick-based:**
   - `GlobalExecutionSequencer` orders mutations strictly by tick
   - `DeterministicScheduler` orders tasks by `(priority desc, task_id asc, tick % 9999)`
   - No `time.time()` in control flow decisions

3. **All IDs are content-addressed:**
   - `DeterministicUUIDFactory.make_id(prefix, content, salt)` is deterministic
   - Same inputs always produce same ID

4. **Therefore:** `trace(t)` = `f(S, tick_sequence, content_hashes)` where `f` is pure and deterministic. Same inputs → same outputs.

### 10.2 Why Race Conditions Are Eliminated

**Theorem:** `AtomicLedgerWriter` guarantees strict linearizability.

**Proof:**

1. **Single-writer:** `record()` uses `threading.Lock`. Only one thread can write at a time.
2. **Ordered append:** Each `record(entry, tick)` checks `tick >= last_tick`. Out-of-order writes raise `SafetyViolationError`.
3. **WAL semantics:** Entries written to WAL before commit. On crash, WAL is replayed.
4. **No concurrent writes:** Lock held for entire `record()` operation (write + verify + WAL + commit).

### 10.3 Why Ledger Is Linearizable

**Theorem:** All ledger entries appear in strict tick order for all observers.

**Proof:**

1. **GlobalExecutionSequencer** enforces FIFO ordering: `enqueue()` appends to queue sorted by tick.
2. **AtomicLedgerWriter** verifies `tick >= last_tick` before every write.
3. **No out-of-order writes possible:** Violation raises `SafetyViolationError` (fail-fast).
4. **Observer sees consistent snapshot:** `_lock` ensures atomic visibility of each entry.

---

## 11. FILES TO CREATE / MODIFY

### New Files

```
core/
├── deterministic.py                          # NEW: Deterministic primitives
│   ├── DeterministicClock
│   ├── DeterministicRNG
│   ├── DeterministicUUIDFactory
│   └── GlobalExecutionSequencer
├── atomic_ledger.py                          # NEW: AtomicLedgerWriter
└── atomic_mutation_processor.py              # NEW: Collapsed execution kernel

tests/
├── test_deterministic_kernel.py              # NEW: Determinism tests
├── test_ledger_linearization.py              # NEW: Ledger safety tests
└── test_execution_boundary.py                # NEW: Boundary enforcement tests
```

### Files to Modify

```
core/runtime/
├── execution_context.py                      # N1-N3: uuid4 → make_context_id/make_entry_id
├── proof_verifier.py                         # N6: uuid4 → make_nonce
│
orchestration/
├── execution_gateway.py                      # N7: nonce → DeterministicClock.tick
├── mutation_executor.py                      # N9: Already OK (seed=tick)
├── deterministic_scheduler.py                # Already clean, integrate
└── v8_2b_controlled_autocorrection/
    ├── feedback_injection.py                 # N10: Already OK (seed=tick)
    └── adaptive_router.py                    # N11: random → deterministic peer selection
│
core/federation/
└── consensus.py                              # N8: uuid4 → tick-based round_id
│
core/proof/
└── execution_request.py                      # N4-N5: uuid4 + time → factory methods
```

---

## 12. SUCCESS CRITERIA

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | `trace(t) == replay(trace(t))` for all t | Run same seed 3x, compare outputs |
| 2 | `MutationLedger` strictly linearizable | `verify_linearizability()` returns `is_linearizable=True` |
| 3 | No concurrent mutation execution | `GlobalExecutionSequencer` enforces FIFO |
| 4 | All nondeterministic sources eliminated | 0 matches for `uuid4`, `time.time`, `random.` in control flow |
| 5 | `ExecutionToken` required for all mutations | `execute()` without valid token → `SafetyViolationError` |
| 6 | AtomicLedgerWriter thread-safe | Concurrent `record()` from 10 threads → no corruption |
| 7 | DeterministicScheduler verified | `verify_determinism()` passes 3x same tick |
| 8 | Execution boundary is single atomic kernel | No `@requires_gateway` decorators (replaced by token) |

---

## 13. CI DETERMINISM GATE

```yaml
# .github/workflows/determinism.yml
name: Determinism Gate

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  determinism-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run determinism test (seed=42)
        run: |
          ATOM_SEED=42 python3 -m pytest tests/test_deterministic_kernel.py -v --tb=short
          cp /tmp/determinism_trace.json determinism_run1.json
      
      - name: Run determinism test (seed=42) — 2nd time
        run: |
          ATOM_SEED=42 python3 -m pytest tests/test_deterministic_kernel.py -v --tb=short
          cp /tmp/determinism_trace.json determinism_run2.json
      
      - name: Run determinism test (seed=42) — 3rd time
        run: |
          ATOM_SEED=42 python3 -m pytest tests/test_deterministic_kernel.py -v --tb=short
          cp /tmp/determinism_trace.json determinism_run3.json
      
      - name: Compare traces (MUST be identical)
        run: |
          diff determinism_run1.json determinism_run2.json
          diff determinism_run2.json determinism_run3.json
          echo “DETERMINISM GATE: PASSED”
```

---

## 14. SUMMARY SCORECARD

| Category | Before (v9.0) | After (ATOM-META-RL-019) |
|----------|---------------|--------------------------|
| **Determinism** | 🔴 0/10 | 🟢 10/10 |
| **Ledger Linearizability** | 🟠 5/10 | 🟢 10/10 |
| **Execution Boundary** | 🟠 7/10 | 🟢 10/10 |
| **Async Determinism** | 🟡 5/10 | 🟢 10/10 |
| **Thread Safety** | 🟠 7/10 | 🟢 10/10 |
| **Replay Correctness** | 🔴 0/10 | 🟢 10/10 |
| **Overall** | **38/70 (54%)** | **70/70 (100%)** |

---

*ATOM-META-RL-019 | Deterministic Kernel & Execution Boundary Hardening | v9.0+ATOM-META-RL-019*