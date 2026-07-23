"""
v7.7 — Temporal Proof Continuity Layer
Proof chain across time ticks: proof(t) → proof(t+1) with causal traceability.
"""

from proof.causal_proof_graph import CausalLink, CausalLinkType, CausalProofGraph
from proof.decision_prover import DecisionProver
from proof.invariant_registry import InvariantRegistry, InvariantType
from proof.proof_chain import ChainLink, ProofChain
from proof.proof_drift_detector import DriftEvent, DriftReport, ProofDriftDetector
from proof.proof_kernel import DecisionRecord, ProofKernel, ProofStatus
from proof.stability_prover import StabilityMetrics, StabilityProver
from proof.temporal_verifier import TemporalVerificationReport, TemporalVerifier
from proof.verification_engine import VerificationEngine

__all__ = [
    # v7.6 core
    "ProofKernel",
    "ProofStatus",
    "DecisionRecord",
    "InvariantRegistry",
    "InvariantType",
    "DecisionProver",
    "VerificationEngine",
    # v7.7 temporal
    "ProofChain",
    "ChainLink",
    "CausalProofGraph",
    "CausalLinkType",
    "CausalLink",
    "StabilityProver",
    "StabilityMetrics",
    "ProofDriftDetector",
    "DriftEvent",
    "DriftReport",
    "TemporalVerifier",
    "TemporalVerificationReport",
]
