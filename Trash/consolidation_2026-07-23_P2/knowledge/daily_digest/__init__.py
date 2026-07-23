"""
Daily Digest Integration Pipeline — ATOM-R-042

Complete pipeline for transforming external multi-agent knowledge
into actionable ATOM improvements for AstroFinSentinelV5.

Modules:
- daily_digest_analytics: Parse and analyze multi-agent digest files
- atom_proposer: Generate concrete ATOM cards from findings
- daily_digest_log: Track processed digests and outcomes
- cli: Unified command-line interface

Usage:
    python -m knowledge.daily_digest analyze --date 2026-03-29
    python -m knowledge.daily_digest propose --latest
    python -m knowledge.daily_digest log --limit 10
    python -m knowledge.daily_digest run --date 2026-03-29

Full Pipeline:
    External (GitHub, arXiv, Reddit, X) → Daily Email (08:00)
        → daily_digest_analytics (parse, categorize, score)
        → atom_proposer (generate ATOM cards)
        → daily_digest_log (track history)
        → Human Review → Implementation

Files:
- knowledge/daily_digest/analytics.py     — Analysis module
- knowledge/daily_digest/atom_proposer.py — ATOM generator
- knowledge/daily_digest/daily_digest_log.py — History tracker
- knowledge/daily_digest/cli.py — CLI interface
- knowledge/proposed_atoms.md — Generated ATOM proposals
- knowledge/daily_digest/daily_digest_log.md — Digest history
"""

from .atom_proposer import AtomProposal, AtomProposer
from .daily_digest_analytics import (
    Category,
    DigestAnalysis,
    DigestAnalyzer,
    Finding,
    RelevanceScore,
)
from .daily_digest_log import DigestEntry, DigestLog, DigestStatus

__all__ = [
    "DigestAnalyzer",
    "Category",
    "RelevanceScore",
    "Finding",
    "DigestAnalysis",
    "AtomProposer",
    "AtomProposal",
    "DigestLog",
    "DigestEntry",
    "DigestStatus",
]
