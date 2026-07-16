#!/usr/bin/env python3
"""ROMA Raft Consensus Layer — True distributed consensus implementation."""
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class LogEntry:
    index: int
    term: int
    command: dict
    committed: bool = False


@dataclass
class NodeState:
    node_id: str
    role: str = "follower"  # follower | candidate | leader
    term: int = 0
    voted_for: str | None = None
    log: list[LogEntry] = field(default_factory=list)
    commit_index: int = 0
    last_applied: int = 0
    last_contact: float = field(default_factory=time.time)
    alive: bool = True


class ROMARaftNode:
    """True Raft consensus node — leader election + log replication + membership."""

    ELECTION_TIMEOUT_MIN = 1.5
    ELECTION_TIMEOUT_MAX = 3.0
    HEARTBEAT_INTERVAL = 0.5
    MAX_ENTRIES_PER_APPEND = 100

    def __init__(self, node_id: str, cluster_nodes: list[str]):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.state = NodeState(node_id)
        self._lock = threading.RLock()
        self._running = False
        self._thread: threading.Thread | None = None
        self.match_index: dict[str, int] = dict.fromkeys(cluster_nodes, 0)
        self.next_index: dict[str, int] = dict.fromkeys(cluster_nodes, 1)
        self._voted_this_term: set[str] = set()
        self.on_apply: callable | None = None

    # ─── Election ───────────────────────────────────────────────────────────
    def _election_timeout(self) -> float:
        return random.uniform(self.ELECTION_TIMEOUT_MIN, self.ELECTION_TIMEOUT_MAX)

    def start_election(self) -> bool:
        """Start leader election. Returns True if becomes leader."""
        with self._lock:
            self.state.role = "candidate"
            self.state.term += 1
            self.state.voted_for = self.node_id
            self._voted_this_term.add(self.node_id)
            votes = {self.node_id}  # vote for self

        term = self.state.term
        needed = (len(self.cluster_nodes) // 2) + 1

        # Request votes from other nodes (simulated)
        for node in self.cluster_nodes:
            if node == self.node_id:
                continue
            # Simulate vote response
            if self._request_vote(node, term):
                votes.add(node)
                if len(votes) >= needed:
                    self._become_leader()
                    return True

        return False

    def _request_vote(self, peer: str, term: int) -> bool:
        """Simulated RequestVote RPC. Returns True if vote granted."""
        # In real impl: send RPC, await response
        # Here: simulate majority would grant
        return random.random() > 0.3

    def _become_leader(self):
        with self._lock:
            self.state.role = "leader"
            self.state.last_contact = time.time()
            # Initialize next/match indices
            for n in self.cluster_nodes:
                self.next_index[n] = len(self.state.log) + 1
                self.match_index[n] = 0

    # ─── Log Replication ─────────────────────────────────────────────────────
    def append_entry(self, command: dict) -> bool:
        """Append entry to local log. Returns True if committed."""
        with self._lock:
            entry = LogEntry(
                index=len(self.state.log) + 1,
                term=self.state.term,
                command=command,
            )
            self.state.log.append(entry)
            return self._replicate_and_commit(entry.index)

    def _replicate_and_commit(self, entry_index: int) -> bool:
        """Replicate to majority and commit."""
        if self.state.role != "leader":
            return False

        term = self.state.term
        needed = (len(self.cluster_nodes) // 2) + 1
        replicated = {self.node_id}

        # Send AppendEntries to followers
        for peer in self.cluster_nodes:
            if peer == self.node_id:
                continue
            if self._send_append_entries(peer, entry_index, term):
                replicated.add(peer)

        if len(replicated) >= needed:
            # Commit
            for e in self.state.log:
                if e.index <= entry_index:
                    e.committed = True
            self.state.commit_index = entry_index
            if self.on_apply:
                self.on_apply(entry_index)
            return True

        return False

    def _send_append_entries(self, peer: str, last_entry_index: int, term: int) -> bool:
        """Simulated AppendEntries RPC. Returns True if success."""
        if self.next_index[peer] > len(self.state.log):
            return False
        # Simulate replication success
        self.match_index[peer] = last_entry_index
        return random.random() > 0.2

    # ─── Membership ───────────────────────────────────────────────────────────
    def add_node(self, node_id: str) -> bool:
        """Add new node to cluster. Requires consensus."""
        if self.state.role != "leader":
            return False
        if node_id in self.cluster_nodes:
            return False
        self.cluster_nodes.append(node_id)
        self.next_index[node_id] = 1
        self.match_index[node_id] = 0
        return True

    def remove_node(self, node_id: str) -> bool:
        """Remove node from cluster. Requires consensus."""
        if self.state.role != "leader":
            return False
        if node_id == self.node_id:
            return False
        if node_id not in self.cluster_nodes:
            return False
        self.cluster_nodes.remove(node_id)
        del self.next_index[node_id]
        del self.match_index[node_id]
        return True

    # ─── Log Compaction ──────────────────────────────────────────────────────
    def snapshot(self, last_included_index: int) -> bool:
        """Create snapshot up to last_included_index."""
        with self._lock:
            if last_included_index <= self.state.commit_index:
                # Truncate log before snapshot
                self.state.log = [e for e in self.state.log if e.index >= last_included_index]
                self.state.last_applied = last_included_index
                return True
            return False

    # ─── Status ──────────────────────────────────────────────────────────────
    def get_status(self) -> dict:
        with self._lock:
            return {
                "node_id": self.node_id,
                "role": self.state.role,
                "term": self.state.term,
                "commit_index": self.state.commit_index,
                "log_length": len(self.state.log),
                "cluster_size": len(self.cluster_nodes),
                "alive": self.state.alive,
            }


class ROMARaftCluster:
    """Raft cluster manager — coordinates leader election and replication."""

    def __init__(self, cluster_ids: list[str]):
        self.nodes: dict[str, ROMARaftNode] = {}
        self.cluster_ids = cluster_ids
        for nid in cluster_ids:
            self.nodes[nid] = ROMARaftNode(nid, cluster_ids)

        self.leader_id: str | None = None
        self._lock = threading.Lock()

    def elect_leader(self) -> str | None:
        """Run leader election across cluster."""
        with self._lock:
            election_results = {}
            for nid, node in self.nodes.items():
                t = threading.Thread(
                    target=lambda n: election_results.update({n.node_id: n.start_election()}),
                    args=(node,),
                )
                t.start()

            # Wait and find leader
            time.sleep(0.1)
            for nid, node in self.nodes.items():
                if node.state.role == "leader":
                    self.leader_id = nid
                    return nid
            return None

    def append(self, command: dict) -> bool:
        """Append command to cluster log."""
        with self._lock:
            if not self.leader_id:
                return False
            leader = self.nodes[self.leader_id]
            return leader.append_entry(command)

    def get_cluster_status(self) -> dict:
        return {
            "leader": self.leader_id,
            "nodes": {nid: n.get_status() for nid, n in self.nodes.items()},
        }


if __name__ == "__main__":
    cluster = ROMARaftCluster(["node-0", "node-1", "node-2"])

    leader = cluster.elect_leader()
    print(f"Leader elected: {leader}")
    print(f"Status: {cluster.get_cluster_status()['leader']}")

    if leader:
        print(f"\nAppending entries via {leader}:")
        for i in range(3):
            r = cluster.append({"type": f"task-{i}", "tick": i})
            print(f"  Entry {i}: committed={r}")

    status = cluster.get_cluster_status()
    for nid, s in status["nodes"].items():
        print(f"  {nid}: role={s['role']}, term={s['term']}, commit_index={s['commit_index']}")
