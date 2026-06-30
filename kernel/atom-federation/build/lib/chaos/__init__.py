"""
Chaos Engineering Layer — v6.3.

Provides adversarial fault injection for distributed cluster validation.

Modules
-------
scenarios : Named chaos scenarios (partition, corruption, spike, etc.)
partitioner : Network partition injector (nftables/iptables on host)
harness : Jepsen-style test harness
validator : SBS-aware result validator
failure_classifier : Integrates with sbs/failure_classifier.py
"""

from chaos.harness import ChaosHarness, ChaosResult
from chaos.partitioner import HostChaosAgent, NetworkPartitioner
from chaos.replay_validator import (
    ChaosTrace,
    DivergenceReport,
    ReplayResult,
    ReplayValidator,
    ReplayVerdict,
    TracePhase,
)
from chaos.scenarios import (
    SCENARIO_REGISTRY,
    ChaosScenario,
    asymmetric_partition,
    byzantine_sender_injection,
    clock_skew_escalation,
    latency_spike,
    loss_burst,
    node_isolation,
    partition_half_cluster,
    slow_node_amplification,
)
from chaos.stress_envelope import StabilityEnvelope, StabilityState
from chaos.validator import ChaosValidator, ValidationResult

__all__ = [
    # Scenarios
    "ChaosScenario",
    "SCENARIO_REGISTRY",
    "partition_half_cluster",
    "slow_node_amplification",
    "byzantine_sender_injection",
    "clock_skew_escalation",
    "loss_burst",
    "node_isolation",
    "asymmetric_partition",
    "latency_spike",
    # Harness
    "ChaosHarness",
    "ChaosResult",
    # Validator
    "ChaosValidator",
    "ValidationResult",
    # Partitioner
    "NetworkPartitioner",
    "HostChaosAgent",
    # Stability envelope
    "StabilityEnvelope",
    "StabilityState",
    # Replay validator
    "ReplayValidator",
    "ReplayVerdict",
    "TracePhase",
    "ChaosTrace",
    "ReplayResult",
    "DivergenceReport",
]
