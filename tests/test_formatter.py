"""Tests for logdiff.formatter module."""

import pytest
from logdiff.differ import EntryDiff, FieldChange
from logdiff.formatter import (
    format_entry_diff,
    format_field_change,
    format_summary,
    render_diff,
)
from logdiff.reporter import DiffReport, build_report


def make_change(field_name, old=None, new=None):
    return FieldChange(field=field_name, old_value=old, new_value=new)


def make_diff(key, changes=None, is_added=False, is_removed=False):
    return EntryDiff(
        key=key,
        changes=changes or [],
        is_added=is_added,
        is_removed=is_removed,
    )


def test_format_field_change_modification():
    change = make_change("status", old=200, new=500)
    result = format_field_change(change)
    assert "status" in result
    assert "200" in result
    assert "500" in result


def test_format_field_change_added_field():
    change = make_change("latency", old=None, new=42)
    result = format_field_change(change)
    assert "+" in result
    assert "latency" in result
    assert "42" in result


def test_format_field_change_removed_field():
    change = make_change("debug", old=True, new=None)
    result = format_field_change(change)
    assert "-" in result
    assert "debug" in result


def test_format_entry_diff_modified():
    diff = make_diff("req-1", changes=[make_change("status", 200, 500)])
    result = format_entry_diff(diff)
    assert "req-1" in result
    assert "MODIFIED" in result
    assert "status" in result


def test_format_entry_diff_added():
    diff = make_diff("req-new", is_added=True)
    result = format_entry_diff(diff)
    assert "req-new" in result
    assert "ADDED" in result


def test_format_entry_diff_removed():
    diff = make_diff("req-old", is_removed=True)
    result = format_entry_diff(diff)
    assert "req-old" in result
    assert "REMOVED" in result


def test_format_summary_contains_counts():
    diffs = [
        make_diff("a", changes=[make_change("x", 1, 2)]),
        make_diff("b", is_added=True),
        make_diff("c", is_removed=True),
        make_diff("d"),
    ]
    report = build_report(diffs, total_before=4, total_after=4)
    summary = format_summary(report)
    assert "Modified" in summary or "modified" in summary.lower()
    assert "Added" in summary or "added" in summary.lower()
    assert "Removed" in summary or "removed" in summary.lower()
    assert "1" in summary


def test_render_diff_summary_only():
    diffs = [make_diff("req-1", changes=[make_change("status", 200, 500)])]
    report = build_report(diffs, total_before=1, total_after=1)
    result = render_diff(report, summary_only=True)
    assert "Summary" in result
    assert "MODIFIED" not in result


def test_render_diff_full():
    diffs = [make_diff("req-1", changes=[make_change("status", 200, 500)])]
    report = build_report(diffs, total_before=1, total_after=1)
    result = render_diff(report, summary_only=False)
    assert "MODIFIED" in result
    assert "Summary" in result


def test_render_diff_empty_report():
    report = build_report([], total_before=0, total_after=0)
    result = render_diff(report)
    assert "Summary" in result
