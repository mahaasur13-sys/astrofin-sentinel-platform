#!/usr/bin/env python3
"""
ATOM-R-042: Daily Digest Analytics

Parses multi-agent digest files, categorizes findings,
and evaluates relevance to AstroFinSentinelV5.
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class Category(Enum):
    TOOLS_AND_FRAMEWORKS = "TOOLS_AND_FRAMEWORKS"
    ARCHITECTURE_PATTERNS = "ARCHITECTURE_PATTERNS"
    RL_OAP_REWARD = "RL_OAP_REWARD"
    VISUALIZATION = "VISUALIZATION"
    DATABASE = "DATABASE"
    DEPLOYMENT = "DEPLOYMENT"
    OTHER = "OTHER"


class RelevanceScore:
    """Relevance scoring for AstroFinSentinelV5."""

    HIGH_RELEVANCE = {
        "multi-agent",
        "mas factory",
        "agent orchestration",
        "agent coordination",
        "thompson sampling",
        "reward function",
        "reward shaping",
        "oap",
        "self-improvement",
        "meta-reasoning",
        "karma",
        "self-questioning",
        "uncertainty",
        "grounding",
        "confidence calibration",
        "position sizing",
        "agent topology",
        "switch node",
        "merge node",
        "sequential node",
        "parallel node",
        "hierarchical",
        "ensemble",
        "voting",
        "crewai",
        "autogen",
        "pressure field",
        "temporal decay",
    }

    MEDIUM_RELEVANCE = {
        "agent",
        "llm",
        "language model",
        "pipeline",
        "workflow",
        "async",
        "parallel",
        "orchestration",
        "framework",
        "tool",
        "api",
        "integration",
        "monitoring",
        "visualization",
        "dashboard",
        "backtest",
        "trading",
        "signal",
        "confidence",
        "decision",
        "arxiv",
        "research",
        "paper",
        "coordination",
    }

    LOW_RELEVANCE = {
        "marketing",
        "community",
        "social media",
        "post",
        "tweet",
        "hacker news",
        "reddit",
        "opinion",
        "speculation",
    }

    @classmethod
    def score(cls, text: str) -> float:
        text_lower = text.lower()
        score = 0.0

        for kw in cls.HIGH_RELEVANCE:
            if kw in text_lower:
                score += 0.25

        for kw in cls.MEDIUM_RELEVANCE:
            if kw in text_lower:
                score += 0.10

        for kw in cls.LOW_RELEVANCE:
            if kw in text_lower:
                score -= 0.15

        return max(0.0, min(1.0, round(score, 2)))


@dataclass
class Finding:
    title: str
    source: str
    source_url: str | None = None
    description: str = ""
    category: str = Category.OTHER.value
    relevance_score: float = 0.0
    potential_applications: list = field(default_factory=list)
    risks: list = field(default_factory=list)
    raw_text: str = ""


@dataclass
class DigestAnalysis:
    date: str
    total_findings: int
    findings: list
    category_breakdown: dict
    high_relevance_findings: list
    summary: str
    analyzed_at: str = None

    def __post_init__(self):
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now().isoformat()


class DigestAnalyzer:
    """Analyzes multi-agent digest files."""

    CATEGORY_KEYWORDS = {
        Category.TOOLS_AND_FRAMEWORKS: [
            "framework",
            "library",
            "tool",
            "release",
            "github",
            "package",
            "sdk",
            "api",
            "module",
            "plugin",
            "extension",
            "crewai",
            "autogen",
        ],
        Category.ARCHITECTURE_PATTERNS: [
            "architecture",
            "design pattern",
            "mas factory",
            "topology",
            "switch node",
            "merge node",
            "sequential",
            "parallel",
            "agent orchestration",
            "workflow",
            "pipeline",
            "routing",
            "hierarchical",
            "multi-agent",
            "coordination",
            "pressure field",
        ],
        Category.RL_OAP_REWARD: [
            "reinforcement learning",
            "reward",
            "rl",
            "oap",
            "optimization",
            "policy",
            "training",
            "trajectory",
            "backprop",
            "gradient",
            "self-improvement",
            "meta-learning",
            "calibration",
            "temporal decay",
        ],
        Category.VISUALIZATION: [
            "visualization",
            "dashboard",
            "monitoring",
            "debugging",
            "tracing",
            "logging",
            "metrics",
            "observability",
            "ui",
        ],
        Category.DATABASE: [
            "database",
            "postgresql",
            "sqlite",
            "persistence",
            "storage",
            "cache",
            "caching",
            "query",
            "schema",
            "migration",
        ],
        Category.DEPLOYMENT: [
            "deployment",
            "production",
            "scaling",
            "kubernetes",
            "docker",
            "ci/cd",
            "infrastructure",
            "cloud",
            "serverless",
        ],
    }

    def __init__(self, digest_path: str = None):
        self.digest_path = digest_path
        self.current_analysis: DigestAnalysis | None = None

    def parse_digest(self, content: str, date_hint: str = None) -> list[Finding]:
        """Parse digest content into structured findings."""
        findings = []

        # Extract date
        date = date_hint
        if not date:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", content[:100])
            if date_match:
                date = date_match.group(1)

        # Split by numbered items: ### 1., ### 2., etc.
        # Pattern: ### N. **Title** or ### Title
        sections = re.split(r"\n(?=###\s+\d+\.)", content)

        for section in sections:
            if not section.strip() or len(section.strip()) < 30:
                continue

            # Extract title: ### N. **Title**
            title_match = re.search(r"###\s+\d+\.\s+\*\*([^*]+)\*\*", section)
            title = ""
            if title_match:
                title = title_match.group(1).strip()

            if not title:
                # Fallback: first line
                lines = [l.strip() for l in section.split("\n") if l.strip() and not l.startswith("#")]
                if lines:
                    title = lines[0][:100]

            # Extract source
            source = "Unknown"
            if "arxiv" in section.lower():
                source = "arXiv"
            elif "github" in section.lower():
                source = "GitHub"
            elif "hacker" in section.lower():
                source = "Hacker News"
            elif "reddit" in section.lower():
                source = "Reddit"
            elif "twitter" in section.lower() or "x.com" in section.lower():
                source = "X"

            # Extract URL
            source_url = None
            url_match = re.search(r"(https?://[^\s\)\"']+)", section)
            if url_match:
                source_url = url_match.group(1)

            # Extract description: **Описание:** ...
            description = ""
            desc_match = re.search(r"\*\*Описание:\*\*\s*(.+?)(?:\n\*\*|$)", section, re.DOTALL)
            if desc_match:
                description = desc_match.group(1).strip()

            # Extract importance: **Важность:** ...
            importance = ""
            imp_match = re.search(r"\*\*Важность:\*\*\s*(.+?)(?:\n|$)", section)
            if imp_match:
                importance = imp_match.group(1).strip()

            # Full text for analysis
            full_text = f"{title} {description} {importance}"

            # Categorize
            category = self._categorize(full_text)

            # Score relevance
            relevance = RelevanceScore.score(full_text)

            # Generate implications
            apps, risks = self._generate_implications(title, description, category, relevance)

            if len(title) > 10:
                finding = Finding(
                    title=title[:200],
                    source=source,
                    source_url=source_url,
                    description=description[:300],
                    category=category.value,
                    relevance_score=relevance,
                    potential_applications=apps,
                    risks=risks,
                    raw_text=section[:1000],
                )
                findings.append(finding)

        return findings

    def _categorize(self, text: str) -> Category:
        text_lower = text.lower()
        scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            scores[category] = sum(1 for kw in keywords if kw in text_lower)

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return Category.OTHER

    def _generate_implications(
        self, title: str, description: str, category: Category, relevance: float
    ) -> tuple[list, list]:
        apps = []
        risks = []
        text = f"{title} {description}".lower()

        if relevance >= 0.5:
            if "multi-agent" in text or "coordination" in text or "pressure field" in text:
                apps.append("Улучшить MAS Factory координацию через pressure field концепцию")
                apps.append("Оптимизировать AgentNode/SwitchNode взаимодействие")

            if "thompson" in text or "sampling" in text:
                apps.append("Улучшить Thompson Sampling agent selection")

            if "reward" in text or "oap" in text or "policy" in text:
                apps.append("Интегрировать в KARL reward calibration loop")

            if "crewai" in text:
                apps.append("CrewAI hierarchical teams для Astro Council")

            if "autogen" in text:
                apps.append("Universal Agent Communication Protocol")

            if "visualization" in text or "flow" in text:
                apps.append("Улучшить MAS Factory visualization")

        if relevance < 0.3:
            risks.append("Низкая релевантность для AstroFinSentinelV5")
        if "experimental" in text or "beta" in text:
            risks.append("Технология нестабильна для production")

        return apps[:3], risks[:2]

    def analyze(self, digest_path: str = None, date_hint: str = None) -> DigestAnalysis:
        path = Path(digest_path or self.digest_path)

        if not path.exists():
            raise FileNotFoundError(f"Digest not found: {path}")

        content = path.read_text(encoding="utf-8")
        date = date_hint or path.stem.split("_")[-1] or datetime.now().strftime("%Y-%m-%d")

        findings = self.parse_digest(content, date)

        breakdown = {}
        for f in findings:
            breakdown[f.category] = breakdown.get(f.category, 0) + 1

        high_rel = [f for f in findings if f.relevance_score >= 0.5]

        summary = self._generate_summary(findings, high_rel, breakdown)

        self.current_analysis = DigestAnalysis(
            date=date,
            total_findings=len(findings),
            findings=findings,
            category_breakdown=breakdown,
            high_relevance_findings=high_rel,
            summary=summary,
        )

        return self.current_analysis

    def _generate_summary(self, findings: list, high_rel: list, breakdown: dict) -> str:
        lines = [
            f"Найдено {len(findings)} находок, {len(high_rel)} с высокой релевантностью (≥0.5).",
        ]

        if breakdown:
            cats = sorted(breakdown.items(), key=lambda x: -x[1])
            lines.append(f"Категории: {', '.join(f'{c}={n}' for c, n in cats[:3])}.")

        if high_rel:
            top3 = sorted(high_rel, key=lambda x: -x.relevance_score)[:3]
            lines.append(f"Топ-3: {', '.join(f.title[:40] for f in top3)}.")

        return " ".join(lines)

    def to_json(self) -> str:
        if not self.current_analysis:
            return "{}"
        data = {
            "date": self.current_analysis.date,
            "total_findings": self.current_analysis.total_findings,
            "findings": [f.__dict__ for f in self.current_analysis.findings],
            "category_breakdown": self.current_analysis.category_breakdown,
            "high_relevance_findings": [f.__dict__ for f in self.current_analysis.high_relevance_findings],
            "summary": self.current_analysis.summary,
            "analyzed_at": self.current_analysis.analyzed_at,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def print_report(self):
        if not self.current_analysis:
            print("No analysis loaded. Run analyze() first.")
            return

        a = self.current_analysis

        print(f"\n{'=' * 70}")
        print(f"  📊 DAILY DIGEST ANALYSIS — {a.date}")
        print(f"{'=' * 70}")

        print(f"\n📈 Всего находок: {a.total_findings} | Высокая релевантность: {len(a.high_relevance_findings)}")

        if a.category_breakdown:
            print("\n📋 Категории:")
            for cat, count in sorted(a.category_breakdown.items(), key=lambda x: -x[1]):
                bar = "█" * count
                print(f"   {cat:<25} {bar} ({count})")

        print(f"\n{'=' * 70}")
        print("  🔥 HIGH RELEVANCE FINDINGS (≥0.5)")
        print(f"{'=' * 70}")

        for f in sorted(a.high_relevance_findings, key=lambda x: -x.relevance_score):
            print(f"\n  [{f.relevance_score:.2f}] {f.title[:60]}")
            print(f"       📂 {f.category} | 📡 {f.source}")
            if f.source_url:
                print(f"       🔗 {f.source_url[:60]}")
            if f.potential_applications:
                print("       ✅ Применения:")
                for app in f.potential_applications[:2]:
                    print(f"          • {app[:70]}")
            if f.risks:
                print("       ⚠️ Риски:")
                for risk in f.risks[:1]:
                    print(f"          • {risk[:70]}")

        print(f"\n{'=' * 70}")
        print("  💡 SUMMARY")
        print(f"{'=' * 70}")
        print(f"\n{a.summary}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Daily Digest Analytics")
    parser.add_argument("--date", type=str, help="Digest date (YYYY-MM-DD)")
    parser.add_argument("--path", type=str, help="Path to digest file")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if args.path:
        path = Path(args.path)
    else:
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        brief_dir = Path(__file__).parent.parent / "daily_brief"
        path = brief_dir / f"brief_{date}.md"
        if not path.exists():
            path = brief_dir / "brief_latest.md"

    analyzer = DigestAnalyzer(str(path))
    analysis = analyzer.analyze()

    if args.json:
        print(analyzer.to_json())
    else:
        analyzer.print_report()
