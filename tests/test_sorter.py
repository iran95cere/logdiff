"""Tests for logdiff.sorter."""

import pytest
from logdiff.sorter import sort_diffs, sort_diffs_by_most_changed, SORT_KEYS
from logdiff.differ import EntryDiff, FieldChange


def make_diff(key, changes=None, status="modified"):
    """Helper to build a minimal EntryDiff."""
    return EntryDiff(
        key=key,
        status=status,
        changes=changes or [],
    )


def make_change(field, old=None, new=None):
    return FieldChange(field=field, old_value=old, new_value=new)


# ---------------------------------------------------------------------------
# sort_diffs
# ---------------------------------------------------------------------------

def test_sort_diffs_by_key_ascending():
    diffs = [make_diff("c"), make_diff("a"), make_diff("b")]
    result = sort_diffs(diffs, by="key")
    assert [d.key for d in result] == ["a", "b", "c"]


def test_sort_diffs_by_key_descending():
    diffs = [make_diff("a"), make_diff("c"), make_diff("b")]
    result = sort_diffs(diffs, by="key", reverse=True)
    assert [d.key for d in result] == ["c", "b", "a"]


def test_sort_diffs_by_change_count():
    diffs = [
        make_diff("x", changes=[make_change("f1"), make_change("f2")]),
        make_diff("y", changes=[]),
        make_diff("z", changes=[make_change("f1")]),
    ]
    result = sort_diffs(diffs, by="change_count")
    assert [d.key for d in result] == ["y", "z", "x"]


def test_sort_diffs_by_status():
    diffs = [
        make_diff("a", status="removed"),
        make_diff("b", status="added"),
        make_diff("c", status="modified"),
    ]
    result = sort_diffs(diffs, by="status")
    assert [d.status for d in result] == ["added", "modified", "removed"]


def test_sort_diffs_invalid_key_raises():
    diffs = [make_diff("a")]
    with pytest.raises(ValueError, match="Invalid sort key"):
        sort_diffs(diffs, by="nonexistent")


def test_sort_diffs_returns_new_list():
    diffs = [make_diff("b"), make_diff("a")]
    result = sort_diffs(diffs, by="key")
    assert result is not diffs


def test_sort_diffs_empty_list():
    assert sort_diffs([], by="key") == []


# ---------------------------------------------------------------------------
# sort_diffs_by_most_changed
# ---------------------------------------------------------------------------

def test_sort_by_most_changed_descending():
    diffs = [
        make_diff("a", changes=[make_change("f")]),
        make_diff("b", changes=[make_change("f"), make_change("g"), make_change("h")]),
        make_diff("c", changes=[]),
    ]
    result = sort_diffs_by_most_changed(diffs)
    assert [d.key for d in result] == ["b", "a", "c"]


def test_sort_by_most_changed_top_n():
    diffs = [
        make_diff("a", changes=[make_change("f")]),
        make_diff("b", changes=[make_change("f"), make_change("g")]),
        make_diff("c", changes=[]),
    ]
    result = sort_diffs_by_most_changed(diffs, top_n=2)
    assert len(result) == 2
    assert result[0].key == "b"


def test_sort_by_most_changed_top_n_larger_than_list():
    diffs = [make_diff("a"), make_diff("b")]
    result = sort_diffs_by_most_changed(diffs, top_n=10)
    assert len(result) == 2


def test_sort_by_most_changed_empty():
    assert sort_diffs_by_most_changed([]) == []
