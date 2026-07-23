#!/usr/bin/env python3
"""test_execution_equivalence.py — P7.1 EG = FEG Equivalence Tests."""
import sys
from pathlib import Path

import logging
log = logging.getLogger(__name__)


sys.path.insert(0, str(Path(__file__).parent))
from trace_normalizer import (
    compare_execution_traces,
    normalize_eg_trace,
    normalize_feg_trace,
    project_feg_to_local,
    trace_fingerprint,
)

TESTS = []

def test(fn):
    TESTS.append(fn)
    return fn

@test
def test_eg_normalize():
    trace = ["G1:pass", "G2:pass", "G3:pass", "ACT:pass"]
    events = normalize_eg_trace(trace)
    labels = [e.label for e in events]
    assert labels == ["G1", "G2", "G3", "ACT"], f"Got {labels}"

@test
def test_feg_normalize():
    fed_trace = [{"stage": "federation", "label": "VERIFY", "detail": "proof_ok"}, {"stage": "ledger", "label": "COMMIT"}]
    local_trace = ["G1:pass", "G2:pass", "ACT:pass"]
    events = normalize_feg_trace(fed_trace, local_trace)
    stages = [e.stage for e in events]
    assert "federation" in stages and "ledger" in stages and "gate" in stages

@test
def test_projection():
    fed_trace = [{"stage": "federation", "label": "VERIFY"}, {"stage": "ledger", "label": "COMMIT"}]
    local_trace = ["G1:pass", "G2:pass", "ACT:pass"]
    events = normalize_feg_trace(fed_trace, local_trace)
    projected = project_feg_to_local(events)
    for e in projected:
        assert e.stage in ("gate", "act")
    assert [e.label for e in projected] == ["G1", "G2", "ACT"]

@test
def test_equivalent_traces():
    eg_trace = ["G1:pass", "G2:pass", "G3:pass", "G4:pass", "ACT:pass"]
    feg_fed = [{"stage": "federation", "label": "VERIFY"}]
    feg_local = ["G1:pass", "G2:pass", "G3:pass", "G4:pass", "ACT:pass"]
    result = compare_execution_traces(eg_trace, feg_fed, feg_local)
    assert result.equivalent, f"Not equivalent: {result.mismatch_reason}"

@test
def test_block_at_g2():
    eg_trace = ["G1:pass", "G2:block"]
    feg_fed = [{"stage": "federation", "label": "VERIFY"}]
    feg_local = ["G1:pass", "G2:block"]
    result = compare_execution_traces(eg_trace, feg_fed, feg_local)
    assert result.equivalent

@test
def test_fingerprint():
    t1 = normalize_eg_trace(["G1:pass", "G2:pass", "ACT:pass"])
    t2 = normalize_eg_trace(["G1:pass", "G2:pass", "ACT:pass"])
    assert trace_fingerprint(t1) == trace_fingerprint(t2)

@test
def test_unequal_gate_count():
    eg_trace = ["G1:pass", "G2:pass", "ACT:pass"]
    feg_fed = [{"stage": "federation", "label": "VERIFY"}]
    feg_local = ["G1:pass", "ACT:pass"]
    result = compare_execution_traces(eg_trace, feg_fed, feg_local)
    assert not result.equivalent
    assert "gate_sequence_mismatch" in result.mismatch_reason

@test
def test_act_mismatch():
    eg_trace = ["G1:pass", "G2:pass", "ACT:block"]
    feg_fed = [{"stage": "federation", "label": "VERIFY"}]
    feg_local = ["G1:pass", "G2:pass"]
    result = compare_execution_traces(eg_trace, feg_fed, feg_local)
    assert not result.equivalent
    assert "ACT_mismatch" in result.mismatch_reason

@test
def test_detail_mismatch():
    eg_trace = ["G1:pass", "G2:block"]
    feg_fed = [{"stage": "federation", "label": "VERIFY"}]
    feg_local = ["G1:pass", "G2:pass"]
    result = compare_execution_traces(eg_trace, feg_fed, feg_local)
    assert not result.equivalent

@test
def test_complex_federation_trace():
    fed_events = [{"stage": "federation", "label": "VERIFY"}, {"stage": "ledger", "label": "COMMIT"}]
    local = ["G1:pass", "G2:pass", "G3:pass", "G4:pass", "G5:pass", "G6:pass", "G7:pass", "G8:pass", "G9:pass", "G10:pass", "ACT:pass"]
    eg_trace = ["G1:pass", "G2:pass", "G3:pass", "G4:pass", "G5:pass", "G6:pass", "G7:pass", "G8:pass", "G9:pass", "G10:pass", "ACT:pass"]
    result = compare_execution_traces(eg_trace, fed_events, local)
    assert result.equivalent

def main() -> int:
    log.info("══════════════════════════════════════════════")
    log.info("  P7.1 — EG = FEG Execution Equivalence")
    log.info("══════════════════════════════════════════════")
    passed = 0
    for t in TESTS:
        try:
            t()
            name = t.__name__.replace("test_", "")
            log.info(f"  [{len(TESTS)}] {name:<30} PASS")
            passed += 1
        except AssertionError as e:
            log.info(f"  [{len(TESTS)}] {t.__name__:<30} FAIL: {e}")
        except Exception as e:
            log.info(f"  [{len(TESTS)}] {t.__name__:<30} ERROR: {e}")
    log.info("══════════════════════════════════════════════")
    log.info(f"  Result: {passed}/{len(TESTS)} passed")
    if passed == len(TESTS):
        log.info("  ✅ EG = FEG equivalence PROVEN")
    return 0 if passed == len(TESTS) else 1

if __name__ == "__main__":
    sys.exit(main())
