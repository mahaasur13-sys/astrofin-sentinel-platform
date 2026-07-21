"""core/ensemble_voting.py — Ensemble Voting Engine (Master Agent)

Sprint 6: Production Readiness & Ensemble Logic.
Взвешенное голосование 13 агентов с учётом:
  - весов агентов (из AGENTS.md)
  - confidence каждого сигнала
  - HMM-режима рынка
  - Nakshatra-фильтра (soft/hard constraint)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Signal(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    HOLD = "HOLD"

    def to_numeric(self) -> float:
        return {Signal.LONG: 1.0, Signal.SHORT: -1.0, Signal.NEUTRAL: 0.0, Signal.HOLD: 0.0}[self]


HYBRID_WEIGHTS: dict[str, float] = {
    "fundamental":     0.1754,
    "quant":           0.1754,
    "macro":           0.1316,
    "options_flow":    0.1316,
    "sentiment":       0.0877,
    "technical":       0.0877,
    "bull":            0.0439,
    "bear":            0.0439,
    "electoral":       0.0263,
    "bradley":         0.0263,
    "gann":            0.0263,
    "cycle":           0.0439,
    "market_analyst":  -1.0,  # informational only, не голосует
}


REGIME_MULTIPLIER: dict[str, float] = {
    "LOW":      1.2,
    "NORMAL":   1.0,
    "HIGH":     0.7,
    "EXTREME":  0.4,
}


@dataclass
class AgentVote:
    agent_name: str
    signal: Signal
    confidence: float
    reasoning: str = ""


@dataclass
class EnsembleResult:
    signal: Signal
    score: float             # weighted composite [-1.0 … +1.0]
    confidence: float        # 0–100%
    votes: list[AgentVote] = field(default_factory=list)
    nakshatra_risk: float = 1.0
    nakshatra: str = ""
    veto_reason: str = ""
    regime: str = "NORMAL"

    @property
    def is_consensus(self) -> bool:
        longs = sum(1 for v in self.votes if v.signal == Signal.LONG)
        shorts = sum(1 for v in self.votes if v.signal == Signal.SHORT)
        return abs(longs - shorts) >= len(self.votes) - 2

    def summary(self) -> str:
        lines = [
            "═" * 72,
            f"  ENSEMBLE VOTE: {self.signal.value} (score={self.score:+.3f}, conf={self.confidence:.0f}%)",
            f"  Regime: {self.regime} | Nakshatra: {self.nakshatra} ×{self.nakshatra_risk:.2f}",
        ]
        if self.veto_reason:
            lines.append(f"  ⛔ VETO: {self.veto_reason}")
        lines.append("─" * 72)
        for v in self.votes:
            arrow = {"LONG": "🟢", "SHORT": "🔴", "NEUTRAL": "⚪", "HOLD": "⏸️"}[v.signal.value]
            lines.append(f"  {arrow} {v.agent_name:20s} {v.signal.value:>8s} ({v.confidence:.0f}%) — {v.reasoning[:60]}")
        lines.append("═" * 72)
        return "\n".join(lines)


@dataclass
class EnsembleVotingEngine:
    weights: dict[str, float] = field(default_factory=lambda: dict(HYBRID_WEIGHTS))
    nakshatra_hard_veto: bool = True
    consensus_boost: float = 0.10

    def vote(
        self,
        agent_results: dict[str, dict],
        regime: str = "NORMAL",
        nakshatra: str = "",
    ) -> EnsembleResult:
        """
        Принимает словарь {agent_name: result_dict} от 13 агентов,
        вычисляет взвешенный ансамблевый сигнал.

        Каждый result_dict должен содержать вложенный сигнал:
            {"<type>_signal": {"signal": "LONG/SHORT/NEUTRAL/HOLD", "confidence": 85, "reasoning": "..."}}
        или ключ "signal" на верхнем уровне.

        Veto-логика:
          - Если Nakshatra в AVOID-списке и nakshatra_hard_veto=True → HOLD
          - Если kill_switch_active у риск-агента → HOLD
          - Если 2+ агентов с confidence < 40% → снижаем уверенность на 25%
        """
        if not agent_results:
            return EnsembleResult(signal=Signal.NEUTRAL, score=0.0, confidence=0.0, nakshatra=nakshatra)

        votes: list[AgentVote] = []
        for name, result in agent_results.items():
            sig, conf, reason = self._extract_signal(result)
            votes.append(AgentVote(agent_name=name, signal=sig, confidence=conf, reasoning=reason))

        result = self._compute_weighted(votes, regime, nakshatra)
        return result

    def _extract_signal(self, result):
        if not isinstance(result, dict):
            return Signal.NEUTRAL, 0.0, str(result)[:80]
        for v in result.values():
            if isinstance(v, dict):
                raw = v.get("signal", "NEUTRAL")
                conf = v.get("confidence", 50)
                reason = v.get("reasoning", "")[:80]
                try:
                    sig = Signal(raw.upper())
                except ValueError:
                    sig = Signal.NEUTRAL
                return sig, float(conf), reason
        raw = result.get("signal", "NEUTRAL")
        conf = result.get("confidence", 50)
        reason = result.get("reasoning", "")[:80]
        try:
            sig = Signal(raw.upper())
        except ValueError:
            sig = Signal.NEUTRAL
        return sig, float(conf), reason

    def _compute_weighted(
        self, votes: list[AgentVote], regime: str, nakshatra: str
    ) -> EnsembleResult:
        from trading.vedic.nakshatra_risk import (
            get_nakshatra_multiplier,
            get_election_grade,
            is_dangerous_nakshatra,
        )

        reg_mult = REGIME_MULTIPLIER.get(regime.upper(), 1.0)
        nak_mult = get_nakshatra_multiplier(nakshatra) if nakshatra else 1.0
        nak_grade = get_election_grade(nakshatra) if nakshatra else None

        veto_reason = ""
        if nakshatra and is_dangerous_nakshatra(nakshatra) and self.nakshatra_hard_veto:
            veto_reason = f"Nakshatra {nakshatra} is AVOID (risk ×{nak_mult:.2f}) — hard veto"
            return EnsembleResult(
                signal=Signal.HOLD, score=0.0, confidence=0.90,
                votes=votes, nakshatra_risk=nak_mult, nakshatra=nakshatra,
                veto_reason=veto_reason, regime=regime,
            )

        total_weight = 0.0
        weighted_score = 0.0
        weighted_conf = 0.0
        low_conf_count = 0

        for v in votes:
            w = self.weights.get(v.agent_name, 0.0)
            if w <= 0:
                continue
            cf = max(0.0, min(100.0, v.confidence)) / 100.0
            if cf < 0.40:
                low_conf_count += 1
            w_conf = w * cf * reg_mult * nak_mult
            weighted_score += v.signal.to_numeric() * w_conf
            weighted_conf += w_conf
            total_weight += w

        if total_weight == 0:
            return EnsembleResult(signal=Signal.NEUTRAL, score=0.0, confidence=0.0,
                                 votes=votes, nakshatra_risk=nak_mult, nakshatra=nakshatra, regime=regime)

        normalizer = total_weight if total_weight > 0 else 1.0
        avg_conf = (weighted_conf / normalizer) * 100.0

        if low_conf_count >= 2:
            avg_conf *= 0.75

        if nak_grade == "avoid" and not self.nakshatra_hard_veto:
            avg_conf *= 0.60

        if abs(weighted_score) > 0.30:
            avg_conf += self.consensus_boost * 100

        avg_conf = max(10.0, min(100.0, avg_conf))

        if weighted_score > 0.15:
            final_signal = Signal.LONG
        elif weighted_score < -0.15:
            final_signal = Signal.SHORT
        else:
            final_signal = Signal.NEUTRAL

        return EnsembleResult(
            signal=final_signal, score=round(weighted_score, 4),
            confidence=round(avg_conf, 1), votes=votes,
            nakshatra_risk=nak_mult, nakshatra=nakshatra,
            veto_reason=veto_reason, regime=regime,
        )


def ensemble_from_13_agents(results: dict[str, dict], regime: str = "NORMAL", nakshatra: str = "") -> EnsembleResult:
    """Convenience: проголосовать 13 агентов через EnsembleVotingEngine."""
    engine = EnsembleVotingEngine()
    return engine.vote(results, regime, nakshatra)
