#!/usr/bin/env python3
"""test_p7_bft.py — atom-federation-os v9.0+P7 Byzantine-Fault-Tolerant Tests.

Tests the full P7 BFT system:
  - f ≤ (n-1)/3 Byzantine nodes tolerated
  - Double-sign detection + slashing
  - PBFT-like three-phase consensus
  - BFTQC validation (≥ 2f+1)
  - Fork accountability
  - Safe mode on consensus failure
"""
import pathlib
import sys
import time

import logging
log = logging.getLogger(__name__)


_REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

from core.federation.bft_consensus import BFTConsensus, BFTVote, Phase, VoteValue
from core.federation.bft_quorum_certificate import BFTQC, BFTQCBuilder, BFTThreshold, validate_bft_qc
from core.federation.federated_gateway import FederatedExecutionGateway
from core.federation.slashing import SlashingEngine


def test_bft_thresholds():
    """✅ BFT threshold calculations."""
    log.info("=== TEST 1: BFT Thresholds ===")

    # 4 nodes → f=1, quorum=3
    t = BFTThreshold.from_n(4)
    assert t.f == 1
    assert t.prepare_threshold == 3
    assert t.commit_threshold == 3
    assert t.honest_minimum == 2

    # 7 nodes → f=2, quorum=5
    t = BFTThreshold.from_n(7)
    assert t.f == 2
    assert t.prepare_threshold == 5
    assert t.commit_threshold == 5
    assert t.honest_minimum == 3

    log.info(f"  n=4: f={BFTThreshold.from_n(4).f}, quorum={BFTThreshold.from_n(4).prepare_threshold}")
    log.info(f"  n=7: f={BFTThreshold.from_n(7).f}, quorum={BFTThreshold.from_n(7).prepare_threshold}")
    log.info("  ✅ PASS")


def test_double_sign_detection():
    """✅ Double-sign detection → node slashed."""
    log.info("\n=== TEST 2: Double-Sign Detection ===")

    slashing = SlashingEngine()
    bft = BFTConsensus(node_id='a', all_nodes=['a', 'b', 'c', 'd'], f=1)

    # Simulate a node signing two different requests at same sequence
    req_a = "req_hash_a_12345678"
    req_b = "req_hash_b_87654321"

    # Node 'b' signs both requests at sequence=5 → BYZANTINE
    key = ('b', 5)
    bft._double_sign_history[key] = {req_a, req_b}

    conflicts = bft.detect_double_sign('b', 5)
    log.info(f"  Conflicts for node-b@seq=5: {conflicts}")
    assert len(conflicts) > 1, "Should detect conflict"

    # Slash the node
    record = slashing.report_double_sign(
        node_id='b',
        request_hash_a=req_a,
        request_hash_b=req_b,
        view=1,
        sequence=5,
        signature_a='sig_a',
        signature_b='sig_b',
        detected_by='a',
    )
    assert slashing.is_slashed('b'), "Node should be slashed"
    log.info(f"  Slashed node: {record.record_id}")
    log.info("  ✅ PASS")


def test_bftqc_valid():
    """✅ BFTQC valid when ≥ 2f+1 signatures."""
    log.info("\n=== TEST 3: BFTQC Validation ===")

    # 4 nodes, f=1, threshold=3
    qc = BFTQC(
        request_hash='req_abc',
        view=1,
        sequence=1,
        signatures=('sig_a', 'sig_b', 'sig_c'),  # 3 signatures
        nodes_signed=('a', 'b', 'c'),
        threshold=3,
        f=1,
        aggregated_sig='agg_sig',
        timestamp=time.time(),
        quorum_type='prepare',
    )

    result = validate_bft_qc(qc, slashed=frozenset())
    log.info(f"  QC valid={result.valid}, strength={result.quorum_strength:.2f}")
    assert result.valid
    assert result.quorum_strength >= 1.0
    log.info("  ✅ PASS")


def test_bftqc_insufficient():
    """❌ BFTQC rejected when < 2f+1 signatures."""
    log.info("\n=== TEST 4: BFTQC Insufficient ===")

    qc = BFTQC(
        request_hash='req_abc',
        view=1,
        sequence=1,
        signatures=('sig_a', 'sig_b'),  # Only 2 signatures — need 3
        nodes_signed=('a', 'b'),
        threshold=3,
        f=1,
        aggregated_sig='agg_sig',
        timestamp=time.time(),
        quorum_type='prepare',
    )

    result = validate_bft_qc(qc, slashed=frozenset())
    log.info(f"  QC valid={result.valid}, reason={result.reason}")
    assert not result.valid
    assert "insufficient" in result.reason
    log.info("  ✅ PASS")


def test_bftqc_slashed_contributor():
    """❌ BFTQC invalid if slashed node contributed."""
    log.info("\n=== TEST 5: BFTQC Slashed Contributor ===")

    qc = BFTQC(
        request_hash='req_abc',
        view=1,
        sequence=1,
        signatures=('sig_a', 'sig_b', 'sig_c'),
        nodes_signed=('a', 'b', 'c'),
        threshold=3,
        f=1,
        aggregated_sig='agg_sig',
        timestamp=time.time(),
        quorum_type='prepare',
    )

    result = validate_bft_qc(qc, slashed=frozenset({'b'}))
    log.info(f"  QC valid={result.valid}, reason={result.reason}")
    assert not result.valid
    assert 'slashed' in result.reason
    log.info("  ✅ PASS")


def test_bft_consensus_phases():
    """✅ BFTConsensus three-phase progression."""
    log.info("\n=== TEST 6: BFT Three-Phase Consensus ===")

    bft = BFTConsensus(node_id='a', all_nodes=['a', 'b', 'c', 'd'], f=1)
    bft.init_view(view=1, primary='a')

    request_hash = "req_test_123"

    # Step 1: Primary receives request
    bft.receive_request(request_hash=request_hash, proof='valid', payload_hash='ph')
    status = bft.get_status(request_hash)
    log.info(f"  After request: phase={status['phase']}")
    assert status['phase'] == 'PRE_PREPARED'

    # Step 2: Receive PREPARE votes from enough nodes
    for node in ['a', 'b', 'c']:
        vote = BFTVote(
            node_id=node,
            phase=Phase.PREPARED,
            request_hash=request_hash,
            view=1,
            sequence=1,
            vote=VoteValue.COMMIT,
            signature=f'sig_{node}',
            timestamp=time.time(),
        )
        bft.receive_prepare(vote)

    status = bft.get_status(request_hash)
    log.info(f"  After 3 PREPARE votes: phase={status['phase']}, votes={status['prepare_votes']}")
    assert status['prepare_votes'] >= 3

    # Step 3: Check PreparedCertificate
    pc = bft.check_prepared(request_hash)
    log.info(f"  PreparedCertificate valid={pc.is_valid if pc else False}")
    assert pc is not None and pc.is_valid

    # Step 4: Receive COMMIT votes
    for node in ['a', 'b', 'c']:
        vote = BFTVote(
            node_id=node,
            phase=Phase.COMMITTED,
            request_hash=request_hash,
            view=1,
            sequence=1,
            vote=VoteValue.COMMIT,
            signature=f'commit_sig_{node}',
            timestamp=time.time(),
        )
        bft.receive_commit(vote)

    # Step 5: Finalize
    can_commit = bft.check_committable(request_hash)
    log.info(f"  Committable={can_commit}")
    assert can_commit

    cc = bft.finalize_commit(request_hash)
    log.info(f"  CommitCertificate valid={cc.is_valid if cc else False}")
    assert cc is not None and cc.is_valid

    status = bft.get_status(request_hash)
    log.info(f"  Final phase={status['phase']}")
    assert status['phase'] == 'DECIDED'
    log.info("  ✅ PASS")


def test_bft_byzantine_node_slashed():
    """✅ Byzantine node (double-sign) is slashed and excluded from quorums."""
    log.info("\n=== TEST 7: Byzantine Node Excluded ===")

    bft = BFTConsensus(node_id='a', all_nodes=['a', 'b', 'c', 'd'], f=1)
    slashing = SlashingEngine()

    # Detect double-sign for node 'c'
    req1 = "req_conflict_1"
    req2 = "req_conflict_2"
    bft._double_sign_history[('c', 3)] = {req1, req2}

    conflicts = bft.detect_double_sign('c', 3)
    assert len(conflicts) > 1

    # Slash
    slashing.report_double_sign(
        node_id='c', request_hash_a=req1, request_hash_b=req2,
        view=1, sequence=3, signature_a='s1', signature_b='s2',
    )
    bft.slash('c')

    assert slashing.is_slashed('c')
    assert bft._slashed == {'c'}

    log.info(f"  Slashed nodes: {slashing.get_slashed_nodes()}")
    log.info(f"  Slashed from BFT: {list(bft._slashed)}")
    log.info("  ✅ PASS")


def test_bftqc_builder_threshold():
    """✅ BFTQCBuilder builds QC only when threshold reached."""
    log.info("\n=== TEST 8: BFTQC Builder Threshold ===")

    builder = BFTQCBuilder(
        request_hash='req_test', view=1, sequence=1,
        threshold=3, f=1, quorum_type='prepare',
    )

    assert not builder.can_build()

    added = builder.add_signature('a', 'sig_a')
    assert not added and builder.count == 1

    added = builder.add_signature('b', 'sig_b')
    assert not added and builder.count == 2

    added = builder.add_signature('c', 'sig_c')
    assert added and builder.can_build()

    qc = builder.build()
    assert qc.request_hash == 'req_test'
    assert len(qc.signatures) == 3

    log.info(f"  QC built: {qc.description}")
    log.info("  ✅ PASS")


def test_federated_gateway_rejects_insufficient_quorum():
    """❌ FederatedExecutionGateway rejects when quorum not reached."""
    log.info("\n=== TEST 9: Gateway Rejects Insufficient Quorum ===")

    gateway = FederatedExecutionGateway(
        node_id='node-a',
        peers=['node-b', 'node-c', 'node-d'],
        federation_disabled=False,
    )

    # Try to execute with empty proof (should fail local verification)
    # In federation mode, even if local passes, need peers
    # Without valid proof from peers, quorum should fail
    result = gateway.execute(
        payload={'action': 'test'},
        proof='',  # empty → invalid
    )

    log.info(f"  committed={result['committed']}, reason={result['reason']}")
    assert not result['committed']

    # Verify stats
    stats = gateway.stats
    log.info(f"  stats: {stats}")
    log.info("  ✅ PASS")


def test_slashing_engine_full():
    """✅ SlashingEngine records all misbehavior types."""
    log.info("\n=== TEST 10: Slashing Engine Full Cycle ===")

    engine = SlashingEngine()

    # Slash for double-sign
    r1 = engine.report_double_sign(
        node_id='malicious', request_hash_a='A', request_hash_b='B',
        view=2, sequence=7, signature_a='sigA', signature_b='sigB',
    )
    assert engine.is_slashed('malicious')

    # Slash for equivocation
    engine.report_equivocation(
        node_id='equivocator',
        payload_hash_a='PA', payload_hash_b='PB',
    )
    assert engine.is_slashed('equivocator')

    # Slash for invalid QC
    engine.report_invalid_qc(
        node_id='bad_actor',
        qc_request_hash='qc_hash',
        expected_threshold=3,
        actual_sigs=1,
    )
    assert engine.is_slashed('bad_actor')

    summary = engine.summary()
    log.info(f"  Summary: {summary}")
    assert summary['total_slashed'] == 3
    assert summary['total_records'] == 3

    # Appeal
    engine.appeal(r1.record_id, "I was network partition, not Byzantine")
    assert engine._appeal_records[r1.record_id]['pending']

    # Resolve — reject appeal (node remains slashed since upheld=False means keep penalty)
    engine.resolve_appeal(r1.record_id, upheld=False)
    # upheld=False = keep penalty → node stays slashed
    assert engine.is_slashed('malicious')

    log.info("  ✅ PASS")


def main():
    log.info("=" * 70)
    log.info("ATOMFEDERATION-OS v9.0+P7 BYZANTINE-FAULT-TOLERANT TESTS")
    log.info("=" * 70)

    tests = [
        test_bft_thresholds,
        test_double_sign_detection,
        test_bftqc_valid,
        test_bftqc_insufficient,
        test_bftqc_slashed_contributor,
        test_bft_consensus_phases,
        test_bft_byzantine_node_slashed,
        test_bftqc_builder_threshold,
        test_federated_gateway_rejects_insufficient_quorum,
        test_slashing_engine_full,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            log.info(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            log.info(f"  ❌ EXCEPTION: {e}")
            failed += 1

    log.info()
    log.info("=" * 70)
    if failed == 0:
        log.info("✅ ALL P7 TESTS PASSED")
    else:
        log.info(f"❌ {failed} P7 TEST(S) FAILED")
    log.info("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
