"""Tests for logdiff.differ_rollup."""

from __future__ import annotations

import pytest

from logdiff.differ import FieldChange, EntryDiff
from logdiff.differ_rollup import build_rollup, DiffRollup, FieldRollup, RollupError


def make_change(
    field: str = "status",
    before: object = "old",
    after: object = "new",
) -> FieldChange:
    return FieldChange(field=field, before=before, after=after)


def make_diff(key: str = "req-1", changes: list | None = None) -> EntryDiff:
    return EntryDiff(key=key, changes=changes or [])


# ---------------------------------------------------------------------------
# build_rollup
# ---------------------------------------------------------------------------

def test_build_rollup_empty_raises() -> None:
    with pytest.raises(RollupError, match="empty"):
        build_rollup([])


def test_build_rollup_total_entries() -> None:
    diffs = [make_diff("a"), make_diff("b")]
    rollup = build_rollup(diffs)
    assert rollup.total_entries == 2


def test_build_rollup_changed_entries_excludes_unchanged() -> None:
    diffs = [
        make_diff("a", [make_change("f", "x", "y")]),
        make_diff("b", []),
    ]
    rollup = build_rollup(diffs)
    assert rollup.changed_entries == 1


def test_build_rollup_counts_modified() -> None:
    diffs = [
        make_diff("a", [make_change("latency", 100, 200)]),
        make_diff("b", [make_change("latency", 200, 300)]),
    ]
    rollup = build_rollup(diffs)
    assert rollup.fields["latency"].modified == 2
    assert rollup.fields["latency"].added == 0
    assert rollup.fields["latency"].removed == 0


def test_build_rollup_counts_added_field() -> None:
    diffs = [make_diff("a", [make_change("new_field", None, "value")])]
    rollup = build_rollup(diffs)
    assert rollup.fields["new_field"].added == 1
    assert rollup.fields["new_field"].modified == 0


def test_build_rollup_counts_removed_field() -> None:
    diffs = [make_diff("a", [make_change("gone", "value", None)])]
    rollup = build_rollup(diffs)
    assert rollup.fields["gone"].removed == 1
    assert rollup.fields["gone"].modified == 0


def test_build_rollup_multiple_fields() -> None:
    diffs = [
        make_diff("a", [make_change("f1", 1, 2), make_change("f2", None, "v")]),
        make_diff("b", [make_change("f1", 2, 3)]),
    ]
    rollup = build_rollup(diffs)
    assert rollup.fields["f1"].modified == 2
    assert rollup.fields["f2"].added == 1


# ---------------------------------------------------------------------------
# FieldRollup.total
# ---------------------------------------------------------------------------

def test_field_rollup_total() -> None:
    fr = FieldRollup(field_name="x", modified=3, added=1, removed=2)
    assert fr.total == 6


def test_field_rollup_total_zero() -> None:
    fr = FieldRollup(field_name="x")
    assert fr.total == 0


# ---------------------------------------------------------------------------
# DiffRollup.top_fields
# ---------------------------------------------------------------------------

def test_top_fields_returns_sorted_by_total() -> None:
    diffs = [
        make_diff("a", [make_change("rare", 1, 2)]),
        make_diff("b", [make_change("common", 1, 2), make_change("common", 3, 4)]),
        make_diff("c", [make_change("common", 5, 6)]),
    ]
    rollup = build_rollup(diffs)
    top = rollup.top_fields(2)
    assert top[0].field_name == "common"
    assert top[1].field_name == "rare"


def test_top_fields_respects_n_limit() -> None:
    changes = [make_change(f"field_{i}", i, i + 1) for i in range(10)]
    diffs = [make_diff("a", changes)]
    rollup = build_rollup(diffs)
    assert len(rollup.top_fields(3)) == 3
