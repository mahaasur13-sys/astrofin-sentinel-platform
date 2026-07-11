# Architecture Decision Records (ADR)

This directory captures significant architectural decisions made on the
`astrofin-sentinel-platform` repository. Each ADR follows the lightweight
template in `docs/adr/ADR-0002-common-contracts.md` (Status / Context /
Decision / Consequences).

## Index

| #    | Title                                          | Status   | Date       | Issue / PR |
|------|------------------------------------------------|----------|------------|------------|
| 0001 | Protocol-based agent abstraction               | Accepted | 2026-06-15 | S1 refactor |
| 0002 | `acos-contracts` shared package                | Accepted | 2026-06-20 | S2 refactor |
| 0003 | Hybrid memory policy (v1)                      | Accepted | 2026-06-22 | —          |
| 0004 | Hybrid memory policy (v2, supersedes 0003)     | Accepted | 2026-06-25 | —          |
| 0005 | Relation weights for hybrid recall             | Accepted | 2026-06-26 | —          |
| 0006 | Recall formula A/B                             | Accepted | 2026-06-28 | —          |
| 0007 | Override-aware tie-break                       | Accepted | 2026-06-30 | —          |
| 0008 | Cross-submodule relations                      | Accepted | 2026-07-02 | —          |
| 0009 | Unified JWT authentication (RS256 + roles)     | Proposed | 2026-07-07 | #81        |

## Authoring a new ADR

1. Copy the most recent ADR as a template.
2. Use the next free 4-digit number (`0010`, `0011`, ...).
3. Filename: `docs/adr/ADR-NNNN-short-slug.md`.
4. Update the index row above.
5. Open a PR. Once merged, change `Status: Proposed` to `Accepted` or
   `Superseded` (with a link to the successor).

## Status lifecycle

- **Proposed** — written, under review.
- **Accepted** — merged into `master`.
- **Superseded by ADR-NNNN** — replaced by a later decision.
- **Deprecated** — kept for context, no longer in force.
