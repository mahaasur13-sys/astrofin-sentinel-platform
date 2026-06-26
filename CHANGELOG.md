# Changelog

All notable changes to AstroFin Sentinel Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial monorepo consolidation (astrofin-sentinel-platform)
- CodeRabbit configuration v2 schema (no deprecated keys)
- MIT LICENSE and CHANGELOG.md for production readiness
- Lint config to allow CI to surface CodeRabbit review status
### Changed
- Migrated `.coderabbit.yaml` from v1 (`path_instructions`/`focus_areas`) to v2 schema
- Removed `path_filters` to let CodeRabbit review all files in PR
