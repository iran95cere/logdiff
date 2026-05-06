"""Tests for logdiff.differ module."""

import pytest
from logdiff.differ import FieldChange, EntryDiff, diff_entries, _diff_fields


BASELINE = [
    {"id": "req-1", "status": 200, "duration_ms": 45, "service": "auth"},
    {"id": "req-2", "status": 500, "duration_ms": 120, "service": "api"},
    {"id": "req-3", "status": 200, "duration_ms": 30, "service": "auth"},
]

TARGET = [
    {"id": "req-1", "status": 200, "duration_ms": 52, "service": "auth"},
    {"id": "req-2", "status": 200, "duration_ms": 98, "service": "api"},
    {"id": "req-4", "status": 201, "duration_ms": 10, "service": "billing"},
]


def test_diff_entries_returns_only_changed():
    results = diff_entries(BASELINE, TARGET)
    assert all(r.has_changes for r in results)


def test_diff_entries_detects_modification():
    results = diff_entries(BASELINE, TARGET)
    req1_diff = next(r for r in results if r.match_value == "req-1")
    assert req1_diff.has_changes
    duration_change = next(c for c in req1_diff.changes if c.key == "duration_ms")
    assert duration_change.change_type == "modified"
    assert duration_change.old_value == 45
    assert duration_change.new_value == 52


def test_diff_entries_detects_status_change():
    results = diff_entries(BASELINE, TARGET)
    req2_diff = next(r for r in results if r.match_value == "req-2")
    status_change = next(c for c in req2_diff.changes if c.key == "status")
    assert status_change.change_type == "modified"
    assert status_change.old_value == 500
    assert status_change.new_value == 200


def test_diff_entries_detects_removed_entry():
    results = diff_entries(BASELINE, TARGET)
    req3_diff = next((r for r in results if r.match_value == "req-3"), None)
    assert req3_diff is not None
    assert all(c.change_type == "removed" for c in req3_diff.changes)


def test_diff_entries_detects_added_entry():
    results = diff_entries(BASELINE, TARGET)
    req4_diff = next((r for r in results if r.match_value == "req-4"), None)
    assert req4_diff is not None
    assert all(c.change_type == "added" for c in req4_diff.changes)


def test_diff_entries_custom_match_key():
    logs_a = [{"trace_id": "abc", "level": "INFO"}]
    logs_b = [{"trace_id": "abc", "level": "ERROR"}]
    results = diff_entries(logs_a, logs_b, match_by="trace_id")
    assert len(results) == 1
    assert results[0].match_key == "trace_id"
    assert results[0].match_value == "abc"


def test_diff_entries_skips_entries_missing_match_key():
    logs_a = [{"status": 200}, {"id": "x", "status": 404}]
    logs_b = [{"status": 201}, {"id": "x", "status": 200}]
    results = diff_entries(logs_a, logs_b, match_by="id")
    assert len(results) == 1
    assert results[0].match_value == "x"


def test_diff_entries_no_changes_returns_empty():
    same = [{"id": "1", "val": 42}]
    results = diff_entries(same, same)
    assert results == []


def test_diff_fields_added_field():
    changes = _diff_fields({"a": 1}, {"a": 1, "b": 2})
    assert len(changes) == 1
    assert changes[0].key == "b"
    assert changes[0].change_type == "added"


def test_diff_fields_removed_field():
    changes = _diff_fields({"a": 1, "b": 2}, {"a": 1})
    assert len(changes) == 1
    assert changes[0].key == "b"
    assert changes[0].change_type == "removed"


def test_field_change_repr_added():
    fc = FieldChange(key="level", old_value=None, new_value="ERROR", change_type="added")
    assert repr(fc) == "[+] level: 'ERROR'"


def test_field_change_repr_removed():
    fc = FieldChange(key="level", old_value="INFO", new_value=None, change_type="removed")
    assert repr(fc) == "[-] level: 'INFO'"


def test_field_change_repr_modified():
    fc = FieldChange(key="status", old_value=200, new_value=500, change_type="modified")
    assert repr(fc) == "[~] status: 200 -> 500"
