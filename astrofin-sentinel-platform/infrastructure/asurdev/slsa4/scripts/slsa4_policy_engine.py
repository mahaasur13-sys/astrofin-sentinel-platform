#!/usr/bin/env python3
"""
SLSA-4 Policy Engine — OPA/Rego Policy Validator
CVG + LCCP Supply Chain Security
==============================================================
Uses OPA (Open Policy Agent) for Rego-based policy enforcement.
Falls back to native Python validator if OPA unavailable.
"""
import hashlib
import json
import logging
import os
import subprocess

log = logging.getLogger(__name__)


POLICY_DIR = os.path.dirname(os.path.abspath(__file__))
OPA_BIN = os.path.join(POLICY_DIR, '../opa_linux_amd64')

SLSA4_POLICY = """package slsa4.release

default release_allowed := false

# G0: Determinism — deterministic setup required
g0_deterministic {
    input.g0.commit != ""
    input.g0.manifest_hash != ""
}

# G1: Hermetic build — no network access during build
g1_hermetic {
    not input.build.had_network
}

# G2: Canonical git-index — git ls-tree only (NO os.walk)
g2_git_index {
    input.manifest.source == "git-index"
    input.manifest.count > 0
    input.manifest.hash != ""
}

# G3: Provenance — SLSA/in-toto valid structure
g3_provenance {
    input.provenance.verified
    input.provenance.standard == "slsa/in-toto"
    input.provenance.predicateType == "https://slsa.dev/provenance/v1"
}

# G4: LCCP deterministic replay
g4_lccp_deterministic {
    input.lccp.deterministic
    input.lccp.replay_verified
}

# G5: CVG governance policy graph valid
g5_cvg_governance {
    input.cvg.policy_valid
    input.cvg.cross_repo_consistent
}

# G6: External cryptographic attestation required
g6_external_attestation {
    input.external.verified
    input.external.method != "none"
    input.external.signature != ""
}

# ALL GATES PASS → release allowed
release_allowed {
    g0_deterministic
    g1_hermetic
    g2_git_index
    g3_provenance
    g4_lccp_deterministic
    g5_cvg_governance
    g6_external_attestation
}

# Release denial reasons
deny_reason = reason {
    not release_allowed
    reasons := [
        { "gate": "G0", "violation": "non-deterministic setup" },
        { "gate": "G1", "violation": "build had network access" },
        { "gate": "G2", "violation": "manifest not from git-index" },
        { "gate": "G3", "violation": "provenance invalid or missing" },
        { "gate": "G4", "violation": "LCCP replay non-deterministic" },
        { "gate": "G5", "violation": "CVG policy graph invalid" },
        { "gate": "G6", "violation": "no external attestation" }
    ]
    reason := [r | reasons[_].gate == r.gate]
}
"""

NATIVE_POLICY = {
    'g0': lambda d: bool(d.get('commit')) and bool(d.get('manifest_hash')),
    'g1': lambda d: not d.get('build', {}).get('had_network', False),
    'g2': lambda d: d.get('manifest', {}).get('source') == 'git-index' and d.get('manifest', {}).get('count', 0) > 0,
    'g3': lambda d: d.get('provenance', {}).get('verified') and d.get('provenance', {}).get('standard') == 'slsa/in-toto',
    'g4': lambda d: d.get('lccp', {}).get('deterministic') and d.get('lccp', {}).get('replay_verified'),
    'g5': lambda d: d.get('cvg', {}).get('policy_valid') and d.get('cvg', {}).get('cross_repo_consistent'),
    'g6': lambda d: d.get('external', {}).get('verified') and d.get('external', {}).get('method') != 'none',
}

def h(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()

class SLSA4PolicyEngine:
    def __init__(self, bundle_path=None):
        self.bundle_path = bundle_path or os.environ.get('SLSA4_BUNDLE', '/tmp/attestation_bundle.json')
        self.policy = SLSA4_POLICY
        self.opa_available = os.path.exists(OPA_BIN)

    def load_bundle(self):
        if os.path.exists(self.bundle_path):
            with open(self.bundle_path) as f:
                return json.load(f)
        return {}

    def evaluate_native(self, bundle: dict) -> dict:
        log.info("[OPA-NATIVE] Evaluating SLSA-4 policy...")
        results = {}
        gate_names = list(NATIVE_POLICY.keys())
        for gate in sorted(gate_names):
            passed = NATIVE_POLICY[gate](bundle)
            results[f'G{gate[-1] if gate.startswith("g") else gate}'] = {'passed': passed}
            status = 'PASS' if passed else 'FAIL'
            log.info(f"  [{status}] {gate.upper()}")
        return results

    def evaluate_opa(self, bundle: dict) -> dict:
        if not self.opa_available:
            log.info("[OPA] Binary not found, using native validator")
            return self.evaluate_native(bundle)
        log.info("[OPA] Using OPA Rego engine...")
        rego_input = {'input': bundle}
        rego_file = os.path.join(POLICY_DIR, 'slsa4_policy.rego')
        with open(rego_file, 'w') as f:
            f.write(self.policy)
        result = subprocess.run(
            [OPA_BIN, 'eval', '--format', 'json', '--data', rego_file, 'data.slsa4.release'],
            input=json.dumps(rego_input).encode(),
            capture_output=True
        )
        if result.returncode != 0:
            log.info(f"[OPA] Error: {result.stderr.decode()}")
            return self.evaluate_native(bundle)
        output = json.loads(result.stdout)
        allowed = output.get('result', [{}])[0].get('release_allowed', False)
        return {'release_allowed': allowed, 'engine': 'OPA Rego v0.69+'}

    def run(self, bundle_path=None):
        bundle = self.load_bundle() if not bundle_path else json.load(open(bundle_path)) if os.path.exists(bundle_path) else {}
        log.info("=" * 70)
        log.info("SLSA-4 POLICY ENGINE v5.0")
        log.info("=" * 70)
        log.info(f"OPA available: {self.opa_available}")
        log.info(f"Bundle: {bundle_path or self.bundle_path}")
        log.info()
        if self.opa_available:
            results = self.evaluate_opa(bundle)
        else:
            results = self.evaluate_native(bundle)
        release_allowed = all(r.get('passed', False) for r in results.values()) if all(isinstance(v, dict) for v in results.values()) else results.get('release_allowed', False)
        log.info()
        log.info("=" * 70)
        log.info(f"SLSA-4 RELEASE ALLOWED: {release_allowed}")
        if not release_allowed:
            log.info("DENY REASONS:")
            for gate, result in sorted(results.items()):
                if isinstance(result, dict) and not result.get('passed'):
                    log.info(f"  ✗ {gate}: {result.get('violation', 'policy violation')}")
        log.info("=" * 70)
        return release_allowed

if __name__ == '__main__':
    import sys
    bundle_arg = sys.argv[1] if len(sys.argv) > 1 else None
    engine = SLSA4PolicyEngine(bundle_arg)
    allowed = engine.run()
    exit(0 if allowed else 1)
