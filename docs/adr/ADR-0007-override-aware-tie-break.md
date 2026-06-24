# ADR-0007: Override-aware tie-break in recall ranking

- **Status:** Accepted
- **Date:** 2026-06-24
- **Context of the previous ADR:** ADR-0006 introduced 4 candidate formulas for
  `recall_score` and concluded that `v1_baseline` (`tier_weight * decay * conf *
  rel_weight`) remains the best trade-off, with the caveat that override pairs
  compete with other T1 pairs on the same `recall_score=1.0` plateau.
- **Supersedes:** n/a
- **Related:** ADR-0004 (override contract), ADR-0005 (relation weights),
  ADR-0006 (recall formula A/B).

## Problem

`recall_score=1.0` is achievable for **any** T1 pair with full decay and full
confidence, regardless of whether it was promoted by the override contract.
That means a T1 pair like `alignment/test_bcil.py → alignment/bcil.py` (parser,
no override) ties with the seven override anchors, and the existing tie-break
(`source_path`, `target_path`, …, `source_node_id`, `target_node_id`) decides
who sits in the top of the recall ranking purely by alphabetical path order.

Measured on `inferred_clean.enriched.jsonl` (316 edges, 7 override anchors,
all 7 with `recall_score=1.0`):

```
$ python3 graphify-out/recall_test.py -n 10
rank 1  1.0000 T1 core   valid  ✓  …scheduler/modules/metrics.py → …scheduler/modules/metrics.py   (override)
rank 2  1.0000 T1 core   valid  ✓  AsurDev/lccp_v12.py          → AsurDev/lccp_v12.py              (override)
rank 3  1.0000 T1 submod valid     …data_room/test_data_room.py → data_room/circuit_breaker.py     (no override)
rank 4  1.0000 T1 submod valid     …alignment/test_bcil.py      → …alignment/bcil.py               (no override)
…
rank 10 0.9000 T1 submod valid     …test_validator.py           → …agent_validator.py
```

**Override coverage in top-10: 2/7.** Five of the seven god-node contracts
(ADR-0004) sit below non-override T1 edges with the same `recall_score`. This
violates the intent of ADR-0004: the override contract is supposed to *force*
edges to the top, not merely *allow* them to compete.

The earlier A/B run (ADR-0006) reported "5/7 override in top-10" — this was
correct on the file it measured but masked the fact that `recall_test.py` (the
actual ranking surface) was still using a path-based tie-break that demotes
overrides whenever a T1 plateau exists.

## Decision

**Make `override_applied` the primary tie-break in the recall ranking.**
Whenever two edges tie on `recall_score`, override edges must rank strictly
above non-override edges. Path / node-id order stays as the final, deterministic
tie-break.

### Canonical sort key

```
key(edge) = (-int(edge.override_applied), -edge.recall_score,
             edge.source_path, edge.target_path,
             edge.source_node_id, edge.target_node_id)
```

The `-int(override_applied)` term collapses `False→0, True→-1`, so `True`
sorts first. `-recall_score` keeps the existing A/B formula ordering. Path and
node-id terms are preserved verbatim from `recall_test.py` so non-tied output
is byte-identical to the previous ranking.

### Scope of the change

- **`graphify-out/recall_test.py`** is the surface that produces the recall
  ranking consumed by `graphify-healthcheck.sh` and any human reviewer. Apply
  the new key to **both** sort calls in that file (the filtered list and the
  table render).
- **`graphify-out/infer_edges.py`** does **not** sort the enriched payload
  today (order follows dictionary iteration); we intentionally do not change
  that here to keep this ADR narrow. If downstream consumers later start
  reading `inferred_clean.enriched.jsonl` as a ranking source, the same
  sort key should be added there in a follow-up.

## Rationale

1. **Override is a contract, not a hint.** ADR-0004 elevates 7 cross-file
   pairs to god-node status explicitly. Anything that competes with that
   decision at the same score is, by construction, noise.
2. **Cheap and stable.** A single boolean column already exists on every
   enriched edge. Adding it to the sort key is O(n log n) and preserves
   determinism (path + node-id still tie-break identical-score rows).
3. **No formula change.** ADR-0006 already concluded `v1_baseline` is the
   right `recall_score` formula. Tie-breaking is orthogonal: it does not
   require touching `compute_recall_score`, the tier weights, the decay
   model, or the relation weights.
4. **Auditable.** The healthcheck already prints an `ovr` column. After this
   change, every override edge must appear before any non-override edge at
   the same `recall_score`, which is observable in plain stdout.

## Consequences

Positive:

- Override@10 from `recall_test.py` becomes 7/7 (matches ADR-0004 contract).
- Downstream ranking surfaces (any script that mirrors `recall_test.py`'s
  sort key) become self-consistent with the override contract.
- ADR-0006's "5/7" footnote no longer applies: `recall_score=1.0` plateau
  no longer hides override edges.

Negative / risks:

- If a future override is *mis-specified* (e.g. points at a low-quality
  pair), it will still be promoted to the top. This was already true under
  ADR-0004; this ADR does not introduce the risk, it only ensures the
  ranking honours it.
- We hard-code `override_applied` into the sort key. If the field is ever
  renamed, the sort silently degrades to the path-only key. Mitigation: the
  healthcheck already asserts the field exists; we should keep that check.

## Verification

After the patch:

```
$ python3 graphify-out/recall_test.py -n 10
…
overridden:  7/7
```

and `bash scripts/graphify-healthcheck.sh` continues to pass (the
`override_applied` field is still asserted and the top-7 contain all seven
override pairs).

## Implementation

- `graphify-out/recall_test.py` — both `sort(...)` calls updated to the
  canonical key above.
- No change to `infer_edges.py`, `compute_recall_score`, or the relation
  weights file.