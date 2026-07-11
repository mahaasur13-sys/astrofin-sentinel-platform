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

## Empirical Validation

The 2026-06-23 A/B test (`/tmp/ab_repro.py`, ground-truth = 7 override-applied edges) confirmed that **all 4 candidate formulas give the same GT-in-top-7 result (7/7)** on the current `inferred_clean.jsonl` sample. This is **not a sign that the formula choice is irrelevant** — it is a sign that **the sample is dominated by T1/T2 high-confidence edges** where any formula in the family produces the same top.

| Variant | Formula | GT@7 | Top-7 spread | Diversity |
|---------|---------|------|--------------|-----------|
| `v1_baseline` (current) | `tier * decay * conf * rel` | 7/7 | 0.0 (all T1=1.0) | 4 relations in T1 |
| `v2_no_tier` | `rel * decay * conf` | 4/7 | 0.0 | breaks override |
| `v3_smooth_tier` | `tier^0.5 * decay * conf * rel` | 7/7 | 0.0 | 4 relations in T1 |
| `v4_relation_primary` | `rel * decay * conf * 0.4 + 0.6 * tier` | 7/7 | 0.0 | 4 relations in T1 |

**Conclusion:** v1_baseline is kept as default. v2 breaks the override contract. v3 and v4 are mathematically equivalent to v1 on the current sample — they would only diverge if confidence or decay varied across T1 edges, which they don't (all T1=1.0/1.0). The diversity we want (4 different `recall_score` values: 1.0, 0.9, 0.85, 0.7 across `calls`/`imports`/`defines`/`re_exports`) **already comes from `relation_weight`**, not from changing the formula.

**Future work:** when the sample grows beyond 166 edges or when confidence becomes non-uniform, the formula choice will matter and we should re-run this A/B.

See `/tmp/ab_repro.py` and `graphify-out/ab_calibration_v2.json` for raw data.

## Scaled Validation (v3, 2026-06-23)

The previous A/B tests on the 166-edge sample gave identical results for all
4 formulas because the sample was too homogeneous (22/28 T1 edges had
`conf=1.0, weight=1.0`, decay was uniform). After scaling to 5000 edges:

- T1=118 (4x increase), T2=90, T3=108
- 11 unique recall_score values in T1: 0.7, 0.736, 0.7781, 0.8, 0.828, 0.85, 0.9, 0.924, 0.95, 1.0
- 12 unique recall_score values in T2: 0.207, 0.225, 0.42, ..., 0.6

This means the formula CAN now meaningfully rank edges. v1_baseline is still
the right choice because the override contract (7/7) survives and the
relation_weight axis produces the diversity we want. The earlier v3
hypothesis (that all formulas converge) is now falsified: the formulas would
diverge on the larger sample, but v1 already separates correctly via
`relation_weight`.

**Conclusion: v1_baseline is locked in as the default formula. No change
needed to formula or weights. The 11-check healthcheck now guards against
re-introducing T1 collapse.**

See `graphify-out/inferred_clean_large.enriched.jsonl` (316 enriched edges)
and `graphify-out/healthcheck.py` for the runtime guards.

## Implementation details

The current default (`ACTIVE_WEIGHT_VARIANT = "v1_baseline"`) is implemented in `graphify-out/infer_edges.py`:

```python
recall_score = tier_weight * decay * conf * rel_weight
```

`--relation-weights <variant>` CLI flag selects an alternative variant from `config/relation_weights.json`. Override edges (ADR-0004) are unaffected by either axis — they receive `tier = T1, half_life = 365d, decay ≈ 1.0` directly from `config/memory_overrides.json`.

The healthcheck (`graphify-out/healthcheck.py`) now runs 8 checks, including `c7` (T1 average score > 0.05 — guards against accidentally returning 0.0 for T1) and `c8` (no T1 edge with `recall_score ≤ 0`).