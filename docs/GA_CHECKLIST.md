# GA Checklist — AstroFin Sentinel v1.0.0

> **Target date:** 2026-08-25  |  **Owner:** Felix / asurdev

## Pre-GA validation

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | All P0 tasks closed (H-01..H-10) | ⬜ | Sprint G tracking |
| 2 | CI 8/8 green (last 5 consecutive) | ⬜ | GitHub Actions |
| 3 | Bandit 0 HIGH/MEDIUM in our code | ⬜ | `.bandit` + `docs/security/bandit-review-2026-08.md` |
| 4 | WAL-G backup + restore drill passed | ⬜ | `docs/runbooks/WALG_RESTORE_DRILL.md` |
| 5 | Load test baseline recorded | ⬜ | `docs/performance/load-test-staging-2026-08-04.md` |
| 6 | Stress test 100 RPS — breaking point known | ⬜ | `docs/performance/stress-test-TEMPLATE.md` |
| 7 | SLO: 99.0% availability over 7 days staging | ⬜ | `docs/slo-calibration-2026-08-04.md` + Grafana |
| 8 | Release notes published (RELEASE_NOTES.md) | ⬜ | `docs/RELEASE_NOTES_v1.0.0.md` |
| 9 | DEPLOYMENT.md quickstart < 5 min | ⬜ | `docs/DEPLOYMENT.md` |
| 10 | Alertmanager routing tested | ⬜ | Slack alert received |
| 11 | Alert storm response documented | ⬜ | `docs/runbooks/ALERT_StormResponse.md` |
| 12 | On-call contacts valid | ⬜ | `docs/on-call.md` |
| 13 | Dependency audit clean (0 HIGH/CRITICAL) | ⬜ | `docs/security/dependency-audit-2026-08.md` |
| 14 | End-to-end test green (3.11 + 3.12) | ⬜ | `tests/test_end_to_end.py` |
| 15 | git tag v1.0.0 && git push --tags | ⬜ | GitHub release |

## Go / No-Go criteria

- **Go:** ≥ 12/15 checks ✅, 0 P0 blockers open
- **No-Go:** any P0 security finding (HIGH/CVE) OR load test error rate > 1%
- **Conditional Go:** 11-12 checks, P1 blockers with documented workarounds

## Post-GA

- [ ] Announce on GitHub Discussions
- [ ] Tweet from @asurdev
- [ ] Update roadmap for v1.1.0
- [ ] Retrospective: what blocked GA?
