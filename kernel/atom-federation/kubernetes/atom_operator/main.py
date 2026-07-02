#!/usr/bin/env python3
"""
ATOM Operator — entrypoint.
Loads kubeconfig, starts controller, handles signals.
"""

from __future__ import annotations

import logging
import os
import signal
import sys

from kubernetes import config

from atom_operator.client import K8sClient
from atom_operator.controller import ATOMController
from atom_operator.health import make_state, start_health_server

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)-20s %(message)s"


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
    )


def load_config():
    """Try in-cluster first, then local kubeconfig."""
    try:
        config.load_incluster_config()
        logging.info("Loaded in-cluster config")
    except Exception:
        try:
            config.load_kube_config()
            logging.info("Loaded kubeconfig from ~/.kube/config")
        except Exception as e:
            logging.error(f"Cannot load kubeconfig: {e}")
            sys.exit(1)


def main() -> None:
    health_state = make_state()
    health_port = int(os.environ.get("HEALTH_PORT", "8080"))
    start_health_server(health_state, host="0.0.0.0", port=health_port)

    setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
    load_config()
    health_state.mark_ready()

    k8s = K8sClient()

    poll_interval = float(os.environ.get("RECONCILE_INTERVAL", "5"))
    controller = ATOMController(k8s, poll_interval=poll_interval)

    def handle_signal(signum, _frame):
        logging.info(f"Received signal {signum}")
        health_state.mark_not_ready()
        controller.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    logging.info(
        f"ATOM Operator v7.0 starting — "
        f"poll_interval={poll_interval}s namespace={os.environ.get('WATCH_NAMESPACE', 'default')}"
    )
    controller.start()


if __name__ == "__main__":
    main()
