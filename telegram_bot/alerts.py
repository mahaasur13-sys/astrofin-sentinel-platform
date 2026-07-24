"""Alert dispatcher — pushes trading signals to Telegram channels."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.base_agent import AgentResponse

logger = logging.getLogger(__name__)

SIGNAL_EMOJI: dict[str, str] = {
    "LONG": "\U0001f7e2",
    "SHORT": "\U0001f534",
    "NEUTRAL": "\u26aa\ufe0f",
    "HOLD": "\u26aa\ufe0f",
}


@dataclass
class Alert:
    symbol: str
    signal: str
    confidence: float
    reasoning: str
    agent_name: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def format_message(self) -> str:
        emoji = SIGNAL_EMOJI.get(self.signal, "\u2753")
        return (
            f"{emoji} <b>{self.signal}</b> — {self.symbol}\n"
            f"\U0001f916 <i>{self.agent_name}</i>\n"
            f"\U0001f4ca Confidence: <b>{self.confidence:.1f}%</b>\n"
            f"\U0001f4dd {self.reasoning[:200]}"
        )

    @classmethod
    def from_response(
        cls, symbol: str, response: AgentResponse
    ) -> Alert:
        return cls(
            symbol=symbol,
            signal=response.signal.name if hasattr(response.signal, "name") else str(response.signal),
            confidence=response.confidence,
            reasoning=response.reasoning or "",
            agent_name=response.agent_name or "unknown",
        )


class AlertDispatcher:
    """Dispatches trading alerts to registered Telegram chat IDs."""

    def __init__(self, send_func) -> None:
        self._send = send_func
        self._chat_ids: set[int] = set()
        self._enabled = True

    def register_chat(self, chat_id: int) -> None:
        self._chat_ids.add(chat_id)
        logger.info("alert_dispatcher_chat_registered", extra={"chat_id": chat_id})

    def unregister_chat(self, chat_id: int) -> None:
        self._chat_ids.discard(chat_id)

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._chat_ids)

    def toggle(self, state: bool) -> None:
        self._enabled = state

    async def dispatch(self, alert: Alert) -> None:
        if not self.enabled:
            return
        text = alert.format_message()
        for chat_id in list(self._chat_ids):
            try:
                await self._send(chat_id=chat_id, text=text, parse_mode="HTML")
            except Exception as exc:
                logger.warning(
                    "alert_dispatch_failed",
                    extra={"chat_id": chat_id, "error": str(exc)},
                )

    async def dispatch_ensemble(self, symbol: str, results: list[AgentResponse]) -> None:
        lines = [f"\U0001f3af <b>Ensemble Signal — {symbol}</b>\n"]
        for r in results:
            emoji = SIGNAL_EMOJI.get(
                r.signal.name if hasattr(r.signal, "name") else str(r.signal), "\u2753"
            )
            lines.append(
                f"  {emoji} {r.agent_name}: {r.signal.name if hasattr(r.signal, 'name') else r.signal} "
                f"({r.confidence:.0f}%)"
            )
        text = "\n".join(lines)
        for chat_id in list(self._chat_ids):
            try:
                await self._send(chat_id=chat_id, text=text, parse_mode="HTML")
            except Exception as exc:
                logger.warning("ensemble_dispatch_failed", extra={"chat_id": chat_id, "error": str(exc)})
