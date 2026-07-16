# ATOM-R-041 Unified Data Contract
#
# Single source of truth for Idea structure. All modules that touch
# Idea must import from here. No dict/dataclass divergence.
#
# Lifecycle: proposed -> scored -> injected -> tested -> accepted/rejected

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum


class IdeaStatus(Enum):
    PROPOSED = "proposed"
    SCORED = "scored"
    INJECTED = "injected"
    TESTED = "tested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class IdeaStage(Enum):
    QUALITY_GATE = "quality_gate"
    KARL_INJECT = "karl_inject"
    TRAJECTORY = "trajectory"
    OUTCOME = "outcome"


SCORE_THRESHOLD = 0.5


@dataclass
class Idea:
    id: str
    source: str
    text: str
    category: str
    status: str
    score: float
    linked_trajectories: list[str] = field(default_factory=list)
    impact_score: float = 0.0
    created_at: str = ""
    tested_at: str | None = None
    evaluated_at: str | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.linked_trajectories is None:
            self.linked_trajectories = []
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Idea":
        d.pop("_id", None)
        d.pop("id", None)
        return Idea(**d)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        setattr(self, key, value)

    def keys(self):
        return [
            "id",
            "source",
            "text",
            "category",
            "status",
            "score",
            "linked_trajectories",
            "impact_score",
            "created_at",
            "tested_at",
            "evaluated_at",
            "tags",
        ]

    def items(self):
        return dict(zip(self.keys(), [getattr(self, k) for k in self.keys()], strict=False))

    def stage(self) -> IdeaStage:
        if self.status == IdeaStatus.PROPOSED.value:
            return IdeaStage.QUALITY_GATE
        elif self.status == IdeaStatus.SCORED.value:
            return IdeaStage.KARL_INJECT
        elif self.status == IdeaStatus.INJECTED.value:
            return IdeaStage.TRAJECTORY
        else:
            return IdeaStage.OUTCOME

    def is_quality_passed(self) -> bool:
        return self.score >= SCORE_THRESHOLD

    def is_terminal(self) -> bool:
        return self.status in (IdeaStatus.ACCEPTED.value, IdeaStatus.REJECTED.value)


__all__ = ["Idea", "IdeaStatus", "IdeaStage", "SCORE_THRESHOLD"]
