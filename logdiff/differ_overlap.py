"""Overlap analysis: find fields that changed in both a before and after diff set."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from logdiff.differ import EntryDiff


class OverlapError(Exception):
    """Raised when overlap analysis cannot be performed."""


@dataclass
class FieldOverlap:
    """Overlap statistics for a single field."""

    field_name: str
    count_a: int = 0
    count_b: int = 0

    def __repr__(self) -> str:
        return (
            f"FieldOverlap(field={self.field_name!r}, "
            f"count_a={self.count_a}, count_b={self.count_b})"
        )

    @property
    def total(self) -> int:
        return self.count_a + self.count_b


@dataclass
class OverlapResult:
    """Result of comparing two sets of diffs for field-level overlap."""

    overlapping_fields: List[FieldOverlap] = field(default_factory=list)
    only_in_a: Set[str] = field(default_factory=set)
    only_in_b: Set[str] = field(default_factory=set)

    @property
    def overlap_count(self) -> int:
        return len(self.overlapping_fields)

    def top(self, n: int = 5) -> List[FieldOverlap]:
        return sorted(self.overlapping_fields, key=lambda f: f.total, reverse=True)[:n]


def _collect_changed_fields(diffs: List[EntryDiff]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for diff in diffs:
        for change in diff.changes:
            counts[change.field] = counts.get(change.field, 0) + 1
    return counts


def find_overlap(
    diffs_a: List[EntryDiff],
    diffs_b: List[EntryDiff],
) -> OverlapResult:
    """Find fields that appear in both diff sets and report their counts."""
    if not diffs_a and not diffs_b:
        raise OverlapError("Both diff sets are empty; nothing to compare.")

    counts_a = _collect_changed_fields(diffs_a)
    counts_b = _collect_changed_fields(diffs_b)

    fields_a = set(counts_a)
    fields_b = set(counts_b)
    shared = fields_a & fields_b

    overlapping = [
        FieldOverlap(
            field_name=f,
            count_a=counts_a[f],
            count_b=counts_b[f],
        )
        for f in sorted(shared)
    ]

    return OverlapResult(
        overlapping_fields=overlapping,
        only_in_a=fields_a - fields_b,
        only_in_b=fields_b - fields_a,
    )
