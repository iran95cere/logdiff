"""CLI integration for the diff ranking feature."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_rank import RankError, RankedDiff, rank_diffs


def add_rank_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *rank* sub-command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "rank",
        help="Rank diffs by composite change score.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N results (default: all).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        dest="min_score",
        metavar="SCORE",
        help="Exclude entries with score below this threshold (default: 0).",
    )
    parser.add_argument(
        "--status-weight",
        type=float,
        default=2.0,
        dest="status_weight",
        help="Score multiplier for status-field changes (default: 2.0).",
    )
    parser.add_argument(
        "--field-weight",
        type=float,
        default=1.0,
        dest="field_weight",
        help="Score multiplier for ordinary field changes (default: 1.0).",
    )


def handle_rank(
    args: argparse.Namespace,
    diffs: List[EntryDiff],
) -> None:
    """Execute the *rank* sub-command."""
    try:
        ranked: List[RankedDiff] = rank_diffs(
            diffs,
            top=args.top,
            min_score=args.min_score,
            status_weight=args.status_weight,
            field_weight=args.field_weight,
        )
    except RankError as exc:
        print(f"rank: {exc}")
        return

    if not ranked:
        print("No entries meet the ranking criteria.")
        return

    header = f"{'Rank':>4}  {'Key':<30}  {'Score':>8}  {'Changes':>7}"
    print(header)
    print("-" * len(header))
    for rd in ranked:
        key_str = str(rd.diff.key) if rd.diff.key is not None else "<no key>"
        print(f"{rd.rank:>4}  {key_str:<30}  {rd.score:>8.3f}  {rd.change_count:>7}")
