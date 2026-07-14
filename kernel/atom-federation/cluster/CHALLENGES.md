# v6.3 Challenges — Chaos Network Layer

> **v6.2 must be fully operational before starting v6.3.**
> v6.3 without v6.2 = chaos without observability → silent corruption.

---

## What v6.3 adds

- `chaos/` — kernel-level network partition injector
- `nftables` / `iptables` DOCKER-USER chain manipulation
- Asymmetric network cuts, packet corruption, partial node isolation
- Jepsen-style cluster validation suite

---

## What MUST break in v6.3

These are the **intentional failures** we will inject and verify the cluster survives:

### 1. 🔴 Network Partition (split-brain)
```
Node A ↮ Node B  (C still reachable from both)
```
**Expected:** Leadership re-election, F2 quorum recalculated, SBS detects violation.

### 2. 🔴 Asymmetric Partition
```
A → B blocked  (B → A still works)
```
**Expected:** One-way heartbeat timeout, leader confusion, DRL reorder detection.

### 3. 🔴 Packet Corruption
```
Bit-flip injection at iptables level (--tatificate corruption)
```
**Expected:** SBS detects corrupted payload, F2 rejects, Gossip quarantine.

### 4. 🔴 Latency Spike (Jitter Storm)
```
DRL delay_mean: 30ms → 2000ms  (sudden)
```
**Expected:** Health pings timeout, node marked LAGGING → UNREACHABLE.

### 5. 🔴 Node Isolation (C minority partition)
```
C alone, A+B form majority
C continues to think it's leader
```
**Expected:** Two leaders appear → SBS LEADER_UNIQUENESS_VIOLATION → cluster halts or re-converges.

### 6. 🔴 Message Loss Storm
```
DRL loss_rate: 5% → 80%
```
**Expected:** Broadcasts start failing, health loop reports peer UNREACHABLE.

### 7. 🔴 Byzantine Node (malicious actor)
```
Node C sends conflicting Forward results to A and B
```
**Expected:** SBS F2 quorum check fails, SBS BYZANTINE_SIGNAL raised.

### 8. 🔴 Clock Skew
```
Node C clock drift: +5000ms from cluster time
```
**Expected:** SBS TEMPORAL_DRIFT violation, SBS enforce CRITICAL → halt.

---

## What v6.3 must NOT break

- ClusterHealthGraph must remain observable during chaos
- SBS audit log must capture all violations even when cluster is degraded
- Graceful shutdown under partition (SIGTERM)
- Log integrity (no silent log loss)

---

## File structure for v6.3

```
chaos/
├── __init__.py
├── partitioner.py      # nftables DOCKER-USER chain injector
├── scenarios.py        # Named chaos scenarios (partition, corruption, etc.)
├── harness.py          # Test harness: run scenario → collect metrics → assert
├── validator.py        # SBS-violation-aware result validator
└── test_chaos.py      # pytest chaos test suite
```

---

## Success criteria

| Scenario | Cluster survives? | SBS catches violation? |
|---|---|---|
| Network partition | ✓ re-elects leader | ✓ LEADER_UNIQUENESS |
| Asymmetric cut | ✓ detects one-way | ✓ DRL reorder |
| Packet corruption | ✓ quarantines node | ✓ BYZANTINE_SIGNAL |
| Latency spike | ✓ marks LAGGING | ✓ |
| Node isolation | ✓ detects split-brain | ✓ |
| Message loss storm | ✓ marks peers UNREACHABLE | ✓ |
| Byzantine node | ✓ quarantines | ✓ BYZANTINE_SIGNAL |
| Clock skew | ✓ detects drift | ✓ TEMPORAL_DRIFT |
