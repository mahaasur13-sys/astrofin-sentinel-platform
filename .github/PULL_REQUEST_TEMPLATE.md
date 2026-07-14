<!--
PR title MUST follow Conventional Commits: <type>(<scope>): <subject>
Types: feat, fix, chore, docs, style, refactor, perf, test, build, ci, revert
Example: feat(karl): add self-improvement budget guard
-->

## Summary
<!-- 1-3 bullet points describing the change. What & why. -->

-

## Test plan
<!-- How you verified the change. Check all that apply. -->

- [ ] Unit tests added/updated (`pytest tests/`)
- [ ] Architecture linter clean (`python3 scripts/architecture_linter.py`)
- [ ] Manual smoke run (`python3 -m orchestration.sentinel_v5 --once`)
- [ ] DORA/budget impact reviewed
- [ ] Docs updated (if user-facing)

## Risk
<!-- Low / Medium / High and why. Default Low for <=100 lines of code. -->

- Risk: **Low | Medium | High**
- Rollback plan: <!-- e.g. `git revert <sha>` -->

## Checklist
- [ ] Linked to issue / ticket
- [ ] No secrets committed
- [ ] No unrelated refactors
- [ ] CI is green on this branch
