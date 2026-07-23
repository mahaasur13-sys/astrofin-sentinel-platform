"""
Meta-Adaptive Control Layer — v7.8
Closes the loop: temporal proof output → control weight adaptation.

Modules:
    proof_feedback_controller     — proof verdict → arbitration weight delta
    stability_weighted_arbitrator — arbitrator with stability-adjusted weights
    drift_policy_adaptor          — drift detection → policy adjustment actuator
    temporal_gain_scheduler       — stability-aware global gain scheduler
"""
from meta_control.drift_policy_adaptor import DriftPolicyAdaptor
from meta_control.proof_feedback_controller import ProofFeedbackController
from meta_control.stability_weighted_arbitrator import StabilityWeightedArbitrator
from meta_control.temporal_gain_scheduler import TemporalGainScheduler

__all__ = [
    "DriftPolicyAdaptor",
    "ProofFeedbackController",
    "StabilityWeightedArbitrator",
    "TemporalGainScheduler",
]
