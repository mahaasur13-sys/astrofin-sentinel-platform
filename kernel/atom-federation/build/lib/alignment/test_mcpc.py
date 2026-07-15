"""test_mcpc.py — v10.3 MCPC tests."""
import sys

sys.path.insert(0, '/home/workspace/atom-federation-os')
from alignment.mcpc import MCPC, DriftKind, MCPCStatus


def load(path):
    with open(path) as f:
        return f.read()

gcpl = load('/home/workspace/atom-federation-os/alignment/gcpl.py')
test_src = load('/home/workspace/atom-federation-os/alignment/test_gcpl.py')

# Test 1: self-check (gcpl vs gcpl) -> COHERENT
mcpc_self = MCPC(gcpl, gcpl, gcpl)
r = mcpc_self.check()
assert r.status == MCPCStatus.COHERENT
assert r.overall_coherence == 1.0
assert not r.blocked
assert r.prover_alignment_score == 1.0
print("[1] gcpl vs gcpl: COHERENT, alignment=1.0")

# Test 2: threshold drift -> BLOCKED
prover_bad = gcpl + "\nMAX_ACTIVE_BRANCHES = 100.0"
mcpc2 = MCPC(gcpl, test_src, prover_bad)
r2 = mcpc2.check()
thresh = [d for d in r2.drifts if d.kind == DriftKind.THRESHOLD_DRIFT]
assert thresh, f"Should detect threshold drift, got {r2.status}"
assert all(d.blocked for d in thresh)
assert r2.status == MCPCStatus.BLOCKED
print("[2] threshold drift: BLOCKED")

# Test 3: ghost function -> BLOCKED
prover_phantom = gcpl + "\ndef phantom_func(x): return x * 2"
mcpc3 = MCPC(gcpl, test_src, prover_phantom)
r3 = mcpc3.check()
ghosts = [d for d in r3.drifts if d.kind == DriftKind.GHOST_FUNCTION]
assert ghosts, "Should detect ghost function"
assert r3.blocked
print("[3] ghost function: BLOCKED")

# Test 4: coherence formula bounds
for label, report in [("self", r), ("thresh", r2), ("ghost", r3)]:
    coh = max(0.0, 1.0 - report.semantic_drift_index)
    assert 0.0 <= coh <= 1.0, f"{label} coherence out of range"
print("[4] coherence formula: 0 <= c <= 1")

# Test 5: coverage and alignment scores
for label, score in [("prover_alignment", r.prover_alignment_score), ("test_consistency", r.test_model_consistency)]:
    assert 0.0 <= score <= 1.0, f"{label} out of range"
print("[5] coverage scores: 0 <= s <= 1")

print()
print("=" * 50)
print("  ALL MCPC TESTS PASSED")
print("=" * 50)
