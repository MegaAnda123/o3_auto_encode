"""Encoding progress heartbeat.

The CLI encoder writes a small json file while encoding so that the frontend can poll it.
The file lives next to the database file and is removed/marked idle once encoding stops.
"""

import json
import os
import time
from pathlib import Path
from typing import Any

from o3_auto_encode import logger

PROGRESS_FILE_NAME = "progress.json"

# Heartbeats older than this are considered stale (encoder died without cleaning up).
STALE_AFTER_S = 15.0


def progress_path_for(db_path: Path | str) -> Path:
    """Resolve the heartbeat path belonging to a database file.

    Args:
        db_path: Path to the database file.

    Returns:
        Path to the progress heartbeat file.

    """
    return Path(db_path).parent / PROGRESS_FILE_NAME


def write_progress(path: Path | str, payload: dict[str, Any]) -> None:
    """Write the heartbeat atomically so pollers never read a partial file.

    Args:
        path: Path to the heartbeat file.
        payload: Progress payload, `updated_at` is added automatically.

    """
    path = Path(path)
    payload = {**payload, "updated_at": time.time()}

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(payload, f)
        os.replace(tmp_path, path)
    except OSError as e:
        logger.debug(f"Could not write progress file `{path}`: {e}")


def clear_progress(path: Path | str) -> None:
    """Mark the heartbeat as idle (no encoding in progress).

    Args:
        path: Path to the heartbeat file.

    """
    write_progress(path, {"bundle": None, "state": "idle"})


def read_progress(path: Path | str) -> dict[str, Any] | None:
    """Read the heartbeat.

    Args:
        path: Path to the heartbeat file.

    Returns:
        Progress payload with an added `stale` flag, or None if unavailable.

    """
    path = Path(path)
    if not path.is_file():
        return None

    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    updated_at = data.get("updated_at") or 0
    data["stale"] = (time.time() - updated_at) > STALE_AFTER_S
    return data

