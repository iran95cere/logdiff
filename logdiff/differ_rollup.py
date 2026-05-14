"""Roll up field-level changes into a compact per-field summary across many diffs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from logdiff.differ import EntryDiff, FieldChange


class RollupError(Exception):
    """Raised when rollup cannot be computed."""


@dataclass
class FieldRollup:
    """Aggregated statistics for a single field across all diffs."""

    field_name: str
    modified: int = 0
    added: int = 0
    removed: int = 0

    @property
    def total(self) -> int:
        return self.modified + self.added + self.removed

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldRollup({self.field_name!r}, "
            f"modified={self.modified}, added={self.added}, removed={self.removed})"
        )


@dataclass
class DiffRollup:
    """Rollup of all field changes across a list of EntryDiffs."""

    fields: Dict[str, FieldRollup] = field(default_factory=dict)
    total_entries: int = 0
    changed_entries: int = 0

    def top_fields(self, n: int = 5) -> List[FieldRollup]:
        """Return the n most frequently changed fields."""
        return sorted(self.fields.values(), key=lambda r: r.total, reverse=True)[:n]


def build_rollup(diffs: List[EntryDiff]) -> DiffRollup:
    """Build a DiffRollup from a list of EntryDiffs.

    Args:
        diffs: List of EntryDiff objects to aggregate.

    Returns:
        A DiffRollup summarising field-level activity.

    Raises:
        RollupError: If diffs is empty.
    """
    if not diffs:
        raise RollupError("Cannot build rollup from an empty diff list.")

    rollup = DiffRollup(total_entries=len(diffs))

    for entry_diff in diffs:
        if entry_diff.has_changes():
            rollup.changed_entries += 1

        for change in entry_diff.changes:
            fr = rollup.fields.setdefault(change.field, FieldRollup(field_name=change.field))
            if change.before is None:
                fr.added += 1
            elif change.after is None:
                fr.removed += 1
            else:
                fr.modified += 1

    return rollup
