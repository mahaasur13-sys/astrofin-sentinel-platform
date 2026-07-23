"""
SBS Distributed Client — cross-node invariant evaluation.

Each node runs a local SBS enforcer; this client coordinates
global (quorum-wide) invariant checks by collecting layer states
from all peers and evaluating them centrally.
"""
import os
import sys
import threading
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from sbs.boundary_spec import SystemBoundarySpec
from sbs.global_invariant_engine import GlobalInvariantEngine


class SBSDistributedClient:
    """
    Manages cross-node SBS invariant evaluation.

    workflow:
        1. collect()  — gather local layer states from all reachable peers
        2. evaluate()  — run GlobalInvariantEngine across all collected states
        3. report()    — log results; optionally halt on violation

    In distributed mode, quorum = majority (N/2+1).
    """

    def __init__(self, node_id: str, peers: list[str]):
        self.node_id = node_id
        self.peers = peers
        self.spec = SystemBoundarySpec()
        self.engine = GlobalInvariantEngine(self.spec)
        self._local_state: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._last_result: dict | None = None
        self._last_evaluate_ts: float = 0

    # ── Local state registration ───────────────────────────────────────────

    def update_local_layer(self, layer: str, state: dict):
        """Update this node's layer state snapshot."""
        with self._lock:
            self._local_state[layer] = state.copy()

    def get_local_state(self) -> dict[str, dict]:
        with self._lock:
            return {k: v.copy() for k, v in self._local_state.items()}

    # ── Cross-node evaluation ──────────────────────────────────────────────

    def evaluate_quorum(
        self,
        peer_states: dict[str, dict[str, dict]],
        quorum_ratio: float = 0.66,
    ) -> bool:
        """
        Evaluate invariants across quorum of nodes.

        peer_states: {
            "node-a": {"drl": {...}, "ccl": {...}, "f2": {...}, "desc": {...}},
            "node-b": {...},
            ...
        }
        At least quorum_ratio fraction of peers must agree (no violation).
        """
        total = len(peer_states) + 1  # +1 for self
        required = max(2, int(total * quorum_ratio))

        all_ok = True
        for node_id, layers in peer_states.items():
            drl = layers.get("drl", {})
            ccl = layers.get("ccl", {})
            f2 = layers.get("f2", {})
            desc = layers.get("desc", {})

            ok = self.engine.evaluate(drl, ccl, f2, desc)
            if not ok:
                all_ok = False

        # Also evaluate local state against global spec
        with self._lock:
            drl_l = self._local_state.get("drl", {})
            ccl_l = self._local_state.get("ccl", {})
            f2_l = self._local_state.get("f2", {})
            desc_l = self._local_state.get("desc", {})

        local_ok = self.engine.evaluate(drl_l, ccl_l, f2_l, desc_l)
        if not local_ok:
            all_ok = False

        self._last_evaluate_ts = time.time()
        self._last_result = {
            "ok": all_ok,
            "quorum_required": required,
            "peers_evaluated": len(peer_states) + 1,
            "violations": self.engine.get_violations(),
            "ts": self._last_evaluate_ts,
        }

        return all_ok

    def get_last_result(self) -> dict | None:
        return self._last_result

    def get_violations(self) -> list[str]:
        return self.engine.get_violations()
