"""CLI integration for diff scoring — adds --top-n and --min-score flags."""

import argparse
from typing import List, Optional

from logdiff.differ import EntryDiff
from logdiff.scorer import score_diffs, top_n, ScoredDiff


def add_scorer_args(parser: argparse.ArgumentParser) -> None:
    """Register scoring-related CLI arguments onto an existing parser."""
    group = parser.add_argument_group("scoring")
    group.add_argument(
        "--top-n",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N highest-scoring diffs.",
    )
    group.add_argument(
        "--min-score",
        type=float,
        default=None,
        metavar="SCORE",
        help="Exclude diffs with a score below this threshold.",
    )
    group.add_argument(
        "--show-scores",
        action="store_true",
        default=False,
        help="Print the numeric score next to each diff entry.",
    )


def handle_scorer(
    diffs: List[EntryDiff],
    args: argparse.Namespace,
) -> List[EntryDiff]:
    """Apply scoring filters and return a (possibly reduced) list of EntryDiffs.

    Scoring is only applied when --top-n or --min-score is provided.
    """
    top_n_val: Optional[int] = getattr(args, "top_n", None)
    min_score_val: Optional[float] = getattr(args, "min_score", None)

    if top_n_val is None and min_score_val is None:
        return diffs

    scored: List[ScoredDiff] = score_diffs(diffs)

    if min_score_val is not None:
        scored = [s for s in scored if s.score >= min_score_val]

    if top_n_val is not None:
        scored = top_n(scored, top_n_val)

    return [s.entry_diff for s in scored]
