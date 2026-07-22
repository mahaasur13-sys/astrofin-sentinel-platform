"""
drift_detector.py — v10.0 Reality Alignment Layer

CORE: Semantic Plan Drift Detection Engine

Detects three orthogonal drift layers:
  L1 — Structural:  DAG dependencies violated during execution
  L2 — Causal:     execution order diverges from planned order
  L3 — Semantic:    execution outcome diverges from planner intent

DriftScore = w1*L1 + w2*L2 + w3*L3
  w1=0.30  w2=0.30  w3=0.40

Key invariant:
  Events are NEVER deleted. Rollback introduces a new causal branch
  that supersedes the drifted plan, preserving full audit trail.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from core.deterministic import DeterministicClock

# ─────────────────────────────────────────────────────────────────
# DRIFT TYPE TAXONOMY
# ─────────────────────────────────────────────────────────────────

class DriftType(Enum):
    NONE = "none"
    STRUCTURAL = "structural"    # L1
    CAUSAL = "causal"            # L2
    SEMANTIC = "semantic"        # L3
    COMPOUND = "compound"         # L1+L2+L3


class DriftSeverity(Enum):
    OK = auto()        # score < 0.20
    DEGRADED = auto()  # 0.20 ≤ score < 0.50
    CRITICAL = auto()  # 0.50 ≤ score < 0.80
    FATAL = auto()     # score ≥ 0.80


# ─────────────────────────────────────────────────────────────────
# EXECUTION TRACE RECORDING
# ─────────────────────────────────────────────────────────────────

@dataclass
class ExecutedNode:
    """A single executed DAG node from the execution trace."""
    node_id: str
    step_name: str
    tool: str
    planned_deps: tuple[str, ...]   # what planner said we depend on
    runtime_waits: tuple[str, ...]      # what we actually waited for
    start_ts_ns: int
    end_ts_ns: int
    success: bool
    output_hash: str                 # sha256 of serialized output
    error: str = ""
    retry_count: int = 0

    @property
    def duration_ms(self) -> float:
        return (self.end_ts_ns - self.start_ts_ns) / 1e6

    def structural_violations(self) -> list[str]:
        """
        L1 detection: planned_deps ⊈ actual_deps.
        A planned dependency was NOT satisfied before this node ran.
        """
        return [
            f"planned_dep={d} not satisfied"
            for d in self.planned_deps
            if d not in self.runtime_waits
        ]


@dataclass
class ExecutionTrace:
    """Complete execution trace for a DAG run. Immutable."""
    trace_id: str
    plan_id: str
    dag_hash: str
    goal: str
    nodes: list[ExecutedNode]
    started_at_ns: int
    finished_at_ns: int
    planner_confidence: float

    @property
    def total_duration_ms(self) -> float:
        return (self.finished_at_ns - self.started_at_ns) / 1e6

    @property
    def success_count(self) -> int:
        return sum(1 for n in self.nodes if n.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for n in self.nodes if not n.success)

    def causal_order(self) -> list[str]:
        """Actual execution order of node_ids."""
        return [n.node_id for n in self.nodes]


# ─────────────────────────────────────────────────────────────────
# PLAN GRAPH (SemanticPlanner output)
# ─────────────────────────────────────────────────────────────────

@dataclass
class PlannedNode:
    node_id: str
    step_name: str
    tool: str
    planned_deps: tuple[str, ...]
    expected_duration_ms: float
    priority: int = 1


@dataclass
class PlannedDAG:
    """DAG produced by SemanticPlanner. Immutable snapshot."""
    plan_id: str
    goal: str
    nodes: list[PlannedNode]
    topological_order: list[str]
    confidence: float
    adaptation_notes: list[str] = field(default_factory=list)

    def node_map(self) -> dict[str, PlannedNode]:
        return {n.node_id: n for n in self.nodes}

    def planned_order_for(self, node_id: str) -> int:
        try:
            return self.topological_order.index(node_id)
        except ValueError:
            return -1


# ─────────────────────────────────────────────────────────────────
# LAYER RESULTS
# ─────────────────────────────────────────────────────────────────

@dataclass
class Layer1Result:
    """L1 — Structural: DAG dependency violations."""
    violation_count: int
    violated_nodes: list[str]
    violation_rate: float
    details: list[str]

    @property
    def score(self) -> float:
        return min(1.0, self.violation_rate * 2.0)


@dataclass
class Layer2Result:
    """L2 — Causal: execution order vs planned topological order."""
    inversion_count: int
    total_pairs: int
    inversion_ratio: float
    inverted_pairs: list[tuple[str, str]]
    details: list[str]

    @property
    def score(self) -> float:
        return self.inversion_ratio


@dataclass
class Layer3Result:
    """L3 — Semantic: outcome diverges from planner intent."""
    semantic_distance: float         # 0..1
    fidelity_components: dict[str, float]
    is_diverged: bool

    @property
    def score(self) -> float:
        return self.semantic_distance


@dataclass
class CompositeDriftReport:
    """Full drift analysis result. Immutable."""
    trace_id: str
    plan_id: str
    computed_at_ns: int
    layer1: Layer1Result
    layer2: Layer2Result
    layer3: Layer3Result
    drift_score: float
    severity: DriftSeverity
    is_rollback_candidate: bool
    correction_type: str   # "none" | "shadow" | "weight_adjust" | "partial" | "full"
    rollback_target_nodes: list[str]

    def summary(self) -> str:
        return (
            f"[{self.severity.name}] score={self.drift_score:.3f} "
            f"(L1={self.layer1.score:.2f} L2={self.layer2.score:.2f} L3={self.layer3.score:.3f}) "
            f"→ {self.correction_type}"
        )


# ─────────────────────────────────────────────────────────────────
# LAYER 1: STRUCTURAL DRIFT
# ─────────────────────────────────────────────────────────────────

class StructuralDriftDetector:
    """L1: planned_deps ⊈ actual_deps → structural violation."""

    def analyze(self, trace: ExecutionTrace) -> Layer1Result:
        if not trace.nodes:
            return Layer1Result(0, [], 0.0, ["empty trace"])

        violations, details = [], []
        for node in trace.nodes:
            v = node.structural_violations()
            if v:
                violations.append(node.node_id)
                details.append(f"node={node.node_id} step={node.step_name}: {'; '.join(v)}")

        total = len(trace.nodes)
        rate = len(violations) / total if total > 0 else 0.0

        return Layer1Result(
            violation_count=len(violations),
            violated_nodes=violations,
            violation_rate=rate,
            details=details,
        )


# ─────────────────────────────────────────────────────────────────
# LAYER 2: CAUSAL ORDER DRIFT
# ─────────────────────────────────────────────────────────────────

class CausalOrderDriftDetector:
    """
    L2: Kendall-tau-like pairwise inversion counting.
    Count (A,B) where planned(A)<planned(B) but executed(A)>executed(B).
    """

    def analyze(self, trace: ExecutionTrace, planned: PlannedDAG) -> Layer2Result:
        if not trace.nodes or not planned.topological_order:
            return Layer2Result(0, 0, 0.0, [], ["empty input"])

        planned_pos = {nid: i for i, nid in enumerate(planned.topological_order)}
        executed_order = trace.causal_order()
        executed_pos = {nid: i for i, nid in enumerate(executed_order)}

        common = set(planned_pos) & set(executed_pos)
        if not common:
            return Layer2Result(0, 0, 0.0, [], ["no common nodes"])

        inversions: list[tuple[str, str]] = []

        # Build a reverse lookup: which planned nodes list each node as a dependency
        # dep_to_nodes[dep_id] = list of node_ids that depend on dep_id
        dep_to_nodes: dict[str, set[str]] = {}
        for pnode in planned.nodes:
            for dep in pnode.planned_deps:
                dep_to_nodes.setdefault(dep, set()).add(pnode.node_id)

        for exec_node in trace.nodes:
            if exec_node.node_id not in common:
                continue
            exec_idx = executed_pos[exec_node.node_id]

            # Which planned deps does this node have?
            pnode_map = planned.node_map()
            pnode = pnode_map.get(exec_node.node_id)
            if pnode is None:
                continue

            for dep_id in pnode.planned_deps:
                if dep_id not in executed_pos:
                    # Dep not executed → not a causal inversion (different failure mode)
                    continue
                dep_idx = executed_pos[dep_id]
                # Causal inversion: exec_node depends on dep_id but dep ran AFTER exec_node
                # (dep was supposed to finish before exec_node started, but it ran after)
                if dep_idx >= exec_idx:
                    inversions.append((dep_id, exec_node.node_id))

        inv_ratio = len(inversions) / len(executed_order) if len(executed_order) > 0 else 0.0

        details = []
        if executed_order and planned.topological_order:
            if executed_order[0] != planned.topological_order[0]:
                details.append(
                    f"entry_mismatch: planned={planned.topological_order[0]} "
                    f"executed={executed_order[0]}"
                )
        if inversions:
            sample = inversions[:5]
            details.append(
                f"inversions={len(inversions)} sample=[{', '.join(f'{a}→{b}' for a, b in sample)}]"
            )

        return Layer2Result(
            inversion_count=len(inversions),
            total_pairs=len(executed_order),
            inversion_ratio=inv_ratio,
            inverted_pairs=inversions,
            details=details,
        )


# ─────────────────────────────────────────────────────────────────
# LAYER 3: SEMANTIC FIDELITY
# ─────────────────────────────────────────────────────────────────

class SemanticFidelityDetector:
    """
    L3: semantic divergence between execution outcome and planner intent.
    Components:
      1. Goal distance: embedding(goal) vs embedding(outcome_text)
      2. Failure rate: fraction of failed nodes
      3. Tool fidelity: was the right tool mix used?
    """

    def __init__(self, embedding_model: Any = None):
        self._model = embedding_model
        self._cache: dict[str, list[float]] = {}

    def _pseudo_embed(self, text: str) -> list[float]:
        """
        Deterministic pseudo-embedding: identical text → identical vectors → cosine distance = 0.
        Uses sha256 digest as stable float vector, centered so average is ~0.
        """
        if text in self._cache:
            return self._cache[text]
        h = hashlib.sha256(text.encode()).digest()
        vec = [float(b) / 255.0 - 0.5 for b in h[:64]]
        self._cache[text] = vec
        return vec

    def _embed(self, text: str) -> list[float]:
        if self._model is not None:
            vec = self._model.encode(text)
            return vec.tolist() if hasattr(vec, 'tolist') else vec
        return self._pseudo_embed(text)

    def _word_set(self, text: str) -> frozenset[str]:
        """Extract lowercase alphanumeric words from text."""
        import re
        words = re.findall(r'[a-z0-9]+', text.lower())
        return frozenset(words)

    def _text_distance(self, text_a: str, text_b: str) -> float:
        """Character-trigram Jaccard distance. Same text → 0, unrelated → ~1."""
        def _trigrams(t: str) -> frozenset[str]:
            if len(t) < 3:
                return frozenset([t]) if t else frozenset()
            return frozenset(t[i:i+3] for i in range(len(t) - 2))

        # Use trigram sets: same word content → high overlap → low distance
        a_set = _trigrams(text_a.lower())
        b_set = _trigrams(text_b.lower())
        if not a_set and not b_set:
            return 0.0
        if not a_set or not b_set:
            return 1.0
        intersection = len(a_set & b_set)
        union = len(a_set | b_set)
        return 1.0 - (intersection / union) if union > 0 else 0.0

    def _build_outcome_text(self, trace: ExecutionTrace) -> str:
        parts = []
        for n in trace.nodes:
            if n.success:
                parts.append(f"step:{n.step_name} tool:{n.tool} ok")
            else:
                parts.append(f"step:{n.step_name} FAILED:{n.error[:80]}")
        return "; ".join(parts)

    def analyze(self, trace: ExecutionTrace, planned: PlannedDAG) -> Layer3Result:
        if not trace.nodes:
            return Layer3Result(semantic_distance=0.0, fidelity_components={}, is_diverged=False)

        # ── Component 1: Goal alignment via word Jaccard distance ──────────
        # word_Jaccard_distance: 0=identical vocab, 1=disjoint vocab
        # Must be INVERTED before use in composite (high distance = low alignment)
        goal_words = frozenset(w.lower() for w in planned.goal.split() if w.isalnum())
        outcome_words = frozenset(w.lower() for s in trace.nodes for w in (s.step_name.split() + [s.tool]) if w.isalnum())
        goal_outcome_intersection = goal_words & outcome_words
        if goal_words and outcome_words:
            goal_words_distance = 1.0 - len(goal_outcome_intersection) / len(goal_words)
        else:
            goal_words_distance = 0.0

        # ── Component 2: Execution success ─────────────────────────────────
        total = len(trace.nodes)
        failed = sum(1 for n in trace.nodes if not n.success)
        failed_rate = failed / total if total > 0 else 0.0

        # ── Component 3: Tool relevance ─────────────────────────────────────
        relevant_tools = {n.tool for n in trace.nodes}
        relevant = sum(1 for n in trace.nodes if n.success)
        tool_extraneous = (total - relevant) / total if total > 0 else 0.0

        # ── Normalize each component to [0, 1] ALIGNMENT scores ────────────
        # Higher = better alignment (same scale as probability)
        # Using exponential decay: alignment = exp(-k × distance)
        k = 3.0  # decay constant — tuned so goal_distance=0.833 → alignment≈0.08
        goal_alignment = 1.0 - (1.0 - math.exp(-k * goal_words_distance))
        failure_alignment = 1.0 - failed_rate
        tool_alignment = 1.0 - tool_extraneous

        # Weighted semantic distance (inverted: 1 - alignment = drift)
        semantic_distance = (
            0.50 * (1.0 - goal_alignment) +
            0.30 * (1.0 - failure_alignment) +
            0.20 * (1.0 - tool_alignment)
        )

        fidelity_components = {
            "goal_distance": goal_words_distance,
            "goal_alignment": goal_alignment,
            "failure_rate": failed_rate,
            "tool_extraneous": tool_extraneous,
        }

        is_diverged = (
            goal_words_distance > 0.5
            or failed_rate > 0.0
            or tool_extraneous > 0.3
        )

        return Layer3Result(
            semantic_distance=round(semantic_distance, 6),
            fidelity_components=fidelity_components,
            is_diverged=is_diverged,
        )


# ─────────────────────────────────────────────────────────────────
# DRIFT ENGINE — COMPOSITE SCORING
# ─────────────────────────────────────────────────────────────────

class DriftEngine:
    """
    Composite drift detection. Binds planner output (PlannedDAG)
    against execution reality (ExecutionTrace).

    Architecture:
        Executor → ExecutionTrace
                     ↓
        PlanRealityComparator (binds D ↔ R)
                     ↓
              DriftEngine.analyze(D, R)
                     ↓
        CompositeDriftReport → RollbackEngine / PlannerCorrector
    """

    WEIGHTS = (0.15, 0.15, 0.70)  # w1=structural, w2=causal, w3=semantic
    # Semantic fidelity dominates: a failed node or goal misalignment alone
    # justifies a rollback. Structural/causal serve as tie-breakers.

    def __init__(
        self,
        structural: StructuralDriftDetector | None = None,
        causal: CausalOrderDriftDetector | None = None,
        semantic: SemanticFidelityDetector | None = None,
    ):
        self._l1 = structural or StructuralDriftDetector()
        self._l2 = causal or CausalOrderDriftDetector()
        self._l3 = semantic or SemanticFidelityDetector()

    def analyze(self, trace: ExecutionTrace, planned: PlannedDAG) -> CompositeDriftReport:
        l1 = self._l1.analyze(trace)
        l2 = self._l2.analyze(trace, planned)
        l3 = self._l3.analyze(trace, planned)

        w1, w2, w3 = self.WEIGHTS
        score = max(0.0, min(1.0, w1 * l1.score + w2 * l2.score + w3 * l3.score))
        severity = self._severity(score)
        rollback_targets = self._rollback_targets(l1, l2, l3, trace)
        correction = self._correction_type(score, severity, l3.is_diverged)

        return CompositeDriftReport(
            trace_id=trace.trace_id,
            plan_id=trace.plan_id,
            computed_at_ns=DeterministicClock.get_tick_ns(),
            layer1=l1,
            layer2=l2,
            layer3=l3,
            drift_score=score,
            severity=severity,
            is_rollback_candidate=severity in (DriftSeverity.CRITICAL, DriftSeverity.FATAL),
            correction_type=correction,
            rollback_target_nodes=rollback_targets,
        )

    @staticmethod
    def _severity(score: float) -> DriftSeverity:
        if score < 0.10:
            return DriftSeverity.OK
        if score < 0.30:
            return DriftSeverity.DEGRADED
        if score < 0.50:
            return DriftSeverity.CRITICAL
        return DriftSeverity.FATAL

    @staticmethod
    def _rollback_targets(
        l1: Layer1Result,
        l2: Layer2Result,
        l3: Layer3Result,
        trace: ExecutionTrace,
    ) -> list[str]:
        targets: list[str] = []
        targets.extend(l1.violated_nodes)
        if l2.inverted_pairs:
            targets.append(l2.inverted_pairs[0][1])
        if l3_fail := [n.node_id for n in trace.nodes if not n.success]:
            targets.extend(l3_fail[:3])
        return list(dict.fromkeys(targets))

    @staticmethod
    def _correction_type(
        score: float,
        severity: DriftSeverity,
        l3_diverged: bool,
    ) -> str:
        if severity == DriftSeverity.OK:
            return "none"
        if severity == DriftSeverity.DEGRADED:
            return "shadow"
        if l3_diverged:
            return "full"
        if severity == DriftSeverity.CRITICAL:
            return "partial"
        return "full"
