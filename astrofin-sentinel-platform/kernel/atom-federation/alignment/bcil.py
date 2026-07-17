"""bcil.py — v10.4 Byzantine-Convergence Integration Layer."""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto


# ─── Byzantine Types ───────────────────────────────────────────────
class ByzantineFailureType(Enum):
    NONE = auto()
    BYZANTINE_BRANCH_DOMINATED = auto()
    QUORUM_BYPASS = auto()
    TRUST_INFLATION = auto()
    EQUIVOCATION = auto()
    CONVERGENCE_TO_INVALID = auto()
    SPLIT_BRAIN = auto()

@dataclass
class QuorumSpec:
    n_nodes: int
    f_byzantine: int
    @property
    def quorum_size(self) -> int:
        return 2 * self.f_byzantine + 1
    @property
    def honest_majority(self) -> int:
        return self.n_nodes - self.f_byzantine

@dataclass
class BranchTrust:
    branch_id: str
    raw_trust: float
    trust_weight: float
    voter_count: int
    is_byzantine_suspect: bool
    quorum_covered: bool
    trust_fraction: float

@dataclass
class ByzantineRiskAssessment:
    branch_trusts: dict[str, BranchTrust]
    max_risk_branch: str | None
    max_risk_score: float
    dominating_byzantine: bool
    equivocation_detected: bool
    conflicting_pairs: list[tuple[str, str]]
    split_brain: bool
    byzantine_nodes_suspected: list[str]

@dataclass
class MergeDecision:
    allowed: bool
    blocked_by: ByzantineFailureType | None
    blocked_branches: list[str]
    c_b: float
    byzantine_risk: float
    base_convergence: float
    lambda_coefficient: float
    merge_type: str
    quorum_satisfied: bool
    trust_threshold_met: bool
    confidence: float
    explanation: str

@dataclass
class BCILReport:
    convergent: bool
    c_b: float
    byzantine_risk: float
    base_convergence: float
    lambda_coefficient: float
    merge_allowed: bool
    merge_decision: MergeDecision
    risk_assessment: ByzantineRiskAssessment
    failure_type: ByzantineFailureType
    failure_severity: float
    gcpl_convergence_preserved: bool
    safe_state: bool
    honest_can_progress: bool
    elapsed_ms: float

# ─── Byzantine Convergence Function ──────────────────────────────────
class ByzantineConvergenceFunction:
    DEFAULT_LAMBDA = 0.5
    def __init__(self, lambda_coefficient: float = DEFAULT_LAMBDA):
        self.lambda_coefficient = lambda_coefficient

    def compute(self, gcpl_convergence: float, byzantine_risk: float) -> float:
        c_b = gcpl_convergence + self.lambda_coefficient * byzantine_risk
        return min(1.0, max(0.0, c_b))

# ─── Byzantine Risk Assessor ────────────────────────────────────────
class ByzantineRiskAssessor:
    TRUST_INFLATION_THRESHOLD = 0.85
    MIN_HONEST_WEIGHT = 0.34
    def __init__(self, quorum: QuorumSpec):
        self.quorum = quorum

    def assess(
        self,
        branch_trusts: dict[str, float],
        digest_by_branch: dict[str, str],
        node_trust: dict[str, float],
        voter_assignments: dict[str, list[str]],
    ) -> ByzantineRiskAssessment:
        total_trust = sum(branch_trusts.values()) or 1.0
        assessments: dict[str, BranchTrust] = {}
        byzantine_nodes: list[str] = []
        for branch_id, raw_trust in branch_trusts.items():
            voters = voter_assignments.get(branch_id, [])
            voter_trusts = [node_trust.get(v, 0.0) for v in voters]
            avg_voter_trust = (sum(voter_trusts) / len(voter_trusts)) if voters else 0.0
            is_byzantine_suspect = (
                len(voters) <= self.quorum.f_byzantine + 1
                and avg_voter_trust > self.TRUST_INFLATION_THRESHOLD
            )
            trust_fraction = raw_trust / total_trust
            quorum_covered = len(voters) >= self.quorum.quorum_size
            assessments[branch_id] = BranchTrust(
                branch_id=branch_id,
                raw_trust=raw_trust,
                trust_weight=raw_trust,
                voter_count=len(voters),
                is_byzantine_suspect=is_byzantine_suspect,
                quorum_covered=quorum_covered,
                trust_fraction=trust_fraction,
            )
            if is_byzantine_suspect:
                byzantine_nodes.extend(voters)

        risk_scores = self._compute_risk_scores(assessments)
        max_risk_branch = (max(risk_scores, key=risk_scores.get) if risk_scores else None)
        max_risk_score = risk_scores.get(max_risk_branch, 0.0) if max_risk_branch else 0.0

        top_branch = (max(branch_trusts, key=branch_trusts.get) if branch_trusts else None)
        dominating_byzantine = False
        if top_branch and top_branch in assessments:
            bt = assessments[top_branch]
            if bt.is_byzantine_suspect and bt.trust_fraction > self.MIN_HONEST_WEIGHT:
                dominating_byzantine = True

        conflicting = self._detect_equivocation(digest_by_branch, voter_assignments)
        quorum_passed = [b for b, bt in assessments.items() if bt.quorum_covered]
        split_brain = len(quorum_passed) >= 2

        return ByzantineRiskAssessment(
            branch_trusts=assessments,
            max_risk_branch=max_risk_branch,
            max_risk_score=max_risk_score,
            dominating_byzantine=dominating_byzantine,
            equivocation_detected=len(conflicting) > 0,
            conflicting_pairs=conflicting,
            split_brain=split_brain,
            byzantine_nodes_suspected=list(set(byzantine_nodes)),
        )

    def _compute_risk_scores(self, assessments: dict[str, BranchTrust]) -> dict[str, float]:
        risks = {}
        for branch_id, bt in assessments.items():
            if bt.voter_count == 0:
                risks[branch_id] = 0.0
                continue
            quorum_gap = max(0, self.quorum.quorum_size - bt.voter_count)
            quorum_gap_penalty = quorum_gap / max(1, self.quorum.quorum_size)
            dominance_penalty = 0.5 if bt.is_byzantine_suspect else 0.0
            trust_penalty = 1.0 - bt.trust_fraction
            risk = (0.5 * trust_penalty + 0.3 * dominance_penalty + 0.2 * quorum_gap_penalty)
            risks[branch_id] = min(1.0, risk)
        return risks

    def _detect_equivocation(self, digest_by_branch: dict[str, str], voter_assignments: dict[str, list[str]]) -> list[tuple[str, str]]:
        if len(digest_by_branch) < 2:
            return []
        conflicts = []
        branches = list(digest_by_branch.keys())
        # Only flag equivocation if the SAME voter set saw different digests
        # (signals Byzantine node sending different values to different honest peers)
        voter_set_by_branch = {b: frozenset(voter_assignments.get(b, [])) for b in branches}
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                ba, bb = branches[i], branches[j]
                da, db = digest_by_branch[ba], digest_by_branch[bb]
                # Different digest?
                diff_ratio = self._digest_diff_ratio(da, db)
                if diff_ratio < 0.05:
                    continue  # Essentially identical — not equivocation
                if diff_ratio > 0.9:
                    continue  # Completely different content — not equivocation
                # Same voter set + different digests = REAL equivocation
                if voter_set_by_branch[ba] == voter_set_by_branch[bb]:
                    conflicts.append((ba, bb))
        return conflicts

    @staticmethod
    def _digest_diff_ratio(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        if len(a) != len(b):
            return 1.0
        matches = sum(ca == cb for ca, cb in zip(a, b))
        return 1.0 - matches / len(a)

# ─── Trust-Weighted Merge Decider ─────────────────────────────────
class TrustWeightedMergeDecider:
    MIN_TRUST_THRESHOLD = 0.30
    SPLIT_BRAIN_TRUST_GAP = 0.10
    def __init__(self, quorum: QuorumSpec):
        self.quorum = quorum

    def decide(
        self,
        gcpl_base_convergence: float,
        gcpl_convergence_rate: float,
        branch_trusts: dict[str, float],
        risk_assessment: ByzantineRiskAssessment,
    ) -> MergeDecision:
        if not branch_trusts:
            return MergeDecision(
                allowed=False, blocked_by=ByzantineFailureType.NONE,
                blocked_branches=[], c_b=gcpl_base_convergence,
                byzantine_risk=0.0, base_convergence=gcpl_base_convergence,
                lambda_coefficient=0.0, merge_type="BLOCKED",
                quorum_satisfied=False, trust_threshold_met=False,
                confidence=0.0, explanation="No branches"
            )

        assessments = risk_assessment.branch_trusts
        quorum_passed = [b for b, bt in assessments.items() if bt.quorum_covered]
        all_trusts = list(branch_trusts.values())
        if all_trusts:
            max_trust = max(all_trusts)
            min(all_trusts)
        else:
            max_trust = 0.0

        trust_threshold_met = max_trust >= self.MIN_TRUST_THRESHOLD
        quorum_satisfied = len(quorum_passed) >= 1

        if risk_assessment.equivocation_detected:
            return MergeDecision(
                allowed=False, blocked_by=ByzantineFailureType.EQUIVOCATION,
                blocked_branches=[b for b, _ in risk_assessment.conflicting_pairs],
                c_b=gcpl_base_convergence, byzantine_risk=risk_assessment.max_risk_score,
                base_convergence=gcpl_base_convergence, lambda_coefficient=0.5,
                merge_type="BLOCKED", quorum_satisfied=quorum_satisfied,
                trust_threshold_met=trust_threshold_met,
                confidence=0.0,
                explanation="Equivocation detected across branches"
            )

        # Check quorum BEFORE byzantine dominance
        if not quorum_satisfied:
            return MergeDecision(
                allowed=False, blocked_by=ByzantineFailureType.QUORUM_BYPASS,
                blocked_branches=list(branch_trusts.keys()),
                c_b=gcpl_base_convergence, byzantine_risk=risk_assessment.max_risk_score,
                base_convergence=gcpl_base_convergence, lambda_coefficient=0.5,
                merge_type="BLOCKED", quorum_satisfied=False,
                trust_threshold_met=trust_threshold_met,
                confidence=0.0,
                explanation="Quorum not satisfied"
            )

        if risk_assessment.dominating_byzantine:
            return MergeDecision(
                allowed=False,
                blocked_by=ByzantineFailureType.BYZANTINE_BRANCH_DOMINATED,
                blocked_branches=[risk_assessment.max_risk_branch] if risk_assessment.max_risk_branch else [],
                c_b=gcpl_base_convergence, byzantine_risk=risk_assessment.max_risk_score,
                base_convergence=gcpl_base_convergence, lambda_coefficient=0.5,
                merge_type="BLOCKED", quorum_satisfied=quorum_satisfied,
                trust_threshold_met=trust_threshold_met,
                confidence=0.0,
                explanation="Byzantine nodes dominate highest-trust branch"
            )

        if risk_assessment.split_brain:
            return MergeDecision(
                allowed=False, blocked_by=ByzantineFailureType.SPLIT_BRAIN,
                blocked_branches=quorum_passed,
                c_b=gcpl_base_convergence, byzantine_risk=risk_assessment.max_risk_score,
                base_convergence=gcpl_base_convergence, lambda_coefficient=0.5,
                merge_type="SPLIT", quorum_satisfied=True,
                trust_threshold_met=trust_threshold_met,
                confidence=0.0,
                explanation="Split-brain: multiple branches have quorum"
            )

        if risk_assessment.max_risk_score > 0.7:
            return MergeDecision(
                allowed=False, blocked_by=ByzantineFailureType.TRUST_INFLATION,
                blocked_branches=[risk_assessment.max_risk_branch] if risk_assessment.max_risk_branch else [],
                c_b=gcpl_base_convergence, byzantine_risk=risk_assessment.max_risk_score,
                base_convergence=gcpl_base_convergence, lambda_coefficient=0.5,
                merge_type="BLOCKED", quorum_satisfied=quorum_satisfied,
                trust_threshold_met=trust_threshold_met,
                confidence=0.0,
                explanation="Byzantine risk too high"
            )

        if not trust_threshold_met:
            return MergeDecision(
                allowed=False, blocked_by=ByzantineFailureType.TRUST_INFLATION,
                blocked_branches=list(branch_trusts.keys()),
                c_b=gcpl_base_convergence, byzantine_risk=risk_assessment.max_risk_score,
                base_convergence=gcpl_base_convergence, lambda_coefficient=0.5,
                merge_type="BLOCKED", quorum_satisfied=quorum_satisfied,
                trust_threshold_met=False,
                confidence=0.0,
                explanation=f"Trust below threshold {self.MIN_TRUST_THRESHOLD}"
            )

        return MergeDecision(
            allowed=True, blocked_by=None, blocked_branches=[],
            c_b=gcpl_base_convergence, byzantine_risk=risk_assessment.max_risk_score,
            base_convergence=gcpl_base_convergence, lambda_coefficient=0.5,
            merge_type="MERGE", quorum_satisfied=quorum_satisfied,
            trust_threshold_met=True,
            confidence=0.8,
            explanation="Merge allowed: quorum satisfied, trust sufficient, no Byzantine risk"
        )

# ─── BCIL ────────────────────────────────────────────────────────
class BCIL:
    def __init__(self, quorum: QuorumSpec, lambda_coefficient: float = 0.5):
        self.quorum = quorum
        self.cf = ByzantineConvergenceFunction(lambda_coefficient)
        self.assessor = ByzantineRiskAssessor(quorum)
        self.decider = TrustWeightedMergeDecider(quorum)

    def analyze(
        self,
        branches: list[dict],  # [{branch_id, digest}]
        trust_scores: dict[str, float],  # branch_id -> trust
        node_trust: dict[str, float],  # node_id -> trust
        voter_assignments: dict[str, list[str]],  # branch_id -> [node_ids]
        gcpl_convergence: float,
        gcpl_convergence_rate: float = 0.0,
    ) -> BCILReport:
        t0 = time.time()
        branch_ids = [b["branch_id"] for b in branches]
        branch_trusts = {bid: trust_scores.get(bid, 0.0) for bid in branch_ids}
        digest_by_branch = {b["branch_id"]: b["digest"] for b in branches if "digest" in b}

        risk = self.assessor.assess(branch_trusts, digest_by_branch, node_trust, voter_assignments)
        decision = self.decider.decide(gcpl_convergence, gcpl_convergence_rate, branch_trusts, risk)
        c_b = self.cf.compute(gcpl_convergence, risk.max_risk_score)

        failure_type = decision.blocked_by or ByzantineFailureType.NONE
        safe_state = decision.allowed and not risk.dominating_byzantine and not risk.equivocation_detected
        honest_can_progress = (
            len([n for n, t in node_trust.items() if t >= 0.5]) >= self.quorum.honest_majority
        )
        gcpl_preserved = (decision.allowed or failure_type == ByzantineFailureType.NONE)

        return BCILReport(
            convergent=decision.allowed,
            c_b=c_b,
            byzantine_risk=risk.max_risk_score,
            base_convergence=gcpl_convergence,
            lambda_coefficient=self.cf.lambda_coefficient,
            merge_allowed=decision.allowed,
            merge_decision=decision,
            risk_assessment=risk,
            failure_type=failure_type,
            failure_severity=risk.max_risk_score,
            gcpl_convergence_preserved=gcpl_preserved,
            safe_state=safe_state,
            honest_can_progress=honest_can_progress,
            elapsed_ms=(time.time() - t0) * 1000,
        )
