"""Field-level comparison utilities for structured log entry diffs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff, FieldChange


class CompareError(Exception):
    """Raised when comparison cannot be performed."""


@dataclass
class CompareResult:
    """Result of comparing two sets of diffs by a shared dimension."""

    label_a: str
    label_b: str
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    in_both: List[str] = field(default_factory=list)
    change_delta: int = 0  # positive means b has more changes

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CompareResult({self.label_a!r} vs {self.label_b!r}, "
            f"only_a={len(self.only_in_a)}, only_b={len(self.only_in_b)}, "
            f"shared={len(self.in_both)}, delta={self.change_delta:+d})"
        )


def _changed_entry_keys(diffs: List[EntryDiff]) -> set:
    return {d.key for d in diffs if d.has_changes()}


def _total_change_count(diffs: List[EntryDiff]) -> int:
    return sum(len(d.changes) for d in diffs)


def compare_diff_sets(
    diffs_a: List[EntryDiff],
    diffs_b: List[EntryDiff],
    label_a: str = "A",
    label_b: str = "B",
) -> CompareResult:
    """Compare two lists of EntryDiff by entry key presence and change volume."""
    if not isinstance(diffs_a, list) or not isinstance(diffs_b, list):
        raise CompareError("Both inputs must be lists of EntryDiff.")

    keys_a = _changed_entry_keys(diffs_a)
    keys_b = _changed_entry_keys(diffs_b)

    only_a = sorted(keys_a - keys_b)
    only_b = sorted(keys_b - keys_a)
    shared = sorted(keys_a & keys_b)

    delta = _total_change_count(diffs_b) - _total_change_count(diffs_a)

    return CompareResult(
        label_a=label_a,
        label_b=label_b,
        only_in_a=only_a,
        only_in_b=only_b,
        in_both=shared,
        change_delta=delta,
    )
