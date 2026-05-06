"""logdiff — diff structured JSON log files and surface field-level changes."""

__version__ = "0.1.0"
__all__ = ["diff_logs", "load_log"]

import json
from typing import Any


def load_log(path: str) -> list[dict[str, Any]]:
    """Load a JSON log file and return a list of log entry dicts.

    Each line in the file is expected to be a valid JSON object (NDJSON format).
    Blank lines are silently skipped.

    Args:
        path: Path to the NDJSON log file.

    Returns:
        A list of parsed log entry dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If a line contains invalid JSON.
    """
    entries: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {lineno} of '{path}': {exc.msg}",
                    exc.doc,
                    exc.pos,
                ) from exc
    return entries
