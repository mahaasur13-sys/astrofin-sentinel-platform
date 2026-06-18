#!/usr/bin/env python3
"""
ATOM-R-042: ATOM Proposer

Generates concrete, actionable ATOM cards from digest analysis.
Outputs structured proposals in knowledge/proposed_atoms.md format.

Usage:
    python knowledge/daily_digest/atom_proposer.py --latest
    python knowledge/daily_digest/atom_proposer.py --analyze knowledge/daily_digest/analysis.json
    python knowledge/daily_digest/atom_proposer.py --propose-from findings.json
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class AtomProposal:
    """A proposed ATOM card."""

    atom_id: str  # e.g., "ATOM-R-044"
    title: str
    priority: str  # P0, P1, P2
    summary: str  # 2-3 sentences
    why_now: str  # Why this matters now
    project_context: str  # Connection to current problems
    complexity: str  # LOW, MEDIUM, HIGH
    expected_effect: str
    related_findings: list = field(default_factory=list)
    proposed_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    status: str = "PROPOSED"


class AtomProposer:
    """Generates ATOM proposals from digest findings."""

    # Known existing ATOMs (to avoid duplicates)
    EXISTING_ATOMS = {
        "R-001",
        "R-002",
        "R-003",
        "R-004",
        "R-005",
        "R-006",
        "R-007",
        "R-008",
        "R-009",
        "R-010",
        "R-011",
        "R-012",
        "R-013",
        "R-014",
        "R-015",
        "R-016",
        "R-017",
        "R-018",
        "R-019",
        "R-020",
        "R-021",
        "R-022",
        "R-023",
        "R-024",
        "R-025",
        "R-026",
        "R-027",
        "R-028",
        "R-029",
        "R-030",
        "R-031",
        "R-032",
        "R-033",
        "R-034",
        "R-035",
        "R-036",
        "R-037",
        "R-038",
        "R-039",
        "R-040",
        "R-041",
        "R-042",
    }

    def __init__(self):
        self.proposals: list[AtomProposal] = []
        self.next_number = 43  # Start after R-042

    def _get_next_id(self) -> str:
        """Get next available ATOM ID."""
        while f"R-{self.next_number:03d}" in self.EXISTING_ATOMS:
            self.next_number += 1
        atom_id = f"R-{self.next_number:03d}"
        self.next_number += 1
        return atom_id

    def _extract_keywords(self, finding) -> list[str]:
        """Extract key concepts from finding."""
        text = f"{finding.title} {finding.description}".lower()
        keywords = []

        important = [
            "multi-agent",
            "coordination",
            "pressure field",
            "temporal decay",
            "thompson sampling",
            "reward",
            "oap",
            "uncertainty",
            "mas factory",
            "topology",
            "switch node",
            "agent",
            "visualization",
            "dashboard",
            "backtest",
            "postgresql",
            "ensemble",
            "voting",
            "confidence",
            "calibration",
            "self-improvement",
            "meta-reasoning",
            "grounding",
        ]

        for kw in important:
            if kw in text:
                keywords.append(kw)

        return keywords[:5]

    def propose_from_analysis(self, analysis_data: dict) -> list[AtomProposal]:
        """Generate ATOM proposals from analysis data."""
        proposals = []

        findings = analysis_data.get("findings", [])
        high_rel = [f for f in findings if f.relevance_score >= 0.5]

        # Process each high-relevance finding
        for finding in high_rel:
            proposal = self._create_proposal(finding)
            if proposal:
                proposals.append(proposal)

        # Cross-cutting proposals based on category distribution
        category_counts = analysis_data.get("category_breakdown", {})

        if category_counts.get("RL_OAP_REWARD", 0) >= 2:
            prop = self._create_crosscut_proposal(
                title="Усилить RL/OAP контур в KARL",
                category="RL_OAP_REWARD",
                description="Несколько находок связаны с reinforcement learning и reward shaping. "
                "Нужно усилить OAP optimizer и reward calibration.",
                priority="P1",
            )
            proposals.append(prop)

        if category_counts.get("VISUALIZATION", 0) >= 1:
            prop = self._create_crosscut_proposal(
                title="Добавить Agent Workflow Visualization",
                category="VISUALIZATION",
                description="Найдены инструменты визуализации. Предложить интеграцию "
                "с MAS Factory visualizer для debugging.",
                priority="P2",
            )
            proposals.append(prop)

        self.proposals = proposals
        return proposals

    def _create_proposal(self, finding) -> AtomProposal | None:
        """Create ATOM proposal from a single finding."""
        keywords = self._extract_keywords(finding)
        title_text = finding.title

        # Map finding categories to ATOM themes
        relevance = finding.relevance_score

        # Pressure Field Coordination
        if "pressure" in title_text.lower() or "coordination" in title_text.lower():
            return self._propose_pressure_field(finding, keywords)

        # CrewAI / Multi-Agent Orchestration
        if "crewai" in title_text.lower() or "orchestration" in title_text.lower():
            return self._propose_crewai_integration(finding, keywords)

        # AutoGen / Agent Communication
        if "autogen" in title_text.lower() or "communication" in title_text.lower():
            return self._propose_autogen_protocol(finding, keywords)

        # Thompson Sampling related
        if "thompson" in title_text.lower() or "sampling" in title_text.lower():
            return self._propose_thompson_improvement(finding, keywords)

        # Generic high-relevance → general improvement
        if relevance >= 0.7:
            return self._propose_generic_improvement(finding, keywords)

        return None

    def _propose_pressure_field(self, finding, keywords) -> AtomProposal:
        """ATOM proposal: Pressure Field Coordination."""
        return AtomProposal(
            atom_id=f"ATOM-{self._get_next_id()}",
            title="Pressure Field Coordination для MAS Factory",
            priority="P1",
            summary="Интегрировать концепцию pressure field coordination из arXiv:2601.08129 "
            "в MAS Factory. Вместо явного иерархического управления, агенты будут "
            "координироваться через quality signals и pressure gradients.",
            why_now="Показано 48.5% solve rate vs 12.6% conversation-based — "
            "это принципиально другой подход к масштабированию агентов. "
            "AstroFinSentinelV5 с 14 агентами нуждается в лучшей координации.",
            project_context="Связано с ATOM-R-028 (MAS Factory), ATOM-R-030 (Switch Nodes). "
            "Текущая архитектура использует hierarchical policy, "
            "но pressure field может улучшить emergent coordination. "
            "Проблема: Sharpe Ratio 0.71 < 1.0 —需要一个更好的 coordination mechanism.",
            complexity="MEDIUM",
            expected_effect="Улучшение agent coordination без явного hierarchical overhead. "
            "Ожидаем impact на WIN rate и Sharpe Ratio.",
            related_findings=[finding.title],
        )

    def _propose_crewai_integration(self, finding, keywords) -> AtomProposal:
        """ATOM proposal: CrewAI integration."""
        return AtomProposal(
            atom_id=f"ATOM-{self._get_next_id()}",
            title="CrewAI v2.3 Integration для Agent Council",
            priority="P2",
            summary="CrewAI v2.3 представил hierarchical agent teams и flow visualization. "
            "Использовать эти концепции для улучшения Astro Council — "
            "организовать agents как команды с явными role hierarchies.",
            why_now="CrewAI now supports dynamic agent addition и memory management. "
            "Это может заменить текущую простую agent pool архитектуру.",
            project_context="Текущий Astro Council использует parallel agent execution. "
            "CrewAI hierarchical teams могут улучшить coordination. "
            "Связано с ATOM-R-028 (MAS Factory).",
            complexity="MEDIUM",
            expected_effect="Более structured agent workflows, easier debugging, "
            "potential improvement in signal quality.",
            related_findings=[finding.title],
        )

    def _propose_autogen_protocol(self, finding, keywords) -> AtomProposal:
        """ATOM proposal: AutoGen communication protocol."""
        return AtomProposal(
            atom_id=f"ATOM-{self._get_next_id()}",
            title="Universal Agent Communication Protocol (AutoGen 0.4 style)",
            priority="P1",
            summary="AutoGen 0.4 представил universal agent communication protocol. "
            "Реализовать similar protocol в AstroFinSentinelV5 для стандартизации "
            "agent-to-agent messaging между MAS Factory components.",
            why_now="Community discussion on HN показывает тренд на standardization. "
            "Early adoption даст конкурентное преимущество.",
            project_context="Связано с ATOM-R-028 (MAS Factory), ATOM-R-031 (Agent Registry). "
            "Текущие agent communications используют ad-hoc JSON formats. "
            "Standardization упростит debugging и extension.",
            complexity="MEDIUM",
            expected_effect="Standardized inter-agent communication, easier integration "
            "of new agents, better maintainability.",
            related_findings=[finding.title],
        )

    def _propose_thompson_improvement(self, finding, keywords) -> AtomProposal:
        """ATOM proposal: Thompson Sampling improvements."""
        return AtomProposal(
            atom_id=f"ATOM-{self._get_next_id()}",
            title="Thompson Sampling с Uncertainty-Aware Temperature",
            priority="P1",
            summary="Улучшить Thompson Sampling agent selection, учитывая epistemic uncertainty. "
            "Добавить temperature scaling based on UncertaintyEngine output — "
            "когда uncertainty высокий, использовать более exploratory policy.",
            why_now="Current Thompson Sampling использует fixed temperature. "
            "Интеграция с KARL UncertaintyEngine может улучшить exploration/exploitation tradeoff.",
            project_context="Связано с ATOM-R-014 (Thompson Sampling), ATOM-R-023 (UncertaintyEngine). "
            "Проблема: Sharpe Ratio 0.71 — uncertainty-aware selection может помочь.",
            complexity="LOW",
            expected_effect="Better balance between exploitation (high confidence signals) "
            "and exploration (trying under-explored agent combinations).",
            related_findings=[finding.title],
        )

    def _propose_generic_improvement(self, finding, keywords) -> AtomProposal:
        """Generic high-relevance improvement."""
        return AtomProposal(
            atom_id=f"ATOM-{self._get_next_id()}",
            title=f"Интеграция находки: {finding.title[:50]}",
            priority="P2",
            summary=f"Исследовать и potentially adopt: {finding.title}. "
            f"Применение: {'; '.join(finding.potential_applications[:2])}",
            why_now=f"Relevance score {finding.relevance_score:.2f} indicates "
            f"direct applicability to AstroFinSentinelV5.",
            project_context="Найдено в ежедневном дайджесте. Требует further research "
            "для определения точного применения.",
            complexity="MEDIUM",
            expected_effect="TBD after further research",
            related_findings=[finding.title],
        )

    def _create_crosscut_proposal(self, title: str, category: str, description: str, priority: str) -> AtomProposal:
        """Create cross-cutting proposal from category analysis."""
        return AtomProposal(
            atom_id=f"ATOM-{self._get_next_id()}",
            title=title,
            priority=priority,
            summary=description,
            why_now="Multiple findings in this category suggest a trend or gap that AstroFinSentinelV5 should address.",
            project_context="Cross-cutting improvement based on digest analysis. "
            "Review required to determine specific implementation steps.",
            complexity="MEDIUM",
            expected_effect="TBD",
            related_findings=[f"Category: {category}"],
        )

    def save_proposals(self, output_path: str = None) -> str:
        """Save proposals to markdown file."""
        if not self.proposals:
            return ""

        if output_path is None:
            output_path = Path(__file__).parent.parent / "proposed_atoms.md"

        output_path = Path(output_path)

        lines = [
            "# Proposed ATOMs — Daily Digest Integration",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total proposals: {len(self.proposals)}",
            "",
            "---",
            "",
        ]

        for p in sorted(
            self.proposals,
            key=lambda x: (["P0", "P1", "P2"].index(x.priority), x.atom_id),
        ):
            lines.extend(
                [
                    f"## {p.atom_id}: {p.title}",
                    "",
                    f"**Priority:** {p.priority}",
                    f"**Status:** {p.status}",
                    f"**Complexity:** {p.complexity}",
                    f"**Proposed:** {p.proposed_at}",
                    "",
                    "### Summary",
                    p.summary,
                    "",
                    "### Why Now?",
                    p.why_now,
                    "",
                    "### Project Context",
                    p.project_context,
                    "",
                    "### Expected Effect",
                    p.expected_effect,
                    "",
                    f"**Related Findings:** {', '.join(p.related_findings)}",
                    "",
                    "---",
                    "",
                ]
            )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return str(output_path)

    def print_proposals(self):
        """Print proposals to console."""
        if not self.proposals:
            print("No proposals generated. Run propose_from_analysis() first.")
            return

        print(f"\n{'=' * 70}")
        print(f"  📋 ATOM PROPOSALS — {len(self.proposals)} Generated")
        print(f"{'=' * 70}\n")

        for p in sorted(
            self.proposals,
            key=lambda x: (["P0", "P1", "P2"].index(x.priority), x.atom_id),
        ):
            print(f"  {p.atom_id} [{p.priority}] {p.title}")
            print(f"       Complexity: {p.complexity}")
            print(f"       Summary: {p.summary[:100]}...")
            print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ATOM Proposer from Daily Digest")
    parser.add_argument("--latest", action="store_true", help="Propose from latest digest")
    parser.add_argument("--analysis", type=str, help="Path to analysis JSON from analytics")
    parser.add_argument("--save", type=str, help="Save proposals to file")
    parser.add_argument("--print", action="store_true", help="Print proposals")

    args = parser.parse_args()

    if args.latest or args.analysis:
        # Find or load analysis
        if args.analysis:
            with open(args.analysis) as f:
                analysis_data = json.load(f)
        else:
            # Run analytics first
            from .daily_digest_analytics import DigestAnalyzer

            brief_dir = Path(__file__).parent.parent / "daily_brief"
            path = brief_dir / "brief_latest.md"
            if not path.exists():
                print("No digest found. Run analytics first.")
                return
            analyzer = DigestAnalyzer(str(path))
            analysis = analyzer.analyze()
            analysis_data = analysis.__dict__ if hasattr(analysis, "__dict__") else analysis

        proposer = AtomProposer()
        proposer.propose_from_analysis(analysis_data)
    else:
        print("Use --latest or --analysis to provide data.")
        return

    if args.print or not args.save:
        proposer.print_proposals()

    if args.save:
        path = proposer.save_proposals(args.save)
        print(f"\nSaved to: {path}")


if __name__ == "__main__":
    main()
