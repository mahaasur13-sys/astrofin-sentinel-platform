# Changelog

All notable changes to the AstroFin Sentinel Platform monorepo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial monorepo bootstrap aggregating three production projects
  - `root (push)`: AstroFinSentinelV5 — multi-agent trading system (KARL/AMRE/Astro Council)
  - `infrastructure/asurdev`: home-cluster IaC, ACOS, observability stack
  - `kernel/atom-federation`: ATOM kernel with formal verification
  - `bridge/roma`: ROMA execution bridge with SaaS billing
- CI workflow (`.github/workflows/ci.yml`) with Python 3.11/3.12 testing
- Flake8, Bandit, Radon static analysis
- Dependabot for weekly pip updates
- CODEOWNERS with two maintainers
- DORA metrics collection script (`scripts/dora_metrics.py`)

## [0.1.0-alpha] - 2026-06-30

### Added
- First tagged release of the unified monorepo

[Unreleased]: https://github.com/mahaasur13-sys/astrofin-sentinel-platform/compare/v0.1.0-alpha...HEAD
[0.1.0-alpha]: https://github.com/mahaasur13-sys/astrofin-sentinel-platform/releases/tag/v0.1.0-alpha