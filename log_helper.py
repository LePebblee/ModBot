# log_helper.py
import json
import os
from datetime import datetime
from typing import Dict

LOGS_FILE = "logs.json"


def _load_logs() -> list:
    """Read the JSON file – return an empty list if the file is missing or broken."""
    if not os.path.exists(LOGS_FILE):
        return []
    try:
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt JSON → start fresh (you can change this behaviour if you prefer)
        return []


def _save_logs(logs: list) -> None:
    """Write the whole list back to disk (pretty‑printed)."""
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4)


def _next_id(logs: list) -> str:
    """
    Determine the next numeric ID.
    Existing entries may or may not have an 'id' key – we ignore those that don’t.
    Returns the new ID as a **string**, matching the format used elsewhere.
    """
    max_id = 0
    for entry in logs:
        try:
            cur = int(entry.get("id", 0))
            if cur > max_id:
                max_id = cur
        except ValueError:
            continue
    return str(max_id + 1)


def add_log(entry: Dict) -> None:
    """
    Append a new moderation entry to logs.json.
    Expected keys in *entry*: type, user_id, reason, timestamp.
    This function adds the missing 'id' field automatically.
    """
    logs = _load_logs()

    # Insert the generated id
    entry_with_id = dict(entry)               # copy so we don’t mutate caller’s dict
    entry_with_id["id"] = _next_id(logs)

    # Newest entries first – the UI expects that order
    logs.insert(0, entry_with_id)
    _save_logs(logs)