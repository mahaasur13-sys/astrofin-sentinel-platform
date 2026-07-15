#!/usr/bin/env python3
"""
ACOS Tunnel Monitor — systemd service entry point.
Runs AmneziaWGManager.health_check_loop() as a daemon.
"""
from __future__ import annotations
import logging
import os
import sys

# Add ACOS to path
sys.path.insert(0, "/opt/acos")

from acos.events.event_log import EventLog
from acos.network.amnezia_wg import AmneziaWGManager

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("acos-tunnel-monitor")


def main() -> None:
    log = EventLog()
    trace_id = os.environ.get("ACOS_TRACE_ID", "tunnel-monitor")

    manager = AmneziaWGManager(
        event_log=log,
        interface=os.environ.get("AWG_INTERFACE", "wg0"),
        trace_id=trace_id,
        max_attempts=int(os.environ.get("AWG_MAX_RETRIES", "5")),
    )

    interval = float(os.environ.get("AWG_CHECK_INTERVAL", "30"))
    max_failures = int(os.environ.get("AWG_MAX_FAILURES", "3"))

    logger.info(f"Starting tunnel monitor: interface={manager._iface}, interval={interval}s")

    # Initial bring-up
    if not manager.status()["up"]:
        logger.info("Tunnel down on startup, bringing up...")
        manager.start()

    # Health check loop
    try:
        manager.health_check_loop(interval=interval, max_failures=max_failures)
    except KeyboardInterrupt:
        logger.info("Received SIGINT, shutting down...")
        manager.stop()


if __name__ == "__main__":
    main()
