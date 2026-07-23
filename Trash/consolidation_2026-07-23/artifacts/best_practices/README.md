# Best Practices — Extracted Artifacts

Curated reference implementations distilled from the
`astrofin-sentinel-platform` master codebase. Each artifact below is
either a *canonical pattern* (the single source of truth) or a
*clean exemplar* (the cleanest of several competing implementations).

**Audience:** any new module in the platform, or any consumer repo
(`AsurDev`, `home-cluster-iac`, `roma-execution-bridge`, future
sibling projects), should mirror these patterns rather than invent
its own.

**Selection criteria** (all five must hold):

1. **Single source of truth** — no parallel copies elsewhere.
2. **Has tests** or has a tested sibling (so the pattern is verified).
3. **Solves a recurring cross-cutting concern** (auth, errors, config,
   contracts, governance) — not a one-off feature.
4. **Stable for ≥1 month** — not a recent experiment.
5. **Documented in the in-repo ADR or PR description** — the design
   rationale is recoverable.

---

## Layout

| Directory | Concern | Artifact(s) | Why it is canonical |
|-----------|---------|-------------|---------------------|
| `error_handling/` | Standardised HTTP error envelope | `error_schema.py` + `test_error_handling_wsgi.py` | Sole `AppException` hierarchy; used by both FastAPI and WSGI middleware; `format_error`/`error_response`/`set_correlation_id` are imported platform-wide. |
| `auth/` | Two-pattern auth (API key + RS256 JWT) | `api_key_auth.py`, `jwt_rs256.py`, `test_api_key.py` | Coexists on purpose (ADR-0009); both have dedicated tests; `secrets.compare_digest` (timing-safe) and RS256 with `PyJWKClient` are the platform's two accepted primitives. |
| `contracts/` | Shared DTOs + cross-repo exception base | `data_contracts.py`, `shared_exceptions.py` | `acos-contracts` is the *one* import-linter-validated cross-repo contract layer; raising `ACOSContractsError` from any consumer keeps the boundary clean. |
| `governance/` | Pre-/mid-/post-execution gate | `governance_gate.py`, `governance_kernel.py` | Three-state `Decision.APPROVED|REJECTED|ESCALATED` model is referenced by `roma-execution-bridge` and the planning DAG; kernel scoring drives the platform-level PASS/REVIEW/BLOCK status. |
| `settings/` | Single env-var entrypoint | `centralised_settings.py` | `pydantic-settings` `BaseSettings` with `os.getenv` shim for legacy callers; every new module imports from here. |

---

## How to use this directory

* **Replicating a pattern in a new module** — copy the artifact into
  the target repo, then re-point its imports to that repo's local
  layout. Do **not** add `astrofin-sentinel-platform` as a dependency
  just to import these.
* **Validating consistency** — `import_linter` rules in
  `pyproject.toml` enforce that consumers use `acos-contracts` rather
  than redefining the same types.
* **Updating a canonical pattern** — change the file here *and* the
  live source in a single PR; CI runs the live tests, this directory
  is documentation, not a fork.

---

## What is *not* in this directory

* Generated code, vendored dependencies, `.egg-info`, build artefacts.
* `audit_repo/` — archival snapshot, deliberately removed from the
  index (PR #187).
* `atom-core/`, `unified-platform/`, `atomos_pkg/`, `local-ai-stack/`
  — overlay directories not tracked in master.

---

## Provenance

Phase 3 of the master consolidation, branch
`chore/best-practices-2026-07-12`, executed 2026-07-12.

Source files copied byte-for-byte; this directory contains no
modifications. If a source file moves, update the copy in the same
PR — they are kept in sync intentionally.
