"""Smoke tests for deploy.iac.ete.gate.governance_gate (R-POL-3)."""

from deploy.iac.ete.gate.governance_gate import Decision, GovernanceGate


def _good_dag() -> dict:
    return {
        "dag_id": "DAG-OK",
        "nodes": [
            {"id": f"n{i}", "action": "buy", "symbol": "BTC/USDT"} for i in range(3)
        ],
        "edges": [{"from": "n0", "to": "n1"}, {"from": "n1", "to": "n2"}],
    }


def test_pre_check_returns_decision_enum_and_reason_str():
    gate = GovernanceGate()
    decision, reason = gate.pre_check(_good_dag(), {"ts": 1})
    assert decision in (Decision.APPROVED, Decision.REJECTED, Decision.ESCALATED)
    assert isinstance(reason, str) and reason


def test_mid_check_returns_bool():
    gate = GovernanceGate()
    result = gate.mid_check("DAG-OK", {"ts": 2})
    assert isinstance(result, bool)


def test_post_check_returns_dict_with_audit_keys():
    gate = GovernanceGate()
    outcome = gate.post_check("DAG-OK", {"status": "ok", "pnl": 0.1})
    assert isinstance(outcome, dict)
    assert "audit_id" in outcome
    assert "dag_id" in outcome
