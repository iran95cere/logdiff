"""Drift detection: identify fields whose change rate has shifted significantly
between two sets of diffs (e.g. two deployment windows)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from logdiff.differ import EntryDiff


class DriftError(Exception):
    """Raised when drift detection cannot be performed."""


@dataclass
class FieldDrift:
    field_name: str
    rate_before: float  # fraction of entries where this field changed
    rate_after: float

    @property
    def delta(self) -> float:
        return self.rate_after - self.rate_before

    @property
    def is_growing(self) -> bool:
        return self.delta > 0

    def __repr__(self) -> str:  # pragma: no cover
        direction = "+" if self.delta >= 0 else ""
        return (
            f"FieldDrift({self.field_name!r}, "
            f"before={self.rate_before:.2%}, "
            f"after={self.rate_after:.2%}, "
            f"delta={direction}{self.delta:.2%})"
        )


@dataclass
class DriftReport:
    drifted_fields: List[FieldDrift] = field(default_factory=list)
    threshold: float = 0.05

    @property
    def significant(self) -> List[FieldDrift]:
        """Fields whose absolute delta exceeds the threshold."""
        return [f for f in self.drifted_fields if abs(f.delta) >= self.threshold]

    def top(self, n: int = 5) -> List[FieldDrift]:
        return sorted(self.drifted_fields, key=lambda f: abs(f.delta), reverse=True)[:n]


def _field_change_rates(diffs: List[EntryDiff]) -> Dict[str, float]:
    """Return {field: fraction_of_entries_with_change} for a list of diffs."""
    if not diffs:
        return {}
    counts: Dict[str, int] = {}
    for d in diffs:
        for change in d.changes:
            counts[change.field] = counts.get(change.field, 0) + 1
    total = len(diffs)
    return {f: c / total for f, c in counts.items()}


def detect_drift(
    before: List[EntryDiff],
    after: List[EntryDiff],
    threshold: float = 0.05,
) -> DriftReport:
    """Compare per-field change rates between *before* and *after* diff sets."""
    if not before:
        raise DriftError("'before' diff list must not be empty")
    if not after:
        raise DriftError("'after' diff list must not be empty")

    rates_before = _field_change_rates(before)
    rates_after = _field_change_rates(after)

    all_fields = set(rates_before) | set(rates_after)
    drifted: List[FieldDrift] = []
    for f in sorted(all_fields):
        rb = rates_before.get(f, 0.0)
        ra = rates_after.get(f, 0.0)
        drifted.append(FieldDrift(field_name=f, rate_before=rb, rate_after=ra))

    drifted.sort(key=lambda fd: abs(fd.delta), reverse=True)
    return DriftReport(drifted_fields=drifted, threshold=threshold)
