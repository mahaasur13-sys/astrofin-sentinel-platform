"""
Named chaos scenarios — fault injection scenarios for cluster validation.
"""

from __future__ import annotations

import json
import os
import subprocess

# ── Base class ────────────────────────────────────────────────────────────────


class ChaosScenario:
    """
    Base class for a single chaos scenario.

    Subclasses must define:
      name        : unique identifier
      description : human-readable one-liner
      fault_type  : Jepsen-aligned fault type
      duration_s  : how long the fault should run (seconds)
      params      : scenario-specific parameters dict

    and implement:
      apply(cluster_ctx) → {"ok": bool, "detail": str}
      rollback() → None
    """

    name: str = ""
    description: str = ""
    fault_type: str = ""
    duration_s: float = 10.0
    params: dict = {}

    def apply(self, cluster_ctx: dict) -> dict:
        raise NotImplementedError

    def rollback(self) -> None:
        pass


# ── Registry ────────────────────────────────────────────────────────────────


SCENARIO_REGISTRY: dict[str, ChaosScenario] = {}


def _reg(cls):
    """Register a ChaosScenario subclass in SCENARIO_REGISTRY."""
    SCENARIO_REGISTRY[cls.name] = cls()
    return cls


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════


@_reg
class _PartitionHalfCluster(ChaosScenario):
    """
    Full bidirectional partition between node-a and node-b.
    Node-c remains reachable from both halves.
    """
    name = "partition_half_cluster"
    description = "Bidirectional partition between node-a and node-b (node-c reachable)"
    fault_type = "partition"
    duration_s = 15.0
    params = {"partition_peers": ["node-a", "node-b"], "exempt": ["node-c"]}

    _rules: list = []
    _cleanup: list = []

    def apply(self, cluster_ctx: dict) -> dict:
        self._rules = [
            "iptables -I DOCKER-USER -s 172.28.1.10 -d 172.28.1.11 -j DROP",
            "iptables -I DOCKER-USER -s 172.28.1.11 -d 172.28.1.10 -j DROP",
        ]
        self._cleanup = [
            "iptables -D DOCKER-USER -s 172.28.1.10 -d 172.28.1.11 -j DROP",
            "iptables -D DOCKER-USER -s 172.28.1.11 -d 172.28.1.10 -j DROP",
        ]
        for r in self._rules:
            subprocess.run(r, shell=True, capture_output=True)
        return {"ok": True, "detail": "partition applied: A↮B, C reachable"}

    def rollback(self) -> None:
        for r in self._cleanup:
            subprocess.run(r, shell=True, capture_output=True)
        self._rules.clear()
        self._cleanup.clear()


@_reg
class _AsymmetricPartition(ChaosScenario):
    """
    Block A→B but allow B→A (one-way heartbeat failure).
    """
    name = "asymmetric_partition"
    description = "One-way block: A→B dropped, B→A allowed"
    fault_type = "partition"
    duration_s = 15.0
    params = {"asymmetric": True, "blocked": ["node-a"], "target": "node-b"}

    _rules: list = []

    def apply(self, cluster_ctx: dict) -> dict:
        self._rules = ["iptables -I DOCKER-USER -s 172.28.1.10 -d 172.28.1.11 -j DROP"]
        for r in self._rules:
            subprocess.run(r, shell=True, capture_output=True)
        return {"ok": True, "detail": "asymmetric partition: A→B blocked, B→A ok"}

    def rollback(self) -> None:
        for r in self._rules:
            subprocess.run(r.replace("-I", "-D"), shell=True, capture_output=True)
        self._rules.clear()


@_reg
class _SlowNodeAmplification(ChaosScenario):
    """
    Inject a 2s pre-processing delay into node-a's RPC path.
    """
    name = "slow_node_amplification"
    description = "Inject 2s pre-processing delay into node-a's RPC path"
    fault_type = "timeout"
    duration_s = 15.0
    params = {"target": "node-a", "delay_s": 2.0}

    def apply(self, cluster_ctx: dict) -> dict:
        t, d = self.params["target"], self.params["delay_s"]
        with open(f"/tmp/chaos_slow_{t}", "w") as f:
            f.write(f"{d}\n")
        os.utime(f"/tmp/chaos_slow_{t}", None)
        return {"ok": True, "detail": f"slow injection: {t} +{d}s delay per RPC"}

    def rollback(self) -> None:
        try:
            os.remove(f"/tmp/chaos_slow_{self.params['target']}")
        except OSError:
            pass


@_reg
class _ByzantineSenderInjection(ChaosScenario):
    """
    Node-c sends conflicting Forward results to A and B.
    """
    name = "byzantine_sender_injection"
    description = "Node-C sends conflicting state to A and B"
    fault_type = "byzantine"
    duration_s = 15.0
    params = {
        "byzantine_node": "node-c",
        "conflicting_terms": {"term": 3, "conflicting_commit_indices": [10, 11]},
    }

    def apply(self, cluster_ctx: dict) -> dict:
        with open("/tmp/chaos_byzantine_node_c", "w") as f:
            json.dump(self.params["conflicting_terms"], f)
        return {"ok": True, "detail": "byzantine injection: node-c will send conflicting state"}

    def rollback(self) -> None:
        try:
            os.remove("/tmp/chaos_byzantine_node_c")
        except OSError:
            pass


@_reg
class _ClockSkewEscalation(ChaosScenario):
    """
    Drift node-c's clock by +5000ms relative to cluster time.
    """
    name = "clock_skew_escalation"
    description = "Inject +5000ms clock drift into node-c"
    fault_type = "clock_skew"
    duration_s = 15.0
    params = {"target": "node-c", "skew_ms": 5000}

    def apply(self, cluster_ctx: dict) -> dict:
        t, sk = self.params["target"], self.params["skew_ms"]
        with open(f"/tmp/chaos_clock_skew_{t}", "w") as f:
            f.write(f"{sk}\n")
        return {"ok": True, "detail": f"clock skew: {t} +{sk}ms drift"}

    def rollback(self) -> None:
        try:
            os.remove(f"/tmp/chaos_clock_skew_{self.params['target']}")
        except OSError:
            pass


@_reg
class _LossBurst(ChaosScenario):
    """
    Spike DRL loss rate from 5% to 80% on node-a.
    """
    name = "loss_burst"
    description = "Spike loss rate 5% → 80% on node-a outbound links"
    fault_type = "drop"
    duration_s = 15.0
    params = {"target": "node-a", "loss_rate": 0.80}

    def apply(self, cluster_ctx: dict) -> dict:
        t, rate = self.params["target"], self.params["loss_rate"]
        with open(f"/tmp/chaos_loss_{t}", "w") as f:
            f.write(f"{rate}\n")
        return {"ok": True, "detail": f"loss burst: {t} loss={rate:.0%}"}

    def rollback(self) -> None:
        try:
            os.remove(f"/tmp/chaos_loss_{self.params['target']}")
        except OSError:
            pass


@_reg
class _NodeIsolation(ChaosScenario):
    """
    Isolate node-c completely: block C↔A and C↔B.
    A+B form majority. C thinks it's still leader (split-brain).
    """
    name = "node_isolation"
    description = "Isolate node-c: C↮A and C↮B blocked, A+B form majority"
    fault_type = "partition"
    duration_s = 15.0
    params = {"isolated_node": "node-c"}

    _rules: list = []

    def apply(self, cluster_ctx: dict) -> dict:
        self._rules = [
            "iptables -I DOCKER-USER -s 172.28.1.12 -d 172.28.1.10 -j DROP",
            "iptables -I DOCKER-USER -s 172.28.1.10 -d 172.28.1.12 -j DROP",
            "iptables -I DOCKER-USER -s 172.28.1.12 -d 172.28.1.11 -j DROP",
            "iptables -I DOCKER-USER -s 172.28.1.11 -d 172.28.1.12 -j DROP",
        ]
        for r in self._rules:
            subprocess.run(r, shell=True, capture_output=True)
        return {"ok": True, "detail": "node-c isolated from A+B"}

    def rollback(self) -> None:
        for r in self._rules:
            subprocess.run(r.replace("-I", "-D"), shell=True, capture_output=True)
        self._rules.clear()


@_reg
class _LatencySpike(ChaosScenario):
    """
    Spike DRL delay_mean from 30ms to 2000ms on node-a.
    """
    name = "latency_spike"
    description = "Spike DRL delay 30ms → 2000ms on node-a"
    fault_type = "timeout"
    duration_s = 15.0
    params = {"target": "node-a", "delay_mean": 2.0, "delay_std": 0.5}

    def apply(self, cluster_ctx: dict) -> dict:
        t, dm, ds = self.params["target"], self.params["delay_mean"], self.params["delay_std"]
        with open(f"/tmp/chaos_delay_{t}", "w") as f:
            f.write(f"{dm}\n{ds}\n")
        return {"ok": True, "detail": f"latency spike: {t} delay={dm}s±{ds}s"}

    def rollback(self) -> None:
        t = self.params["target"]
        for s in ["", "_std"]:
            try:
                os.remove(f"/tmp/chaos_delay_{t}{s}")
            except OSError:
                pass


# ── Factory functions ─────────────────────────────────────────────────────────

def partition_half_cluster() -> ChaosScenario:
    return _PartitionHalfCluster()

def asymmetric_partition() -> ChaosScenario:
    return _AsymmetricPartition()

def slow_node_amplification() -> ChaosScenario:
    return _SlowNodeAmplification()

def byzantine_sender_injection() -> ChaosScenario:
    return _ByzantineSenderInjection()

def clock_skew_escalation() -> ChaosScenario:
    return _ClockSkewEscalation()

def loss_burst() -> ChaosScenario:
    return _LossBurst()

def node_isolation() -> ChaosScenario:
    return _NodeIsolation()

def latency_spike() -> ChaosScenario:
    return _LatencySpike()
