"""Compute change velocity: rate of change per field across ordered diff snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from logdiff.differ import EntryDiff


class VelocityError(Exception):
    """Raised when velocity computation fails."""


@dataclass
class FieldVelocity:
    field_name: str
    counts: List[int]  # change count per snapshot
    snapshots: List[str]  # snapshot labels

    def __repr__(self) -> str:
        return f"FieldVelocity(field={self.field_name!r}, avg={self.average:.2f})"

    @property
    def average(self) -> float:
        if not self.counts:
            return 0.0
        return sum(self.counts) / len(self.counts)

    @property
    def peak(self) -> int:
        return max(self.counts, default=0)

    @property
    def is_accelerating(self) -> bool:
        """True if the last interval has more changes than the first."""
        if len(self.counts) < 2:
            return False
        return self.counts[-1] > self.counts[0]


@dataclass
class VelocityReport:
    snapshots: List[str]
    field_velocities: List[FieldVelocity] = field(default_factory=list)

    @property
    def top_field(self) -> Optional[FieldVelocity]:
        if not self.field_velocities:
            return None
        return max(self.field_velocities, key=lambda fv: fv.average)


def build_velocity(
    snapshot_diffs: List[tuple[str, List[EntryDiff]]],
    top: int = 10,
) -> VelocityReport:
    """Build a velocity report from ordered (label, diffs) snapshot pairs."""
    if not snapshot_diffs:
        raise VelocityError("At least one snapshot is required to compute velocity.")

    labels = [label for label, _ in snapshot_diffs]
    field_counts: Dict[str, List[int]] = {}

    for _label, diffs in snapshot_diffs:
        snapshot_field_counts: Dict[str, int] = {}
        for diff in diffs:
            for change in diff.changes:
                snapshot_field_counts[change.field] = (
                    snapshot_field_counts.get(change.field, 0) + 1
                )
        for fname, cnt in snapshot_field_counts.items():
            field_counts.setdefault(fname, [0] * len(snapshot_diffs))
        for fname in field_counts:
            idx = labels.index(_label)
            field_counts[fname][idx] = snapshot_field_counts.get(fname, 0)

    velocities = [
        FieldVelocity(field_name=fname, counts=counts, snapshots=labels)
        for fname, counts in field_counts.items()
    ]
    velocities.sort(key=lambda fv: fv.average, reverse=True)

    return VelocityReport(
        snapshots=labels,
        field_velocities=velocities[:top],
    )
