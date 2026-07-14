# ADR-0002: Introduction of acos-contracts shared package

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Architecture / Lead (S2 refactor scope)
- **Sprint:** S2 — Cross-repo contract unification
- **Supersedes:** — (no prior ADR for this concern)
- **Related:** `REFACTOR_PROMPT.md` §3.3, `graphify-out/GRAPH_REPORT.md`, ADR-0001 (Protocol-based agent abstraction, S1)

---

## Context

Architectural audit of `astrofin-sentinel-platform` (`graphify-out/GRAPH_REPORT.md`,
2026-06-17) processed a graph of **38 682 nodes / 62 196 edges** and surfaced
two structural problems that no per-module cleanup could fix:

### God Nodes (top-10 by degree)

The following symbols were imported by 134+ files each, producing
implementation-coupled call-sites that made any change to a God Node ripple
across the whole platform:

| # | Symbol | Degree (in) | Owner module |
|---|---|---:|---|
| 1 | `AgentResponse` | 348 | `agents/base_agent.py` |
| 2 | `SignalDirection` | 321 | `agents/base_agent.py` |
| 3 | `BaseAgent` | 254 | `agents/base_agent.py` |
| 4 | `EphemerisUnavailableError` | 210 | `core/ephemeris.py` |
| 5 | `RiskEngineV2` | 151 | `risk/risk_v2.py` |
| 6 | `DeterministicClock` | 134 | `core/deterministic.py` |
| 7 | `BaseAgentProtocol` (S1 abstraction) | — | `common/interfaces.py` |
| 8 | `RiskEngineProtocol` | — | `common/interfaces.py` |
| 9 | `StrategyEvaluatorProtocol` | — | `common/interfaces.py` |
| 10 | `MarketStateProtocol` | — | `common/interfaces.py` |

S1 introduced `typing.Protocol` definitions for the first six, but the
**protocols themselves** were duplicated across `astrofin-sentinel-platform`
and `AsurDev` submodules — exactly the kind of drift that defeats the
purpose of an abstraction layer.

### Surprising Connections (5 cross-repo edges)

Graphify's INFERRED edges revealed direct cross-repository coupling
between the three independent codebases:

1. `AsurDev` → `home-cluster-iac` (`WindowEngine`) — stateful window logic
   imported across infra boundary.
2. `AsurDev` → `roma-execution-bridge` (`StateStore`) — durable storage
   interface imported across infra boundary.
3. `AsurDev` ↔ `astrofin-sentinel-platform` (`EventType`, `Decision`,
   `ExecutionResult`) — event/decision DTOs declared in two places, with
   no source of truth.
4. `astrofin-sentinel-platform` → `roma-execution-bridge` (`TraceContract`)
   — trace persistence contract duplicated.
5. `astrofin-sentinel-platform` → `AsurDev` (`StorageBackendContract`,
   `TraceRecorderContract`) — same drift in the opposite direction.

### Operational evidence

- `pytest` collections were polluted: each project carried its own copy of
  the contracts, and tests for one would silently use the other's DTOs.
- A field added to `EventType` in one repo would not appear in the other
  until the second import path was hit at runtime — a classic "works on
  my machine" failure mode.
- Release coordination required a 3-repo lockstep bump, which S1 audit
  repeatedly flagged as a deployment risk.

## Decision

We will create a **standalone Python package** `acos-contracts` that
becomes the **single source of truth** for all cross-repo contracts:

### Location & packaging

- Path: `/home/workspace/acos-contracts/`
- Distribution: `acos_contracts` Python package, version **v0.1.0**,
  declared in `pyproject.toml` (PEP 621).
- Installation: `pip install -e /home/workspace/acos-contracts/` (editable)
  in every consuming project. No PyPI publish for v0.x; consumption is
  internal to the `astrofin-sentinel-platform` workspace.
- Versioning: **SemVer** (`MAJOR.MINOR.PATCH`) — answered Q5 in
  `REFACTOR_PROMPT.md` §9. A MAJOR bump requires a written migration note
  in the consuming repo's `CHANGELOG.md`.

### Contents (v0.1.0)

The package exposes ten modules, each with a single responsibility:

| Module | Public surface | Purpose |
|---|---|---|
| `acos_contracts.interfaces` | `AgentResponseProtocol`, `SignalDirectionProtocol`, `BaseAgentProtocol` | Structural types for agent layer (replaces top-3 God Nodes) |
| `acos_contracts.contracts` | `TraceRecorderContract`, `StorageBackendContract`, validation helpers | Recorder/storage protocol |
| `acos_contracts.deterministic` | `DeterministicClock`, `DeterministicUUIDFactory` | Time + UUID infrastructure |
| `acos_contracts.deterministic_factory` | factory functions | Construction helpers for the above |
| `acos_contracts.events` | `EventType`, `Decision`, `ExecutionResult` | DTOs that broke the AsurDev ↔ astrofin edge |
| `acos_contracts.feature_pipeline` | `WindowEngineProtocol` | Stateful window contract (replaces AsurDev→home-cluster-iac edge) |
| `acos_contracts.state` | `StateStoreProtocol` | Durable storage contract (replaces AsurDev→roma-execution-bridge edge) |
| `acos_contracts.trading` | `RiskEngineProtocol`, `StrategyEvaluatorProtocol`, `MarketStateProtocol` | Trading-domain protocols (top-5/8/9/10) |
| `acos_contracts.errors` | `AcosContractError` + hierarchy | Common error vocabulary |
| `acos_contracts` (root) | re-exports | Convenience namespace for the most-used symbols |

### Implementation rules

- All structural types use `typing.Protocol` with `@runtime_checkable`
  so `isinstance(x, AgentResponseProtocol)` works in tests.
- All concrete DTOs are `frozen=True` `@dataclass`es — immutable, hashable,
  no default-mutable traps.
- **No I/O, no logging, no time imports** in `acos_contracts` itself.
  The package is pure data + signatures; behaviour lives in implementations.
- All modules are `from __future__ import annotations` to keep the package
  import-cheap and side-effect free.

### Migration policy

For S2 the rule is **identity-true re-export**: consumers that depended
on a symbol via `common.events.EventType` (or any other old path) now
get the same class object via the new path, so `is` checks across the
old and new import paths still pass. This keeps every `import acos...`
caller working without a per-callsite edit, and isolates future
dependency changes to one file per project.

## Alternatives Considered

### A1. Keep duplicates in each repository (status quo)

**Rejected.** This is the state Graphify flagged. Drift between the
three copies of `EventType` had already produced at least one
production-internal test flake during S1 (recorded in `AUDIT_2026-06-17.md`).
At 6+ months of forward development the divergence was projected to
grow exponentially — every new field needed three coordinated edits and
three independent release pipelines. Not sustainable.

### A2. Monorepo with shared `common/` source tree

**Rejected.** A single monorepo would solve duplication but introduces
**deployment tight-coupling**: every infra service (`home-cluster-iac`,
`roma-execution-bridge`) would need to build, version, and release
alongside `astrofin-sentinel-platform`. Those services have independent
release cadences and on-call rotations, and `home-cluster-iac` in
particular is provisioned through GitOps with its own ArgoCD app. A
monorepo would either force those infra repos into the same Argo
application (operational blast radius) or keep them separate with
synchronised submodules (defeats the simplification). The cost of
monorepo adoption exceeded the cost of a tiny shared package.

### A3. Pick one existing repo as the canonical source

**Rejected.** Choosing, say, `astrofin-sentinel-platform` as the canon
would create an **implicit hierarchy** where a contract change in
`AsurDev` (e.g. adding a `WindowEngine` parameter) required a PR
against a different repo, then a coordinated release. It also leaves
the question of who owns the contract when both sides evolve. A
dedicated package makes the ownership explicit and the boundary stable.

### A4. Use an existing public package (e.g. `pydantic`, `attrs`)

**Rejected as a baseline, but `dataclass(frozen=True)` from the stdlib
is used.** A public runtime-validation package would add a runtime
dependency to every service for a feature (`@runtime_checkable Protocol`
+ frozen dataclasses) that the stdlib already provides. Pydantic-style
runtime coercion was explicitly out of scope — the contracts module
stays pure.

## Consequences

### Positive

- **Single source of truth.** All 10 God Nodes and 5 Surprising
  Connections resolve to one package, one version, one set of tests.
- **Independent releases.** Each consuming project can bump
  `acos-contracts` on its own schedule, pinned in its own lockfile.
- **Easier testing.** Protocol-based contracts with `@runtime_checkable`
  let us write `isinstance`-based smoke tests in the consuming repos
  without mocking the whole implementation.
- **Stable DI surface.** Constructor signatures of agents, risk
  engines, and execution gateways now reference a Protocol that lives
  in a package they already import — no more `TYPE_CHECKING` shims.

### Negative

- **Additional dependency.** Every repo now has one more
  `pyproject.toml` entry and one more `pip install -e` step in its
  bootstrap. Mitigated by documenting the install command in
  each repo's `README.md`.
- **Backward-compatibility burden.** Once v1.0 ships, breaking changes
  require a deprecation cycle (MINOR bump + warning, MAJOR bump after
  one release). For v0.x we are still pre-1.0, so the cycle is
  "release notes + bump" — accepted because all consumers are
  internal.
- **Edits ripple through the lockfile.** A field added to `EventType`
  forces a `pip install -e acos-contracts` in every project. Mitigated
  by editable installs: a `git pull` in the contracts repo is enough
  for dev, and a tag-driven bump is enough for release.

### Neutral

- A new contract change requires a new package version. We treat this
  as the cost of doing business, not a net loss — the version bump is
  what *makes* the change traceable in `git log`.
- The contracts package must be import-cheap. CI now runs an
  import-time smoke test (`python -c "import acos_contracts"`) in
  addition to the per-protocol unit tests.

## Implementation Notes (S2 evidence)

- **Created:** `/home/workspace/acos-contracts/` (10 modules, `pyproject.toml`,
  `README.md`, `acos_contracts.egg-info/` from the editable install).
- **Migrated repositories:**
  | Repo | Commit | Notes |
  |---|---|---|
  | `astrofin-sentinel-platform` (`/home/workspace/`) | `a664f74` | `common.*` → `acos_contracts.*`; `common/` left as re-export shims |
  | `AsurDev` (`/home/workspace/AsurDev/`) | `7f50ea6` | Local `EventType` / `Decision` / `ExecutionResult` replaced by re-exports; richer implementations kept locally |
  | `acos-contracts` | `860ab03` | v0.1.0 baseline |
- **Not migrated (no cross-imports):** `home-cluster-iac`, `roma-execution-bridge`.
  They are pure consumers of contracts but never imported the old `common.*`
  paths, so no edit was required.

## References

- `graphify-out/GRAPH_REPORT.md` — source of God Node and Surprising
  Connection metrics (2026-06-17).
- `docs/refactor/REFACTOR_PROMPT.md` §3.3, §9 (Q5 SemVer decision).
- `AUDIT_2026-06-17.md` — operational evidence of duplicate-DTO drift.
- S1 ADR for the Protocol-based agent abstraction (this ADR
  supersedes its in-tree protocol definitions).
- S2 commits: `acos-contracts@860ab03`, `astrofin-sentinel-platform@a664f74`,
  `AsurDev@7f50ea6`.
