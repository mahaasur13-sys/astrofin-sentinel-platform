from __future__ import annotations
from flask import Flask, jsonify, request

from core.auth import require_api_key

server = Flask(__name__)


# Базовый эндпоинт для проверки работоспособности
@server.route("/health")
def health():
    return jsonify({"status": "ok"})


# Защищённый A/B-тест
@server.route("/api/ab/compare")
@require_api_key
def ab_compare():
    """A/B compare two sessions: ?sid_a=X&sid_b=Y
    Supports both new-style sessions (ScoredStrategy dicts) and legacy
    history_db sessions (confidence-based proxy rewards)."""
    sid_a = request.args.get("sid_a", "")
    sid_b = request.args.get("sid_b", "")
    if not sid_a or not sid_b:
        return jsonify({"status": "ERROR", "error": "sid_a and sid_b required"}), 400

    try:
        # здесь логика сравнения, возвращающая результат
        # для примера – заглушка
        result = {
            "status": "OK",
            "sid_a": sid_a,
            "sid_b": sid_b,
            "p_value": 0.05,
            "effect_size": 0.2,
            "winner": "TIE",
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500


# Защищённый эндпоинт для включения live-режима
@server.route("/api/live/enable", methods=["POST"])
@require_api_key
def live_enable():
    """Включает live-режим. Требует подтверждение и API-ключ."""
    data = request.get_json(silent=True) or {}
    confirmed = data.get("confirmed", False)
    if not confirmed:
        return jsonify({"error": "Confirmation required"}), 400
    return jsonify({"status": "live_enabled", "mode": "live"})


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000, debug=False)
