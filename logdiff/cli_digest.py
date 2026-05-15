"""CLI handler for the `digest` subcommand."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_digest import DigestError, build_digest


def add_digest_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the `digest` subcommand with its arguments."""
    parser = subparsers.add_parser(
        "digest",
        help="Print a compact fingerprint digest of a diff set.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of top changed fields to display (default: 5).",
    )
    parser.add_argument(
        "--fingerprint-only",
        action="store_true",
        default=False,
        help="Print only the SHA-256 fingerprint and exit.",
    )


def handle_digest(
    args: argparse.Namespace,
    diffs: List[EntryDiff],
) -> int:
    """Handle the `digest` subcommand.

    Args:
        args: Parsed CLI arguments (expects ``top`` and ``fingerprint_only``).
        diffs: Pre-computed list of EntryDiff objects.

    Returns:
        Exit code (0 on success, 1 on error).
    """
    try:
        digest = build_digest(diffs, top_n=args.top)
    except DigestError as exc:
        print(f"digest error: {exc}")
        return 1

    if args.fingerprint_only:
        print(digest.fingerprint)
        return 0

    print(f"Entries   : {digest.entry_count}")
    print(f"Changed   : {digest.changed_count}")
    print(f"Fields    : {digest.field_count}")
    if digest.top_fields:
        print(f"Top fields: {', '.join(digest.top_fields)}")
    else:
        print("Top fields: (none)")
    print(f"Fingerprint: {digest.fingerprint}")
    return 0
