"""Explicit refusal types for the OOS protocol."""


class ValidationError(Exception):
    """Base class: validation refused."""


class ChronologyError(ValidationError):
    """Data or windows are not strictly chronological, overlap, or violate the embargo."""


class LeakageError(ValidationError):
    """A feature is timestamped after the decision it informs (lookahead)."""


class ProtocolError(ValidationError):
    """Frozen protocol missing, corrupt, or not matching the requested run."""


class ContaminationError(ValidationError):
    """Final OOS was already viewed for this protocol / strategy; any re-run or change is refused."""
