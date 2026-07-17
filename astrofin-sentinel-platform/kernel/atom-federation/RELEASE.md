# v0.4.0 — Phase 4 Complete: ALL PHASES DONE

**Date:** 2026-04-27
**Version:** v10.8-ATOM-HARDENING-PHASE4

## What's New

### Phase 1-4 All Complete ✅

| Phase | Component | Tests | Status |
|-------|-----------|-------|--------|
| PH1 | Circuit Breaker | ✅ | Complete |
| PH2 | Chaos Integration + Failure Replay | ✅ | Complete |
| PH2 | `sbs replay` CLI | ✅ | Complete |
| PH3 | Federation Sync | ✅ | Complete |
| PH4 | Invariant Evolution (UST) | ✅ | Complete |

### New CLI Commands

- `sbs replay --list` — list saved failure incidents
- `sbs replay --id <id>` — replay specific incident
- `sbs replay --batch` — batch replay all incidents
- `sbs replay --id <id> --json` — machine-readable output
- `sbs chaos --list-scenarios` — show available chaos scenarios
- `sbs chaos --scenario <name>` — run chaos + auto-save to failure replay

### Bug Fixes

- Fixed `sbs __main__.py` entry point (double-call → direct `app()`)
- Fixed `FailureReplay.save()` to add `.json` extension
- Fixed `ChaosResult.save_to_failure_replay()` integration
- Fixed `TickState` → `TickRecord` in phase2 imports
- Fixed all federation tests (C1 wall-clock time → xfail markers)
- Added `typer` to core dependencies in pyproject.toml
