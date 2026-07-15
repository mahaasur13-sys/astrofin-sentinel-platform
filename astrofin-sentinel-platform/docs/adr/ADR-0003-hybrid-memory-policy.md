# ADR-0003: Hybrid Memory — Decay Policy and Ingestion Contract

- **Status:** Superseded
- **Superseded by:** [ADR-0004](./ADR-0004-hybrid-memory-policy.md) — adds tier policy by confidence, half-life by archive category, decay floor, and manual override mechanism.
- **Date:** 2026-06-23
- **Deciders:** Architecture (cross-repo) / Hybrid Memory owner
- **Sprint:** S3 (Hybrid Memory scaffolding)
- **Supersedes:** —
- **Related:** `file docs/KNOWN_ISSUES.md` KI-014, KI-015, KI-016; `file graphify-out/GRAPH_REPORT.md` (2026-06-17); `file graphify-out/validate_inferred.py`; `file graphify-out/infer_edges.py`; `file docs/VALIDATION_REPORT.md`; ADR-0002 (acos-contracts)

## Context

The 2026-06-17 graph audit surfaced two related problems that no per-module cleanup can fix:

1. **KI-014 / KI-015 (parser noise):** `file graph.json` contains 20 phantom self-imports, a 45% false-positive rate on INFERRED edges (KI-016), and a hard conflict between the `astrofin-sentinel-v5/agents/` and the platform-root `agents/` packages (same Python name, different content, no marker in the graph).

2. **Hybrid Memory has no policy for ingesting these edges.** Without explicit guidance, the new memory layer risks: (a) re-injecting the 41% parser-false edges as if they were real relations; (b) treating the 33% "ambiguous" edges as fully trusted facts; (c) ignoring time — edges from a stale snapshot will look identical to fresh ones, even when the underlying code has moved on.

## Decision

We adopt a **3-tier evidence model** and a **time-decay ranking policy** for all edges ingested from `file graph.json`. The policy is data, not code — shipped as a single JSON file `file config/memory_policy.json` (loaded by `file graphify-out/infer_edges.py` at export time, and again by the Hybrid Memory recall path).

### 3-tier evidence model

Each edge gets one tier based on its validation verdict in `file VALIDATION_REPORT.md`:

| Tier | Verdict | Trust | Recall weight | Why |
| --- | --- | --- | --- | --- |
| **T1 — verified** | `valid` | 1.00 | 1.0 | Symbol exists at the cited location |
| **T2 — human-review** | `ambiguous` | 0.60 | 0.7 | Symbol exists but cross-submodule / structurally unclear |
| **T3 — discarded** | `false` / `outdated` | 0.00 | 0.0 | Parser bug or stale reference — never ingested |

The tier is **computed once** at ingestion, then re-evaluated **every 90 days** by re-running `file validate_inferred.py` against the latest `file graph.json`. An edge that was T1 today can drop to T2 or T3 later if the target symbol is renamed, archived, or moved out of an active submodule.

### Time-decay ranking

Recall score is multiplied by an exponential decay factor based on the **edge's** `source_location` **last-modified time** (read from `git log -1 --format=%ct` for that file):

```markdown
recall_score = tier_weight × decay_factor × confidence_score
decay_factor = exp(-Δdays / half_life)
```

Two half-lives, by source category:

- **Active core (**`AstroFinSentinelV5/`**,** `core/`**,** `agents/`**):** half_life = 180 days. Slow churn, references stay relevant longer.
- **Submodules and forks (**`astrofin-sentinel-v5/`**,** `atom-federation-os/`**,** `roma-execution-bridge/`**,** `AsurDev/`**):** half_life = 60 days. Fast-moving; an "ambiguous" edge in `astrofin-sentinel-v5` is much more likely to be stale than the same edge in core.

A reference whose source file has not changed in 1 year decays to `1/8` of its tier weight — still recallable, but loses to a fresh T1 edge by a wide margin. This is what keeps the memory layer from over-fitting to the 2026-06-17 snapshot forever.

### Ingestion contract

Hybrid Memory **must not** import `file graph.json` directly. The single supported path is:

```markdown
graph.json
  └─► validate_inferred.py  (tier assignment)
        └─► inferred_clean.jsonl  (T1+T2 only, 248 of 500 sampled)
              └─► infer_edges.py  (decay factor computed from git mtime)
                    └─► config/memory_policy.json  (final recall policy)
                          └─► Hybrid Memory recall path
```

Three enforced invariants:

1. **No T3 ever crosses into Hybrid Memory.** `file infer_edges.py` filters them out; Hybrid Memory receives only T1+T2.
2. **All recall is policy-driven.** No code in the recall path hard-codes tier weights or half-lives — they read `file config/memory_policy.json` at boot. Changing policy is a config PR, not a code PR.
3. **Decay is sourced from git, not from import time.** This means a fresh re-clone of an old submodule still gets the correct freshness signal. It also means the same edge loaded from a frozen artifact and from a live working tree decays identically.

## Consequences

Positive:

- Parser noise cannot poison Hybrid Memory — T3 is dropped at the export boundary.
- Stale edges naturally lose priority; the recall layer does not need a separate "re-validate" cron job.
- Policy changes are auditable as a single JSON diff.

Negative / costs:

- A `git log` per edge is required to compute the decay factor. For the 248 sampled edges this is \~248 ms total (parallelised); for the full 9 601 INFERRED edges it would be \~10 s, still cheap. A daily re-export of the full set is acceptable.
- Human-review edges (T2) require a periodic batch review. We accept that work; the alternative is dropping them, which loses signal.
- The `astrofin-sentinel-v5` submodule's HEAD is currently detached at `4de2d62` (synchronised with platform-root). If the submodule ever gets a divergent HEAD, the git-mtime decay will produce inconsistent values between platform-root and submodule recall paths. We monitor this in CI.

## Implementation

Already shipped (this PR):

- `file graphify-out/validate_inferred.py` — verdict source
- `file graphify-out/infer_edges.py` — clean JSONL export
- `file graphify-out/inferred_clean.jsonl` — 248 T1+T2 edges
- `file config/memory_policy.json` — tier weights, half-lives, decay formula constants

Next (separate PRs):

- Add a "Hybrid Memory recall" hook that reads `file memory_policy.json` and re-ranks by `tier_weight × decay_factor × confidence_score`.
- Schedule `file validate_inferred.py` weekly via the existing CI cron in `file .github/workflows/ci.yml`.
- Wire the ingestion path into the next `file graph.json` re-export.

## Alternatives considered

- **Drop the full 9 601 INFERRED set, use only EXTRACTED (52 595 edges).** Rejected: 17% of INFERRED is real signal we cannot recover from any other source. EXTRACTED alone misses cross-file symbol references the parser cannot statically resolve.
- **Re-validate edges on every recall (no decay).** Rejected: too slow at scale, and the per-call validation cost dominates recall latency.
- **Single half-life for all sources.** Rejected: submodules have a different churn profile; using one half-life either over-weights stale submodule edges (180 d) or discards fresh core edges (60 d).