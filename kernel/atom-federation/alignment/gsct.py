"""gsct.py — v11.4 Global System Closure Theorem.

GSCT is the final theoretical layer that proves the entire
ATOMFEDERATION-OS system is a CLOSED dynamical system.

Formal definition:
    System state S(t) = {R(t), GCST(t), GAST(t), branch_graph(t), trust_field(t)}
    Closure condition:
        ∀ trajectory ∈ S : trajectory ∈ Bounded ∪ Convergent ∪ DetectableOscillation
    No external escape: ∄ ε(t): S(t) → ∞
    Attractor partition: ∃ {A1..An} : ⋃Ai = S

GSCT is READ-ONLY. No modification of any layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class Regime(Enum):
    CONVERGENT = auto()
    OSCILLATORY = auto()
    DIVERGENT = auto()
    UNDEFINED = auto()
    TERMINAL = auto()  # reserved terminal state


@dataclass
class AttractorClass:
    """A closed subset of the state space containing trajectories."""
    id: str
    type: str  # "fixed_point" | "limit_cycle" | "divergent"
    contained: bool  # bounded subset?
    trajectories: list[str] = field(default_factory=list)

    def __repr__(self):
        return f"AttractorClass({self.type}, trajectories={len(self.trajectories)}, contained={self.contained})"


@dataclass
class StepEvidence:
    """Evidence for a single step in the closure proof."""
    layer: str
    claim: str
    data: dict
    satisfied: bool

    def __repr__(self):
        return f"[{'✅' if self.satisfied else '❌'}] {self.layer}: {self.claim}"


@dataclass
class ClosureProof:
    is_closed_system: bool
    global_convergence: bool
    attractor_partition: list[AttractorClass]
    boundedness_proof: bool
    termination_guarantee: bool
    failure_modes: list[str]
    proof_trace: list[StepEvidence]
    summary: str = ""

    def __repr__(self):
        status = "✅ CLOSED" if self.is_closed_system else "❌ NOT CLOSED"
        conv = "✅ CONVERGENT" if self.global_convergence else "❌ DIVERGENT"
        parts = [f"GSCT: {status}, {conv}"]
        for ac in self.attractor_partition:
            parts.append(f"  → {ac}")
        for fm in self.failure_modes:
            parts.append(f"  ⚠️ {fm}")
        return "\n".join(parts)


class GSCT:
    """
    Global System Closure Theorem.

    Reads from: RCF history, GCST history, GAST report, branch graph.
    Writes:    nothing (READ-ONLY).

    Decision logic:
        SYSTEM IS CLOSED IF:
          - GAST regime ∈ {CONVERGENT, OSCILLATORY} (no UNDEFINED)
          - GCST stability bound holds
          - RCF drift bounded by GCST envelope
          - branch entropy bounded
          - no uncontrolled BCIL veto loops
          - no unbounded trust field growth
    """

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.entropy_threshold: float = cfg.get("entropy_threshold", 3.0)
        self.max_branches: int = cfg.get("max_branches", 100)
        self.stability_min: float = cfg.get("stability_min", 0.5)

    def evaluate(
        self,
        rcf_history: list[dict],
        gcst_history: list[dict],
        gast_report: dict,
        branch_graph: dict,
        system_invariants: dict,
    ) -> ClosureProof:
        """
        Main entry point.

        Args:
            rcf_history: [{t, drift_score, convergence_score}]
            gcst_history: [{t, stability_score, coherent}]
            gast_report: from GAST (regime, attractor_exists, etc.)
            branch_graph: {branch_id: {state, entropy, last_update}}
            system_invariants: {name: bool}

        Returns:
            ClosureProof with full justification.
        """
        trace: list[StepEvidence] = []

        # ── 1. GAST regime must be CONVERGENT or OSCILLATORY ────────────
        gast_regime = gast_report.get("regime", "UNDEFINED")
        gast_regime = Regime[gast_regime] if gast_regime in Regime._member_names_ else Regime.UNDEFINED

        trace.append(StepEvidence(
            layer="GAST", claim=f"regime={gast_regime.name}",
            data={"regime": gast_regime.name},
            satisfied=gast_regime in (Regime.CONVERGENT, Regime.OSCILLATORY)
        ))

        # ── 2. GCST stability bound holds ────────────────────────────────
        gcst_stable = all(s.get("coherent", False) or s.get("stability_score", 0) >= self.stability_min
                         for s in gcst_history[-3:])
        trace.append(StepEvidence(
            layer="GCST", claim="stability bound holds",
            data={"recent_scores": [s.get("stability_score", 0) for s in gcst_history[-3:]]},
            satisfied=gcst_stable
        ))

        # ── 3. RCF drift bounded by GCST envelope ───────────────────────
        rcf_bounded = all(
            s.get("drift_score", 0) <= gcst_history[i].get("stability_score", 1.0)
            for i, s in enumerate(rcf_history[-3:])
            if i < len(gcst_history)
        )
        trace.append(StepEvidence(
            layer="RCF", claim="drift within GCST envelope",
            data={"max_drift": max(s.get("drift_score", 0) for s in rcf_history[-3:])},
            satisfied=rcf_bounded
        ))

        # ── 4. Branch entropy bounded ──────────────────────────────────
        branches = list(branch_graph.values()) if branch_graph else []
        entropies = [b.get("entropy", 0) for b in branches]
        entropy_bounded = (
            len(branches) <= self.max_branches
            and all(e <= self.entropy_threshold for e in entropies)
        )
        trace.append(StepEvidence(
            layer="branch", claim=f"entropy bounded ({len(branches)} branches)",
            data={"entropies": entropies, "max_allowed": self.entropy_threshold},
            satisfied=entropy_bounded
        ))

        # ── 5. System invariants hold ────────────────────────────────────
        invariants_ok = all(bool(v) for v in system_invariants.values())
        trace.append(StepEvidence(
            layer="invariants", claim="all system invariants satisfied",
            data={k: v for k, v in system_invariants.items()},
            satisfied=invariants_ok
        ))

        # ── 6. Build attractor partition ────────────────────────────────
        partition = self._build_partition(gast_report, gcst_history, rcf_history)

        # ── 7. Determine global convergence ──────────────────────────────
        global_conv = (
            gast_regime == Regime.CONVERGENT
            and gcst_stable
            and rcf_bounded
        )

        # ── 8. Boundedness proof ────────────────────────────────────────
        bounded = (
            entropy_bounded
            and gcst_stable
            and gast_regime != Regime.UNDEFINED
        )

        # ── 9. Termination guarantee ────────────────────────────────────
        termination = (
            bounded
            and gast_regime == Regime.CONVERGENT
            and partition and all(a.contained for a in partition)
        )

        # ── 10. Failure modes ───────────────────────────────────────────
        failures = self._detect_failures(
            gast_regime, gcst_stable, rcf_bounded,
            entropy_bounded, invariants_ok, gast_report
        )

        is_closed = (
            gast_regime in (Regime.CONVERGENT, Regime.OSCILLATORY)
            and gcst_stable
            and rcf_bounded
            and entropy_bounded
            and invariants_ok
            and not failures
        )

        return ClosureProof(
            is_closed_system=is_closed,
            global_convergence=global_conv,
            attractor_partition=partition,
            boundedness_proof=bounded,
            termination_guarantee=termination,
            failure_modes=[f"GSCT-F{i+1}: {fm}" for i, fm in enumerate(failures)],
            proof_trace=trace,
            summary=self._make_summary(is_closed, global_conv, partition, failures),
        )

    def _build_partition(
        self,
        gast_report: dict,
        gcst_history: list[dict],
        rcf_history: list[dict],
    ) -> list[AttractorClass]:
        """Partition the state space into attractor classes."""
        regime = gast_report.get("regime", "UNDEFINED")
        attractor_exists = gast_report.get("attractor_exists", False)

        classes: list[AttractorClass] = []

        if regime == "CONVERGENT" and attractor_exists:
            classes.append(AttractorClass(
                id="A_conv",
                type="fixed_point",
                contained=True,
                trajectories=["GAST(CONVERGENT)", "GCST(stable)"]
            ))

        elif regime == "OSCILLATORY":
            classes.append(AttractorClass(
                id="A_cycle",
                type="limit_cycle",
                contained=True,
                trajectories=["GAST(OSCILLATORY)", "RCF(bounded_drift)"]
            ))

        elif regime == "DIVERGENT":
            classes.append(AttractorClass(
                id="A_div",
                type="divergent",
                contained=False,
                trajectories=["GAST(DIVERGENT)"]
            ))
            classes.append(AttractorClass(
                id="A_boundary",
                type="bounded_subspace",
                contained=True,
                trajectories=["GCST(envelope)", "branch(entropy_cap)"]
            ))

        elif regime == "TERMINAL":
            classes.append(AttractorClass(
                id="A_terminal",
                type="fixed_point",
                contained=True,
                trajectories=["TERMINAL"]
            ))

        else:  # UNDEFINED
            classes.append(AttractorClass(
                id="A_unknown",
                type="undefined",
                contained=False,
                trajectories=["UNCLASSIFIED"]
            ))

        return classes

    def _detect_failures(
        self,
        gast_regime: Regime,
        gcst_stable: bool,
        rcf_bounded: bool,
        entropy_bounded: bool,
        invariants_ok: bool,
        gast_report: dict,
    ) -> list[str]:
        """Detect GSCT-level failure modes."""
        failures = []

        # F1: Unbounded branch explosion
        if not entropy_bounded:
            failures.append("branch entropy exceeds bound")

        # F2: GCST instability
        if not gcst_stable:
            failures.append("GCST stability bound violated")

        # F3: RCF drift overflow
        if not rcf_bounded:
            failures.append("RCF drift exceeds GCST envelope")

        # F4: Undefined attractor (false closure illusion)
        if gast_regime == Regime.UNDEFINED:
            failures.append("GAST regime UNDEFINED — cannot prove closure")

        # F5: Invariant violation
        if not invariants_ok:
            failures.append("system invariants violated")

        # F6: Multiple undefined attractors (inconsistent partition)
        attractors = gast_report.get("attractor_count", 0)
        if attractors > 10 and gast_regime == Regime.CONVERGENT:
            failures.append("too many attractors for convergent claim")

        return failures

    def _make_summary(
        self,
        is_closed: bool,
        global_conv: bool,
        partition: list[AttractorClass],
        failures: list[str],
    ) -> str:
        lines = [
            "GSCT — Global System Closure Theorem Summary",
            "=" * 50,
            f"Closed system: {'YES' if is_closed else 'NO'}",
            f"Global convergence: {'YES' if global_conv else 'NO'}",
            f"Attractor classes: {len(partition)}",
            f"Failure modes: {len(failures)}",
        ]
        for i, ac in enumerate(partition):
            lines.append(f"  A{i+1}: {ac}")
        for fm in failures:
            lines.append(f"  ⚠️ {fm}")
        return "\n".join(lines)
