# Known Issues & Technical Debt

> **Last updated:** 2026-06-05
> **Format:** each issue has an ID, severity, owner, target version, and current mitigation.

---

## Severity legend

- 🔴 **P0** — blocks production, must fix this sprint
- 🟠 **P1** — significant risk, must fix this quarter
- 🟡 **P2** — known debt, fix opportunistically
- ⚪ **P3** — nice-to-have, no SLA

---

## KI-001 — Data Room is a draft, not a runtime contract

- **Severity:** 🟠 P1
- **Component:** `data_room/`
- **Symptom:** Agents still call external APIs directly; the Data Room is a documentation aid, not an enforced boundary.
- **Target:** Q3 2026 — `data_room/blueprint.py` becomes the only path; linter (`scripts/architecture_linter.py`) fails the build on direct `requests.get(...)` outside `data_room/`.
- **Mitigation:** Documented in `docs/ARCHITECTURE.md` §4; manual review in PR.

## KI-002 — Manual registry edits

- **Severity:** 🟡 P2
- **Component:** `agents/gitagent_registry.py:AGENT_AGENTS`
- **Symptom:** Adding a new agent requires hand-editing the dict. Easy to forget.
- **Target:** Q3 2026 — entry points (`pyproject.toml [project.entry-points."agents.v5"]`).
- **Mitigation:** CI linter `scripts/validate_agent.py` checks that the registry contains every file in `agents/_impl/`.

## KI-003 — No Postgres in dev environments

- **Severity:** 🟡 P2
- **Component:** `core/history_db.py`, `db/`
- **Symptom:** Devs run on SQLite; production is meant to be Postgres + TimescaleDB. Drift between dev and prod schemas.
- **Target:** Q4 2026 — Postgres + pgvector cutover.
- **Mitigation:** Alembic migrations (`migrations/`) should run identically against both.

## KI-004 — LangGraph and asyncio.gather both active

- **Severity:** 🟡 P2
- **Component:** `orchestration/sentinel_v5.py`, `langgraph_schema.py`
- **Symptom:** Two orchestrators; behavior divergence risk.
- **Target:** Q4 2026 — event bus; deprecate both.
- **Mitigation:** All new features go through `asyncio.gather` path. `langgraph_schema.py` is opt-in.

## KI-005 — 7 archived root-level agent duplicates

- **Severity:** ⚪ P3
- **Component:** `agents/_archived/`
- **Symptom:** Old duplicates still in the tree; confusing for newcomers.
- **Target:** Q4 2026 — remove `agents/_archived/` entirely, redirect `git log` to canonical files.
- **Mitigation:** `AGENTS.md` flags this; CI linter refuses to import from `agents/_archived/`.

## KI-006 — Plotly Dash dashboard, no React yet

- **Severity:** 🟡 P2
- **Component:** `web/app.py`, `web/callbacks.py`
- **Symptom:** Plotly Dash works but is slow; React rewrite is in flight (`astrofin-meta-rl/`).
- **Target:** Q3 2026 — full React dashboard.
- **Mitigation:** Both work; CI verifies both.

## KI-007 — `core/base_agent.py` and `core/base_agent.py.bak` coexist

- **Status:** ✅ Resolved (2026-06-05)
- **Component:** `core/`
- **Symptom:** Two files; one is a stale backup. Risk of confusion.
- **Resolution:** `core/base_agent.py.bak` was removed on 2026-06-05 during the Pattern A cleanup commit. No `.bak` files remain in the repository (verified via `find /home/workspace -name "*.bak"`).
- **Was target:** Next release.

## KI-008 — `web/wsgi.py.bak` exists

- **Status:** ✅ Resolved (2026-06-05)
- **Component:** `web/`
- **Symptom:** Stale backup file.
- **Resolution:** `web/wsgi.py.bak` was removed on 2026-06-05 during the Pattern A cleanup commit. No `.bak` files remain in the repository.
- **Was target:** Next release.

## KI-009 — No central config file for agent weights

- **Severity:** 🟡 P2
- **Component:** `agents/gitagent_registry.py:AGENT_AGENTS` + `AGENT_AGENTS[...].weight`
- **Symptom:** Weights are baked into code. Backtest updates require code changes.
- **Target:** Q3 2026 — `config/agent_weights.yaml` (hot-reloadable).
- **Mitigation:** Backtest writes a `weights_proposal.json`; humans manually apply.

## KI-010 — `core/belief.py` is monolithic

- **Severity:** ⚪ P3
- **Component:** `core/belief.py`
- **Symptom:** Single file, 18KB. Should be split per concern.
- **Target:** Q4 2026.
- **Mitigation:** None yet.

## KI-011 — No automatic e2e CI run on real agents

- **Severity:** 🟠 P1
- **Component:** `tests/`
- **Symptom:** `test_backtest_real_agents.py` exists but is not in the default CI path (slow + non-deterministic).
- **Target:** Q3 2026 — split into nightly and per-PR tracks.
- **Mitigation:** Manual run via `pytest tests/test_backtest_real_agents.py -q`.

## KI-012 — Secrets in `.env` (not gitignored cleanly)

- **Severity:** 🟠 P1
- **Component:** `.env`, `.env.example`
- **Symptom:** `.env` is in `.gitignore` but `.env.example` is shipped; risk of leaking via accidental copy.
- **Target:** Immediate.
- **Mitigation:** `.env.example` is the only file in git; production uses secrets manager.

## KI-013 — `house_cluster` symlink exists in project root

- **Severity:** ⚪ P3
- **Component:** `home-cluster-iac/` symlink at `/home/workspace/`
- **Symptom:** Confusing for new devs.
- **Target:** Move to separate repo.
- **Mitigation:** Document in `AGENTS.md`.

## KI-014 — graph.json reports 20 "1-file self-imports" that are parser bugs

- **Severity:** ⚪ P3
- **Component:** `graphify-out/graph.json` (snapshot 2026-06-17)
- **Symptom:** The graph report (table 7.2 in `GRAPH_REPORT.md`) lists 20 files as "1-file cycles" with one self-edge per file. The edge in every case is `imports_from <file_node> → <file_node>_datetime` (or `_topology`) at L3–L23. The target node is the same file with a generated suffix; the target's `source_file` is **empty**.
- **Root cause:** AST parser mis-resolves `from datetime import datetime, timedelta` and similar self-named imports. When the imported attribute shares the module's name, the resolver creates a self-edge instead of linking to the stdlib `datetime` node.
- **Files affected (none require code changes):**
  - `AsurDev/acos/storage/schema.py` (L7)
  - `AsurDev/feature_pipeline/{backfill,exporter,window_engine}.py` (L9–L11)
  - `AsurDev/load_test/workload/generator.py` (L7)
  - `AsurDev/ml_engine/dataset/builder.py` (L7)
  - `agents/_impl/technical_agent.py` (L10)
  - `agents/astro_council_agent.py` (L12) — also has a separate `inherits` self-edge: `AstroCouncilAgent → baseagent` (target = `BaseAgent` from `push/core/base_agent.py`; no self-cycle, but target resolution failed)
  - `astrofin-sentinel-v5/agents/_impl/technical_agent.py` (L10)
  - `astrofin-sentinel-v5/agents/astro_council_agent.py` (L12)
  - `astrofin-sentinel-v5/astrology/vedic.py` (L8)
  - `astrofin-sentinel-v5/backtest/engine.py` (L9)
  - `astrofin-sentinel-v5/core/{ephemeris,houses,online_trainer,panchanga}.py` (L5–L10)
  - `astrofin-sentinel-v5/integrations/__init__.py` (L3)
  - `astrofin-sentinel-v5/mas_factory/visualizer.py` (L8) — `_topology` (target has empty source_file)
  - `astrofin-sentinel-v5/meta_rl/calibration.py` (L23)
  - `astrofin-sentinel-v5/muhurtha.py` (L7) — file is **missing from working tree**; appears to be a stale entry; only exists in graph cache.
- **Verification:** 2026-06-23 sweep over `graph.json` (62 196 edges, 38 682 nodes) confirmed zero real `imports_from` self-cycles. All 20 are target-resolution failures where the resolved target node has an empty `source_file` — i.e., the parser created a phantom local node instead of resolving to the stdlib module.
- **Action:** **No code changes** in any of the 20 files. The fix lives in the graphify tool (out of repo). Track in KI-015.
- **Mitigation:** Treat all 20 entries in §7.2 of `GRAPH_REPORT.md` as known-false-positives until graphify resolves stdlib imports correctly.

## KI-015 — Duplicate `agents/` namespace in workspace root vs. submodule

- **Severity:** 🟠 P1
- **Component:** `agents/` (root) vs. `astrofin-sentinel-v5/agents/` (submodule)
- **Symptom:** Both directories expose a top-level `agents` package with overlapping symbols (`astro_council_agent.py`, `technical_agent.py`, `base_agent.py`, etc.). The submodule copy is **not byte-identical** to the root copy (diff confirms it). `astro_council_agent.py` in root imports `from agents._impl.synthesis_agent import AGENT_WEIGHTS, CATEGORY_WEIGHTS` — which resolves differently depending on which `agents/` Python picks up first on `sys.path`.
- **Impact:** When running from `/home/workspace/`, `python -m agents.astro_council_agent` and `cd astrofin-sentinel-v5 && python -m agents.astro_council_agent` can bind to **different** code paths. The submodule copy additionally depends on `core.base_agent` (root-only) and `core.ephemeris_decorator` (submodule-internal re-export) — so a direct `python -m agents.astro_council_agent` from the submodule path may fail with `ImportError: cannot import name 'EPHEMERIS_UNAVAILABLE' from 'core.base_agent'`.
- **Submodule HEAD:** `4de2d62` ("chore: clean up workspace, remove duplicate submodule, archive docs"). Working tree has uncommitted changes (`M AsurDev`, `M Dockerfile`, `M atom-federation-os`, `R core/residual_model.py → astrology/residual_model.py`).
- **Target:** Q3 2026 — promote the root `agents/` package to the canonical source; submodule's `astrofin-sentinel-v5/agents/` either becomes a thin re-export package or is removed entirely; symlink or full move once submodule's `core/` is reorganized.
- **Action plan (deferred until uncommitted submodule work is committed):**
  1. Commit pending submodule changes (`core/residual_model.py` rename, `astrology/models/.gitkeep`, `AsurDev` mods).
  2. Diff `agents/astro_council_agent.py` root vs. submodule and decide which is canonical.
  3. If root is canonical: replace submodule's `astro_council_agent.py` with a re-export: `from agents.astro_council_agent import *  # noqa`.
  4. Update import paths in all submodule files that use `core.base_agent` / `core.ephemeris_decorator` to use root paths.
  5. Add an architecture linter rule that fails CI if a file imports from both `agents.X` (root) and `astrofin-sentinel-v5.agents.X` (submodule).
- **Mitigation:** Until resolved, prefer running from `/home/workspace/` root so the root `agents/` wins on `sys.path`. The submodule's `agents/` should be considered legacy.

## KI-016 — graph.json INFERRED edges are mostly noise (17% signal)

- **Severity:** 🟠 P1
- **Component:** `graphify-out/graph.json` (snapshot 2026-06-17)
- **Symptom:** Of 9 601 INFERRED edges, **only ~17 % are real** (85 / 500 stratified sample). 41 % are parser-bug (`target_symbol` not found in `target_file`), 33 % ambiguous (cross-submodule), 10 % outdated (`_archived/`, deleted submodules).
- **Evidence:** `docs/VALIDATION_REPORT.md`, generated by `graphify-out/validate_inferred.py` (top-500 stratified by `relation × target_kind`).
- **Root cause (parser):** INFERRED edges are emitted on **weak signal** (cross-file name lookup without import statement, partial node-ID match). Score range is hard-coded 0.500–0.800, mean 0.517 — there is no high-confidence band.
- **Impact:** Downstream tooling (Hybrid Memory, dependency mapper, dead-code detector) would consume ~83 % noise if it ingests INFERRED naively.
- **Mitigation (already in place):** `validate_inferred.py` provides a heuristic verdict (`valid | false | outdated | ambiguous`) via `rg` symbol search + path blacklist (`_archived/`, `push/`, `roma-execution-bridge/`).
- **Target:** Q3 2026
  1. Filter INFERRED through `validate_inferred.py::verdict` before any downstream use; only `valid` and human-confirmed `ambiguous` are admitted.
  2. Open upstream bug against the graph builder: tighten the INFERRED emitter (require import statement OR a strict node-ID match; raise the score floor to 0.7 or remove the band).
  3. Re-run the validation after each graph snapshot — gate PR merges on `false + outdated < 25 %`.
- **Mitigation:** Use `graphify-out/validate_inferred.py` and `graphify-out/infer_edges.py` as the only supported ingestion path. The policy is formalized in `docs/adr/ADR-0003-hybrid-memory-policy.md`.

---

## Reconciliation with target architecture

The target architecture (see `docs/ARCHITECTURE.md`) requires:

1. **All** external data to go through the Data Room → **KI-001** blocks this.
2. **All** agents to be in the registry → **KI-002** blocks this mechanically.
3. **One** orchestrator in production → **KI-004** blocks this.

Everything else (observability, security, AMRE, KARL) is already ✅.
