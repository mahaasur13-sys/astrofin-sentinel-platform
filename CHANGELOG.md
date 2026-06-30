# Changelog

All notable changes to AstroFin Sentinel Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (none yet)

### Changed
- (none yet)

### Fixed
- (none yet)

## [5.0.0] - 2026-06-30

### Added
- Monorepo bootstrap (`astrofin-monorepo/`) consolidating v1/v2 audits.
- Architectural linter (`scripts/architecture_linter.py`) enforcing R1–R10 rules.
- Multi-tier data room (`data_room/{public,partner,private}/`) with per-tier ACL.
- `web/data_room.py` @require_auth decorator for partner/private tier access.
- Agent registry (`docs/AGENT_REGISTRY.md`) and capability index.
- CI pipeline (`.github/workflows/ci.yml`) with flake8, ruff, bandit, radon, pytest.
- Nightly workflow with DORA metrics collection and smoke tests.
- Release workflow with semantic-versioned tags and GitHub release notes.
- Security workflow with blocking bandit, secret-scanning, and weekly schedule.
- PR-checks workflow with size thresholds, conventional-commit validation, and tier-allowlist.
- Pre-commit hooks (`.pre-commit-config.yaml`) for ruff + black + architecture linter.
- `scripts/release.sh` (patch/minor/major bump) and `scripts/hotfix.sh` (fast-track).
- Release-drafter with conventional-commit categorization.
- Dependabot for pip and GitHub Actions.

### Changed
- Single repository `astrofin-sentinel-platform` with `astrofin-monorepo/` overlay.
- `agents/karl_synthesis.py`: `KARLSynthesisAgent` now inherits `SynthesisAgent` (resolves R1).
- `scripts/architecture_linter.py:check_require_ephemeris` switched to AST traversal (resolves R2 false positives).

### Fixed
- (none)

[Unreleased]: https://github.com/mahaasur13-sys/astrofin-sentinel-platform/compare/v5.0.0...HEAD
[5.0.0]: https://github.com/mahaasur13-sys/astrofin-sentinel-platform/releases/tag/v5.0.0
