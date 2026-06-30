# SLSA-4 Release Policy — OPA Rego
# CVG + LCCP Supply Chain Security
# ==============================================================
# This policy enforces SLSA Level 4 requirements:
# - Deterministic builds
# - Hermetic execution
# - Canonical git-index manifest
# - SLSA/in-toto provenance
# - External cryptographic attestation
# ==============================================================

package slsa4.release

# ==============================================================
# DEFAULT DENY
# ==============================================================
default release_allowed := false
default deny_reasons := []

# ==============================================================
# G0 — DETERMINISM SETUP
# Must have valid git commit + manifest hash
# ==============================================================
g0_pass {
    input.g0.commit != ""
    input.g0.commit != null
    input.g0.manifest_hash != ""
    input.g0.manifest_hash != null
    count(input.g0.commit) == 40
}

# ==============================================================
# G1 — HERMETIC BUILD
# No network access during build phase
# ==============================================================
g1_pass {
    not input.build.network_accessible
}

# ==============================================================
# G2 — CANONICAL GIT-INDEX MANIFEST
# MUST use git ls-tree (not os.walk)
# ==============================================================
g2_pass {
    input.manifest.source == "git-index"
    input.manifest.count > 0
    input.manifest.hash != ""
    input.manifest.hash != null
}

# ==============================================================
# G3 — SLSA / IN-TOTO PROVENANCE
# Must have valid provenance structure
# ==============================================================
g3_pass {
    input.provenance.verified == true
    input.provenance.standard == "slsa/in-toto"
    input.provenance.predicateType == "https://slsa.dev/provenance/v1"
}

# ==============================================================
# G4 — LCCP DETERMINISTIC REPLAY
# Event-sourced replay must be deterministic
# ==============================================================
g4_pass {
    input.lccp.deterministic == true
    input.lccp.replay_verified == true
}

# ==============================================================
# G5 — CVG GOVERNANCE
# Policy graph + cross-repo consistency
# ==============================================================
g5_pass {
    input.cvg.policy_valid == true
    input.cvg.cross_repo_consistent == true
}

# ==============================================================
# G6 — EXTERNAL ATTESTATION (REQUIRED FOR SLSA-4)
# Cryptographic signature from trusted external anchor
# Valid: GitHub OIDC, Sigstore, HSM, TPM
# ==============================================================
g6_pass {
    input.external.verified == true
    input.external.method != "none"
    input.external.method != ""
    input.external.signature != ""
}

# ==============================================================
# ALL GATES PASS → RELEASE ALLOWED
# ==============================================================
release_allowed {
    g0_pass
    g1_pass
    g2_pass
    g3_pass
    g4_pass
    g5_pass
    g6_pass
}

# ==============================================================
# DENY REASONS — for audit trail
# ==============================================================
deny_reasons[reason] {
    not g0_pass
    reason := {"gate": "G0", "violation": "non-deterministic setup (missing commit or manifest_hash)"}
}

deny_reasons[reason] {
    not g1_pass
    reason := {"gate": "G1", "violation": "build had network access (hermetic violation)"}
}

deny_reasons[reason] {
    not g2_pass
    reason := {"gate": "G2", "violation": "manifest not from canonical git-index"}
}

deny_reasons[reason] {
    not g3_pass
    reason := {"gate": "G3", "violation": "provenance invalid or not SLSA/in-toto format"}
}

deny_reasons[reason] {
    not g4_pass
    reason := {"gate": "G4", "violation": "LCCP replay non-deterministic"}
}

deny_reasons[reason] {
    not g5_pass
    reason := {"gate": "G5", "violation": "CVG policy graph invalid or cross-repo inconsistency"}
}

deny_reasons[reason] {
    not g6_pass
    reason := {"gate": "G6", "violation": "no external cryptographic attestation (SLSA-4 requirement)"}
}

# ==============================================================
# SLSA LEVEL PREDICATE
# ==============================================================
slsa_level := 4 {
    release_allowed
}

slsa_level := 3 {
    not release_allowed
    g0_pass
    g2_pass
    g3_pass
}

slsa_level := 0 {
    not g0_pass
}

# ==============================================================
# SUMMARY
# ==============================================================
summary := result {
    result := {
        "release_allowed": release_allowed,
        "slsa_level": slsa_level,
        "gates_passed": [gate |
            g := ["g0", "g1", "g2", "g3", "g4", "g5", "g6"][_]
            passes := [g0_pass, g1_pass, g2_pass, g3_pass, g4_pass, g5_pass, g6_pass][_]
            passes
        ],
        "gates_failed": [gate |
            g := ["g0", "g1", "g2", "g3", "g4", "g5", "g6"][_]
            not_passes := [g0_pass, g1_pass, g2_pass, g3_pass, g4_pass, g5_pass, g6_pass][_]
            not not_passes
        ],
        "deny_reasons": deny_reasons
    }
}
