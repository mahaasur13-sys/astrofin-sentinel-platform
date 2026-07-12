# Contributing to AstroFin Sentinel V5

> **Audience:** Every engineer who touches this repo, including future-you.
> **TL;DR:** Read the [Code of Conduct](#1-code-of-conduct), follow the [7-category PR checklist](#3-pr-review-checklist), and use the [agent template](#6-adding-a-new-agent-step-by-step).

---

## 1. Code of Conduct

We follow a **professional, evidence-driven** engineering culture, in the spirit of BlackRock's engineering values:

- **Disagree, then commit.** Argue your position with data; once a decision is made, align behind it.
- **Document your trade-offs.** Every "I chose X over Y" decision is an ADR-style note in your PR description.
- **No silent failures.** If you swallow an exception, log it with `logger.warning(...)` and surface it via a metric.
- **Leave the camp cleaner than you found it.** Every PR that touches `agents/_impl/` should also update `docs/ARCHITECTURE.md` or `docs/STATUS.md` if the contract changed.

Unacceptable behavior:
- Harassment, discrimination, personal attacks
- Bypassing the linter (`# noqa` without justification)
- Skipping tests to "make CI green"
- Hard-coding secrets, even temporarily
- Pushing directly to `master`

---

## 2. Quick start

```bash
git clone <repo>
cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt
pre-commit install
pytest -q   # must end with 0 failures
```

Before opening a PR, run:

```bash
python scripts/validate_agent.py --changed-only
```

This is the same linter CI runs. If it fails locally, CI will fail remotely.

---

## 3. PR Review Checklist (7 categories)

Every PR must be reviewed through these 7 lenses. The author should self-check before requesting review.

### 3.1 Architectural conformance

- [ ] New agents are placed under `agents/_impl/` (not in `agents/` root — those are archived).
- [ ] New agents inherit from `BaseAgent[AgentResponse]`.
- [ ] New agents appear in `AGENT_AGENTS` in `agents/gitagent_registry.py`.
- [ ] Cross-domain calls go through the Data Room (no direct API hits).
- [ ] No new top-level package has been added without an ADR entry in `docs/ARCHITECTURE.md`.

### 3.2 Data Room compliance

- [ ] Every external data source the PR touches is registered in `data_room/inventory/sources_inventory.json`.
- [ ] If the PR introduces a new conflict-resolution rule, `conflict_journal.json` documents it.
- [ ] If the PR makes a source optional, `missing_context.json` lists the gap.
- [ ] No `requests.get("https://api.coingecko.com/...")` outside `data_room/`.

### 3.3 Security

- [ ] No secrets in code, comments, or test fixtures.
- [ ] All public HTTP endpoints go through `@require_auth` (see `core/auth.py`).
- [ ] No `eval`, `exec`, `pickle.loads` on untrusted input.
- [ ] SQL is parameterized (`?` placeholders), never f-stringed.
- [ ] `bandit` reports no new high-severity issues.

### 3.4 Testing

- [ ] New code is covered by tests. **Coverage ≥ 85%** for the touched module.
- [ ] Edge cases listed in `tests/_template_agent_test.py` are mirrored.
- [ ] At least one **graceful-degradation** test for any agent that uses `@require_ephemeris`.
- [ ] Tests are deterministic — no `sleep`, no `random` without a seeded `RNG`.
- [ ] `pytest -q` passes locally.

### 3.5 Metrics & observability

- [ ] New agents emit at least `agent_runs_total` and `agent_latency_seconds`.
- [ ] New error paths emit `agent_errors_total{reason="..."}`.
- [ ] Decision writes emit `audit_write_seconds`.
- [ ] All metrics are declared in `meta_rl/metrics.py` (the single source of truth).

### 3.6 Documentation

- [ ] Public functions have docstrings (Google style).
- [ ] New env vars are documented in `.env.example`.
- [ ] New CLI commands are documented in the relevant `docs/*.md`.
- [ ] `docs/STATUS.md` is updated if the PR moves a component from "In Progress" → "Ready".

### 3.7 Performance

- [ ] No new O(n²) loops over agent responses.
- [ ] No new sync I/O in async paths (use `httpx.AsyncClient`, `aiohttp`, etc.).
- [ ] DB writes are batched where possible.
- [ ] Hot paths are profiled — no PR should regress P99 latency by >10%.

---

## 4. Branch & commit conventions

- **Branch names:** `feat/<short-topic>`, `fix/<short-topic>`, `chore/<short-topic>`, `docs/<short-topic>`.
- **Commit messages:** [Conventional Commits](https://www.conventionalcommits.org/).
  ```
  feat(quant): add rolling sharpe to QuantAgent.run
  fix(data-room): handle CoinGecko 429 with exponential backoff
  docs(arch): document the Data Room quality gates
  ```
- **PR titles:** match the commit message of the squash-merge.

---

## 5. CI gates — what CI will and won't do

CI will **block** the merge if:
- `pytest -q` fails.
- Coverage drops below 85%.
- `ruff` finds a fixable lint.
- `bandit` finds a high-severity issue.
- `scripts/validate_agent.py` reports any `FAIL` for a changed file.

CI will **warn** (not block) if:
- Touching `agents/_impl/` without touching `docs/`.
- A new agent is added but `AGENT_AGENTS` is unchanged.
- Coverage dropped by ≤1% but stayed ≥85%.

---

## 6. Adding a new agent — step-by-step

> Use the template: `agents/_impl/_template_agent.py` and `tests/_template_agent_test.py`.

1. **Copy the template**
   ```bash
   cp agents/_impl/_template_agent.py agents/_impl/my_new_agent.py
   cp tests/_template_agent_test.py tests/test_my_new_agent.py
   ```
2. **Rename** `TemplateAgent` → `MyNewAgent` everywhere (the template has `# TODO` markers).
3. **Implement** `async def analyze(self, state)` and replace the body.
4. **Decorate** with `@require_ephemeris` if you need planetary positions.
5. **Return a full `AgentResponse`** — never return early, never swallow exceptions.
6. **Register** in `agents/gitagent_registry.py:AGENT_AGENTS`:
   ```python
   "MyNewAgent": {
       "name": "MyNewAgent",
       "domain": "quant",  # or whichever domain fits
       "weight": 0.0,      # tune in backtest
       "karl": True,
       "ttc": True,
       "selfq": True,
       "path": "agents._impl.my_new_agent",
       "method": "run_my_new_agent",
   },
   ```
7. **Write the `run_my_new_agent` convenience function**:
   ```python
   async def run_my_new_agent(state: dict) -> AgentResponse:
       return await MyNewAgent().run(state)
   ```
8. **Add tests** mirroring `tests/_template_agent_test.py`:
   - happy path
   - empty state
   - malformed state
   - missing RAG
   - missing ephemeris (graceful degradation)
   - large input
9. **Validate locally**:
   ```bash
   python scripts/validate_agent.py agents/_impl/my_new_agent.py
   pytest -q tests/test_my_new_agent.py
   ```
10. **Update** `docs/STATUS.md` to mark the agent as "Ready".

### Checklist (print and tick)

```
[ ] agents/_impl/my_new_agent.py
[ ]   [ ] inherits BaseAgent[AgentResponse]
[ ]   [ ] calls super().__init__(name, instructions_path, domain, weight)
[ ]   [ ] uses @require_ephemeris if applicable
[ ]   [ ] returns AgentResponse with full metadata
[ ]   [ ] defines run_my_new_agent() convenience function
[ ]   [ ] docstring on every public method
[ ] tests/test_my_new_agent.py
[ ]   [ ] happy path
[ ]   [ ] empty state
[ ]   [ ] malformed state
[ ]   [ ] missing RAG
[ ]   [ ] missing ephemeris (graceful degradation)
[ ]   [ ] large input
[ ] agents/gitagent_registry.py
[ ]   [ ] AGENT_AGENTS entry added
[ ]   [ ] weight in [0, 1]
[ ]   [ ] domain is one of the 6 DDD domains
[ ] docs/STATUS.md
[ ]   [ ] MyNewAgent status updated
[ ] docs/ARCHITECTURE.md
[ ]   [ ] domain table updated if a new domain was created (rare)
[ ] CI
[ ]   [ ] python scripts/validate_agent.py agents/_impl/my_new_agent.py → pass
[ ]   [ ] pytest -q tests/test_my_new_agent.py → pass
[ ]   [ ] pytest --cov agents/_impl/my_new_agent → ≥85%
```

---

## 7. Adding a new HTTP endpoint — checklist

```
[ ] web/app.py or a Blueprint
[ ]   [ ] @require_auth applied (unless public-by-design)
[ ]   [ ] @rate_limit("X/minute") applied
[ ]   [ ] CORS origin allowlist updated
[ ]   [ ] Input validated against a JSON Schema
[ ]   [ ] Emits a Prometheus counter
[ ]   [ ] Error path returns a structured JSON error
[ ] tests/
[ ]   [ ] 200 happy path
[ ]   [ ] 401 unauthorized
[ ]   [ ] 422 validation failure
[ ]   [ ] 429 rate limit
[ ]   [ ] 500 internal error (mocked)
[ ] docs/STATUS.md
[ ]   [ ] endpoint listed as Ready
```

---

## 8. Testing requirements

- **Coverage floor:** 85% line coverage on touched files. PRs that drop global coverage by >1% require an explicit justification in the PR description.
- **Test types:**
  - `tests/test_<module>.py` — happy path + 5 edge cases (mirror `_template_agent_test.py`).
  - `tests/test_observability_<module>.py` — graceful degradation + metrics emission.
  - `tests/test_integration_<feature>.py` — for anything that crosses module boundaries.
- **Required edge cases (the "BlackRock six"):**
  1. Empty / missing input
  2. Malformed input (wrong types, missing fields)
  3. Source unavailable (network down, 5xx, 4xx)
  4. Concurrent execution (race conditions, deadlocks)
  5. Resource exhaustion (OOM, disk full) — at least one test per process
  6. Clock skew (timestamps in the past / future)
- **Property-based tests:** Use `hypothesis` for any parsing/validation code.

---

## 9. Templates & examples

- **Agent template:** `agents/_impl/_template_agent.py`
- **Test template:** `tests/_template_agent_test.py`
- **Validator:** `scripts/validate_agent.py`
- **Architectural linter:** `scripts/architecture_linter.py`
- **Real-world example:** `agents/_impl/fundamental_agent.py` (canonical implementation)

---

## 10. Questions?

- Open a GitHub Discussion.
- Ping `#astrofin-dev` on Slack.
- Or just open a draft PR — the CI failure messages are usually the best docs.

> **Note (ERR-01):** "structured JSON error" means the standard envelope from `core.error_schema` — see `docs/api_errors.md`. Use `from core.error_schema import BadRequest, NotFound, …` and let `web.middleware.install_error_handling` format the response.
