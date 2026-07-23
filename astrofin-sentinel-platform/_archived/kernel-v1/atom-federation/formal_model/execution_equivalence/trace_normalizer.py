"""
trace_normalizer.py — Unified trace representation for EG = FEG proof.

Both ExecutionGateway and FederatedExecutionGateway produce execution traces.
This module normalizes them to a common canonical form for equivalence comparison.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal

TraceEventType = Literal["gate", "act", "federation", "ledger"]

@dataclass(frozen=True)
class TraceEvent:
    stage: TraceEventType
    label: str
    detail: str = ""
    tick: int = 0
    def __repr__(self) -> str:
        return f"{self.label}:{self.detail}" if self.detail else self.label

def normalize_eg_trace(gateway_trace: list[str], intent: str = "", plan_id: str = "") -> list[TraceEvent]:
    events: list[TraceEvent] = []
    tick = 0
    for entry in gateway_trace:
        tick += 1
        if not entry.strip():
            continue
        if entry.startswith("ACT"):
            parts = entry.split(":", 1)
            events.append(TraceEvent(stage="act", label="ACT", detail=parts[1] if len(parts) > 1 else "", tick=tick))
            continue
        parts = entry.split(":", 1)
        gate = parts[0]
        detail = parts[1] if len(parts) > 1 else ""
        if gate.startswith("G") and len(gate) > 1 and gate[1].isdigit():
            events.append(TraceEvent(stage="gate", label=gate, detail=detail, tick=tick))
    return events

def normalize_feg_trace(federated_trace: list[dict[str, Any]], local_trace: list[str], intent: str = "", plan_id: str = "") -> list[TraceEvent]:
    events: list[TraceEvent] = []
    tick = 0
    for entry in federated_trace:
        tick += 1
        stage = entry.get("stage", "federation")
        label = entry.get("label", entry.get("event", "?"))
        events.append(TraceEvent(stage=stage, label=label, detail=entry.get("detail", ""), tick=tick))
    local_events = normalize_eg_trace(local_trace, intent, plan_id)
    for evt in local_events:
        events.append(TraceEvent(stage=evt.stage, label=evt.label, detail=evt.detail, tick=tick + evt.tick))
    return events

def project_feg_to_local(feg_trace: list[TraceEvent]) -> list[TraceEvent]:
    return [e for e in feg_trace if e.stage in ("gate", "act")]

@dataclass
class EquivalenceResult:
    equivalent: bool
    eg_trace_len: int
    feg_trace_len: int
    eg_normalized: list[TraceEvent]
    feg_projected: list[TraceEvent]
    mismatch_at: int | None = None
    mismatch_reason: str = ""

def compare_execution_traces(eg_trace: list[str], feg_trace: list[dict[str, Any]], local_trace: list[str], intent: str = "", plan_id: str = "") -> EquivalenceResult:
    eg_normalized = normalize_eg_trace(eg_trace, intent, plan_id)
    feg_full = normalize_feg_trace(feg_trace, local_trace, intent, plan_id)
    feg_projected = project_feg_to_local(feg_full)
    eg_gates = [e.label for e in eg_normalized if e.stage == "gate"]
    feg_gates = [e.label for e in feg_projected if e.stage == "gate"]
    if eg_gates != feg_gates:
        return EquivalenceResult(equivalent=False, eg_trace_len=len(eg_normalized), feg_trace_len=len(feg_projected),
            eg_normalized=eg_normalized, feg_projected=feg_projected, mismatch_at=0,
            mismatch_reason=f"gate_sequence_mismatch: EG={eg_gates} vs FEG={feg_gates}")
    for i, (e1, e2) in enumerate(zip(eg_normalized, feg_projected)):
        if e1.label != e2.label:
            return EquivalenceResult(equivalent=False, eg_trace_len=len(eg_normalized), feg_trace_len=len(feg_projected),
                eg_normalized=eg_normalized, feg_projected=feg_projected, mismatch_at=i,
                mismatch_reason=f"label_mismatch at position {i}: {e1.label} vs {e2.label}")
        if e1.detail != e2.detail:
            return EquivalenceResult(equivalent=False, eg_trace_len=len(eg_normalized), feg_trace_len=len(feg_projected),
                eg_normalized=eg_normalized, feg_projected=feg_projected, mismatch_at=i,
                mismatch_reason=f"detail_mismatch at position {i}: {e1} vs {e2}")
    eg_has_act = any(e.label == "ACT" for e in eg_normalized)
    feg_has_act = any(e.label == "ACT" for e in feg_projected)
    if eg_has_act != feg_has_act:
        return EquivalenceResult(equivalent=False, eg_trace_len=len(eg_normalized), feg_trace_len=len(feg_projected),
            eg_normalized=eg_normalized, feg_projected=feg_projected,
            mismatch_at=max(len(eg_normalized), len(feg_projected)),
            mismatch_reason=f"ACT_mismatch: EG_has_ACT={eg_has_act}, FEG_has_ACT={feg_has_act}")
    return EquivalenceResult(equivalent=True, eg_trace_len=len(eg_normalized), feg_trace_len=len(feg_projected),
        eg_normalized=eg_normalized, feg_projected=feg_projected)

def trace_fingerprint(events: list[TraceEvent]) -> str:
    parts = [f"{e.stage}:{e.label}:{e.detail}" for e in events]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
