"""CLI helpers that wire the --export flag into the main logdiff pipeline."""

from __future__ import annotations

import argparse
from typing import List, Optional

from logdiff.differ import EntryDiff
from logdiff.reporter import DiffReport
from logdiff.output_writer import write_output, UnsupportedFormatError

EXPORT_FORMATS = ["json", "csv", "markdown"]


def add_export_args(parser: argparse.ArgumentParser) -> None:
    """Attach export-related arguments to an existing ArgumentParser."""
    parser.add_argument(
        "--export-format",
        choices=EXPORT_FORMATS,
        default=None,
        metavar="FORMAT",
        help="Export diff results in the given format (%(choices)s).",
    )
    parser.add_argument(
        "--export-output",
        default=None,
        metavar="FILE",
        help="File path for exported output. Defaults to stdout if omitted.",
    )


def handle_export(
    report: DiffReport,
    diffs: List[EntryDiff],
    fmt: Optional[str],
    output_path: Optional[str],
) -> int:
    """Run the export step and return an exit code.

    Returns:
        0 on success, 2 on configuration error.
    """
    if fmt is None:
        return 0

    try:
        write_output(report, diffs, fmt=fmt, output_path=output_path)
    except UnsupportedFormatError as exc:
        print(f"logdiff export error: {exc}")
        return 2

    if output_path:
        print(f"Exported {fmt.upper()} report to {output_path}")

    return 0
