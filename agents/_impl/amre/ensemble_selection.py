"""amre/ensemble_selection.py — Ensemble diversity selection"""

from __future__ import annotations

from typing import Any


def select_ensemble(signals: list[Any], target_size: int = 5) -> list[Any]:
    if len(signals) <= target_size:
        return signals
    by_cat: dict[str, list[Any]] = {}
    for s in signals:
        cat = (
            s.get("category", "other")
            if isinstance(s, dict)
            else getattr(s, "category", "other")
        )
        by_cat.setdefault(cat, []).append(s)
    result = []
    cats = list(by_cat.keys())
    for i in range(min(target_size, len(signals))):
        cat = cats[i % len(cats)]
        if by_cat[cat]:
            result.append(by_cat[cat].pop(0))
    return result


def ensemble_diversity_score(signals: list[Any]) -> float:
    if len(signals) < 2:
        return 0.0
    signal_types = [s.get("signal", "") for s in signals if isinstance(s, dict)]
    unique = len(set(signal_types))
    return min(1.0, unique / len(signals))


def select_ensemble_by_confidence(signals: list[Any], top_k: int = 5) -> list[Any]:
    scored = [
        (
            s,
            (
                s.get("confidence", 50)
                if isinstance(s, dict)
                else getattr(s, "confidence", 50)
            ),
        )
        for s in signals
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in scored[:top_k]]
