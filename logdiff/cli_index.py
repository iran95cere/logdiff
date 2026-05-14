"""CLI sub-command: build and query the field index."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_index import DiffIndex, build_index


def add_index_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *index* sub-command onto *subparsers*."""
    parser = subparsers.add_parser(
        "index",
        help="Build an inverted field index and query which entries changed a field.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Show the top N most-changed fields (default: 10).",
    )
    parser.add_argument(
        "--field",
        metavar="FIELD",
        default=None,
        help="Look up a specific field and list affected entry keys.",
    )


def handle_index(
    args: argparse.Namespace,
    diffs: List[EntryDiff],
) -> None:
    """Execute the *index* sub-command.

    Args:
        args: Parsed CLI arguments (expects ``top`` and ``field`` attributes).
        diffs: The list of entry diffs to index.
    """
    from logdiff.differ_index import IndexError as IdxError  # local to avoid shadowing

    try:
        idx: DiffIndex = build_index(diffs)
    except IdxError as exc:
        print(f"[index] error: {exc}")
        return

    if args.field:
        entry = idx.lookup(args.field)
        if entry is None:
            print(f"Field '{args.field}' not found in index.")
        else:
            print(f"Field '{args.field}' changed in {entry.count} entr(ies):")
            for key in entry.entry_keys:
                change_type = entry.change_types.get(key, "unknown")
                print(f"  {key}  [{change_type}]")
        return

    top_entries = idx.top(n=args.top)
    if not top_entries:
        print("No field changes found.")
        return

    print(f"Top {args.top} most-changed fields:")
    print(f"  {'Field':<30} {'Entries Changed':>15}")
    print(f"  {'-'*30} {'-'*15}")
    for entry in top_entries:
        print(f"  {entry.field_name:<30} {entry.count:>15}")
