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

---

## Reconciliation with target architecture

The target architecture (see `docs/ARCHITECTURE.md`) requires:

1. **All** external data to go through the Data Room → **KI-001** blocks this.
2. **All** agents to be in the registry → **KI-002** blocks this mechanically.
3. **One** orchestrator in production → **KI-004** blocks this.

Everything else (observability, security, AMRE, KARL) is already ✅.
