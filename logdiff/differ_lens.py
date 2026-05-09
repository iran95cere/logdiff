"""Lens module: focus diff analysis on a subset of fields with depth-aware extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff, FieldChange


class LensError(Exception):
    """Raised when lens configuration or application fails."""


@dataclass
class LensResult:
    """A focused view of an EntryDiff restricted to selected fields."""

    entry_id: str
    focused_changes: List[FieldChange]
    omitted_count: int

    def has_changes(self) -> bool:
        return bool(self.focused_changes)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"LensResult(entry_id={self.entry_id!r}, "
            f"focused={len(self.focused_changes)}, omitted={self.omitted_count})"
        )


def _field_matches(field_name: str, patterns: List[str]) -> bool:
    """Return True if field_name matches any pattern (prefix or exact)."""
    for pattern in patterns:
        if field_name == pattern or field_name.startswith(pattern + "."):
            return True
    return False


def apply_lens(
    diffs: List[EntryDiff],
    fields: List[str],
    require_all: bool = False,
) -> List[LensResult]:
    """Focus a list of EntryDiff objects on the given field names/prefixes.

    Args:
        diffs: List of EntryDiff objects to process.
        fields: Field names or dot-prefix patterns to include.
        require_all: If True, only include results where every focused field
                     has a change (AND semantics). Default is OR semantics.

    Returns:
        List of LensResult objects (only entries with at least one focused change).

    Raises:
        LensError: If fields list is empty.
    """
    if not fields:
        raise LensError("fields list must not be empty")

    results: List[LensResult] = []

    for diff in diffs:
        all_changes = diff.changes
        focused = [c for c in all_changes if _field_matches(c.field, fields)]
        omitted = len(all_changes) - len(focused)

        if not focused:
            continue

        if require_all:
            matched_patterns = {p for p in fields if any(_field_matches(c.field, [p]) for c in focused)}
            if matched_patterns != set(fields):
                continue

        results.append(
            LensResult(
                entry_id=diff.entry_id,
                focused_changes=focused,
                omitted_count=omitted,
            )
        )

    return results
