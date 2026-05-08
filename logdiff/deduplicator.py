"""Deduplicator: remove or flag duplicate EntryDiff objects based on key and change fingerprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from logdiff.differ import EntryDiff, FieldChange


class DeduplicatorError(Exception):
    """Raised when deduplication encounters an invalid state."""


def _change_fingerprint(changes: List[FieldChange]) -> Tuple:
    """Return a hashable fingerprint for a list of FieldChange objects."""
    return tuple(
        sorted((c.field, c.before, c.after) for c in changes)
    )


def deduplicate(diffs: List[EntryDiff], key: str = "key") -> List[EntryDiff]:
    """Return diffs with exact duplicates removed.

    Two EntryDiff objects are considered duplicates when they share the same
    *key* value AND have an identical set of field changes.

    Args:
        diffs: List of EntryDiff objects to process.
        key:   The attribute on EntryDiff used to identify an entry (default ``"key"``).

    Returns:
        Deduplicated list preserving first-occurrence order.
    """
    if not diffs:
        return []

    seen: Dict[Tuple, bool] = {}
    result: List[EntryDiff] = []

    for diff in diffs:
        entry_key = getattr(diff, key, None)
        fingerprint = (entry_key, _change_fingerprint(diff.changes))
        if fingerprint not in seen:
            seen[fingerprint] = True
            result.append(diff)

    return result


@dataclass
class DeduplicationReport:
    """Summary produced by :func:`deduplicate_with_report`."""

    original_count: int
    deduplicated_count: int
    removed_keys: List[str] = field(default_factory=list)

    @property
    def duplicates_removed(self) -> int:
        return self.original_count - self.deduplicated_count


def deduplicate_with_report(
    diffs: List[EntryDiff], key: str = "key"
) -> Tuple[List[EntryDiff], DeduplicationReport]:
    """Deduplicate *diffs* and return both the cleaned list and a report.

    Args:
        diffs: List of EntryDiff objects to process.
        key:   The attribute on EntryDiff used to identify an entry.

    Returns:
        A tuple of (deduplicated list, DeduplicationReport).
    """
    original_count = len(diffs)
    seen: Dict[Tuple, bool] = {}
    result: List[EntryDiff] = []
    removed_keys: List[str] = []

    for diff in diffs:
        entry_key = getattr(diff, key, None)
        fingerprint = (entry_key, _change_fingerprint(diff.changes))
        if fingerprint not in seen:
            seen[fingerprint] = True
            result.append(diff)
        else:
            removed_keys.append(str(entry_key))

    report = DeduplicationReport(
        original_count=original_count,
        deduplicated_count=len(result),
        removed_keys=removed_keys,
    )
    return result, report
