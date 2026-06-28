"""orchestration — AstroFin Sentinel v5 orchestration layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestration import sentinel_v5, sentinel_v5_mas  # noqa: F401  # re-exported via __getattr__ below  # noqa: F401  # re-exported via __getattr__ below


def __getattr__(name: str):
    if name == "sentinel_v5_mas":
        import orchestration.sentinel_v5_mas

        return orchestration.sentinel_v5_mas
    if name == "sentinel_v5":
        import orchestration.sentinel_v5

        return orchestration.sentinel_v5
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
