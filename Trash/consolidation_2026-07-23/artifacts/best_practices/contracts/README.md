# Contracts

**Source of truth:** `acos-contracts/` package (live in the repo, not
here — this directory holds the two highest-traffic files for quick
reference).

The `acos-contracts` package is the **only** layer that all four
repos in the AsurDev ecosystem are allowed to depend on, in any
direction. `import_linter` enforces this.

## Files in this directory

* `data_contracts.py` — DTOs (`TraceRecord`, …) and storage
  protocols (`TraceStoreProtocol`). Anything that has to be passed
  between repos goes here first.
* `shared_exceptions.py` — `ACOSContractsError` base + concrete
  subclasses (`EphemerisUnavailableError`, …). Catching this base in
  any repo means "the contract layer is the one that failed", which
  is much more useful than `except Exception`.

## How to extend

1. Add the DTO/exception to `acos-contracts/acos_contracts/`.
2. Bump `__version__` in `acos-contracts/pyproject.toml`.
3. Re-export from any convenience location if needed — do not fork
   the class.
4. Add a test under `acos-contracts/tests/`.
