"""Formatter module: renders diff output as human-readable text."""

import sys
from typing import List

from logdiff.differ import EntryDiff, FieldChange
from logdiff.reporter import DiffReport

COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}


def _colorize(text: str, color: str) -> str:
    if not sys.stdout.isatty():
        return text
    code = COLORS.get(color, "")
    return f"{code}{text}{COLORS['reset']}"


def format_field_change(change: FieldChange) -> str:
    if change.old_value is None:
        return _colorize(f"  + {change.field}: {change.new_value!r}", "green")
    if change.new_value is None:
        return _colorize(f"  - {change.field}: {change.old_value!r}", "red")
    return (
        _colorize(f"  ~ {change.field}: ", "yellow")
        + _colorize(repr(change.old_value), "red")
        + " -> "
        + _colorize(repr(change.new_value), "green")
    )


def format_entry_diff(diff: EntryDiff) -> str:
    lines = []
    label = _colorize(f"[{diff.key}]", "cyan")
    if diff.is_added:
        lines.append(f"{label} " + _colorize("ADDED", "green"))
    elif diff.is_removed:
        lines.append(f"{label} " + _colorize("REMOVED", "red"))
    else:
        lines.append(f"{label} " + _colorize("MODIFIED", "yellow"))
        for change in diff.changes:
            lines.append(format_field_change(change))
    return "\n".join(lines)


def format_summary(report: DiffReport) -> str:
    lines = [
        _colorize("=== Summary ===", "bold"),
        f"  Total entries : {report.total_entries}",
        _colorize(f"  Added         : {report.added}", "green"),
        _colorize(f"  Removed       : {report.removed}", "red"),
        _colorize(f"  Modified      : {report.modified}", "yellow"),
        f"  Unchanged     : {report.unchanged}",
        f"  Change rate   : {report.change_rate * 100:.1f}%",
    ]
    top_fields = report.most_changed_fields(top_n=3)
    if top_fields:
        lines.append("  Top changed fields:")
        for fname, count in top_fields:
            lines.append(f"    {fname}: {count} change(s)")
    return "\n".join(lines)


def render_diff(report: DiffReport, summary_only: bool = False) -> str:
    parts = []
    if not summary_only:
        for diff in report.diffs:
            if diff.has_changes or diff.is_added or diff.is_removed:
                parts.append(format_entry_diff(diff))
    parts.append(format_summary(report))
    return "\n".join(parts)
