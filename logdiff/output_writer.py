"""Write exported diff output to files or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from logdiff.differ import EntryDiff
from logdiff.reporter import DiffReport
from logdiff.exporter import export_csv, export_json, export_markdown


FORMAT_EXTENSIONS = {
    "json": ".json",
    "csv": ".csv",
    "markdown": ".md",
}


class UnsupportedFormatError(ValueError):
    """Raised when an unsupported export format is requested."""


def write_output(
    report: DiffReport,
    diffs: List[EntryDiff],
    fmt: str,
    output_path: Optional[str] = None,
) -> None:
    """Render diffs in the requested format and write to file or stdout.

    Args:
        report: Aggregated diff statistics.
        diffs: List of entry-level diffs to export.
        fmt: Output format — one of 'json', 'csv', 'markdown'.
        output_path: File path to write to; if None, writes to stdout.

    Raises:
        UnsupportedFormatError: If *fmt* is not a recognised format.
    """
    fmt = fmt.lower()
    if fmt not in FORMAT_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(FORMAT_EXTENSIONS)}"
        )

    if fmt == "json":
        content = export_json(report, diffs)
    elif fmt == "csv":
        content = export_csv(diffs)
    else:
        content = export_markdown(report, diffs)

    if output_path is None:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
    else:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
