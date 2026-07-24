"""core/council/council.py - AstroCouncil: Multi-Agent Voting System"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from core.council.types import AGENT_WEIGHTS, CouncilResult, Signal


def _signal_val(s: Signal) -> float:
    return {Signal.LONG: 1.0, Signal.SHORT: -1.0, Signal.NEUTRAL: 0.0}[s]


def compute_weighted_signal(members, weights):
    if not members:
        return 0.0, "no_members"
    total_w = sum(x.weight for x in members)
    wsum = sum(_signal_val(x.vote) * x.confidence * x.weight for x in members)
    norm = wsum / total_w if total_w > 0 else 0.0
    return norm, f"weighted={norm:.3f} from {len(members)} members"


def resolve_conflict(members):
    longs = shorts = neutrals = 0
    for x in members:
        if x.vote == Signal.LONG:
            longs += 1
        elif x.vote == Signal.SHORT:
            shorts += 1
        else:
            neutrals += 1
    n = len(members)
    dissent = []
    if longs > shorts and longs >= neutrals:
        final, consensus = Signal.LONG, longs / n
    elif shorts > longs and shorts >= neutrals:
        final, consensus = Signal.SHORT, shorts / n
    else:
        final, consensus = Signal.NEUTRAL, max(longs, shorts, neutrals) / n
        for x in members:
            if x.vote != Signal.NEUTRAL:
                dissent.append({"member": x.name, "vote": x.vote.value})
    return final, consensus, dissent


def build_council_result(symbol, members, deliberation=""):
    ws, dlog = compute_weighted_signal(members, None)
    deliberation += dlog + "; "
    final_signal, consensus, dissent = resolve_conflict(members)
    deliberation += f"final={final_signal.value} consensus={consensus:.2f}"
    return CouncilResult(
        timestamp=datetime.utcnow(),
        symbol=symbol,
        weighted_signal=ws,
        final_signal=final_signal,
        confidence=int(consensus * 100),
        consensus=consensus,
        members=members,
        deliberation=deliberation,
        conflict_resolved=True,
        dissent=dissent,
    )


@dataclass
class AstroCouncil:
    name: str = "AstroCouncil"
    members: list = field(default_factory=list)
    weights: dict = field(default_factory=lambda: AGENT_WEIGHTS.copy())

    def add_member(self, member):
        self.members.append(member)

    def vote(self, symbol, deliberation=""):
        deliberation += f"Council: {len(self.members)} members on {symbol}; "
        return build_council_result(symbol, self.members, deliberation)

    def summary(self, result):
        lines = [
            f"AstroCouncil: {result.symbol} @ {result.timestamp.strftime('%H:%M')}",
            f"  Final: {result.final_signal.value} ({result.confidence}% conf)",
            f"  Consensus: {result.consensus:.0%}  W-signal: {result.weighted_signal:+.3f}",
        ]
        for m in sorted(result.members, key=lambda x: -x.weight):
            lines.append(
                f"  [{m.weight:.0%}] {m.name}: {m.vote.value} ({m.confidence:.0f}%)"
            )
        if result.dissent:
            lines.append(f"  Dissent: {len(result.dissent)} disagree")
        return "\n".join(lines)
