# ADR-0004: Hybrid Memory — Tiering, Decay, and Manual Overrides

- **Status:** Accepted
- **Date:** 2026-06-23
- **Deciders:** Architecture (cross-repo) / Hybrid Memory owner
- **Supersedes:** [`ADR-0003`](./ADR-0003-hybrid-memory-policy.md)
- **Related:** `docs/KNOWN_ISSUES.md` KI-014, KI-015, KI-016; `config/memory_overrides.json`; `graphify-out/GRAPH_REPORT.md`; `graphify-out/VALIDATION_REPORT.md`

## Context

`graphify-out/validate_inferred.py` and `graphify-out/infer_edges.py` form the ingestion path for inferred relationships extracted from the repository graph. The validator must classify each edge with a human-meaningful verdict (`valid`, `false`, `moved`, `outdated`, `ambiguous`) and the ingestion layer must convert that verdict into a storage tier.

The graph report contains two distinct classes of noise:

1. Parser artifacts, including phantom self-imports and false INFERRED edges whose target symbol does not exist in the target file.
2. Legitimate but low-confidence or stale edges that should still be retained for auditability, but should not influence recall strongly.

## Decision

We use three storage tiers and one manual escape hatch:

- **T1** — strong, current, validated edges.
- **T2** — useful but weaker or ambiguous edges.
- **T3** — archival edges that remain queryable but carry very low influence.

### Tier assignment rules

- `valid` + `confidence >= 0.7` → `T1`
- `valid` + `confidence < 0.7` → `T2`
- `ambiguous` → `T2`
- `false` / `moved` / `outdated` → `T3`

### Half-life rules

- `core`: **180 days**
- `submodule`: **60 days**
- `archived`: **14 days**
- `trash`: **14 days**

### Decay function

Use a floor so old but important edges never collapse to zero influence:

```python
decay_factor = max(0.05, math.exp(-delta_days / half_life))
```

### Manual overrides

Manual overrides live in `config/memory_overrides.json` and are keyed by `(source_node_id, target_node_id)`.

Supported fields:

- `tier`
- `half_life`
- `reason`
- `author`
- `date`

Overrides are authoritative and bypass automatic tiering, but must be audited.

## Consequences

- `validate_inferred.py` remains the source of truth for verdicts.
- `infer_edges.py` maps verdict + confidence to tier and emits a clean export for downstream memory ingestion.
- Hybrid Memory can safely ingest graph-derived edges without amplifying parser noise.
- Archived code remains queryable, but loses influence quickly.

## Implementation notes

1. Add `archived` as an explicit category in the validator / exporter.
2. Ensure the exporter records both `verdict` and `tier`.
3. Apply manual overrides before default tier assignment.
4. Re-generate `inferred_clean.jsonl` after policy changes.
5. Report final counts for `T1`, `T2`, and `T3`.
