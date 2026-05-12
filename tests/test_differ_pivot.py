"""Tests for logdiff.differ_pivot."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_pivot import PivotCell, PivotTable, PivotError, build_pivot


def make_change(
    field: str,
    before=None,
    after=None,
) -> FieldChange:
    return FieldChange(field=field, before=before, after=after)


def make_diff(
    key: str,
    changes: list,
    before: dict | None = None,
    after: dict | None = None,
) -> EntryDiff:
    return EntryDiff(
        key=key,
        before=before or {"id": key},
        after=after or {"id": key},
        changes=changes,
    )


# ---------------------------------------------------------------------------
# PivotCell
# ---------------------------------------------------------------------------

def test_pivot_cell_total_sums_all():
    cell = PivotCell(added=1, removed=2, modified=3)
    assert cell.total == 6


def test_pivot_cell_default_total_is_zero():
    assert PivotCell().total == 0


# ---------------------------------------------------------------------------
# build_pivot — error cases
# ---------------------------------------------------------------------------

def test_build_pivot_empty_raises():
    with pytest.raises(PivotError, match="empty"):
        build_pivot([], pivot_field="service")


# ---------------------------------------------------------------------------
# build_pivot — basic grouping
# ---------------------------------------------------------------------------

def test_build_pivot_groups_by_field():
    diffs = [
        make_diff("a", [make_change("cpu", 0.1, 0.9)], before={"id": "a", "service": "api"}),
        make_diff("b", [make_change("cpu", 0.2, 0.8)], before={"id": "b", "service": "worker"}),
    ]
    table = build_pivot(diffs, pivot_field="service")
    assert set(table.groups) == {"api", "worker"}


def test_build_pivot_counts_modified():
    diffs = [
        make_diff("a", [make_change("cpu", 0.1, 0.9)], before={"id": "a", "svc": "api"}),
    ]
    table = build_pivot(diffs, pivot_field="svc")
    assert table.cell("api", "cpu").modified == 1
    assert table.cell("api", "cpu").added == 0


def test_build_pivot_counts_added():
    diffs = [
        make_diff("a", [make_change("newf", None, "v")], before={"id": "a", "svc": "api"}),
    ]
    table = build_pivot(diffs, pivot_field="svc")
    assert table.cell("api", "newf").added == 1


def test_build_pivot_counts_removed():
    diffs = [
        make_diff("a", [make_change("oldf", "v", None)], before={"id": "a", "svc": "api"}),
    ]
    table = build_pivot(diffs, pivot_field="svc")
    assert table.cell("api", "oldf").removed == 1


def test_build_pivot_missing_pivot_field_uses_sentinel():
    diffs = [
        make_diff("a", [make_change("x", 1, 2)], before={"id": "a"}),
    ]
    table = build_pivot(diffs, pivot_field="service", sentinel="<none>")
    assert "<none>" in table.groups


def test_build_pivot_fields_returns_sorted_unique():
    diffs = [
        make_diff("a", [make_change("z", 1, 2), make_change("a", 1, 2)], before={"id": "a", "s": "x"}),
    ]
    table = build_pivot(diffs, pivot_field="s")
    assert table.fields == ["a", "z"]


def test_build_pivot_cell_missing_group_returns_empty():
    diffs = [
        make_diff("a", [make_change("f", 1, 2)], before={"id": "a", "s": "x"}),
    ]
    table = build_pivot(diffs, pivot_field="s")
    cell = table.cell("nonexistent", "f")
    assert cell.total == 0


def test_build_pivot_aggregates_multiple_entries_same_group():
    diffs = [
        make_diff("a", [make_change("cpu", 0.1, 0.9)], before={"id": "a", "svc": "api"}),
        make_diff("b", [make_change("cpu", 0.2, 0.8)], before={"id": "b", "svc": "api"}),
    ]
    table = build_pivot(diffs, pivot_field="svc")
    assert table.cell("api", "cpu").modified == 2
