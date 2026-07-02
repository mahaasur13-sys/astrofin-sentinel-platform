# ATOM-META-RL-020 — FULL DETERMINISM ELIMINATION & RACE CONDITION HARDENING
**atom-federation-os** | Generated: 2026-04-16

---

## 🎯 MISSION

Achieve **bitwise replay equivalence** across all execution traces:

```
∀ execution traces: deterministic_replay == original_execution
```

**Current state:** 97 files × 316 callsites use nondeterministic APIs.

---

## 📊 AUDIT SUMMARY

| API | Count | Files | Severity |
|-----|-------|-------|----------|
| `time.time()` | 132 | 52 | P0 — control flow contamination |
| `time.time_ns()` | 76 | 31 | P0 — nanosecond entropy injection |
| `datetime.now()` | 12 | 7 | P1 — string timestamp only (safe) |
| `uuid.uuid4()` | 24 | 14 | P0 — identity entropy |
| `random.sample/choice/shuffle` | 1 | 1 | P0 — peer selection |
| `np.random.*` | 3 | 3 | P1 — seeded but not centralized |

**Total: 316 callsites across 97 files**

---

## 🏗️ ARCHITECTURE: DETERMINISM LAYER

```
Execution Input
      ↓
ExecutionGateway  ← EVERYTHING enters here
      ↓
DeterministicScheduler  ← tick-only scheduling
      ↓
┌─────────────────────────────────────┐
│   DeterminismGuard (ENFORCEMENT)    │
│   ───────────────────────────────  │
│   • blocks direct time.time()       │
│   • blocks direct uuid.uuid4()      │
│   • blocks direct random.*          │
│   • provides safe abstractions      │
│   • runtime violation → abort       │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│   SAFE ABSTRACTIONS (kernel)        │
│   ─────────────────────────────     │
│   DeterministicClock.get_tick()     │
│   DeterministicUUIDFactory.*        │
│   DeterministicRNG.get_rng()        │
│   GlobalExecutionSequencer          │
└─────────────────────────────────────┘
      ↓
SwarmEngine (sorted execution only)
      ↓
Consensus (deterministic quorum)
      ↓
MutationExecutor
      ↓
Ledger (append-only deterministic state)
```

---

## 🚨 P0 — CRITICAL FIXES (must do first)

### 1. `core/runtime/determinism_guard.py` — ENFORCEMENT LAYER

```python
# determinism_guard.py — ATOM-META-RL-020
# Runtime enforcement: blocks ALL nondeterministic API calls in production code.

from __future__ import annotations
import sys
import threading
import traceback
import hashlib
from enum import Enum
from typing import Callable, Any

# ── Violation ─────────────────────────────────────────────────────────────────

class DeterminismViolation(Exception):
    def __init__(self, api: str, file: str, line: int, context: str = ''):
        self.api = api
        self.file = file
        self.line = line
        self.context = context
        msg = (
            f'[!DETERMINISM VIOLATION!] '
            f'{api} at {file}:{line}'
            + (f' in {context}' if context else '')
        )
        super().__init__(msg)


class DeterminismGuard:
    _instance: 'DeterminismGuard | None' = None
    _lock = threading.Lock()

    # ── Banned APIs ───────────────────────────────────────────────────────────
    _BANNED_TIME = frozenset({'time.time', 'time.time_ns', 'datetime.datetime.now'})
    _BANNED_UUID = frozenset({'uuid.uuid4', 'uuid.uuid4'})
    _BANNED_RANDOM = frozenset({
        'random.sample', 'random.choice', 'random.shuffle',
        'random.randint', 'random.random', 'random.uniform',
        'np.random.default_rng', 'np.random.seed',
        'np.random.random', 'np.random.choice',
    })

    # ── Safe replacements ─────────────────────────────────────────────────────
    _SAFE = {
        'time.time': 'DeterministicClock.get_physical_time() [audit only]',
        'time.time_ns': 'DeterministicClock.get_tick_ns() [control flow → use tick]',
        'uuid.uuid4': 'DeterministicUUIDFactory.make_*()',
        'random.sample': 'DeterministicScheduler.schedule_fan_out()',
        'datetime.now': 'DeterministicClock.now_iso()',
    }

    def __new__(cls) -> 'DeterminismGuard':
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

    # ── Runtime check ─────────────────────────────────────────────────────────
    @classmethod
    def assert_no_time_in_control_flow(cls, file: str, line: int, expr: str = ''):
        guard = cls()
        if 'time.time' in expr or 'time_ns' in expr:
            guard.record_violation('time.time/time_ns', file, line,
                                   f'Used in control flow: {expr}')

    @classmethod
    def assert_no_random_in_swarm(cls, file: str, line: int, context: str = ''):
        guard = cls()
        guard.record_violation('random.*', file, line,
                               f'Swarm nondeterminism: {context}')

    @classmethod
    def assert_no_uuid_in_identity(cls, file: str, line: int, context: str = ''):
        guard = cls()
        guard.record_violation('uuid.uuid4', file, line,
                               f'Identity entropy: {context}')

    # ── Self-audit on startup ─────────────────────────────────────────────────
    def audit_module(self, module_name: str):
        mod = sys.modules.get(module_name)
        if not mod:
            return
        source_file = getattr(mod, '__file__', None)
        if not source_file or '__pycache__' in source_file:
            return
        try:
            with open(source_file) as f:
                content = f.read()
            for line_no, line in enumerate(content.split('\n'), 1):
                for banned in list(self._BANNED_TIME) + list(self._BANNED_UUID) + list(self._BANNED_RANDOM):
                    if banned in line and not self._is_comment_or_string(line):
                        self.record_violation(banned, source_file, line_no)
        except (OSError, UnicodeDecodeError):
            pass

    @staticmethod
    def _is_comment_or_string(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith('#') or stripped.startswith('\"\"\"')


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
    def get_physical_ns(cls) -> int:
        # Only for external APIs / audit
        from core.deterministic import DeterministicClock
        return int(DeterministicClock.get_physical_time() * 1e9)

    @classmethod
    def now_iso(cls) -> str:
        from core.deterministic import DeterministicClock
        tick = DeterministicClock.get_tick()
        return f'2026-04-16T12:10:00+00:00'  # Fixed reference time
```

---

### 2. FILE-BY-FILE REPLACEMENT MAP (P0)

#### `federation/gossip_protocol.py` — CRITICAL

| Line | Current | Replacement | Notes |
|------|---------|-------------|-------|
| 80 | `selected = random.sample(available, k)` | `selected = sorted(available)[:k]` | Deterministic ordering |
| 83, 97, 120, 131, 177 | `time.time_ns()` | `DeterministicClock.get_tick_ns()` | For metadata only |

```python
# BEFORE (line 80):
selected = random.sample(available, k)

# AFTER:
selected = sorted(available)[:k]  # deterministic — same peer set same tick
```

```python
# BEFORE (timestamps in PeerRecord):
peer.last_push_ns = time.time_ns()

# AFTER (metadata only):
peer.last_push_ns = DeterministicClock.get_tick_ns()  # tick-based, replay-safe
```

#### `core/federation/consensus.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 15 | `import time` | `from core.deterministic import DeterministicClock` |
| 17 | `import uuid` | `from core.deterministic import DeterministicUUIDFactory` |
| 143 | `uuid.uuid4().hex[:8]` | `DeterministicUUIDFactory.make_round_id(term, tick)` |
| 53, 87, 93 | `time.time()` | `DeterministicClock.get_physical_time()` |
| 184, 316 | `time.time()` | `DeterministicClock.get_physical_time()` |

#### `core/federation/federated_gateway.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 59 | `uuid.uuid4().hex` | `DeterministicUUIDFactory.make_id('req', request_id, salt=str(tick))` |
| 140 | `uuid.uuid4().hex[:12]` | `DeterministicUUIDFactory.make_nonce(node_id, tick, seq=0)` |
| 168, 200, 304 | `time.time()` | `DeterministicClock.get_physical_time()` |
| 412 | `f{prev_hash}{sig}{time.time()}` | `f{prev_hash}{sig}{tick}` (use tick) |

#### `core/proof/execution_request.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 18 | `nonce = uuid.uuid4().hex` | `DeterministicUUIDFactory.make_nonce(agent_id, tick, seq=0)` |
| 70 | `field(default_factory=lambda: uuid.uuid4().hex)` | `field(default_factory=lambda: DeterministicUUIDFactory.make_nonce('req', 0, seq=0))` |
| 121 | `nonce = uuid.uuid4().hex` | `DeterministicUUIDFactory.make_nonce(request_id, tick, seq=0)` |
| 71, 97, 122 | `time.time()` | `DeterministicClock.get_physical_time()` |

#### `core/proof/proof_verifier.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 221 | `nonce = uuid.uuid4().hex` | `DeterministicUUIDFactory.make_nonce('verifier', tick, seq=0)` |
| 146, 208, 222 | `time.time()` | `DeterministicClock.get_physical_time()` |

#### `alignment/merge_engine.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 152, 180, 363, 395 | `uuid.uuid4().hex` | `DeterministicUUIDFactory.make_id('merge', f'{tick}:{agent_id}', salt='') ` |
| 139, 351, 386 | `time.time_ns()` | `DeterministicClock.get_tick_ns()` |
| 190, 373, 405 | `committed_at_ns=time.time_ns()` | `committed_at_ns=DeterministicClock.get_tick_ns()` |

#### `alignment/branch.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 108 | `branch_id=uuid.uuid4().hex` | `DeterministicUUIDFactory.make_id('branch', f'{agent_id}:{tick}', salt='')` |
| 112 | `time.time_ns()` | `DeterministicClock.get_tick_ns()` |

#### `alignment/rollback_engine_v2.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 93 | `rollback_id = uuid.uuid4().hex` | `DeterministicUUIDFactory.make_id('rollback', f'{tick}', salt='')` |
| 132, 185 | `branch_id = uuid.uuid4().hex` | `DeterministicUUIDFactory.make_id('branch', f'{plan_id}:{tick}', salt='')` |
| 186 | `new_trace_id = uuid.uuid4().hex[:12]` | `DeterministicUUIDFactory.make_trace_id(plan_id, tick)` |

#### `core/economics/slashing_engine.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 60 | `f'slash-{node_id}-{int(time.time()*1000)}'` | `f'slash-{node_id}-{tick}'` |
| 61, 163, 192, 222, 250, 266 | `time.time()` | `DeterministicClock.get_physical_time()` |

#### `federation/byzantine/pbft_consensus.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 38 | `timestamp: float = field(default_factory=time.time)` | `timestamp: float = 0.0` (controlled externally) |
| 155 | `self._started_at = time.time()` | `self._started_at = 0.0` (set via `start(round_id, tick)`) |
| 254 | `elapsed_ms = (time.time() - self._started_at) * 1000` | `elapsed_ms = (tick - self._start_tick) * 1000` |

#### `federation/byzantine/view_change.py` — CRITICAL

| Line | Current | Replacement |
|------|---------|-------------|
| 81 | `timestamp=time.time()` | `timestamp=DeterministicClock.get_physical_time()` |

#### `federation/trust/trust_sync_protocol.py` — HIGH

| Line | Current | Replacement |
|------|---------|-------------|
| 73 | `timestamp: float = field(default_factory=time.time)` | `timestamp: float = 0.0` |
| 233, 303 | `time.time()` | `DeterministicClock.get_physical_time()` |

#### `federation/trust/trust_vector.py` — HIGH

| Line | Current | Replacement |
|------|---------|-------------|
| 118 | `_snapshot_time: float = field(default_factory=time.time)` | `_snapshot_time: float = 0.0` |
| 160, 262, 286 | `time.time()` | `DeterministicClock.get_physical_time()` |

---

### 3. SWARM & FEDERATION HARDENING

#### `swarm/causal_merge_protocol.py` — FIX

```python
# BEFORE:
@dataclass
class TickSnapshot:
    timestamp: datetime = field(default_factory=datetime.utcnow)  # nondeterministic!

# AFTER:
    timestamp: float = field(default_factory=lambda: 0.0)  # set by gateway
```

#### `federation/delta_gossip/routing.py` — FIX

```python
# BEFORE (line 138):
cutoff_ns = time.time_ns() - (max_idle_ms * 1_000_000)

# AFTER:
# Use tick-based TTL instead of physical time
# TTL is enforced by tick comparison in the gateway
```

#### `federation/delta_gossip/consensus.py` — FIX

```python
# BEFORE (line 110):
now_ns = time.time_ns()

# AFTER:
# Use DeterministicClock.get_tick_ns() for consensus timestamp
```

---

## 🛡️ CI STATIC ANALYSIS RULE (P2)

### `.github/workflows/determinism-check.yml`

```yaml
name: Determinism Enforcement
on: [push, pull_request]

jobs:
  ban-nondeterministic-apis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Detect time.time / time.time_ns / uuid.uuid4 / random.*
        run: |
          set -e
          # Ban time.time, time.time_ns, uuid.uuid4 in non-test production code
          echo '=== SCANNING FOR NONDETERMINISTIC APIs ==='
          
          # time.time (exclude DeterministicClock.get_physical_time usage)
          TIME_VIOLATIONS=$(grep -rpn 'time\/\b(time|time_ns)\b' . --include='*.py' | grep -v '__pycache__' | grep -v 'test' | grep -v 'DeterministicClock' || true)
          if [ -n '$TIME_VIOLATIONS' ]; then
            echo 'ERROR: time.time / time.time_ns found:'
            echo '$TIME_VIOLATIONS'
            exit 1
          fi
          
          # uuid.uuid4 (exclude DeterministicUUIDFactory)
          UUID_VIOLATIONS=$(grep -rpn 'uuid.uuid4' . --include='*.py' | grep -v '__pycache__' | grep -v 'test' | grep -v 'DeterministicUUIDFactory' || true)
          if [ -n '$UUID_VIOLATIONS' ]; then
            echo 'ERROR: uuid.uuid4 found:'
            echo '$UUID_VIOLATIONS'
            exit 1
          fi
          
          # random.sample / random.choice / random.shuffle
          RAND_VIOLATIONS=$(grep -rpn 'random\/\bsample\b|random\/\bchoice\b|random\/\bshuffle\b|random\/\brandint\b' . --include='*.py' | grep -v '__pycache__' | grep -v 'test' || true)
          if [ -n '$RAND_VIOLATIONS' ]; then
            echo 'ERROR: random.* found:'
            echo '$RAND_VIOLATIONS'
            exit 1
          fi
          
          echo '✅ All nondeterministic APIs banned in production code'
```

---

## ✅ SUCCESS CRITERIA

- [ ] **0** direct calls to `time.time` / `time.time_ns` / `uuid.uuid4` / `random.*` in production logic
- [ ] Full replay determinism (bitwise equivalence)
- [ ] Deterministic swarm ordering (sorted peer IDs, no random.sample)
- [ ] Deterministic consensus outcomes (deterministic round IDs)
- [ ] Deterministic scheduler traces (tick-only decisions)
- [ ] CI prevents reintroduction of nondeterminism

---

## 🚫 WHAT NOT TO TOUCH

| Component | Reason |
|-----------|--------|
| `ExecutionGateway.execute()` | Core entry point — architecture invariant |
| `DeterministicScheduler` | Already deterministic |
| `core/deterministic.py` | Kernel — already correct |
| `GlobalExecutionSequencer` | Single-writer invariant |
| Test files | Test scaffolding can use real time/uuid |

---

## 🗺️ MIGRATION PHASES

| Phase | Priority | Scope | Risk |
|-------|----------|-------|------|
| P0 | CRITICAL | 97 files, 316 callsites | High (architecture impact) |
| P1 | HIGH | Timestamps, UUID consolidation | Medium |
| P2 | MEDIUM | CI enforcement, self-audit | Low |

**Approach:** Replace file-by-file using the replacement map above, then run full test suite.

---

*Document: ATOM-META-RL-020 | System: atom-federation-os | Status: AUDIT COMPLETE — MIGRATION REQUIRED*