"""Field co-change correlation: detect which fields tend to change together."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from logdiff.differ import EntryDiff


class CorrError(Exception):
    """Raised when correlation analysis cannot be completed."""


@dataclass
class FieldPair:
    field_a: str
    field_b: str
    co_change_count: int = 0
    total_entries: int = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldPair({self.field_a!r}, {self.field_b!r}, "
            f"co_changes={self.co_change_count}, total={self.total_entries})"
        )

    @property
    def correlation(self) -> float:
        if self.total_entries == 0:
            return 0.0
        return self.co_change_count / self.total_entries


@dataclass
class CorrResult:
    pairs: List[FieldPair] = field(default_factory=list)
    entry_count: int = 0

    def top(self, n: int = 5) -> List[FieldPair]:
        return sorted(self.pairs, key=lambda p: p.correlation, reverse=True)[:n]


def build_corr(diffs: List[EntryDiff], min_count: int = 1) -> CorrResult:
    """Compute pairwise field co-change correlations across *diffs*.

    Args:
        diffs: list of EntryDiff objects to analyse.
        min_count: minimum co-change count to include a pair in the result.

    Returns:
        A CorrResult containing FieldPair statistics.

    Raises:
        CorrError: if *diffs* is empty.
    """
    if not diffs:
        raise CorrError("Cannot compute correlation on an empty diff list.")

    pair_counts: Dict[Tuple[str, str], int] = {}
    entry_count = len(diffs)

    for diff in diffs:
        changed_fields = sorted({c.field for c in diff.changes})
        for i, fa in enumerate(changed_fields):
            for fb in changed_fields[i + 1 :]:
                key = (fa, fb)
                pair_counts[key] = pair_counts.get(key, 0) + 1

    pairs = [
        FieldPair(
            field_a=fa,
            field_b=fb,
            co_change_count=count,
            total_entries=entry_count,
        )
        for (fa, fb), count in pair_counts.items()
        if count >= min_count
    ]

    return CorrResult(pairs=pairs, entry_count=entry_count)
