

class ConflictResolutionMatrix:
    """
    Formal resolution of inter-layer control conflicts.
    Precedence matrix: higher pairwise weight wins.
    """

    def __init__(self) -> None:
        self._matrix: Dict[tuple[str, str], float] = {}

    def set_priority(self, a: str, b: str, weight: float) -> None:
        """Set winning weight of 'a' over 'b'."""
        self._matrix[(a, b)] = weight

    def resolve(self, candidates: list[str]) -> str:
        if not candidates:
            raise ValueError("No candidates provided")
        if len(candidates) == 1:
            return candidates[0]
        best: str | None = None
        best_score = float("-inf")
        for c in candidates:
            score = 0.0
            for other in candidates:
                if c == other:
                    continue
                score += self._matrix.get((c, other), 0.0)
            if score > best_score:
                best_score = score
                best = c
        return best if best is not None else candidates[0]

    def pairwise_winner(self, a: str, b: str) -> str:
        """Return the higher-priority layer between two."""
        w = self._matrix.get((a, b), 0.0) - self._matrix.get((b, a), 0.0)
        return a if w > 0 else b
