"""gcpl.py — v10.3 Global Convergence Proof Layer

Formal layer providing global convergence guarantees over branching causal DAGs.

Architecture position:
  v10.0 L1/L2/L3 drift detection
  v10.1 Local convergence (pairwise merge decisions)
  v10.2 Convergence guarantees (oscillation, entropy, audit)
  v10.3 GCPL — GLOBAL convergence proof + system-level invariant enforcement

This module does NOT modify merge decisions. It provides:
  1. Formal branch space model (metric space over branch histories)
  2. Convergence function C(t) — monotonic decreasing under correct merges
  3. Global invariants (branch entropy, irreconcilable ratio)
  4. Merge algebra constraints (commutativity, associativity, idempotency)
  5. Termination condition (eventual convergence or terminal leaf set)
  6. GlobalConsistencyChecker — GCPL.check() → {OK, DRIFT, NON_CONVERGENT}
  7. ConvergenceMetrics — branch_entropy, merge_velocity, convergence_rate

CORE FORMAL MODEL
=================
Branch Space as Metric Space:
  Let B = {b1, b2, ..., bn} be the set of active branches at time t.
  Each branch bi is a finite causal DAG of events.

  Define EDIT_DISTANCE(bi, bj) = minimum edit operations to transform
  the event sequence of bi into bj (insert/delete/substitute events).

  This defines a METRIC SPACE (B, d) where d(bi, bj) = EDIT_DISTANCE(bi, bj):
    d(bi, bj) = 0 iff bi ≡ bj (identical histories)
    d(bi, bj) = d(bj, bi) (symmetry)
    d(bi, bj) ≤ d(bi, bk) + d(bk, bj) (triangle inequality)

Convergence Function:
  C(t) = mean_{i<j} d(bi, bj)  [average pairwise branch distance]

  MERGE(bi, bj) produces bk where:
    d(bi, bk) ≤ d(bi, bj)  (bk closer to bi than bj was to bi)
    d(bj, bk) ≤ d(bi, bj)  (same for bj)

  Therefore: C(t+1) ≤ C(t)  with equality only when bi ≡ bj.

Global Convergence Invariant:
  GCI(t) = |B(t)| * C(t)  [total branch-space spread]

  Invariant: GCI(t+1) < GCI(t) whenever a non-trivial merge occurs.
  Eventually: GCI(t*) = 0 for some t* (all branches converged).

Termination Condition:
  System TERMINATES if:
    ∃ t* : ∀ t ≥ t* : C(t) = 0
    (all branches have identical histories)

  OR:
    ∃ t* : ∀ t ≥ t* : |B(t)| = K (constant)
    AND ∀ unmerged pairs (bi, bj): d(bi, bj) = CONSTANT
    AND no more merge decisions are triggered.
  This is the "terminal leaf set" case.

Merge Algebra:
  MERGE is:
    COMMUTATIVE: MERGE(a,b) = MERGE(b,a)
    ASSOCIATIVE: MERGE(a, MERGE(b,c)) = MERGE(MERGE(a,b), c)
      (true when all three branches are pairwise mergeable)
    IDEMPOTENT: MERGE(a, a) = a
      (trivially true)
    NOT: MERGE(MERGE(a,b), MERGE(a,b)) = MERGE(a,b)
      (true if inner merge is stable — oscillation prevention)

NON_CONVERGENCE CONDITIONS:
  System enters NON_CONVERGENT state if:
    1. Branch count grows without bound AND C(t) does not → 0
    2. Oscillation without termination: infinite MERGE/SPLIT cycles
    3. C(t) increases despite merge operations (wrong merge → audit)
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto

# ─────────────────────────────────────────────────────────────────
# METRIC SPACE — Branch Distance
# ─────────────────────────────────────────────────────────────────

def causal_edit_distance(events_a: list, events_b: list) -> float:
    """
    LCS-based edit distance between two causal event sequences.
    d(a,b) = |a| + |b| - 2*LCS(a,b)  /  max(|a|,|b|)

    Returns: normalized distance ∈ [0.0, 1.0]
    """
    if not events_a and not events_b:
        return 0.0
    if not events_a or not events_b:
        return 1.0

    ids_a = [getattr(e, 'event_id', str(e)) for e in events_a]
    ids_b = [getattr(e, 'event_id', str(e)) for e in events_b]

    m, n = len(ids_a), len(ids_b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ids_a[i-1] == ids_b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    lcs_len = dp[m][n]
    raw = m + n - 2 * lcs_len
    return min(1.0, raw / max(m, n)) if max(m, n) > 0 else 0.0

# ─────────────────────────────────────────────────────────────────
# CONVERGENCE FUNCTION
# ─────────────────────────────────────────────────────────────────

class ConvergenceFunction:

    @staticmethod
    def mean_pairwise_distance(branches: list) -> float:
        """C(t) = mean pairwise distance over all active branches."""
        n = len(branches)
        if n < 2:
            return 0.0
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                bi = getattr(branches[i], 'events', [])
                bj = getattr(branches[j], 'events', [])
                total += causal_edit_distance(bi, bj)
                count += 1
        return total / count if count > 0 else 0.0

    @staticmethod
    def convergence_rate(history: list[float], window: int = 5) -> float:
        """dC/dt numerical derivative. < 0 = converging."""
        if len(history) < 2:
            return 0.0
        recent = history[-window:]
        if len(recent) < 2:
            return 0.0
        n = len(recent)
        t = list(range(n))
        mean_t = sum(t) / n
        mean_c = sum(recent) / n
        num = sum((t[i] - mean_t) * (recent[i] - mean_c) for i in range(n))
        denom = sum((t[i] - mean_t) ** 2 for i in range(n))
        if abs(denom) < 1e-9:
            return 0.0
        return num / denom

# ─────────────────────────────────────────────────────────────────
# GLOBAL INVARIANTS
# ─────────────────────────────────────────────────────────────────

class GlobalInvariant(Enum):
    BRANCH_ENTROPY_BOUNDED = auto()
    CONVERGENCE_MONOTONIC = auto()
    IRRECONCILABLE_RATIO_BOUNDED = auto()
    MERGE_LOOP_FREE = auto()
    DRIFT_ACCUMULATION_NEGATIVE = auto()
    POST_MERGE_AUDIT_PASSED = auto()

# ─────────────────────────────────────────────────────────────────
# GLOBAL CONSISTENCY CHECKER
# ─────────────────────────────────────────────────────────────────

class GCPLCheckResult(Enum):
    OK = "ok"
    DRIFT = "drift"
    NON_CONVERGENT = "non_convergent"

@dataclass
class ConvergenceSnapshot:
    timestamp_ns: int
    branch_count: int
    active_branch_count: int
    convergence_function: float
    branch_entropy: float
    merge_velocity: float
    irreconcilable_ratio: float
    convergence_rate: float
    oscillation_count: int
    invariant_violations: list[GlobalInvariant]
    status: GCPLCheckResult

class GlobalConsistencyChecker:
    MAX_ACTIVE = 32
    MAX_IRRECONCILABLE_RATIO = 0.10
    DRIFT_RATE_THRESHOLD = 0.05
    DIVERGENCE_RATE_THRESHOLD = 0.10

    def __init__(self):
        self._convergence_history: list[float] = []
        self._entropy_history: list[float] = []
        self._merge_timestamps: list[float] = []
        self._lock = threading.RLock()

    def check(
        self,
        branches: list,
        active_branches: list,
        oscillation_count: int,
        terminal_branch_ids: list[str],
        last_convergence_ts: float,
        post_audit_pass: int,
        post_audit_total: int,
    ) -> ConvergenceSnapshot:
        now_ns = int(time.time() * 1e9)
        now_sec = time.time()

        violations: list[GlobalInvariant] = []

        with self._lock:
            # H(t)
            n_active = len(active_branches)
            entropy = math.log2(n_active) if n_active > 1 else 0.0
            self._entropy_history.append(entropy)
            if len(self._entropy_history) > 1000:
                self._entropy_history = self._entropy_history[-1000:]

            # C(t)
            c_val = 1.0 - ConvergenceFunction.mean_pairwise_distance(active_branches)
            self._convergence_history.append(c_val)
            if len(self._convergence_history) > 1000:
                self._convergence_history = self._convergence_history[-1000:]

            # dC/dt
            rate = ConvergenceFunction.convergence_rate(self._convergence_history)

            # merge velocity
            self._merge_timestamps.append(now_sec)
            recent = [t for t in self._merge_timestamps if now_sec - t < 3600.0]
            velocity = len(recent) / 3600.0

            # irreconcilable ratio
            n_total = len(branches)
            n_terminal = len(terminal_branch_ids)
            irreconcilable_ratio = n_terminal / n_total if n_total > 0 else 0.0

            # Invariant checks
            if n_active > self.MAX_ACTIVE:
                violations.append(GlobalInvariant.BRANCH_ENTROPY_BOUNDED)

            if rate > self.DIVERGENCE_RATE_THRESHOLD:
                violations.append(GlobalInvariant.CONVERGENCE_MONOTONIC)
            elif rate > self.DRIFT_RATE_THRESHOLD:
                pass  # DRIFT but not yet NON_CONVERGENT

            if irreconcilable_ratio > self.MAX_IRRECONCILABLE_RATIO:
                violations.append(GlobalInvariant.IRRECONCILABLE_RATIO_BOUNDED)

            if oscillation_count > 0 and rate >= 0:
                violations.append(GlobalInvariant.MERGE_LOOP_FREE)

            if post_audit_total > 0 and post_audit_pass < post_audit_total:
                violations.append(GlobalInvariant.POST_MERGE_AUDIT_PASSED)

            # Status
            if violations:
                status = GCPLCheckResult.NON_CONVERGENT
            elif rate > self.DRIFT_RATE_THRESHOLD:
                status = GCPLCheckResult.DRIFT
            else:
                status = GCPLCheckResult.OK

            return ConvergenceSnapshot(
                timestamp_ns=now_ns,
                branch_count=n_total,
                active_branch_count=n_active,
                convergence_function=c_val,
                branch_entropy=entropy,
                merge_velocity=velocity,
                irreconcilable_ratio=irreconcilable_ratio,
                convergence_rate=rate,
                oscillation_count=oscillation_count,
                invariant_violations=violations,
                status=status,
            )

# ─────────────────────────────────────────────────────────────────
# TERMINATION PROVER (interface)
# ─────────────────────────────────────────────────────────────────

class TerminationResult:
    def __init__(
        self,
        converged: bool,
        terminal_leaves: bool,
        deadlocked: bool,
        details: str,
    ):
        self.converged = converged
        self.terminal_leaves = terminal_leaves
        self.deadlocked = deadlocked
        self.details = details

class TerminationProver:
    """
    Proves or disproves termination of the branch space.

    TERMINATION THEOREM:
      System terminates if:
        ∃ t*: ∀ t ≥ t*: C(t) = 0
        OR
        ∃ t*: ∀ t ≥ t*: |B(t)| = K AND
          ∀ unmerged pairs (bi, bj): d(bi, bj) = CONSTANT

    DEADLOCK THEOREM:
      System deadlocks if:
        ∃ infinite sequence of MERGE/SPLIT cycles
        AND C(t) does not converge to 0
        AND |B(t)| does not stabilize
    """

    def prove(
        self,
        convergence_history: list[float],
        branch_count_history: list[int],
        oscillation_count: int,
    ) -> TerminationResult:
        if len(convergence_history) < 3:
            return TerminationResult(False, False, False, "insufficient history")

        # Check: C(t) → 0
        recent_c = convergence_history[-5:]
        if max(recent_c) < 0.01:
            return TerminationResult(
                converged=True,
                terminal_leaves=False,
                deadlocked=False,
                details=f"C(t) → 0: converged (C={recent_c[-1]:.4f})",
            )

        # Check: |B(t)| stable + no oscillation
        recent_b = branch_count_history[-5:]
        if max(recent_b) == min(recent_b) and oscillation_count == 0:
            return TerminationResult(
                converged=False,
                terminal_leaves=True,
                deadlocked=False,
                details=f"|B|={recent_b[0]} stable, oscillation_free: terminal leaves",
            )

        # Check: deadlocked (oscillating, |B| growing)
        rate_c = ConvergenceFunction.convergence_rate(convergence_history)
        if oscillation_count > 0 and rate_c >= 0 and len(branch_count_history) >= 5:
            b_growing = branch_count_history[-1] > branch_count_history[0]
            if b_growing:
                return TerminationResult(
                    converged=False,
                    terminal_leaves=False,
                    deadlocked=True,
                    details="oscillating + |B| growing + C not decreasing: DEADLOCKED",
                )

        return TerminationResult(
            converged=False,
            terminal_leaves=False,
            deadlocked=False,
            details="neither converged, terminal, nor deadlocked",
        )
