"""
web/data_room.py

Data Room API endpoints.
"""

from __future__ import annotations
import json
from pathlib import Path

from flask import Blueprint, jsonify

from core.error_schema import InternalError, NotFound

data_room_bp = Blueprint("data_room", __name__)

CONFLICT_JOURNAL = Path("data_room/conflict_journal.json")


@data_room_bp.route("/data-room/conflicts", methods=["GET"])
def list_conflicts():
    """
    Return conflict journal contents as JSON.
    """

    if not CONFLICT_JOURNAL.exists():
        raise NotFound(
            f"{CONFLICT_JOURNAL} not found",
            details={"path": str(CONFLICT_JOURNAL)},
        )

    try:
        with CONFLICT_JOURNAL.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data)

    except json.JSONDecodeError as exc:
        raise InternalError("Invalid JSON in conflict journal") from exc

    except Exception as exc:
        raise InternalError(str(exc)) from exc
