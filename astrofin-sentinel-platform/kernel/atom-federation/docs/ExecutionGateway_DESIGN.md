# ExecutionGateway — v9.0+P2 Final Design Specification

> **Status:** IMPLEMENTED + VERIFIED
> **Validated:** `execution_algebra_validator.py` → `✅ PASS`
> **Version:** 9.0+P2

---

## 1. Architectural Invariant (Formal)

```
∃! P : P = ExecutionGateway.execute()
∀ other P_i : P_i is NOT reachable as execution root

MutationExecutor.apply_mutation()
  → called ONLY from ExecutionGateway._act_stage()
  → NEVER externally accessible
  → NEVER imported as execution entry
```

---

## 2. Execution Algebra (Enforced Chain)

```
G1 → G2 → G3 → G4 → G5 → G6 → G7 → G8 → G9 → G10 → ACT
```

| Stage | Function | Real Implementation |
|---|---|---|
| G1 | AdversarialDetector | Stub (keyword block) |
| G2 | PolicyKernelV4 | Stub (always pass) |
| G3 | Alignment (GSCT/GCST/GAST/UST) | Stub |
| G4 | StabilityGovernor | Stub |
| G5 | CircuitBreaker | Stub |
| G6 | PreValidation (InvariantContract) | Stub |
| G7 | ActuationGate | Controls actuator isolation |
| **ACT** | **MutationExecutor.apply_mutation()** | **Wired — Gateway-owned** |
| G8 | InvariantChecker.post_validate | Stub |
| G9 | MutationLedger (HMAC-chained) | Stub |
| G10 | RollbackEngine | Stub |

---

## 3. Dominator Tree

```
ExecutionGateway.execute()     [SOLE ENTRY]
    │
    ├─ G1: adversarial_detector
    ├─ G2: policy_kernel
    ├─ G3: alignment_layer
    ├─ G4: stability_governor
    ├─ G5: circuit_breaker
    ├─ G6: prevalidation
    ├─ G7: actuation_gate
    ├─ G8: invariant_checker
    ├─ G9: mutation_ledger
    ├─ G10: rollback_engine
    │
    └─ ACT: _act_stage()
            └─ MutationExecutor.apply_mutation()   [PRIVATE — Gateway-owned]
                    └─ _execute_internal()          [internal only]
                            ├─ _generate_delta()
                            ├─ _blocked_result()
                            ├─ _failed_result()
                            ├─ _rollback_result()
                            └─ _fire_callback()
```

**Key property:** `MutationExecutor` is instantiated inside `ExecutionGateway.__init__()`. It is never exposed via `__init__`, never returned, never stored as a module-level singleton. It exists solely to serve the ACT stage.

---

## 4. MutationExecutor — Final Capability Interface

After P2, `MutationExecutor` exposes:

| Method | Access | Purpose |
|---|---|---|
| `apply_mutation(...)` | **public** — gateway-only | ACT stage mutation entry |
| `current_theta()` | public — read-only | State inspection |
| `_generate_delta(...)` | **private** | Delta generation |
| `_execute_internal(...)` | **private** | Full pipeline (called by apply_mutation) |
| `_blocked_result(...)` | private | Result factory |
| `_failed_result(...)` | private | Result factory |
| `_rollback_result(...)` | private | Result factory |
| `_fire_callback(...)` | private | Callback runner |
| `_default_update_fn(...)` | private | Health-aware update |
| `__init__` | **public** — Gateway-only | Capability injection |

`execute()` — **DELETED** (P1).

---

## 5. ExecutionGateway — Constructor Interface

```python
class ExecutionGateway:
    def __init__(self, mutation_executor=None):
        """
        Args:
            mutation_executor: MutationExecutor instance.
                                If None → ACT stage runs in stub mode.
                                Always instantiated by Gateway itself in production.
        """
```

**P2 rule:** `MutationExecutor` MUST be injected at Gateway construction. It MUST NOT be callable externally.

---

## 6. CI / Validator Rules (Enforced)

| Rule | Validator Check | CI Action |
|---|---|---|
| Single entry | `len(entry_points) == 1` | FAIL if >1 |
| No bypass | `execute()` only in ExecutionGateway | FAIL if elsewhere |
| No mutagen | `mutation_executor.execute()` anywhere | **FAIL (hard)** |
| Actuator isolation | No external `CausalActuationEngine` refs | WARN |
| Dominator rule | ExecutionGateway dominates all mutation paths | FAIL if violated |

**Validator:** `scripts/execution_algebra_validator.py`
**CI:** `.github/workflows/safety-algebra.yml`

---

## 7. Architecture Freeze (P2)

After P2, the following are **forbidden**:

| Prohibition | Reason |
|---|---|
| New `execute()` functions anywhere | Bypass the algebra |
| New entry points | Violates single-entry invariant |
| Direct `MutationExecutor.apply_mutation()` outside ACT stage | Destroys dominator tree |
| Returning `MutationExecutor` from Gateway | Exposes actuator |
| Module-level MutationExecutor singletons | External mutation paths |

New execution capabilities MUST be added as Gateway stage functions or ACT sub-operations.

---

## 8. P2 Changes Summary

| File | Change | DoD |
|---|---|---|
| `execution_gateway.py` | ACT stage wired to MutationExecutor | ✅ |
| `mutation_executor.py` | `execute()` deleted, `apply_mutation()` = public gateway-only | ✅ |
| `execution_algebra_validator.py` | `MUTAGEN_REMOVE_CLASS`, hard FAIL | ✅ |
| `ExecutionGateway_DESIGN.md` | Updated with final architecture | ✅ |
| `merge_engine.py` | `execute()` → `apply_merge_alignment()` (gateway-only) | ✅ |
| `cluster/node/node.py` | `execute()` deprecated, `handle_forward()` via Gateway | ✅ |

---

## 9. Test Invariants (Formal)

```python
# Invariant 1: Single entry
assert len(entry_points) == 1
assert entry_points[0].file.endswith("ExecutionGateway/execution_gateway.py")

# Invariant 2: MutationExecutor dominance
# MutationExecutor is NEVER directly callable as entry
mutagen.execute() → FAIL (hard violation in validator)

# Invariant 3: Gateway owns ACT
# Only ExecutionGateway._act_stage() calls MutationExecutor.apply_mutation()
# apply_mutation() is NOT callable from outside Gateway

# Invariant 4: No bypass
# execute() exists ONLY in ExecutionGateway
# All other execute() methods are deleted or hard-deprecated
```

---

## 10. Version History

| Version | Milestone |
|---|---|
| 9.0 | Initial ExecutionGateway skeleton |
| P1 | Deprecation + removal of 4 bypass entry points |
| **P2** | **ACT stage wiring + MutationExecutor dominator + validator hardening** |
