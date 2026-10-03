"""Fail-closed tool allowlist for the DSH MCP bridges.

Design constraints (deliberate, do not weaken):
  * Default deny. An unset or blank allowlist means READ-ONLY, never allow-all.
  * No wildcard. Every grant is a name that exists in the bridge's registry, so a
    tool added later is never admitted silently by an earlier "allow everything".
  * Unknown names are dropped, not granted.
  * Privileged (mutating / financial / destructive) tools are granted only when
    named explicitly.

The bridge process is host-level (one `dsh-mcp-client` instance per server), so
this allowlist is process-wide. Per-role differentiation is a separate, larger
change: it needs a `ctx.tools.guard()` / `ctx.tools.restrict()` plugin on the
DSH side, which this repository does not yet ship.
"""
from __future__ import annotations

import sys

_SENTINELS = frozenset({"", "undefined", "null"})


def parse_allowlist(raw: str | None) -> frozenset[str] | None:
    """Parse a comma-separated allowlist. Returns None when unset or blank."""
    if raw is None:
        return None
    value = str(raw).strip()
    if value.lower() in _SENTINELS:
        return None
    names = {part.strip() for part in value.split(",") if part.strip()}
    return frozenset(names) or None


def resolve_allowed_tools(
    read_only: frozenset[str],
    privileged: frozenset[str],
    raw: str | None,
) -> frozenset[str]:
    """Resolve the effective allowlist for one bridge. Fail-closed."""
    known = read_only | privileged
    requested = parse_allowlist(raw)
    if requested is None:
        return frozenset(read_only)
    # No wildcard: an "all" token is refused rather than expanded, so a tool
    # added later can never be admitted by a grant written earlier.
    if "*" in requested or any(part.lower() == "all" for part in requested):
        warn("ignoring wildcard in allowlist; name tools explicitly")
        requested = frozenset(
            part for part in requested
            if part != "*" and part.lower() != "all"
        )
    return frozenset(requested & known)


def is_allowed(name: str, allowed: frozenset[str]) -> bool:
    """A tool is permitted only if its exact name is in the effective allowlist."""
    return isinstance(name, str) and name in allowed


def warn(message: str) -> None:
    """Emit a stable, secret-free diagnostic to stderr (stdio transport: never stdout)."""
    print(f"[tool-allowlist] {message}", file=sys.stderr, flush=True)
