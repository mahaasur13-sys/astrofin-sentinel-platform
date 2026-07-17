# MAINTAINERS

> Bus-factor and ownership map for `astrofin-sentinel-platform`.
> If this file goes out of date, the next on-call rotation will hurt.

## Current maintainers

| Handle | GitHub | Time zone | Areas of ownership |
|---|---|---|---|
| Felix | `@mahaasur13-sys` | Europe/Samara | Everything (sole maintainer as of 2026-07) |

> A second maintainer is a 2026 Q3 hiring goal. Until then, all reviews
> are Felix + CodeRabbit (autoreviewer) + one external reviewer for
> changes touching `web/auth*`, `core/auth*`, or release workflows.

## Areas of ownership

| Area | Primary | Notes |
|---|---|---|
| `core/`            | Felix | Auth, history DB, agent base classes |
| `agents/`          | Felix | Multi-agent orchestration |
| `meta_rl/`         | Felix | Thompson sampling, A/B testing, persistence |
| `web/`             | Felix | Dash dashboard, Flask blueprints, data room |
| `deploy/`          | Felix | Docker, k8s manifests, Helm/Terraform |
| `migrations/`      | Felix | SQLite schema evolution |
| `docs/adr/`        | Felix | Architectural decisions (gatekept) |
| `.github/`         | Felix | CI workflows and CODEOWNERS |
| Release / tagging  | Felix | Manual `vX.Y.Z` tags; no release-bot yet |

## Decision authority

- **Day-to-day PRs**: any maintainer with admin merge rights.
- **Architecture changes (new ADRs, breaking API changes, schema
  migrations that drop columns)**: requires an ADR under
  `docs/adr/000N-*.md` and explicit approval from Felix.
- **Security-sensitive changes** (auth, secrets, CI permissions):
  Felix + external reviewer.
- **Dependency upgrades that change a major version** (`faiss-cpu`,
  `pandas`, etc.): must reference a tracked issue with a migration
  note.

## PR acceptance process

1. **CI green** — `lint`, `type-check`, `tests`, `security`,
   `compose-check`, `docs-build` must all be green.
2. **CodeRabbit review** — auto-reviews every PR; unresolved
   `nit:` comments are non-blocking, `bug:` and `security:` comments
   are blocking.
3. **Human review** — required for:
   - Any change to `core/auth.py`, `web/auth*`, `.github/workflows/*`.
   - Any ADR.
   - Any change over 500 LOC.
4. **Self-merge rule** — Felix may self-merge if and only if at least
   one external reviewer has approved (or the change is < 50 LOC and
   only docs/CI).
5. **Squash-merge** is the default; the PR title becomes the
   single-commit subject.

## Release cycle

- **Cadence** — manual, ad-hoc until 2026 Q4.
- **Versioning** — SemVer. `vX.Y.Z` tags are immutable.
- **Process**:
  1. Open a `release/X.Y.Z` branch from `master`.
  2. Bump version in `pyproject.toml` and `CHANGELOG.md`.
  3. Open a PR titled `release: vX.Y.Z`.
  4. Tag the merge commit: `git tag -s vX.Y.Z -m "vX.Y.Z"`.
  5. Push tag: `git push origin vX.Y.Z`. CI publishes the release
     artifacts.
- **Hotfixes** — branch from the release tag, not from `master`.
