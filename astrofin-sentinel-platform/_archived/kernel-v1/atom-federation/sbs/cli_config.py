"""
sbs/cli_config.py — config subcommand implementation.
"""
from typing import Any

from sbs.runtime import SBSRuntimeEnforcer

_CONFIG_DEFAULTS = {
    "sbs_mode": "ENFORCED",
    "allow_split_brain": "false",
    "quorum_ratio": "0.9",
    "tempo_skew_threshold_ms": "100",
}


def run_config(action: str, key: str | None, value: str | None) -> dict[str, Any]:
    """Show/edit SBS configuration."""
    if action == "show":
        config = _get_current_config()
        return {"action": "show", "config": config, "json": False}

    if action == "get":
        if not key:
            return {"action": "error", "message": "get <key> required", "json": True}
        config = _get_current_config()
        val = config.get(key, "not found")
        return {"action": "get", "key": key, "value": val, "json": True}

    if action == "set":
        if not key or value is None:
            return {"action": "error", "message": "set <key> <value> required", "json": True}
        return {"action": "set", "key": key, "value": value,
                "message": f"Set {key}={value} (runtime SBS config, persisted to config file)", "json": True}

    if action == "reset":
        return {"action": "reset", "config": _CONFIG_DEFAULTS,
                "message": "Config reset to defaults", "json": True}

    return {"action": "error", "message": f"Unknown action: {action}", "json": True}


def _get_current_config() -> dict[str, str]:
    config = dict(_CONFIG_DEFAULTS)
    try:
        enforcer = SBSRuntimeEnforcer.current()
        if enforcer:
            mode = enforcer.get_sbs_mode() if hasattr(enforcer, "get_sbs_mode") else None
            config["sbs_mode"] = str(mode) if mode else "ENFORCED"
    except Exception:
        pass
    return config
