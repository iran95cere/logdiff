"""Group diff results by a specified field value for structured analysis."""

from collections import defaultdict
from typing import Dict, List, Optional

from logdiff.differ import EntryDiff


class GroupingError(Exception):
    """Raised when grouping cannot be performed."""


def group_by_field(
    diffs: List[EntryDiff],
    field: str,
    source: str = "before",
) -> Dict[str, List[EntryDiff]]:
    """Group EntryDiff objects by the value of a field in their before or after entry.

    Args:
        diffs: List of EntryDiff objects to group.
        field: The field name to group by.
        source: Whether to read from 'before' or 'after' entry. Defaults to 'before'.

    Returns:
        A dict mapping field values to lists of EntryDiff objects.
        Entries where the field is missing are grouped under '__missing__'.

    Raises:
        GroupingError: If source is not 'before' or 'after'.
    """
    if source not in ("before", "after"):
        raise GroupingError(f"source must be 'before' or 'after', got: {source!r}")

    groups: Dict[str, List[EntryDiff]] = defaultdict(list)

    for diff in diffs:
        entry = diff.before if source == "before" else diff.after
        if entry is None:
            value = "__missing__"
        else:
            raw = entry.get(field)
            value = str(raw) if raw is not None else "__missing__"
        groups[value].append(diff)

    return dict(groups)


def group_summary(groups: Dict[str, List[EntryDiff]]) -> Dict[str, Dict[str, int]]:
    """Produce a summary count dict for each group.

    Returns:
        A dict mapping group keys to dicts with 'total' and 'changed' counts.
    """
    summary: Dict[str, Dict[str, int]] = {}
    for key, entries in groups.items():
        changed = sum(1 for d in entries if d.has_changes())
        summary[key] = {"total": len(entries), "changed": changed}
    return summary
