"""Tests for logdiff.filter."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.filter import filter_by_fields, filter_by_status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_diff(key: str, fields: list[tuple], status: str = "modified") -> EntryDiff:
    changes = [
        FieldChange(field=f, old_value=old, new_value=new)
        for f, old, new in fields
    ]
    return EntryDiff(key=key, changes=changes, status=status)


# ---------------------------------------------------------------------------
# filter_by_fields
# ---------------------------------------------------------------------------

def test_filter_by_fields_include_keeps_matching():
    diff = make_diff("req-1", [("level", "info", "warn"), ("msg", "a", "b")])
    result = filter_by_fields([diff], include_fields=["level"])
    assert len(result) == 1
    assert len(result[0].changes) == 1
    assert result[0].changes[0].field == "level"


def test_filter_by_fields_include_drops_entry_when_no_match():
    diff = make_diff("req-1", [("msg", "a", "b")])
    result = filter_by_fields([diff], include_fields=["level"])
    assert result == []


def test_filter_by_fields_exclude_removes_matching():
    diff = make_diff("req-1", [("level", "info", "warn"), ("msg", "a", "b")])
    result = filter_by_fields([diff], exclude_fields=["msg"])
    assert len(result) == 1
    assert all(c.field != "msg" for c in result[0].changes)


def test_filter_by_fields_exclude_drops_entry_when_all_excluded():
    diff = make_diff("req-1", [("msg", "a", "b")])
    result = filter_by_fields([diff], exclude_fields=["msg"])
    assert result == []


def test_filter_by_fields_no_filters_returns_all():
    diffs = [
        make_diff("req-1", [("level", "info", "warn")]),
        make_diff("req-2", [("status", 200, 500)]),
    ]
    result = filter_by_fields(diffs)
    assert len(result) == 2


def test_filter_by_fields_include_and_exclude_combined():
    diff = make_diff("req-1", [("level", "info", "warn"), ("msg", "a", "b"), ("ts", 1, 2)])
    result = filter_by_fields(diff for diff in [diff], include_fields=["level", "ts"], exclude_fields=["ts"])
    assert len(result) == 1
    assert [c.field for c in result[0].changes] == ["level"]


# ---------------------------------------------------------------------------
# filter_by_status
# ---------------------------------------------------------------------------

def test_filter_by_status_keeps_matching():
    diffs = [
        make_diff("req-1", [("level", "info", "warn")], status="modified"),
        make_diff("req-2", [], status="added"),
        make_diff("req-3", [], status="removed"),
    ]
    result = filter_by_status(diffs, ["added", "removed"])
    assert len(result) == 2
    assert all(d.status in ("added", "removed") for d in result)


def test_filter_by_status_empty_list_returns_nothing():
    diffs = [make_diff("req-1", [("level", "info", "warn")], status="modified")]
    result = filter_by_status(diffs, [])
    assert result == []


def test_filter_by_status_all_statuses_returns_all():
    diffs = [
        make_diff("req-1", [], status="modified"),
        make_diff("req-2", [], status="added"),
    ]
    result = filter_by_status(diffs, ["modified", "added", "removed"])
    assert len(result) == 2
