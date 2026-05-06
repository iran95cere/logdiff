"""Export diff results to various output formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from logdiff.reporter import DiffReport
from logdiff.differ import EntryDiff


def export_json(report: DiffReport, diffs: List[EntryDiff]) -> str:
    """Serialize the report and diffs to a JSON string."""
    entries = []
    for d in diffs:
        changes = [
            {
                "field": c.field,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "change_type": c.change_type,
            }
            for c in d.changes
        ]
        entries.append({"key": d.key, "changes": changes})

    payload = {
        "summary": {
            "total": report.total,
            "modified": report.modified,
            "added": report.added,
            "removed": report.removed,
            "unchanged": report.unchanged,
            "change_rate": report.change_rate(),
            "most_changed_fields": report.most_changed_fields(),
        },
        "entries": entries,
    }
    return json.dumps(payload, indent=2)


def export_csv(diffs: List[EntryDiff]) -> str:
    """Serialize field-level changes to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["key", "field", "change_type", "old_value", "new_value"])
    for d in diffs:
        for c in d.changes:
            writer.writerow([d.key, c.field, c.change_type, c.old_value, c.new_value])
    return output.getvalue()


def export_markdown(report: DiffReport, diffs: List[EntryDiff]) -> str:
    """Render the diff report as a Markdown document."""
    lines = []
    lines.append("# Log Diff Report\n")
    lines.append("## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total entries | {report.total} |")
    lines.append(f"| Modified | {report.modified} |")
    lines.append(f"| Added | {report.added} |")
    lines.append(f"| Removed | {report.removed} |")
    lines.append(f"| Unchanged | {report.unchanged} |")
    lines.append(f"| Change rate | {report.change_rate():.1%} |\n")

    top_fields = report.most_changed_fields()
    if top_fields:
        lines.append("## Most Changed Fields\n")
        for field, count in top_fields:
            lines.append(f"- `{field}`: {count} change(s)")
        lines.append("")

    if diffs:
        lines.append("## Changed Entries\n")
        for d in diffs:
            lines.append(f"### `{d.key}`\n")
            lines.append("| Field | Change | Old | New |")
            lines.append("|-------|--------|-----|-----|")
            for c in d.changes:
                old = c.old_value if c.old_value is not None else "—"
                new = c.new_value if c.new_value is not None else "—"
                lines.append(f"| `{c.field}` | {c.change_type} | {old} | {new} |")
            lines.append("")

    return "\n".join(lines)
