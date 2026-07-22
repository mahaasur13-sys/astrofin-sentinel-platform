# Changelog — atom-federation-os

## v9.10 — Semantic Consistency Lock Layer
**Date:** 2026-04-13
**Status:** STABLE — freeze point

### Added
- `federation/semantic/v910.py` — Canonical Event Model
  - `EventType`: GOSSIP / CONSENSUS / PROOF / REPLAY / TRUST
  - `HashMode`: CAUSAL / CONSENSUS
  - `EventStore`: in-memory event emission, query, resolution
  - `SemanticProjection`: per-entity canonical event + typed buckets
  - `SemanticBinder`: protocol → canonical layer binding helpers
  - `DriftDetector`: cross-layer invariant violation scanner
  - `DriftKind`: HASH_MISMATCH / GOSSIP_CONSENSUS / PROOF_CONSENSUS / TRUST_REPLAY / IDENTITY_COLLISION
  - `DriftReport`: structured drift description with involved event IDs

### Invariants
- **Semantic Identity Contract:** `semantic_id = (type, entity_hash, hash_mode)`
- Cross-layer identity consistency via `Event.semantic_id()`
- Self-integrity verification via `Event.verify_integrity()`
- Causal ancestry traversal via `Event.causal_ancestry()`

### Guarantees
- Cross-layer identity consistency
- Detectable semantic drift (cross-reference checks)
- Deterministic projection across layers (CONSENSUS prioritized as canonical)
- No duplicate event_ids within a single store

### Tests
- `federation/semantic/test_v910.py`: **24 passed**
- Full suite: **42 passed** (excluding sbs/ which has external atomos_pkg dependency)

### Architecture
- Layer v7.x: control
- Layer v8.x: observability + safety
- Layer v9.x: federation + trust + proof
- Layer v9.10: **semantic lock** (canonical event model + drift detection)

### System Type
Semantic Distributed State Machine

---

## v9.9 — Integration Layer (Stub)
**Date:** 2026-04-12
- `federation/semantic/` directory created
- Placeholder for canonical event model

---

## v9.8 — Proof & Trust Layer
**Date:** 2026-04-10
- PROOF and TRUST event types
- Signed envelope layer
- Inbound security gate

---

## v9.0 — Federation Core
**Date:** 2026-04-08
- GOSSIP / CONSENSUS event model
- Node registry
- Delta gossip propagation
