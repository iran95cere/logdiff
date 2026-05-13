"""Trend analysis across multiple diff snapshots over time."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class TrendError(Exception):
    """Raised when trend analysis fails."""


@dataclass
class TrendPoint:
    """A single data point in a trend series."""

    label: str
    total_entries: int
    changed_entries: int
    change_rate: float

    def __repr__(self) -> str:
        return (
            f"TrendPoint(label={self.label!r}, "
            f"change_rate={self.change_rate:.2f})"
        )


@dataclass
class FieldTrend:
    """Trend data for a single field across snapshots."""

    field: str
    counts: List[int] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(self.counts)

    @property
    def is_growing(self) -> bool:
        if len(self.counts) < 2:
            return False
        return self.counts[-1] > self.counts[0]

    @property
    def is_shrinking(self) -> bool:
        if len(self.counts) < 2:
            return False
        return self.counts[-1] < self.counts[0]


@dataclass
class DiffTrend:
    """Aggregated trend report across multiple snapshots."""

    points: List[TrendPoint]
    field_trends: Dict[str, FieldTrend]

    @property
    def avg_change_rate(self) -> float:
        if not self.points:
            return 0.0
        return sum(p.change_rate for p in self.points) / len(self.points)

    def most_volatile_fields(self, top: int = 5) -> List[FieldTrend]:
        sorted_fields = sorted(
            self.field_trends.values(), key=lambda f: f.total, reverse=True
        )
        return sorted_fields[:top]


def build_trend(snapshots: List[Dict]) -> DiffTrend:
    """Build a DiffTrend from a list of snapshot dicts.

    Each snapshot dict must have:
      - 'label': str
      - 'diffs': list of EntryDiff-like objects with .changes list
    """
    if not snapshots:
        raise TrendError("At least one snapshot is required to build a trend.")

    points: List[TrendPoint] = []
    field_trends: Dict[str, FieldTrend] = {}

    for snap in snapshots:
        label = snap.get("label", "unknown")
        diffs = snap.get("diffs", [])
        total = len(diffs)
        changed = sum(1 for d in diffs if d.has_changes())
        rate = (changed / total) if total > 0 else 0.0
        points.append(TrendPoint(label=label, total_entries=total,
                                  changed_entries=changed, change_rate=rate))

        for diff in diffs:
            for change in diff.changes:
                ft = field_trends.setdefault(
                    change.field, FieldTrend(field=change.field)
                )
                while len(ft.counts) < len(points):
                    ft.counts.append(0)
                ft.counts[-1] += 1

        for ft in field_trends.values():
            while len(ft.counts) < len(points):
                ft.counts.append(0)

    return DiffTrend(points=points, field_trends=field_trends)
