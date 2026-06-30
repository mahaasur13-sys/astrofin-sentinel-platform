

class SystemWideGainScheduler:
    """
    Prevents gain explosion across multiple feedback loops.
    Normalizes so total absolute gain <= max_global_gain.
    """

    def __init__(self, max_global_gain: float = 2.0) -> None:
        self.max_global_gain = max_global_gain

    def normalize(self, gains: dict[str, float]) -> dict[str, float]:
        total = sum(abs(g) for g in gains.values()) or 1.0
        scale = min(1.0, self.max_global_gain / total)
        return {k: v * scale for k, v in gains.items()}

    def normalize_and_cap(self, gains: dict[str, float], per_layer_cap: float = 1.5) -> dict[str, float]:
        """Normalize then cap each layer gain individually."""
        normalized = self.normalize(gains)
        return {k: max(-per_layer_cap, min(per_layer_cap, v)) for k, v in normalized.items()}
