"""
Output formatting — breakdown, source collection, signal attribute access.

Extracted from synthesis_agent.py (v1.0.0).
"""
from __future__ import annotations

from agents._impl.synthesis.weights import CATEGORY_WEIGHTS


def get_signal_attr(sig, key: str, default=None):
    """Get attribute or dict key from signal (handles both AgentResponse and dict)."""
    if hasattr(sig, key):
        return getattr(sig, key)
    if isinstance(sig, dict):
        return sig.get(key, default)
    return default


def format_breakdown(categories: dict[str, list]) -> str:
    """Format per-category breakdown string for metadata."""
    lines: list[str] = []

    for cat, signals in categories.items():
        w = CATEGORY_WEIGHTS.get(cat, 0.0)
        if not signals:
            lines.append(
                f"  [{cat.upper():12s}] NEUTRAL    [░░░░░░░░░░]   0.0% w={w:.2f} (no signals)"
            )
            continue

        conf_avg = sum(get_signal_attr(s, "confidence", 50) for s in signals) / len(signals)
        votes = [get_signal_attr(s, "signal", "NEUTRAL").upper() for s in signals]
        long_v = votes.count("LONG") + votes.count("BUY")
        short_v = votes.count("SHORT") + votes.count("SELL")

        direction = (
            "LONG ▲" if long_v > short_v
            else "SHORT ▼" if short_v > long_v
            else "NEUT"
        )

        n = max(1, int(conf_avg / 10))
        bar = "█" * n + "░" * (10 - n)
        agents_str = ", ".join(get_signal_attr(s, "agent_name", "?") for s in signals)

        lines.append(
            f"  [{cat.upper():12s}] {direction:12s} [{bar}] {conf_avg:5.1f}% w={w:.2f} ({agents_str})"
        )

    return "\n".join(lines)


def collect_sources(signals: list) -> list[str]:
    """Collect unique source URLs/docs from all agent signals."""
    sources: list[str] = []
    for sig in signals:
        for src in get_signal_attr(sig, "sources", []):
            if src and isinstance(src, str):
                sources.append(src)
    return list(set(sources))
