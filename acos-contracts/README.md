# acos-contracts

Shared cross-repo **protocols, DTOs, and determinism primitives** for the
AstroFin Sentinel ecosystem. This package is the single allowed
inter-repo dependency surface.

## What lives here

- **Protocols** (`acos_contracts.interfaces`):
  - `AgentResponseProtocol` — multi-agent signal envelope
  - `SignalDirectionProtocol` — LONG / SHORT / NEUTRAL
  - `BaseAgentProtocol` — common agent contract
  - `EphemerisProtocol` — planetary positions interface
  - `DeterministicClock` — clock / RNG injection contract

- **DTOs** (`acos_contracts.contracts`):
  - `TraceRecord` — normalized trace storage record

- **Determinism** (`acos_contracts.deterministic`):
  - `DeterministicContext`, `DeterministicClockImpl`, `DeterministicRNG`
  - `utc_now_deterministic()`, `uuid4_deterministic()`

## Repos that depend on this package

- `astrofin-sentinel-platform` (master)
- `AsurDev` (submodule of astrofin-sentinel-platform)
- `home-cluster-iac` (planned)
- `roma-execution-bridge` (planned)

**No repo may import another repo's code directly.** All shared types
must go through `acos-contracts`.

## Versioning

SemVer. Currently `0.1.0` (S2 refactor baseline).

## Install (dev)

```bash
pip install -e .[dev]
pytest tests/  # when tests are added
```
