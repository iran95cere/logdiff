"""Field index builder for fast lookup of which entries changed a given field."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logdiff.differ import EntryDiff


class IndexError(Exception):  # noqa: A001
    """Raised when the index cannot be built or queried."""


@dataclass
class FieldIndexEntry:
    """Records which entry keys changed a specific field."""

    field_name: str
    entry_keys: List[str] = field(default_factory=list)
    change_types: Dict[str, str] = field(default_factory=dict)  # key -> change_type

    @property
    def count(self) -> int:
        return len(self.entry_keys)

    def __repr__(self) -> str:  # pragma: no cover
        return f"FieldIndexEntry(field={self.field_name!r}, count={self.count})"


@dataclass
class DiffIndex:
    """Inverted index mapping field names to the entries that changed them."""

    entries: Dict[str, FieldIndexEntry] = field(default_factory=dict)

    def lookup(self, field_name: str) -> Optional[FieldIndexEntry]:
        """Return the index entry for *field_name*, or None if not indexed."""
        return self.entries.get(field_name)

    def fields(self) -> List[str]:
        """Return all indexed field names, sorted alphabetically."""
        return sorted(self.entries.keys())

    def top(self, n: int = 5) -> List[FieldIndexEntry]:
        """Return the *n* most-changed fields by entry count."""
        sorted_entries = sorted(
            self.entries.values(), key=lambda e: e.count, reverse=True
        )
        return sorted_entries[:n]


def build_index(diffs: List[EntryDiff]) -> DiffIndex:
    """Build an inverted index from a list of :class:`EntryDiff` objects.

    Args:
        diffs: The list of entry diffs to index.

    Returns:
        A :class:`DiffIndex` mapping each changed field to the entries
        that contain that change.

    Raises:
        IndexError: If *diffs* is empty.
    """
    if not diffs:
        raise IndexError("Cannot build index from an empty diff list.")

    index: Dict[str, FieldIndexEntry] = {}

    for diff in diffs:
        for change in diff.changes:
            fname = change.field
            if fname not in index:
                index[fname] = FieldIndexEntry(field_name=fname)
            entry = index[fname]
            entry.entry_keys.append(diff.key)
            entry.change_types[diff.key] = change.change_type

    return DiffIndex(entries=index)
