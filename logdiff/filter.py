"""Field-level filtering for log diff results."""

from __future__ import annotations

from typing import Iterable, Optional

from logdiff.differ import EntryDiff, FieldChange


def filter_by_fields(
    diffs: Iterable[EntryDiff],
    include_fields: Optional[list[str]] = None,
    exclude_fields: Optional[list[str]] = None,
) -> list[EntryDiff]:
    """Return diffs with changes restricted to the specified fields.

    Args:
        diffs: Iterable of EntryDiff objects to filter.
        include_fields: If provided, only changes for these field names are kept.
        exclude_fields: If provided, changes for these field names are removed.

    Returns:
        A new list of EntryDiff objects.  Entries whose change list becomes
        empty after filtering are omitted entirely.
    """
    result: list[EntryDiff] = []

    for entry in diffs:
        filtered = _filter_changes(
            entry.changes,
            include_fields=include_fields,
            exclude_fields=exclude_fields,
        )
        if filtered:
            result.append(
                EntryDiff(
                    key=entry.key,
                    changes=filtered,
                    status=entry.status,
                )
            )

    return result


def _filter_changes(
    changes: list[FieldChange],
    include_fields: Optional[list[str]],
    exclude_fields: Optional[list[str]],
) -> list[FieldChange]:
    """Apply include/exclude field filters to a list of FieldChange objects."""
    result: list[FieldChange] = []

    for change in changes:
        if include_fields is not None and change.field not in include_fields:
            continue
        if exclude_fields is not None and change.field in exclude_fields:
            continue
        result.append(change)

    return result


def filter_by_status(
    diffs: Iterable[EntryDiff],
    statuses: list[str],
) -> list[EntryDiff]:
    """Return only diffs whose status is in *statuses*.

    Args:
        diffs: Iterable of EntryDiff objects.
        statuses: List of status strings to keep, e.g. ``['added', 'removed']``.

    Returns:
        Filtered list of EntryDiff objects.
    """
    return [entry for entry in diffs if entry.status in statuses]
