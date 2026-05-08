"""Field-level profiling: compute statistics about change frequency across diffs."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from logdiff.differ import EntryDiff, FieldChange


class ProfilerError(Exception):
    """Raised when profiling cannot be completed."""


@dataclass
class FieldProfile:
    """Statistics for a single field across all diffs."""

    field_name: str
    change_count: int = 0
    added_count: int = 0
    removed_count: int = 0
    modified_count: int = 0
    unique_before_values: int = 0
    unique_after_values: int = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldProfile(field={self.field_name!r}, changes={self.change_count}, "
            f"added={self.added_count}, removed={self.removed_count}, "
            f"modified={self.modified_count})"
        )


@dataclass
class DiffProfile:
    """Aggregated profiling result across a list of EntryDiffs."""

    total_entries: int = 0
    total_changes: int = 0
    fields: Dict[str, FieldProfile] = field(default_factory=dict)

    @property
    def most_volatile_field(self) -> Optional[str]:
        """Return the field name with the highest change count."""
        if not self.fields:
            return None
        return max(self.fields, key=lambda f: self.fields[f].change_count)

    @property
    def change_density(self) -> float:
        """Average number of field changes per entry."""
        if self.total_entries == 0:
            return 0.0
        return self.total_changes / self.total_entries


def profile_diffs(diffs: List[EntryDiff]) -> DiffProfile:
    """Build a DiffProfile from a list of EntryDiff objects."""
    if not isinstance(diffs, list):
        raise ProfilerError("diffs must be a list of EntryDiff objects")

    result = DiffProfile(total_entries=len(diffs))
    before_values: Dict[str, Counter] = defaultdict(Counter)
    after_values: Dict[str, Counter] = defaultdict(Counter)

    for entry in diffs:
        for change in entry.changes:
            fname = change.field
            if fname not in result.fields:
                result.fields[fname] = FieldProfile(field_name=fname)

            prof = result.fields[fname]
            prof.change_count += 1
            result.total_changes += 1

            if change.before is None and change.after is not None:
                prof.added_count += 1
            elif change.before is not None and change.after is None:
                prof.removed_count += 1
            else:
                prof.modified_count += 1

            if change.before is not None:
                before_values[fname][str(change.before)] += 1
            if change.after is not None:
                after_values[fname][str(change.after)] += 1

    for fname, prof in result.fields.items():
        prof.unique_before_values = len(before_values[fname])
        prof.unique_after_values = len(after_values[fname])

    return result
