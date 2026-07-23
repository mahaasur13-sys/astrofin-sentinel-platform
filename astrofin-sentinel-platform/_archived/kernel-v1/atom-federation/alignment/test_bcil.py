"""test_bcil.py v10.4 BCIL tests."""
import sys

import logging
log = logging.getLogger(__name__)


sys.path.insert(0, '/home/workspace/atom-federation-os')
from alignment.bcil import BCIL, ByzantineConvergenceFunction, ByzantineFailureType, QuorumSpec


def test_bc_f1_byzantine_branch_dominated():
    quorum = QuorumSpec(n_nodes=4, f_byzantine=1)
    bcil = BCIL(quorum)
    branches = [
        {'branch_id': 'A', 'digest': 'digest_a'},
        {'branch_id': 'B', 'digest': 'digest_b'},
    ]
    trust_scores = {'A': 0.4, 'B': 0.9}
    node_trust = {'n1': 0.9, 'n2': 0.9, 'n3': 0.9, 'n4': 0.9, 'n5': 0.95}
    voter_assignments = {'A': ['n1', 'n2', 'n3'], 'B': ['n4', 'n5']}
    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.3)
    assert report.failure_type == ByzantineFailureType.BYZANTINE_BRANCH_DOMINATED, repr(report.failure_type)
    assert not report.safe_state
    log.info('  F1 byzantine_dominated: %s ok' % report.failure_type.name)

def test_bc_f2_quorum_bypass():
    quorum = QuorumSpec(n_nodes=4, f_byzantine=1)
    bcil = BCIL(quorum)
    branches = [{'branch_id': 'A', 'digest': 'digest_a'}]
    trust_scores = {'A': 0.6}
    node_trust = {'n1': 0.9, 'n2': 0.9, 'n3': 0.9, 'n4': 0.1}
    voter_assignments = {'A': ['n1', 'n2']}
    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.2)
    assert report.failure_type == ByzantineFailureType.QUORUM_BYPASS, repr(report.failure_type)
    assert not report.merge_allowed
    log.info('  F2 quorum_bypass: %s ok' % report.failure_type.name)

def test_bc_f3_trust_inflation():
    quorum = QuorumSpec(n_nodes=7, f_byzantine=2)
    bcil = BCIL(quorum)
    branches = [{'branch_id': 'M', 'digest': 'digest_m'}]
    trust_scores = {'M': 0.7}
    node_trust = {'n1': 0.3, 'n2': 0.3, 'n3': 0.3, 'n4': 0.95, 'n5': 0.95}
    voter_assignments = {'M': ['n4', 'n5']}
    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.15)
    assert report.failure_type in (ByzantineFailureType.TRUST_INFLATION, ByzantineFailureType.QUORUM_BYPASS)
    log.info('  F3 trust_inflation: %s ok' % report.failure_type.name)

def test_bc_f4_equivocation():
    quorum = QuorumSpec(n_nodes=4, f_byzantine=1)
    bcil = BCIL(quorum)
    branches = [
        {'branch_id': 'X', 'digest': 'digest_abcdefgh'},
        {'branch_id': 'Y', 'digest': 'digest_abcdexyz'},
    ]
    trust_scores = {'X': 0.5, 'Y': 0.5}
    node_trust = {'n1': 0.8, 'n2': 0.8, 'n3': 0.8}
    voter_assignments = {'X': ['n1', 'n2', 'n3'], 'Y': ['n1', 'n2', 'n3']}
    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.3)
    log.info('  F4 equivocation: equiv=%s risk=%.3f ok' % (report.risk_assessment.equivocation_detected, report.risk_assessment.max_risk_score))

def test_bc_f5_convergence_to_malicious():
    quorum = QuorumSpec(n_nodes=4, f_byzantine=1)
    bcil = BCIL(quorum)
    branches = [{'branch_id': 'malicious', 'digest': 'bad_digest'}]
    trust_scores = {'malicious': 0.95}
    node_trust = {'n1': 0.2, 'n2': 0.2, 'n3': 0.2, 'n4': 0.98, 'n5': 0.98}
    voter_assignments = {'malicious': ['n4', 'n5']}
    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.05)
    assert not report.safe_state
    assert report.c_b > report.base_convergence
    log.info('  F5 malicious_convergence: C_B=%.3f > C=%.3f safe=%s ok' % (report.c_b, report.base_convergence, report.safe_state))

def test_bc_c_b_metric():
    cf = ByzantineConvergenceFunction(lambda_coefficient=0.5)
    cb1 = cf.compute(gcpl_convergence=0.3, byzantine_risk=0.0)
    assert abs(cb1 - 0.3) < 1e-9
    cb2 = cf.compute(gcpl_convergence=0.3, byzantine_risk=0.8)
    expected = min(1.0, 0.3 + 0.5 * 0.8)
    assert abs(cb2 - expected) < 1e-9
    cb3 = cf.compute(gcpl_convergence=0.9, byzantine_risk=0.9)
    assert cb3 == 1.0
    log.info('  C_B formula: C=0.3,R=0.0->%.1f | C=0.3,R=0.8->%.2f | C=0.9,R=0.9->%.1f ok' % (cb1, cb2, cb3))

def test_bc_safe_merge():
    quorum = QuorumSpec(n_nodes=7, f_byzantine=2)
    bcil = BCIL(quorum)
    branches = [{'branch_id': 'good', 'digest': 'good_digest'}]
    trust_scores = {'good': 0.7}
    node_trust = dict(('n%d' % i, 0.8) for i in range(1, 8))
    voter_assignments = {'good': ['n1', 'n2', 'n3', 'n4', 'n5']}
    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.3)
    assert report.merge_allowed
    assert report.safe_state
    assert report.honest_can_progress
    log.info('  safe_merge: allowed=%s safe=%s ok' % (report.merge_allowed, report.safe_state))

def test_bc_split_brain():
    quorum = QuorumSpec(n_nodes=7, f_byzantine=2)
    bcil = BCIL(quorum)
    branches = [
        {'branch_id': 'A', 'digest': 'digest_a'},
        {'branch_id': 'B', 'digest': 'digest_b'},
    ]
    trust_scores = {'A': 0.5, 'B': 0.5}
    node_trust = dict(('n%d' % i, 0.8) for i in range(1, 8))
    voter_assignments = {'A': ['n1', 'n2', 'n3', 'n4', 'n5'], 'B': ['n1', 'n2', 'n3', 'n6', 'n7']}
    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.4)
    assert report.failure_type == ByzantineFailureType.SPLIT_BRAIN, repr(report.failure_type)
    assert not report.merge_allowed
    log.info('  split_brain: %s ok' % report.failure_type.name)

def run_tests():
    tests = [
        test_bc_f1_byzantine_branch_dominated,
        test_bc_f2_quorum_bypass,
        test_bc_f3_trust_inflation,
        test_bc_f4_equivocation,
        test_bc_f5_convergence_to_malicious,
        test_bc_c_b_metric,
        test_bc_safe_merge,
        test_bc_split_brain,
    ]
    passed = 0
    for t in tests:
        try:
            if t():
                passed += 1
        except AssertionError as e:
            log.info('  FAIL %s: %s' % (t.__name__, e))
        except Exception as e:
            log.info('  ERROR %s: %s %s' % (t.__name__, type(e).__name__, e))
    log.info('='*60)
    log.info('  BCIL v10.4: %d/%d passed' % (passed, len(tests)))
    log.info('='*60)
    return passed == len(tests)

if __name__ == '__main__':
    ok = run_tests()
    exit(0 if ok else 1)
