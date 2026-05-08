"""CLI integration for the diff profiler."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.profiler import profile_diffs, DiffProfile


def add_profiler_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'profile' subcommand."""
    parser = subparsers.add_parser(
        "profile",
        help="Show field-level change statistics across diffs.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show only the top N most volatile fields (0 = all).",
    )
    parser.add_argument(
        "--min-changes",
        type=int,
        default=1,
        metavar="N",
        help="Only include fields with at least N changes.",
    )
    parser.add_argument(
        "--show-density",
        action="store_true",
        default=False,
        help="Print the overall change density (changes per entry).",
    )


def handle_profiler(
    args: argparse.Namespace,
    diffs: List[EntryDiff],
) -> None:
    """Run the profiler and print results to stdout."""
    profile: DiffProfile = profile_diffs(diffs)

    if args.show_density:
        print(f"Change density: {profile.change_density:.2f} changes/entry")
        print(f"Total entries : {profile.total_entries}")
        print(f"Total changes : {profile.total_changes}")
        print()

    fields = [
        fp
        for fp in profile.fields.values()
        if fp.change_count >= args.min_changes
    ]
    fields.sort(key=lambda fp: fp.change_count, reverse=True)

    if args.top > 0:
        fields = fields[: args.top]

    if not fields:
        print("No fields match the given criteria.")
        return

    header = f"{'Field':<30} {'Changes':>8} {'Added':>7} {'Removed':>8} {'Modified':>9}"
    print(header)
    print("-" * len(header))
    for fp in fields:
        print(
            f"{fp.field_name:<30} {fp.change_count:>8} "
            f"{fp.added_count:>7} {fp.removed_count:>8} {fp.modified_count:>9}"
        )

    if profile.most_volatile_field:
        print()
        print(f"Most volatile field: {profile.most_volatile_field}")
