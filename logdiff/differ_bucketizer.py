"""Bucketize diff entries by numeric field ranges."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from logdiff.differ import EntryDiff


class BucketizerError(Exception):
    """Raised when bucketization fails."""


@dataclass
class Bucket:
    """A range bucket holding matching diffs."""

    label: str
    low: float
    high: float
    entries: List[EntryDiff] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Bucket({self.label!r}, count={self.count})"


@dataclass
class BucketResult:
    """Result of a bucketization operation."""

    target_field: str
    buckets: List[Bucket]

    @property
    def total_entries(self) -> int:
        return sum(b.count for b in self.buckets)

    def get(self, label: str) -> Optional[Bucket]:
        for b in self.buckets:
            if b.label == label:
                return b
        return None


def _extract_numeric(diff: EntryDiff, field_name: str) -> Optional[float]:
    """Return the numeric after-value for *field_name* in a diff, or None."""
    for change in diff.changes:
        if change.field == field_name and change.after is not None:
            try:
                return float(change.after)
            except (TypeError, ValueError):
                return None
    return None


def bucketize(
    diffs: List[EntryDiff],
    target_field: str,
    boundaries: List[float],
) -> BucketResult:
    """Group diffs into range buckets based on *target_field* numeric value.

    *boundaries* is a sorted list of split points, e.g. [0, 10, 100] produces
    buckets ``(-inf, 0)``, ``[0, 10)``, ``[10, 100)``, ``[100, +inf)``.
    """
    if not diffs:
        raise BucketizerError("Cannot bucketize an empty diff list.")
    if not boundaries:
        raise BucketizerError("At least one boundary value is required.")

    sorted_bounds = sorted(boundaries)
    edges: List[Tuple[float, float]] = []
    edges.append((float("-inf"), sorted_bounds[0]))
    for i in range(len(sorted_bounds) - 1):
        edges.append((sorted_bounds[i], sorted_bounds[i + 1]))
    edges.append((sorted_bounds[-1], float("inf")))

    def _label(lo: float, hi: float) -> str:
        lo_s = "-inf" if lo == float("-inf") else str(lo)
        hi_s = "+inf" if hi == float("inf") else str(hi)
        return f"[{lo_s}, {hi_s})"

    buckets = [Bucket(label=_label(lo, hi), low=lo, high=hi) for lo, hi in edges]

    for diff in diffs:
        value = _extract_numeric(diff, target_field)
        if value is None:
            continue
        for bucket in buckets:
            if bucket.low <= value < bucket.high:
                bucket.entries.append(diff)
                break

    return BucketResult(target_field=target_field, buckets=buckets)
