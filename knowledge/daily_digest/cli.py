#!/usr/bin/env python3
"""
ATOM-R-042: Daily Digest Integration CLI

Commands:
    analyze   — Parse and analyze a digest file
    propose   — Generate ATOM proposals from analysis
    log       — Show digest processing history
    run       — Full pipeline: analyze → propose → log

Usage:
    python -m knowledge.daily_digest analyze --date 2026-03-29
    python -m knowledge.daily_digest propose --latest
    python -m knowledge.daily_digest log --limit 10
    python -m knowledge.daily_digest run --date 2026-03-29
"""

from __future__ import annotations

import logging
log = logging.getLogger(__name__)
import argparse
import sys
from datetime import datetime
from pathlib import Path


def cmd_analyze(args):
    """Analyze a digest file."""
    from .daily_digest_analytics import DigestAnalyzer

    # Find digest
    if args.path:
        path = Path(args.path)
    else:
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        brief_dir = Path(__file__).parent.parent / "daily_brief"
        path = brief_dir / f"brief_{date}.md"
        if not path.exists():
            # Try latest
            briefs = sorted(brief_dir.glob("brief_????-??-??.md"), reverse=True)
            if briefs:
                path = briefs[0]
            else:
                log.info(f"Error: No digest found for {date}")
                return 1

    log.info(f"Analyzing: {path}")

    analyzer = DigestAnalyzer(str(path))
    analysis = analyzer.analyze()

    if args.json:
        log.info(analyzer.to_json())
    else:
        analyzer.print_report()

    # Save analysis for later use
    analysis_file = Path(__file__).parent / f"analysis_{analysis.date}.json"
    analysis_file.write_text(analyzer.to_json(), encoding="utf-8")
    log.info(f"\nAnalysis saved: {analysis_file}")

    return 0


def cmd_propose(args):
    """Generate ATOM proposals from analysis."""
    from .atom_proposer import AtomProposer
    from .daily_digest_analytics import DigestAnalyzer

    # Find analysis or digest
    analysis_data = None

    if args.analysis:
        path = Path(args.analysis)
        if path.exists():
            import json

            analysis_data = json.loads(path.read_text())
    else:
        # Try to find latest analysis
        analyses = sorted(
            Path(__file__).parent.glob("analysis_????-??-??.json"), reverse=True
        )
        if analyses:
            import json

            analysis_data = json.loads(analyses[0].read_text())
        else:
            # Run analytics
            brief_dir = Path(__file__).parent.parent / "daily_brief"
            briefs = sorted(brief_dir.glob("brief_????-??-??.md"), reverse=True)
            if briefs:
                analyzer = DigestAnalyzer(str(briefs[0]))
                analysis = analyzer.analyze()
                analysis_data = (
                    analysis.__dict__ if hasattr(analysis, "__dict__") else analysis
                )
            else:
                log.info("Error: No digest found. Run analyze first.")
                return 1

    proposer = AtomProposer()
    proposer.propose_from_analysis(analysis_data)

    if args.print or not args.save:
        proposer.print_proposals()

    if args.save:
        path = proposer.save_proposals(args.save)
        log.info(f"\nProposals saved: {path}")

    return 0


def cmd_log(args):
    """Show digest log."""
    from .daily_digest_log import DigestLog

    log = DigestLog()

    if args.stats:
        stats = log.get_stats()
        log.info(f"\n{'=' * 50}")
        log.info("  📊 DIGEST LOG STATISTICS")
        log.info(f"{'=' * 50}")
        log.info(f"  Total digests: {stats.get('total', 0)}")
        log.info("\n  By status:")
        for status, count in stats.get("by_status", {}).items():
            log.info(f"    {status}: {count}")
    else:
        log.list_entries(limit=args.limit, status_filter=args.filter)

    return 0


def cmd_run(args):
    """Run full pipeline: analyze → propose → log."""
    from .atom_proposer import AtomProposer
    from .daily_digest_analytics import DigestAnalyzer
    from .daily_digest_log import DigestLog

    log.info(f"\n{'=' * 70}")
    log.info(
        f"  🔄 DAILY DIGEST PIPELINE — {args.date or datetime.now().strftime('%Y-%m-%d')}"
    )
    log.info(f"{'=' * 70}\n")

    # Step 1: Find and analyze digest
    log.info("📥 Step 1: Analyzing digest...")

    if args.path:
        path = Path(args.path)
    else:
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        brief_dir = Path(__file__).parent.parent / "daily_brief"
        path = brief_dir / f"brief_{date}.md"
        if not path.exists():
            briefs = sorted(brief_dir.glob("brief_????-??-??.md"), reverse=True)
            if briefs:
                path = briefs[0]
            else:
                log.info("Error: No digest found")
                return 1

    analyzer = DigestAnalyzer(str(path))
    analysis = analyzer.analyze()

    # Save analysis
    analysis_file = Path(__file__).parent / f"analysis_{analysis.date}.json"
    analysis_file.write_text(analyzer.to_json(), encoding="utf-8")
    log.info(f"   ✅ Analysis saved: {analysis_file}")

    # Step 2: Generate proposals
    log.info("\n📋 Step 2: Generating ATOM proposals...")

    analysis_data = analysis.__dict__ if hasattr(analysis, "__dict__") else analysis
    proposer = AtomProposer()
    proposals = proposer.propose_from_analysis(analysis_data)

    if proposals:
        proposals_file = Path(__file__).parent.parent / "proposed_atoms.md"
        proposer.save_proposals(str(proposals_file))
        log.info(f"   ✅ Proposals saved: {proposals_file}")
    else:
        log.info("   ⚠️ No proposals generated")

    # Step 3: Log the digest
    log.info("\n📔 Step 3: Logging digest...")

    log = DigestLog()

    # Extract key ideas for log
    key_ideas = []
    for f in sorted(analysis.high_relevance_findings, key=lambda x: -x.relevance_score)[
        :3
    ]:
        key_ideas.append(f.title[:40])

    entry = log.add_entry(
        date=analysis.date,
        source="email",
        key_ideas=key_ideas,
        status="ANALYZED" if proposals else "PROCESSED",
    )
    log.info(f"   ✅ Logged: {entry.date}")

    # Summary
    log.info(f"\n{'=' * 70}")
    log.info("  ✅ PIPELINE COMPLETE")
    log.info(f"{'=' * 70}")
    log.info(f"   Findings: {analysis.total_findings}")
    log.info(f"   High relevance: {len(analysis.high_relevance_findings)}")
    log.info(f"   Proposals: {len(proposals)}")
    log.info("")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="ATOM-R-042: Daily Digest Integration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze a digest file")
    p_analyze.add_argument("--date", type=str, help="Digest date (YYYY-MM-DD)")
    p_analyze.add_argument("--path", type=str, help="Path to digest file")
    p_analyze.add_argument("--json", action="store_true", help="Output JSON")

    # propose
    p_propose = subparsers.add_parser("propose", help="Generate ATOM proposals")
    p_propose.add_argument("--latest", action="store_true", help="Use latest analysis")
    p_propose.add_argument("--analysis", type=str, help="Path to analysis JSON")
    p_propose.add_argument("--save", type=str, help="Save proposals to file")
    p_propose.add_argument("--print", action="store_true", help="Print to console")

    # log
    p_log = subparsers.add_parser("log", help="Show digest log")
    p_log.add_argument("--limit", type=int, default=20, help="Limit entries")
    p_log.add_argument("--filter", type=str, help="Filter by status")
    p_log.add_argument("--stats", action="store_true", help="Show statistics")

    # run
    p_run = subparsers.add_parser("run", help="Run full pipeline")
    p_run.add_argument("--date", type=str, help="Digest date (YYYY-MM-DD)")
    p_run.add_argument("--path", type=str, help="Path to digest file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch
    if args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "propose":
        return cmd_propose(args)
    elif args.command == "log":
        return cmd_log(args)
    elif args.command == "run":
        return cmd_run(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
