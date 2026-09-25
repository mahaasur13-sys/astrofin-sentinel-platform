"""
DecisionOS Main Entry Point.

Starts the minimal core and boots all plugins.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.plugin_manager import PluginManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("decisionos")


class DecisionOS:
    """Minimal DecisionOS core — everything else is a plugin."""

    def __init__(self, plugins_dir: Path | None = None, tenant_tier: str = "Pro") -> None:
        self.manager = PluginManager(plugins_dir=plugins_dir, tenant_tier=tenant_tier)

    def boot(self) -> int:
        """Bootstrap all plugins. Returns count of active plugins."""
        logger.info("DecisionOS v1.0.0 starting...")

        count = self.manager.bootstrap()
        logger.info(f"Bootstrapped {count} built-in plugins")

        self._boot_extra_plugins()

        active = self.manager.active_count
        logger.info(f"DecisionOS ready — {active} plugins active")
        return active

    def _boot_extra_plugins(self) -> None:
        """Load community and dashbeam plugins."""
        for category in ("community", "dashbeam-transfer"):
            cat_dir = self.manager.plugins_dir / category
            if cat_dir.exists():
                for plugin_dir in sorted(cat_dir.iterdir()):
                    if plugin_dir.is_dir():
                        try:
                            entry = self.manager.install(plugin_dir)
                            if entry:
                                logger.info(f"Extra plugin loaded: {plugin_dir.name}")
                        except Exception as e:
                            logger.error(f"Failed to load extra plugin {plugin_dir.name}: {e}")

    def shutdown(self) -> None:
        self.manager.shutdown()
        logger.info("DecisionOS shutdown complete")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="DecisionOS v1.0.0")
    parser.add_argument("--tier", default="Pro", choices=["Start", "Pro", "Enterprise"])
    parser.add_argument("--plugins-dir", type=Path, help="Custom plugins directory")
    args = parser.parse_args()

    os = DecisionOS(plugins_dir=args.plugins_dir, tenant_tier=args.tier)
    active = os.boot()

    if active == 0:
        logger.error("No plugins active! Check configuration.")
        sys.exit(1)

    logger.info(f"DecisionOS v1.0.0 running with {active} active plugins")

    try:
        import signal

        def shutdown_handler(signum, frame):
            logger.info("Received shutdown signal")
            os.shutdown()

        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

        signal.pause()
    except ImportError:
        pass


if __name__ == "__main__":
    main()
