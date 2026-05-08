"""CLI integration for watchlist feature."""

import argparse
from typing import List

from logdiff.watchlist import Watchlist, WatchlistError, match_watchlist, summarize_watchlist_matches
from logdiff.differ import EntryDiff


def add_watchlist_args(parser: argparse.ArgumentParser) -> None:
    """Register --watch and --watch-summary flags on an argument parser."""
    parser.add_argument(
        "--watch",
        metavar="FIELD",
        nargs="+",
        default=[],
        help="Watch specific fields and surface only diffs that touch them.",
    )
    parser.add_argument(
        "--watch-summary",
        action="store_true",
        default=False,
        help="Print a summary of watchlist hits instead of full diff output.",
    )


def handle_watchlist(
    args: argparse.Namespace,
    diffs: List[EntryDiff],
) -> List[EntryDiff]:
    """Filter diffs by watchlist if --watch flags are provided.

    Returns the filtered list of EntryDiff objects.  When --watch-summary is
    set the summary is printed to stdout and the original list is returned
    unchanged so downstream rendering is skipped by the caller.
    """
    if not getattr(args, "watch", None):
        return diffs

    watchlist = Watchlist()
    for f in args.watch:
        try:
            watchlist.add(f)
        except WatchlistError as exc:
            print(f"[watchlist] warning: {exc}")

    try:
        matches = match_watchlist(diffs, watchlist)
    except WatchlistError as exc:
        print(f"[watchlist] error: {exc}")
        return diffs

    if getattr(args, "watch_summary", False):
        summary = summarize_watchlist_matches(matches)
        print(f"Watchlist summary: {summary['total_matches']} match(es)")
        for field_name, count in sorted(summary["field_hits"].items()):
            print(f"  {field_name}: {count} hit(s)")
        return []

    return [m.entry_diff for m in matches]
