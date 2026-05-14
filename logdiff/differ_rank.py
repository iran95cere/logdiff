"""Rank diffs by a composite score across multiple dimensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff
from logdiff.scorer import ScoredDiff, score_diffs


class RankError(Exception):
    """Raised when ranking cannot be performed."""


@dataclass
class RankedDiff:
    """An EntryDiff with a computed rank and composite score."""

    diff: EntryDiff
    rank: int
    score: float
    change_count: int
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RankedDiff(rank={self.rank}, key={self.diff.key!r}, "
            f"score={self.score:.3f}, changes={self.change_count})"
        )


def rank_diffs(
    diffs: List[EntryDiff],
    *,
    top: Optional[int] = None,
    min_score: float = 0.0,
    status_weight: float = 2.0,
    field_weight: float = 1.0,
) -> List[RankedDiff]:
    """Rank *diffs* by composite score descending.

    Args:
        diffs: List of EntryDiff objects to rank.
        top: If given, return only the top-N results.
        min_score: Exclude entries whose score is below this threshold.
        status_weight: Multiplier applied to status-field changes.
        field_weight: Multiplier applied to ordinary field changes.

    Returns:
        Ordered list of RankedDiff, highest score first.

    Raises:
        RankError: If *diffs* is empty.
    """
    if not diffs:
        raise RankError("Cannot rank an empty diff list.")

    scored: List[ScoredDiff] = score_diffs(
        diffs,
        status_weight=status_weight,
        field_weight=field_weight,
    )

    filtered = [s for s in scored if s.score >= min_score]
    filtered.sort(key=lambda s: s.score, reverse=True)

    ranked: List[RankedDiff] = []
    for position, scored_diff in enumerate(filtered, start=1):
        change_count = len(scored_diff.diff.changes)
        ranked.append(
            RankedDiff(
                diff=scored_diff.diff,
                rank=position,
                score=scored_diff.score,
                change_count=change_count,
            )
        )

    if top is not None:
        ranked = ranked[:top]

    return ranked
