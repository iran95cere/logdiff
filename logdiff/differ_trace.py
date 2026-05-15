"""Trace field changes across a sequence of diff snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from logdiff.differ import EntryDiff


class TraceError(Exception):
    """Raised when trace construction fails."""


@dataclass
class TracePoint:
    """A single observation of a field value at a snapshot label."""

    label: str
    value: Any

    def __repr__(self) -> str:  # pragma: no cover
        return f"TracePoint(label={self.label!r}, value={self.value!r})"


@dataclass
class FieldTrace:
    """Full trace of a single field across snapshots."""

    field_name: str
    points: List[TracePoint] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        """Number of times the value changed between consecutive points."""
        changes = 0
        for i in range(1, len(self.points)):
            if self.points[i].value != self.points[i - 1].value:
                changes += 1
        return changes

    @property
    def is_stable(self) -> bool:
        return self.total_changes == 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldTrace(field={self.field_name!r}, "
            f"points={len(self.points)}, changes={self.total_changes})"
        )


@dataclass
class TraceResult:
    """Collection of field traces built from labelled diff snapshots."""

    traces: Dict[str, FieldTrace] = field(default_factory=dict)

    def get(self, field_name: str) -> Optional[FieldTrace]:
        return self.traces.get(field_name)

    @property
    def unstable_fields(self) -> List[str]:
        return [name for name, t in self.traces.items() if not t.is_stable]


def build_trace(
    snapshots: List[tuple[str, List[EntryDiff]]],
    key_field: str = "id",
) -> TraceResult:
    """Build per-field traces from a list of (label, diffs) pairs.

    Args:
        snapshots: Ordered list of (label, diffs) pairs.
        key_field: Field used to align entries across snapshots.

    Returns:
        TraceResult containing FieldTrace objects.
    """
    if not snapshots:
        raise TraceError("At least one snapshot is required to build a trace.")

    result = TraceResult()

    for label, diffs in snapshots:
        for diff in diffs:
            for change in diff.changes:
                fname = change.field
                if fname not in result.traces:
                    result.traces[fname] = FieldTrace(field_name=fname)
                value = change.after
                result.traces[fname].points.append(TracePoint(label=label, value=value))

    return result
