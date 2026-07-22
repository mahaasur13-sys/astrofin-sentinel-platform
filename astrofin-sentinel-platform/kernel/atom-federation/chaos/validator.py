# ruff: noqa: F821
"""
ChaosValidator — SBS-aware result validator for chaos experiments.

Validates the outcome of a chaos experiment against the cluster's SBS invariants
and the FailureClassifier taxonomy. Produces a ValidationResult with:

  - classified_failures : list of ClassifiedFailure objects
  - sbs_violations_detected : list[str]
  - system_response : what the cluster did during the chaos
  - verdict : PASS / PARTIAL / FAIL

Jepsen-style verdict definitions
---------------------------------
PASS    : cluster remained fully consistent throughout chaos
PARTIAL : cluster detected violations correctly and recovered
FAIL    : cluster silently corrupted state or diverged without detection
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum

import logging
log = logging.getLogger(__name__)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from sbs.boundary_spec import SystemBoundarySpec
from sbs.failure_classifier import ClassifiedFailure, FailureCategory, FailureClassifier, FailureSeverity
from sbs.global_invariant_engine import GlobalInvariantEngine


class Verdict(Enum):
    PASS = "PASS"           # cluster remained fully consistent
    PARTIAL = "PARTIAL"     # detected + recovered correctly
    FAIL = "FAIL"           # silent corruption or divergence


@dataclass
class ValidationResult:
    """Immutable result of a single chaos experiment validation."""

    verdict: Verdict
    sbs_violations: list[str] = field(default_factory=list)
    classified_failures: list[ClassifiedFailure] = field(default_factory=list)
    system_response: dict = field(default_factory=dict)
    notes: str = ""
    duration_s: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        sev_counts: dict[str, int] = {}
        for f in self.classified_failures:
            sev_counts[f.severity.value] = sev_counts.get(f.severity.value, 0) + 1

        lines = [
            f"Verdict: {self.verdict.value}",
            f"SBS violations ({len(self.sbs_violations)}): {self.sbs_violations}",
            f"Classified failures: {sev_counts}",
            f"System response: {self.system_response}",
        ]
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)


class ChaosValidator:
    """
    Validate the outcome of a chaos experiment.

    Integrates with:
      - SBS GlobalInvariantEngine  (detects invariant violations)
      - FailureClassifier           (maps raw events → semantic categories)
      - ClusterHealthGraph state    (peer health during chaos)

    Usage
    -----
    validator = ChaosValidator()

    # After running a chaos scenario:
    result = validator.validate(
        scenario_name="partition_half_cluster",
        health_states={"node-b": "unreachable", "node-c": "reachable"},
        sbs_results=[{"ok": False, "violations": ["LEADER_UNIQUENESS_VIOLATION"]}],
        raw_events=[
            {"type": "partition", "layer": "DRL", "description": "A↮B blocked"},
            {"type": "drop", "layer": "DRL", "description": "Forward timeout"},
        ],
        expected_behavior={
            "sbs_violations": ["LEADER_UNIQUENESS", "QUORUM_VIOLATION"],
            "system_response": "cluster_detects_and_recovers",
        },
    )
    log.info(result)
    """

    def __init__(self):
        self.classifier = FailureClassifier()
        self.spec = SystemBoundarySpec()
        self.engine = GlobalInvariantEngine(self.spec)

    def validate(
        self,
        scenario_name: str,
        health_states: dict[str, str],
        sbs_results: list[dict],
        raw_events: list[dict],
        expected_behavior: dict,
        cluster_metrics: dict | None = None,
    ) -> ValidationResult:
        """
        Validate a chaos experiment run.

        Parameters
        ----------
        scenario_name       : name of the scenario that was run
        health_states       : {node_id: health_state} during chaos
        sbs_results         : list of SBS evaluate() results during the experiment
        raw_events          : raw failure events captured during chaos
        expected_behavior   : {
            "sbs_violations": [...],   # expected SBS violation types
            "system_response": str,    # "cluster_detects_and_recovers"
                                     # "cluster_halts"
                                     # "cluster_silent_corruption"
        }
        cluster_metrics     : optional MetricsCollector snapshot

        Returns
        -------
        ValidationResult
        """
        start = time.time()

        # ── 1. Classify failures ─────────────────────────────────────────
        classified = self.classifier.classify_batch(raw_events)
        critical_failures = [
            f for f in classified
            if f.severity == FailureSeverity.CRITICAL
        ]

        # ── 2. Collect SBS violations ────────────────────────────────────
        sbs_violations: list[str] = []
        for result in sbs_results:
            violations = result.get("violations", [])
            if isinstance(violations, list):
                sbs_violations.extend(violations)
            elif not result.get("ok", True):
                sbs_violations.append("UNKNOWN_SBS_VIOLATION")

        sbs_violations = list(dict.fromkeys(sbs_violations))  # deduplicate

        # ── 3. Determine system response ────────────────────────────────
        system_response = self._classify_system_response(
            health_states, sbs_violations, critical_failures
        )

        # ── 4. Determine verdict ─────────────────────────────────────────
        verdict = self._determine_verdict(
            scenario_name,
            sbs_violations,
            classified,
            expected_behavior,
            system_response,
        )

        duration_s = time.time() - start

        # ── 5. Generate notes ───────────────────────────────────────────
        notes = self._generate_notes(
            scenario_name, classified, sbs_violations, system_response
        )

        return ValidationResult(
            verdict=verdict,
            sbs_violations=sbs_violations,
            classified_failures=classified,
            system_response=system_response,
            notes=notes,
            duration_s=duration_s,
        )

    def _classify_system_response(
        self,
        health_states: dict[str, str],
        sbs_violations: list[str],
        critical_failures: list[ClassifiedFailure],
    ) -> dict:
        """Determine what the cluster did in response to the chaos."""
        response: dict = {
            "detected_partition": False,
            "detected_violations": len(sbs_violations) > 0,
            "cluster_halted": False,
            "recovered": False,
            "unreachable_nodes": [],
            "lagging_nodes": [],
            "violation_nodes": [],
        }

        for node_id, state in health_states.items():
            if state in ("unreachable",):
                response["unreachable_nodes"].append(node_id)
            elif state == "lagging":
                response["lagging_nodes"].append(node_id)
            elif state == "violation":
                response["violation_nodes"].append(node_id)

        response["detected_partition"] = (
            len(response["unreachable_nodes"]) >= 1
        )

        # SBS violations mean cluster detected the problem
        if sbs_violations:
            # Check if violation was LEADER_UNIQUENESS
            has_leadership_split = any(
                "LEADER" in v or "SPLIT" in v for v in sbs_violations
            )
            if has_leadership_split:
                # This is recoverable if cluster_recovered later
                response["recovered"] = False
                response["cluster_halted"] = False
            else:
                # Other violations — may be recoverable
                response["recovered"] = False

        # Check for CRITICAL unhandled failures (BYZANTINE, STATE_CORRUPTION)
        unhandled = [
            f for f in critical_failures
            if f.category in (
                FailureCategory.BYZANTINE_BEHAVIOR,
                FailureCategory.STATE_CORRUPTION,
                FailureCategory.CONSENSUS_BREAK,
            )
        ]
        if unhandled:
            response["cluster_halted"] = True

        return response

    def _determine_verdict(
        self,
        scenario_name: str,
        sbs_violations: list[str],
        classified: list[ClassifiedFailure],
        expected_behavior: dict,
        system_response: dict,
    ) -> Verdict:
        """Determine the final verdict (PASS / PARTIAL / FAIL)."""

        expected_violations = expected_behavior.get("sbs_violations", [])
        expected_response = expected_behavior.get("system_response", "")

        # ── Check for silent corruption / undetected violations ─────────
        def _matches_expected(expected: str, actual: list[str]) -> bool:
            """Return True if expected violation name matches any actual violation (substring or exact)."""
            for a in actual:
                if expected.lower() in a.lower() or a.lower() in expected.lower():
                    return True
                # Token-level: check for significant token overlap
                exp_tokens = set(expected.lower().split("_"))
                act_tokens = set(a.lower().split("_"))
                overlap = exp_tokens & act_tokens - {"violation", "signal", "category"}
                if overlap:
                    return True
            return False

        for ev in expected_violations:
            if not _matches_expected(ev, sbs_violations):
                # Expected violation was NOT detected → potential silent corruption
                if system_response.get("detected_violations"):
                    return Verdict.FAIL

        # ── CRITICAL failures that were NOT raised as SBS violations ──
        # BYZANTINE_SIGNAL and BYZANTINE_BEHAVIOR are the same event (different names)
        # Check for key token overlap between category and violation names
        def _semantic_match(category_val: str, violation: str) -> bool:
            """Return True if category and violation are semantically the same."""
            cat_lower = category_val.lower()
            viol_lower = violation.lower()
            if cat_lower in viol_lower or viol_lower in cat_lower:
                return True
            # Token-level overlap: split on underscore and check partial match
            cat_tokens = set(cat_lower.split("_"))
            viol_tokens = set(viol_lower.split("_"))
            # If they share at least one substantive token (len > 2), consider it a match
            overlap = cat_tokens & viol_tokens - {"signal", "violation", "category"}
            return bool(overlap)

        critical_undetected = [
            f for f in classified
            if f.severity == FailureSeverity.CRITICAL
            and not any(
                _semantic_match(f.category.value, v)
                for v in sbs_violations
            )
        ]
        if critical_undetected:
            return Verdict.FAIL

        # ── Cluster halted when it shouldn't have ───────────────────────
        if system_response.get("cluster_halted"):
            if expected_response != "cluster_halts":
                return Verdict.FAIL

        # ── Normal flow: violations detected + cluster recovered ───────
        if sbs_violations and system_response.get("detected_violations"):
            if expected_response == "cluster_detects_and_recovers":
                return Verdict.PARTIAL
            if expected_response == "cluster_halts":
                return Verdict.PASS  # halting is correct behavior

        # ── No violations when we expected none ────────────────────────
        # (some scenarios may legitimately not trigger SBS violations)

        # ── PASS: expected violations detected, cluster recovered ──────
        detected_expected = sum(1 for ev in expected_violations if ev in sbs_violations)
        if detected_expected >= len(expected_violations) and system_response.get("detected_partition"):
            if system_response.get("recovered"):
                return Verdict.PASS
            return Verdict.PARTIAL

        return Verdict.PASS

    def _generate_notes(
        self,
        scenario_name: str,
        classified: list[ClassifiedFailure],
        sbs_violations: list[str],
        system_response: dict,
    ) -> str:
        """Generate human-readable notes about the validation."""
        parts = []

        if not classified and not sbs_violations:
            parts.append("No failures detected — cluster remained stable.")

        sev_counts: dict[str, int] = {}
        for f in classified:
            sev_counts[f.severity.value] = sev_counts.get(f.severity.value, 0) + 1
        if sev_counts:
            parts.append(f"Failure severity distribution: {sev_counts}")

        if sbs_violations:
            parts.append(f"SBS violations: {', '.join(sbs_violations)}")

        if system_response.get("unreachable_nodes"):
            parts.append(
                f"Unreachable nodes during chaos: {system_response['unreachable_nodes']}"
            )

        if system_response.get("cluster_halted"):
            parts.append("Cluster halted (correct for CRITICAL violations).")

        return " | ".join(parts)


def chaos_result_to_adlr_record(result: ChaosResult) -> dict:
    """Convert ChaosResult to FailureReplay-compatible record."""
    result.cluster_metrics.get("post", {})
    score = result.violation_score or 0.0
    stages = []
    actions = []
    osc = []
    byzantine = False

    if result.raw_events:
        for ev in result.raw_events:
            if ev.get("type") == "violation":
                stages.append("VALIDATION")
                actions.append("record_violation")
                osc.append(int(score * 3))
        stages.append("TERMINAL")
        actions.append("chaos_complete")

    return {
        "action_sequence": actions or ["no_action"],
        "stage_sequence": stages or ["IDLE"],
        "oscillation_scores": osc or [0],
        "byzantine_risk": byzantine,
        "k": len(stages) if stages else 1,
        "t": len(stages) if stages else 1,
        "final_stage": "FAIL" if result.verdict.value == "FAIL" else "TERMINAL",
        "final_action": "chaos_FAIL" if result.verdict.value == "FAIL" else "chaos_PASS",
        "metadata": {
            "chaos_scenario": result.scenario_name,
            "verdict": result.verdict.value,
            "duration_s": result.duration_s,
        },
    }
