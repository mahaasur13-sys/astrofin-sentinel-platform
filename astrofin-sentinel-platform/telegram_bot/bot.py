"""AstroFin Sentinel V5 — Telegram Bot for trade alerts and control.

Usage:
    python -m telegram_bot.bot

Requires TELEGRAM_BOT_TOKEN in environment or .env file.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from telegram_bot.alerts import Alert, AlertDispatcher

logger = logging.getLogger(__name__)

START_TIME = time.time()

START_MESSAGE = (
    "\U0001f4e1 <b>AstroFin Sentinel V5 Bot</b>\n\n"
    "Commands:\n"
    "  /status — system health\n"
    "  /analyze &lt;symbol&gt; — run full analysis\n"
    "  /alerts on|off — toggle trade alerts\n"
    "  /help — this message\n\n"
    "Alerts are sent when ensemble signals are generated."
)


class AstroFinBot:
    """Telegram bot wrapping python-telegram-bot with alert dispatch."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._app: Application | None = None
        self._alerts = AlertDispatcher(self._send_message)
        self._chat_ids: set[int] = set()

    async def _send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> None:
        if not self._app:
            logger.warning("bot_not_initialized")
            return
        await self._app.bot.send_message(
            chat_id=chat_id, text=text, parse_mode=ParseMode.HTML
        )

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id if update.effective_chat else 0
        self._chat_ids.add(chat_id)
        self._alerts.register_chat(chat_id)
        await update.message.reply_text(
            START_MESSAGE,
            parse_mode=ParseMode.HTML,
        )

    async def _status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        uptime_sec = int(time.time() - START_TIME)
        h, m = divmod(uptime_sec, 3600)
        m, s = divmod(m, 60)

        try:
            from meta_rl.quant.risk import RegimeDetector
            regime = RegimeDetector().detect({"volatility": 0.02}).name
        except Exception:
            regime = "unknown"

        msg = (
            f"\U0001f4ca <b>Status</b>\n"
            f"Uptime: {h}h {m}m {s}s\n"
            f"Regime: {regime}\n"
            f"Chats registered: {len(self._chat_ids)}\n"
            f"Alerts: {'\U0001f7e2 ON' if self._alerts.enabled else '\U0001f534 OFF'}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    async def _analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        symbol = " ".join(context.args) if context.args else "BTCUSDT"
        await update.message.reply_text(
            f"\u23f3 Running analysis for <b>{symbol}</b>...",
            parse_mode=ParseMode.HTML,
        )

        try:
            from orchestration.sentinel_v5_broker import (
                BrokerConfig,
                SentinelV5Broker,
            )

            config = BrokerConfig(worker_count=2)
            hub = SentinelV5Broker(config=config)
            await hub.start()

            result = await hub.run_analysis(
                symbol=symbol,
                state={"symbol": symbol, "timeframe": "1D"},
            )

            await hub.stop()

            lines = [
                f"\U0001f3af <b>Analysis — {symbol}</b>\n",
                f"Signal: <b>{result.ensemble_signal}</b>",
                f"Confidence: {result.ensemble_confidence:.1f}%",
                f"Success: {result.agents_success}/{result.agents_success + result.agents_failed}",
            ]
            if result.agent_results:
                for ar in result.agent_results:
                    emoji = "\u2705" if not ar.error else "\u274c"
                    lines.append(f"  {emoji} {ar.agent_name}: {ar.signal} ({ar.confidence:.0f}%)")

            await update.message.reply_text(
                "\n".join(lines), parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.exception("analyze_command_failed")
            await update.message.reply_text(
                f"\u274c Analysis failed: {e}", parse_mode=ParseMode.HTML
            )

    async def _alerts_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            state = "ON" if self._alerts.enabled else "OFF"
            await update.message.reply_text(f"Alerts are <b>{state}</b>. Use /alerts on|off")
            return

        action = context.args[0].lower()
        if action == "on":
            self._alerts.toggle(True)
            await update.message.reply_text("\U0001f7e2 Alerts <b>ON</b>", parse_mode=ParseMode.HTML)
        elif action == "off":
            self._alerts.toggle(False)
            await update.message.reply_text("\U0001f534 Alerts <b>OFF</b>", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("Usage: /alerts on|off")

    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(START_MESSAGE, parse_mode=ParseMode.HTML)

    @property
    def alert_dispatcher(self) -> AlertDispatcher:
        return self._alerts

    async def send_signal(self, symbol: str, signal: str, confidence: float, reasoning: str, agent: str) -> None:
        alert = Alert(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            agent_name=agent,
        )
        await self._alerts.dispatch(alert)

    async def start(self) -> None:
        self._app = Application.builder().token(self._token).build()

        self._app.add_handler(CommandHandler("start", self._start))
        self._app.add_handler(CommandHandler("status", self._status))
        self._app.add_handler(CommandHandler("analyze", self._analyze))
        self._app.add_handler(CommandHandler("alerts", self._alerts_cmd))
        self._app.add_handler(CommandHandler("help", self._help))

        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        logger.info("telegram_bot_started")

    async def stop(self) -> None:
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
        logger.info("telegram_bot_stopped")

    async def run_forever(self) -> None:
        await self.start()
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await self.stop()


async def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        log.info("Error: TELEGRAM_BOT_TOKEN not set in environment.")
        log.info("Export it or add to .env:  export TELEGRAM_BOT_TOKEN=123456:ABC...")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    bot = AstroFinBot(token)
    await bot.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
