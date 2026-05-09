"""Heatmap module: aggregates field-level change frequency into a heat score grid."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from logdiff.differ import EntryDiff


class HeatmapError(Exception):
    """Raised when heatmap generation fails."""


@dataclass
class FieldHeat:
    """Heat score for a single field across all diffs."""

    field_name: str
    modified: int = 0
    added: int = 0
    removed: int = 0

    @property
    def total(self) -> int:
        return self.modified + self.added + self.removed

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldHeat(field={self.field_name!r}, total={self.total}, "
            f"modified={self.modified}, added={self.added}, removed={self.removed})"
        )


@dataclass
class DiffHeatmap:
    """Aggregated heatmap across a collection of EntryDiffs."""

    field_heats: Dict[str, FieldHeat] = field(default_factory=dict)
    total_entries: int = 0

    def hottest_fields(self, top_n: int = 5) -> List[FieldHeat]:
        """Return the top-N fields by total change count, descending."""
        sorted_heats = sorted(
            self.field_heats.values(), key=lambda h: h.total, reverse=True
        )
        return sorted_heats[:top_n]

    def coverage(self) -> float:
        """Fraction of entries that had at least one changed field."""
        if self.total_entries == 0:
            return 0.0
        changed = sum(1 for h in self.field_heats.values() if h.total > 0)
        # coverage = unique fields changed / total entries (capped at 1.0)
        return min(changed / self.total_entries, 1.0)


def build_heatmap(diffs: Sequence[EntryDiff]) -> DiffHeatmap:
    """Aggregate field-level changes from *diffs* into a DiffHeatmap."""
    if not diffs:
        raise HeatmapError("Cannot build heatmap from an empty diff list.")

    heatmap = DiffHeatmap(total_entries=len(diffs))

    for entry_diff in diffs:
        for change in entry_diff.changes:
            fname = change.field
            if fname not in heatmap.field_heats:
                heatmap.field_heats[fname] = FieldHeat(field_name=fname)
            heat = heatmap.field_heats[fname]
            if change.before is None:
                heat.added += 1
            elif change.after is None:
                heat.removed += 1
            else:
                heat.modified += 1

    return heatmap
