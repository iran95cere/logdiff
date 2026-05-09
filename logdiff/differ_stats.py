"""Field-level statistics aggregated across a list of EntryDiff objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict

from logdiff.differ import EntryDiff, FieldChange


class StatsError(ValueError):
    """Raised when stats cannot be computed from the provided diffs."""


@dataclass
class FieldStats:
    """Aggregated statistics for a single field across all diffs."""

    field_name: str
    modified_count: int = 0
    added_count: int = 0
    removed_count: int = 0

    @property
    def total_changes(self) -> int:
        return self.modified_count + self.added_count + self.removed_count

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldStats(field={self.field_name!r}, "
            f"modified={self.modified_count}, "
            f"added={self.added_count}, "
            f"removed={self.removed_count})"
        )


@dataclass
class DiffStats:
    """Top-level statistics computed from a collection of EntryDiff objects."""

    total_entries: int = 0
    changed_entries: int = 0
    unchanged_entries: int = 0
    field_stats: Dict[str, FieldStats] = field(default_factory=dict)

    @property
    def change_rate(self) -> float:
        if self.total_entries == 0:
            return 0.0
        return self.changed_entries / self.total_entries

    def top_fields(self, n: int = 5) -> List[FieldStats]:
        """Return the top *n* most frequently changed fields."""
        return sorted(
            self.field_stats.values(),
            key=lambda fs: fs.total_changes,
            reverse=True,
        )[:n]


def compute_stats(diffs: List[EntryDiff]) -> DiffStats:
    """Compute field-level statistics from *diffs*.

    Parameters
    ----------
    diffs:
        A list of :class:`~logdiff.differ.EntryDiff` objects to analyse.

    Raises
    ------
    StatsError
        If *diffs* is not a list.
    """
    if not isinstance(diffs, list):
        raise StatsError("diffs must be a list of EntryDiff objects")

    stats = DiffStats(total_entries=len(diffs))
    field_buckets: Dict[str, FieldStats] = defaultdict(
        lambda: FieldStats(field_name="")
    )

    for diff in diffs:
        if diff.has_changes():
            stats.changed_entries += 1
        else:
            stats.unchanged_entries += 1

        for change in diff.changes:
            fname = change.field
            if fname not in field_buckets:
                field_buckets[fname] = FieldStats(field_name=fname)
            fs = field_buckets[fname]
            if change.before is None:
                fs.added_count += 1
            elif change.after is None:
                fs.removed_count += 1
            else:
                fs.modified_count += 1

    stats.field_stats = dict(field_buckets)
    return stats
