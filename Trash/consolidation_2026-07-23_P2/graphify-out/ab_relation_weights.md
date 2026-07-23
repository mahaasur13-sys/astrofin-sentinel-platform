# A/B Test: Relation Weights (ADR-0005 calibration)

**Date:** 2026-06-23  
**Sample:** inferred_clean.jsonl (500 edges, 11 relations, 7 override anchors)  
**Variants:** 4 (v1_baseline, v2_boost_inherits, v3_penalize_uses, v4_boost_method)  

## Conclusion

**All 4 variants produce identical rankings of override edges (rank 4-10)** and an
identical top-10 composition (100% `calls`). The mean per-relation score differs
only at the 4th decimal place, and only for relations sitting on T3 edges with
confidence ~0.05. **No signal exists in this sample to pick a winner.**

### Why no signal?

1. Override edges all have `tier=T1, conf=1.0, decay=1.0` → their `recall_score = 1.0`
   regardless of relation weight.
2. T1 non-override edges cluster around `conf=0.85-1.0` and `tier_weight=1.0`, so
   they all sit near the top in the same order.
3. Relation weights only move T3 / low-confidence edges (mean 0.002-0.01), which
   occupy positions 11-166 — the long tail.

### What this means

- **v1_baseline is the safe default** (current production). No change recommended.
- The relation-weight table is a **future-proofing layer**: it matters once the
  ingest pulls in edges with lower confidence or more variety in T1.
- To produce a real A/B signal, the next step is either (a) more data so T1
  contains a mix of relations with varying weights, or (b) introduce a T1-level
  override-class that lets us A/B test the *intended* rank position.

## Per-variant metrics

| variant | total | T1 | T2 | T3 | override mean | valid mean |
|---------|-------|----|----|----|---------------|------------|
| v1_baseline | 166 | 28 | 20 | 118 | 1.0000 | 0.8625 |
| v2_boost_inherits | 166 | 28 | 20 | 118 | 1.0000 | 0.8625 |
| v3_penalize_uses | 166 | 28 | 20 | 118 | 1.0000 | 0.8625 |
| v4_boost_method | 166 | 28 | 20 | 118 | 1.0000 | 0.8625 |

## Mean recall_score per relation

| relation | v1_baseline | v2_boost_inherits | v3_penalize_uses | v4_boost_method |
|----------|-------------|-------------------|------------------|------------------|
| calls | 0.6820 | 0.6820 | 0.6820 | 0.6820 |
| contains | 0.0048 | 0.0048 | 0.0048 | 0.0048 |
| defines | 0.8160 | 0.8160 | 0.8160 | 0.8160 |
| imports | 0.3083 | 0.3083 | 0.3083 | 0.3083 |
| imports_from | 0.0048 | 0.0048 | 0.0048 | 0.0048 |
| inherits | 0.0048 | 0.0050 | 0.0048 | 0.0048 |
| method | 0.0045 | 0.0045 | 0.0045 | 0.0050 |
| rationale_for | 0.0040 | 0.0040 | 0.0040 | 0.0040 |
| re_exports | 0.6689 | 0.6689 | 0.6689 | 0.6689 |
| references | 0.0033 | 0.0033 | 0.0033 | 0.0033 |
| uses | 0.0019 | 0.0019 | 0.0013 | 0.0019 |

## Override-edge rank position (over all 166 enriched edges)

| edge | v1 | v2 | v3 | v4 |
|------|----|----|----|----|
| acos_network_amnezia_wg → amnezia_wg | 4 | 4 | 4 | 4 |
| ai_scheduler/modules/metrics → ray_active_workers | 5 | 5 | 5 | 5 |
| astrofin/constraint_compiler → constraint_compiler | 6 | 6 | 6 | 6 |
| astrofin/meta_rl/engine → metarlengine_reproduce | 7 | 7 | 7 | 7 |
| failure_orchestrator/recovery → recovery | 8 | 8 | 8 | 8 |
| job_engine/engine → job_engine_telemetry | 9 | 9 | 9 | 9 |
| lccp_v12/main → lccp_v12/staterebuilder_verify | 10 | 10 | 10 | 10 |

## Files

- `graphify-out/ab_relation_weights.json` — full per-variant metrics (machine-readable)
- `config/relation_weights.json` — the 4 variants, ready for future use
