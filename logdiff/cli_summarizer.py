"""CLI integration for the summarizer module."""

import argparse
from typing import List

from logdiff.reporter import DiffReport
from logdiff.summarizer import build_summary, format_summary_compact


def add_summarizer_args(parser: argparse.ArgumentParser) -> None:
    """Register summarizer-related flags on an existing parser."""
    parser.add_argument(
        "--summary-title",
        metavar="TITLE",
        default=None,
        help="Custom title for the diff summary block.",
    )
    parser.add_argument(
        "--compact-summary",
        action="store_true",
        default=False,
        help="Print a single-line compact summary instead of the full block.",
    )


def handle_summarizer(
    args: argparse.Namespace,
    report: DiffReport,
) -> str:
    """Produce and return a summary string based on CLI args and the report.

    Returns the rendered summary as a string (caller is responsible for printing).
    """
    if args.compact_summary:
        return format_summary_compact(report)

    title = getattr(args, "summary_title", None)
    summary = build_summary(report, title=title)
    return summary.render()
