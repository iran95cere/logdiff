"""CLI integration for the differ_rollup module."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_rollup import build_rollup, DiffRollup


def add_rollup_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'rollup' subcommand."""
    parser = subparsers.add_parser(
        "rollup",
        help="Aggregate field-level changes into a compact rollup summary.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Show the top N most changed fields (default: 10).",
    )
    parser.add_argument(
        "--min-changes",
        type=int,
        default=1,
        metavar="N",
        help="Only show fields with at least N total changes (default: 1).",
    )


def _format_rollup_row(field_name: str, modified: int, added: int, removed: int, total: int) -> str:
    """Format a single field row for the rollup table.

    Args:
        field_name: The name of the field.
        modified: Number of modified occurrences.
        added: Number of added occurrences.
        removed: Number of removed occurrences.
        total: Total number of changes.

    Returns:
        A formatted string row suitable for tabular display.
    """
    return f"{field_name:<30} {modified:>10} {added:>8} {removed:>9} {total:>7}"


def handle_rollup(args: argparse.Namespace, diffs: List[EntryDiff]) -> None:
    """Execute the rollup command and print results to stdout.

    Args:
        args: Parsed CLI arguments (expects .top and .min_changes).
        diffs: List of EntryDiff objects to roll up.
    """
    rollup: DiffRollup = build_rollup(diffs)
    top_n: int = getattr(args, "top", 10)
    min_changes: int = getattr(args, "min_changes", 1)

    print(f"Rollup: {rollup.changed_entries}/{rollup.total_entries} entries changed")
    print()

    candidates = [fr for fr in rollup.top_fields(top_n) if fr.total >= min_changes]

    if not candidates:
        print("No fields meet the minimum change threshold.")
        return

    header = _format_rollup_row("Field", "Modified", "Added", "Removed", "Total")
    print(header)
    print("-" * len(header))

    for fr in candidates:
        print(_format_rollup_row(fr.field_name, fr.modified, fr.added, fr.removed, fr.total))
