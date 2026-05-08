"""Tests for logdiff.deduplicator."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.deduplicator import (
    deduplicate,
    deduplicate_with_report,
    DeduplicationReport,
    _change_fingerprint,
)


def make_change(field_name: str, before=None, after=None) -> FieldChange:
    return FieldChange(field=field_name, before=before, after=after)


def make_diff(key: str, changes: list[FieldChange] | None = None) -> EntryDiff:
    return EntryDiff(key=key, changes=changes or [])


# ---------------------------------------------------------------------------
# _change_fingerprint
# ---------------------------------------------------------------------------

def test_change_fingerprint_is_order_independent():
    c1 = make_change("status", "ok", "error")
    c2 = make_change("latency", 100, 200)
    assert _change_fingerprint([c1, c2]) == _change_fingerprint([c2, c1])


def test_change_fingerprint_differs_for_different_values():
    c1 = make_change("status", "ok", "error")
    c2 = make_change("status", "ok", "timeout")
    assert _change_fingerprint([c1]) != _change_fingerprint([c2])


# ---------------------------------------------------------------------------
# deduplicate
# ---------------------------------------------------------------------------

def test_deduplicate_empty_list():
    assert deduplicate([]) == []


def test_deduplicate_no_duplicates_returns_all():
    diffs = [
        make_diff("a", [make_change("f", 1, 2)]),
        make_diff("b", [make_change("f", 3, 4)]),
    ]
    result = deduplicate(diffs)
    assert len(result) == 2


def test_deduplicate_removes_exact_duplicate():
    change = make_change("status", "ok", "error")
    diffs = [
        make_diff("entry-1", [change]),
        make_diff("entry-1", [change]),
    ]
    result = deduplicate(diffs)
    assert len(result) == 1
    assert result[0].key == "entry-1"


def test_deduplicate_same_key_different_changes_kept():
    diffs = [
        make_diff("entry-1", [make_change("a", 1, 2)]),
        make_diff("entry-1", [make_change("b", 3, 4)]),
    ]
    result = deduplicate(diffs)
    assert len(result) == 2


def test_deduplicate_preserves_first_occurrence_order():
    c = make_change("x", 0, 1)
    d1 = make_diff("z", [c])
    d2 = make_diff("a", [c])
    d3 = make_diff("z", [c])  # duplicate of d1
    result = deduplicate([d1, d2, d3])
    assert [r.key for r in result] == ["z", "a"]


def test_deduplicate_multiple_duplicates():
    c = make_change("field", "before", "after")
    diffs = [make_diff("k", [c])] * 5
    result = deduplicate(diffs)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# deduplicate_with_report
# ---------------------------------------------------------------------------

def test_deduplicate_with_report_no_duplicates():
    diffs = [make_diff("a"), make_diff("b")]
    result, report = deduplicate_with_report(diffs)
    assert report.original_count == 2
    assert report.deduplicated_count == 2
    assert report.duplicates_removed == 0
    assert report.removed_keys == []


def test_deduplicate_with_report_tracks_removed_keys():
    c = make_change("status", "ok", "fail")
    diffs = [
        make_diff("entry-x", [c]),
        make_diff("entry-x", [c]),
        make_diff("entry-y", [c]),
    ]
    result, report = deduplicate_with_report(diffs)
    assert report.duplicates_removed == 1
    assert "entry-x" in report.removed_keys
    assert len(result) == 2


def test_deduplicate_with_report_empty_input():
    result, report = deduplicate_with_report([])
    assert result == []
    assert report.original_count == 0
    assert report.deduplicated_count == 0
