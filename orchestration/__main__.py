"""Main entry point with dual-mode + graceful degradation."""

import asyncio
import logging
import sys
import traceback

from core.logging import setup_logging

logger = logging.getLogger(__name__)


def main():
    setup_logging()

    args = sys.argv[1:]

    # Parse flags
    masfactory = "--masfactory" in args or "--karl" in args

    # Remove flags from args
    clean_args = [a for a in args if not a.startswith("--")]
    query = " ".join(clean_args) if clean_args else "Analyze BTC"
    symbol = "BTCUSDT"
    timeframe = "SWING"

    if masfactory:
        logger.info("masfactory.mode_enabled")
        logger.info("masfactory.attempting_topology")
        try:
            from orchestration.sentinel_v5_mas import run_sentinel_v5_mas

            result = asyncio.run(
                run_sentinel_v5_mas(
                    user_query=query,
                    symbol=symbol,
                    timeframe=timeframe,
                )
            )
            logger.info("masfactory.completed_successfully")
            logger.info("masfactory.result", result=str(result))
            return
        except Exception as e:
            logger.error("masfactory.error", error=str(e))
            logger.info("masfactory.falling_back_to_legacy")
            logger.debug(traceback.format_exc())

    # Legacy mode (unchanged)
    logger.info("masfactory.mode_disabled_legacy")
    from orchestration import karl_cli

    karl_cli.main()


if __name__ == "__main__":
    main()
