# ATOMFederationOS — SBS v1

> System Boundary Spec — инструмент проверки распределённых систем на корректность.

## 🧠 Что это простыми словами

**Проблема:** Distributed системы (backend с many services) сложно тестировать на реальные сбои — разрыв сети, разделённые узлы (split-brain), несинхронные часы. Большинство багов проявляются только в production.

**Что делает SBS:** Вы описываете правила (инварианты) — например "нельзя иметь двух лидеров одновременно" или "все узлы видят одинаковые данные". SBS проверяет, что ваша система не нарушает эти правила при сбоях.

**Зачем:** Гарантирует, что данные остаются корректными даже при реальных проблемах в сети.

**Где используется:** Distributed databases, consensus systems (Raft, Paxos), microservices с gossip-протоколами, Kubernetes-операторы, blockchain-like systems.

## ✅ Status

| Metric | Value |
|--------|-------|
| **Version** | 0.6.0 |
| **Tests** | 55/55 PASS |
| **Determinism** | ✅ Hash стабилен между запусками |
| **CLI** | `sbs verify` `sbs status` `sbs inspect` |

## 🚀 Установка за 2 минуты

```bash
git clone https://github.com/mahaasur13-sys/atom-federation-os.git
cd atom-federation-os
python3 -m venv venv && source venv/bin/activate
pip install .

# проверка
sbs verify
sbs --version   # должен показать 0.6.0
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  SBS (System Boundary Spec) — GLOBAL INVARIANTS │
│  GlobalInvariantEngine │ FailureClassifier      │
│  SYSTEM_CONTRACT                                │
└───────────┬─────────────────┬──────────────────┘
            ▼                 ▼                   ▼
   CCL Contracts     F2/F3/F8 Kernel     DESC Log
   (local rules)     (execution)         (audit trail)
            ▲                 ▲                   ▲
            └─────────────────┴───────────────────┘
                       DRL (network reality)
```

## Stack Layers

| Layer | Role |
|---|---|
| **DRL** | Distributed Reality Layer — network partition, clock skew, causality |
| **CCL** | Consensus Contract Layer — semantic contracts, stale reads |
| **F2/F3/F8** | Quorum kernel — commit safety, leader uniqueness |
| **DESC** | Distributed Event Sourcing Component — immutable audit trail |
| **SBS** | System Boundary Spec — **global invariant enforcement** |

## SBS v1 Components

| Module | Responsibility |
|---|---|
| `SystemBoundarySpec` | Hard boundary validation gate (split-brain, quorum, uncommitted reads) |
| `GlobalInvariantEngine` | Cross-layer invariant verification (DRL+CCL+F2+DESC) |
| `FailureClassifier` | Jepsen-aligned failure taxonomy (11 categories) |
| `SYSTEM_CONTRACT` | Immutable hard constraints registry |

## Installation

```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest sbs/tests/ -v
```

## Quick Usage

```python
from sbs import SystemBoundarySpec, GlobalInvariantEngine

spec = SystemBoundarySpec(allow_split_brain=False)
engine = GlobalInvariantEngine(spec)

ok = engine.evaluate(
    drl_state={"leader": "node-1", "term": 3, "partitions": 0},
    ccl_state={"leader": "node-1", "term": 3, "stale_reads": 0},
    f2_state={"leader": "node-1", "term": 3, "quorum_ratio": 0.9, "commit_index": 10},
    desc_state={"leader": "node-1", "term": 3, "commit_index": 10},
)
print(ok)  # True
```

## Version History

| Version | Milestone |
|---------|-----------|
| **0.6.0** | CLI, schema validator, regression tests, single-source version |
| **0.5.2** | conftest fix, schema_validator, regression tests, CI pipeline, security hardening |
| **0.5.1** | SBS v1 initial release (GlobalInvariantEngine, SystemBoundarySpec, FailureClassifier, SYSTEM_CONTRACT) |
