"""core/safe_json.py — ATOM-017 FIX: Safe JSON operations with error handling"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def safe_json_dump(data: Any, filepath: str, ensure_ascii: bool = False) -> bool:
    """Safely dump data to JSON file. Returns True on success."""
    if data is None:
        data = {"status": "null", "timestamp": datetime.now().isoformat()}
    if not isinstance(data, (dict, list)):  # noqa: UP038
        data = {"value": str(data), "timestamp": datetime.now().isoformat()}
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=2, default=str)
        return True
    except (TypeError, ValueError) as e:
        logger.error(f"[safe_json] Type/Value error dumping to {filepath}: {e}")
        return False
    except OSError as e:
        logger.error(f"[safe_json] IO error writing {filepath}: {e}")
        return False


def safe_json_load(filepath: str, default: Any = None) -> Any:
    """Safely load JSON file. Returns default on failure."""
    if default is None:
        default = {}
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"[safe_json] Empty file: {filepath}")
                return {"status": "empty", "timestamp": datetime.now().isoformat()}
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"[safe_json] Corrupted JSON in {filepath}: {e}")
        return {"status": "corrupted", "error": str(e), "filepath": filepath}
    except OSError as e:
        logger.error(f"[safe_json] Cannot read {filepath}: {e}")
        return {"status": "file_not_found", "error": str(e), "filepath": filepath}
    except Exception as e:
        logger.error(f"[safe_json] Unexpected error loading {filepath}: {e}")
        return {"status": "error", "error": str(e), "filepath": filepath}


def safe_jsonl_append(record: Any, filepath: str) -> bool:
    """Append a record to a JSONL file safely."""
    if record is None:
        logger.warning(f"[safe_json] Refusing to append null record to {filepath}")
        return False
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, default=str)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return True
    except Exception as e:
        logger.error(f"[safe_json] JSONL append failed for {filepath}: {e}")
        return False


def safe_jsonl_load(filepath: str) -> list:
    """Load all records from a JSONL file safely."""
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        records = []
        for i, line in enumerate(lines):
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"[safe_json] Corrupted line {i + 1} in {filepath}: {e}")
                records.append(
                    {"status": "corrupted_line", "line": i + 1, "raw": line[:100]}
                )
        return records
    except OSError:
        logger.info(f"[safe_json] JSONL file not found: {filepath}")
        return []
    except Exception as e:
        logger.error(f"[safe_json] Error reading {filepath}: {e}")
        return []
