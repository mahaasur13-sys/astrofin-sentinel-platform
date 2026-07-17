# Governance

Two layers, intentionally separated:

| Layer | Artifact | When it runs | Output |
|-------|----------|--------------|--------|
| **Static kernel** | `governance_kernel.py` | Pre-deploy / pre-merge | `STATUS ∈ {PASS, REVIEW, BLOCK}` + risk score 0..1 |
| **Execution gate** | `governance_gate.py` | Per DAG run, before/after each node | `Decision ∈ {APPROVED, REJECTED, ESCALATED}` + audit trail |

## Why two layers

* Kernel answers "is the *system* safe to deploy?" (topology, layer
  purity, determinism).
* Gate answers "is *this* execution safe to run *right now*?" (risk
  score, constraint breaches, kill switch).

Mixing them leads to either false positives (gate refusing a build
because a node's runtime risk > 0.5) or false negatives (kernel
approving a deploy whose runtime has no kill switch).

## Decision semantics

* `APPROVED` — proceed.
* `ESCALATED` — `risk_score ∈ (0.25, 0.5]`, halt and require human
  review.
* `REJECTED` — `risk_score > 0.5` or hard constraint breach, refuse
  outright.
