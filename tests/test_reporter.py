"""Tests for logdiff.reporter module."""

import pytest
from logdiff.differ import EntryDiff, FieldChange
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


def test_build_report_counts_modified():
    diffs = [
        make_diff("req-1", changes=[make_change("status", 200, 500)]),
        make_diff("req-2", changes=[make_change("latency", 10, 20)]),
    ]
    report = build_report(diffs, total_before=2, total_after=2)
    assert report.modified == 2
    assert report.added == 0
    assert report.removed == 0


def test_build_report_counts_added_and_removed():
    diffs = [
        make_diff("req-new", is_added=True),
        make_diff("req-old", is_removed=True),
    ]
    report = build_report(diffs, total_before=3, total_after=3)
    assert report.added == 1
    assert report.removed == 1
    assert report.modified == 0


def test_build_report_unchanged():
    diffs = [make_diff("req-1", changes=[])]
    report = build_report(diffs, total_before=1, total_after=1)
    assert report.unchanged == 1


def test_has_changes_true():
    diffs = [make_diff("req-1", changes=[make_change("status", 200, 500)])]
    report = build_report(diffs, total_before=1, total_after=1)
    assert report.has_changes is True


def test_has_changes_false():
    diffs = [make_diff("req-1", changes=[])]
    report = build_report(diffs, total_before=1, total_after=1)
    assert report.has_changes is False


def test_change_rate():
    diffs = [
        make_diff("req-1", changes=[make_change("status", 200, 500)]),
        make_diff("req-2", changes=[]),
        make_diff("req-3", changes=[]),
        make_diff("req-4", changes=[]),
    ]
    report = build_report(diffs, total_before=4, total_after=4)
    assert report.change_rate == 0.25


def test_most_changed_fields():
    diffs = [
        make_diff("req-1", changes=[make_change("status"), make_change("latency")]),
        make_diff("req-2", changes=[make_change("status")]),
        make_diff("req-3", changes=[make_change("status")]),
    ]
    report = build_report(diffs, total_before=3, total_after=3)
    top = report.most_changed_fields(top_n=2)
    assert top[0] == ("status", 3)
    assert top[1] == ("latency", 1)


def test_empty_report():
    report = build_report([], total_before=0, total_after=0)
    assert report.total_entries == 0
    assert report.change_rate == 0.0
    assert report.has_changes is False
    assert report.most_changed_fields() == []
