"""Field change frequency analysis across diff sets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from logdiff.differ import EntryDiff


class FrequencyError(Exception):
    """Raised when frequency analysis cannot be completed."""


@dataclass
class FieldFrequency:
    """Frequency statistics for a single field."""
    field_name: str
    change_count: int
    entry_count: int

    @property
    def frequency(self) -> float:
        """Fraction of entries in which this field changed."""
        if self.entry_count == 0:
            return 0.0
        return self.change_count / self.entry_count

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldFrequency(field={self.field_name!r}, "
            f"count={self.change_count}, freq={self.frequency:.2%})"
        )


@dataclass
class FrequencyResult:
    """Aggregated field-change frequency across a list of diffs."""
    entry_count: int
    field_frequencies: List[FieldFrequency] = field(default_factory=list)

    def top(self, n: int = 10) -> List[FieldFrequency]:
        """Return the *n* most frequently changed fields."""
        return sorted(
            self.field_frequencies, key=lambda f: f.frequency, reverse=True
        )[:n]

    def get(self, field_name: str) -> FieldFrequency | None:
        """Look up a specific field by name."""
        for ff in self.field_frequencies:
            if ff.field_name == field_name:
                return ff
        return None


def build_frequency(diffs: List[EntryDiff]) -> FrequencyResult:
    """Compute per-field change frequency over *diffs*.

    Raises FrequencyError if *diffs* is empty.
    """
    if not diffs:
        raise FrequencyError("Cannot compute frequency from an empty diff list.")

    entry_count = len(diffs)
    counts: Dict[str, int] = {}

    for diff in diffs:
        for change in diff.changes:
            counts[change.field] = counts.get(change.field, 0) + 1

    field_frequencies = [
        FieldFrequency(
            field_name=fname,
            change_count=cnt,
            entry_count=entry_count,
        )
        for fname, cnt in counts.items()
    ]

    return FrequencyResult(
        entry_count=entry_count,
        field_frequencies=field_frequencies,
    )
