"""
ProofDriftDetector — detects drift in reasoning itself (not just actions).
Drift = when the reasoning pattern changes without justification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from proof.proof_chain import ChainLink, ProofChain


class DriftType(str, Enum):
    SOURCE_SWITCH = "source_switch"
    REASONING_COLLAPSE = "reasoning_collapse"
    CAUSAL_BREAK = "causal_break"
    PROOF_REGRESSION = "proof_regression"


@dataclass
class DriftEvent:
    """Detected drift between two ticks."""
    from_tick: int
    to_tick: int
    drift_type: DriftType     # enum, not str
    severity: float          # 0..1
    description: str
    affected_ticks: list[int] = field(default_factory=list)
    from_source: str | None = None
    to_source: str | None = None

    # For compatibility with code that accesses .source
    @property
    def source(self) -> str:
        return "system"


@dataclass
class DriftReport:
    """Report of all drift events in a window."""
    tick_range: tuple[int, int]
    events: list[DriftEvent]
    drift_score: float      # aggregate: 0=no drift, 1=heavy drift
    is_drifted: bool        # threshold-based
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tick_range": self.tick_range,
            "drift_score": round(self.drift_score, 4),
            "is_drifted": self.is_drifted,
            "event_count": len(self.events),
            "events": [
                {
                    "type": e.drift_type.value,
                    "from": e.from_tick,
                    "to": e.to_tick,
                    "severity": round(e.severity, 3),
                    "description": e.description,
                }
                for e in self.events
            ],
            "summary": self.summary,
        }


class ProofDriftDetector:
    """
    Detects reasoning drift — changes in the proof chain that indicate
    instability in the reasoning process itself.
    """

    def __init__(self, severity_threshold: float = 0.6,
                 continuity_drop_threshold: float = 0.3):
        self.severity_threshold = severity_threshold
        self.continuity_drop_threshold = continuity_drop_threshold

    def detect(self, chain: ProofChain,
               window: tuple[int, int] | None = None) -> DriftReport:
        """
        Scan chain for drift events within optional window.
        """
        if chain.length == 0:
            return DriftReport(
                tick_range=(0, 0),
                events=[],
                drift_score=0.0,
                is_drifted=False,
            )

        start_tick = window[0] if window else chain.genesis_tick
        end_tick = window[1] if window else chain.latest_tick
        links = chain.window(start_tick, end_tick)

        events = []
        for i in range(1, len(links)):
            prev_link = links[i - 1]
            curr_link = links[i]

            # Check for source switch (reasoning switch)
            drift = self._check_source_switch(prev_link, curr_link)
            if drift:
                events.append(drift)

            # Check for reasoning collapse (continuity score drops sharply)
            drift = self._check_continuity_drop(prev_link, curr_link)
            if drift:
                events.append(drift)

            # Check for causal break (non-consecutive ticks)
            drift = self._check_causal_break(prev_link, curr_link)
            if drift:
                events.append(drift)

            # Check for proof status regression (PASS → FAIL)
            drift = self._check_proof_regression(prev_link, curr_link)
            if drift:
                events.append(drift)

        # Compute aggregate drift score
        if not events:
            drift_score = 0.0
        else:
            max_severity = max(e.severity for e in events)
            avg_severity = sum(e.severity for e in events) / len(events)
            drift_score = max(max_severity * 0.6, avg_severity * 0.4)

        # Build summary
        event_types = {}
        for e in events:
            event_types[e.drift_type.value] = event_types.get(e.drift_type.value, 0) + 1

        summary = {
            "total_events": len(events),
            "by_type": event_types,
            "max_severity": max((e.severity for e in events), default=0.0),
        }

        return DriftReport(
            tick_range=(start_tick, end_tick),
            events=events,
            drift_score=drift_score,
            is_drifted=drift_score >= self.severity_threshold,
            summary=summary,
        )

    def _check_source_switch(self, prev: ChainLink, curr: ChainLink) -> DriftEvent | None:
        prev_action = prev.record.selected_action
        curr_action = curr.record.selected_action
        if prev_action is None or curr_action is None:
            return None

        prev_src = prev_action.label.split(":")[1] if ":" in prev_action.label else ""
        curr_src = curr_action.label.split(":")[1] if ":" in curr_action.label else ""

        if prev_src != curr_src:
            return DriftEvent(
                from_tick=prev.tick,
                to_tick=curr.tick,
                drift_type=DriftType.SOURCE_SWITCH,
                severity=0.5,
                description=f"Reasoning switched from {prev_src} to {curr_src}",
                affected_ticks=[prev.tick, curr.tick],
                from_source=prev_src,
                to_source=curr_src,
            )
        return None

    def _check_continuity_drop(self, prev: ChainLink, curr: ChainLink) -> DriftEvent | None:
        drop = prev.continuity_score - curr.continuity_score
        if drop > self.continuity_drop_threshold:
            return DriftEvent(
                from_tick=prev.tick,
                to_tick=curr.tick,
                drift_type=DriftType.REASONING_COLLAPSE,
                severity=min(drop, 1.0),
                description=(
                    f"Continuity dropped from {prev.continuity_score:.2f} "
                    f"to {curr.continuity_score:.2f} (Δ={drop:.2f})"
                ),
                affected_ticks=[prev.tick, curr.tick],
            )
        return None

    def _check_causal_break(self, prev: ChainLink, curr: ChainLink) -> DriftEvent | None:
        if curr.tick != prev.tick + 1:
            return DriftEvent(
                from_tick=prev.tick,
                to_tick=curr.tick,
                drift_type=DriftType.CAUSAL_BREAK,
                severity=0.8,
                description=f"Non-consecutive ticks: {prev.tick} → {curr.tick}",
                affected_ticks=[prev.tick, curr.tick],
            )
        return None

    def _check_proof_regression(self, prev: ChainLink, curr: ChainLink) -> DriftEvent | None:
        prev_pass = prev.record.proof_status == "PASS"
        curr_pass = curr.record.proof_status == "PASS"

        if prev_pass and not curr_pass:
            return DriftEvent(
                from_tick=prev.tick,
                to_tick=curr.tick,
                drift_type=DriftType.PROOF_REGRESSION,
                severity=0.9,
                description=(
                    f"Proof status regressed: {prev.record.proof_status} → "
                    f"{curr.record.proof_status}"
                ),
                affected_ticks=[prev.tick, curr.tick],
            )
        return None
