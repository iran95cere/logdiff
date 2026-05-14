"""Tests for logdiff.differ_index."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_index import (
    DiffIndex,
    FieldIndexEntry,
    IndexError,
    build_index,
)


def make_change(field: str, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type=change_type)


def make_diff(key: str, *fields: str, change_type: str = "modified") -> EntryDiff:
    changes = [make_change(f, change_type) for f in fields]
    return EntryDiff(key=key, changes=changes)


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

def test_build_index_empty_raises():
    with pytest.raises(IndexError, match="empty"):
        build_index([])


def test_build_index_returns_diff_index():
    diffs = [make_diff("e1", "status")]
    result = build_index(diffs)
    assert isinstance(result, DiffIndex)


def test_build_index_indexes_single_field():
    diffs = [make_diff("e1", "status")]
    idx = build_index(diffs)
    assert "status" in idx.entries


def test_build_index_counts_correctly():
    diffs = [
        make_diff("e1", "status"),
        make_diff("e2", "status"),
        make_diff("e3", "level"),
    ]
    idx = build_index(diffs)
    assert idx.entries["status"].count == 2
    assert idx.entries["level"].count == 1


def test_build_index_records_entry_keys():
    diffs = [
        make_diff("e1", "status"),
        make_diff("e2", "status"),
    ]
    idx = build_index(diffs)
    assert set(idx.entries["status"].entry_keys) == {"e1", "e2"}


def test_build_index_records_change_types():
    diffs = [make_diff("e1", "status", change_type="added")]
    idx = build_index(diffs)
    assert idx.entries["status"].change_types["e1"] == "added"


def test_build_index_multiple_fields_per_entry():
    diffs = [make_diff("e1", "status", "level", "message")]
    idx = build_index(diffs)
    assert set(idx.fields()) == {"status", "level", "message"}


# ---------------------------------------------------------------------------
# DiffIndex helpers
# ---------------------------------------------------------------------------

def test_lookup_returns_none_for_unknown_field():
    diffs = [make_diff("e1", "status")]
    idx = build_index(diffs)
    assert idx.lookup("nonexistent") is None


def test_lookup_returns_entry_for_known_field():
    diffs = [make_diff("e1", "status")]
    idx = build_index(diffs)
    entry = idx.lookup("status")
    assert isinstance(entry, FieldIndexEntry)
    assert entry.field_name == "status"


def test_fields_returns_sorted_list():
    diffs = [
        make_diff("e1", "zebra"),
        make_diff("e2", "alpha"),
        make_diff("e3", "monkey"),
    ]
    idx = build_index(diffs)
    assert idx.fields() == ["alpha", "monkey", "zebra"]


def test_top_returns_most_changed():
    diffs = [
        make_diff("e1", "status"),
        make_diff("e2", "status"),
        make_diff("e3", "status"),
        make_diff("e4", "level"),
        make_diff("e5", "message"),
        make_diff("e6", "message"),
    ]
    idx = build_index(diffs)
    top = idx.top(n=2)
    assert len(top) == 2
    assert top[0].field_name == "status"
    assert top[1].field_name == "message"


def test_top_respects_n_limit():
    diffs = [make_diff(f"e{i}", "f1", "f2", "f3", "f4", "f5") for i in range(3)]
    idx = build_index(diffs)
    assert len(idx.top(n=3)) == 3
