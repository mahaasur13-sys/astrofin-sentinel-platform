"""Shared exceptions reused across acos-contracts consumers.

These exceptions live here so that *all* consumers (astrofin-sentinel-platform,
AsurDev, home-cluster-iac, roma-execution-bridge) raise and catch the *same*
type — never an ad-hoc local copy. Having a single hierarchy means import-linter
can forbid cross-repo exception imports.
"""

from __future__ import annotations


class ACOSContractsError(Exception):
    """Base class for all exceptions raised by acos-contracts consumers.

    Catching this is the recommended way to handle "something in the
    shared contract layer went wrong" without binding to a specific
    underlying repo.
    """


class EphemerisUnavailableError(ACOSContractsError):
    """Raised when the ephemeris provider cannot answer a query.

    Lifted from `core/ephemeris.py` and `agents/_impl/ephemeris_decorator.py`.
    Downstream code (orchestrators, dashboards) should catch the type
    imported from `acos_contracts` rather than the local copy.
    """

    def __init__(self, message: str = "Ephemeris provider unavailable", *, provider: str | None = None) -> None:
        super().__init__(message)
        self.provider = provider


__all__ = ["ACOSContractsError", "EphemerisUnavailableError"]
