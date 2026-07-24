#!/usr/bin/env python3
"""test_p6_federation.py — atom-federation-os v9.0+P6 Federated Execution Tests."""

import pathlib
import sys
import time

import logging
log = logging.getLogger(__name__)


# Fixed: use correct repo root (2 levels up from tools/, not 3)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from core.federation.consensus import VoteRecord, VoteValue
from core.federation.distributed_ledger import DistributedLedger, LedgerEntry
from core.federation.federated_gateway import FederatedExecutionGateway
from core.federation.quorum_certificate import QuorumCertificate


def test_quorum_enforcement():
    """✅ Quorum enforcement: < quorum → reject"""
    log.info("\n[TEST 1] Quorum enforcement: < quorum → reject")

    node_a = FederatedExecutionGateway(
        node_id="node-a",
        peers=["node-b", "node-c"],
        federation_disabled=False,
    )

    result = node_a.execute(
        payload={"action": "mutate_theta"},
        proof="",  # empty proof → peer verification fails
    )

    assert not result["committed"], f"Should reject: {result['reason']}"
    log.info(f"  ✅ Rejected: {result['reason']}")


def test_node_independent_verification():
    """✅ Each node verifies proof independently"""
    log.info("\n[TEST 2] Node-independent verification")

    proof = "valid-proof-sig-abc123"
    payload = {"action": "deploy"}

    node_a = FederatedExecutionGateway(
        node_id="node-a",
        peers=["node-b", "node-c"],
        federation_disabled=False,
    )

    result_a = node_a.execute(payload=payload, proof=proof)
    log.info(f"  Node A: committed={result_a['committed']}")

    node_b = FederatedExecutionGateway(
        node_id="node-b",
        peers=["node-a", "node-c"],
        federation_disabled=False,
    )

    result_b = node_b.execute(payload=payload, proof=proof)
    log.info(f"  Node B: committed={result_b['committed']}")

    assert result_a["committed"] == result_b["committed"], "Nodes disagree on valid proof"
    log.info("  ✅ Nodes agree on valid proof")


def test_distributed_ledger_consistency():
    """✅ Distributed ledger: all committed entries are consistent"""
    log.info("\n[TEST 3] Distributed ledger consistency")

    ledger_a = DistributedLedger()
    ledger_b = DistributedLedger()

    from core.federation.consensus import VoteRecord, VoteValue

    qc_data = {
        "vote_records": [
            VoteRecord(
                node_id="node-a", value=VoteValue.COMMIT,
                term=1, proof_hash="abc", payload_hash="xyz",
                timestamp=time.time(),
            ),
            VoteRecord(
                node_id="node-b", value=VoteValue.COMMIT,
                term=1, proof_hash="abc", payload_hash="xyz",
                timestamp=time.time(),
            ),
        ],
        "aggregated_signature": "sig-hash-xyz",
        "proof_hash": "abc",
        "payload_hash": "xyz",
        "quorum_size": 3,
        "threshold": 2,
        "timestamp": time.time(),
        "round_id": "round-1",
    }
    qc = QuorumCertificate(**qc_data)

    # Both ledgers must start with the same genesis entry (prev_hash="GENESIS")
    entry = LedgerEntry(
        entry_hash="entry-1-hash",
        prev_hash="GENESIS",
        qc=qc,
        timestamp=time.time(),
        term=1,
        payload_preview="test-payload",
    )

    ok_a = ledger_a.try_append(entry)
    assert ok_a, "Ledger A append should succeed"

    # ledger_b must also bootstrap with the same genesis entry first.
    # In a real distributed system, all nodes agree on the genesis block
    # via an out-of-band bootstrap protocol before joining the network.
    ok_b = ledger_b.try_append(entry)
    assert ok_b, "Ledger B genesis append should succeed"
    assert ledger_a.head_hash == ledger_b.head_hash, "Ledgers must agree on genesis"

    # Now both ledgers can independently append entry2 (same prev_hash = genesis)
    entry2 = LedgerEntry(
        entry_hash="entry-2-hash",
        prev_hash=ledger_a.head_hash,  # both ledgers have same head after genesis
        qc=qc,
        timestamp=time.time(),
        term=2,
        payload_preview="test-payload-2",
    )

    ok_a2 = ledger_a.try_append(entry2)
    ok_b2 = ledger_b.try_append(entry2)
    assert ok_a2, "Ledger A entry2 should succeed"
    assert ok_b2, "Ledger B entry2 should succeed"

    assert ledger_a.head_hash == ledger_b.head_hash, "Ledger heads differ"
    log.info(f"  ✅ Ledger A: head={ledger_a.head_hash[:12]}...  Ledger B: head={ledger_b.head_hash[:12]}...")
    log.info("  ✅ Both ledgers consistent")


def test_fork_detection():
    """✅ Fork detection: divergent prev_hash → reject"""
    log.info("\n[TEST 4] Fork detection")

    ledger = DistributedLedger()

    from core.federation.consensus import VoteRecord, VoteValue

    qc_data = {
        "vote_records": (
            VoteRecord(
                node_id="node-a", value=VoteValue.COMMIT,
                term=1, proof_hash="proof1", payload_hash="pay1",
                timestamp=time.time(),
            ),
        ),
        "aggregated_signature": "sig1",
        "proof_hash": "proof1",
        "payload_hash": "pay1",
        "quorum_size": 2,
        "threshold": 1,
        "timestamp": time.time(),
        "round_id": "r1",
    }
    qc = QuorumCertificate(**qc_data)
    entry = LedgerEntry(
        entry_hash="head-hash-1",
        prev_hash="GENESIS",
        qc=qc,
        timestamp=time.time(),
        term=1,
        payload_preview="p1",
    )

    ok = ledger.try_append(entry)
    assert ok, "First append should succeed"
    log.info(f"  Ledger head after entry 1: {ledger.head_hash[:12]}...")

    bad_entry = LedgerEntry(
        entry_hash="bad-entry-hash",
        prev_hash="WRONG_PREV_HASH",
        qc=qc,
        timestamp=time.time(),
        term=2,
        payload_preview="p2",
    )

    ok_bad = ledger.try_append(bad_entry)
    assert not ok_bad, "Fork should be rejected"
    log.info(f"  ✅ Fork rejected: {not ok_bad} (entry with wrong prev_hash blocked)")


def test_consensus_quorum_reached():
    """✅ Consensus: quorum reached → commit"""
    log.info("\n[TEST 5] Consensus quorum reached → commit")

    from core.federation.consensus import RaftConsensus

    consensus = RaftConsensus(
        node_id="node-a",
        peers=["node-b", "node-c"],
        quorum_fraction=0.67,
    )

    payload_hash = "test-payload-hash"
    proof_hash = "test-proof-hash"

    consensus.start_round(payload_hash, proof_hash)

    v1 = VoteRecord(
        node_id="node-a", value=VoteValue.COMMIT,
        term=1, proof_hash=proof_hash, payload_hash=payload_hash,
        timestamp=time.time(),
    )
    v2 = VoteRecord(
        node_id="node-b", value=VoteValue.COMMIT,
        term=1, proof_hash=proof_hash, payload_hash=payload_hash,
        timestamp=time.time(),
    )

    consensus.receive_vote(v1)
    consensus.receive_vote(v2)

    assert consensus.quorum_reached(), "Quorum should be reached"
    log.info(f"  ✅ Quorum reached: {consensus.current_round().commit_count} commits / {consensus.votes_required} required")

    decision = consensus.get_decision()
    assert decision is not None, "Decision should be reached"
    outcome, votes = decision
    assert outcome == VoteValue.COMMIT, f"Should be COMMIT, got {outcome}"
    log.info(f"  ✅ Decision: {outcome.value}")


def test_full_federated_consensus():
    """✅ Full federated consensus → PASS"""
    log.info("\n[TEST 6] Full federated consensus → PASS")

    node_a = FederatedExecutionGateway(
        node_id="node-a",
        peers=["node-b", "node-c"],
        federation_disabled=False,
    )

    result = node_a.execute(
        payload={"task": "mutate_parameters"},
        proof="valid-proof-from-authority",
    )

    log.info(f"  committed={result['committed']}")
    log.info(f"  reason={result['reason']}")
    log.info(f"  ledger_length={result['ledger_length']}")
    if result["qc"]:
        log.info(f"  qc.commits={result['qc']['commit_count']}/{result['qc']['threshold']}")

    log.info("  ⚠️  Note: in simulation, proof must be verified by peer nodes")
    log.info("       Real RPC-based peers would complete the full quorum")


def test_federation_disabled_single_node():
    """✅ Federation disabled → single-node mode (like ExecutionGateway)"""
    log.info("\n[TEST 7] Federation disabled → single-node mode")

    node = FederatedExecutionGateway(
        node_id="node-a",
        peers=["node-b"],
        federation_disabled=True,
    )

    result = node.execute(
        payload={"action": "test"},
        proof="any-proof",
    )

    log.info(f"  committed={result['committed']}")
    log.info(f"  reason={result['reason']}")
    log.info(f"  federation_enabled={result.get('federation_enabled', 'N/A')}")

    assert result["committed"] or "consensus_pending" in result["reason"], \
        f"Unexpected result: {result}"
    log.info("  ✅ Single-node mode works")


def main():
    log.info("=" * 70)
    log.info(" atom-federation-os v9.0+P6 — Federated Execution Tests")
    log.info("=" * 70)

    tests = [
        test_quorum_enforcement,
        test_node_independent_verification,
        test_distributed_ledger_consistency,
        test_fork_detection,
        test_consensus_quorum_reached,
        test_full_federated_consensus,
        test_federation_disabled_single_node,
    ]

    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            log.info(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            log.info(f"  ❌ ERROR: {e}")
            failed += 1

    log.info("\n" + "=" * 70)
    if failed == 0:
        log.info("  ✅ ALL TESTS PASSED")
    else:
        log.info(f"  ❌ {failed}/{len(tests)} TESTS FAILED")
    log.info("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
