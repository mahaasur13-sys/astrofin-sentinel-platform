# Phase B2b — Policy / Audit Modules Audit

> **Date:** 2026-07-13
> **Scope:** `agents/_impl/amre/`, `deploy/iac/{ai_scheduler,ete,l9_ebl}/`, plus cross-references
> **Mode:** Read-only inventory. No code changes in this turn.

---

## 1. Inventory map

| File | LOC | Public API (top-level) | Role |
|---|---:|---|---|
| `agents/_impl/amre/audit.py` | 658 | `TrajectorySnapshot`, `EnsembleMember`, `TrajectoryScore`, `MarketSnapshot`, `EnsembleSelection`, `KPISnapshot`, `DecisionRecord`, `MetaRLDecisionRecord`, `get_audit_log`, `record_decision`, `build_decision_record`, `record_meta_rl_decision`, `get_meta_rl_audit_log` | Decision audit trail (ATOM-KARL-009). In-process append-only log. |
| `agents/_impl/amre/hierarchical_policy.py` | 52 | `HierarchicalPolicy` (4 regimes: LOW/NORMAL/HIGH/EXTREME, `detect_regime`, `get_action`) | Regime → action mapping for AMRE ensemble. |
| `agents/_impl/amre/audit.py.bak-006` | 13 074 bytes | — | **Stale backup**, should be removed. |
| `deploy/iac/ai_scheduler/modules/policy.py` | 81 | `select_node(job_type, memory_gb, priority, dataset_ceph) -> dict` | K8s node / partition selector for AI training jobs. Pure infra layer, no business decisions. |
| `deploy/iac/ete/gate/governance_gate.py` | 67 | `Decision` enum (APPROVED/REJECTED/ESCALATED), `GovernanceGate` | L8/L9 **business** gate. Pre/mid/post-execution. |
| `deploy/iac/l9_ebl/gate/gate.py` | 95 | `ActionResult` (ALLOW/DENY/REDIRECT/ESCALATE), `GateDecision`, `ExecutionGate` | L9 infra **capability** gate. Import-time fails: `from l9_ebl.capabilities.registry import ExecutionContext` is **not importable from project root** (only inside `deploy/iac/`). |
| `deploy/iac/k8s/federation/placement-policy.yaml` | — | — | Static K8s manifest, not Python. |
| `core/*`, `meta_rl/*` | 0 | — | No `policy.py` / `audit.py` files matching the policy/audit family in the canonical tree (excluding `core/metrics.py` removed in B2a and `meta_rl/metrics.py` which is a different concern). |

---

## 2. Three independent "gates" — purpose disambiguation

| Gate | Domain | Decision states | Audience |
|---|---|---|---|
| `ete/governance_gate.py` | Business / trading | APPROVED / REJECTED / ESCALATED | Risk & strategy layer |
| `l9_ebl/gate/gate.py` | Infra / capability | ALLOW / DENY / REDIRECT / ESCALATE | IaC (k8s, federation, scheduler) |
| `ai_scheduler/policy.py` | K8s node selection | (return dict) | Scheduler / batch jobs |

**No functional overlap** — they live on different layers (L8 business vs L9 infra vs L10 batch). They share only the word "policy/gate". **Do not merge.**

---

## 3. Findings

### F-POL-1 — `HierarchicalPolicy` has zero runtime callers
- Class is re-exported in `agents/_impl/amre/__init__.py` (line 22) and in `validate_agent.py` (line 103, as a path string).
- **No `HierarchicalPolicy(...)` instantiation anywhere** outside its own module. Module is referenced in audit reports but not in the live ensemble path (which goes through `oap_optimizer.py` → `audit.get_audit_log`).
- Risk: dead code that may still be picked up by `__init__.py` exports and confuse readers.
- Severity: **Low** (L1 / cosmetic / drift risk).

### F-POL-2 — `audit.py.bak-006` orphan
- 13 KB stale backup left in tree. Not a runtime risk (Python ignores), but it's noise and a leak risk (could contain older secrets).
- Severity: **Low**.

### F-POL-3 — `l9_ebl/gate/gate.py` is not importable from project root
- `python -c "from l9_ebl.gate.gate import ExecutionGate"` fails with `ModuleNotFoundError: No module named 'l9_ebl'`.
- Correct: `cd deploy/iac && python -c "from l9_ebl.gate.gate import ExecutionGate"`.
- `acos.py` and `acos_cli.py` are also unimportable from root.
- This is by design (`deploy/iac/` is a sub-package with its own layout) but means:
  - `l9_ebl` is invisible to top-level tests/agents.
  - Anyone adding tests at root level will hit the same wall.
- Severity: **Low** (architectural; not a defect).

### F-POL-4 — Regime vocabulary drift between `HierarchicalPolicy` and `meta_rl/live_provider`
- `HierarchicalPolicy.regimes` = `["LOW", "NORMAL", "HIGH", "EXTREME"]` (volatility-based, AMRE-ensemble).
- `meta_rl/live_provider._detect_regime_fast` returns `Literal["BULL", "BEAR", "NEUTRAL", "VOLATILE"]` (trend-based, market regime).
- `strategies/generator.py` `Regime` enum = `BULL / BEAR / NEUTRAL_R / VOLATILE`.
- They live in different layers and answer different questions. **Not a duplication** — but the namespace collision is a documentation hazard.
- Severity: **Low** (cosmetic / naming).

### F-POL-5 — Zero test coverage on all three audit/policy files
- `grep -l "amre.audit\|governance_gate\|ExecutionGate" tests/` returns no matches.
- `tests/test_validator.py` and `tests/test_karl_synthesis_lag.py` exist but do not import these modules.
- Severity: **Medium** (audit trail is a critical path; absence of tests means drift can land silently).

### F-POL-6 — `amre/audit.py` is **not exercised at all** by current tests
- Confirmed: `get_audit_log()`, `record_decision()`, `record_meta_rl_decision()` are not called in `tests/`. The only live caller is `oap_optimizer.py` (one call) and `meta_rl/meta_agent.py` (one lazy import inside a method).
- Severity: **Medium** (audit trail is a critical path; absence of tests means drift can land silently).

### F-POL-7 — Mirrored copies in `audit_repo/`, `asp-work/`, `asp-canonical/`, `Projects/asp-canonical{,-real,-work}/`
- `hierarchical_policy.py`, `audit.py`, `karl_integration.py`, `oap_optimizer.py`, `__init__.py` exist in **5** parallel locations. Sizes match exactly (660/52/…). Confirmed by LOC count.
- Status: `audit_repo/` and `asp-canonical/` are **stale mirrors** (last touched 2026-05; not in current tree). `Projects/asp-canonical-real` is the live repo.
- Severity: **Medium** (workspace hygiene; risk of editing the wrong copy).

---

## 4. Recommendations (no commits in this turn)

| ID | Action | Priority | Risk | Suggested PR |
|---|---|---|---|---|
| R-POL-1 | Delete `agents/_impl/amre/audit.py.bak-006` (after confirming git history covers the older version) | P0 | trivial | chore: remove stale `.bak-006` |
| R-POL-2 | Add a smoke test for `amre/audit.py` (record a `DecisionRecord` → assert it appears in `get_audit_log()`) | P1 | low | test(amre): smoke-test audit log |
| R-POL-3 | Add a smoke test for `ete/governance_gate.py` (APPROVED/REJECTED/ESCALATED paths) | P1 | low | test(ete): smoke-test governance gate |
| R-POL-4 | Add a docstring to `HierarchicalPolicy` clarifying that it is **not** part of the live ensemble path (which goes through `oap_optimizer`) | P2 | none | docs(amre): clarify HierarchicalPolicy status |
| R-POL-5 | Move stale mirrors out of `$HOME` (`audit_repo/`, `asp-canonical/`, `asp-work/`) into `Trash/` or `~/archive/` | P0 | low (only affects home dir) | chore: archive stale mirrors |
| R-POL-6 | Document the three gates in `docs/architecture/gates.md` (8 lines: who calls, decision states, when to add) | P2 | none | docs: gates overview |
| R-POL-7 | Do **not** merge `ete/governance_gate.py` and `l9_ebl/gate/gate.py` — they are different layers | — | — | (anti-recommendation) |

---

## 5. Out of scope (parked)

- Refactoring `HierarchicalPolicy` to be actually used (would need product decision).
- Replacing in-process `AuditLog` with a structured logger — already partially done via OTel in `core/logging.py`; cross-check is a separate audit.
- `l9_ebl` importability from root — would require a package layout change in `deploy/iac/`.

---

## 6. Open questions for you

1. Is `HierarchicalPolicy` deliberately unused (legacy), or is the ensemble path supposed to call it?
2. Do you want me to clean up the mirrored copies now (R-POL-5) or after the metrics refactor lands?
3. Should I add a test for `AuditLog` (R-POL-2) in the same PR, or as a separate change?

---

No commits to code in this turn — analysis only, as requested.
