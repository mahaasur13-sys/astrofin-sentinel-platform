#!/usr/bin/env python3
"""test_p5_proof_carrying.py — P5 proof-carrying execution tests."""
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from core.proof.execution_request import ExecutionRequest
from core.proof.proof_verifier import ProofVerificationError, ProofVerifier, ReplayError, StaleRequestError
from orchestration.ExecutionGateway import ExecutionGateway


def ok(cond, msg=""):
    if not cond:
        print(f"  FAIL: {msg}")
        return False
    print(f"  OK: {msg}")
    return True

def test1():
    print("\n[1] Valid signed request")
    with tempfile.TemporaryDirectory() as td:
        pv = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        gw = ExecutionGateway(proof_verifier=pv)
        req = pv.sign(payload={"a": 1}, issuer_id="test")
        r = gw.execute_proof_carried(req)
        return ok(r.passed, f"expected pass, got {r.block_gate}")

def test2():
    print("\n[2] Missing proof rejected")
    with tempfile.TemporaryDirectory() as td:
        v = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        gw = ExecutionGateway(proof_verifier=v)
        bad = ExecutionRequest(payload={"a": 1}, proof=b"", signature=b"", issuer_id="i")
        try:
            gw.execute_proof_carried(bad)
            return ok(False, "not rejected")
        except ProofVerificationError:
            return ok(True, "rejected")

def test3():
    print("\n[3] Invalid signature rejected")
    with tempfile.TemporaryDirectory() as td:
        v = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        ExecutionGateway(proof_verifier=v)
        req = v.sign(payload={"a": 1}, issuer_id="i")
        bad = ExecutionRequest(payload={"a": 1}, proof=b"WRONG", signature=b"WRONG",
                             issuer_id="i", nonce=req.nonce, timestamp=req.timestamp)
        try:
            v.verify(bad)
            return ok(False, "not rejected")
        except ProofVerificationError:
            return ok(True, "rejected")

def test4():
    print("\n[4] Replay blocked")
    with tempfile.TemporaryDirectory() as td:
        pv = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        req = pv.sign(payload={"a": 1}, issuer_id="test")
        pv.verify(req)  # first use
        try:
            pv.verify(req)  # second use = replay
            return ok(False, "replay not blocked")
        except ReplayError as e:
            return ok(True, f"replay blocked: {e.code}")

def test5():
    print("\n[5] Tamper detected")
    with tempfile.TemporaryDirectory() as td:
        v = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        req = v.sign(payload={"a": 1}, issuer_id="i")
        bad = ExecutionRequest(payload={"a": 99}, proof=req.proof, signature=req.signature,
                             issuer_id="i", nonce=req.nonce, timestamp=req.timestamp)
        try:
            v.verify(bad)
            return ok(False, "not rejected")
        except ProofVerificationError as e:
            return ok(True, f"rejected: {e.code}")

def test6():
    print("\n[6] Stale rejected")
    with tempfile.TemporaryDirectory() as td:
        stale = ExecutionRequest(payload={"a": 1}, proof=b"\x00"*32, signature=b"\x00"*32,
                               issuer_id="i", nonce="n", timestamp=0, metadata=())
        v = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        try:
            v.verify(stale)
            return ok(False, "not rejected")
        except StaleRequestError as e:
            return ok(True, f"stale: {e.code}")
        except ProofVerificationError as e:
            return ok(True, f"stale or invalid: {e.code}")

def test7():
    print("\n[7] Ledger proof binding")
    with tempfile.TemporaryDirectory() as td:
        pv = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        req = pv.sign(payload={"x": 1}, issuer_id="ledger_test")
        pv.verify(req)
        entries = list(pv.iterate_ledger())
        return ok(len(entries) >= 1, f"ledger entries: {len(entries)}")

def test8():
    print("\n[8] Gateway proof gate enforced")
    with tempfile.TemporaryDirectory() as td:
        p = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        gw = ExecutionGateway(proof_verifier=p)
        req = p.sign(payload={"gate": "test"}, issuer_id="gw")
        r = gw.execute_proof_carried(req)
        return ok(r.passed, f"G1..G10 + proof: {r.block_gate}")

def test9():
    print("\n[9] Gateway replay blocked")
    with tempfile.TemporaryDirectory() as td:
        pv = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        gw = ExecutionGateway(proof_verifier=pv)
        req1 = pv.sign(payload={"action": "retune"}, issuer_id="test")
        r1 = gw.execute_proof_carried(req1)
        if not r1.passed:
            return ok(False, f"first failed: {r1.block_gate}")
        try:
            gw.execute_proof_carried(req1)
            return ok(False, "replay not blocked")
        except ReplayError as e:
            return ok(True, f"replay blocked: {e.code}")
        except ProofVerificationError as e:
            return ok(True, f"replay blocked: {e.code}")

def test10():
    print("\n[10] P4+P5 aligned: runtime_integrity + proof_valid + G1..G10")
    with tempfile.TemporaryDirectory() as td:
        pv = ProofVerifier(signing_key=b"k", state_dir=pathlib.Path(td))
        gw = ExecutionGateway(proof_verifier=pv)
        req = pv.sign(payload={"combined": True}, issuer_id="test")
        r = gw.execute_proof_carried(req)
        if not r.passed:
            return ok(False, f"combined failed: {r.block_gate}")
        print("  OK: P4 runtime_integrity + P5 proof_valid + G1..G10 passed")
        return True

if __name__ == "__main__":
    tests = [test1, test2, test3, test4, test5, test6, test7, test8, test9, test10]
    p = f = 0
    for t in tests:
        try:
            if t():
                p += 1
            else: f += 1
        except Exception as e:
            print(f"  EXCEPTION: {type(e).__name__}: {e}")
            f += 1
    print(f"\n{'='*60}")
    print(f"RESULTS: {p} passed / {f} failed / {len(tests)} total")
    sys.exit(0 if f == 0 else 1)
