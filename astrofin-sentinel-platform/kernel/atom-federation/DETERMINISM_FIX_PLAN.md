# Determinism Fix Plan — ATOMFederation-OS
## Status: 🔴 CRITICAL BLOCKER — Must fix before production

---

## 📊 Inventory Summary

| Category | Count | Control-flow impact |
|----------|-------|---------------------|
| `time.time_ns()` in nonce generation | 1 | 🔴 CRITICAL |
| `np.random.default_rng()` in mutation path | 1 | 🔴 CRITICAL |
| `np.random.default_rng()` in feedback injection | 1 | 🟠 HIGH |
| `uuid4()` in proof/contract identity | 5 | 🟡 MEDIUM |
| `time.time()` in contracts/events | 6 | 🟡 MEDIUM (seeded OK) |
| `time.monotonic()` in metrics/healer | 40+ | 🟢 OK (metrics only) |
| `time.time()` in DRL/network sim | 2 | 🟢 OK (sim layer) |
| `random` in adaptive_router | 1 | 🟠 HIGH (routing) |
| `random` in cluster_simulator | 1 | 🟢 OK (sim only) |

---

## 🔴 CRITICAL FIXES (control flow — must be deterministic)

### FIX-1: `execution_gateway.py` — Nonce generation
**File:** `orchestration/ExecutionGateway/execution_gateway.py:206`

```python
# ❌ BEFORE (nondeterministic)
f"{str(input_data)}{time.time_ns()}{uuid.uuid4().hex}".encode()

# ✅ AFTER — deterministic hash chain
f"{str(input_data)}{tick}".encode()  # tick is monotonically increasing
```

**Risk:** Changes replay protection — must propagate `tick` counter properly.
**Verification:** Same input + same tick → same nonce.

---

### FIX-2: `mutation_executor.py` — MutationExecutor RNG
**File:** `orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:159`

```python
# ❌ BEFORE (nondeterministic — health-aware scaling uses RNG)
rng = np.random.default_rng()

# ✅ AFTER — use deterministic seeded RNG from tick
rng = np.random.default_rng(seed=tick)
```

**Risk:** Changes delta generation — need to verify `health * delta` still bounded.
**Verification:** Same state + same tick → same mutation delta.

---

### FIX-3: `feedback_injection.py` — Feedback noise injection
**File:** `orchestration/v8_2b_controlled_autocorrection/feedback_injection.py:201`

```python
# ❌ BEFORE (nondeterministic noise)
rng = np.random.default_rng()

# ✅ AFTER — deterministic noise from tick
rng = np.random.default_rng(seed=tick)
```

**Risk:** Feedback signals change — verify no oscillation/feedback explosion.
**Verification:** Same state + same tick → same feedback vector.

---

## 🟠 HIGH FIXES (affects routing/decisions)

### FIX-4: `adaptive_router.py` — Weighted random peer selection
**File:** `resilience/adaptive_router.py:258,264`

```python
# ❌ BEFORE (nondeterministic random selection)
chosen = random.choices(healthy, weights=...)
chosen = random.choice(healthy)

# ✅ AFTER — deterministic: deterministic tiebreak by peer_id
healthy_sorted = sorted(healthy, key=lambda p: p.peer_id)
if weights:
    # Use deterministic cumulative weight + tick-based index
    idx = tick % len(healthy_sorted)
    chosen = healthy_sorted[idx]
else:
    idx = tick % len(healthy_sorted)
    chosen = healthy_sorted[idx]
```

**Risk:** Changes routing behavior — peer selection is now deterministic.
**Verification:** Same topology + same tick → same peer selected.

---

## 🟡 MEDIUM FIXES (identity/observability)

### FIX-5: `cross_origin_proof.py` — Proof IDs
**File:** `orchestration/consistency/invariant_contract/cross_origin_proof.py`

```python
# ❌ BEFORE
step_id: str = field(default_factory=lambda: f"proj_{uuid4().hex[:8]}")
proof_id: str = field(default_factory=lambda: f"sp_{uuid4().hex[:12]}")

# ✅ AFTER — deterministic IDs from content hash
import hashlib
def content_based_id(prefix: str, content: str, salt: str) -> str:
    h = hashlib.sha256(f"{salt}:{content}".encode()).hexdigest()[:12]
    return f"{prefix}_{h}"

# Usage: proof_id = content_based_id("sp", str(proof_payload), salt=str(tick))
```

**Risk:** Proof IDs change format — need to update proof verification logic.
**Verification:** Same proof content → same proof ID.

---

### FIX-6: `invariant_contract.py` — Contract IDs
**File:** `orchestration/consistency/invariant_contract/invariant_contract.py`

```python
# ❌ BEFORE
id: str = field(default_factory=lambda: str(uuid4())[:8])
detected_at: float = field(default_factory=time.time)

# ✅ AFTER — deterministic from invariant signature + tick
id = field(default_factory=lambda: f"inv_{hash(invariant_signature) % 2**32:08x}")
detected_at: float = field(default_factory=lambda: float(tick))  # tick-based
```

---

## 🟢 ACCEPTABLE (no control-flow impact)

These are OK — used only for metrics, logging, and timing measurements:

| File | Usage | Risk |
|------|-------|------|
| `eigenstate_detector.py` | `time.time()` for first_seen/last_seen | None |
| `healer.py` | `time.monotonic()` for duration | None |
| `arbitrer.py` | `time.monotonic()` for window | None |
| `reactor.py` | `time.monotonic()` for ts | None |
| `closed_loop.py` | `time.monotonic()` for convergence | None |
| `compute_budget_controller.py` | `time.time()` for budget tracking | None |
| `cluster_simulator.py` | `random.uniform()` | OK — sim only |

---

## 🛠 Implementation Order

```
Step 1: Create DeterministicScheduler base class
        ├── tick counter (monotonically increasing)
        ├── seeded RNG per agent
        └── tick-based nonce factory

Step 2: Fix FIX-1 (execution_gateway nonce) — highest priority
        ├── Replace uuid4()+time.time_ns() with tick-based nonce
        └── Test: same input + same tick = same nonce

Step 3: Fix FIX-2 (mutation_executor RNG)
        ├── Pass deterministic RNG seed=tick
        └── Verify delta bounds still hold

Step 4: Fix FIX-3 (feedback_injection RNG)
        ├── Pass deterministic RNG seed=tick
        └── Verify feedback signal stability

Step 5: Fix FIX-4 (adaptive_router)
        ├── Deterministic peer selection
        └── Test: same topology = same route

Step 6: Fix FIX-5 (proof IDs) + FIX-6 (contract IDs)
        └── Update proof verification

Step 7: Add DeterminismAssertionTest
        ├── Run 3x same seed → same output
        └── CI gate: fails if any deviation

Step 8: CI/CD enforcement (see CI_FIX_PLAN.md)
```

---

## ✅ Verification Strategy

```bash
# Determinism assertion test
ATOM_SEED=42 pytest tests/test_determinism.py -v

# Expected: same seed → same output across 3 runs
# CI gate: exit code 0 only if all 3 runs produce identical output
```

---

## 📁 Files to Modify

```
orchestration/
├── ExecutionGateway/execution_gateway.py           # FIX-1
├── v8_2b_controlled_autocorrection/
│   ├── mutation_executor.py                       # FIX-2
│   └── feedback_injection.py                      # FIX-3
resilience/
└── adaptive_router.py                             # FIX-4
orchestration/consistency/invariant_contract/
├── cross_origin_proof.py                          # FIX-5
└── invariant_contract.py                          # FIX-6
```

---

## 🚦 Success Criteria

- [ ] 0 nondeterministic calls in core control flow
- [ ] DeterminismAssertionTest passes 3x with same seed
- [ ] Federation consensus stable across 3 identical runs
- [ ] CI gate: pytest must fail on nondeterminism detection
- [ ] Ledger replay produces identical trace
