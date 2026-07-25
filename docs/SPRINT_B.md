# AstroFin Sentinel V5 — Sprint B: CI Cleanup & Infra Polish

> **Start:** 2026-07-25
> **Status:** 🔴 Planned — pending OAuth token scope fix
> **Depends on:** PAT with `workflow` scope (or SSH key push)

---

## Sprint B Objective

Convert CI from mixed green/red to all-green on `master`.
Clean up pre-existing failures, remove redundant checks, fix architecture linter.
**Zero new features** — infrastructure polish only.

---

## B1: Resolve OAuth Push Blocker ⛔ P0

**Problem:** OAuth token (`gho_*`) lacks `workflow` scope → cannot push `.github/workflows/*`.

**Fix (user action):**
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Find the token used by `gh auth` → Edit → add **`workflow`** scope
3. Or: create Fine-Grained PAT with **`Actions: Read/Write`** + **`Workflows: Read/Write`**
4. Or: switch to SSH (`git remote set-url origin git@github.com:mahaasur13-sys/astrofin-sentinel-platform.git`)

**Once unblocked, push these ready fixes:**
- `data-room` CI: add `pip install pytest pydantic`
- `quality-gate.yml`: fix `uses:` → `run:` YAML error
- Security CI: exclude `.zo_scratch/` from bandit scan

---

## B2: Security CI — Bandit Clean 🟡 P1

**Current:** CI Security workflow fails because Bandit scans `.zo_scratch/submodule-archive-*` → 858 false HIGH findings.

**Fix (already applied locally):**
```yaml
- name: Bandit (blocking)
  run: |
    pip install bandit
    bandit -r agents/ core/ orchestration/ web/ api/ meta_rl/ trading/ knowledge/ backtest/ telegram_bot/ \
      --ini .bandit -ll
```

**Verification:** `bandit` on project dirs → 0 Medium, 0 High, 37 Low (nosec'd).

---

## B3: CI — Remove Flake8 Duplication 🟡 P1

**Current:** Lint job runs both `ruff` and `flake8`. Ruff handles all of Flake8's checks plus more.

**Fix:** Remove `- name: flake8` step from `ci.yml` lint job. Ruff already covers:
- E/W/F (pycodestyle/pyflakes) → `ruff check --select E,W,F`
- F401 (unused imports) → `ruff check --select F401`

---

## B4: CI — Meta-RL Nightly Migration 🟢 P2

**Current:** `test-meta-rl` job in CI has `continue-on-error: true` but still runs on every push.

**Fix:** Move meta_rl tests to a nightly scheduled workflow.
```yaml
name: Nightly Meta-RL
on:
  schedule:
    - cron: '0 6 * * *'  # 06:00 UTC daily
  workflow_dispatch:
```

---

## B5: Architecture Linter — 0 Violations 🟡 P1

**Current:** Arch linter exits code 1 with pre-existing violations.

**Todo:**
1. Run `python scripts/architecture_linter.py` locally
2. Fix all violations or add exempt annotations
3. Verify `--changed` mode works correctly on PRs

---

## B6: Dependabot — Version Pin Review 🟢 P2

**Current:** 0 open PRs. Review pinned versions:
- `pydantic>=2.0,<3.0` — pin upper bound
- `openai>=1.0,<2.0` — pin upper bound
- `fastapi>=0.100,<1.0` — pin upper bound
- `ruff<1.0` — pin upper bound

---

## Sprint B Task List

| ID | Task | Priority | Status |
|----|------|----------|--------|
| B1 | OAuth push unblock | **P0** | 🔴 needs user PAT update |
| B2 | Security CI — exclude archived dirs | **P1** | 🟡 fix ready, blocked by B1 |
| B3 | Remove flake8 from CI lint | **P1** | 🟡 fix ready, blocked by B1 |
| B4 | Meta-RL → nightly schedule | **P2** | 🔴 not started |
| B5 | Architecture linter → 0 violations | **P1** | 🔴 needs investigation |
| B6 | Dependabot version pin review | **P2** | 🔴 not started |

---

## Expected CI State After Sprint B

```
✅ CI (7 jobs) — all green
✅ Security (bandit only) — 0 HIGH, 0 Medium
✅ quality-gate — YAML fixed, runs on PR
❌ quality-gate — still fails on PR (no .github push)
🏃 Nightly Meta-RL — runs on schedule, not every push
```

---

## Blocked By

- **OAuth token `workflow` scope** — user must update PAT or switch to SSH
- **Architecture linter timeout** — needs investigation of why it hangs on full scan
