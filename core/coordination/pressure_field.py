"""
core/coordination/pressure_field.py — ATOM-COORD-001: Pressure Field Coordination

Sandbox-безопасная версия: никаких embeddings, только сигналы и confidence.

Ограничения (Phase 1):
- НЕ меняет signal (BUY/SELL/NEUTRAL)
- influence_strength ≤ 0.2
- k_neighbors ≤ 5
- БЕЗ embeddings
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.coordination.constants import (
    PRESSURE_FIELD_ENABLED,
    PRESSURE_FIELD_INFLUENCE_STRENGTH,
    PRESSURE_FIELD_K_NEIGHBORS,
    PRESSURE_FIELD_MIN_CONSENSUS,
)

# ─── AgentSignal Dataclass ───────────────────────────────────────────────────────


@dataclass
class AgentSignal:
    """Унифицированный формат сигнала агента."""

    name: str
    signal: str  # BUY | SELL | NEUTRAL
    confidence: float  # raw confidence (0–100)
    eff_conf: float  # effective confidence (после uncertainty + regime)
    weight: float  # вес в гибридном сигнале
    regime: str = "NORMAL"
    uncertainty: float = 0.5
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "signal": self.signal,
            "confidence": self.confidence,
            "eff_conf": self.eff_conf,
            "weight": self.weight,
            "regime": self.regime,
            "uncertainty": self.uncertainty,
        }


# ─── Signal Mapping ─────────────────────────────────────────────────────────────


def signal_to_direction(signal: str) -> int:
    """Map signal → direction vector (+1=BUY, -1=SELL, 0=NEUTRAL)."""
    return {
        "BUY": 1,
        "LONG": 1,
        "STRONG_BUY": 1,
        "SELL": -1,
        "SHORT": -1,
        "STRONG_SELL": -1,
        "NEUTRAL": 0,
        "HOLD": 0,
        "AVOID": 0,
    }.get(signal.upper(), 0)


# ─── Similarity (Sandbox: без embeddings) ───────────────────────────────────────


def compute_similarity(a: AgentSignal, b: AgentSignal) -> float:
    """
    Similarity magnitude между агентами (всегда положительное в magnitude):
    - нейтральный → 0.0 (нет влияния)
    - иначе → 1.0
    """
    if a.signal in ("NEUTRAL", "HOLD", "AVOID") or b.signal in (
        "NEUTRAL",
        "HOLD",
        "AVOID",
    ):
        return 0.0
    return 1.0


# ─── Regime-Aware Influence ──────────────────────────────────────────────────────


def get_regime_multiplier(regime: str) -> float:
    """Regime reception discount: agent в EXTREME получает меньше influence."""
    return {"NORMAL": 1.0, "LOW": 1.0, "HIGH": 0.7, "EXTREME": 0.4}.get(regime, 1.0)


# ─── Core: apply_pressure_field ────────────────────────────────────────────────


def apply_pressure_field(
    agents: list[AgentSignal],
    k_neighbors: int = None,
    influence_strength: float = None,
    min_consensus_pct: float = None,
    enabled: bool = None,
) -> list[AgentSignal]:
    """
    Pressure Field Coordination (sandbox version).

    Influence агента B на агента A:

      influence_B→A = agreement_score(A,B) × conf_B

    Где agreement_score:
      - dir_A == dir_B:  +conf_B   (согласны → A усиливается в своём направлении)
      - dir_A != dir_B:  -conf_B   (несогласны → A теряет conviction)
      - нейтральный:      0         (нет влияния)

    Regime: EXTREME × 0.4 (агент изолирован высокой волатильностью).

    Consensus: снижаем alpha если < min_consensus% согласных.

    Args:
        enabled: Override feature flag. None = use PRESSURE_FIELD_ENABLED env var.

    Returns:
        List[AgentSignal] — обновлённые eff_conf
    """
    if enabled is None:
        _enabled = PRESSURE_FIELD_ENABLED
    else:
        _enabled = enabled

    if not _enabled:
        return agents

    # Cap параметры
    k = min(k_neighbors or PRESSURE_FIELD_K_NEIGHBORS, 5)
    alpha = min(influence_strength or PRESSURE_FIELD_INFLUENCE_STRENGTH, 0.2)
    min_consensus = min_consensus_pct or PRESSURE_FIELD_MIN_CONSENSUS

    if len(agents) < 2:
        return agents

    updated = []

    for i, agent_i in enumerate(agents):
        influences = []
        dir_i = signal_to_direction(agent_i.signal)

        for j, agent_j in enumerate(agents):
            if i == j:
                continue

            sim = compute_similarity(agent_i, agent_j)
            if sim == 0.0:
                continue

            dir_j = signal_to_direction(agent_j.signal)
            conf_b = agent_j.eff_conf / 100.0

            # Agreement: +conf_B если согласны, -conf_B если нет
            if dir_i == 0 or dir_j == 0:
                score = 0.0
            elif dir_i == dir_j:
                score = conf_b  # согласны → A усиливается
            else:
                score = -conf_b  # несогласны → A теряет conviction

            influences.append((j, agent_j.name, score, agent_j.signal))

        if not influences:
            updated.append(agent_i)
            continue

        # Consensus: доля согласных
        agreeing = sum(1 for _, _, score, _ in influences if score > 0)
        consensus_pct = agreeing / len(influences)

        # Топ-k по абсолютному влиянию
        top = sorted(influences, key=lambda x: abs(x[2]), reverse=True)[:k]
        total_influence = sum(score for _, _, score, _ in top)

        # Regime: EXTREME получает меньше influence
        regime_mult = get_regime_multiplier(agent_i.regime)

        # Consensus discount: если consensus < min, снижаем alpha
        effective_alpha = alpha
        if 0 < consensus_pct < min_consensus:
            effective_alpha *= consensus_pct / min_consensus

        # Delta
        delta = effective_alpha * regime_mult * total_influence
        raw_eff = agent_i.eff_conf
        new_eff = raw_eff + delta

        # Clamp
        new_eff = max(0.0, min(100.0, new_eff))

        # Логирование
        if abs(delta) > 0.1:
            top_names = [n for _, n, _, _ in top]
            logger.info(
                f"[PF] %s(%s): %.2f -> %.2f (delta=%+.2f, regime=%s, consensus=%.0f%%, from=%s)",
                agent_i.name, agent_i.signal, raw_eff, new_eff, delta, agent_i.regime, consensus_pct * 100, top_names,
            )

        updated.append(
            AgentSignal(
                name=agent_i.name,
                signal=agent_i.signal,
                confidence=agent_i.confidence,
                eff_conf=new_eff,
                weight=agent_i.weight,
                regime=agent_i.regime,
                uncertainty=agent_i.uncertainty,
                sources=agent_i.sources,
            )
        )

    return updated


# ─── Batch apply с метриками ─────────────────────────────────────────────────


def apply_pressure_field_with_metrics(
    agents: list[AgentSignal],
    **kwargs,
) -> tuple[list[AgentSignal], dict]:
    """
    apply_pressure_field + возвращает метрики для аналитики.

    Returns:
        (updated_agents, metrics_dict)
    """
    before = {a.name: a.eff_conf for a in agents}

    updated = apply_pressure_field(agents, **kwargs)

    after = {a.name: a.eff_conf for a in updated}

    deltas = {name: after[name] - before[name] for name in before}

    metrics = {
        "pressure_field_enabled": PRESSURE_FIELD_ENABLED,
        "agents_count": len(agents),
        "k_neighbors": kwargs.get("k_neighbors", PRESSURE_FIELD_K_NEIGHBORS),
        "influence_strength": kwargs.get("influence_strength", PRESSURE_FIELD_INFLUENCE_STRENGTH),
        "avg_delta": sum(abs(v) for v in deltas.values()) / len(deltas) if deltas else 0,
        "max_delta": max(abs(v) for v in deltas.values()) if deltas else 0,
        "deltas": deltas,
    }

    return updated, metrics
