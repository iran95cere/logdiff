"""Tests for logdiff.differ_stats."""

import pytest

from logdiff.differ import FieldChange, EntryDiff
from logdiff.differ_stats import (
    FieldStats,
    DiffStats,
    StatsError,
    compute_stats,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field, before, after):
    return FieldChange(field=field, before=before, after=after)


def make_diff(key, changes):
    return EntryDiff(key=key, changes=changes)


# ---------------------------------------------------------------------------
# FieldStats
# ---------------------------------------------------------------------------

def test_field_stats_total_changes():
    fs = FieldStats(field_name="status", modified_count=2, added_count=1, removed_count=1)
    assert fs.total_changes == 4


def test_field_stats_zero_total():
    fs = FieldStats(field_name="level")
    assert fs.total_changes == 0


# ---------------------------------------------------------------------------
# DiffStats
# ---------------------------------------------------------------------------

def test_diff_stats_change_rate_zero_entries():
    ds = DiffStats()
    assert ds.change_rate == 0.0


def test_diff_stats_change_rate():
    ds = DiffStats(total_entries=10, changed_entries=4)
    assert ds.change_rate == pytest.approx(0.4)


def test_diff_stats_top_fields_returns_sorted():
    ds = DiffStats(
        total_entries=5,
        changed_entries=3,
        field_stats={
            "a": FieldStats("a", modified_count=1),
            "b": FieldStats("b", modified_count=5),
            "c": FieldStats("c", modified_count=3),
        },
    )
    top = ds.top_fields(n=2)
    assert [fs.field_name for fs in top] == ["b", "c"]


def test_diff_stats_top_fields_fewer_than_n():
    ds = DiffStats(
        total_entries=2,
        changed_entries=1,
        field_stats={"x": FieldStats("x", modified_count=1)},
    )
    assert len(ds.top_fields(n=10)) == 1


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

def test_compute_stats_raises_on_non_list():
    with pytest.raises(StatsError):
        compute_stats("not a list")


def test_compute_stats_empty_list():
    result = compute_stats([])
    assert result.total_entries == 0
    assert result.changed_entries == 0
    assert result.unchanged_entries == 0
    assert result.field_stats == {}


def test_compute_stats_counts_entries():
    diffs = [
        make_diff("req-1", [make_change("status", "200", "500")]),
        make_diff("req-2", []),
    ]
    result = compute_stats(diffs)
    assert result.total_entries == 2
    assert result.changed_entries == 1
    assert result.unchanged_entries == 1


def test_compute_stats_modified_field():
    diffs = [make_diff("r1", [make_change("level", "info", "error")])]
    result = compute_stats(diffs)
    assert result.field_stats["level"].modified_count == 1
    assert result.field_stats["level"].added_count == 0
    assert result.field_stats["level"].removed_count == 0


def test_compute_stats_added_field():
    diffs = [make_diff("r1", [make_change("trace_id", None, "abc123")])]
    result = compute_stats(diffs)
    assert result.field_stats["trace_id"].added_count == 1


def test_compute_stats_removed_field():
    diffs = [make_diff("r1", [make_change("debug", "verbose", None)])]
    result = compute_stats(diffs)
    assert result.field_stats["debug"].removed_count == 1


def test_compute_stats_change_rate():
    diffs = [
        make_diff("a", [make_change("f", 1, 2)]),
        make_diff("b", [make_change("f", 1, 2)]),
        make_diff("c", []),
        make_diff("d", []),
    ]
    result = compute_stats(diffs)
    assert result.change_rate == pytest.approx(0.5)
