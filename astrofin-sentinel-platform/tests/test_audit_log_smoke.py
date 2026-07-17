"""Smoke tests for agents._impl.amre.audit (R-POL-2)."""

from __future__ import annotations

from agents._impl.amre.audit import (
    AuditLog,
    DecisionRecord,
    build_decision_record,
    get_audit_log,
)


def _mk_kpi() -> dict[str, float]:
    return {
        "oos_fail_rate": 0.1,
        "entropy": 0.5,
        "uncertainty": 0.2,
        "avg_confidence": 70.0,
        "sharpe_ratio": 1.2,
        "win_rate": 0.55,
        "regime_stability": 0.8,
        "exploration_rate": 0.1,
        "ttc_depth": 0.5,
        "grounding_strength": 0.7,
    }


def _mk_record(i: int = 0) -> DecisionRecord:
    return build_decision_record(
        decision_id=f"d-{i}",
        session_id="sess-1",
        symbol="BTC/USDT",
        price=100.0 + i,
        timeframe="1h",
        regime="trending",
        state_hash=f"hash-{i}",
        top_trajectories=[],
        selected_ensemble=[],
        q_values=[0.1, 0.2],
        q_star=0.2,
        uncertainty={"aleatoric": 0.1, "epistemic": 0.1, "total": 0.2},
        confidence_raw=70,
        confidence_final=70,
        confidence_adjustments=[],
        final_action="LONG",
        position_pct=0.1,
        kpi_snapshot=_mk_kpi(),
        metadata={"src": "smoke"},
    )


def test_get_audit_log_singleton() -> None:
    log1 = get_audit_log()
    log2 = get_audit_log()
    assert log1 is log2
    assert isinstance(log1, AuditLog)


def test_record_appends_and_get_recent_returns_in_reverse_order() -> None:
    log = get_audit_log()
    # Reset by re-recording over; AuditLog has no public clear.
    for i in range(3):
        log.record(_mk_record(i))
    recent = log.get_recent(n=2)
    assert len(recent) == 2
    assert recent[0].decision_id == "d-1"
    assert recent[1].decision_id == "d-2"


def test_record_is_decisionrecord_instance() -> None:
    rec = _mk_record(99)
    assert isinstance(rec, DecisionRecord)
    assert rec.symbol == "BTC/USDT"
    assert rec.final_action == "LONG"
    assert rec.confidence_raw == 70
