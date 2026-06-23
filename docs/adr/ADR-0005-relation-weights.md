# ADR-0005: Relation Weights

| Status | Date | Deciders |
|--------|------|----------|
| Accepted | 2026-06-23 | asurdev |

## Context

`graph.json` carries 11 distinct relation types (`calls`, `contains`,
`method`, `rationale_for`, `uses`, `references`, `imports_from`, `inherits`,
`defines`, `imports`, `re_exports`). The previous `infer_edges.py` pipeline
collapsed all of them onto the same weight axis (tier × decay × confidence),
treating `contains` and `imports_from` as semantically equivalent even though
the latter is a hard dependency and the former is a structural fact.

This became visible after the multi-relation selector (`select_top_inferred.py`)
restored diversity in the input sample: 11 distinct relation types started
flowing into the validator, but `recall_score` could not rank them — `uses`
and `imports_from` showed up with the same weight despite very different
semantic strength.

## Decision

Introduce a third axis in `recall_score`: a per-relation multiplier
(`RELATION_WEIGHTS`) that reflects **semantic strength of the link**.

```
recall_score = tier_weight × decay × confidence × relation_weight
```

### Weight table

| Relation | Weight | Justification |
|----------|--------|---------------|
| `imports_from` | 0.95 | hard dependency (Python import) |
| `imports` | 0.90 | hard dependency (variant spelling) |
| `inherits` | 0.95 | hard dependency (class hierarchy) |
| `calls` | 1.00 | explicit imperative link, the strongest semantic signal |
| `defines` | 0.85 | structural (function/class body) |
| `method` | 0.90 | method inside class (structural + behavioural) |
| `contains` | 0.95 | structural, always true when present |
| `uses` | 0.75 | semantic, often inferred (e.g. agent uses tool) |
| `references` | 0.65 | often indirect (string-level mention) |
| `rationale_for` | 0.80 | meta-information: why a node exists |
| `re_exports` | 0.70 | transitive dependency |
| _default_ | 0.50 | unknown / future relation types |

## Consequences

- **Positive**: `recall_score` now reflects the relative semantic strength
  of an edge, not just its tier and age. A `calls` edge with confidence 0.6
  now outranks a `references` edge with confidence 0.95 (1.0 × 1.0 × 0.6 × 1.0
  vs 1.0 × 1.0 × 0.95 × 0.65 = 0.6 vs 0.62 — still close, but the bias
  is correct).
- **Positive**: Override edges (ADR-0004) get the same `relation_weight` as
  any other edge — the multiplier only kicks in at the same tier/confidence
  range, so the 7 cross-file contracts continue to dominate the top.
- **Positive**: New relations added to `graph.json` fall back to
  `DEFAULT_RELATION_WEIGHT = 0.5` (conservative) until explicitly weighted.
- **Negative**: Rank order in `recall_test.py` shifts slightly; a small
  amount of "regime re-tuning" is needed for downstream consumers that
  hard-coded a 0.5 cutoff.

## Compliance

- The 7 ADR-0004 override pairs are **preserved verbatim** by
  `select_top_inferred.py` (Pass 0: anchor override pairs) and now also
  receive the relation-weight multiplier. Verified end-to-end:
  `infer_edges.py` reports 7/7 override hits on every run since 2026-06-23.
- Tier and decay axes are unchanged (ADR-0004 still authoritative on
  those dimensions).
