"""CLI sub-command for field-change frequency analysis."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_frequency import build_frequency, FrequencyError


def add_frequency_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *frequency* sub-command."""
    p = subparsers.add_parser(
        "frequency",
        help="Show how often each field changes across all entries.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of top fields to display (default: 10).",
    )
    p.add_argument(
        "--min-freq",
        type=float,
        default=0.0,
        dest="min_freq",
        metavar="RATE",
        help="Only show fields with frequency >= RATE (0.0–1.0).",
    )
    p.set_defaults(func=handle_frequency)


def handle_frequency(args: argparse.Namespace, diffs: List[EntryDiff]) -> int:
    """Execute the frequency sub-command.

    Returns an exit code (0 = success, 1 = error).
    """
    try:
        result = build_frequency(diffs)
    except FrequencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    candidates = result.top(args.top)
    filtered = [ff for ff in candidates if ff.frequency >= args.min_freq]

    if not filtered:
        print("No fields matched the given criteria.")
        return 0

    print(f"Field change frequency ({result.entry_count} entries):\n")
    header = f"  {'Field':<30} {'Changes':>8}  {'Frequency':>10}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for ff in filtered:
        print(f"  {ff.field_name:<30} {ff.change_count:>8}  {ff.frequency:>9.2%}")

    return 0
