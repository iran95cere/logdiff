"""Merge multiple diff lists into a unified result, resolving conflicts by key."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logdiff.differ import EntryDiff, FieldChange


class MergerError(Exception):
    """Raised when merging cannot be completed."""


@dataclass
class MergeResult:
    """Holds the outcome of merging two or more diff lists."""

    merged: List[EntryDiff] = field(default_factory=list)
    conflicts: Dict[str, List[str]] = field(default_factory=dict)  # key -> [source labels]
    source_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.merged)

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)


def _entry_key(entry: EntryDiff) -> Optional[str]:
    """Return the key field value used to identify an entry."""
    before = entry.before or {}
    after = entry.after or {}
    return after.get("id") or before.get("id") or after.get("key") or before.get("key")


def _merge_changes(base: List[FieldChange], incoming: List[FieldChange]) -> List[FieldChange]:
    """Merge two change lists, preferring incoming values on conflict."""
    base_map: Dict[str, FieldChange] = {c.field: c for c in base}
    for change in incoming:
        base_map[change.field] = change
    return list(base_map.values())


def merge_diffs(
    sources: Dict[str, List[EntryDiff]],
    *,
    prefer_last: bool = True,
) -> MergeResult:
    """Merge named diff sources into a single unified diff list.

    Args:
        sources: Mapping of label -> list of EntryDiff.
        prefer_last: When True, later sources overwrite earlier ones on conflict.

    Returns:
        MergeResult with merged diffs and conflict metadata.
    """
    if not sources:
        raise MergerError("No sources provided to merge.")

    result = MergeResult()
    seen: Dict[str, EntryDiff] = {}
    key_sources: Dict[str, List[str]] = {}

    for label, diffs in sources.items():
        result.source_counts[label] = len(diffs)
        for entry in diffs:
            key = _entry_key(entry)
            if key is None:
                result.merged.append(entry)
                continue

            if key not in seen:
                seen[key] = entry
                key_sources[key] = [label]
            else:
                key_sources[key].append(label)
                if prefer_last:
                    existing = seen[key]
                    merged_changes = _merge_changes(existing.changes, entry.changes)
                    seen[key] = EntryDiff(
                        before=entry.before or existing.before,
                        after=entry.after or existing.after,
                        changes=merged_changes,
                    )

    for key, labels in key_sources.items():
        if len(labels) > 1:
            result.conflicts[key] = labels

    result.merged.extend(seen.values())
    return result
