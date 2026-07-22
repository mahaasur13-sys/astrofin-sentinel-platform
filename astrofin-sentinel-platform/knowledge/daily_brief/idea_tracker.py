#!/usr/bin/env python3
"""
ATOM-R-041: Idea → Outcome Tracking

Жизненный цикл идеи:
- proposed: идея из daily_brief или пользователя
- scored: прошла quality filter
- injected: добавлена в KARL buffer
- tested: траектории созданы
- accepted: impact_score > 0
- rejected: impact_score <= 0

Usage:
    python knowledge/daily_brief/idea_tracker.py --list              # показать все идеи
    python knowledge/daily_brief/idea_tracker.py --pending           # идеи готовые к тесту
    python knowledge/daily_brief/idea_tracker.py --kpi               # показать KPI
    python knowledge/daily_brief/idea_tracker.py --inject IDEA_ID    # внедрить идею в buffer
    python knowledge/daily_brief/idea_tracker.py --eval IDEA_ID --reward 0.15  # оценить
    python knowledge/daily_brief/idea_tracker.py --import IDEAS_JSON  # импорт из JSON
"""

from __future__ import annotations
import argparse
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import logging
log = logging.getLogger(__name__)



class IdeaStatus(Enum):
    PROPOSED = "proposed"
    SCORED = "scored"
    INJECTED = "injected"
    TESTED = "tested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


IDEAS_DIR = Path(__file__).parent
IDEAS_FILE = IDEAS_DIR / "ideas.jsonl"
IDEAS_INDEX = IDEAS_DIR / "ideas_index.json"
SCORE_THRESHOLD = 0.5


@dataclass
class Idea:
    id: str
    source: str
    text: str
    category: str
    status: str
    score: float
    linked_trajectories: list
    impact_score: float
    created_at: str
    tested_at: Optional[str] = None
    evaluated_at: Optional[str] = None
    tags: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        d.pop("_id", None)
        return Idea(**d)


def load_ideas() -> list:
    """Load all ideas from storage."""
    if not IDEAS_FILE.exists():
        return []
    ideas = []
    with open(IDEAS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                ideas.append(Idea.from_dict(json.loads(line)))
    return ideas


def save_idea(idea: Idea):
    """Append idea to storage."""
    with open(IDEAS_FILE, "a") as f:
        f.write(json.dumps(idea.to_dict(), ensure_ascii=False) + "\n")


def update_idea(updated_idea: Idea):
    """Update idea in storage (rewrite file)."""
    ideas = load_ideas()
    for i, idea in enumerate(ideas):
        if idea.id == updated_idea.id:
            ideas[i] = updated_idea
            break
    else:
        ideas.append(updated_idea)

    with open(IDEAS_FILE, "w") as f:
        for idea in ideas:
            f.write(json.dumps(idea.to_dict(), ensure_ascii=False) + "\n")


def score_idea(text: str, category: str = "") -> float:
    """
    Quality filter — scoring idea by relevance.

    Positive signals:
    - API, integration keywords → +1.0
    - model, architecture, algorithm → +1.5
    - tool, framework, library → +0.8
    - performance, optimization → +1.2

    Negative signals:
    - marketing, community, social → -1.0
    - vague/generic → -0.5
    """
    text_lower = text.lower()
    score = 0.0

    positive_keywords = {
        "api": 1.0,
        "integration": 1.0,
        "model": 1.5,
        "architecture": 1.5,
        "algorithm": 1.5,
        "tool": 0.8,
        "framework": 0.8,
        "library": 0.8,
        "performance": 1.2,
        "optimization": 1.2,
        "efficiency": 1.2,
        "reward": 1.0,
        "policy": 1.0,
        "trajectory": 0.8,
        "agent": 0.8,
        "multi-agent": 1.5,
        # Research
        "arxiv": 1.0,
        "research": 0.8,
        "paper": 0.8,
        "coordination": 1.0,
    }

    negative_keywords = {
        "marketing": -1.0,
        "social media": -1.0,
        "community": -0.3,
        "post": -0.3,
        "tweet": -0.8,
        "reddit": -0.3,
        "hacker news": -0.3,
        "vague": -0.5,
        "maybe": -0.3,
    }

    for kw, weight in positive_keywords.items():
        if kw in text_lower:
            score += weight

    for kw, weight in negative_keywords.items():
        if kw in text_lower:
            score += weight

    return round(score, 2)


def create_idea(text: str, source: str, category: str = "GENERAL") -> Idea:
    """Create new idea with scoring."""
    idea_id = f"IDEA-{uuid.uuid4().hex[:8].upper()}"
    score = score_idea(text, category)

    idea = Idea(
        id=idea_id,
        source=source,
        text=text,
        category=category,
        status=IdeaStatus.PROPOSED.value,
        score=score,
        linked_trajectories=[],
        impact_score=0.0,
        created_at=datetime.now().isoformat(),
        tags=[],
    )

    if score >= SCORE_THRESHOLD:
        idea.status = IdeaStatus.SCORED.value

    return idea


def inject_idea(idea_id: str, trajectory_id: str = None) -> Optional[Idea]:
    """
    Inject idea into KARL buffer.
    Returns updated idea or None if not found.
    """
    ideas = load_ideas()
    for idea in ideas:
        if idea.id == idea_id:
            idea.status = IdeaStatus.INJECTED.value
            if trajectory_id:
                idea.linked_trajectories.append(trajectory_id)
            update_idea(idea)
            return idea
    return None


def mark_tested(idea_id: str, trajectory_ids: list) -> Optional[Idea]:
    """Mark idea as tested with linked trajectories."""
    ideas = load_ideas()
    for idea in ideas:
        if idea.id == idea_id:
            idea.status = IdeaStatus.TESTED.value
            idea.linked_trajectories.extend(trajectory_ids)
            idea.tested_at = datetime.now().isoformat()
            update_idea(idea)
            return idea
    return None


def evaluate_idea(idea_id: str, reward: float) -> Optional[Idea]:
    """
    Evaluate idea by final reward from trajectory.
    Updates impact_score and sets accepted/rejected status.
    """
    ideas = load_ideas()
    for idea in ideas:
        if idea.id == idea_id:
            idea.impact_score = round(reward, 4)
            idea.evaluated_at = datetime.now().isoformat()

            if reward > 0:
                idea.status = IdeaStatus.ACCEPTED.value
            else:
                idea.status = IdeaStatus.REJECTED.value

            update_idea(idea)
            return idea
    return None


def get_ideas_by_status(status: str) -> list:
    """Filter ideas by status."""
    ideas = load_ideas()
    return [i for i in ideas if i.status == status]


def get_kpi() -> dict:
    """Calculate KPI for idea system."""
    ideas = load_ideas()

    kpi = {
        "ideas_total": len(ideas),
        "ideas_proposed": sum(
            1 for i in ideas if i.status == IdeaStatus.PROPOSED.value
        ),
        "ideas_scored": sum(1 for i in ideas if i.status == IdeaStatus.SCORED.value),
        "ideas_injected": sum(
            1 for i in ideas if i.status == IdeaStatus.INJECTED.value
        ),
        "ideas_tested": sum(1 for i in ideas if i.status == IdeaStatus.TESTED.value),
        "ideas_accepted": sum(
            1 for i in ideas if i.status == IdeaStatus.ACCEPTED.value
        ),
        "ideas_rejected": sum(
            1 for i in ideas if i.status == IdeaStatus.REJECTED.value
        ),
    }

    tested_ideas = [i for i in ideas if i.impact_score != 0.0]
    if tested_ideas:
        kpi["impact_mean"] = round(
            sum(i.impact_score for i in tested_ideas) / len(tested_ideas), 4
        )
        kpi["acceptance_rate"] = (
            round(kpi["ideas_accepted"] / len(tested_ideas), 4) if tested_ideas else 0
        )
    else:
        kpi["impact_mean"] = 0.0
        kpi["acceptance_rate"] = 0.0

    return kpi


def list_ideas(status_filter: str = None, limit: int = 50):
    """List all ideas with optional status filter."""
    ideas = load_ideas()
    if status_filter:
        ideas = [i for i in ideas if i.status == status_filter]

    ideas = sorted(ideas, key=lambda x: x.created_at, reverse=True)[:limit]

    if not ideas:
        log.info("No ideas found.")
        return

    log.info(f"\n{'=== Idea Tracker ===':^60}")
    log.info(f"{'ID':<16} {'Status':<10} {'Score':>6} {'Impact':>8} {'Category':<20}")
    log.info("-" * 70)

    for idea in ideas:
        log.info(
            f"  {idea.id:<14} {idea.status:<10} {idea.score:>6.2f} {idea.impact_score:>8.4f} {idea.category:<20}"
        )

    log.info(f"\nTotal: {len(ideas)} ideas")


def show_idea(idea_id: str):
    """Show detailed idea info."""
    ideas = load_ideas()
    for idea in ideas:
        if idea.id == idea_id:
            log.info(f"\n{'=' * 60}")
            log.info(f"  {idea.id} — {idea.category}")
            log.info(f"{'=' * 60}")
            log.info(f"\nStatus:    {idea.status}")
            log.info(f"Score:     {idea.score:.2f}")
            log.info(f"Impact:    {idea.impact_score:.4f}")
            log.info(f"Source:    {idea.source}")
            log.info(f"Created:   {idea.created_at}")
            if idea.tested_at:
                log.info(f"Tested:    {idea.tested_at}")
            if idea.evaluated_at:
                log.info(f"Evaluated: {idea.evaluated_at}")
            log.info(f"\nText:\n  {idea.text}")
            if idea.linked_trajectories:
                log.info(f"\nTrajectories: {', '.join(idea.linked_trajectories)}")
            return

    log.info(f"Idea {idea_id} not found.")


def main():
    parser = argparse.ArgumentParser(description="ATOM-R-041: Idea → Outcome Tracking")
    parser.add_argument("--list", action="store_true", help="List all ideas")
    parser.add_argument(
        "--pending", action="store_true", help="Show ideas ready for testing"
    )
    parser.add_argument("--kpi", action="store_true", help="Show KPI dashboard")
    parser.add_argument("--inject", type=str, help="Inject idea into KARL buffer")
    parser.add_argument("--eval", type=str, help="Evaluate idea by ID")
    parser.add_argument("--reward", type=float, help="Reward value for --eval")
    parser.add_argument("--add", type=str, help="Add new idea text")
    parser.add_argument("--source", type=str, default="manual", help="Source for --add")
    parser.add_argument(
        "--category", type=str, default="GENERAL", help="Category for --add"
    )
    parser.add_argument("--status", type=str, help="Filter by status for --list")
    parser.add_argument("--show", type=str, help="Show idea details")
    parser.add_argument("--import-json", type=str, help="Import ideas from JSON file")

    args = parser.parse_args()

    if args.add:
        idea = create_idea(args.add, args.source, args.category)
        save_idea(idea)
        status_note = (
            "(scored)" if idea.status == IdeaStatus.SCORED.value else "(low score)"
        )
        log.info(f"Created: {idea.id} {status_note}")
        log.info(f"  Score: {idea.score:.2f} (threshold: {SCORE_THRESHOLD})")
        return

    if args.import_json:
        path = Path(args.import_json)
        if not path.exists():
            log.info(f"File not found: {path}")
            return

        data = json.loads(path.read_text())
        if isinstance(data, list):
            for item in data:
                text = item.get("text", item.get("prompt", ""))
                source = item.get("source", "import")
                category = item.get("category", "IMPORTED")
                idea = create_idea(text, source, category)
                save_idea(idea)
            log.info(f"Imported {len(data)} ideas.")
        return

    if args.show:
        show_idea(args.show)
        return

    if args.inject:
        idea = inject_idea(args.inject)
        if idea:
            log.info(f"Injected: {idea.id} → {idea.status}")
        else:
            log.info(f"Idea {args.inject} not found.")
        return

    if args.eval:
        if args.reward is None:
            log.info("--reward required for evaluation")
            return
        idea = evaluate_idea(args.eval, args.reward)
        if idea:
            log.info(f"Evaluated: {idea.id}")
            log.info(f"  Status: {idea.status}")
            log.info(f"  Impact: {idea.impact_score:.4f}")
        else:
            log.info(f"Idea {args.eval} not found.")
        return

    if args.kpi:
        kpi = get_kpi()
        log.info(f"\n{'=== ATOM-R-041 KPI ===':^60}")
        log.info(f"  Total ideas:      {kpi['ideas_total']}")
        log.info(f"  Proposed:          {kpi['ideas_proposed']}")
        log.info(f"  Scored (pass):     {kpi['ideas_scored']}")
        log.info(f"  Injected:          {kpi['ideas_injected']}")
        log.info(f"  Tested:            {kpi['ideas_tested']}")
        log.info(f"  Accepted:          {kpi['ideas_accepted']}")
        log.info(f"  Rejected:          {kpi['ideas_rejected']}")
        log.info(f"  Impact mean:       {kpi['impact_mean']:.4f}")
        log.info(f"  Acceptance rate:   {kpi['acceptance_rate']:.1%}")
        return

    if args.pending:
        scored = get_ideas_by_status(IdeaStatus.SCORED.value)
        injected = get_ideas_by_status(IdeaStatus.INJECTED.value)
        tested = get_ideas_by_status(IdeaStatus.TESTED.value)

        log.info(f"\n{'=== Pending Ideas ===':^60}")
        log.info(f"\n  Ready to inject (scored):   {len(scored)}")
        for i in scored[:5]:
            log.info(f"    {i.id}: {i.text[:60]}...")

        log.info(f"\n  Ready to test (injected):  {len(injected)}")
        for i in injected[:5]:
            log.info(f"    {i.id}: {i.text[:60]}...")

        log.info(f"\n  Ready to evaluate (tested): {len(tested)}")
        for i in tested[:5]:
            log.info(f"    {i.id}: impact={i.impact_score:.4f}")
        return

    if args.list:
        list_ideas(status_filter=args.status)
        return

    # Default: show KPI
    kpi = get_kpi()
    log.info(f"\n{'=== ATOM-R-041 ===':^60}")
    log.info(
        f"  Total: {kpi['ideas_total']} | Accepted: {kpi['ideas_accepted']} | Impact: {kpi['impact_mean']:.4f}"
    )
    log.info("\nUse --help for commands.")


if __name__ == "__main__":
    main()
