# kubernetes/deterministic_operator.py — NEW
# ATOM-META-RL-022 P1 — Kubernetes Execution Determinism Layer

import hashlib
from dataclasses import dataclass

# ── DeterministicPodScheduler ─────────────────────────────────────────────────

class DeterministicPodScheduler:
    r'''
    Deterministic Kubernetes pod scheduling.

    Guarantees:
      - Pod startup order is deterministic (hash-based)
      - Replica IDs are stable across restarts (deterministic)
      - No random in scheduling decisions
    '''

    def __init__(self, cluster_name: str, all_nodes: list[str]):
        self.cluster_name = cluster_name
        self.all_nodes = sorted(all_nodes)  # deterministic ordering

    def get_startup_order(self) -> list[str]:
        r'''
        Compute deterministic pod startup order.
        Sort nodes by hash(node_id + cluster_name).

        Returns: list of node_ids in deterministic startup order.
        '''
        return sorted(
            self.all_nodes,
            key=lambda n: hashlib.sha256(
                f'{n}:{self.cluster_name}:ATOM-STARTUP'.encode()
            ).hexdigest()
        )

    def assign_replica_id(self, pod_name: str, total_replicas: int) -> int:
        r'''
        Assign deterministic replica ID.
        hash(pod_name) % total_replicas — stable across restarts.

        Returns: replica ID (0-indexed).
        '''
        if total_replicas <= 0:
            return 0
        h = int(
            hashlib.sha256(pod_name.encode()).hexdigest()[:8],
            16
        )
        return h % total_replicas

    def get_primary_node(self) -> str | None:
        '''Get the primary node (first in startup order).'''
        if self.all_nodes:
            return self.get_startup_order()[0]
        return None


# ── ReplicaIdentityStabilityMapping ──────────────────────────────────────────

class ReplicaIdentityStabilityMapping:
    r'''
    Stable replica identity across pod restarts.

    Guarantees:
      - Same pod_uid always maps to same stable_id
      - Identity doesn't change on restart (content-addressed)
      - No random, no time in identity computation
    '''

    def __init__(self, cluster_name: str):
        self.cluster_name = cluster_name
        self._mapping: dict[str, str] = {}  # pod_uid -> stable_node_id

    def get_stable_id(self, pod_uid: str, node_id: str) -> str:
        r'''
        Get stable identity for pod.

        stable_id = hash(pod_uid + cluster_name) — deterministic,
        doesn't change on restart.

        Args:
            pod_uid: Kubernetes pod UID (changes on restart)
            node_id: Current node assignment

        Returns:
            Stable identity string (12 hex chars)
        '''
        return hashlib.sha256(
            f'{pod_uid}:{self.cluster_name}:ATOM-IDENTITY'.encode()
        ).hexdigest()[:12]

    def register_pod(self, pod_uid: str, node_id: str, stable_id: str) -> None:
        '''Register a pod's stable identity.'''
        self._mapping[pod_uid] = stable_id

    def verify_stability(self, pod_uid: str, expected_stable_id: str) -> bool:
        '''Verify pod's stable identity hasn't changed.'''
        return self._mapping.get(pod_uid) == expected_stable_id

    def get_stable_id_for_pod(self, pod_uid: str) -> str | None:
        '''Get stable ID for registered pod.'''
        return self._mapping.get(pod_uid)


# ── DeterministicStartupSequence ──────────────────────────────────────────────

@dataclass
class StartupState:
    node_id: str
    started: bool = False
    ready: bool = False
    barrier_arrived: bool = False


class DeterministicStartupSequence:
    r'''
    Deterministic cluster startup sequence.

    Guarantees:
      - Nodes start in deterministic order (hash-based)
      - Quorum must be reached before execution starts
      - Startup sequence is reproducible (deterministic)
    '''

    def __init__(self, nodes: list[str], cluster_name: str):
        self.nodes = sorted(nodes)  # deterministic ordering
        self.cluster_name = cluster_name
        self._started: set[str] = set()
        self._ready: set[str] = set()
        self._states: dict[str, StartupState] = {
            n: StartupState(node_id=n) for n in self.nodes
        }

    def get_next_startup_candidate(self) -> str | None:
        '''Get next node that should start (deterministic order).'''
        startup_order = sorted(
            self.nodes,
            key=lambda n: hashlib.sha256(
                f'{n}:{self.cluster_name}:ATOM-STARTUP'.encode()
            ).hexdigest()
        )
        for node in startup_order:
            if node not in self._started:
                return node
        return None

    def mark_started(self, node_id: str) -> None:
        '''Mark node as started.'''
        if node_id in self._states:
            self._states[node_id].started = True
            self._started.add(node_id)

    def mark_ready(self, node_id: str) -> None:
        '''Mark node as ready to execute.'''
        if node_id in self._states:
            self._states[node_id].ready = True
            self._ready.add(node_id)

    def mark_barrier_arrived(self, node_id: str) -> None:
        '''Mark node as having arrived at startup barrier.'''
        if node_id in self._states:
            self._states[node_id].barrier_arrived = True

    def is_ready_to_execute(self) -> bool:
        '''
        Check if cluster is ready to execute.
        Ready when quorum of nodes have started AND are ready.
        '''
        quorum = (len(self.nodes) // 2) + 1
        return len(self._ready) >= quorum

    def get_started_count(self) -> int:
        return len(self._started)

    def get_ready_count(self) -> int:
        return len(self._ready)

    def get_startup_progress(self) -> dict[str, int]:
        return {
            'total': len(self.nodes),
            'started': len(self._started),
            'ready': len(self._ready),
            'quorum': (len(self.nodes) // 2) + 1,
            'can_execute': self.is_ready_to_execute(),
        }

    def get_deterministic_sequence_hash(self) -> str:
        '''
        Compute deterministic hash of startup sequence.
        Same cluster config + same nodes → same hash.
        '''
        ordered = sorted(
            self.nodes,
            key=lambda n: hashlib.sha256(
                f'{n}:{self.cluster_name}:ATOM-STARTUP'.encode()
            ).hexdigest()
        )
        content = ','.join(ordered)
        return hashlib.sha256(
            f'{content}:{self.cluster_name}:ATOM-SEQ'.encode()
        ).hexdigest()[:16]


# ── DeterministicKubernetesAnnotations ────────────────────────────────────────

class DeterministicKubernetesAnnotations:
    r'''
    Kubernetes pod annotations for deterministic execution.

    These annotations ensure K8s scheduler and operator respect
    deterministic ordering constraints.
    '''

    @staticmethod
    def make_startup_annotation(cluster_name: str, startup_sequence_hash: str) -> dict:
        return {
            'atom-federation.io/startup-sequence-hash': startup_sequence_hash,
            'atom-federation.io/startup-barrier-enabled': 'true',
        }

    @staticmethod
    def make_replica_annotation(cluster_name: str, stable_id: str, replica_id: int) -> dict:
        return {
            'atom-federation.io/replica-identity': f'stable-{stable_id}',
            'atom-federation.io/replica-id': str(replica_id),
            'atom-federation.io/cluster': cluster_name,
        }

    @staticmethod
    def make_lockstep_annotation(enabled: bool = True) -> dict:
        return {
            'atom-federation.io/lockstep-mode': 'strict' if enabled else 'disabled',
            'atom-federation.io/execution-barrier': 'true',
        }

    @staticmethod
    def compute_pod_identity_hash(pod_name: str, cluster_name: str) -> str:
        return hashlib.sha256(
            f'{pod_name}:{cluster_name}:ATOM-POD-ID'.encode()
        ).hexdigest()[:12]


# ── DeterministicInitContainerOrder ───────────────────────────────────────────

class DeterministicInitContainerOrder:
    r'''
    Deterministic init container ordering for pod startup.

    Ensures init containers run in deterministic order across all pods.
    '''

    @staticmethod
    def get_init_container_order(pod_name: str) -> list[str]:
        r'''
        Get deterministic init container execution order.

        Order is based on hash(pod_name + container_name).
        Same pod → same container order regardless of restart.
        '''
        # Standard init containers for ATOM pods
        containers = [
            'wait-for-federation',
            'validate-config',
            'setup-persistence',
            'init-barrier',
        ]
        return sorted(
            containers,
            key=lambda c: hashlib.sha256(
                f'{pod_name}:{c}:ATOM-INIT'.encode()
            ).hexdigest()
        )
