# ADR-0008: Cross-submodule relation resolution

- **Status:** Proposed
- **Date:** 2026-06-25
- **Context of the previous ADR:** ADR-0007 introduced an override-aware
  tie-break so that the 7 god-node contracts defined in ADR-0004 always
  dominate the recall ranking at equal `recall_score`. That fix made the
  ranking *honour* the override contract but did not make `infer_edges.py`
  *detect* the structural property that the override contract is encoding —
  namely, that some edges cross submodule boundaries while others stay
  inside one. Once that property is explicit in the data, multiple downstream
  decisions (relation weights, sampling, override selection, verification
  depth) can be expressed more cleanly than by overloading the existing
  `override_applied` boolean.
- **Supersedes:** n/a (additive; ADR-0004 / ADR-0007 still hold)
- **Related:** ADR-0004 (override contract), ADR-0005 (relation weights),
  ADR-0006 (recall formula A/B), ADR-0007 (override-aware tie-break).

## Problem

`infer_edges.py` emits enriched edges without distinguishing where their two
endpoints live. In practice we see three regimes:

1. **Intra-submodule.** Both endpoints are inside the same submodule
   (e.g. `alignment/test_bcil.py → alignment/bcil.py`,
   `core/foo.py → core/bar.py`). These are usually concrete references with
   full local context and easy to verify with a static `ast` walk.
2. **Cross-submodule.** Endpoints live in different submodules
   (e.g. `AsurDev/lccp_v12.py → AsurDev/lccp_v12.py`,
   `core/scheduler/modules/metrics.py → core/scheduler/modules/metrics.py`,
   `data_room/test_data_room.py → data_room/circuit_breaker.py`).
   These are the **public-API surfaces** of each submodule: they usually
   expose contracts that other modules depend on and are the natural
   candidates for the ADR-0004 override contract.
3. **Unknown / cross-repo.** One endpoint cannot be resolved to a known
   file inside the repo (third-party import, generated stub, dynamic import).
   Today these flow through the same pipeline as (1) and (2), which is the
   reason `ambiguous` verdicts cluster around `calls` / `imports` edges
   (14 of the 27 `calls` edges in `inferred_clean.enriched.jsonl` are
   tagged `ambiguous` and at least 10 of those are cross-submodule or
   unknown).

Because the regime is implicit, every downstream tool has to rediscover it:

- `recall_test.py` has to special-case `override_applied` to put the 7
  cross-submodule anchors on top (ADR-0007).
- The balanced sampler has to know which relation types are likely to be
  cross-submodule to avoid drawing a sample that is mostly intra-module.
- `graphify-healthcheck.sh` and any future verification script cannot
  cheaply ask "show me edges whose target is the public surface of a
  submodule" without re-parsing file paths by hand.

The fix in ADR-0007 (a boolean sort key) papers over the symptom. The
underlying problem — that `infer_edges` does not annotate edge locality —
remains and will keep producing one-off patches.

## Decision

**Introduce an explicit `locality` classification on every enriched edge,
plus a `submodule` annotation on every node, and use them as first-class
signals downstream.**

### Canonical model

Add two fields to the enriched-edge schema:

```
edge.locality ∈ {"intra", "cross", "external"}   # default: "intra"
edge.submodule_source : str | None              # e.g. "core/scheduler"
edge.submodule_target : str | None
node.submodule        : str | None              # set when a node first appears
```

Where:

- `intra` — both endpoints share the same `submodule`.
- `cross` — endpoints live in different submodules inside the repo. This is
  the structural pre-condition for the ADR-0004 override contract.
- `external` — at least one endpoint cannot be resolved inside the repo
  (third-party, generated, dynamic).

### Submodule definition

Use the existing top-level directory as the submodule:

```
submodule(path) = path.split("/", 1)[0]   # first path segment
```

This matches the conventions already implicit in the override contract
(ADR-0004 anchors all live one level deep) and the audit log convention in
`graphify-out/`. We deliberately do **not** invent a deeper hierarchy now:
when/if we need it, it can be derived from `submodule` + path later without
breaking the schema.

### Where the change lives

- **`graphify-out/infer_edges.py`** — populate `locality`,
  `submodule_source`, `submodule_target` while emitting the enriched edge.
  Reuse the existing path-resolution helper (`resolve_target`) and the
  existing "node registry" pattern that already lives next to the edge
  emitter, so we don't introduce a second source of truth.
- **`graphify-out/recall_test.py`** — once `locality` is present, expose a
  `--breakdown-by locality` view alongside the existing override column.
  Do **not** change the canonical sort key from ADR-0007: `locality` is a
  diagnostic, override stays the contract enforcer.
- **Downstream consumers** (balanced sampler, healthcheck) opt in to
  `locality` gradually; no schema removal.

### Relation to the override contract

`override_applied` (ADR-0004) and `locality == "cross"` are **not** the
same. The correct relationship is:

```
override_applied ⇒ locality == "cross"
```

but the converse does not hold — there are many cross-submodule edges that
are *not* god-node contracts and should not be force-promoted. ADR-0008
makes `cross` a structural property; ADR-0004 keeps `override_applied` as a
manual selection on top of it. This separation is what lets future ADRs
(reasoning about "is this cross-submodule edge a public API?") be
expressed without overloading either field.

## Rationale

1. **Schema, not patches.** Each previous fix (ADR-0006 formula choice,
   ADR-0007 tie-break) patched a downstream symptom. Adding `locality` to
   the enriched schema fixes the data so future decisions have something to
   read.
2. **Cheap and local.** `submodule(path)` is one `split`. The classifier
   is a 3-branch `if`. No new dependencies, no new pipelines, no schema
   migration — just two new optional fields plus a small classifier.
3. **Composable with everything that exists.** ADR-0005 (relation weights)
   can later say "boost cross-submodule `calls` by k"; ADR-0007 keeps
   forcing overrides to the top; ADR-0004 keeps its manual selection. None
   of them need to change.
4. **Auditable.** `graphify-healthcheck.sh` can assert that every
   `override_applied` edge has `locality == "cross"` — turning the override
   contract into a structural invariant instead of a curated list.

## Consequences

Positive:

- `infer_edges.py` becomes self-describing: every edge carries enough
  information for a downstream tool to answer "is this a public-API edge?"
  without re-parsing file paths.
- The "override coverage 7/7" success criterion from ADR-0007 stays
  intact, and we gain a new success criterion:
  `∀ edge.override_applied ⇒ edge.locality == "cross"`.
- Balanced sampling can stratify by `locality` instead of guessing from
  relation type. The 14 ambiguous `calls` / `imports` edges that motivated
  this ADR stop being a surprise: they become the expected population of
  `cross` edges.
- Future ADRs (e.g. "weight public-API edges higher") have a stable
  primitive to build on.

Negative / risks:

- Adding fields to the enriched schema is technically backwards-compatible
  (extra keys), but every consumer that asserts the full schema must be
  updated. We mitigate by keeping the new fields optional and asserting
  them only in the healthcheck, not in `recall_test.py`.
- "Submodule = first path segment" is a heuristic. Deeply nested repos
  with multiple top-level entries per logical module will mis-classify.
  Mitigation: ADR-0008 explicitly defers nested hierarchies; the
  implementation must record `submodule_source` / `submodule_target` as
  raw values so a later ADR can refine the mapping without re-running
  inference.
- If a future change renames `locality` or `submodule_*`, downstream
  filters break silently. Mitigation: the healthcheck asserts the three
  new fields exist, mirroring how `override_applied` is asserted today.

## Verification

After implementation:

```
$ python3 graphify-out/infer_edges.py \
    --in graphify-out/inferred_clean.jsonl \
    --out graphify-out/inferred_clean.enriched.jsonl

$ python3 -c "
import json
edges = [json.loads(l) for l in open('graphify-out/inferred_clean.enriched.jsonl')]
assert all('locality' in e for e in edges)
assert all('submodule_source' in e for e in edges)
assert all(e['override_applied'] is False or e['locality'] == 'cross' for e in edges)
from collections import Counter
print(Counter(e['locality'] for e in edges))
# expected: {'intra': ~120, 'cross': ~46, 'external': ~0}
"
```

Plus the existing checks continue to pass:

```
$ python3 graphify-out/recall_test.py -n 10    # overridden: 7/7
$ bash scripts/graphify-healthcheck.sh         # all green
```

## Implementation outline (not a contract yet)

The exact placement of the classifier inside `infer_edges.py` is the part of
this ADR that needs a small design pass before code lands. Open questions
to resolve in the next session:

1. **Where in the enriched-edge builder do we already have `path_source`
   and `path_target` in scope?** (Almost certainly right after the
   existing `resolve_target` call, but worth confirming.)
2. **Do we want a node-level `submodule` registry, or is per-edge enough
   for now?** (Per-edge is simpler; node-level unlocks graph algorithms
   like "edges per submodule".)
3. **Should `external` edges still get a `submodule_target` of `None`, or
   a sentinel like `<external>`?** (`None` is honest; the sentinel is
   easier to group by.)
4. **Where do the 14 currently-ambiguous `calls` / `imports` edges end up
   under the new scheme?** If most become `cross`, this ADR also makes the
   long-standing "verdicts look noisy" complaint a one-shot, not a
   recurring fight.

Once these are answered, the implementation is ~40 lines in
`infer_edges.py` plus the healthcheck assertion, and a follow-up ADR can
decide what to *do* with the new field (sampling weights, recall formula
tweak, etc.).

## Next steps

- Land this ADR as **Proposed** (this document).
- Schedule a short follow-up session to answer the four open questions
  above, ideally by reading `infer_edges.py` end-to-end and tracing one
  `intra`, one `cross`, and one `external` edge through the existing code.
- Promote ADR-0008 to **Accepted** once the implementation outline is
  concrete enough to land in one PR.
- After acceptance, file a follow-up ADR (likely ADR-0009) that decides
  *what to do with* the new field — likely a sampling/weighting tweak
  rather than another ranking change.