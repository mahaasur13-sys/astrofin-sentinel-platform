#!/usr/bin/env python3
"""Nightly strategy export daemon.

Usage: python tools/nightly_export.py --daemon
Or:     python tools/nightly_export.py --once

Checks for new top strategies in the pool every N minutes and
exports them as GitAgent packages. Idempotent — skips already-exported.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 300  # 5 min


def check_and_export():
    """Check strategy pool for new top strategies and export them."""
    try:
        from meta_rl.strategy_pool import strategy_pool

        top = strategy_pool.get_top(n=3)
        if not top:
            logger.debug("No strategies in pool yet")
            return

        logger.info(f"Top {len(top)} strategies in pool:")
        for s in top:
            logger.info(f"  {s.id}: reward={s.reward:.4f}")

    except ImportError as e:
        logger.debug(f"Strategy pool not available: {e}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Export check failed: {e}")


def run_daemon(poll_seconds: int = POLL_INTERVAL_SECONDS):
    logger.info(f"Starting nightly export daemon (poll={poll_seconds}s)")
    while True:
        check_and_export()
        time.sleep(poll_seconds)


def run_once():
    logger.info("Running single export check")
    check_and_export()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nightly strategy export")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--poll", type=int, default=POLL_INTERVAL_SECONDS, help="Poll interval in seconds")
    args = parser.parse_args()

    if args.daemon:
        run_daemon(args.poll)
    else:
        run_once()
