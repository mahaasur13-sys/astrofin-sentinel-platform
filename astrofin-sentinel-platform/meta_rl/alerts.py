"""meta_rl/alerts.py — ATOM-META-RL-006: Telegram Alerts (P1.3)

Sends alerts to Telegram when:
  - Strategy reward exceeds TELEGRAM_MIN_REWARD_ALERT threshold
  - Evolution completes (with summary)
  - Walk-forward overfit detected
  - KARL state update

Feature flags:
  TELEGRAM_ALERTS_ENABLED (default: false — must be explicitly enabled)
  TELEGRAM_BOT_TOKEN (required for alerts)
  TELEGRAM_CHAT_ID (required for alerts)

All tokens configured via environment variables.
"""

from __future__ import annotations

import logging

from meta_rl.config import (
    TELEGRAM_ALERTS_ENABLED,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_MIN_REWARD_ALERT,
)

logger = logging.getLogger(__name__)

# Singleton bot instance
_telegram = None


class TelegramAlerter:
    """
    Sends formatted alerts to Telegram.

    Usage:
        alerter = TelegramAlerter()
        alerter.send_reward_alert(strategy, reward)
        alerter.send_evolution_complete(history, best_strategy)
        alerter.send_overfit_alert(strategy, overfit_report)
    """

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        min_reward: float = TELEGRAM_MIN_REWARD_ALERT,
    ):
        self.enabled = TELEGRAM_ALERTS_ENABLED and bool(TELEGRAM_BOT_TOKEN)
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.min_reward = min_reward
        self._alert_count = 0

        if not self.enabled:
            logger.info("[ALERTS] Telegram alerts disabled")
        elif not self.bot_token or not self.chat_id:
            logger.warning("[ALERTS] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
            self.enabled = False
        else:
            logger.info(f"[ALERTS] Telegram enabled — min_reward={min_reward}")

    def _send(self, text: str) -> bool:
        """Send message via Telegram Bot API. Returns True on success."""
        if not self.enabled:
            return False
        try:
            import json
            import urllib.request

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = json.dumps(
                {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                }
            ).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(
                req, timeout=10
            ) as resp:  # nosec B310 — webhook URL validated upstream
                result = json.loads(resp.read())
                if result.get("ok"):
                    self._alert_count += 1
                    return True
                logger.warning(f"[ALERTS] Telegram API error: {result}")
                return False
        except Exception as e:
            logger.warning(f"[ALERTS] Failed to send: {e}")
            return False

    def send_reward_alert(
        self,
        strategy,
        reward: float,
        generation: int,
        extra: str | None = None,
    ) -> bool:
        """
        Alert when a strategy exceeds min_reward threshold.

        Use after each evolution generation or when best is found.
        """
        if reward < self.min_reward:
            return False

        sid = getattr(strategy, "id", "?")[:16]
        ev = getattr(strategy, "evaluation", None)
        sharpe = f"{getattr(ev, 'sharpe', 0):.3f}" if ev else "N/A"
        wr = f"{getattr(ev, 'win_rate', 0):.0%}" if ev else "N/A"
        dd = f"{getattr(ev, 'max_drawdown', 0):.2%}" if ev else "N/A"
        trades = str(getattr(ev, "trades", 0)) if ev else "N/A"

        msg = (
            f"🟢 *Strategy Alert*\n"
            f"`Reward: {reward:+.4f}`\n"
            f"Gen: {generation} | ID: `{sid}`\n"
            f"Sharpe: {sharpe} | Win: {wr} | DD: {dd}\n"
            f"Trades: {trades}"
        )
        if extra:
            msg += f"\n_{extra}_"

        ok = self._send(msg)
        if ok:
            logger.info(f"[ALERTS] Reward alert sent: {reward:+.4f} gen={generation}")
        return ok

    def send_evolution_complete(
        self,
        history,
        best_strategy,
        session_id: str,
        elapsed_seconds: float = 0,
    ) -> bool:
        """
        Alert when evolution run completes.
        Includes summary of all generations.
        """
        if not self.enabled:
            return False

        n_gens = len(history)
        best_reward = history[-1].max_reward if history else 0
        best_sharpe = "N/A"
        best_wr = "N/A"

        if best_strategy:
            ev = getattr(best_strategy, "evaluation", None)
            best_sharpe = f"{getattr(ev, 'sharpe', 0):.3f}" if ev else "N/A"
            best_wr = f"{getattr(ev, 'win_rate', 0):.0%}" if ev else "N/A"

        elapsed_str = (
            f"{int(elapsed_seconds // 60)}m {int(elapsed_seconds % 60)}s"
            if elapsed_seconds > 0
            else "N/A"
        )

        msg = (
            f"🏁 *Evolution Complete*\n"
            f"Session: `{session_id}`\n"
            f"Gens: {n_gens} | Time: {elapsed_str}\n"
            f"─────────────\n"
            f"Best reward: `{best_reward:+.4f}`\n"
            f"Sharpe: {best_sharpe} | Win: {best_wr}\n"
            f"─────────────\n"
            f"Alerts sent: {self._alert_count}"
        )

        ok = self._send(msg)
        if ok:
            logger.info("[ALERTS] Evolution complete alert sent")
        return ok

    def send_overfit_alert(
        self,
        strategy,
        overfit_report,
        generation: int,
    ) -> bool:
        """
        Alert when walk-forward analysis detects overfitting.
        """
        if not self.enabled:
            return False

        sid = getattr(strategy, "id", "?")[:16]
        splits = getattr(overfit_report, "overfit_splits", 0)
        n_splits = getattr(overfit_report, "n_splits", 0)
        deg = getattr(overfit_report, "mean_degradation", 0)

        msg = (
            f"⚠️ *Overfit Detected*\n"
            f"Strategy: `{sid}`\n"
            f"Gen: {generation}\n"
            f"OOS failed: {splits}/{n_splits} splits\n"
            f"Sharpe degradation: {deg:+.3f}\n"
            f"Action: Reduce complexity or increase regularization"
        )

        ok = self._send(msg)
        if ok:
            logger.warning(f"[ALERTS] Overfit alert sent for gen {generation}")
        return ok

    def send_karl_update(self, karl_state: dict, generation: int) -> bool:
        """Alert when KARL state is updated with key metrics."""
        if not self.enabled:
            return False

        top_q = karl_state.get("q_star", karl_state.get("top_q", "N/A"))
        if isinstance(top_q, float):
            top_q = f"{top_q:.4f}"

        msg = (
            f"🧠 *KARL Update*\n"
            f"Gen: {generation}\n"
            f"Q* (top): {top_q}\n"
            f"Generation: {karl_state.get('generation', generation)}"
        )

        ok = self._send(msg)
        return ok


# ── Convenience factory ─────────────────────────────────────────────────────────

_alerter: TelegramAlerter | None = None


def get_alerter() -> TelegramAlerter:
    """Get or create singleton TelegramAlerter instance."""
    global _alerter
    if _alerter is None:
        _alerter = TelegramAlerter()
    return _alerter


def send_reward_alert(strategy, reward: float, generation: int, **kwargs) -> bool:
    """Quick alert when strategy reward exceeds threshold."""
    return get_alerter().send_reward_alert(strategy, reward, generation, **kwargs)


def send_evolution_complete(history, best_strategy, session_id: str, **kwargs) -> bool:
    """Quick alert when evolution completes."""
    return get_alerter().send_evolution_complete(
        history, best_strategy, session_id, **kwargs
    )
