"""Field-level diff engine for structured log entries."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldChange:
    """Represents a single field-level change between two log entries."""

    key: str
    old_value: Any
    new_value: Any
    change_type: str  # 'added', 'removed', 'modified'

    def __repr__(self) -> str:
        if self.change_type == "added":
            return f"[+] {self.key}: {self.new_value!r}"
        if self.change_type == "removed":
            return f"[-] {self.key}: {self.old_value!r}"
        return f"[~] {self.key}: {self.old_value!r} -> {self.new_value!r}"


@dataclass
class EntryDiff:
    """Diff result for a matched pair of log entries."""

    match_key: str
    match_value: Any
    changes: list[FieldChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0


def diff_entries(
    baseline: list[dict],
    target: list[dict],
    match_by: str = "id",
) -> list[EntryDiff]:
    """Diff two lists of log entries matched by a common key.

    Args:
        baseline: Parsed log entries from the baseline deployment.
        target: Parsed log entries from the target deployment.
        match_by: Field name used to correlate entries across logs.

    Returns:
        List of EntryDiff objects for all matched entries with changes.
    """
    baseline_index = {entry[match_by]: entry for entry in baseline if match_by in entry}
    target_index = {entry[match_by]: entry for entry in target if match_by in entry}

    results: list[EntryDiff] = []

    all_keys = set(baseline_index) | set(target_index)

    for key in sorted(all_keys, key=str):
        base_entry = baseline_index.get(key)
        tgt_entry = target_index.get(key)

        entry_diff = EntryDiff(match_key=match_by, match_value=key)

        if base_entry is None:
            # Entire entry is new in target
            for field_name, value in (tgt_entry or {}).items():
                entry_diff.changes.append(
                    FieldChange(key=field_name, old_value=None, new_value=value, change_type="added")
                )
        elif tgt_entry is None:
            # Entire entry removed in target
            for field_name, value in base_entry.items():
                entry_diff.changes.append(
                    FieldChange(key=field_name, old_value=value, new_value=None, change_type="removed")
                )
        else:
            entry_diff.changes = _diff_fields(base_entry, tgt_entry)

        if entry_diff.has_changes:
            results.append(entry_diff)

    return results


def _diff_fields(base: dict, target: dict) -> list[FieldChange]:
    """Compare two dicts and return field-level changes."""
    changes: list[FieldChange] = []
    all_fields = set(base) | set(target)

    for key in sorted(all_fields):
        base_val = base.get(key)
        tgt_val = target.get(key)

        if key not in base:
            changes.append(FieldChange(key=key, old_value=None, new_value=tgt_val, change_type="added"))
        elif key not in target:
            changes.append(FieldChange(key=key, old_value=base_val, new_value=None, change_type="removed"))
        elif base_val != tgt_val:
            changes.append(FieldChange(key=key, old_value=base_val, new_value=tgt_val, change_type="modified"))

    return changes
