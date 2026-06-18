"""amre/idea_buffer_integration.py — ATOM-R-041: Idea → KARL Buffer Integration
Встраивает Idea в KARL replay buffer lifecycle.

Flow:
    Idea (scored) → inject_idea() → BufferEntry created → backtest → Trajectory
                 → mark_tested()   → trajectory linked
                 → evaluate_idea() → impact_score recorded

Usage:
    from agents._impl.amre.idea_buffer_integration import (
        inject_idea_to_buffer,
        link_trajectory_to_idea,
        get_buffer_entries_for_idea,
    )
"""
from __future__ import annotations


from core.idea_model import Idea, IdeaStatus

# ─── Forward-declare to avoid circular import ─────────────────────────────────
# ReplayBuffer and BufferEntry live in replay_buffer.py
# We only interact through a thin adapter that works with Idea dicts/dclasses


class BufferEntry:
    """Wrapper that adapts Idea into a buffer-compatible entry."""

    def __init__(
        self,
        idea: Idea,
        trajectory_id: str | None = None,
        reward: float = 0.0,
        market_context: dict = None,
    ):
        self.idea_id = idea.id
        self.idea_dict = idea.to_dict()  # Freeze snapshot at entry time
        self.trajectory_id = trajectory_id
        self.reward = reward
        self.market_context = market_context or {}
        self.created_at = idea.created_at


# ─── KARL Buffer Adapter ────────────────────────────────────────────────────────
# Thin adapter that bridges Idea lifecycle → ReplayBuffer
# The actual ReplayBuffer lives in replay_buffer.py

_KARL_BUFFER: list[BufferEntry] = []


def inject_idea_to_buffer(idea: Idea, market_context: dict = None) -> str:
    """
    Inject a scored Idea into the KARL replay buffer.
    Creates a BufferEntry snapshot and returns the trajectory_id.

    Returns:
        trajectory_id: str — used to link backtest results
    """
    import uuid

    trajectory_id = f"TRAJ-{uuid.uuid4().hex[:8].upper()}"

    entry = BufferEntry(
        idea=idea,
        trajectory_id=trajectory_id,
        reward=0.0,
        market_context=market_context or {},
    )
    _KARL_BUFFER.append(entry)
    return trajectory_id


def link_trajectory_to_idea(
    idea_id: str,
    trajectory_id: str,
    reward: float = 0.0,
    trajectory_data: dict = None,
) -> bool:
    """
    Link a completed trajectory back to its Idea.
    Updates the buffer entry with reward and trajectory data.

    Returns:
        True if idea_id found in buffer, False otherwise
    """
    for entry in _KARL_BUFFER:
        if entry.idea_id == idea_id and entry.trajectory_id == trajectory_id:
            entry.reward = reward
            if trajectory_data:
                entry.trajectory_data = trajectory_data
            return True
    return False


def get_buffer_entries_for_idea(idea_id: str) -> list[BufferEntry]:
    """Get all buffer entries linked to an Idea."""
    return [e for e in _KARL_BUFFER if e.idea_id == idea_id]


def get_all_buffer_entries() -> list[BufferEntry]:
    """Get all buffer entries (for diagnostics)."""
    return list(_KARL_BUFFER)


def clear_buffer():
    """Clear the in-memory buffer (for testing/reset)."""
    _KARL_BUFFER.clear()


# ─── Idea → KARL Workflow ──────────────────────────────────────────────────────


def karl_inject_idea(
    idea: Idea,
    market_context: dict = None,
) -> dict:
    """
    Full injection workflow:
    1. Validate idea is in scored status
    2. Create buffer entry
    3. Return trajectory_id for tracking

    Returns:
        dict with trajectory_id and buffer_status
    """
    if idea.status != IdeaStatus.SCORED.value:
        return {
            "success": False,
            "error": f"Cannot inject idea in status={idea.status}. Must be SCORED.",
            "trajectory_id": None,
        }

    trajectory_id = inject_idea_to_buffer(idea, market_context)

    return {
        "success": True,
        "idea_id": idea.id,
        "trajectory_id": trajectory_id,
        "buffer_status": "injected",
        "next_step": "run_backtest_and_call link_trajectory_to_idea()",
    }


def karl_evaluate_idea(
    idea: Idea,
    trajectory_id: str,
    reward: float,
    trajectory_data: dict = None,
) -> dict:
    """
    Full evaluation workflow:
    1. Link trajectory to idea
    2. Determine accept/reject
    3. Return impact result

    Returns:
        dict with outcome summary
    """
    linked = link_trajectory_to_idea(
        idea_id=idea.id,
        trajectory_id=trajectory_id,
        reward=reward,
        trajectory_data=trajectory_data,
    )

    if not linked:
        return {
            "success": False,
            "error": f"No buffer entry for idea={idea.id}, trajectory={trajectory_id}",
        }

    accepted = reward > 0
    impact_score = round(reward, 4)

    return {
        "success": True,
        "idea_id": idea.id,
        "trajectory_id": trajectory_id,
        "reward": reward,
        "impact_score": impact_score,
        "status": IdeaStatus.ACCEPTED.value if accepted else IdeaStatus.REJECTED.value,
        "next_step": "call evaluate_idea() in idea_tracker to persist",
    }


# ─── Self-Questioning Integration ───────────────────────────────────────────────


def ideas_to_self_questioning_prompts(
    ideas: list[Idea],
    max_ideas: int = 5,
) -> list[str]:
    """
    ATOM-R-041 + ATOM-016 bridge:
    Convert scored ideas into self-questioning prompts for synthesis.

    Seeds the self-questioning engine with external ideas from the pipeline.
    """
    scored = [i for i in ideas if i.status == IdeaStatus.SCORED.value]
    scored.sort(key=lambda x: x.score, reverse=True)

    prompts = []
    for idea in scored[:max_ideas]:
        prompts.append(
            f"Does this improve system performance? {idea.text} (source={idea.source}, category={idea.category})"
        )

    return prompts


# ─── Buffer Stats ───────────────────────────────────────────────────────────────


def get_buffer_stats() -> dict:
    """Return buffer diagnostics for KPI dashboard."""
    if not _KARL_BUFFER:
        return {"total_entries": 0, "total_rewards": 0, "avg_reward": 0}

    rewards = [e.reward for e in _KARL_BUFFER if e.reward != 0]
    return {
        "total_entries": len(_KARL_BUFFER),
        "entries_with_rewards": len(rewards),
        "total_rewards": round(sum(rewards), 4) if rewards else 0,
        "avg_reward": round(sum(rewards) / len(rewards), 4) if rewards else 0,
        "ideas": list(set(e.idea_id for e in _KARL_BUFFER)),
    }
