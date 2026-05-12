"""Pivot diffs by a chosen field, producing a table of field changes per group."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logdiff.differ import EntryDiff


class PivotError(Exception):
    """Raised when pivot operations fail."""


@dataclass
class PivotCell:
    """A single cell in the pivot table: change counts for one (group, field) pair."""

    added: int = 0
    removed: int = 0
    modified: int = 0

    @property
    def total(self) -> int:
        return self.added + self.removed + self.modified

    def __repr__(self) -> str:  # pragma: no cover
        return f"PivotCell(added={self.added}, removed={self.removed}, modified={self.modified})"


@dataclass
class PivotTable:
    """A pivot table grouping field-change counts by a pivot field value."""

    pivot_field: str
    # rows keyed by group value -> field name -> PivotCell
    rows: Dict[str, Dict[str, PivotCell]] = field(default_factory=dict)

    @property
    def groups(self) -> List[str]:
        return sorted(self.rows.keys())

    @property
    def fields(self) -> List[str]:
        all_fields: set = set()
        for row in self.rows.values():
            all_fields.update(row.keys())
        return sorted(all_fields)

    def cell(self, group: str, field_name: str) -> PivotCell:
        return self.rows.get(group, {}).get(field_name, PivotCell())

    def __repr__(self) -> str:  # pragma: no cover
        return f"PivotTable(pivot_field={self.pivot_field!r}, groups={self.groups})"


def build_pivot(
    diffs: List[EntryDiff],
    pivot_field: str,
    sentinel: str = "<missing>",
) -> PivotTable:
    """Build a PivotTable from a list of EntryDiff objects.

    Args:
        diffs: List of EntryDiff instances to pivot.
        pivot_field: The field whose value determines the row group.
        sentinel: Value used when pivot_field is absent from an entry.

    Returns:
        A populated PivotTable.

    Raises:
        PivotError: If diffs is empty.
    """
    if not diffs:
        raise PivotError("Cannot build pivot table from empty diff list.")

    table = PivotTable(pivot_field=pivot_field)

    for entry_diff in diffs:
        # Determine group value from before or after entry
        entry = entry_diff.before or entry_diff.after or {}
        group_value = str(entry.get(pivot_field, sentinel))

        if group_value not in table.rows:
            table.rows[group_value] = {}

        for change in entry_diff.changes:
            if change.field not in table.rows[group_value]:
                table.rows[group_value][change.field] = PivotCell()

            cell = table.rows[group_value][change.field]
            if change.before is None:
                cell.added += 1
            elif change.after is None:
                cell.removed += 1
            else:
                cell.modified += 1

    return table
