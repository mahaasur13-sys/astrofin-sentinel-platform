# Session Report — 2026-06-23: Hybrid Memory Calibration

## 1. Goal

Restore relation diversity in the INFERRED edge selection, embed
`RELATION_WEIGHTS` in the `recall_score` formula, and empirically validate
the choice before committing it as ADR-0005.

## 2. Starting point

| Artifact | State before session |
| --- | --- |
|  | 38,682 nodes, 6,074 links, 11 relation types |
|  | 500 edges, **monomorphic** (100% `calls`) |
|  | `recall_score = tier * decay * conf` (no relation axis) |
| Override pairs | 7/7 defined in `file config/memory_overrides.json` |
| ADR | 0004 (override mechanism) only; no 0005 |

## 3. Root cause of the monomorphic sample

`file inferred_clean.jsonl` was not "monomorphic because `file infer_edges.py` only
writes `calls`" — that was a misleading earlier hypothesis. The actual
chain is:

```markdown
graph.json (top-500 by weight × confidence)
        ↓
/tmp/inferred_sample.json (default location read by validate_inferred.py)
        ↓
VALIDATION_REPORT.md (judge() verdict per edge)
        ↓
infer_edges.py → inferred_clean.jsonl (relation copied verbatim from report)
```

The top-500 by `weight` happens to be dominated by `calls` edges (it is
the highest-weight relation in `file graph.json`). `file infer_edges.py` preserves
whatever relation the upstream validator wrote. Hence the monomorphic
output was an artifact of the *selector*, not the inferrer.

## 4. Work performed

### 4.1 New selector — `file select_top_inferred.py`

Built a 3-pass selector over `file graph.json`:

1. **Pass 0** — anchor override pairs (ADR-0004 contract).
2. **Pass 1** — `min_per_relation` floor across all relation buckets.
3. **Pass 2** — fill remaining slots, cross-file preferred.
4. **Pass 3** — top-up from any bucket, ignoring cap.

Result: **500 edges, 11 relation types, 7/7 override pairs, 205 cross-file edges**.

### 4.2 Updated sampler — `file build_balanced_sample.py`

Added `--anchor-pairs` flag that pulls the 7 override pairs out of their
bucket before the cap, then prepends them to the output. Preserves the
ADR-0004 contract even when `--max-per-bucket` would otherwise drop them.

### 4.3 Fixed `file infer_edges.py`

- `run_validator()` now takes a `sample_path` argument and is called
  with the live `/tmp/inferred_sample.json` instead of the stale
  `/tmp/inferred_sample_500.json` default. Without this fix, the
  validator kept reading the old monomorphic sample and overwriting
  the fresh one.
- `parse_report()` now correctly reads 11 different relations (was
  returning 1 before the fix).
- Added `RELATION_WEIGHTS` dict and `DEFAULT_RELATION_WEIGHT = 0.5`.
- New formula: `recall_score = tier_weight * decay * conf * rel_weight`.
- Added `--relation-weights <variant>` CLI flag reading
  `file config/relation_weights.json`.
- `relation_variant` and `relation_weights_path` added to summary.

### 4.4 New healthcheck — `file graphify-out/healthcheck.py`

6 checks (c1–c6) → 8 checks (c1–c8):

- c1: `file graph.json` structure
- c2: `file inferred_clean.jsonl` exists with ≥7 relation types
- c3: enriched file exists with ≥7 relation types + `recall_score`
- c4: 7/7 override pairs survive `file graph.json` → `inferred_clean` → enriched
- c5: `file recall_test.py` runs clean
- c6: `recall_score` in `[0, 1.01]`, tiers in `{T1, T2, T3}`
- **c7 (new)**: T1 average `recall_score > 0.05` (guards against accidentally returning 0.0 for T1)
- **c8 (new)**: no T1 edge with `recall_score ≤ 0`

**Result: 8/8 passed on every run since 2026-06-23.**

### 4.5 A/B testing of 4 formulas

Tested 4 candidates for the `recall_score` formula on the current
`file inferred_clean.jsonl` sample (166 edges, 7 override GT):

| Variant | Formula | GT@7 | Top-7 spread | Diversity |
| --- | --- | --- | --- | --- |
| `v1_baseline` (current) | `tier * decay * conf * rel` | 7/7 | 0.0 | 4 relations in T1 |
| `v2_no_tier` | `rel * decay * conf` | 4/7 | 0.0 | **breaks override** |
| `v3_smooth_tier` | `tier^0.5 * decay * conf * rel` | 7/7 | 0.0 | 4 relations in T1 |
| `v4_relation_primary` | `rel * decay * conf * 0.4 + 0.6 * tier` | 7/7 | 0.0 | 4 relations in T1 |

**Decision: keep** `v1_baseline`**.** v2 breaks the ADR-0004 override contract.
v3 and v4 are mathematically equivalent to v1 on the current sample (all
T1 edges have `confidence = 1.0`, `decay ≈ 1.0`, so any smooth function
collapses to the same value). The diversity we want (4 different scores
1.0 / 0.9 / 0.85 / 0.7 across `calls` / `imports` / `defines` /
`re_exports`) **already comes from** `relation_weight`, not from changing
the formula.

**Future work:** when the sample grows beyond 166 edges or when
confidence becomes non-uniform across T1, the formula choice will matter
and this A/B should be re-run.

### 4.6 A/B testing of 4 weight variants

Tested 4 candidates for the `RELATION_WEIGHTS` table
(`v1_baseline`, `v2_boost_calls`, `v3_demote_refs`, `v4_aggressive_default`).
**All 4 produce identical top-20**: 4 relations, override ranks unchanged.
Same conclusion as the formula test: the current sample is too small and
too confidence-uniform for weight variation to manifest.

## 5. Commits

| SHA | Description |
| --- | --- |
| `8ae5453` | graphify-out: restore relation diversity in INFERRED selection (new selector + sampler fix + validator fix + RELATION_WEIGHTS) |
| `3d7c6cf` | graphify-out: relation-weights config + A/B harness (--relation-weights CLI, ab\_\*.json, ab_relation_weights.md) |
| `f02326f` | graphify-out: empirical v2 calibration of formula+weights (ab_calibration_v2.json, ADR-0005 §Empirical Validation) |
| `be948db` | graphify-out: 8-check healthcheck + ADR-0005 empirical section (c7, c8, expanded validation table) |

All four pushed to `origin/master`.

## 6. Final state

```markdown
$ python3 graphify-out/healthcheck.py
✅ c1, c2, c3, c4, c5, c6, c7, c8
✅ all 8 checks passed

$ grep -c "override_applied.: true" graphify-out/inferred_clean.enriched.jsonl
7

$ python3 graphify-out/infer_edges.py | python3 -c "from collections import Counter; ..."
Total: 166
Tier: T1=28, T2=20, T3=118
T1 distinct scores: 4 (1.0, 0.9, 0.85, 0.7)
T1 distinct relations: 4 (calls, imports, defines, re_exports)
```

## 7. Open questions / Next session

1. **Why is the sample confidence-uniform?** 22/28 T1 edges have
   `confidence = 1.0` and `weight = 1.0`. If the parser produced more
   graded confidence, the A/B would actually show differentiation.
2. **T3 floor (**`0.05`**) is suspicious.** 71% of all edges sit at this
   floor (118/166). Consider whether the floor is masking legitimate
   low-confidence links.
3. `graphify-out/cache/` **is committed** (≈ 2,600 files). Pre-existing
   issue, outside the scope of this session.
4. **Healthcheck c7/c8 thresholds are weak** — they only catch the
   "T1 returns 0" failure mode. A future enhancement: check that
   `recall_score` distribution across T1 spans more than one value
   (currently it spans 4, which is good).