"""JSON log file parser for logdiff."""

import json
from pathlib import Path
from typing import Any, Iterator


class ParseError(Exception):
    """Raised when a log file cannot be parsed."""


def parse_log_file(path: str | Path) -> list[dict[str, Any]]:
    """Parse a JSON log file and return a list of log entries.

    Supports two formats:
    - A JSON array of objects
    - Newline-delimited JSON (NDJSON), one object per line

    Args:
        path: Path to the log file.

    Returns:
        List of parsed log entry dictionaries.

    Raises:
        ParseError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.exists():
        raise ParseError(f"File not found: {path}")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ParseError(f"Cannot read file {path}: {exc}") from exc

    text = text.strip()
    if not text:
        raise ParseError(f"File is empty: {path}")

    # Try JSON array first
    if text.startswith("["):
        try:
            entries = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParseError(f"Invalid JSON array in {path}: {exc}") from exc
        if not isinstance(entries, list):
            raise ParseError(f"Expected a JSON array in {path}")
        return _validate_entries(entries, path)

    # Fall back to NDJSON
    return list(_parse_ndjson(text, path))


def _parse_ndjson(text: str, path: Path) -> Iterator[dict[str, Any]]:
    """Parse newline-delimited JSON."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ParseError(
                f"Invalid JSON on line {lineno} of {path}: {exc}"
            ) from exc
        if not isinstance(entry, dict):
            raise ParseError(
                f"Expected a JSON object on line {lineno} of {path}, "
                f"got {type(entry).__name__}"
            )
        yield entry


def _validate_entries(
    entries: list[Any], path: Path
) -> list[dict[str, Any]]:
    """Ensure every entry in the list is a dict."""
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ParseError(
                f"Entry {idx} in {path} is not a JSON object"
            )
    return entries
