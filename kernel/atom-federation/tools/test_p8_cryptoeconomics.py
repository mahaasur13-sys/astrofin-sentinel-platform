#!/usr/bin/env python3
"""test_p8_cryptoeconomics.py — P8.1 cryptoeconomic slashing tests."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from core.economics.slashing_engine import EconomicSecurityViolation, SlashingEngine, SlashingReason
from core.economics.stake_registry import StakeRegistry, StakeTier


def check(cond, msg):
    if not cond:
        print(f"  FAIL: {msg}")
        raise AssertionError(msg)
    print(f"  PASS: {msg}")

def slashed(reg, node_id, initial):
    return reg.get_stake(node_id) < initial

def make():
    registry = StakeRegistry(initial_total_stake=10000.0)
    slashing = SlashingEngine(registry)
    for n in ["node-a","node-b","node-c","node-d","attacker","validator","rich"]:
        registry.deposit(n, 1000.0)
    registry.deposit("rich", 9000.0)  # rich = 10000 total
    initial = {n: registry.get_stake(n) for n in ["node-a","node-b","node-c","node-d","attacker","validator","rich"]}
    return registry, slashing, initial

def test1_invalid_proof():
    print("\n[1] Invalid Proof Slash")
    reg, slash, init = make()
    amt = slash.slash_invalid_proof("attacker", {"proof": "INVALID"})
    check(amt > 0, f"Slashed {amt} for invalid proof")
    check(slashed(reg, "attacker", init["attacker"]), f"Attacker slashed: {reg.get_stake('attacker')} < {init['attacker']}")
    check(slash.get_records("attacker")[-1].reason == SlashingReason.INVALID_PROOF, "Reason recorded")

def test2_replay():
    print("\n[2] Replay Attack Slash")
    reg, slash, init = make()
    slash.slash_replay_attack("attacker", {"nonce": "reused"})
    check(slashed(reg, "attacker", init["attacker"]), "Attacker slashed for replay")
    check(slash.get_records("attacker")[-1].reason == SlashingReason.REPLAY_ATTACK, "Reason recorded")

def test3_fork():
    print("\n[3] Fork Slash (100%)")
    reg, slash, init = make()
    slash.slash_fork("attacker", {"forks": 2})
    check(slashed(reg, "attacker", init["attacker"]), "Attacker slashed for fork")
    check(reg.get_stake("attacker") == 0.0, "Fork = 100% slash: stake=0")

def test4_runtime():
    print("\n[4] Runtime Violation Slash (50%)")
    reg, slash, init = make()
    slash.slash_runtime_violation("attacker", {"violation": "ast_hash_mismatch"})
    check(slashed(reg, "attacker", init["attacker"]), "Attacker slashed for runtime violation")
    check(slash.get_records("attacker")[-1].fraction == 0.50, "50% slash for runtime violation")

def test5_double_vote():
    print("\n[5] Double Vote Slash")
    reg, slash, init = make()
    clean = slash.verify_and_slash_vote("attacker", "prop-A")
    check(clean, "First vote accepted")
    clean = slash.verify_and_slash_vote("attacker", "prop-B")
    check(not clean, "Second vote rejected (double vote)")
    check(slashed(reg, "attacker", init["attacker"]), f"Attacker slashed for double vote: {reg.get_stake('attacker')} < {init['attacker']}")

def test6_bypass():
    print("\n[6] Bypass Attempt Slash")
    reg, slash, init = make()
    slash.slash_bypass_attempt("attacker", {"caller": "direct_apply_mutation"})
    check(slashed(reg, "attacker", init["attacker"]), "Attacker slashed for bypass attempt")
    check(slash.get_records("attacker")[-1].fraction == 0.25, "25% slash for bypass")

def test7_triple_vote():
    print("\n[7] Triple Vote = 100% Slash")
    reg, slash, init = make()
    # Three votes on different proposals
    slash.verify_and_slash_vote("attacker", "prop-A")  # 1st: clean
    slash.verify_and_slash_vote("attacker", "prop-B")  # 2nd: double vote -> rejected, no additional slash (already slashed)
    reg.get_stake("attacker")  # 1000 * 0.5 = 500 after first slash
    slash.verify_and_slash_vote("attacker", "prop-C")  # 3rd: triple vote -> 100% on remaining
    check(reg.get_stake("attacker") == 0.0, f"After triple vote: 0: {reg.get_stake('attacker')}")
    check(slashed(reg, "attacker", init["attacker"]), "Attacker slashed for triple vote")

def test8_validator_miss():
    print("\n[8] Validator Missed Violation Slash")
    reg, slash, init = make()
    was_late = slash.record_validator_miss(validator_node_id="validator", violation_type="invalid_proof", request_hash="rh1", detection_lag_ms=5000)
    check(was_late, "Validator flagged for late detection (lag >= 5000ms)")
    check(slashed(reg, "validator", init["validator"]), f"Validator slashed for miss: {reg.get_stake('validator')} < {init['validator']}")

def test9_no_stake_no_influence():
    print("\n[9] No Stake = No Weight")
    reg, slash, init = make()
    reg.withdraw("zero", reg.get_stake("zero"))
    check(reg.get_stake("zero") == 0.0, "Zero-stake node has 0 stake")
    w = reg.get_weight("zero")
    check(w == 0.0, f"Zero stake = zero weight: {w}")

def test10_slash_persistence():
    print("\n[10] Slash Cannot Be Reversed")
    reg, slash, init = make()
    slash.slash_fork("attacker", {})
    stake_after = reg.get_stake("attacker")
    try:
        slash.reverse_slashing("attacker")
        check(False, "reverse_slashing() should raise")
    except EconomicSecurityViolation:
        check(True, "reverse_slashing() raises EconomicSecurityViolation")
    check(reg.get_stake("attacker") == stake_after, "Stake unchanged after reversal attempt")

def test11_weighted_slash():
    print("\n[11] Weighted Slash (larger stake = larger penalty)")
    reg, slash, init = make()
    slash.slash_invalid_proof("rich", {})  # 25% of 10000 = 2500
    slash.slash_invalid_proof("attacker", {})  # 25% of 1000 = 250
    rich_slashed = 10000.0 - reg.get_stake("rich")
    attacker_slashed = 1000.0 - reg.get_stake("attacker")
    check(rich_slashed > attacker_slashed * 2, f"Weighted: rich={rich_slashed} > attacker*2={attacker_slashed*2}")

def test12_records_immutable():
    print("\n[12] Slash Records Immutable (tuple)")
    reg, slash, init = make()
    slash.slash_fork("attacker", {})
    records = slash.get_records("attacker")
    check(isinstance(records, tuple), f"Records is tuple: {type(records)}")
    check(len(records) == 1, f"1 record: {len(records)}")

def test13_jailing():
    print("\n[13] Node Jailed After Full Slash")
    reg, slash, init = make()
    slash.slash_fork("attacker", {})  # 100% slash
    check(reg.get_stake("attacker") == 0.0, f"Stake zero after fork slash: {reg.get_stake('attacker')}")
    check(reg.get_tier("attacker") == StakeTier.JAILED, f"Tier is JAILED: {reg.get_tier('attacker')}")
    check(reg.is_jailed("attacker"), "is_jailed() returns True for zero-stake node")

if __name__ == "__main__":
    tests = [test1_invalid_proof, test2_replay, test3_fork, test4_runtime,
             test5_double_vote, test6_bypass, test7_triple_vote,
             test8_validator_miss, test9_no_stake_no_influence,
             test10_slash_persistence, test11_weighted_slash,
             test12_records_immutable, test13_jailing]
    passed = 0
    for t in tests:
        try:
            t(); passed += 1
        except Exception as e:
            print(f"  EXCEPTION: {e}")
    print(f"\n{'='*60}\n{passed}/{len(tests)} P8 TESTS PASSED\n{'='*60}")
    sys.exit(0 if passed == len(tests) else 1)
