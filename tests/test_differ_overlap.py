"""Tests for logdiff.differ_overlap."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_overlap import (
    FieldOverlap,
    OverlapError,
    OverlapResult,
    find_overlap,
)


def make_change(field: str, kind: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="old", after="new", kind=kind)


def make_diff(key: str, fields: list) -> EntryDiff:
    changes = [make_change(f) for f in fields]
    return EntryDiff(key=key, changes=changes)


# --- FieldOverlap ---

def test_field_overlap_total():
    fo = FieldOverlap(field_name="status", count_a=3, count_b=5)
    assert fo.total == 8


def test_field_overlap_repr():
    fo = FieldOverlap(field_name="level", count_a=1, count_b=2)
    assert "level" in repr(fo)
    assert "count_a=1" in repr(fo)
    assert "count_b=2" in repr(fo)


# --- OverlapResult ---

def test_overlap_result_overlap_count():
    result = OverlapResult(
        overlapping_fields=[
            FieldOverlap("a", 1, 1),
            FieldOverlap("b", 2, 3),
        ]
    )
    assert result.overlap_count == 2


def test_overlap_result_top_limits():
    fields = [FieldOverlap(f"f{i}", i, i) for i in range(10)]
    result = OverlapResult(overlapping_fields=fields)
    assert len(result.top(3)) == 3


def test_overlap_result_top_sorted_by_total():
    fields = [
        FieldOverlap("low", 1, 1),
        FieldOverlap("high", 10, 10),
        FieldOverlap("mid", 3, 3),
    ]
    result = OverlapResult(overlapping_fields=fields)
    top = result.top(2)
    assert top[0].field_name == "high"
    assert top[1].field_name == "mid"


# --- find_overlap ---

def test_find_overlap_empty_both_raises():
    with pytest.raises(OverlapError):
        find_overlap([], [])


def test_find_overlap_shared_fields():
    a = [make_diff("k1", ["status", "level"]), make_diff("k2", ["status"])]
    b = [make_diff("k3", ["status", "message"])]
    result = find_overlap(a, b)
    shared_names = {f.field_name for f in result.overlapping_fields}
    assert "status" in shared_names
    assert "level" not in shared_names
    assert "message" not in shared_names


def test_find_overlap_only_in_a():
    a = [make_diff("k1", ["exclusive_a"])]
    b = [make_diff("k2", ["exclusive_b"])]
    result = find_overlap(a, b)
    assert "exclusive_a" in result.only_in_a
    assert "exclusive_b" not in result.only_in_a


def test_find_overlap_only_in_b():
    a = [make_diff("k1", ["field_a"])]
    b = [make_diff("k2", ["field_b"])]
    result = find_overlap(a, b)
    assert "field_b" in result.only_in_b


def test_find_overlap_counts_correctly():
    a = [make_diff("k1", ["x"]), make_diff("k2", ["x"])]
    b = [make_diff("k3", ["x"])]
    result = find_overlap(a, b)
    overlap = next(f for f in result.overlapping_fields if f.field_name == "x")
    assert overlap.count_a == 2
    assert overlap.count_b == 1


def test_find_overlap_one_empty_side():
    a = [make_diff("k1", ["alpha", "beta"])]
    result = find_overlap(a, [])
    assert result.overlap_count == 0
    assert "alpha" in result.only_in_a
    assert "beta" in result.only_in_a
    assert len(result.only_in_b) == 0
