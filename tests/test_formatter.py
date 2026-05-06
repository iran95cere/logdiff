"""Tests for logdiff.formatter output rendering."""

import pytest
from logdiff.differ import EntryDiff, FieldChange
from logdiff.formatter import (
    format_field_change,
    format_entry_diff,
    format_summary,
    render_diff,
)


def make_change(field, old=None, new=None):
    return FieldChange(field=field, old_value=old, new_value=new)


def make_diff(key, changes=None, added=False, removed=False, old=None, new=None):
    return EntryDiff(
        key=key,
        changes=changes or [],
        added=added,
        removed=removed,
        old_entry=old,
        new_entry=new,
    )


def test_format_field_change_modification():
    change = make_change("status", old="ok", new="error")
    result = format_field_change(change, use_color=False)
    assert "~" in result
    assert "status" in result
    assert "'ok'" in result
    assert "'error'" in result


def test_format_field_change_added_field():
    change = make_change("latency", old=None, new=42)
    result = format_field_change(change, use_color=False)
    assert result.startswith("  +")
    assert "latency" in result
    assert "42" in result


def test_format_field_change_removed_field():
    change = make_change("debug", old=True, new=None)
    result = format_field_change(change, use_color=False)
    assert result.startswith("  -")
    assert "debug" in result


def test_format_entry_diff_changed():
    diff = make_diff(
        key="req-1",
        changes=[make_change("level", old="info", new="warn")],
    )
    result = format_entry_diff(diff, use_color=False)
    assert "[CHANGED]" in result
    assert "req-1" in result
    assert "level" in result


def test_format_entry_diff_added():
    diff = make_diff(
        key="req-99",
        added=True,
        new={"level": "info", "msg": "hello"},
    )
    result = format_entry_diff(diff, use_color=False)
    assert "[ADDED]" in result
    assert "req-99" in result
    assert "level" in result


def test_format_entry_diff_removed():
    diff = make_diff(
        key="req-0",
        removed=True,
        old={"level": "error", "msg": "gone"},
    )
    result = format_entry_diff(diff, use_color=False)
    assert "[REMOVED]" in result
    assert "req-0" in result


def test_format_summary_counts():
    diffs = [
        make_diff("a", added=True, new={"x": 1}),
        make_diff("b", removed=True, old={"x": 2}),
        make_diff("c", changes=[make_change("f", old=1, new=2)]),
    ]
    result = format_summary(diffs, use_color=False)
    assert "+1 added" in result
    assert "-1 removed" in result
    assert "~1 changed" in result


def test_render_diff_no_changes():
    result = render_diff([], use_color=False)
    assert "No differences found" in result


def test_render_diff_full_report():
    diffs = [
        make_diff("x", changes=[make_change("status", old="ok", new="fail")]),
        make_diff("y", added=True, new={"msg": "new"}),
    ]
    result = render_diff(diffs, use_color=False)
    assert "[CHANGED]" in result
    assert "[ADDED]" in result
    assert "Summary:" in result
