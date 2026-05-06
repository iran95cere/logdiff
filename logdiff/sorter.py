"""Sorting utilities for log diff entries and field changes."""

from typing import List, Optional
from logdiff.differ import EntryDiff


SORT_KEYS = ("key", "change_count", "status")


def sort_diffs(
    diffs: List[EntryDiff],
    by: str = "key",
    reverse: bool = False,
) -> List[EntryDiff]:
    """Sort a list of EntryDiff objects by a given attribute.

    Args:
        diffs: List of EntryDiff instances to sort.
        by: Attribute to sort by. One of 'key', 'change_count', 'status'.
        reverse: If True, sort in descending order.

    Returns:
        A new sorted list of EntryDiff instances.

    Raises:
        ValueError: If *by* is not a recognised sort key.
    """
    if by not in SORT_KEYS:
        raise ValueError(
            f"Invalid sort key {by!r}. Choose from: {', '.join(SORT_KEYS)}"
        )

    if by == "key":
        key_fn = lambda d: (d.key or "")
    elif by == "change_count":
        key_fn = lambda d: len(d.changes)
    elif by == "status":
        key_fn = lambda d: (d.status or "")
    else:  # pragma: no cover
        key_fn = lambda d: (d.key or "")

    return sorted(diffs, key=key_fn, reverse=reverse)


def sort_diffs_by_most_changed(
    diffs: List[EntryDiff],
    top_n: Optional[int] = None,
) -> List[EntryDiff]:
    """Return diffs ordered from most to fewest field changes.

    Args:
        diffs: List of EntryDiff instances.
        top_n: If provided, return only the top N entries.

    Returns:
        Sorted (and optionally truncated) list of EntryDiff instances.
    """
    sorted_diffs = sort_diffs(diffs, by="change_count", reverse=True)
    if top_n is not None:
        return sorted_diffs[:top_n]
    return sorted_diffs
