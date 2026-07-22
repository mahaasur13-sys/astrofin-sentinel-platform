"""amre/meta_questioning.py - ATOM-022: Meta-Questioning Engine
Self-Improvement: Agent generates + refines questions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_SAFE_OPS: dict[str, Any] = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "in": lambda a, b: a in b,
}


def _safe_compare(ctx_val: Any, op: str, val: Any) -> bool:
    """Safe comparison without eval(). Supports > < >= <= == != in."""
    try:
        if op in _SAFE_OPS:
            return bool(_SAFE_OPS[op](ctx_val, val))
        return False
    except Exception:
        return False


@dataclass
class MetaQuestion:
    id: str
    text: str
    category: str
    trigger_condition: str
    weight: float
    times_asked: int = 0
    times_passed: int = 0
    effectiveness_score: float = 0.5


@dataclass
class QuestionEvolution:
    original_text: str
    refined_text: str
    improvement_reason: str
    outcome_before: bool
    outcome_after: bool


class MetaQuestionBank:
    def __init__(self):
        self.questions: list[MetaQuestion] = []
        self.evolutions: list[QuestionEvolution] = []
        self._init_default_questions()

    def _init_default_questions(self):
        defaults = [
            MetaQuestion(
                id="calib_001",
                text="Is my confidence level justified by the quality of signals?",
                category="calibration",
                trigger_condition="confidence > 80",
                weight=1.0,
            ),
            MetaQuestion(
                id="calib_002",
                text="Would I make the same decision if signals were 10% weaker?",
                category="calibration",
                trigger_condition="confidence > 70",
                weight=0.8,
            ),
            MetaQuestion(
                id="bias_001",
                text="Am I reinforcing my existing belief or genuinely updating?",
                category="bias",
                trigger_condition="confidence > 75",
                weight=1.0,
            ),
            MetaQuestion(
                id="uncert_001",
                text="Is high uncertainty due to conflicting or missing data?",
                category="uncertainty",
                trigger_condition="uncertainty_total > 0.5",
                weight=1.0,
            ),
            MetaQuestion(
                id="regime_001",
                text="Is this the right regime for this strategy?",
                category="regime",
                trigger_condition="regime == EXTREME",
                weight=1.0,
            ),
            MetaQuestion(
                id="contra_001",
                text="Is there unresolved conflict between Astro and Fundamental?",
                category="contradiction",
                trigger_condition="astro_signal != fundamental_signal",
                weight=1.0,
            ),
        ]
        self.questions.extend(defaults)

    def get_applicable(self, context: dict[str, Any]) -> list[MetaQuestion]:
        applicable = []
        for q in self.questions:
            if self._matches_condition(q, context):
                applicable.append(q)
        return sorted(applicable, key=lambda x: x.weight, reverse=True)[:3]

    def _matches_condition(self, q: MetaQuestion, ctx: dict) -> bool:
        cond = q.trigger_condition
        if not cond:
            return True
        try:
            for op in [">=", "<=", "==", "!=", ">", "<"]:
                if op in cond:
                    parts = cond.split(op)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val_str = parts[1].strip()
                        try:
                            val = float(val_str)
                        except Exception:
                            val = val_str.strip()
                        ctx_val = ctx.get(key)
                        if ctx_val is None:
                            return False
                        if isinstance(ctx_val, str):
                            ctx_val = ctx_val.strip()
                        return _safe_compare(ctx_val, op, val)
        except Exception:
            pass
        return False

    def refine_question(self, q_id: str, passed: bool, outcome: bool) -> str | None:
        q = next((x for x in self.questions if x.id == q_id), None)
        if not q:
            return None
        q.times_asked += 1
        if passed:
            q.times_passed += 1
        if q.times_asked >= 3:
            q.effectiveness_score = q.times_passed / q.times_asked
        if q.times_asked >= 5 and q.effectiveness_score > 0.8 and not outcome:
            refined = q.text.replace("!", "? (Double-check)")
            if refined != q.text:
                self.evolutions.append(
                    QuestionEvolution(
                        q.text, refined, "High pass but poor outcome", passed, False
                    )
                )
                q.text = refined
                q.weight *= 0.9
                return refined
        return None


class MetaQuestioningEngine:
    def __init__(self):
        self.bank = MetaQuestionBank()
        self.history: list[dict] = []

    def generate_questions(self, ctx: dict) -> list[MetaQuestion]:
        return self.bank.get_applicable(ctx)

    def ask(self, questions: list[MetaQuestion], state: dict) -> list[dict]:
        answers = []
        for q in questions:
            a = self._answer_question(q, state)
            answers.append(
                {
                    "question_id": q.id,
                    "question": q.text,
                    "answer": a["text"],
                    "passed": a["passed"],
                    "adjustment": a["adjustment"],
                }
            )
        return answers

    def _answer_question(self, q: MetaQuestion, state: dict) -> dict:
        conf = state.get("confidence", 50)
        regime = state.get("regime", "NORMAL")
        if q.category == "calibration":
            if conf > 80:
                return {"text": "Overconfident", "passed": False, "adjustment": -10}
            return {"text": "Justified", "passed": True, "adjustment": 0}
        elif q.category == "bias":
            return {"text": "No bias", "passed": True, "adjustment": 0}
        elif q.category == "uncertainty":
            if state.get("uncertainty", {}).get("total", 0) > 0.5:
                return {"text": "High uncertainty", "passed": False, "adjustment": -5}
            return {"text": "Manageable", "passed": True, "adjustment": 0}
        elif q.category == "regime":
            if regime == "EXTREME":
                return {
                    "text": "EXTREME - reduce exposure",
                    "passed": False,
                    "adjustment": -10,
                }
            return {"text": "Appropriate", "passed": True, "adjustment": 0}
        return {"text": "Processed", "passed": True, "adjustment": 0}

    def evaluate(self, answers: list[dict]) -> bool:
        if not answers:
            return True
        return sum(1 for a in answers if a["passed"]) >= len(answers) / 2

    def refine(
        self, questions: list[MetaQuestion], answers: list[dict], outcome: bool
    ) -> list[str]:
        refinements = []
        for q, a in zip(questions, answers, strict=False):
            r = self.bank.refine_question(q.id, a["passed"], outcome)
            if r:
                refinements.append(r)
        return refinements

    def get_statistics(self) -> dict:
        total = len(self.history)
        if total == 0:
            return {"total_sessions": 0}
        passed = sum(1 for h in self.history if h.get("passed", False))
        return {
            "total_sessions": total,
            "pass_rate": round(passed / total, 3),
            "questions": len(self.bank.questions),
            "evolutions": len(self.bank.evolutions),
        }


_META_ENGINE: MetaQuestioningEngine | None = None


def get_meta_engine() -> MetaQuestioningEngine:
    global _META_ENGINE
    if _META_ENGINE is None:
        _META_ENGINE = MetaQuestioningEngine()
    return _META_ENGINE
