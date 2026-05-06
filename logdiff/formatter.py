"""Formatters for rendering diff output to the terminal or plain text."""

from dataclasses import dataclass
from typing import List, Optional
from logdiff.differ import EntryDiff, FieldChange


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_CYAN = "\033[36m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_field_change(change: FieldChange, use_color: bool = True) -> str:
    """Format a single field-level change as a human-readable string."""
    field = _colorize(change.field, ANSI_BOLD, use_color)
    if change.old_value is None:
        value = _colorize(repr(change.new_value), ANSI_GREEN, use_color)
        return f"  + {field}: {value}"
    if change.new_value is None:
        value = _colorize(repr(change.old_value), ANSI_RED, use_color)
        return f"  - {field}: {value}"
    old = _colorize(repr(change.old_value), ANSI_RED, use_color)
    new = _colorize(repr(change.new_value), ANSI_GREEN, use_color)
    return f"  ~ {field}: {old} -> {new}"


def format_entry_diff(diff: EntryDiff, use_color: bool = True) -> str:
    """Format a full EntryDiff block for display."""
    lines: List[str] = []

    if diff.added:
        header = _colorize(f"[ADDED] key={diff.key}", ANSI_GREEN, use_color)
        lines.append(header)
        for field, val in (diff.new_entry or {}).items():
            lines.append(_colorize(f"  + {field}: {repr(val)}", ANSI_GREEN, use_color))
    elif diff.removed:
        header = _colorize(f"[REMOVED] key={diff.key}", ANSI_RED, use_color)
        lines.append(header)
        for field, val in (diff.old_entry or {}).items():
            lines.append(_colorize(f"  - {field}: {repr(val)}", ANSI_RED, use_color))
    else:
        header = _colorize(f"[CHANGED] key={diff.key}", ANSI_YELLOW, use_color)
        lines.append(header)
        for change in diff.changes:
            lines.append(format_field_change(change, use_color=use_color))

    return "\n".join(lines)


def format_summary(diffs: List[EntryDiff], use_color: bool = True) -> str:
    """Render a summary line showing counts of added, removed, and changed entries."""
    added = sum(1 for d in diffs if d.added)
    removed = sum(1 for d in diffs if d.removed)
    changed = sum(1 for d in diffs if not d.added and not d.removed)

    parts = [
        _colorize(f"+{added} added", ANSI_GREEN, use_color),
        _colorize(f"-{removed} removed", ANSI_RED, use_color),
        _colorize(f"~{changed} changed", ANSI_YELLOW, use_color),
    ]
    return "Summary: " + ", ".join(parts)


def render_diff(diffs: List[EntryDiff], use_color: bool = True) -> str:
    """Render all diffs as a complete formatted report string."""
    if not diffs:
        return _colorize("No differences found.", ANSI_CYAN, use_color)

    blocks = [format_entry_diff(d, use_color=use_color) for d in diffs]
    blocks.append("")
    blocks.append(format_summary(diffs, use_color=use_color))
    return "\n".join(blocks)
