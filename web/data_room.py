"""
web/data_room.py

Data Room API endpoints.
"""

import json
from pathlib import Path

from flask import Blueprint, jsonify

from core.auth import require_api_key as require_auth

data_room_bp = Blueprint("data_room", __name__)

CONFLICT_JOURNAL = Path("data_room/conflict_journal.json")


@require_auth
@data_room_bp.route("/data-room/conflicts", methods=["GET"])
def list_conflicts():
    """
    Return conflict journal contents as JSON.
    """

    if not CONFLICT_JOURNAL.exists():
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"{CONFLICT_JOURNAL} not found",
                    "conflicts": [],
                }
            ),
            404,
        )

    try:
        with CONFLICT_JOURNAL.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data)

    except json.JSONDecodeError:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid JSON in conflict journal",
                    "conflicts": [],
                }
            ),
            500,
        )

    except Exception as exc:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": str(exc),
                    "conflicts": [],
                }
            ),
            500,
        )
